#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dn4-22 / AC5 — L'ETIQUETTE XIP NE PEUT PLUS MENTIR.

======================= CE QUE CET OUTIL FAIT, ET POURQUOI ==================

Le 2026-08-28, le bandeau de boot a annonce « XIP depuis la PSRAM DESACTIVE »
SUR UN BINAIRE OU XIP TOURNAIT. Il testait `CONFIG_SPIRAM_XIP_FROM_PSRAM` — le
symbole PARAPLUIE — alors que la configuration pose les DEUX SOUS-SYMBOLES
(`SPIRAM_FETCH_INSTRUCTIONS` / `SPIRAM_RODATA`), et sous IDF 5.5 poser les
enfants n'active PAS le parapluie.

⇒ UN `#if` SUR UN SYMBOLE QUE PERSONNE NE POSE NE PEUT IMPRIMER QUE SA BRANCHE
  `else`. C'est une etiquette qui ne peut pas dire la verite, jamais.

🔴 CE QUE CA A FAILLI COUTER : la seance a mesure XIP et allait publier
   « XIP ne change rien » sur la foi du bandeau. Seule la preuve d'EXECUTION
   (`mmu_psram: Instructions copied and mapped to SPIRAM`, dans le log de boot)
   a rattrape le coup. Et la meme etiquette etait deja en place quand `dn1-3` a
   REFUTE XIP (§11.4, ligne 6) — cette refutation est donc NON ETABLIE.

======================= LA PROPRIETE EPINGLEE ==============================

⛔ CETTE GATE NE RECITE AUCUNE VALEUR (AC5.4). Elle ne sait pas quels symboles
   XIP « devraient » etre poses : elle LIT les deux cotes et compare.

  1. Le bloc XIP du bandeau EXISTE, et il vit dans une fonction REELLEMENT
     APPELEE depuis `app_main` (⇒ la garde est ATTEIGNABLE, AC5.3).
  2. TOUT symbole `CONFIG_*` teste par ce bloc est un symbole que les fichiers
     de configuration du projet POSENT reellement. ⇒ un `#if` sur un symbole
     fantome est REFUSE.
  3. Les symboles XIP poses par `sdkconfig.defaults` et par la branche
     `sdkconfig.defaults.xip-lecture-code` sont LES MEMES ⇒ la branche d'essai
     et le defaut livre ne peuvent pas diverger en silence.
  4. Le bloc distingue les cas PARTIELS : les deux sous-symboles sont
     independants dans Kconfig, et « l'un sans l'autre » est un etat LEGAL qui
     serait invisible sur un test unique.

======================= ⛔ CE QU'ELLE NE COUVRE PAS =========================

⛔ Elle ne prouve PAS que XIP est arme A L'EXECUTION. Seul le log de boot le
   dit (`mmu_psram: ...`), et c'est une observation de CARTE.
⛔ Elle ne prouve PAS que XIP corrige le defaut — c'est §26 du dossier, et ca
   s'est mesure sur la dalle.
⛔ Elle ne verifie PAS les autres `#if` du bandeau (LCD_RGB_RESTART_IN_VSYNC,
   SPIRAM_MODE_OCT, SPIRAM_SPEED_*). Portee VOLONTAIREMENT etroite : le defaut
   trouve est celui-la. ⚠️ Le depot a deja paye « une gate scopee a UNE fonction
   epingle vert le meme defaut ailleurs » — c'est DECLARE, pas ignore.
⛔ Elle ne lit PAS `sdkconfig` (genere, gitignore) : elle lit les DEFAULTS, qui
   font autorite au depot.

Sortie : `N OK / M KO`, exit 0 si tout passe, 1 sinon.
Usage  : python3 tools/verif_xip_dn422.py [--mutant <1..4>]
         `--mutant` casse la propriete EN MEMOIRE et doit faire ROUGIR (AC5.2).
"""

import io
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FW = os.path.join(RACINE, "firmware", "desknode")
MAIN_C = os.path.join(FW, "main", "desknode_main.c")
DEFAULTS = os.path.join(FW, "sdkconfig.defaults")
BRANCHE = os.path.join(FW, "sdkconfig.defaults.xip-lecture-code")

OK = KO = 0


def dire(bon, titre, detail=""):
    global OK, KO
    if bon:
        OK += 1
        print(f"  [OK ] {titre}" + (f"  {detail}" if detail else ""))
    else:
        KO += 1
        print(f"  [KO ] {titre}" + (f"  {detail}" if detail else ""))


def lire(p):
    return io.open(p, encoding="utf-8").read()


def symboles_poses(texte):
    """Les CONFIG_* que ce fichier POSE (y compris a =n). ⛔ pas les commentaires."""
    out = set()
    for l in texte.splitlines():
        m = re.match(r"^\s*(CONFIG_[A-Z0-9_]+)\s*=", l)
        if m:
            out.add(m.group(1))
    return out


def bloc_xip(texte):
    """Le bloc de directives qui imprime l'etat XIP, ⛔ localise par son CONTENU."""
    lignes = texte.splitlines()
    idx = [i for i, l in enumerate(lignes) if "XIP depuis la PSRAM" in l]
    if not idx:
        return None, []
    # on remonte au `#if` qui ouvre, on descend au `#endif` qui ferme
    debut = idx[0]
    while debut > 0 and not lignes[debut].lstrip().startswith("#if"):
        debut -= 1
    fin = idx[-1]
    while fin < len(lignes) - 1 and not lignes[fin].lstrip().startswith("#endif"):
        fin += 1
    return "\n".join(lignes[debut:fin + 1]), lignes


def main():
    mutant = None
    if "--mutant" in sys.argv:
        mutant = int(sys.argv[sys.argv.index("--mutant") + 1])

    print("=" * 78)
    print("dn4-22 / AC5 — L'ETIQUETTE XIP NE PEUT PLUS MENTIR")
    if mutant:
        print(f"  🔬 MUTANT {mutant} ACTIF — cette gate DOIT rougir.")
    print("=" * 78)

    for p in (MAIN_C, DEFAULTS, BRANCHE):
        if not os.path.exists(p):
            print(f"  [KO ] fichier introuvable : {p}")
            print("BILAN : 0 OK / 1 KO")
            return 1

    src = lire(MAIN_C)
    txt_def = lire(DEFAULTS)
    txt_br = lire(BRANCHE)

    if mutant == 1:   # le bandeau re-teste le symbole PARAPLUIE (le defaut d'origine)
        src = src.replace("#if CONFIG_SPIRAM_FETCH_INSTRUCTIONS && CONFIG_SPIRAM_RODATA",
                          "#if CONFIG_SPIRAM_XIP_FROM_PSRAM")
    if mutant == 2:   # la config ne pose plus qu'un seul sous-symbole
        txt_def = re.sub(r"^CONFIG_SPIRAM_RODATA=y\s*$", "", txt_def, flags=re.M)
    if mutant == 3:   # la branche d'essai diverge du defaut livre
        txt_br = re.sub(r"^CONFIG_SPIRAM_RODATA=y\s*$", "", txt_br, flags=re.M)
    if mutant == 4:   # le bandeau ne distingue plus les cas PARTIELS
        src = src.replace("#elif CONFIG_SPIRAM_FETCH_INSTRUCTIONS", "#elif 0")

    print("\n── 1. LA GARDE EXISTE ET ELLE EST ATTEIGNABLE ──────────────────────")
    bloc, lignes = bloc_xip(src)
    dire(bloc is not None, "le bloc XIP du bandeau existe (localise par son CONTENU)")
    if bloc is None:
        print(f"\nBILAN : {OK} OK / {KO} KO")
        return 1

    m_fn = re.search(r"static void (\w+)\(void\)\s*\{", src[:src.index(bloc)][::-1][::-1])
    fonctions = [m.group(1) for m in re.finditer(r"^static void (\w+)\(void\)", src, re.M)]
    porteuse = None
    for f in fonctions:
        d = src.index(f"static void {f}(void)")
        if d < src.index(bloc):
            porteuse = f
    dire(porteuse is not None, "le bloc vit dans une fonction nommee", f"⇒ `{porteuse}()`")
    appelee = porteuse and re.search(rf"^\s*{porteuse}\(\);", src, re.M)
    dire(bool(appelee),
         "…et cette fonction est REELLEMENT APPELEE dans ce fichier",
         "⛔ une garde jamais atteinte n'est pas une garde")

    print("\n── 2. AUCUN `#if` SUR UN SYMBOLE FANTOME ───────────────────────────")
    testes = set(re.findall(r"CONFIG_[A-Z0-9_]+", bloc))
    poses = symboles_poses(txt_def) | symboles_poses(txt_br)
    fantomes = sorted(testes - poses)
    dire(len(testes) > 0, "le bloc teste au moins un symbole", f"⇒ {sorted(testes)}")
    dire(not fantomes,
         "TOUT symbole teste est POSE par la configuration du projet",
         f"⛔ fantome(s) : {fantomes}" if fantomes else
         "⇒ l'etiquette PEUT dire la verite")

    print("\n── 3. LA BRANCHE D'ESSAI ET LE DEFAUT LIVRE NE DIVERGENT PAS ───────")
    xip_def = {s for s in symboles_poses(txt_def) if "SPIRAM_FETCH" in s or "SPIRAM_RODATA" in s
               or "SPIRAM_XIP" in s}
    xip_br = {s for s in symboles_poses(txt_br) if "SPIRAM_FETCH" in s or "SPIRAM_RODATA" in s
              or "SPIRAM_XIP" in s}
    dire(bool(xip_def), "`sdkconfig.defaults` pose des symboles XIP", f"⇒ {sorted(xip_def)}")
    dire(xip_def == xip_br,
         "…et la branche `xip-lecture-code` pose EXACTEMENT LES MEMES",
         f"⛔ ecart : {sorted(xip_def ^ xip_br)}" if xip_def != xip_br else "")
    dire(testes >= xip_def,
         "…et le bandeau teste TOUS ceux que la config pose",
         f"⛔ non testes : {sorted(xip_def - testes)}" if not (testes >= xip_def) else "")

    print("\n── 4. LES CAS PARTIELS SONT DISTINGUES ─────────────────────────────")
    # 🔴 DURCIE LE 2026-08-28 — LE MUTANT 4 NE LA FAISAIT PAS ROUGIR. La version
    #    d'avant COMPTAIT les branches (>= 3) ; remplacer `#elif CONFIG_X` par
    #    `#elif 0` laissait le compte INCHANGE et la gate VERTE, alors que le cas
    #    partiel « X sans Y » etait devenu invisible. ⛔ Compter n'est pas verifier.
    # ⇒ ON EXIGE, POUR CHAQUE symbole XIP pose, UNE BRANCHE QUI L'ISOLE : une
    #   condition qui le mentionne LUI et PAS l'autre. C'est la seule forme qui
    #   rende l'etat « l'un sans l'autre » lisible au bandeau.
    conditions = re.findall(r"^\s*#(?:if|elif)\s+(.+)$", bloc, re.M)
    for sym in sorted(xip_def):
        autres = xip_def - {sym}
        isolante = [c for c in conditions
                    if sym in c and not any(a in c for a in autres)]
        dire(bool(isolante),
             f"une branche ISOLE `{sym}`",
             f"⇒ « {isolante[0].strip()} »" if isolante
             else "⛔ le cas « lui sans l'autre » serait INVISIBLE au bandeau")

    print("\n" + "=" * 78)
    print(f"BILAN : {OK} OK / {KO} KO")
    print("=" * 78)
    return 0 if KO == 0 else 1


sys.exit(main())
