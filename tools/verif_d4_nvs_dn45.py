#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dn4-5 / AC9 — D4 EST **VERIFIE**, ⛔ PAS AFFIRME : AUCUNE ECRITURE NVS/FLASH EN
REGIME.

======================= CE QUE CET OUTIL FAIT, ET POURQUOI ==================

D4 interdit toute ecriture flash/NVS **en regime**, et une semaine H24 est tres
exactement le regime ou une ecriture periodique se paierait — mesure : sous
ecriture flash, *« l'image defile »*, a **165 343 o/s**.

🔴 L'INSTRUMENT QUI EXISTAIT NE COUVRAIT QU'UN SEUL ECRIVAIN. La commande
   `veille` publie « aucune ecriture NVS depuis le boot ou le dernier
   `veille reset` » — mais elle ne connait que `dn_veille`. Un verdict fonde sur
   elle seule serait **LOCAL**, pas global : *« une gate scopee a UNE fonction
   peut epingler VERT le meme defaut ailleurs »*.

⇒ CETTE GATE BALAIE **TOUT** `firmware/desknode/main/` a la recherche des
  primitives d'ecriture, et confronte a une table ou **chaque ecrivain declare
  son DECLENCHEUR**. Elle echoue si :
    · un ecrivain apparait sans etre classe (⇒ un chemin d'ecriture neuf) ;
    · une entree de table ne correspond plus a rien (⇒ table perimee) ;
    · un ecrivain est classe « REGIME » (⇒ D4 est viole).

⚠️ CE QU'ELLE NE PROUVE PAS, et c'est ecrit : que rien n'a ete ecrit PENDANT le
   soak. Elle prouve que **les seuls chemins d'ecriture qui existent** sont hors
   regime. La verification de terrain est AC9.1 — relire `veille` a la fin du
   soak, sur la carte.

Sortie : exit 0 si tout passe, 1 sinon.
"""

import hashlib
import io
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(RACINE, "firmware", "desknode", "main")

# 🔴 `nvs_flash_erase` AJOUTEE LE 2026-08-28 (revue de code). Elle MANQUAIT, et
#    l'omission etait invisible parce qu'elle ressemble aux autres : ni
#    "nvs_erase" ni "esp_flash_erase" n'est une SOUS-CHAINE de "nvs_flash_erase"
#    (verifie : `[p for p in PRIMITIVES if p in "nvs_flash_erase"]` rendait []).
#    ⇒ `desknode_main.c` effacait LA PARTITION NVS ENTIERE sans que l'inventaire
#      d'AC9.2 le voie, et le dossier publiait « balayage sur les SEPT
#      primitives » avec 3 ecrivains au lieu de 4 fichiers.
#    ⚠️ LA SUBSTANCE DE D4 TENAIT : ce chemin est un `nvs_flash_init()` en ECHEC
#      AU BOOT, donc hors regime. Ce qui etait en defaut, c'est L'INVENTAIRE —
#      et un inventaire incomplet rend le verdict d'AC9.1 LOCAL, pas global.
#      C'est exactement ce qu'AC9.2 interdit.
PRIMITIVES = ["nvs_set_", "nvs_commit", "nvs_erase", "nvs_flash_erase",
              "esp_partition_write", "esp_partition_erase", "esp_flash_write",
              "esp_flash_erase"]

# ── LA TABLE : ecrivain -> (regime ?, declencheur) ──────────────────────────
#    « REGIME » ferait echouer la gate. Aucun ne doit l'etre.
ECRIVAINS = {
    "dn_bootcfg.c": (
        "HORS REGIME",
        "console UNIQUEMENT (`set fbs|bounce|lines|drawmem|core`, `cfg reset`, "
        "et `cfg repli clear` -> `dn_bootcfg_clear_repli()` : ce dernier a ete "
        "AJOUTE APRES dn4-5 et le dossier ne le nommait pas — trouve en revue le "
        "2026-08-28) — ET UN CHEMIN DE BOOT, nomme plutot que tu : "
        "desknode_main.c corrige la NVS quand `bounce_px` NE S'ALLOUE PAS "
        "(repli dn4-10 du 2026-08-23). "
        "⚠️ Ce chemin est CONDITIONNEL, il tombe AVANT que le regime commence, "
        "et il s'auto-eteint (le boot suivant est propre). "
        "⚠️ LE COMPTE PUBLIE PAR LE DOSSIER ETAIT 4 APPELS : il y en a 16 au "
        "HEAD. Le COMPTE avait derive, ⛔ pas le VERDICT — aucun chemin de "
        "REGIME n'a ete introduit"),
    "desknode_main.c": (
        "HORS REGIME",
        "`nvs_flash_erase()` — efface la partition NVS ENTIERE, temoin compris. "
        "Declencheur : `nvs_flash_init()` qui rend NO_FREE_PAGES ou "
        "NEW_VERSION_FOUND AU BOOT (desknode_main.c:267). ⛔ Il tombe AVANT que "
        "le regime commence, et il ne peut pas se rejouer sans un nouveau boot. "
        "🔴 CE SITE EXISTAIT DEJA A `c31bb97` : ⛔ ce n'est PAS une regression "
        "post-dn4-5, c'est un ANGLE MORT de la gate, trouve en revue le "
        "2026-08-28 (la primitive `nvs_flash_erase` n'etait pas cherchee)"),
    "dn_stimulus.c": (
        "HORS REGIME",
        "`esp_partition_write` du STIMULUS flash, arme par la commande "
        "`flash on` UNIQUEMENT. ⛔ C'est l'instrument qui MESURE le cout d'une "
        "ecriture flash — il ne tourne jamais tout seul"),
    "dn_veille.c": (
        "HORS REGIME",
        "persistance des DEUX reglages de veille (delai, armee), declenchee par "
        "un GESTE (tap MENU ou commande `veille`). ⛔ Un soak sans-les-mains "
        "n'en produit aucune. ✅ Et c'est le seul ecrivain INSTRUMENTE : "
        "`veille` publie son compteur d'ecritures depuis le boot"),
}

ok_total = [0]
ko_total = [0]


def ctrl(ok, libelle, detail=""):
    if ok:
        ok_total[0] += 1
        print("  [OK ] %-56s %s" % (libelle, detail))
    else:
        ko_total[0] += 1
        print("  [KO ] %-56s %s" % (libelle, detail))
    return ok


def sans_commentaires(txt):
    """Blanchit les commentaires ET LES LITTERAUX DE CHAINE.

    🔴 LES CHAINES ONT ETE AJOUTEES LE 2026-08-28 (revue de code), ET C'EST LA
       GATE ELLE-MEME QUI L'A EXIGE. En ajoutant `nvs_flash_erase` aux
       primitives, le balayage a classe `dn_console.c` comme ECRIVAIN — alors
       que ses deux seules occurrences sont (a) un `printf(...)` qui EXPLIQUE a
       l'operateur ce qu'est un `nvs_flash_erase()` au boot (dn_console.c:503)
       et (b) un commentaire. ⛔ Une gate qui prend une MENTION TEXTUELLE pour un
       APPEL accuse du code sain, et sur ce depot le precedent inverse est deja
       paye : « une gate verte sur du code faux ». Les deux fautes ont la meme
       racine — un balayage qui lit du TEXTE la ou il croit lire du CODE.
    ⚠️ Les sequences d'echappement sont traitees : `"\\""` ne ferme pas la chaine.
    """
    out, i, n = [], 0, len(txt)
    while i < n:
        c = txt[i]
        if c == '/' and i + 1 < n and txt[i + 1] == '*':
            j = txt.find('*/', i + 2)
            j = n if j < 0 else j + 2
            out.append(re.sub(r'[^\n]', ' ', txt[i:j]))
            i = j
        elif c == '/' and i + 1 < n and txt[i + 1] == '/':
            j = txt.find('\n', i)
            j = n if j < 0 else j
            out.append(' ' * (j - i))
            i = j
        elif c == '"' or c == "'":
            # ⛔ LE CONTENU D'UNE CHAINE N'EST PAS DU CODE. On garde les
            #    delimiteurs et les sauts de ligne (les numeros de ligne et le
            #    hash de forme restent lisibles), on blanchit l'interieur.
            fin = c
            out.append(c)
            i += 1
            while i < n:
                if txt[i] == '\\' and i + 1 < n:
                    out.append('  ' if txt[i + 1] != '\n' else ' \n')
                    i += 2
                    continue
                if txt[i] == fin:
                    out.append(fin)
                    i += 1
                    break
                out.append('\n' if txt[i] == '\n' else ' ')
                i += 1
        else:
            out.append(c)
            i += 1
    return ''.join(out)


def main():
    print("=" * 78)
    print("dn4-5 / AC9 — D4 : AUCUNE ECRITURE NVS/FLASH EN REGIME")
    print("=" * 78)
    fichiers = sorted(f for f in os.listdir(MAIN) if f.endswith(".c"))
    h = hashlib.sha256()
    for f in fichiers:
        h.update(open(os.path.join(MAIN, f), "rb").read())
    print("\nperimetre : %d fichiers .c — sha256 : %s"
          % (len(fichiers), h.hexdigest()[:16]))
    print("primitives cherchees : %s" % " · ".join(PRIMITIVES))

    print("\n── 1. LE BALAYAGE, SUR TOUT `main/` ──────────────────────────────")
    trouves = {}
    for f in fichiers:
        # ⛔ SUR LE TEXTE DEPOUSSIERE : ce depot CITE `nvs_set_i32` dans des
        #    commentaires, et compter une citation comme un chemin d'ecriture
        #    ferait accuser un fichier qui n'ecrit rien.
        nu = sans_commentaires(io.open(os.path.join(MAIN, f), encoding="utf-8").read())
        n = sum(nu.count(p) for p in PRIMITIVES)
        if n:
            trouves[f] = n
    ctrl(bool(trouves), "des ecrivains sont trouves",
         "%d fichier(s) : %s" % (len(trouves), ", ".join(sorted(trouves))))

    print("\n── 2. CHAQUE ECRIVAIN DECLARE SON DECLENCHEUR ────────────────────")
    inconnus = sorted(set(trouves) - set(ECRIVAINS))
    perimes = sorted(set(ECRIVAINS) - set(trouves))
    ctrl(not inconnus, "aucun ecrivain NON CLASSE",
         "⛔ NOUVEAUX : %s" % inconnus if inconnus else "%d classes" % len(trouves))
    ctrl(not perimes, "aucune entree de table perimee",
         "⛔ n'ecrivent plus : %s" % perimes if perimes else "table a jour")
    for f in sorted(trouves):
        cl, motif = ECRIVAINS.get(f, ("?", "⛔ NON CLASSE"))
        marque = "✅" if cl == "HORS REGIME" else "🔴"
        print("   %s %-16s %-12s %d appel(s)" % (marque, f, cl, trouves[f]))
        print("       ↳ " + motif)
    en_regime = [f for f in trouves if ECRIVAINS.get(f, ("?",))[0] != "HORS REGIME"]
    ctrl(not en_regime, "⛔ AUCUN ecrivain n'est classe « REGIME »",
         "🔴 %s" % en_regime if en_regime else "D4 tient sur les %d chemins"
         % len(trouves))

    print("\n── 3. L'INSTRUMENT D'AC9.1 EXISTE ET IL EST NOMME ────────────────")
    cons = io.open(os.path.join(MAIN, "dn_console.c"), encoding="utf-8").read()
    ctrl("aucune ecriture NVS" in cons.replace("é", "e"),
         "`veille` publie son compteur d'ecritures NVS",
         "c'est l'instrument a relire A LA FIN DU SOAK (AC9.1)")
    ctrl("EN RAM" in cons and "AUCUNE" in cons,
         "`hist` declare rester EN RAM (AC9.3)",
         "l'historique de session ne survit pas au reboot, et c'est VOULU")

    print("\n── 4. CE QUE CETTE GATE NE PROUVE PAS ────────────────────────────")
    print("   ⛔ Que rien n'a ete ecrit PENDANT le soak. Elle prouve que les")
    print("      seuls chemins d'ecriture QUI EXISTENT sont hors regime.")
    print("   ⇒ La verification de terrain est AC9.1 : relire `veille` a la fin")
    print("      du soak, SUR LA CARTE.")

    print("\n" + "=" * 78)
    print("BILAN : %d OK, %d KO" % (ok_total[0], ko_total[0]))
    print("=" * 78)
    return 1 if ko_total[0] else 0


if __name__ == "__main__":
    sys.exit(main())
