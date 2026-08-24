#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""campagne_bruit_dn48.py — chaque cas de bruit sur SON compteur, diff avant/apres.

🔴 CE QU'IL VERIFIE, ET C'EST PLUS DUR QUE « le compteur attendu a monte » :
   pour chaque trame injectee, le compteur ATTENDU monte de 1 **ET TOUS LES
   AUTRES RESTENT A ZERO**. Un cas qui incremente deux compteurs, ou le mauvais,
   est un ECHEC — meme si « le bon » a monte.
⚠️ Motif : « tronquee » et « trop longue » sont des diagnostics CONTRAIRES, et le
   depot a deja eu les deux dans le MEME seau. Un compteur qui compte autre chose
   que ce que son nom dit est la classe de defaut que ce depot traque.

🔴 ET SON PARSEUR SE PROUVE SUR UNE LIGNE FABRIQUEE AVANT D'ETRE CRU. Gratter
   au `grep` une console redigee pour un humain FABRIQUE des nombres plausibles :
   un motif qui ne matche plus rend « 0 » au lieu de lever, et tous les deltas
   deviennent nuls — la campagne conclurait « aucun compteur n'a bouge » sur une
   carte qui repond parfaitement. ⇒ auto-test EN TETE, ⛔ pas en option.

Usage :  python3 tools/campagne_bruit_dn48.py
Sortie : 0 si les N cas tombent chacun dans SON compteur, 1 sinon.
"""
import os
import re
import sys
import time

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "tools"))
import dn_console  # noqa: E402

COMPTEURS = ("tronquee", "trop longue", "checksum", "version", "format", "bornes")
_LIGNE_REJ = re.compile(
    r"^rejets\s*:\s*tronquee\s+(\d+)\s*\u00b7\s*trop longue\s+(\d+)\s*\u00b7\s*"
    r"checksum\s+(\d+)\s*\u00b7\s*version\s+(\d+)\s*\u00b7\s*format\s+(\d+)\s*"
    r"\u00b7\s*bornes\s+(\d+)\s*$", re.M)


def ck(corps):
    x = 0
    for o in corps.encode("ascii"):
        x ^= o
    return "%02X" % x


def trame(ver, seq, t, met, vals, ck_faux=False, sans_ck=False):
    """⚠️ `vals` peut contenir `None` (champ VIDE) — c'est le point de plusieurs cas."""
    corps = "DN,%d,%d,%d,%s," % (ver, seq, t, met) + ",".join(
        "" if v is None else str(v) for v in vals)
    if sans_ck:
        return "$" + corps
    if not ck_faux:
        return "$" + corps + "*" + ck(corps)
    # 🔴 GARDE ANTI-COLLISION (revue dn4-8, 2026-08-21). Le faux checksum etait
    #    force a "00" EN DUR : quand le checksum REEL de la trame vaut lui-meme
    #    00, la trame est VALIDE, aucun compteur ne bouge, et le cas « checksum
    #    FAUX » est signale en ECHEC alors que le firmware a eu RAISON.
    # ⚠️ Le jumeau `dn_injecteur.py:264-266` garde exactement cette collision avec
    #    un repli "11". Deux outils du meme depot, sur le meme piege, un seul
    #    protege : c'est la classe « garde scopee a un endroit ».
    vrai = ck(corps)
    return "$" + corps + "*" + ("11" if vrai == "00" else "00")


def cases_pc(ligne):
    """Decoupe une ligne `pc` de metrique en SES GRANDEURS, par POSITION.

    🔴 MIROIR EXACT DU FORMAT DE `dn_console.c:2664` :
         "  %-5s -> case %d %-9s %-12s"   puis, par grandeur,
         " %d,%d %s"  ou  " -- (<unite> ATTENDUE, non publiee par la source)",
         separees par " \u00b7", et une QUEUE "  \u00b7 age %lld ms \u00b7 seq %u".

    ⚠️ ECRIT APRES UN ECHEC D'INSTRUMENT, LE 2026-08-21, SUR LA CARTE. La
       premiere version faisait `ligne.split("->")[-1].split("\u00b7")` en supposant
       que les valeurs suivaient la fleche. Elles ne suivent pas : il y a
       `case <n> <NOM> <ETAT>` entre les deux. Resultat : les trois controles de
       position ont ete declares EN ECHEC alors que la carte affichait
       EXACTEMENT l'attendu. ⛔ Un instrument faux accuse le sujet sain.
    ⚠️ La queue `age`/`seq` n'est PAS une grandeur : la garder decalerait tout
       raisonnement sur « combien de grandeurs la ligne porte ».

    Rend `None` si la ligne ne se parse pas — ⛔ JAMAIS un decoupage douteux
    qu'un appelant prendrait pour un verdict.
    """
    m = re.search(r"->\s+case\s+-?\d+\s", ligne)
    if not m:
        return None
    bouts = re.split(r"\s{2,}", ligne[m.end():].strip(), maxsplit=2)
    if len(bouts) != 3:              # <NOM> <ETAT> <valeurs...>
        return None
    cases = [c.strip() for c in bouts[2].split("\u00b7")]
    # ⛔ on JETTE la queue de diagnostic, on ne la compte pas comme grandeur
    cases = [c for c in cases
             if c and not c.startswith("age ") and not c.startswith("seq ")]
    if not cases:
        return None
    # 🎯 VALIDATION : la 1re case DOIT ressembler a une grandeur. Sinon le
    #    decoupage a rate et on le DIT, ⛔ on ne rend pas des chaines au hasard.
    # 🔴 2e REVUE (2026-08-24) : `re.match` ANCRE AU DEBUT, donc cette validation
    #    aurait rendu `None` D'EMBLEE le jour ou une grandeur d'INDEX 0 recevrait
    #    un prefixe d'ecran. ⇒ on cherche le motif OU QU'IL SOIT dans la case.
    if not _VALEUR.search(cases[0]):
        return None
    return cases


# 🔴 LE PREFIXE D'ECRAN N'EXISTAIT PAS QUAND CE FICHIER A ETE ECRIT — ET IL A
#    CASSE LES DEUX TEMOINS v3 (2e revue, 2026-08-24). `dn4-9` a pose les
#    prefixes (`extr.moy` / `ventirad` / `boitier` sur `disk`, `c.max` sur `cpu`)
#    et `dn_console.c:2843` les IMPRIME :
#        printf(" %s%s%d,%d %s", px ? px : "", px ? " " : "", ...)
#    avec `px = dn_ui_case_prefixe(idx, g)`, qui passe `detail = true` et rend
#    donc AUSSI les `prefixe_detail_seul`. Les assertions comparaient le NOMBRE
#    NU (`startswith("800,0 tr/min")`) : les deux temoins v3 et le cas AC7
#    « champ VIDE en position INTERNE » sortaient ✖️ SUR UNE CARTE QUI AFFICHAIT
#    EXACTEMENT L'ATTENDU. ⛔ Un instrument faux accuse le sujet sain — le defaut
#    meme que le commit `1d0227c` dit fermer.
# ⚠️ `dn_console.c:2822` NOMMAIT deja ce fichier comme lecteur de la console.
_VALEUR = re.compile(r"(-?\d+,\d|--)")


def _prefixe(case):
    """La partie AVANT la valeur — `""` s'il n'y en a pas. ⛔ Jamais `None`."""
    m = _VALEUR.search(case or "")
    return (case[:m.start()].strip() if m else "")


def _valeur(case):
    """La case SANS son prefixe d'ecran. ⛔ Rend `None` si rien ne ressemble a
    une grandeur : un decoupage rate est un ECHEC D'INSTRUMENT, pas un verdict.
    """
    m = _VALEUR.search(case or "")
    return case[m.start():] if m else None


def _extraire(txt):
    """Rend le dict des six compteurs. \u26d4 LEVE si le motif ne matche pas."""
    m = _LIGNE_REJ.search(txt)
    if not m:
        raise RuntimeError(
            "la ligne `rejets :` n'a pas ete trouvee dans la sortie de `pc`. "
            "\u26d4 REFUS DE RENDRE DES ZEROS : un parseur permissif ferait "
            "conclure « aucun compteur n'a bouge » sur une carte qui repond.")
    return dict(zip(COMPTEURS, (int(g) for g in m.groups())))


def autotest():
    """\U0001f534 LE PARSEUR SE PROUVE SUR UNE LIGNE FABRIQUEE, ⛔ pas sur la carte."""
    faux = ("liaison PC : VIVANTE\n"
            "rejets     : tronquee 3 \u00b7 trop longue 1 \u00b7 checksum 4 \u00b7 "
            "version 1 \u00b7 format 5 \u00b7 bornes 9\n"
            "latence ...\n")
    got = _extraire(faux)
    att = {"tronquee": 3, "trop longue": 1, "checksum": 4, "version": 1,
           "format": 5, "bornes": 9}
    if got != att:
        sys.exit("\u26d4 AUTO-TEST DU PARSEUR ECHOUE : %s != %s" % (got, att))
    # Et il doit LEVER sur une ligne qui ne contient pas ce qu'il cherche.
    try:
        _extraire("liaison PC : VIVANTE\nrien ici\n")
    except RuntimeError:
        pass
    else:
        sys.exit("\u26d4 AUTO-TEST : le parseur a rendu quelque chose sur une "
                 "sortie SANS ligne `rejets` — il ne peut pas voir le defaut "
                 "qu'il pretend exclure.")
    # 🔴 2e REVUE (2026-08-24) — LE DECOUPAGE DES CASES SE PROUVE AUSSI, ET SUR
    #    LE FORMAT **DE HEAD**, PREFIXES COMPRIS. C'est ce controle qui manquait :
    #    `dn4-9` a ajoute les prefixes d'ecran a `pc`, les assertions comparaient
    #    le nombre nu, et les deux temoins v3 sortaient ✖️ sur une carte SAINE.
    #    Ces deux lignes sont FABRIQUEES au format que `dn_console.c` produit a
    #    HEAD — ⛔ pas relevees sur la carte, pour que l'auto-test tourne partout.
    for etiq, ligne, att_px, att_v in (
        ("disk", "  disk  -> case 4 DISQUE    VIVANTE      480,0 Mo/s \u00b7 "
                 "extr.moy -- (tr/min ATTENDUE, non publiee par la source) \u00b7 "
                 "ventirad 800,0 tr/min \u00b7 boitier 1400,0 tr/min  \u00b7 age 12 ms "
                 "\u00b7 seq 7",
         ["", "extr.moy", "ventirad", "boitier"],
         ["480,0 Mo/s", "--", "800,0 tr/min", "1400,0 tr/min"]),
        ("cpu", "  cpu   -> case 0 CPU       VIVANTE      52,0 % \u00b7 3,2 GHz \u00b7 "
                "c.max 88,0 % \u00b7 -- (\u00b0C ATTENDUE, non publiee par la source)"
                "  \u00b7 age 12 ms \u00b7 seq 8",
         ["", "", "c.max", ""],
         ["52,0 %", "3,2 GHz", "88,0 %", "--"]),
    ):
        cs = cases_pc(ligne)
        if cs is None or len(cs) != 4:
            sys.exit("\u26d4 AUTO-TEST : `cases_pc` ne decoupe pas la ligne `%s` du "
                     "format de HEAD (rendu : %r)" % (etiq, cs))
        px = [_prefixe(c) for c in cs]
        vl = [_valeur(c) for c in cs]
        if px != att_px:
            sys.exit("\u26d4 AUTO-TEST : prefixes `%s` = %r, attendu %r" % (etiq, px, att_px))
        if any(v is None or not v.startswith(a) for v, a in zip(vl, att_v)):
            sys.exit("\u26d4 AUTO-TEST : valeurs `%s` = %r, attendu %r" % (etiq, vl, att_v))
    # ⛔ ET IL DOIT REFUSER un decoupage douteux, sinon il rendrait des chaines au
    #    hasard qu'un appelant prendrait pour un verdict.
    if cases_pc("  cpu   -> case 0 CPU  VIVANTE  rien qui ressemble a une valeur") is not None:
        sys.exit("\u26d4 AUTO-TEST : `cases_pc` a accepte une ligne SANS grandeur.")
    print("  [OK ] auto-test du parseur : il lit une ligne FABRIQUEE, il separe "
          "PREFIXE et VALEUR au format de HEAD, et il LEVE quand la ligne manque")


def _cmd(ser, c):
    """⚠️ `envoyer()` rend un DICT, ⛔ pas une chaine — et son timeout est
       EXPLICITE. Un wrapper local plutot que dix appels a trois arguments."""
    return dn_console.envoyer(ser, c, 5.0)["sortie"]


def lire_compteurs(ser):
    return _extraire(_cmd(ser, "pc"))


def main():
    for f in (sys.stdout, sys.stderr):
        try:
            f.reconfigure(encoding="utf-8")
        except Exception:
            pass
    print("=" * 92)
    print("dn4-8 / AC7 — CAMPAGNE DE BRUIT : chaque cas sur SON compteur, diff avant/apres")
    print("=" * 92)
    autotest()

    # \u26a0\ufe0f Les trames sont construites ICI, et leur LONGUEUR est verifiee avant
    #    le tir pour le cas « trop longue » : un cas qui ne tomberait pas dans la
    #    bande 72..124 mesurerait autre chose que son nom.
    CAS = [
        ("version hors [1..3]",
         lambda s, t: trame(9, s, t, "cpu", [520]), "version"),
        ("ver=1 a 7 champs (v1 n'en connait que 6)",
         lambda s, t: trame(1, s, t, "cpu", [520, 320]), "format"),
        ("ver=2 a 9 champs (champ EN TROP)",
         lambda s, t: trame(2, s, t, "cpu", [520, 320, 880, 410]), "format"),
        ("plus de valeurs que la metrique n'en publie (ram=2)",
         lambda s, t: trame(3, s, t, "ram", [660, 340, 100, 200]), "format"),
        ("NOUVELLE grandeur hors plafond : cpu degC 1600 > 1500",
         lambda s, t: trame(3, s, t, "cpu", [520, 320, 880, 1600]), "bornes"),
        ("NOUVELLE grandeur hors plafond : disk tr/min 999999 > 100000",
         lambda s, t: trame(3, s, t, "disk", [4800, 999999, 8000, 14000]), "bornes"),
        ("ligne COMPLETE dans la bande 72..124",
         lambda s, t: trame(3, 4294967295, 4294967295, "disk",
                            [1000000, 100000, 100000, 100000, 100000, 100000]),
         "trop longue"),
        ("ligne SANS *CK",
         lambda s, t: trame(3, s, t, "cpu", [520], sans_ck=True), "tronquee"),
        ("checksum FAUX",
         lambda s, t: trame(3, s, t, "cpu", [520], ck_faux=True), "checksum"),
        ("champ VIDE en position 0",
         lambda s, t: trame(3, s, t, "cpu", [None, 320, 880, 410]), "format"),
        # 🔴 CE CAS MANQUAIT, ET C'EST UNE LIGNE DU TABLEAU D'AC7 (revue du
        #    2026-08-21). La campagne portait DEUX cas « hors plafond » et AUCUN
        #    « champ vide en position INTERNE », alors que story et doc annoncent
        #    « 10 cas » couvrant cette ligne. Elle n'avait ete fermee que par une
        #    LECTURE HUMAINE d'un dump `pc`, donc un re-tir aurait affiche 10/10
        #    sans jamais l'eprouver.
        # ⛔ ET SA FORME DE VERDICT EST DIFFERENTE : ici on attend qu'AUCUN
        #    compteur ne bouge (la trame est ACCEPTEE) **ET** que la valeur
        #    suivante ne soit PAS DECALEE. `ok = bouges == {attendu: 1}` ne peut
        #    pas exprimer ca — d'ou `attendu = None` + un controle sur `pc`.
        ("champ VIDE en position INTERNE (ACCEPTEE, suivante NON decalee)",
         lambda s, t: trame(3, s, t, "disk", [4800, None, 8000, 14000]),
         None),
    ]

    ser = dn_console.ouvrir(dn_console.DEFAULT_PORT, dn_console.DEFAULT_BAUD)
    echecs = []
    try:
        dn_console.reveiller(ser)
        _cmd(ser, "pc reset")
        seq = 1000
        for nom, fab, attendu in CAS:
            seq += 1
            ligne = fab(seq, seq * 10)
            avant = lire_compteurs(ser)
            _cmd(ser, "pc " + ligne)
            time.sleep(0.15)
            apres = lire_compteurs(ser)
            delta = {k: apres[k] - avant[k] for k in COMPTEURS}
            bouges = {k: v for k, v in delta.items() if v}
            n = len(ligne)
            info = "%3d o" % n
            detail = ""

            if attendu is None:
                # 🔴 CAS « ACCEPTEE » : aucun compteur ne doit bouger, ET la valeur
                #    suivante ne doit PAS etre decalee. Le second membre se LIT sur
                #    `pc` — un decalage ne fait bouger AUCUN compteur, donc les
                #    compteurs seuls ne peuvent pas le voir. (revue 2026-08-21)
                vue_cas = _cmd(ser, "pc")
                mligne = re.search(r"^\s*disk\s+->.*$", vue_cas, re.M)
                ligne_disk = mligne.group(0) if mligne else ""
                # `dn_console` separe les grandeurs par « · » (dn_console.c:2684).
                #   attendu : 480,0 Mo/s · -- (...) · 800,0 tr/min · 1400,0 tr/min
                # ⚠️ ON DECOUPE PAR POSITION, ⛔ on ne cherche pas les nombres en
                #    vrac : « la valeur suivante n'est pas decalee » est une
                #    propriete de POSITION, et un `in` sur toute la ligne serait
                #    vrai meme si la valeur avait glisse d'un cran.
                cases = cases_pc(ligne_disk) or []
                def _case(i):
                    return cases[i] if i < len(cases) else ""
                # ⚠️ ON COMPARE LA VALEUR **SANS** LE PREFIXE D'ECRAN, et on
                #    verifie le prefixe SEPAREMENT : les deux sont de
                #    l'information, et les melanger a fait sortir ✖️ sur une
                #    carte saine (2e revue). ⛔ `_valeur` rend `None` si le
                #    decoupage rate — un `startswith` sur `None` leverait, donc
                #    on le teste.
                _v = [_valeur(_case(i)) for i in range(4)]
                _px = [_prefixe(_case(i)) for i in range(4)]
                ok = ((not bouges) and len(cases) == 4
                      and all(x is not None for x in _v)
                      and _v[0].startswith("480,0 Mo/s")
                      and _v[1].startswith("--")
                      and _v[2].startswith("800,0 tr/min")
                      and _v[3].startswith("1400,0 tr/min")
                      # 🎯 LE PREFIXE EST UNE PROPRIETE A PART ENTIERE : c'est lui
                      #    qui NOMME quel ventilateur est muet (dn4-9). Un
                      #    prefixe qui glisserait d'un cran serait un defaut, et
                      #    sans ce controle il passerait inapercu.
                      and _px[1:] == ["extr.moy", "ventirad", "boitier"])
                detail = ("  |  %s" % (ligne_disk.strip() or
                                       "\u26d4 ligne `disk` INTROUVABLE dans `pc`"))
                etiq = "ACCEPTEE"
            else:
                ok = bouges == {attendu: 1}
                etiq = attendu
                if attendu == "trop longue":
                    # 🔴 LA BANDE EST DESORMAIS ASSERTEE, ⛔ PLUS DECORATIVE.
                    #    L'en-tete promet qu'elle est « verifiee AVANT le tir » ;
                    #    elle etait calculee APRES et n'entrait jamais dans `ok`.
                    #    Un cas sorti de la bande mesurerait autre chose que son
                    #    nom, et l'outil imprimait `NON` en concluant `[OK ]`.
                    dans_bande = 72 <= n <= 124
                    info += "  (bande 72..124 : %s)" % ("oui" if dans_bande else "NON")
                    if not dans_bande:
                        detail = ("  ⛔ HORS BANDE : ce cas ne mesure PAS ce que "
                                  "son nom dit")
                    ok = ok and dans_bande

            print("  [%s] %-52s -> %-11s %s %s%s"
                  % ("OK " if ok else "\u2716\ufe0f ", nom, etiq, info,
                     "" if ok else "  \u26d4 OBSERVE : %s" % (bouges or "AUCUN"),
                     detail))
            if not ok:
                echecs.append(nom)

        # \U0001f3af LE TEMOIN v1 : l'agent de dn2-2, NON MODIFIE, doit rester VALIDE.
        print()
        avant = lire_compteurs(ser)
        _cmd(ser, "pc $DN,1,42,123456,cpu,153*47")
        time.sleep(0.15)
        apres = lire_compteurs(ser)
        delta = {k: apres[k] - avant[k] for k in COMPTEURS}
        vue = _cmd(ser, "pc")
        vivante = "cpu   -> case 0 CPU       VIVANTE" in vue
        ok = not any(delta.values()) and vivante
        print("  [%s] TEMOIN v1 (agent dn2-2 NON MODIFIE) : 6 champs, `cpu` seul"
              % ("OK " if ok else "\u2716\ufe0f "))
        print("        rejets_version = 0 et la case CPU est VIVANTE  ->  %s"
              % ("oui" if ok else "NON : delta=%s vivante=%s" % (delta, vivante)))
        if not ok:
            echecs.append("temoin v1")

        # 🔴 LE TEMOIN v3 — AC5 L'EXIGEAIT, IL N'AVAIT JAMAIS ETE TIRE.
        #    Ecrit le 2026-08-21 apres la revue de code. AC5 demandait que le
        #    temoin v3 soit « soit RE-QUALIFIE, soit RETIRE explicitement, ⛔ jamais
        #    laisse vert par inadvertance sur une semantique qui a change ». La
        #    campagne ne portait qu'un temoin v1 ; la story ecrivait elle-meme, a
        #    deux endroits, « re-qualifie PAR CONSTRUCTION, ⛔ pas encore par la
        #    mesure ». La seance carte suivante ne l'a pas ajoute, et AC5 comme AC7
        #    ont ete marques SOLDES.
        #
        # 🎯 CE QU'IL PROUVE, ET C'EST LA DECISION CENTRALE DE LA STORY :
        #    un agent v3 **NON MODIFIE** (ere dn4-6) emet `cpu` a TROIS valeurs
        #    [%, GHz, c.max] et `disk` a UNE [Mo/s]. Contre le firmware dn4-8 :
        #      · la trame doit rester ACCEPTEE (⛔ aucun compteur ne bouge) ;
        #      · le `c.max` doit atterrir en INDEX 2 ;
        #      · l'index 3 (la °C) doit dire « -- ».
        # ⛔ SI LA °C AVAIT ETE MISE EN INDEX 2 — l'ordre « naif » — le `c.max` d'un
        #    agent v3 non modifie serait tombe DANS LA CASE TEMPERATURE, et AUCUN
        #    COMPTEUR N'AURAIT BRONCHE. C'est precisement ce que la 4e voie evite,
        #    et c'est CE tir qui le demontre au lieu de le raisonner.
        for nom_t, met, vals, att, att_px in (
                # 🔴 L'UNITE FAIT PARTIE DE L'ATTENDU, ⛔ PAS SEULEMENT LE NOMBRE.
                #    Premiere version de ce temoin : `["52,0", "3,2", "88,0", "--"]`.
                #    Elle etait AVEUGLE au defaut qu'elle pretend exclure — si la
                #    °C etait en index 2, la dalle ecrirait « 88,0 degC » et
                #    `startswith("88,0")` passerait quand meme. On aurait ecrit,
                #    pour solder AC5, exactement la garde decorative que la revue
                #    du 2026-08-21 a passe sa journee a retirer d'ailleurs.
                # ⇒ unites reprises de `k_metriques[]` (dn_link.c:128 et :174).
                # ⚠️ 4e COLONNE AJOUTEE EN 2e REVUE : LES PREFIXES D'ECRAN
                #    ATTENDUS, position par position (`dn4-9`). ⛔ Les ignorer
                #    faisait sortir ces deux temoins en ECHEC sur une carte saine.
                ("TEMOIN v3 `cpu` a TROIS (agent dn4-6 NON MODIFIE)",
                 "cpu", [520, 32, 880],
                 ["52,0 %", "3,2 GHz", "88,0 %", "--"],
                 ["", "", "c.max", ""]),
                ("TEMOIN v3 `disk` a UNE (agent dn4-6 NON MODIFIE)",
                 "disk", [7085],
                 ["708,5 Mo/s", "--", "--", "--"],
                 ["", "extr.moy", "ventirad", "boitier"])):
            print()
            seq += 1
            avant = lire_compteurs(ser)
            _cmd(ser, "pc " + trame(3, seq, seq * 10, met, vals))
            time.sleep(0.15)
            apres = lire_compteurs(ser)
            delta = {k: apres[k] - avant[k] for k in COMPTEURS}
            vue = _cmd(ser, "pc")
            m = re.search(r"^\s*%s\s+->.*$" % met, vue, re.M)
            ligne = m.group(0) if m else ""
            cases = cases_pc(ligne)
            # ⚠️ CONTROLE PAR POSITION, ⛔ pas un `in` sur toute la ligne : « le
            #    c.max n'a pas glisse » est une propriete de POSITION, et un test
            #    en vrac serait vrai meme apres un decalage d'un cran.
            # ⛔ Un decoupage rate rend `None` : c'est un ECHEC D'INSTRUMENT, et il
            #    se dit comme tel, ⛔ pas comme un echec de la carte.
            # ⚠️ VALEUR ET PREFIXE SONT COMPARES SEPAREMENT (2e revue). Le
            #    prefixe est ce qui NOMME le ventilateur muet : un glissement d'un
            #    cran s'y verrait, et nulle part ailleurs.
            vals = [_valeur(c) for c in (cases or [])]
            pxs = [_prefixe(c) for c in (cases or [])]
            places = (cases is not None and len(cases) == len(att)
                      and all(v is not None for v in vals)
                      and all(vals[i].startswith(a) for i, a in enumerate(att))
                      and pxs == att_px)
            ok = (not any(delta.values())) and places
            print("  [%s] %s" % ("OK " if ok else "\u2716\ufe0f ", nom_t))
            print("        attendu aux 4 positions : %s"
                  % " | ".join(("%s %s" % (px, a)).strip()
                               for px, a in zip(att_px, att)))
            print("        lu  : %s" % (ligne.strip() or
                                        "\u26d4 ligne INTROUVABLE dans `pc`"))
            if not ok:
                print("        \u26d4 delta=%s  positions_ok=%s" % (delta, places))
                echecs.append(nom_t)
    finally:
        try:
            ser.close()
        except Exception:
            pass

    print("\n" + "=" * 92)
    if echecs:
        print("\u2716\ufe0f  %d CAS EN ECHEC : %s" % (len(echecs), echecs))
        return 1
    print("\u2705 %d cas + le temoin v1 : chacun dans SON compteur, et LUI SEUL."
          % len(CAS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
