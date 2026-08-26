#!/usr/bin/env python3
"""
DeskNode — ÉPREUVE FONCTIONNELLE de la reprise d'horloge.   (dn4-18, 2026-08-26)

🔴 CE QU'ELLE PROUVE
====================
Neuf scènes, une par conduite que la story EXIGE, jouées sur le **vrai**
`ReprisHorloge` et le **vrai** `SortieSerie.commande_console()`, avec un port
de papier qui rend des **réponses de carte RÉELLES** (reprises des captures de
séance du 2026-08-26).

⛔ CE N'EST PAS UN SIMULATEUR DE CARTE. Le port de papier ne décide rien : il
   rend les octets qu'on lui donne et enregistre ce que l'agent écrit. Toutes
   les décisions testées sont prises par le code livré.

⚠️ UNE SEULE VALEUR EST SYNTHÉTISÉE, ET ON LE DIT : l'heure décalée d'une heure
   de la scène « été/hiver ». Ce cas-là n'arrive que **deux fois par an** ; on
   ne pouvait pas le capturer. ⇒ le FORMAT vient d'une réponse réelle, seule la
   valeur du champ `lue` est réécrite. ⛔ Aucun autre octet n'est inventé.

USAGE
=====
    python3 tools/verif_reprise_horloge_dn418.py
    python3 tools/verif_reprise_horloge_dn418.py --montrer-l-echec

Code de retour : 0 si les neuf scènes tiennent, 1 sinon.
"""

import os
import re
import sys
import time

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "agent"))
os.environ.setdefault("DN_STUB_PSUTIL", "1")
sys.path.insert(0, os.path.join(RACINE, "tools", "stub_psutil"))

import dn_agent  # noqa: E402

MESURES = os.path.join(RACINE, "mesures", "dn4-18")


# ── LES RÉPONSES DE CARTE, REPRISES DES CAPTURES DE SÉANCE ───────────────────
def _extraire(chemin, debut, fin_apres):
    brut = open(chemin, "rb").read()
    i = brut.find(debut)
    if i < 0:
        raise SystemExit("ECHEC : %r absent de %s" % (debut, chemin))
    j = brut.find(fin_apres, i)
    if j < 0:
        raise SystemExit("ECHEC : fin %r absente de %s" % (fin_apres, chemin))
    return brut[i:j + len(fin_apres)]


def reponse_os1():
    """La réponse RÉELLE de `rtc` sur une carte qui a PERDU l'heure (T1, 13:25)."""
    return _extraire(os.path.join(MESURES, "T1-rtc-etat-depart.log"),
                     b"horloge PCF85063A @ 0x51 : NON FIABLE (OS=1)",
                     b"epoque     : 2000..2099") + b"\r\ndesknode> "


def reponse_os0():
    """La réponse RÉELLE de `rtc` sur une carte à l'heure (côté TOUR, 13:47)."""
    return _extraire(os.path.join(MESURES, "AC1-2-pose-cote-tour-windows.log"),
                     b"horloge PCF85063A @ 0x51 : FIABLE",
                     b"epoque     : 2000..2099") + b"\r\ndesknode> "


def reponse_pose_ok():
    """La réponse RÉELLE de `rtc set` acceptée (côté TOUR, 13:47)."""
    return _extraire(os.path.join(MESURES, "AC1-2-pose-cote-tour-windows.log"),
                     b"heure posee : ", b"a l'heure reelle") + b"\r\ndesknode> "


def a_l_heure(reponse, decalage_s=0):
    """Réécrit le champ `lue` pour qu'il colle à l'horloge de l'hôte (+ décalage).

    ⚠️ C'EST LA SEULE FABRICATION DE CE FICHIER, et elle est bornée à un champ.
       Sans elle, la scène « la carte est à l'heure » testerait un écart de
       plusieurs heures — donc l'inverse de ce qu'elle prétend tester.
    """
    lt = time.localtime(time.time() + decalage_s)
    txt = "%04d-%02d-%02d %02d:%02d:%02d" % (
        lt.tm_year, lt.tm_mon, lt.tm_mday, lt.tm_hour, lt.tm_min, lt.tm_sec)
    return re.sub(rb"lue        : \d{4}-\d\d-\d\d \d\d:\d\d:\d\d",
                  b"lue        : " + txt.encode("ascii"), reponse)


REFUS_FIRMWARE = (b"\xf0\x9f\x94\xb4 ECRITURE REFUSEE ou OS RESTE A 1 "
                  b"\xe2\x80\x94 la pose n'a PAS pris.\r\n"
                  b"Command returned non-zero error code: 0x103 (ESP_FAIL)\r\n"
                  b"desknode> ")
NON_ARMEE = (b"horloge PCF85063A @ 0x51 : NON ARMEE\r\n"
             b"  le device I2C n'existe pas : soit le bus etait absent au boot,\r\n"
             b"  \xe2\x87\x92 la barre affiche \xc2\xab --:-- HEURE NON POSEE \xc2\xbb, "
             b"et c'est CORRECT.\r\ndesknode> ")
BRUIT = (b"desknode> pc $DN,3,1,1032,cpu,118,32,250,433*54\r\n"
         b"I (474367) desknode: up 470 s \xe2\x80\x94 vsync=17627\r\ndesknode> ")


class PortDeScene:
    """Un port série de papier. ⛔ Il ne DÉCIDE rien : il rend ce qu'on lui donne
    et note ce que l'agent écrit."""

    def __init__(self):
        self.ecrits = []
        self.a_rendre = []

    @property
    def in_waiting(self):
        return len(self.a_rendre[0]) if self.a_rendre else 0

    def read(self, n):
        if not self.a_rendre or n <= 0:
            return b""
        return self.a_rendre.pop(0)

    def write(self, octets):
        self.ecrits.append(octets)
        return len(octets)

    def flush(self):
        pass

    def close(self):
        pass


class Scene:
    """Le montage : le VRAI `SortieSerie`, le VRAI `ReprisHorloge`, un port de papier."""

    def __init__(self):
        self.port = PortDeScene()
        self.sortie = dn_agent.SortieSerie("PORT_DE_SCENE")
        self.sortie._con = self.port
        self.horloge = dn_agent.ReprisHorloge(self.sortie)
        self.t = 10000.0

    def repondre(self, octets):
        self.port.a_rendre.append(octets)

    def cycle(self, avance_s=1.0):
        """Un tour de la boucle de `principal()`, dans le MÊME ordre.

        🔴 LES TRAMES D'ABORD, ET CE N'EST PAS UN DÉTAIL DE MISE EN SCÈNE :
           `_drainer()` n'est appelé QUE depuis `envoyer()` (après une écriture
           réussie) et depuis `fermer()`. C'est donc l'émission des trames qui
           fait entrer le fil dans le lecteur. Une scène qui appellerait
           `horloge.cycle()` toute seule testerait un agent qui n'existe pas —
           et elle serait VERTE sur un mécanisme MORT.
        """
        self.t += avance_s
        self.seq = getattr(self, "seq", 0) + 1
        self.sortie.envoyer(dn_agent.trame(self.seq, int(self.t * 1000) & 0xFFFFFFFF,
                                           "cpu", [118, 32, 250, 433]))
        self.horloge.cycle(self.t)

    def commandes(self):
        """Ce que l'agent a écrit SUR LE CANAL CONSOLE — ⛔ pas ses trames.

        C'est aussi un contrôle d'AC2.4 : les trames partent avec le préfixe
        `pc ` (dialecte des trames), les commandes console SANS. Si une
        commande console sortait préfixée, elle apparaîtrait ici et le filtre
        la ferait disparaître ⇒ les scènes crieraient.
        """
        return [b.decode("ascii", "replace").strip() for b in self.port.ecrits
                if not b.startswith(b"pc ")]

    def derniere_commande(self):
        c = self.commandes()
        return c[-1] if c else None

    def cycle_repondeur(self, table, avance_s=1.0):
        """Un cycle, puis la carte ne répond QU'AUX commandes reçues.

        ⛔ CE N'EST TOUJOURS PAS UN SIMULATEUR : `table` est un dictionnaire de
           réponses CANONIQUES, servies telles quelles. Mais c'est ce qui rend
           un COÛT CONSOLE mesurable — une scène qui déverse une réponse à
           chaque cycle mesurerait le bruit de la SCÈNE, ⛔ pas celui de
           l'agent. (défaut attrapé sur la scène 5, 2026-08-26)
        """
        n = len(self.commandes())
        self.cycle(avance_s)
        for c in self.commandes()[n:]:
            cle = "rtc set" if c.startswith("rtc set ") else c
            if cle in table:
                self.repondre(table[cle])


def _dire(ok, texte):
    print("  %s %s" % ("✅" if ok else "🔴", texte))
    return ok


# ── LES NEUF SCÈNES ─────────────────────────────────────────────────────────
def scene_1_perte_puis_pose():
    """AC4.1 + AC4.2 + AC4.5 — la carte a perdu l'heure, l'agent la repose."""
    s = Scene()
    s.sortie.reprise_liaison = True          # ouverture du port (AC4.2)
    s.cycle()
    ok = _dire(s.derniere_commande() == "rtc",
               "reprise de liaison ⇒ l'agent INTERROGE (« %s »)"
               % s.derniere_commande())
    s.repondre(reponse_os1())
    s.cycle()
    ok &= _dire(s.sortie.horloge.etat == "OS1",
                "la reponse OS=1 est LUE ⇒ etat « %s »" % s.sortie.horloge.etat)
    cmd = s.derniere_commande()
    ok &= _dire(cmd is not None and cmd.startswith("rtc set "),
                "⇒ l'agent POSE l'heure (« %s »)" % cmd)
    ok &= _dire(re.fullmatch(r"rtc set \d{4}-\d\d-\d\d \d\d:\d\d:\d\d", cmd or "")
                is not None,
                "…au format HEURE LOCALE DECOMPOSEE (⛔ pas un epoch UTC)")
    s.repondre(reponse_pose_ok())
    s.cycle()
    h = s.horloge
    ok &= _dire(h.poses_tentees == 1 and h.poses_reussies == 1
                and h.poses_refusees == 0 and h.poses_sans_reponse == 0,
                "le verdict de la CARTE est lu : %d tentee / %d reussie / "
                "%d refusee / %d sans reponse"
                % (h.poses_tentees, h.poses_reussies, h.poses_refusees,
                   h.poses_sans_reponse))
    ok &= _dire(s.sortie.horloge.etat == "OS0",
                "et l'etat qui suit la pose est LU sur la reponse ⇒ « %s »"
                % s.sortie.horloge.etat)
    ok &= _dire(s.sortie.commandes_console == 2 and s.sortie.echo_octets > 0,
                "%d commande(s) console, ⛔ HORS trames (%d o d'echo draines)"
                % (s.sortie.commandes_console, s.sortie.echo_octets))
    return ok


def scene_2_fiable_pas_de_pose():
    """AC4.6 — ⛔ AUCUNE pose quand la carte dit FIABLE et qu'elle est à l'heure."""
    s = Scene()
    s.sortie.reprise_liaison = True
    s.cycle()
    s.repondre(a_l_heure(reponse_os0()))
    for _ in range(30):
        s.cycle()
    return (_dire(s.sortie.horloge.etat == "OS0", "carte FIABLE et a l'heure")
            and _dire(s.horloge.poses_tentees == 0,
                      "⇒ 0 pose tentee en 30 cycles (%d)" % s.horloge.poses_tentees))


def scene_3_non_armee_terminal():
    """AC3.3 — `NON ARMEE` est TERMINAL : ⛔ jamais de boucle de réessai."""
    s = Scene()
    s.sortie.reprise_liaison = True
    s.cycle()
    s.repondre(NON_ARMEE)
    s.cycle()
    ok = _dire(s.sortie.horloge.etat == "NON_ARMEE",
               "etat lu « %s »" % s.sortie.horloge.etat)
    avant = len(s.commandes())
    for _ in range(50):
        s.sortie.reprise_liaison = True      # le port bat : 50 reprises !
        s.cycle(avance_s=60.0)               # et 50 minutes passent
    ok &= _dire(len(s.commandes()) == avant,
                "⇒ 0 commande console de plus apres 50 reprises et 50 min (%d)"
                % (len(s.commandes()) - avant))
    ok &= _dire(s.horloge.poses_tentees == 0, "⇒ 0 pose tentee")
    return ok


def scene_4_inconnu_ne_pose_pas():
    """AC3.2 — `INCONNU` n'est ⛔ NI `OS0` NI `OS1` : on ne pose pas, et on ne
    conclut pas que tout va bien."""
    s = Scene()
    s.sortie.reprise_liaison = True
    s.cycle()
    s.repondre(BRUIT)                        # du fil, mais rien d'horloge dedans
    for _ in range(20):
        s.cycle()
    return (_dire(s.sortie.horloge.etat == "INCONNU",
                  "rien de reconnu sur le fil ⇒ etat « %s »" % s.sortie.horloge.etat)
            and _dire(s.horloge.poses_tentees == 0,
                      "⇒ 0 pose (⛔ INCONNU n'est pas OS=1)")
            and _dire(s.sortie.horloge.etats_lus == 0,
                      "⇒ 0 etat lu (⛔ INCONNU n'est pas OS=0 non plus)"))


def scene_5_anti_rafale():
    """AC4.3 — un refus en boucle ne doit PAS noyer le fil.

    🔴 C'EST LE PIRE CAS QUE LA STORY NOMME : « `rtc set` refusé en boucle à
       5 essais/s ⇒ plusieurs Ko/s injectés dans le flux console », c'est-à-dire
       le NOYAGE de `echo_octets` — l'instrument d'AC3 de dn2-2, sur le fil qui
       EST le transport des cinq métriques.
    """
    # La carte ne répond QU'AUX commandes reçues, et elle refuse TOUJOURS.
    table = {"rtc": reponse_os1(), "rtc set": REFUS_FIRMWARE}
    s = Scene()
    s.sortie.reprise_liaison = True
    s.cycle_repondeur(table)                  # ⇒ `rtc`
    s.cycle_repondeur(table)                  # ⇒ OS=1 lu, 1re pose
    s.cycle_repondeur(table)                  # ⇒ refus lu
    ok = _dire(s.horloge.poses_refusees == 1,
               "1er refus compte (%d), motif(s) %s"
               % (s.horloge.poses_refusees, list(s.horloge.motifs_refus)))
    n, m = s.horloge.poses_tentees, s.horloge.interrogations
    for _ in range(55):                       # 55 s de plus, carte toujours OS=1
        s.cycle_repondeur(table)
    ok &= _dire(s.horloge.poses_tentees == n,
                "⇒ AUCUNE nouvelle tentative pendant 55 s (%d)"
                % (s.horloge.poses_tentees - n))
    ok &= _dire(s.horloge.interrogations == m,
                "⇒ ET AUCUNE nouvelle interrogation non plus (%d) — le palier "
                "gouverne les DEUX, sinon le fil serait noye de `rtc`"
                % (s.horloge.interrogations - m))
    s.cycle_repondeur(table, avance_s=10.0)   # on franchit le palier de 60 s
    ok &= _dire(s.horloge.interrogations == m + 1,
                "⇒ apres le palier de %.0f s, l'agent RELIT d'abord l'etat"
                % dn_agent.DN_H_BACKOFF_S)
    s.cycle_repondeur(table)
    ok &= _dire(s.horloge.poses_tentees == n + 1,
                "⇒ puis retente UNE fois, sur une lecture FRAICHE (%d)"
                % (s.horloge.poses_tentees - n))
    s.cycle_repondeur(table)
    ok &= _dire(s.horloge.prochaine_pose - s.t >= dn_agent.DN_H_BACKOFF_S * 2 - 2,
                "⇒ le 2e refus DOUBLE le palier (%.0f s)"
                % (s.horloge.prochaine_pose - s.t))
    # ⛔ LE PIRE CAS, CHIFFRÉ, ET SUR LE FIL RÉEL : la carte ne parle QUE quand
    #    on l'interroge, donc `echo_octets` ne compte plus que ce que ce
    #    mécanisme a RÉELLEMENT provoqué.
    duree = s.t - 10000.0
    cout = s.sortie.echo_octets / max(duree, 1e-6)
    ok &= _dire(cout < 100.0,
                "⇒ cout console PROVOQUE par le mecanisme : %.1f o/s sur %.0f s "
                "en refus PERMANENT (⛔ pas « plusieurs Ko/s » ; le bruit de "
                "regime mesure vaut 272,9 o/s)" % (cout, duree))
    return ok


def scene_6_ete_hiver():
    """AC6 — la carte dit FIABLE, et elle a UNE HEURE de retard."""
    s = Scene()
    s.sortie.reprise_liaison = True
    s.cycle()
    s.repondre(a_l_heure(reponse_os0(), decalage_s=3600))
    s.cycle()
    lect = s.sortie.horloge
    ok = _dire(lect.etat == "OS0",
               "la carte se declare « %s » — ⛔ elle ne SAIT PAS qu'elle a tort"
               % lect.etat_texte)
    ok &= _dire(abs(lect.lue_ecart_s - 3600) <= 2,
                "l'ecart mesure vaut %+d s (attendu +3600 ± 2)" % lect.lue_ecart_s)
    cmd = s.derniere_commande()
    ok &= _dire(cmd is not None and cmd.startswith("rtc set "),
                "⇒ la pose est DECLENCHEE malgre OS=0 (« %s »)" % cmd)
    ok &= _dire(any("ecart" in m for m in s.horloge.motifs_pose),
                "⇒ et le motif publie est l'ECART : %s"
                % list(s.horloge.motifs_pose))
    # ⛔ Et le seuil ne doit PAS confondre la derive avec un fuseau.
    s2 = Scene()
    s2.sortie.reprise_liaison = True
    s2.cycle()
    s2.repondre(a_l_heure(reponse_os0(), decalage_s=24))   # 1 jour de derive MAX
    for _ in range(10):
        s2.cycle()
    ok &= _dire(s2.horloge.poses_tentees == 0,
                "⇒ mais 24 s (la derive d'UN JOUR au pire) ne declenchent RIEN")
    return ok


def scene_7_plancher():
    """AC4.3 — le PLANCHER borne le coût console quand le port bat."""
    s = Scene()
    for _ in range(20):
        s.sortie.reprise_liaison = True       # une reprise par seconde !
        s.cycle()
    return _dire(s.horloge.interrogations == 1,
                 "20 reprises de liaison en 20 s ⇒ %d interrogation "
                 "(plancher %.0f s)"
                 % (s.horloge.interrogations, dn_agent.DN_H_PLANCHER_S))


def scene_8_sans_reponse():
    """AC5.1 — « pas de réponse » est un TROISIÈME seau, ⛔ ni succès ni refus."""
    s = Scene()
    s.sortie.reprise_liaison = True
    s.cycle()
    s.repondre(reponse_os1())
    s.cycle()                                  # ⇒ pose envoyee
    for _ in range(15):
        s.cycle()                              # …et la carte ne repond JAMAIS
    h = s.horloge
    return (_dire(h.poses_sans_reponse == 1,
                  "%d pose(s) SANS REPONSE apres %.0f s"
                  % (h.poses_sans_reponse, dn_agent.DN_H_ATTENTE_VERDICT_S))
            and _dire(h.poses_reussies == 0 and h.poses_refusees == 0,
                      "⇒ et elle n'est comptee ⛔ NI en reussite ⛔ NI en refus"))


def scene_9_pas_de_canal():
    """AC2.4 — sur stdout, l'absence de canal est un ÉTAT DÉCLARÉ."""
    h = dn_agent.ReprisHorloge(dn_agent.SortieStdout())
    ok = _dire(h.actif is False, "branche stdout ⇒ reprise DESARMEE")
    try:
        for _ in range(5):
            h.cycle(1.0)
        ok &= _dire(True, "⇒ 5 cycles sans AttributeError et sans rien emettre")
    except Exception as exc:
        ok &= _dire(False, "⇒ EXCEPTION : %r" % exc)
    ok &= _dire(getattr(dn_agent.SortieWebSocket, "canal_console", None) is False,
                "et la branche websocket declare aussi son absence de canal")
    return ok


SCENES = [
    ("1 — la carte a perdu l'heure, l'agent la repose  (AC4.1/4.2/4.5)", scene_1_perte_puis_pose),
    ("2 — carte FIABLE et a l'heure ⇒ AUCUNE pose      (AC4.6)", scene_2_fiable_pas_de_pose),
    ("3 — NON ARMEE est TERMINAL                       (AC3.3)", scene_3_non_armee_terminal),
    ("4 — INCONNU n'est ni OS0 ni OS1                  (AC3.2)", scene_4_inconnu_ne_pose_pas),
    ("5 — un refus en boucle ne noie pas le fil        (AC4.3)", scene_5_anti_rafale),
    ("6 — le trou ETE/HIVER                            (AC6)", scene_6_ete_hiver),
    ("7 — le plancher borne le port qui bat            (AC4.3)", scene_7_plancher),
    ("8 — « sans reponse » est un 3e seau              (AC5.1)", scene_8_sans_reponse),
    ("9 — pas de canal console = etat DECLARE          (AC2.4)", scene_9_pas_de_canal),
]


def main():
    if "--montrer-l-echec" in sys.argv[1:]:
        print("=== ⛔ ECHEC PROVOQUE — on retire le PLANCHER de l'anti-rafale ===")
        print("    DN_H_PLANCHER_S : %.0f -> 0" % dn_agent.DN_H_PLANCHER_S)
        print("    (c'est ce que ferait une « simplification » : le plancher est")
        print("     le seul rempart quand le port BAT, et son absence ne se voit")
        print("     PAS en regime — seulement le jour ou le cable est douteux)")
        print()
        print("⚠️ ET UNE PREMIERE INJECTION N'A PAS SUFFI, C'EST UN FAIT MESURE :")
        print("   casser DN_H_ETATS[b'NON FIABLE (OS=1)'] ne casse PAS la scene 1,")
        print("   parce que l'etat a DEUX sources INDEPENDANTES dans la meme")
        print("   reponse — la ligne `horloge … : ETAT` et la ligne `bit OS : 1`.")
        print("   ⇒ c'est une redondance REELLE du mecanisme, ⛔ pas un trou du")
        print("     temoin. La gate MIROIR, elle, attrape ce cas-la statiquement.")
        dn_agent.DN_H_PLANCHER_S = 0.0
        print()
        crie = []
        for titre, fn in SCENES:
            print("[scene %s]" % titre)
            if not fn():
                crie.append(titre.split("—")[0].strip())
            print()
        if not crie:
            print("🔴 L'EPREUVE N'A PAS CRIE ALORS QU'ON A CASSE L'ANTI-RAFALE.")
            print("   ⛔ Une epreuve qui ne peut pas echouer ne prouve rien.")
            return 1
        print("✅ L'EPREUVE A CRIE — scene(s) %s." % ", ".join(crie))
        print("   Elle peut donc etre crue quand elle est verte.")
        return 0

    print("=== EPREUVE FONCTIONNELLE — reprise d'horloge (dn4-18) ===")
    tout = True
    for titre, fn in SCENES:
        print()
        print("[scene %s]" % titre)
        tout &= bool(fn())
    print()
    if tout:
        print("✅ LES NEUF SCENES TIENNENT.")
        return 0
    print("🔴 AU MOINS UNE SCENE A ECHOUE.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
