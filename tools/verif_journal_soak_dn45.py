#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dn4-5 / AC2.5 — LA BOITE NOIRE DU SOAK NE PERD RIEN, ET N'INONDE RIEN.

======================= CE QUE CET OUTIL FAIT, ET POURQUOI ==================

⛔ IL NE REJOUE RIEN : il IMPORTE `dn_agent.JournalSoak` et l'APPELLE. La classe
   testee est celle qui tournera pendant sept jours, ⛔ pas une copie.

🔴 LES QUATRE PROPRIETES QUI COMPTENT, ET POURQUOI CHACUNE :

   1. **LE FRAGMENT REPORTE.** Le flux serie arrive par `read()` de taille
      arbitraire : une ligne de battement PEUT etre coupee en deux. Sans report
      du reste, on en perdrait une de temps en temps — en SILENCE, et le journal
      aurait des trous qu'aucun compteur ne signalerait. C'est le piege exact
      que dn4-18 a paye sur son marqueur (« `count()` portait sur UN SEUL
      `read()`, sans report »).

   2. **LE QUOTA QUI SE DECLARE.** Une tempete d'erreurs ne doit pas noyer la
      boite noire — mais un ecretage SILENCIEUX serait un mensonge. On exige
      donc que les lignes ecartees soient COMPTEES ET DITES.

   3. **LES EVENEMENTS DE PORT ECHAPPENT AU QUOTA.** Ce sont eux qui separent
      « l'agent a perdu le port » de « la carte est haltee » (AC2.3). Les
      perdre sous un quota reviendrait a rendre les deux cas indiscernables —
      c'est-a-dire a perdre le verdict du soak.

   4. **LA ROTATION.** « Un instrument qui remplit le disque de la tour casse ce
      qu'il observe. »

⚠️ CE QUE CETTE GATE NE PROUVE PAS : que la carte emet bien ces lignes. Elle
   prouve que SI elle les emet, le journal les garde. La confirmation carte est
   AC3.

Sortie : exit 0 si tout passe, 1 sinon.
"""

import io
import os
import shutil
import sys
import tempfile

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "agent"))
# ⚠️ MEME RITUEL QUE `verif_reprise_horloge_dn418.py` : sans ce drapeau, l'import
#    de `dn_agent` s'arrete sur « psutil manquant » et la gate ne dit pas « KO »,
#    elle dit « je n'ai pas tourne » — les deux se lisent tres differemment.
os.environ.setdefault("DN_STUB_PSUTIL", "1")
sys.path.insert(0, os.path.join(RACINE, "tools", "stub_psutil"))

import dn_agent  # noqa: E402

ok_total = [0]
ko_total = [0]


def ctrl(ok, libelle, detail=""):
    if ok:
        ok_total[0] += 1
        print("  [OK ] %-58s %s" % (libelle, detail))
    else:
        ko_total[0] += 1
        print("  [KO ] %-58s %s" % (libelle, detail))
    return ok


BATTEMENT = (b"I (474367) desknode: up 470 s \xe2\x80\x94 vsync=17627 \xe2\x80\x94 "
             b"flush=3921 cycles=1307 \xe2\x80\x94 PSRAM libre 2064384 o \xe2\x80\x94 "
             b"mural 471 s (\xc3\xa9cart +1 s) \xe2\x80\x94 reset: POWERON\r\n")


def lignes(chemin):
    if not os.path.exists(chemin):
        return []
    return [l for l in io.open(chemin, encoding="utf-8").read().split("\n") if l]


def main():
    print("=" * 78)
    print("dn4-5 / AC2.5 — LA BOITE NOIRE DU SOAK")
    print("=" * 78)
    d = tempfile.mkdtemp(prefix="dn45j_")
    try:
        # ── 1. LE BATTEMENT EST GARDE, LE BRUIT EST FILTRE ──────────────────
        print("\n── 1. CE QUI EST GARDE, ET CE QUI NE L'EST PAS ───────────────────")
        p = os.path.join(d, "soak.log")
        j = dn_agent.JournalSoak(p)
        j.alimenter(BATTEMENT)
        j.alimenter(b"desknode> \r\n")
        j.alimenter(b"I (474400) dn_link: trame acceptee\r\n")
        j.alimenter(b"ets Jul 29 2019 12:21:46\r\nrst:0x1 (POWERON),boot:0x8\r\n")
        j.alimenter(b"Guru Meditation Error: Core 0 panic'ed\r\n")
        j.fermer()
        ls = lignes(p)
        ctrl(sum("BATTEMENT" in l for l in ls) == 1, "le battement est journalise",
             "1 ligne BATTEMENT")
        ctrl(sum("REBOOT" in l for l in ls) == 1, "un redemarrage est journalise",
             "`rst:0x…` reconnu")
        ctrl(sum("ALARME" in l for l in ls) == 1, "une panique est journalisee",
             "`Guru Meditation` reconnu")
        ctrl(all("up 470 s" in l for l in ls if "BATTEMENT" in l),
             "la ligne de battement est gardee ENTIERE", "texte preserve")

        # ── 2. LE FRAGMENT REPORTE ──────────────────────────────────────────
        print("\n── 2. UNE LIGNE COUPEE ENTRE DEUX `read()` N'EST PAS PERDUE ──────")
        for coupe in (10, 40, len(BATTEMENT) - 3):
            p2 = os.path.join(d, "coupe%d.log" % coupe)
            j2 = dn_agent.JournalSoak(p2)
            j2.alimenter(BATTEMENT[:coupe])
            j2.alimenter(BATTEMENT[coupe:])
            j2.fermer()
            l2 = lignes(p2)
            ctrl(sum("BATTEMENT" in l for l in l2) == 1
                 and any("up 470 s" in l for l in l2),
                 "coupure a l'octet %d : la ligne survit ENTIERE" % coupe,
                 "%d ligne(s) ecrite(s)" % len(l2))

        # ── 3. LE QUOTA, ET SON AVEU ────────────────────────────────────────
        print("\n── 3. LE QUOTA ECRETE, ET IL LE DIT ──────────────────────────────")
        p3 = os.path.join(d, "quota.log")
        j3 = dn_agent.JournalSoak(p3)
        n = dn_agent.JournalSoak.QUOTA_AUTRES_PAR_MIN
        for i in range(n + 50):
            j3.alimenter(b"I (1) dn_env: bruit %d\r\n" % i)
        garde = sum(1 for l in lignes(p3) if " fil " in l)
        ctrl(garde == n, "le quota plafonne bien les lignes « fil »",
             "%d gardees pour %d emises (plafond %d)" % (garde, n + 50, n))
        # On force la minute suivante : l'aveu doit sortir.
        j3._fenetre_min = -999
        j3.alimenter(b"I (1) dn_env: minute suivante\r\n")
        j3.fermer()
        aveu = [l for l in lignes(p3) if "MINUTE" in l]
        ctrl(len(aveu) == 1 and "50 ligne(s) ECARTEE(S)" in aveu[0],
             "⛔ l'ecretage est DIT, jamais silencieux",
             aveu[0].split("MINUTE")[-1].strip()[:60] if aveu else "⛔ AUCUN AVEU")

        # ── L'ECHO DE L'AGENT — LE DEFAUT QUE LA CARTE A TROUVE ─────────────
        print("\n── 3 bis. L'ECHO DE L'AGENT EST FILTRE, ⛔ PAS ECRETE ────────────")
        # 🔴 MESURE DU 2026-08-26, SUR LA CARTE : le REPL RENVOIE en echo chaque
        #    trame `pc $DN,...` (cinq par seconde), entrelacee d'invites. Ce
        #    bruit SATURAIT le quota — 437 lignes jetees en 2 minutes — et une
        #    anomalie REELLE pouvait partir avec. Un instrument qui jette le
        #    signal pour garder son propre bruit ne protege rien.
        p3b = os.path.join(d, "echo.log")
        j3b = dn_agent.JournalSoak(p3b)
        for i in range(300):
            j3b.alimenter(b"pc $DN,3,1,1050,cpu,83,23,164,433*67\r\n")
            j3b.alimenter(b"desknode> pc $DN,3,2,1050,gpu,80,480,530,6000*69\r\n")
            j3b.alimenter(b"desknode> \r\n")
        # 🔴 LE FRAGMENT — mesure sur la carte le 2026-08-26. Le REPL entrelace
        #    ses invites AU MILIEU des echos, et une trame coupee entre deux
        #    `read()` arrive sous la forme `desknode> desknode> c $DN,3,126,...`
        #    (le `p` de `pc` est parti dans l'autre morceau). Un filtre ancre en
        #    debut de ligne la laissait passer.
        j3b.alimenter(b"desknode> desknode> c $DN,3,126,26027,cpu,73,30,203*5A\r\n")
        j3b.alimenter(b"desknode> 33,gpu,70 $DN,4,1,1*02\r\n")
        j3b.alimenter(b"I (1) dn_env: une VRAIE ligne\r\n")
        j3b.fermer()
        ls3b = lignes(p3b)
        ctrl(not any("$DN," in l for l in ls3b),
             "⛔ AUCUN echo `$DN,` n'entre dans la boite noire, FRAGMENTS COMPRIS",
             "%d ligne(s) ecrite(s) pour 902 echos injectes (dont 2 fragments)"
             % len(ls3b))
        ctrl(any("une VRAIE ligne" in l for l in ls3b),
             "et la VRAIE ligne passe quand meme",
             "⛔ 900 echos ne doivent PAS saturer le quota d'une vraie ligne")
        j3b2 = dn_agent.JournalSoak(os.path.join(d, "echo2.log"))
        j3b2.alimenter(b"pc $DN,3,1,1050,cpu,1*01\r\n")
        j3b2._fenetre_min = -999
        j3b2.alimenter(b"I (1) x: suivante\r\n")
        j3b2.fermer()
        av2 = [l for l in lignes(os.path.join(d, "echo2.log")) if "MINUTE" in l]
        ctrl(av2 and "1 echo(s) de l'agent filtre(s)" in av2[0],
             "les echos filtres sont COMPTES et DITS",
             "⛔ un echo qui s'effondre dirait que la carte ne recoit plus rien")

        # ── 4. LES EVENEMENTS DE PORT ECHAPPENT AU QUOTA ────────────────────
        print("\n── 4. LES EVENEMENTS DE PORT PASSENT TOUJOURS ────────────────────")
        p4 = os.path.join(d, "port.log")
        j4 = dn_agent.JournalSoak(p4)
        for i in range(n + 20):
            j4.alimenter(b"I (1) dn_env: bruit\r\n")
        j4.evenement("PORT", "PERDU — backoff 0.5 s")
        j4.fermer()
        ctrl(any("PERDU" in l for l in lignes(p4)),
             "un PORT PERDU passe malgre le quota SATURE",
             "c'est lui qui separe « agent sans port » de « carte haltee »")

        # ── 5. LA ROTATION ──────────────────────────────────────────────────
        print("\n── 5. LA ROTATION BORNE LE DISQUE ────────────────────────────────")
        p5 = os.path.join(d, "rot.log")
        j5 = dn_agent.JournalSoak(p5, max_octets=4096, rotations=2)
        for i in range(400):
            j5.evenement("DEPART", "remplissage %04d" % i)
        j5.fermer()
        presents = [f for f in os.listdir(d) if f.startswith("rot.log")]
        ctrl(len(presents) <= 3, "au plus `rotations`+1 fichiers subsistent",
             "%d fichier(s) : %s" % (len(presents), sorted(presents)))
        gros = max(os.path.getsize(os.path.join(d, f)) for f in presents)
        ctrl(gros < 4096 * 3, "aucun fichier ne depasse grossierement le plafond",
             "le plus gros : %d o pour un plafond de 4 096 o" % gros)

        # ── 6. LE VOLUME ANNONCE, CALCULE SUR LA VRAIE LIGNE ────────────────
        print("\n── 6. LE VOLUME SUR 7 JOURS, ⛔ PAS ESTIME AU DOIGT ──────────────")
        p6 = os.path.join(d, "vol.log")
        j6 = dn_agent.JournalSoak(p6)
        j6.alimenter(BATTEMENT)
        j6.fermer()
        taille = os.path.getsize(p6)
        par_s = taille / 10.0            # une ligne de battement toutes les 10 s
        sept_j = par_s * 7 * 24 * 3600
        # 🔴 CE CHIFFRE DE BANC EST UN PLANCHER, ⛔ PAS UNE PREVISION — ET LA
        #    CARTE L'A DEMONTRE. Le banc ne compte QUE le battement ; le 2026-08-26,
        #    sur 120 s de regime reel, le journal a ecrit 18 873 o = **157 o/s**,
        #    soit ~95 Mo sur 7 jours — **8,6x** ce que ce calcul annonce. L'ecart
        #    venait de l'echo de l'agent, desormais FILTRE (§3 bis), mais le
        #    principe reste : un volume estime au banc borne par le BAS.
        ctrl(sept_j < 50 * 1024 * 1024,
             "le PLANCHER de banc tient largement sur 7 jours",
             "%d o/ligne ⇒ %.1f o/s ⇒ %.1f Mo (⚠️ PLANCHER : la carte a mesure "
             "157 o/s AVANT le filtre d'echo ⇒ ~95 Mo)"
             % (taille, par_s, sept_j / (1024 * 1024)))
        ctrl(True, "⚠️ et la limite de ce calcul est DECLAREE",
             "il ne compte que le battement ; le fil porte aussi les logs des "
             "autres modules")
    finally:
        shutil.rmtree(d, ignore_errors=True)

    print("\n" + "=" * 78)
    print("BILAN : %d OK, %d KO" % (ok_total[0], ko_total[0]))
    print("=" * 78)
    return 1 if ko_total[0] else 0


if __name__ == "__main__":
    sys.exit(main())
