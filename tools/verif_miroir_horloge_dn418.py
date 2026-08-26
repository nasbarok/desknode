#!/usr/bin/env python3
"""
DeskNode — GATE MIROIR firmware ↔ agent (horloge).          (dn4-18, 2026-08-26)

🔴 POURQUOI CETTE GATE EXISTE, ET POURQUOI ELLE EST DIFFÉRENTE DES AUTRES
=========================================================================
L'agent lit l'état d'horloge de la carte en cherchant, sur le fil, des LITTÉRAUX
que le firmware imprime. Les deux tables sont donc **recopiées, pas dérivées** —
c'est déjà le risque assumé de `BORNES` ↔ `k_metriques[]` dans `dn_link.c`.

⚠️ MAIS LÀ-BAS, UNE DÉRIVE SE VOIT : `rejets_bornes` monte côté firmware.
🔴 ICI, **RIEN NE LA SIGNALERAIT.** Un libellé retouché — un accent, une
   majuscule, un espace — ferait retomber l'agent en `INCONNU` **EN SILENCE**.
   Et `INCONNU` ne déclenche aucune pose (AC3.2, et c'est voulu) : la barre
   resterait donc `--:--` **pour toujours**, sans une seule ligne d'erreur.

⇒ C'est exactement le mode de panne que cette story existe pour fermer. La gate
  est ce qui empêche la correction de se retourner contre elle-même.

🔴 ELLE VÉRIFIE LES DEUX SENS
=============================
1. **AGENT → FIRMWARE** : chaque littéral que l'agent cherche existe TEL QUEL
   dans `dn_console.c` ou `dn_rtc.c`.
2. **FIRMWARE → AGENT** : chaque état que `dn_rtc_etat_nom()` peut RENDRE est
   connu de la table de l'agent. ⇒ un état AJOUTÉ au firmware fait CRIER la
   gate, au lieu de faire retomber l'agent en `INCONNU` sans bruit.

⛔ Le sens n°2 est celui qu'une gate naïve oublie : elle vérifierait que ce
   qu'on cherche existe, ⛔ jamais que ce qui existe est cherché.

USAGE
=====
    python3 tools/verif_miroir_horloge_dn418.py
    python3 tools/verif_miroir_horloge_dn418.py --montrer-l-echec

⛔ `--montrer-l-echec` EST OBLIGATOIRE AVANT DE CROIRE LE VERT : « une gate
   jamais vue CRIER n'est pas une gate ». Précédent MESURÉ le 2026-08-26 : la
   gate CRLF de `deployer_tour.sh` regardait un `.cmd` **0/6 en CR** sans le voir.

Code de retour : 0 si le miroir tient, 1 sinon.
"""

import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "agent"))
os.environ.setdefault("DN_STUB_PSUTIL", "1")
sys.path.insert(0, os.path.join(RACINE, "tools", "stub_psutil"))

import dn_agent  # noqa: E402

SOURCES = [
    os.path.join(RACINE, "firmware", "desknode", "main", "dn_console.c"),
    os.path.join(RACINE, "firmware", "desknode", "main", "dn_rtc.c"),
]

# ⚠️ `dn_rtc_etat_nom()` a un `default: return "?"`. Ce n'est PAS un état : c'est
#    le refus d'en nommer un. L'agent le traite comme n'importe quel texte non
#    reconnu — donc `INCONNU`, ce qui est LA bonne conduite. On le déclare ici
#    pour que la gate ne le compte pas comme une dérive.
DEFAUT_NON_ETAT = {"?"}


def _sources():
    manquants = [p for p in SOURCES if not os.path.exists(p)]
    if manquants:
        print("ECHEC : source(s) firmware introuvable(s) :")
        for p in manquants:
            print("   ", p)
        return None
    return {p: open(p, "rb").read() for p in SOURCES}


def sens_agent_vers_firmware(src, injecter=None):
    """1/2 — chaque littéral CHERCHÉ par l'agent existe TEL QUEL dans le firmware."""
    a_verifier = []
    for brut in dn_agent.DN_H_ETATS:
        a_verifier.append(("etat", brut))
    for nom in ("DN_H_ANCRE_RTC", "DN_H_ANCRE_BARRE", "DN_H_ANCRE_OS",
                "DN_H_ANCRE_LUE", "DN_H_POSE_OK", "DN_H_POSE_ETAT",
                "DN_H_NON_AFFICHABLE"):
        a_verifier.append((nom, getattr(dn_agent, nom)))
    for motif in dn_agent.DN_H_POSE_REFUS:
        a_verifier.append(("DN_H_POSE_REFUS", motif))
    if injecter is not None:
        a_verifier.append(("INJECTE", injecter))

    ok = True
    for nom, litteral in a_verifier:
        ou = [os.path.basename(p) for p, t in src.items() if litteral in t]
        if ou:
            print("  ✅ %-18s %-36r -> %s" % (nom, litteral, ", ".join(ou)))
        else:
            ok = False
            print("  🔴 %-18s %-36r -> INTROUVABLE dans le firmware" % (nom, litteral))
            print("      ⇒ l'agent chercherait un texte que la carte n'imprime "
                  "PLUS. Il retomberait en INCONNU EN SILENCE, et la barre "
                  "resterait « --:-- » pour toujours.")
    return ok


def sens_firmware_vers_agent(src, injecter=None, vider=False):
    """2/2 — chaque état que le FIRMWARE peut rendre est CONNU de l'agent.

    ⛔ `injecter` / `vider` ne servent QU'À `--montrer-l-echec` : ils simulent
       respectivement un état AJOUTÉ au firmware et une table devenue
       ILLISIBLE. Correctif de revue 2026-08-26 : ce sens-ci était le seul des
       deux à n'avoir JAMAIS été vu crier, alors que la docstring le présente
       comme « celui qu'une gate naïve oublie ».
    """
    corps = None
    for p, t in src.items():
        if b"dn_rtc_etat_nom" in t:
            txt = t.decode("utf-8", "replace")
            i = txt.find("const char *dn_rtc_etat_nom")
            if i < 0:
                continue
            j = txt.find("\n}", i)
            corps = txt[i:j]
            break
    if corps is None:
        print("  🔴 `dn_rtc_etat_nom()` INTROUVABLE : la gate ne peut pas lire "
              "la liste des etats du firmware. ⛔ Un miroir qui ne voit qu'un "
              "cote n'est pas un miroir.")
        return False
    if vider:
        corps = "const char *dn_rtc_etat_nom(dn_rtc_etat_t e) { return k_noms[e];"
    rendus = set(re.findall(r'return\s+"([^"]*)"\s*;', corps)) - DEFAUT_NON_ETAT
    if injecter is not None:
        rendus.add(injecter)
    # 🔴 GARDE DE DISCRIMINANCE — CORRECTIF DE REVUE 2026-08-26. Sans elle, une
    #    réécriture de `dn_rtc_etat_nom()` en TABLE (`return k_noms[e];`) rendait
    #    `rendus` VIDE, donc `inconnus` vide, donc la gate imprimait
    #    « ✅ les 0 etats du firmware sont TOUS connus » et retournait VRAI.
    #    Une gate qui passe sur du VIDE ne prouve rien — c'est le même défaut
    #    que `temoin_decoupe` ferme déjà par son `exige = {...}`.
    if len(rendus) < 4:
        print("  🔴 SEULEMENT %d etat(s) EXTRAIT(S) de `dn_rtc_etat_nom()` "
              "(minimum attendu : 4)." % len(rendus))
        print("      ⇒ la gate ne lit PLUS la table du firmware — elle passerait "
              "sur du VIDE. ⛔ Un miroir qui ne reflete rien n'est pas vert, il "
              "est AVEUGLE.")
        return False
    connus = {k.decode("utf-8") for k in dn_agent.DN_H_ETATS}
    print("  firmware rend : %s" % ", ".join(sorted(repr(x) for x in rendus)))
    print("  agent connait : %s" % ", ".join(sorted(repr(x) for x in connus)))
    inconnus = rendus - connus
    if inconnus:
        print("  🔴 ETAT(S) RENDU(S) PAR LE FIRMWARE ET INCONNU(S) DE L'AGENT : %s"
              % ", ".join(sorted(repr(x) for x in inconnus)))
        print("      ⇒ l'agent les lirait comme INCONNU, donc ne poserait RIEN, "
              "SANS le dire.")
        return False
    # ⚠️ L'inverse n'est PAS une erreur : `NON ARMEE` est cherché par l'agent et
    #    n'est pas rendu par `dn_rtc_etat_nom()` — il vient de `dn_console.c`,
    #    qui l'imprime quand `dn_rtc_arme()` est faux. Le sens 1 l'a déjà couvert.
    print("  ✅ les %d etats du firmware sont TOUS connus de l'agent" % len(rendus))
    return True


def main():
    montrer = "--montrer-l-echec" in sys.argv[1:]
    src = _sources()
    if src is None:
        return 1

    if montrer:
        # 🔴 TROIS ECHECS PROVOQUES, ⛔ PAS UN. Correctif de revue 2026-08-26 :
        #    seul le sens 1 etait mis a l'epreuve, alors que le sens 2 est celui
        #    que la docstring presente comme le plus precieux.
        echecs = []

        print("=== 1/3 ⛔ SENS 1 — on injecte un litteral VOLONTAIREMENT FAUX ===")
        print("    (c'est ce que ferait un libelle firmware retouche d'un accent)")
        faux = b"horloge PCF85063A @ 0X"      # X majuscule : une seule lettre
        echecs.append(("sens 1, une seule lettre de difference",
                       sens_agent_vers_firmware(src, injecter=faux)))
        print()

        print("=== 2/3 ⛔ SENS 2 — le firmware GAGNE un etat que l'agent ignore ===")
        print("    (c'est ce que ferait un `DN_RTC_...` ajoute a l'enum)")
        echecs.append(("sens 2, etat firmware inconnu de l'agent",
                       sens_firmware_vers_agent(src, injecter="ARRETEE PAR L'HOTE")))
        print()

        print("=== 3/3 ⛔ SENS 2 — la table devient ILLISIBLE (passage en k_noms[]) ===")
        print("    (la gate doit CRIER, ⛔ pas annoncer « 0 etats, tous connus »)")
        echecs.append(("sens 2, table vide",
                       sens_firmware_vers_agent(src, vider=True)))
        print()

        muettes = [nom for nom, ok in echecs if ok]
        if muettes:
            for nom in muettes:
                print("🔴 LA GATE N'A PAS CRIE : %s" % nom)
            print("   ⛔ Une gate qui ne peut pas echouer ne prouve rien.")
            return 1
        print("✅ LA GATE A CRIE SUR LES TROIS — les DEUX sens sont discriminants.")
        print("   Elle peut donc etre crue quand elle est verte.")
        return 0

    print("=== GATE MIROIR firmware ↔ agent — horloge (dn4-18) ===")
    print()
    print("[1/2] AGENT -> FIRMWARE : ce que l'agent cherche existe-t-il ?")
    a = sens_agent_vers_firmware(src)
    print()
    print("[2/2] FIRMWARE -> AGENT : ce que la carte peut dire est-il connu ?")
    b = sens_firmware_vers_agent(src)
    print()
    if a and b:
        print("✅ LE MIROIR TIENT.")
        return 0
    print("🔴 LE MIROIR EST CASSE.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
