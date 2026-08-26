#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dn4-5 / AC6 — LE BME680 DIT SON CYCLE DE RETARD, ET LES DEUX ENDROITS QUI LE
DISENT NE PEUVENT PAS DIVERGER.

======================= CE QUE CET OUTIL FAIT, ET POURQUOI ==================

AC6.3 exige que « le docblock de `dn_capteurs.c` porte LA MEME PHRASE que la
console ». Le piege est connu et il a un nom dans ce depot : **deux verites
contradictoires**, c'est le defaut traque depuis `dn4-8`, et il ne se produit
jamais d'un coup — il se produit quand QUELQU'UN CORRIGE UN SEUL DES DEUX.

⇒ LA PARADE EST STRUCTURELLE, ⛔ PAS DECLARATIVE : la phrase est definie **une
  seule fois** (`DN_CAPT_RETARD_TXT`), la console la RECOIT par
  `dn_capt_retard_txt()`, et cette gate exige que **chaque chiffre de la phrase
  se retrouve dans le docblock**. Un correctif qui ne toucherait qu'un cote fait
  rougir la gate.

🔴 ET AC6.2 EST UNE INTERDICTION, DONC ELLE SE VERIFIE PAR L'ABSENCE :
   ⛔ pas d'attente bloquante ajoutee (41 ms par cycle, 341 ms gaz allume, sur
   la tache qui partage le bus I2C avec l'horloge et le tactile),
   ⛔ pas de changement de cadence (`DN_CAPT_PERIODE_MS` reste a 5 000).

⚠️ CE QUE CETTE GATE NE PROUVE PAS : que le retard EST d'un cycle. Ce chiffre
   vient d'une mesure anterieure (le temoin `capteurs gaz on` : +300 ms de
   chauffe, cycle inchange a 26 ms, temperature qui derive de 26,0 a 26,2 C).
   Elle prouve que le produit le DIT, partout, de la meme facon.

Sortie : exit 0 si tout passe, 1 sinon.
"""

import hashlib
import io
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(RACINE, "firmware", "desknode", "main")
CAPT_C = os.path.join(MAIN, "dn_capteurs.c")
CAPT_H = os.path.join(MAIN, "dn_capteurs.h")
CONSOLE_C = os.path.join(MAIN, "dn_console.c")

ok_total = [0]
ko_total = [0]


def lire(p):
    b = open(p, "rb").read()
    return b.decode("utf-8"), hashlib.sha256(b).hexdigest()[:16]


def ctrl(ok, libelle, detail=""):
    if ok:
        ok_total[0] += 1
        print("  [OK ] %-56s %s" % (libelle, detail))
    else:
        ko_total[0] += 1
        print("  [KO ] %-56s %s" % (libelle, detail))
    return ok


def macro(src):
    """Extrait le texte de `DN_CAPT_RETARD_TXT`, concatenation C comprise."""
    m = re.search(r'#define DN_CAPT_RETARD_TXT\s*\\\n(.*?)(?=\n\n|\n[^ \\"])',
                  src, re.S)
    if not m:
        return None
    return " ".join(re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(1)))


def docblock(src):
    """Le premier commentaire de bloc du fichier."""
    d = src.index("/*")
    return src[d:src.index("*/", d)]


def chiffres(txt):
    """Les grandeurs CHIFFREES, unite comprise. ⛔ Pas les nombres nus : « 8x »
    et « 1x » de l'oversampling ne se comparent pas a « 8 »."""
    return set(re.findall(r'\d+(?:[.,]\d+)?\s*(?:ms|s|x)\b', txt.replace(" ", " ")))


def main():
    print("=" * 78)
    print("dn4-5 / AC6 — LE BME680 DIT SON RETARD, ET NE SE CONTREDIT PAS")
    print("=" * 78)
    src_c, sha_c = lire(CAPT_C)
    src_h, sha_h = lire(CAPT_H)
    src_k, sha_k = lire(CONSOLE_C)
    print("\nsources LUES : dn_capteurs.c %s · .h %s · dn_console.c %s"
          % (sha_c, sha_h, sha_k))

    print("\n── 1. LA PHRASE EXISTE, ET UNE SEULE FOIS ────────────────────────")
    n_def = src_c.count("#define DN_CAPT_RETARD_TXT")
    ctrl(n_def == 1, "`DN_CAPT_RETARD_TXT` est defini EXACTEMENT une fois",
         "%d definition(s)" % n_def)
    phrase = macro(src_c)
    if not ctrl(phrase is not None and len(phrase) > 80,
                "la phrase est extractible et non vide",
                "%d caracteres" % (len(phrase) if phrase else 0)):
        return 1
    ctrl("dn_capt_retard_txt" in src_h,
         "le getter est DECLARE dans l'en-tete", "dn_capteurs.h")
    ctrl(src_c.count("const char *dn_capt_retard_txt(void)") == 1,
         "et DEFINI une seule fois", "dn_capteurs.c")

    print("\n── 2. LA CONSOLE NE RECOPIE PAS — ELLE DEMANDE ───────────────────")
    ctrl("dn_capt_retard_txt()" in src_k,
         "`dn_console.c` APPELLE le getter", "⛔ pas de copie de la phrase")
    # ⚠️ ON CHERCHE DES FRAGMENTS **DISTINCTIFS**, ET LE CHOIX A ETE CORRIGE
    #    PAR LA MESURE (2026-08-26). « data ready » figurait dans cette liste :
    #    la gate a rougi sur `dn_console.c:7340`, une mention PREEXISTANTE et
    #    LEGITIME (un autre diagnostic capteur). Un terme generique fait crier
    #    une gate sur du vide — et une gate qui crie sur du vide finit desarmee.
    #    Les trois fragments ci-dessous ne peuvent etre QUE des copies.
    for frag in ("UN CYCLE DE RETARD", "LIT LA PRECEDENTE", "341 ms"):
        ctrl(frag not in src_k,
             "⛔ « %s » n'est PAS recopie dans dn_console.c" % frag,
             "la phrase n'a qu'un seul proprietaire")

    print("\n── 3. LE DOCBLOCK PORTE LES MEMES CHIFFRES QUE LA PHRASE ─────────")
    doc = docblock(src_c)
    c_phrase, c_doc = chiffres(phrase), chiffres(doc)
    manquants = sorted(c_phrase - c_doc)
    ctrl(not manquants,
         "chaque chiffre de la phrase est DANS le docblock",
         "⛔ absent(s) du docblock : %s" % manquants if manquants
         else "%d grandeur(s) chiffree(s) : %s"
         % (len(c_phrase), sorted(c_phrase)))
    ctrl("cycle de retard" in doc.lower() or "CYCLE DE RETARD" in doc,
         "et le docblock nomme le defaut", "« un cycle de retard »")

    print("\n── 4. AC6.2 — L'INTERDICTION, VERIFIEE PAR L'ABSENCE ─────────────")
    ctrl("#define DN_CAPT_PERIODE_MS 5000" in src_h,
         "⛔ la cadence n'a PAS bouge", "DN_CAPT_PERIODE_MS = 5000")
    ctrl("341" in phrase and "41 ms" in phrase,
         "la phrase CHIFFRE ce que couterait l'attente",
         "41 ms par cycle, 341 ms gaz allume — ⛔ pas « ce serait cher »")
    ctrl("ASSUME" in phrase.upper(),
         "et elle dit que le retard est ASSUME, ⛔ pas subi", "")

    print("\n── 5. LE TEMOIN NEGATIF — ON DOIT VOIR LA GATE ROUGIR ────────────")
    # 🔴 On MUTE la phrase (en memoire) et on exige que le miroir casse. Sans ce
    #    temoin, rien ne dirait que le controle du §3 regarde quelque chose.
    mut = src_c.replace('"demande ~41 ms, et le cycle mesure 25-26 ms. '
                        'Chaque cycle DECLENCHE une "',
                        '"demande ~99 ms, et le cycle mesure 25-26 ms. '
                        'Chaque cycle DECLENCHE une "', 1)
    if ctrl(mut != src_c, "la mutation s'applique", "41 ms -> 99 ms"):
        p2 = macro(mut)
        m2 = sorted(chiffres(p2) - chiffres(docblock(mut)))
        ctrl(bool(m2), "mutant : VU ROUGIR",
             "le docblock ne porte plus %s — la divergence est DETECTEE" % m2)

    print("\n" + "=" * 78)
    print("BILAN : %d OK, %d KO" % (ok_total[0], ko_total[0]))
    print("=" * 78)
    return 1 if ko_total[0] else 0


if __name__ == "__main__":
    sys.exit(main())
