#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dn4-41 / AC7 — LES PALIERS TIENNENT, ET CE QUI LES TIENT EST GARDE.

======================= CE QUE CET OUTIL FAIT, ET POURQUOI ==================

`dn4-41` rend DeskNode utilisable SANS capteurs soudes et SANS
LibreHardwareMonitor. Six proprietes portent cette promesse, et **aucune n'est
visible a l'oeil sur une carte complete** : elles ne se manifestent que sur une
configuration que le banc de developpement N'A PAS en permanence.

⇒ Sans cette gate, chacune ne serait gardee que par la seance qui l'a posee.

======================= ⛔ CE QU'ELLE NE RECITE PAS =========================

⛔ ELLE NE CONNAIT AUCUNE VALEUR « ATTENDUE ». Elle LIT LES DEUX COTES et les
   CONFRONTE : la prose contre les `#define`, l'enumeration contre les appels,
   l'agent contre le firmware, la table d'une AUTRE gate contre l'arbre.
   Motif paye : *« une gate `N OK / 0 KO` peut epingler du code FAUX »*
   (`dn4-14`) — une gate qui recite ce qu'elle veut trouver ne trouve rien.

⛔ ELLE NE CODE PAS EN DUR LA CLE `dn4-41` DANS UN MOTIF DE FORMAT (AC7.4).
   Le defaut est celui de `dn4-16` : une gate qui codait SA PROPRE cle laissait
   passer la premiere entree de tout autre auteur. Ici, les seules chaines
   cherchees sont des SYMBOLES DU CODE (`DN_ENV_ABSENT_SEUIL`, …), qui ne
   portent pas de numero de story.

⛔ ELLE NE POSE **AUCUN JETON D'EXEMPTION**, et c'est declare (AC7.4) : ces
   jetons n'ont aucun echappement, et les citer en commentaire les ACCORDE
   (defaut mesure dans ce depot). Aucun controle ci-dessous ne peut donc etre
   desarme par une ligne de commentaire.

======================= ⛔ CE QU'ELLE NE COUVRE PAS =========================

⛔ Elle ne prouve RIEN sur le materiel. Le verdict « ABSENT » se qualifie par
   un DEBRANCHEMENT REEL (AC2.9) ; le temoin `0x40` (AC2.8) exerce du vrai
   silence sur UNE adresse. Cette gate garde LE CODE et LES DOSSIERS.
⛔ Elle ne mesure pas le cout LHM (AC5) : ca se joue SUR LA TOUR, ⛔ jamais
   sous WSL, ou un port ferme rend `ConnectionRefusedError` INSTANTANEMENT.
⛔ Elle est SCOPEE aux six proprietes de `dn4-41`. Le depot a deja paye
   *« une gate scopee a UNE fonction epingle vert le meme defaut ailleurs »*
   (`dn4-16`) — c'est DECLARE ici, ⛔ pas ignore.

Sortie : `BILAN : n OK, m KO`, rc 0 si tout passe, 1 sinon.
Usage  : python3 tools/verif_paliers_dn441.py [--mutant <1..16>]
         `--mutant` casse UNE propriete EN MEMOIRE et doit faire ROUGIR (AC7.3).
         ⛔ Aucun fichier n'est modifie.
"""

import argparse
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(RACINE, "firmware", "desknode", "main")
AGENT = os.path.join(RACINE, "agent", "dn_agent.py")
# ⚠️ dn8-4 (2026-09-13) — REPOINTE. Ce chemin valait `README.md` a la racine.
#    Le journal francais que cette gate garde y est parti OCTET POUR OCTET
#    (13 liens rebases, preuve : `tools/scission_readme_dn84.py --verifier`) ;
#    la racine porte desormais une VITRINE anglaise, gardee par
#    `tools/verif_vitrine_dn84.py`. ⛔ Aucune ancre ni aucun mutant touche : la
#    gate garde le JOURNAL, ⛔ plus ce qu'un inconnu lit en premier.
README = os.path.join(RACINE, "docs", "journal-de-bord.md")
GATE_NVS = os.path.join(RACINE, "tools", "verif_d4_nvs_dn45.py")

# 🔴 LA FENETRE FROIDE, EN SECONDES — MESUREE, ⛔ PAS CHOISIE.
# A froid le bus I2C ENTIER se degrade (950 erreurs / 1 713 lectures du GT911,
# soit 55,5 %, TOUTES dans les ~40 premieres secondes) et se retablit SEUL vers
# T+~60 s. Dossier capteurs §13.17.1, A/B de six cycles.
# ⇒ Un verdict rendu avant CE chiffre declarerait ABSENT un capteur SOUDE.
FENETRE_FROIDE_S = 60

OK = [0]
KO = [0]
_MUTANT = None


# 🔴 dn4-40 / AC40.7.c — L'INSTRUMENT DE CAMPAGNE, ⛔ PAS UN CHANGEMENT DE
# FORMAT. Import DEFENSIF : une gate reste jouable si son instrument manque.
# Sans `DN_TRACE_CTRL`, la console sort a l'octet pres comme avant.
try:
    import dn_trace
except ImportError:                                  # pragma: no cover
    dn_trace = None


def dire(ok, libelle, detail=""):
    if dn_trace is not None:
        dn_trace.trace(ok, libelle)
    (OK if ok else KO)[0] += 1
    print(f"  [{'OK ' if ok else 'KO '}] {libelle:<58} {detail}")


def lire(chemin):
    with open(chemin, encoding="utf-8", errors="replace") as f:
        return f.read()


def code_nu(src):
    """Retire commentaires ET chaines. ⛔ DANS CET ORDRE, et les deux :

    🔴 DEFAUT TROUVE EN ECRIVANT CETTE GATE. Un comptage qui ne retire que les
       commentaires epinglait `dn_ui.c:3675` — un message `ESP_LOGE` qui CITE
       `dn_display_backlight_pct(` — comme un ECRIVAIN de LEDC. La gate aurait
       compte 9 sites la ou il y en a 8, et aurait rougi sur du code juste.
    ⚠️ C'est la meme classe que « le jeton d'exemption cite en commentaire
       l'ACCORDE » : du texte qui ressemble a du code n'est pas du code.
    """
    src = re.sub(r"/\*.*?\*/", " ", src, flags=re.S)
    src = re.sub(r"//[^\n]*", " ", src)
    src = re.sub(r'"(?:\\.|[^"\\])*"', '""', src)
    return src


def defini(src, nom):
    """La valeur ENTIERE d'un `#define <nom> <n>`. None si absent."""
    m = re.search(r"^#define\s+%s\s+(-?\d+)" % re.escape(nom), src, re.M)
    return int(m.group(1)) if m else None


def mut(n, src):
    """Applique le mutant `n` a `src` si c'est celui qui est demande."""
    return src


def main():
    global _MUTANT
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--mutant", type=int, default=None,
                    help="casse UNE propriete EN MEMOIRE (1..16) pour prouver "
                         "que le controle correspondant sait ROUGIR")
    args = ap.parse_args()
    _MUTANT = args.mutant

    def M(n, src, avant, apres):
        """Mutation ciblee : si `--mutant n`, remplace `avant` par `apres`."""
        if _MUTANT != n:
            return src
        if avant not in src:
            print(f"  ⛔ MUTANT {n} INAPPLICABLE : le motif a disparu du source. "
                  f"⇒ le mutant est PERIME, ⛔ pas la propriete.")
            sys.exit(3)
        return src.replace(avant, apres, 1)

    print("=" * 78)
    print("dn4-41 / AC7 — LES PALIERS TIENNENT, ET CE QUI LES TIENT EST GARDE")
    if _MUTANT:
        print(f"⚠️  MUTANT {_MUTANT} ARME — cette execution DOIT rougir.")
    print("=" * 78)

    agent = lire(AGENT)
    env_h = lire(os.path.join(MAIN, "dn_env.h"))
    env_c = lire(os.path.join(MAIN, "dn_env.c"))
    capt_h = lire(os.path.join(MAIN, "dn_capteurs.h"))
    capt_c = lire(os.path.join(MAIN, "dn_capteurs.c"))
    veille_h = lire(os.path.join(MAIN, "dn_veille.h"))
    ui_c = lire(os.path.join(MAIN, "dn_ui.c"))
    link_c = lire(os.path.join(MAIN, "dn_link.c"))
    readme = lire(README)
    gate_nvs = lire(GATE_NVS)

    # ══════════════════════════════════════════════════════════════════════
    print("\n── 1. ⛔ AUCUNE GRANDEUR LHM EN POSITION 0 ─────────────────────────")
    print("      (couper LHM ne doit emporter NI le %% CPU NI le Mo/s disque)")
    # ------------------------------------------------------------------
    m = re.search(r"^LHM_SONDES\s*=\s*\((.*?)^\)", agent, re.M | re.S)
    sondes = re.findall(r'^\s*\("([^"]+)"', m.group(1), re.M) if m else []
    dire(len(sondes) >= 1, "la table `LHM_SONDES` est lisible",
         f"{len(sondes)} sonde(s) : {', '.join(sondes)}")

    agent_nu = agent
    # 🔴 MUTANT 1 DURCI, ET LE MOTIF EST UNE LECON. Sa premiere version mettait
    #    `noctua` (un ventilateur LHM) en position 0 de `disk` — et LA GATE EST
    #    RESTEE VERTE. Cause : le controle cherchait la CLE de sonde
    #    (`"fan.cpu_noctua"`) ou le mot `lhm` DANS la position 0, or a cet
    #    endroit la valeur porte un NOM DE VARIABLE. ⛔ Un controle qui ne suit
    #    pas la valeur ne garde pas la valeur.
    agent_nu = M(1, agent_nu,
                 '_dx(mo_s, BORNES["disk"][0], e, "disk"),',
                 '_dx(noctua, BORNES["disk"][0], e, "disk"),')
    blocs = re.findall(r'out\.append\(\("(\w+)",\s*\[(.*?)\]\s*\)\)',
                       agent_nu, re.S)

    # 🔴 LES VARIABLES QUI **PORTENT** UNE VALEUR LHM — resolues, ⛔ pas devinees.
    #    Toute affectation `X = lhm.get(...)` ou `X = self.lhm.<...>` fait de `X`
    #    un porteur de LHM. C'est ce que la position 0 ne doit jamais contenir.
    porteurs = set(re.findall(r"^\s*(\w+)\s*=\s*(?:self\.)?lhm\b", agent_nu, re.M))
    porteurs |= set(re.findall(r"^\s*(\w+)\s*=\s*self\.lhm\.", agent_nu, re.M))
    dire(bool(porteurs),
         "les VARIABLES qui portent une valeur LHM sont resolues",
         f"{len(porteurs)} : {', '.join(sorted(porteurs))}")
    dire(len(blocs) >= 5, "les blocs d'emission de metriques sont lisibles",
         f"{len(blocs)} metrique(s) : {', '.join(b[0] for b in blocs)}")
    for nom, corps in blocs:
        # La grandeur en POSITION 0 = le premier element de la liste, jusqu'a
        # la premiere virgule de PREMIER NIVEAU.
        prof, fin = 0, len(corps)
        for i, ch in enumerate(corps):
            if ch in "([{":
                prof += 1
            elif ch in ")]}":
                prof -= 1
            elif ch == "," and prof == 0:
                fin = i
                break
        pos0 = corps[:fin]
        coupable = [s for s in sondes if s in pos0]
        # ⇒ ET les variables qui PORTENT du LHM (le trou du mutant 1)
        coupable += [v for v in sorted(porteurs)
                     if re.search(r"\b%s\b" % re.escape(v), pos0)]
        if not coupable and re.search(r"\blhm\b", pos0):
            coupable = ["<reference a `lhm`>"]
        dire(not coupable,
             f"`{nom}` : la grandeur en position 0 ne vient PAS de LHM",
             "⛔ " + ", ".join(coupable) if coupable
             else "⇒ la metrique survit a l'arret de LHM")

    # ══════════════════════════════════════════════════════════════════════
    print("\n── 2. LE VERDICT « ABSENT » NE PEUT PAS TOMBER DANS LE FROID ───────")
    # ------------------------------------------------------------------
    env_h_m = M(2, env_h, "#define DN_ENV_ABSENT_SEUIL 2",
                "#define DN_ENV_ABSENT_SEUIL 1")
    capt_h_m = M(3, capt_h, "#define DN_CAPT_ABSENT_SEUIL 2",
                 "#define DN_CAPT_ABSENT_SEUIL 1")

    modules = [
        ("dn_env", env_h_m, "DN_ENV_ABSENT_SEUIL", "DN_ENV_REINIT_CYCLES",
         "DN_ENV_PERIODE_MS"),
        ("dn_capt", capt_h_m + "\n" + capt_c, "DN_CAPT_ABSENT_SEUIL",
         "DN_CAPT_REINIT_CYCLES", "DN_CAPT_PERIODE_MS"),
    ]
    for nom, src, s_nom, b_nom, p_nom in modules:
        seuil = defini(src, s_nom)
        backoff = defini(src, b_nom)
        periode = defini(src, p_nom)
        dire(seuil is not None and seuil >= 2,
             f"{nom} : seuil ABSENT >= 2 re-ouvertures",
             f"{s_nom} = {seuil}")
        if None in (seuil, backoff, periode):
            dire(False, f"{nom} : les trois chiffres du delai sont lisibles",
                 f"seuil={seuil} backoff={backoff} periode={periode}")
            continue
        delai = seuil * backoff * periode / 1000.0
        dire(delai > FENETRE_FROIDE_S,
             f"{nom} : seuil x backoff DEPASSE la fenetre froide",
             f"{seuil} x {backoff} x {periode} ms = {delai:.0f} s "
             f"> {FENETRE_FROIDE_S} s")

    # 2.x — le verdict ne se prend NI au scan NI au probe
    env_c_m = M(4, env_c, "        if (configurer(id) != ESP_OK) {\n"
                          "            compter_i2c(id);\n"
                          "            /* 🔴 dn4-41 / AC2 — C'EST **ICI**",
                "        if (i2c_master_probe(NULL, 0, 0) != ESP_OK) {\n"
                "            compter_i2c(id);\n"
                "            /* 🔴 dn4-41 / AC2 — C'EST **ICI**")
    for nom, src, fonc in (("dn_env", env_c_m, "reouv_echouee"),
                           ("dn_capt", capt_c, "verdict_absence_maj")):
        nu = code_nu(src)
        # le corps de la fonction de verdict
        mm = re.search(r"static void %s\s*\([^)]*\)\s*\{" % fonc, nu)
        dire(mm is not None, f"{nom} : la fonction de verdict `{fonc}()` existe",
             "" if mm else "⛔ INTROUVABLE")
        # et AUCUN de ses appelants ne passe par un probe/scan
        appels = [l for l in nu.splitlines() if fonc + "(" in l]
        dire(bool(appels), f"{nom} : `{fonc}()` est APPELE quelque part",
             f"{len(appels)} appel(s) — ⛔ un etat sans chemin est inatteignable")
        # ⛔ le probe ne doit apparaitre dans AUCUNE ligne qui mene au verdict
        ctx = "\n".join(nu.splitlines())
        near = re.findall(r"i2c_master_probe\s*\(", ctx)
        dire(not near,
             f"{nom} : ⛔ AUCUN `i2c_master_probe` dans le module du verdict",
             "⇒ « le scan DECOUVRE, seule une transaction de DONNEE QUALIFIE »"
             if not near else f"⛔ {len(near)} occurrence(s)")

    # 2.y — la tentative du BOOT ne compte pas
    env_c_boot = M(5, env_c, "        if (configurer((dn_env_id_t)i) != ESP_OK) {",
                   "        if (configurer((dn_env_id_t)i) != ESP_OK) {\n"
                   "            reouv_echouee((dn_env_id_t)i);")
    nu = code_nu(env_c_boot)
    mm = re.search(r"esp_err_t dn_env_init\s*\(void\)\s*\{(.*?)\n\}", nu, re.S)
    dire(mm is not None and "reouv_echouee" not in mm.group(1),
         "dn_env : ⛔ la tentative du BOOT n'alimente PAS le verdict",
         "⇒ sinon le verdict tomberait a 60 s, DANS la fenetre froide")
    nu_c = code_nu(M(6, capt_c, "    relever_identite(bus);\n    /* 🔴 `dn4-41` / AC2.3",
                     "    relever_identite(bus);\n    verdict_absence_maj();\n    /* 🔴 `dn4-41` / AC2.3"))
    mm = re.search(r"esp_err_t dn_capteurs_init\s*\(void\)\s*\{(.*?)\n\}", nu_c, re.S)
    dire(mm is not None and "verdict_absence_maj" not in mm.group(1),
         "dn_capt : ⛔ la tentative du BOOT n'alimente PAS le verdict",
         "⇒ meme motif, meme chiffre")

    # 2.z — le verdict est REVERSIBLE, et le meme MOT dans les deux modules
    for nom, src, jeton in (("dn_env", env_h, "DN_ENV_ABSENT"),
                            ("dn_capt", capt_h, "DN_CAPT_ABSENT")):
        mm = re.search(r"typedef enum\s*\{(.*?)\}\s*dn_\w+_etat_t", src, re.S)
        dire(mm is not None and re.search(r"\b%s\b" % jeton, mm.group(1)) is not None,
             f"{nom} : l'etat `{jeton}` est DANS l'enumeration",
             "⇒ meme MOT dans les deux modules : ils se comparent")
    env_c_rev = M(7, env_c, "    s_c[id].reouv_echecs = 0;\n    s_c[id].etait_absent = false;",
                  "    /* mutant : le verdict devient DEFINITIF */")
    dire("reouv_reussie" in code_nu(env_c_rev)
         and "s_c[id].reouv_echecs = 0" in code_nu(env_c_rev),
         "dn_env : le verdict est REVERSIBLE (remise a zero)",
         "⇒ ⛔ un « absent » a vie est le defaut qu'a paye dn2-1")

    # ══════════════════════════════════════════════════════════════════════
    print("\n── 3. LES TROIS PLANCHERS, ET LA LISTE QUI LES ENONCE ──────────────")
    # ------------------------------------------------------------------
    env_h_p = M(8, env_h, "#define DN_ENV_BL_AMB_PCT_MIN_DEFAUT 16",
                "#define DN_ENV_BL_AMB_PCT_MIN_DEFAUT 20")
    planchers = {
        "DN_VEILLE_PCT_MIN": defini(veille_h, "DN_VEILLE_PCT_MIN"),
        "DN_ENV_BL_PCT_MIN": defini(env_h_p, "DN_ENV_BL_PCT_MIN"),
        "DN_ENV_BL_AMB_PCT_MIN_DEFAUT":
            defini(env_h_p, "DN_ENV_BL_AMB_PCT_MIN_DEFAUT"),
    }
    dire(all(v is not None for v in planchers.values()),
         "les TROIS planchers existent, sous leur nom REEL",
         " · ".join(f"{k}={v}" for k, v in planchers.items()))
    vals = [v for v in planchers.values() if v is not None]
    dire(len(set(vals)) == len(vals),
         "les trois planchers sont DISTINCTS",
         "⇒ « un plancher est une propriete du COUPLE duty x contenu »"
         if len(set(vals)) == len(vals) else f"⛔ collision : {vals}")

    # 3.x — LA LISTE CANONIQUE NE MENT PLUS (le defaut trouve par dn4-41)
    env_h_l = M(9, env_h,
                " *      · `DN_ENV_BL_PCT_MIN`   = ~~8~~ **20 %**",
                " *      · `DN_ENV_BL_PCT_MIN`   = ~~20~~ **8 %**")
    # ⚠️ « dépôt » porte DEUX accents : `d.p.t`, ⛔ pas `d.pot`. Ce bug-la a fait
    #    dire « INTROUVABLE » a la premiere execution de cette gate, SUR UNE
    #    LISTE PRESENTE — c'est-a-dire un FAUX ROUGE. Il est note plutot que
    #    tu : une gate qui se trompe de motif accuse le code d'un defaut a elle.
    mm = re.search(r"Les trois planchers du d.p.t\s*:(.*?)\*/", env_h_l, re.S)
    if mm is None:
        dire(False, "la liste CANONIQUE des trois planchers est lisible",
             "⛔ INTROUVABLE dans dn_env.h")
    else:
        bloc = mm.group(1)
        dire(True, "la liste CANONIQUE des trois planchers est lisible",
             f"{len(bloc.splitlines())} ligne(s)")

        def valeur_prose(ligne):
            """La valeur COURANTE citee par la prose.

            ⛔ ⛔ PAS « le dernier chiffre de la ligne » : la premiere version de
               cette gate faisait ça, et lisait **7** pour `DN_VEILLE_PCT_MIN`
               parce que la ligne finit par « (dn1-3/AC7) ». Un FAUX ROUGE de
               plus, produit par le controle lui-meme.
            ⇒ On lit ce qui suit le `=`, en SAUTANT une valeur barree — la
              convention du depot est « barrer, jamais effacer », donc
              `= ~~8~~ **20 %**` vaut **20**.
            """
            m2 = re.search(r"=\s*(?:~~\d+~~\s*)?\**\s*(\d+)", ligne)
            return int(m2.group(1)) if m2 else None

        cibles = (
            ("DN_VEILLE_PCT_MIN", planchers["DN_VEILLE_PCT_MIN"]),
            ("DN_ENV_BL_PCT_MIN", planchers["DN_ENV_BL_PCT_MIN"]),
            ("celui-ci", planchers["DN_ENV_BL_AMB_PCT_MIN_DEFAUT"]),
        )
        for sym, attendu in cibles:
            ligne = [l for l in bloc.splitlines() if sym in l]
            lu = valeur_prose(ligne[0]) if ligne else None
            dire(lu == attendu,
                 f"la liste canonique dit la VRAIE valeur de `{sym}`",
                 f"prose = {lu} · #define = {attendu}"
                 + ("" if lu == attendu
                    else "  ⛔ UNE LISTE DE REFERENCE QUI MENT"))

    # ══ 3.y — LE REPLI DE DERNIER RECOURS EST PLANCHERISE, ET AUX TROIS SITES
    #
    # 🔴 CE CONTROLE A ETE VU DECORATIF, ET LE MOTIF VAUT D'ETRE ECRIT. Sa
    #    premiere version testait `"dn_veille_pct" in nu` — c'est-a-dire
    #    « la chaine apparait QUELQUE PART dans un fichier de 11 000 lignes ».
    #    Le mutant 10 retirait le plancher et LA GATE RESTAIT VERTE, parce que
    #    la chaine survivait ailleurs. ⛔ « Le symbole existe » n'est PAS
    #    « la propriete tient » — c'est le defaut « une gate scopee epingle vert
    #    le meme defaut ailleurs » (dn4-16), pris par l'autre bout.
    # ⇒ ON EPINGLE LE CORPS DE LA FONCTION, PUIS SES APPELANTS.
    ui_m = M(10, ui_c,
             "    return (pct < plancher) ? plancher : pct;",
             "    return pct; /* mutant : plus de plancher */")
    ui_m = M(16, ui_m,
             "        cible = veille_bl_dernier_recours();",
             "        cible = dn_veille_pct(); /* mutant : plancher CONTOURNE */")
    nu = code_nu(ui_m)
    mm = re.search(r"static int veille_bl_dernier_recours\s*\(void\)\s*\{(.*?)\n\}",
                   nu, re.S)
    corps = mm.group(1) if mm else ""
    dire(mm is not None, "dn_ui : `veille_bl_dernier_recours()` existe",
         "" if mm else "⛔ INTROUVABLE")
    dire("dn_env_bl_amb_plancher" in corps and "<" in corps,
         "dn_ui : le repli est PLANCHERISE dans son corps",
         "⇒ `(pct < plancher) ? plancher : pct` — ⛔ jamais un litteral"
         if "dn_env_bl_amb_plancher" in corps
         else "⛔ le plancher a disparu du corps")
    # ⚠️ `\(\)` ne matche PAS la definition, qui s'ecrit `(void)` en C. ⛔ Ne pas
    #    soustraire 1 « pour la definition » : c'etait un ajustement a l'aveugle,
    #    et il faisait dire 2 la ou il y en a 3. Un compteur qu'on corrige par
    #    une constante est un compteur qu'on n'a pas compris.
    appels = len(re.findall(r"veille_bl_dernier_recours\s*\(\)", nu))
    dire(appels >= 3,
         "dn_ui : le repli plancherise est appele aux TROIS sites",
         f"{appels} appelant(s) — ⛔ un site qui l'evite pose un duty NU")
    # ⛔ et AUCUN site ne pose `dn_veille_pct()` directement dans un duty
    direct = re.findall(r"cible\s*=\s*dn_veille_pct\s*\(\)", nu)
    dire(not direct,
         "dn_ui : ⛔ AUCUN site ne CONTOURNE le plancher",
         "⇒ « ni eteindre l'ecran ni le mettre a fond » vaut A FORTIORI absent"
         if not direct else f"⛔ {len(direct)} contournement(s)")

    # ══════════════════════════════════════════════════════════════════════
    print("\n── 4. LA REGLE DE PRIORITE LEDC EST A JOUR ─────────────────────────")
    # ------------------------------------------------------------------
    env_h_e = M(11, env_h, "#define DN_ENV_LEDC_SITES 8",
                "#define DN_ENV_LEDC_SITES 7")
    declares = defini(env_h_e, "DN_ENV_LEDC_ECRIVAINS")
    sites_dec = defini(env_h_e, "DN_ENV_LEDC_SITES")
    dire(declares is not None and sites_dec is not None,
         "le compte d'ecrivains et de sites est DECLARE",
         f"ecrivains={declares} · sites={sites_dec}")
    # les ROLES enumeres dans le docblock
    mm = re.search(r"Les sept .crivains, et ce que la r.gle leur donne\s*:(.*?)\*/",
                   env_h_e, re.S)
    roles = re.findall(r"^\s*\*\s+(\d+)\.", mm.group(1), re.M) if mm else []
    dire(declares is not None and len(roles) == declares,
         "l'ENUMERATION porte autant de roles que le compte declare",
         f"{len(roles)} role(s) enumere(s) vs {declares} declare(s)")
    # les SITES reellement presents dans l'arbre
    reels = 0
    detail = []
    for f in sorted(os.listdir(MAIN)):
        if not f.endswith(".c") or f == "dn_display.c":
            continue
        src = ui_c if f == "dn_ui.c" else lire(os.path.join(MAIN, f))
        n = len(re.findall(r"\bdn_display_backlight_pct\s*\(", code_nu(src)))
        if n:
            reels += n
            detail.append(f"{f}:{n}")
    dire(sites_dec == reels,
         "le compte de SITES declare colle aux appels REELS",
         f"declare={sites_dec} · mesure={reels}  ({' · '.join(detail)})")

    # ══════════════════════════════════════════════════════════════════════
    print("\n── 5. NVS : TOUT ECRIVAIN EST DECLARE, ET `dn_env.c` N'EN EST PAS ──")
    # ------------------------------------------------------------------
    PRIM = ("nvs_set_", "nvs_commit", "nvs_erase", "nvs_flash_erase")
    gate_nvs_m = M(12, gate_nvs, '    "dn_reglage.c": (', '    "dn_reglage_ABSENT.c": (')
    table = set(re.findall(r'^\s*"([\w.]+)"\s*:\s*\(', gate_nvs_m, re.M))
    ecrivains = []
    for f in sorted(os.listdir(MAIN)):
        if not f.endswith(".c"):
            continue
        src = code_nu(lire(os.path.join(MAIN, f)))
        if any(p in src for p in PRIM):
            ecrivains.append(f)
    manquants = [f for f in ecrivains if f not in table]
    dire(not manquants,
         "tout fichier qui ECRIT en NVS est DECLARE dans verif_d4_nvs_dn45.py",
         f"{len(ecrivains)} ecrivain(s)" if not manquants
         else "⛔ NON DECLARE : " + ", ".join(manquants))
    env_c_nvs = M(13, env_c, "static const char *TAG",
                  "static void _mutant(void){ nvs_commit(0); }\nstatic const char *TAG")
    dire(not any(p in code_nu(env_c_nvs) for p in PRIM),
         "⛔ `dn_env.c` n'ecrit RIEN en NVS (D16)",
         "⇒ c'est ce qui garde D4 : aucune ecriture EN REGIME")
    dire("dn_env.c" not in table,
         "⛔ `dn_env.c` n'est PAS dans la table des ecrivains (D16)",
         "⇒ la contrainte est gardee des DEUX cotes")

    # ══════════════════════════════════════════════════════════════════════
    print("\n── 6. LE README DIT LES PALIERS, ET IL NE PROMET PAS NVIDIA ────────")
    # ------------------------------------------------------------------
    readme_m = M(14, readme, "DeskNode + Ambiance", "DeskNode + Capteurs")
    lignes_nv = [l for l in readme.splitlines() if "GPU NVIDIA" in l]
    README_LIGNE_NVIDIA = lignes_nv[0] if lignes_nv else "<absente>"
    # 🔴 MUTANT 15 DURCI. Sa premiere version ne remplacait QUE le debut de la
    #    ligne : les trois autres marqueurs de refutation (« aucun NVML »,
    #    « c'est faux », « ne le promet pas ») survivaient sur la MEME ligne, et
    #    la gate restait VERTE. ⛔ Un mutant qui laisse la propriete vraie ne
    #    prouve rien — c'est le mutant qui etait faible, ⛔ pas le controle.
    readme_m = M(15, readme_m, README_LIGNE_NVIDIA,
                 "| **GPU NVIDIA** | ✅ pris en charge (NVML). |")
    for nom in ("DeskNode + Ambiance",):
        dire(nom in readme_m, f"le README nomme le palier « {nom} »",
             "⇒ ce sont les noms de D19, ⛔ pas des synonymes")
    axes = {
        "capteurs": re.search(r"capteurs\s+soud", readme_m, re.I) is not None,
        "LHM": "LibreHardwareMonitor" in readme_m,
        "PC allume": re.search(r"PC\s+(allum|eteint|éteint)", readme_m, re.I)
                     is not None,
    }
    dire(all(axes.values()), "le README porte les TROIS axes (AC8.2)",
         " · ".join(f"{k}={'✅' if v else '⛔'}" for k, v in axes.items()))
    # ══ AC8.6 — ⛔ LE README NE PROMET PAS NVIDIA ═══════════════════════════
    #
    # 🔴 CE CONTROLE A ETE VU FAUX-ROUGE, ET LE MOTIF VAUT D'ETRE ECRIT.
    #    Sa premiere version cherchait la CHAINE « NVIDIA (NVML) ». Elle a
    #    rougi sur un README qui CITE cette promesse **pour la REFUTER** :
    #      « Un dossier de ce depot a ecrit *« GPU : NVIDIA (NVML) et AMD »* —
    #        c'est FAUX dans le code, et le README ne le promet pas. »
    #    ⇒ **CITER LE JETON L'ACCORDAIT** — exactement le defaut que ce depot a
    #      deja paye sur un jeton d'exemption cite en commentaire.
    # ⇒ LA PROPRIETE N'EST PAS « le mot NVIDIA est absent » — ce serait interdire
    #   d'en PARLER, donc interdire de dire la verite. C'est : **toute ligne qui
    #   nomme NVIDIA porte sa REFUTATION**.
    nvml_agent = re.search(r"^\s*import\s+pynvml", agent, re.M) is not None
    REFUTATIONS = ("NON IMPLÉMENT", "NON IMPLEMENT", "aucun NVML",
                   "ne le promet pas", "c'est faux")
    nues = [l.strip()[:70] for l in readme_m.splitlines()
            if "NVIDIA" in l and not any(r in l for r in REFUTATIONS)]
    dire(nvml_agent or not nues,
         "⛔ le README ne PROMET PAS NVIDIA (l'agent n'a aucun NVML)",
         "⇒ mesure : `pynvml` n'est pas importe ; seule source GPU = AMD ADL"
         if not nues else "⛔ ligne SANS refutation : " + nues[0])

    print("\n" + "=" * 78)
    print(f"BILAN : {OK[0]} OK, {KO[0]} KO")
    print("=" * 78)
    return 0 if KO[0] == 0 else 1


sys.exit(main())
