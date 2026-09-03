# -*- coding: utf-8 -*-
"""dn4-44 / AC5.7 — LES BANCS DE LA CAMPAGNE SONT-ILS CAPABLES DE ROUGIR ?

🔴 LA QUESTION QUE CETTE STORY S'APPLIQUE A ELLE-MEME. `verif_campagne_dn440.py`
porte desormais **12 bancs** qui gardent ses propres correctifs. Ce sont des
CONTROLES NEUFS. La regle de la story — « aucun controle neuf ne sort sans son
mutant » — leur est due comme aux autres.

⛔ CE N'EST PAS UN DEBRANCHEMENT, ET LA DIFFERENCE EST LE SUJET DE dn4-44.
Ce script ne met pas `if False:` devant un banc pour le rendre muet : il
REJOUE **L'ETAT D'AVANT LE CORRECTIF** — exactement l'idiome `--gate` que la
campagne porte deja pour prouver un defaut « a vide » plutot que l'affirmer.
La faute replantee est la faute HISTORIQUE, celle que le correctif a soldee :

  · le `rc` du T0 imprime et **jamais teste** ;
  · la garde de mutation nulle **absente** ;
  · la lecture de trace « **derniere gagne** » ;
  · la cle de trace **sans discriminant** ;
  · la resolution des cibles **au regex** ;
  · le `rc` de la regeneration **jete** ;
  · le compte « gardes par rien » **publie sans garder** ;
  · l'exemption **muette**, qui ne se dement jamais.

⚠️ ⛔ AUCUNE ECRITURE DANS `tools/`. Chaque temoin travaille dans une COPIE du
   repertoire, montee sous un temporaire et rendue.
⚠️ ⛔ UN SEUL SITE A LA FOIS — muter au remplacement global synchroniserait la
   faute ET sa fixture.

🎯 OU S'ARRETE LA REGRESSION, ET C'EST **DECLARE** : ce script ⛔ n'est pas
   lui-meme garde par un banc. Un banc de banc de banc ne finit pas. Ce qui
   tient a sa place : **chaque banc IMPRIME la valeur qu'il a mesuree**
   (« vu : KO », « vu : 2 », « rc vu : 1 »), donc un banc devenu vide se voit
   a la lecture ; et ce script-ci est REJOUABLE, sa sortie est une mesure.

Usage :  python3 tools/temoins_bancs_dn444.py [--cockpit CHEMIN]
"""
import argparse
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)


def monte(tmp, nom):
    """Un FAUX DEPOT DeskNode : `tools/` copie, `firmware/` LIE.

    ⚠️ Sans `firmware/`, la gate du ledger rougit sur « le depot code est le
    depot DESKNODE » — son propre controle, et il a raison. ⛔ On ne copie pas
    186 Mo pour autant : on LIE, comme la campagne du tri le fait deja.
    """
    d = os.path.join(tmp, nom)
    os.makedirs(d)
    shutil.copytree(ICI, os.path.join(d, "tools"),
                    ignore=shutil.ignore_patterns("fixtures", "stub_psutil",
                                                  "__pycache__"))
    os.symlink(os.path.join(RACINE, "firmware"), os.path.join(d, "firmware"))
    return os.path.join(d, "tools")

# (nom du temoin, fichier, ancien texte -> texte HISTORIQUE, bancs vises)
TEMOINS = [
    # ⚠️ DEUX ETATS HISTORIQUES SUCCESSIFS, ⛔ PAS UN SEUL — et il faut les
    #    DEUX : le 1er (aucune garde) est celui d'avant la revue du
    #    2026-09-03, le 2e (« quelque chose a change ») est celui que la revue
    #    a pose et que dn4-44 remplace. Ils ne font ⛔ PAS rougir les memes
    #    bancs, et c'est tout l'ecart entre « ca a bouge » et « LA BONNE chose
    #    a bouge ».
    ("aucune garde de mutation — etat d'AVANT la revue du 2026-09-03",
     "verif_campagne_dn440.py",
     '''        if led != led_a:
            change["ledger"] = _lignes(led_a, led)
        if trk != trk_a:
            change["tracker"] = _lignes(trk_a, trk)''',
     '''        change = {k: [] for k in (mutant.change or ())}''',
     ["B1-mutation-nulle", "B1b-mutation-hors-cible"]),

    ("la garde dit « QUELQUE CHOSE a change », ⛔ pas QUOI — etat du 2026-09-03",
     "verif_campagne_dn440.py",
     '''        if led != led_a:
            change["ledger"] = _lignes(led_a, led)
        if trk != trk_a:
            change["tracker"] = _lignes(trk_a, trk)''',
     '''        if (led != led_a) or (trk != trk_a):
            change = {k: [] for k in (mutant.change or ())}''',
     ["B1b-mutation-hors-cible"]),

    ("le motif de cle de tracker n'est PAS borne",
     "verif_campagne_dn440.py",
     r'''    m = re.search(r"^  (%s(?:-[a-z0-9\-]*)?):\s*[a-z\-]+" % re.escape(court),
                  trk, flags=re.M)''',
     r'''    m = re.search(r"^  (%s[a-z0-9\-]*):\s*[a-z\-]+" % re.escape(court),
                  trk, flags=re.M)''',
     ["B1c-prefixe-sans-borne"]),

    ("le `rc` du T0 est imprime et JAMAIS teste",
     "verif_campagne_dn440.py",
     '''        if rc0 != 0 or not tr0 or ko0 or rg0 not in (0, None):''',
     '''        if False:  # ETAT HISTORIQUE : le rc etait imprime, jamais teste''',
     ["B2a-T0-rc-non-nul", "B2b-T0-trace-vide", "B2c-T0-deja-rouge"]),

    ("la lecture de trace est « DERNIERE GAGNE »",
     "dn_trace.py",
     '''        if k in d and d[k][0] == "KO":
            continue''',
     '''        pass''',
     ["B3-ko-l-emporte"]),

    ("la cle de trace n'a PAS de discriminant",
     "dn_trace.py",
     '''    return "%s%s%s" % (site, SEP, aplati(libelle))''',
     '''    return site''',
     ["B3b-discriminant"]),

    ("la resolution des cibles se fait AU REGEX",
     "dn_sites.py",
     '''    par = {}
    for ligne, _t, lib, forme in sites(chemin):
        if forme == "litteral" and lib:
            par.setdefault(lib, []).append(ligne)
    return par''',
     '''    import re as _re
    src = io.open(chemin, encoding="utf-8").read()
    par = {}
    for m in _re.finditer(r"ctrl\\(\\s*(?:not\\s+)?[^,]+?,\\s*\\n?\\s*(\\"[^\\"]*\\")",
                          src):
        lib = m.group(1)[1:-1]
        par.setdefault(lib, []).append(src.count("\\n", 0, m.start()) + 1)
    return par''',
     ["B4-quatre-formes"]),

    ("le `rc` de la regeneration du manifeste est JETE",
     "verif_campagne_dn440.py",
     '''        rc_regen = r.returncode''',
     '''        rc_regen = None''',
     ["B5-rc-regeneration"]),

    ("le compte « gardes par rien » PUBLIE sans garder",
     "verif_campagne_dn440.py",
     '''        if nus_reels:
            echecs.append("gardes-par-rien")''',
     '''        if False:
            echecs.append("gardes-par-rien")''',
     ["B6-le-compte-garde"]),

    # ═══════════════════════════════════════════════════════════════════════
    #  LES CINQ TEMOINS AJOUTES PAR LA REVUE DE CODE DU 2026-09-03.
    #  🔴 QUATRE GARDENT DES BANCS NEUFS (B7b, B8, B9, B10), poses parce que la
    #     revue a MESURE que `campagne_ctrl_dn440.py` ne recevait AUCUN banc :
    #     AC5.3, AC5.4 et son T0 etaient des correctifs « gardes par rien »,
    #     dans la marche qui existe pour les compter. Decision owner du
    #     2026-09-03 : les ARMER, ⛔ pas fermer avec ecart.
    #  🔴 LE CINQUIEME GARDE UN BANC QUI EXISTAIT ET QUI REGARDAIT AILLEURS :
    #     `B1c` n'interrogeait que l'ORACLE (`_mute_trk_cle`), jamais le MUTEUR
    #     (`mute_tracker`), alors que le motif borne est ecrit dans les DEUX.
    #     Une regression posee dans le muteur SEUL le laissait VERT, et la
    #     campagne imprimait une phrase FAUSSE calculee depuis l'oracle.
    #  ⛔ Chacun REJOUE l'etat d'avant correctif. Aucun ne debranche un banc.
    # ═══════════════════════════════════════════════════════════════════════
    ("le motif du MUTEUR de tracker n'est pas borne (⛔ pas l'oracle)",
     'verif_campagne_dn440.py',
     '        return led, re.sub(\n            r"^(  %s(?:-[a-z0-9\\-]*)?:)\\s*[a-z\\-]+" % re.escape(c),\n            r"\\1 done", trk, count=1, flags=re.M)',
     '        return led, re.sub(\n            r"^(  %s[a-z0-9\\-]*:)\\s*[a-z\\-]+" % re.escape(c),\n            r"\\1 done", trk, count=1, flags=re.M)',
     ['B1c-prefixe-sans-borne']),

    ("l'appariement des libelles est un PREFIXE SYMETRIQUE",
     'dn_sites.py',
     '    return bool(a) and bool(b) and a == b',
     '    return bool(a) and bool(b) and (a.startswith(b) or b.startswith(a))',
     ['B7b-exemption-sans-joker']),

    ('le remede se cherche dans le TEXTE BRUT (commentaires compris)',
     'campagne_ctrl_dn440.py',
     '    chemin = os.path.join(arbre, gate)\n    try:\n        lignes_ctrl = {ligne for ligne, _t, lib, _f in dn_sites.sites(chemin)\n                       if lib and libelle in lib}\n        for ligne, val in dn_sites.chaines(chemin):\n            if libelle in val and ligne not in lignes_ctrl:\n                return True\n    except dn_sites.SourceIllisible:\n        return False\n',
     '    return libelle in dn_sites.texte(os.path.join(arbre, gate))\n',
     ['B8-remede-prouve']),

    ('le bilan annonce le compte DECLARE, ⛔ pas le compte joue',
     'verif_campagne_dn440.py',
     '% (len(tirs), len(echecs), len(nus_reels)))',
     '% (len(MUTANTS) + 1, len(echecs), len(nus_reels)))',
     ['B9-compte-joue']),

    ("le T0 du tri n'existe pas — le `rc` est imprime et jete",
     'campagne_ctrl_dn440.py',
     '    if a_plante(rc, err):',
     "    if False:  # ETAT HISTORIQUE : le tri n'avait AUCUN T0",
     ['B10-T0-du-tri']),

    ("l'exemption est MUETTE — elle ne se dement jamais",
     "verif_campagne_dn440.py",
     '''    for gate, lib, verdict, _m, _q in CC.CAS:''',
     '''    return True, "exempte (liste muette — ETAT HISTORIQUE)"
    for gate, lib, verdict, _m, _q in CC.CAS:''',
     ["B7-exemption-falsifiable"]),
]


def joue_les_bancs(racine, cockpit):
    """Rend `{nom du banc: True si VERT}` — la campagne, bancs seuls."""
    r = subprocess.run(
        [sys.executable, os.path.join(racine, "verif_campagne_dn440.py"),
         "--cockpit", cockpit, "--bancs-seuls"],
        capture_output=True, text=True)
    etat = {}
    for l in r.stdout.split("\n"):
        m = re.match(r"^   \[(OK|!!)\] (\S+)", l)
        if m:
            etat[m.group(2)] = (m.group(1) == "OK")
    return etat, r.returncode, r.stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cockpit", default=os.path.join(
        os.environ.get("HOME") or "/nonexistent", "projects", "compagnon_project"))
    a = ap.parse_args()

    print("=" * 78)
    print("dn4-44 / AC5.7 — TEMOINS NEGATIFS DES BANCS DE verif_campagne_dn440.py")
    print("=" * 78)
    print("⛔ chaque temoin REJOUE L'ETAT D'AVANT LE CORRECTIF, ⛔ il ne")
    print("   debranche aucune garde. ⛔ Un seul site a la fois.")
    print("⛔ aucune ecriture dans tools/ : copie jetable.")

    echecs = []
    tmp = tempfile.mkdtemp(prefix="dn444tem-")
    try:
        # ── LE T0 DE CE SCRIPT : tous les bancs sont VERTS a HEAD ───────────
        src = monte(tmp, "t0")
        base, rc0, sortie0 = joue_les_bancs(src, a.cockpit)
        print("\n── T0 : LES BANCS A HEAD ─────────────────────────────────────")
        rouges0 = sorted(k for k, v in base.items() if not v)
        print("   %d banc(s) lu(s) · rc=%d · rouge(s) : %s"
              % (len(base), rc0, ", ".join(rouges0) or "aucun"))
        if rc0 != 0 or not base or rouges0:
            print("   ⛔ le T0 n'est pas vert — TEMOINS ININTERPRETABLES")
            print("   ── sortie de la campagne, pour dire POURQUOI ──")
            for l in sortie0.strip().split("\n")[-12:]:
                print("   | %s" % l)
            return 1

        print("\n── LES TEMOINS ───────────────────────────────────────────────")
        for nom, fic, neuf, vieux, vises in TEMOINS:
            d = monte(tmp, re.sub(r"\W+", "_", nom)[:40])
            p = os.path.join(d, fic)
            s = io.open(p, encoding="utf-8").read()
            if neuf not in s:
                echecs.append(nom)
                print("   [!!] %-52s ⛔ MOTIF INTROUVABLE dans %s — le temoin"
                      " ⛔ NE S'APPLIQUE PAS, il ne prouve RIEN" % (nom[:52], fic))
                continue
            if s.count(neuf) != 1:
                echecs.append(nom)
                print("   [!!] %-52s ⛔ MOTIF vu %d fois dans %s — ⛔ un seul"
                      " site a la fois" % (nom[:52], s.count(neuf), fic))
                continue
            io.open(p, "w", encoding="utf-8").write(s.replace(neuf, vieux))
            etat, rc, sortie = joue_les_bancs(d, a.cockpit)
            rouges = sorted(k for k, v in etat.items() if not v)
            attrape = [b for b in vises if etat.get(b) is False]
            manques = [b for b in vises if etat.get(b) is not False]
            bon = not manques and rc == 1
            if not bon:
                echecs.append(nom)
            print("   [%s] %-52s" % ("OK" if bon else "!!", nom[:52]))
            print("        vise   : %s" % ", ".join(vises))
            print("        rougit : %s (rc=%d)" % (", ".join(rouges) or "aucun", rc))
            if manques:
                print("        ⛔ RESTE(NT) VERT(S) : %s — ⛔ le banc ne garde"
                      " pas ce qu'il annonce" % ", ".join(manques))
            elif set(rouges) - set(attrape):
                print("        ⚠️ rouges COLLATERAUX (declares, ⛔ pas tus) : %s"
                      % ", ".join(sorted(set(rouges) - set(attrape))))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("\n" + "=" * 78)
    print("BILAN TEMOINS : %d temoin(s), %d echec(s)" % (len(TEMOINS), len(echecs)))
    print("=" * 78)
    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(main())
