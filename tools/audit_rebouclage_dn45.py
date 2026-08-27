#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dn4-5 / AC1.1 — L'AUDIT DE REBOUCLAGE. TOUT `firmware/desknode/main/`, PAS UN
FICHIER, PAS UN DIFF.

======================= CE QUE CET OUTIL FAIT, ET POURQUOI ==================

L'epic nomme « le compteur `esp_timer` reboucle en ~71 min » comme LE PREMIER
DEFAUT A FERMER avant de lancer un soak de 7 jours. Un inventaire ecrit a la
main serait une liste d'opinions : celui-ci est MECANIQUE, et il est concu pour
CRIER quand il ne sait pas, ⛔ jamais pour omettre en silence.

── LES TROIS PHASES ────────────────────────────────────────────────────────

  1. BALAYAGE. On part des ACCUMULATIONS (`x++`, `++x`, `x += ...`), ⛔ PAS des
     declarations. C'est deliberé et c'est le fruit de deux trous payes pendant
     l'ecriture de cet outil :
       · une premiere passe qui listait les `static uint32_t` ratait
         `s_px`, `s_copie_us`, `s_attente_us` — declares en MULTI-DECLARATEUR
         sur une seule ligne (`static volatile uint32_t a, b, c;`) ;
       · une deuxieme passe les rattrapait mais ratait `s_lat_somme` et
         `s_flash_bytes`, declares dans des formes encore differentes.
     Les accumulations, elles, ont une syntaxe unique. On ne peut pas les rater.

  2. RESOLUTION DE TYPE. Pour chaque cible persistante (portee fichier), on
     resout le type DECLARE, y compris a travers les membres de structures
     (`s_cnt.err_i2c`, `s_c[id].cnt.lectures`) en suivant les `typedef struct`
     des en-tetes. ⛔ SI UN TYPE N'EST PAS RESOLU, LA GATE ECHOUE : un site dont
     on ne connait pas la largeur est exactement le site qu'un audit doit
     signaler, pas celui qu'il doit sauter.

  3. TABLE DECLAREE. Chaque site porte une classe (OK / ATTENTION / ROUGE) et un
     HORIZON CHIFFRE, avec son motif. La gate echoue si :
       · un site balaye est ABSENT de la table (⇒ un compteur neuf est arrive
         sans classement — c'est la propriete qui fait vivre cet audit apres
         dn4-5) ;
       · une entree de table ne correspond plus a aucun site (⇒ table perimee) ;
       · une entree est classee ROUGE (⇒ un rebouclage sans parade subsiste).

⚠️ LES LOCALES SONT ECARTEES, ET L'EXCLUSION EST DECLAREE, ⛔ pas silencieuse :
   une variable de pile repart a chaque appel, elle ne cumule pas dans le temps.
   Le compte des exclusions est imprime.

⚠️ CE QUE CET AUDIT NE PEUT PAS VOIR — et c'est ecrit ici parce qu'un instrument
   qui ne declare pas son angle mort en fabrique un :
     · les compteurs des COMPOSANTS ESP-IDF et de LVGL (hors `main/`) ;
     · un debordement qui viendrait d'une MULTIPLICATION ou d'un decalage, pas
       d'une accumulation ;
     · le rebouclage de `configRUN_TIME_COUNTER_TYPE`, qui n'est pas une
       variable du depot — il est traite a part, en phase 4 ;
     · la JUSTESSE des cadences declarees ci-dessous : elles sont SOURCEES, mais
       une cadence fausse rendrait un horizon faux. Chacune porte sa source.

Sortie : exit 0 si tout passe, 1 sinon. Publie le sha256 des sources LUES.
"""

import hashlib
import io
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(RACINE, "firmware", "desknode", "main")

ok_total = [0]
ko_total = [0]


def ctrl(ok, libelle, detail=""):
    if ok:
        ok_total[0] += 1
        print("  [OK ] %-62s %s" % (libelle, detail))
    else:
        ko_total[0] += 1
        print("  [KO ] %-62s %s" % (libelle, detail))
    return ok


# ═══════════════════════════════════════════════════════════════════════════
#  LES CADENCES — chacune avec SA SOURCE. Un horizon n'est pas plus solide
#  que la cadence qui le produit.
# ═══════════════════════════════════════════════════════════════════════════
CADENCES = {
    # nom              : (Hz,      source)
    "vsync":            (37.40,   "mesure dn1-2, 37,40 Hz — dalle 620x690 @ 16 MHz"),
    "lvgl":             (30.30,   "cycle LVGL 33 ms (dn_ui.c, lv timer) — majorant"),
    "touch_poll":       (100.0,   "DN_TP_INT_LOW_MS, majorant de scrutation tactile"),
    "touch_evt":        (10.0,    "majorant GENEREUX d'appuis humains : 10/s"),
    "hist":             (1.0,     "DN_HIST_PERIODE_MS = 1000 (dn_hist.h:137)"),
    "rtc":              (2.0,     "DN_RTC_PERIODE_MS = 500 (dn_rtc.h:136)"),
    "link":             (4.0,     "tache dn_link : vTaskDelayUntil 250 ms (dn_link.c:853)"),
    "link_trame":       (5.0,     "5 metriques a 1 Hz sur le fil (dn2-2)"),
    "capteurs":         (0.2,     "DN_CAPT_PERIODE_MS = 5000 (dn_capteurs.h:72)"),
    "env":              (0.2,     "DN_ENV_PERIODE_MS = 5000 (dn_env.h:75)"),
    "veille_tick":      (1.0,     "dn_veille_tick, un par seconde (dn3-3)"),
    "console":          (0.0,     "commande console : cadence HUMAINE, pas de regime"),
}

SEPT_JOURS_S = 7 * 24 * 3600  # 604 800


def horizon_s(bits, hz, par_incr=1.0):
    """Duree avant rebouclage, en secondes. `par_incr` = quantite ajoutee par
    evenement (1 pour un compteur d'evenements)."""
    if hz <= 0:
        return float("inf")
    return (2.0 ** bits) / (hz * par_incr)


def humain(s):
    if s == float("inf"):
        return "jamais (cadence humaine)"
    if s < 120:
        return "%.0f s" % s
    if s < 7200:
        return "%.1f min" % (s / 60.0)
    if s < 172800:
        return "%.1f h" % (s / 3600.0)
    if s < 3.15e7:
        return "%.1f j" % (s / 86400.0)
    return "%.1f ans" % (s / 3.15576e7)


# ═══════════════════════════════════════════════════════════════════════════
#  PHASE 1 — LE BALAYAGE
# ═══════════════════════════════════════════════════════════════════════════

RE_ACC = re.compile(
    r'(?<![\w.>])((?:[A-Za-z_]\w*)'          # base
    r'(?:\s*\[[^\]]*\])?'                     # index eventuel
    r'(?:\s*(?:\.|->)\s*[A-Za-z_]\w*(?:\s*\[[^\]]*\])?)*)'  # membres
    r'\s*(\+\+|\+=)')
RE_ACC_PRE = re.compile(r'\+\+\s*((?:[A-Za-z_]\w*)'
                        r'(?:\s*\[[^\]]*\])?'
                        r'(?:\s*(?:\.|->)\s*[A-Za-z_]\w*(?:\s*\[[^\]]*\])?)*)')


def sans_commentaires(txt):
    """Retire commentaires et chaines. ⚠️ Indispensable : ce depot documente
    massivement, et un `x += 1` cite dans un commentaire compterait comme un
    site reel — l'audit dirait alors du faux dans le sens le plus trompeur, celui
    qui GONFLE la liste."""
    out = []
    i, n = 0, len(txt)
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
        elif c in '"\'':
            j = i + 1
            while j < n and txt[j] != c:
                j += 2 if txt[j] == '\\' else 1
            j = min(j + 1, n)
            out.append(re.sub(r'[^\n]', ' ', txt[i:j]))
            i = j
        else:
            out.append(c)
            i += 1
    return ''.join(out)


RE_STATIC = re.compile(
    r'^[ \t]*static[ \t]+((?:volatile[ \t]+|const[ \t]+|unsigned[ \t]+|signed[ \t]+)*'
    r'[A-Za-z_]\w*(?:[ \t]+\w+)*?)[ \t]+((?:volatile[ \t]+)?\*?\w+[^;=]*'
    r'(?:=[^;]*)?(?:,[^;]*)*);', re.M)


def statiques(txt_nu):
    """Table nom -> type declare, pour les variables a portee fichier.
    Gere les multi-declarateurs : c'est par la qu'un premier balayage s'est
    troue sur `static volatile uint32_t s_n_flush, s_n_cycles, s_px, ...`."""
    d = {}
    for m in RE_STATIC.finditer(txt_nu):
        typ = re.sub(r'\s+', ' ', m.group(1)).replace('volatile ', '').strip()
        if '(' in m.group(2):
            # ⛔ PROTOTYPE DE FONCTION, pas une variable. Sans ce filtre les NOMS
            #    DES PARAMETRES entraient dans la table des statiques, et des
            #    variables de boucle homonymes (`a`, `c`, `y`) etaient promues
            #    « persistantes » — un audit qui invente des sites est aussi faux
            #    qu'un audit qui en oublie, et il est plus difficile a detecter.
            continue
        for part in m.group(2).split(','):
            part = part.split('=')[0].strip()
            part = part.replace('volatile', '').strip()
            tab = '[' in part
            nom = re.sub(r'\[.*', '', part).strip().lstrip('*')
            if re.fullmatch(r'\w+', nom or ''):
                d[nom] = (typ + ('[]' if tab else ''), typ)
    return d


# ═══════════════════════════════════════════════════════════════════════════
#  PHASE 2 — LA RESOLUTION DE TYPE, MEMBRES DE STRUCTURES COMPRIS
# ═══════════════════════════════════════════════════════════════════════════

RE_TYPEDEF = re.compile(r'typedef\s+struct\s*\{(.*?)\}\s*(\w+)\s*;', re.S)


def structs_du_projet():
    """nom_de_type -> {membre: type}. Lu dans TOUS les .h ET .c de main/."""
    tables = {}
    for fn in sorted(os.listdir(MAIN)):
        # ⚠️ LES DEUX EXTENSIONS. `env_capteur_t` (dn_env.c) est typedef DANS LE
        #    .c : ne lire que les en-tetes laissait les six compteurs de
        #    `s_c[id].cnt.*` NON RESOLUS, donc invisibles a l'audit.
        if not fn.endswith(('.h', '.c')):
            continue
        txt = sans_commentaires(io.open(os.path.join(MAIN, fn), encoding='utf-8').read())
        for m in RE_TYPEDEF.finditer(txt):
            corps, nom = m.group(1), m.group(2)
            champs = {}
            for ligne in corps.split(';'):
                ligne = re.sub(r'\s+', ' ', ligne).strip()
                if not ligne:
                    continue
                mm = re.match(r'((?:unsigned |signed |const )*[A-Za-z_]\w*)\s+(.+)$', ligne)
                if not mm:
                    continue
                typ = mm.group(1)
                for part in mm.group(2).split(','):
                    part = part.strip().lstrip('*')
                    nomc = re.sub(r'\[.*', '', part).strip()
                    if re.fullmatch(r'\w+', nomc or ''):
                        champs[nomc] = typ
            tables[nom] = champs
    return tables


LARGEUR = {
    'uint8_t': 8, 'int8_t': 8, 'char': 8,
    'uint16_t': 16, 'int16_t': 16, 'short': 16,
    'uint32_t': 32, 'int32_t': 32, 'int': 32, 'unsigned': 32,
    'unsigned int': 32, 'long': 32, 'unsigned long': 32, 'size_t': 32,
    'TickType_t': 32, 'UBaseType_t': 32, 'BaseType_t': 32, 'esp_err_t': 32,
    'float': 24,
    'uint64_t': 64, 'int64_t': 64, 'long long': 64, 'unsigned long long': 64,
    'double': 53,
}


def normaliser(cible):
    """`s_ecrits[s]` et `s_ecrits[serie]` sont LE MEME site : l'index est une
    variable de boucle. On le vide, sinon la table declaree serait sensible au
    RENOMMAGE D'UNE VARIABLE LOCALE — une gate qui rougit sur un renommage sans
    effet finit par etre desarmee, et c'est comme ca qu'on perd une gate."""
    return re.sub(r'\[[^\]]*\]', '[]', cible)


def resoudre(cible, stat, structs):
    """Rend (type, bits) ou (None, None) si non resolu."""
    morceaux = re.split(r'\.|->', cible)
    base = re.sub(r'\[.*', '', morceaux[0]).strip()
    if base not in stat:
        return (None, None)
    typ = stat[base][1]
    for membre in morceaux[1:]:
        membre = re.sub(r'\[.*', '', membre).strip()
        if typ not in structs or membre not in structs[typ]:
            return (None, None)
        typ = structs[typ][membre]
    return (typ, LARGEUR.get(typ))


BITS_UTILES = {8: 8, 16: 16, 24: 24, 32: 32, 53: 53, 64: 64}
SIGNES = {'int', 'int8_t', 'int16_t', 'int32_t', 'int64_t', 'long', 'long long',
          'short', 'char', 'BaseType_t'}


def portee(typ, bits):
    """Un signe coute un bit : un `int` deborde a 2^31, ⛔ pas 2^32 — et le
    debordement signe est un COMPORTEMENT INDEFINI, donc pire qu'un
    enroulement."""
    return (bits - 1) if typ in SIGNES else bits


# ═══════════════════════════════════════════════════════════════════════════
#  PHASE 3 — LA TABLE DECLAREE
#
#  (classe, cadence, quantite_par_increment, motif)
#    classe  : "OK" survit a 7 j avec marge · "ATTENTION" reboucle mais la
#              parade est ECRITE dans le depot · "BORNE" garde explicite, ne
#              cumule pas · "ROUGE" reboucle sans parade => LA GATE ECHOUE
#    cadence : cle de CADENCES, ou None pour "BORNE"
#
#  ⚠️ « ATTENTION » N'EST PAS UN LAISSER-PASSER : il exige que la parade soit
#     ECRITE quelque part dans le depot, et le motif dit OU. Une parade qu'on
#     ne peut pas citer n'existe pas.
# ═══════════════════════════════════════════════════════════════════════════

_EVT = "compteur d'EVENEMENTS (+1) : l'horizon est 2^n / cadence"

TABLE = {}


def _fam(fichier, cibles, classe, cadence, par_incr, motif):
    for c in cibles:
        TABLE[(fichier, c)] = (classe, cadence, par_incr, motif)


# ── dn_capteurs.c — tache capteurs, 5 000 ms ────────────────────────────────
_fam("dn_capteurs.c",
     ["s_cnt.err_bornes", "s_cnt.err_donnee", "s_cnt.err_i2c", "s_cnt.lectures",
      "s_cnt.pousses_ratees", "s_cnt.reconfigs", "s_cnt.reprises",
      "s_reconf_echecs"],
     "OK", "capteurs", 1, _EVT)

# ── dn_env.c — meme tache (assert statique DN_ENV_PERIODE_MS == DN_CAPT) ────
_fam("dn_env.c",
     ["s_c[].cnt.conformite", "s_c[].cnt.err_bornes", "s_c[].cnt.err_donnee",
      "s_c[].cnt.err_i2c", "s_c[].cnt.lectures", "s_c[].cnt.reprises",
      "s_cycles"],
     "OK", "env", 1, _EVT)
_fam("dn_env.c", ["s_w2[].ruptures"], "OK", "veille_tick", 1,
     "une rupture par tick hors Ambient au plus (dn_env.h:480 : 28 800 en 8 h)")

# ── dn_hist.c ───────────────────────────────────────────────────────────────
_fam("dn_hist.c", ["s_ecrits[]"], "BORNE", None, 1,
     "garde explicite `if (s_ecrits[s] < DN_HIST_N_POINTS)` — ⛔ ne cumule pas")
_fam("dn_hist.c", ["s_rattr_evts"], "OK", "hist", 1, _EVT)
_fam("dn_hist.c", ["s_rattr_trous"], "OK", "hist", 1,
     "cumule des TICKS 1 Hz manques : borne par l'uptime en secondes, "
     "quelle que soit la taille des rafales")
_fam("dn_hist.c", ["s_tick_us"], "OK", "hist", 1000000,
     "int64 : meme en cumulant des microsecondes, l'horizon reste geologique")

# ── dn_link.c — 5 trames/s sur le fil ───────────────────────────────────────
_fam("dn_link.c",
     ["s_cnt.doublons", "s_cnt.pertes_seq", "s_cnt.recues", "s_cnt.rejets_bornes",
      "s_cnt.rejets_checksum", "s_cnt.rejets_format", "s_cnt.rejets_tronquee",
      "s_cnt.rejets_trop_longue", "s_cnt.rejets_version", "s_cnt.reprises",
      "s_cnt.resynchros", "s_lat_n"],
     "OK", "link_trame", 1, _EVT)
_fam("dn_link.c", ["s_lat_somme"], "OK", "link_trame", 1000000,
     "int64 (dn_link.c:191) : cumul de latences en us, horizon geologique")

# ── dn_measure.c — l'ISR de vsync, 37,40 Hz ─────────────────────────────────
_fam("dn_measure.c",
     ["s_vsync_count", "s_bnc_wraps", "s_bnc_manques", "s_bnc_doubles",
      "s_bnc_inter_n", "s_bnc_ph_n", "s_bnc_ph_ecarte", "s_bnc_ret_100",
      "s_bnc_ret_bp", "s_bnc_ret_vb", "s_bnc_ret_trame", "s_bnc_ph_10pc",
      "s_bnc_ph_25pc", "s_bnc_ph_50pc", "s_bnc_ph_100pc",
      # 🆕 dn4-10, 2026-08-27 : les trois compteurs de REJET de la phase. Meme
      #    cadence et meme largeur que leurs voisins — au plus UNE incrementation
      #    par trame, donc l'horizon de la famille. ⛔ Ils etaient BALAYES sans
      #    etre DECLARES, et la gate le criait : « NON CLASSES ».
      "s_bnc_ph_rejete", "s_bnc_ph_doubles_ec", "s_bnc_ph_dechire",
      # 🆕 3e revue du 2026-08-27 : `ph_futur` separe de `ph_rejete` (horodatage
      #    d'enroulement POSTERIEUR a l'entree de l'ISR = entrelacement des deux
      #    ISR, ⛔ pas un retard). Meme cadence, meme largeur.
      #    🎯 CETTE ENTREE A ETE POSEE PARCE QUE LA GATE L'A EXIGEE : elle a
      #       criee « NON CLASSES » au premier tir apres l'ajout du compteur.
      "s_bnc_ph_futur"],
     "OK", "vsync", 1, _EVT)
_fam("dn_measure.c", ["s_bnc_inter_somme", "s_bnc_ph_somme"], "OK", "vsync",
     53400, "uint64 DEJA en place : cumul d'intervalles/phases en us")
_fam("dn_measure.c", ["s_bnc_raz_gen"], "OK", "console", 1,
     "dn4-5/AC1.2 : +1 par RAZ CONSOMMEE, donc a cadence humaine")

# ── dn_recal.c — au plus une bascule par trame ──────────────────────────────
_fam("dn_recal.c", ["s_count", "s_rate"], "OK", "vsync", 1,
     _EVT + " ; majore par le vsync, une bascule ne peut pas aller plus vite")

# ── dn_rtc.c — 500 ms ───────────────────────────────────────────────────────
_fam("dn_rtc.c",
     ["s_cpt.bascules", "s_cpt.err_bcd", "s_cpt.err_i2c", "s_cpt.lectures",
      "s_cpt.os_vus", "s_cpt.poses", "s_cpt.poussees_perdues", "s_cpt.reprises",
      "s_cpt.temoins_perdus"],
     "OK", "rtc", 1, _EVT)
_fam("dn_rtc.c", ["s_generation"], "OK", "console", 1,
     "+1 par pose d'heure : commande console ou reprise de liaison")

# ── dn_stimulus.c — le stimulus flash est une COMMANDE, ⛔ pas un regime ────
_fam("dn_stimulus.c", ["s_flash_bytes"], "OK", "console", 1,
     "uint64 (dn_stimulus.c:376) — et D4 interdit l'ecriture flash en regime")
_fam("dn_stimulus.c", ["s_flash_sectors"], "OK", "console", 1,
     "40 secteurs/s au debit mesure (165 343 o/s / 4 096) : 3,4 ans de "
     "stimulus CONTINU — et D4 l'interdit en regime")
_fam("dn_stimulus.c", ["s_tear_miss_vsync", "s_tear_miss_fbdone"], "OK",
     "vsync", 1, _EVT)

# ── dn_touch.c ──────────────────────────────────────────────────────────────
_fam("dn_touch.c", ["s_lectures", "s_err_i2c", "s_irq"], "OK", "touch_poll", 1,
     _EVT + " ; cadence de scrutation, majorant genereux")
_fam("dn_touch.c", ["s_appuis", "s_relaches", "s_consommes", "s_lat_n",
                    "s_lat_rejets"],
     "OK", "touch_evt", 1, _EVT + " ; majorant de 10 appuis/s")
_fam("dn_touch.c", ["s_lat_total_us"], "ATTENTION", "touch_evt", 100000,
     "cumul de latences en us. PARADE ECRITE : dn_touch.h:306 dit « reboucle a "
     "~4295 s cumulees », et `dn_touch_reset_latence()` (dn_touch.c:1061) rebase")

# ── dn_ui.c ─────────────────────────────────────────────────────────────────
_fam("dn_ui.c", ["s_n_flush", "s_n_cycles", "s_n_noop", "s_timeouts",
                 "s_courbe_appels", "s_courbe_redessins", "s_gardeh_n",
                 "s_gardeh_cris"],
     "OK", "lvgl", 1, _EVT + " ; cadence du cycle LVGL")
_fam("dn_ui.c", ["s_taps", "s_menu_taps", "s_async_refus", "s_clic_seq",
                 "s_menu_reglages", "s_nav_count", "s_nav_veille_count",
                 "s_lat_w", "s_lat_ecrits"],
     "OK", "touch_evt", 1, _EVT + " ; cadence tactile humaine")
_fam("dn_ui.c", ["s_pousse_seq"], "OK", "link_trame", 1, _EVT)
_fam("dn_ui.c", ["s_px"], "ATTENTION", "lvgl", 307200,
     "aire cumulee. PARADE ECRITE : dn_ui.h:171-176 chiffre « ~13 981 ecrans "
     "pleins » et pose « toute mesure publiee part d'un reset » (`flush reset`)")
_fam("dn_ui.c", ["s_copie_us", "s_attente_us"], "ATTENTION", "lvgl", 33000,
     "temps cumule en us. PARADE ECRITE : dn_ui.h:171-176 chiffre « ~4 295 s "
     "de temps CUMULE » et pose le depart depuis un reset")
_fam("dn_ui.c", ["s_voiles_n"], "BORNE", None, 1,
     "garde explicite `if (s_voiles_n < DN_UI_VOILES_MAX)` — ⛔ ne cumule pas")

# ── dn_veille.c ─────────────────────────────────────────────────────────────
_fam("dn_veille.c", ["s_secondes_vues"], "OK", "veille_tick", 1,
     "+1 par seconde : l'horizon EST 2^32 s")
_fam("dn_veille.c", ["s_bascules", "s_reveils", "s_annulations", "s_rebases",
                     "s_inact_bascule_w"],
     "OK", "veille_tick", 1, _EVT + " ; au plus une bascule par tick")
# 🎯 AJOUTE PAR dn4-5 LUI-MEME — et c'est l'audit qui l'a RECLAME : la story a
#    cree ce compteur en T2, l'audit a rougi au tir suivant en le trouvant NON
#    CLASSE. C'est la propriete pour laquelle il existe, vue a l'oeuvre.
_fam("dn_veille.c", ["s_cumul_us[]"], "OK", "veille_tick", 1000000,
     "int64 en microsecondes (dn4-5/AC3.2). Meme en cumulant l'integralite du "
     "temps mural, 2^63 us = 292 471 ANS. ⛔ Et il ne peut pas cumuler plus vite "
     "que l'horloge : la somme des deux modes EST le temps ecoule, une gate le "
     "verifie (`verif_cumul_ambient_dn45.py`)")
_fam("dn_veille.c", ["s_persist_n"], "OK", "console", 1,
     "+1 par ecriture NVS — et D4 les interdit en regime (AC9)")

# ── dn_widget.c ─────────────────────────────────────────────────────────────
_fam("dn_widget.c", ["s_chevauchements", "s_trop_larges"], "OK", "lvgl", 1, _EVT)
_fam("dn_widget.c", ["s_debordements"], "OK", "lvgl", 8,
     "cumule un NOMBRE DE VALEURS qui debordent (≤ 8 par case), ⛔ pas des px")

# ── dn_wifi.c — code MORT en V1 ─────────────────────────────────────────────
_fam("dn_wifi.c", ["s_reconnexions", "s_ws_connexions", "s_ws_messages"],
     "OK", "console", 1,
     "⛔ LE WIFI EST MORT EN V1 (dn2-2, verrou RAM) : ce code ne tourne pas. "
     "Classe OK par INEXECUTION, ⛔ pas par calcul — et c'est ecrit ici")


# ═══════════════════════════════════════════════════════════════════════════
#  PHASE 4 — LES TRONCATURES DE L'HORLOGE 64 BITS
#
#  Famille DISTINCTE des accumulations, et c'est elle que M1 designe :
#  `esp_timer_get_time()` rend un `int64_t` qui ne deborde qu'apres ~292 000
#  ans. Tronque en 32 bits, il reboucle toutes les 4 294,967 s = 71,58 min.
#  Une DIFFERENCE de deux troncatures reste JUSTE tant qu'elle porte sur moins
#  d'un enroulement — c'est la propriete de l'arithmetique non signee, et c'est
#  pour ca que les deltas courts sont sains. Ce qui ne l'est pas, c'est une
#  difference qui peut porter sur PLUS de 71,58 min.
#
#  Detection : (a) tout cast 32 bits d'une expression contenant
#  `esp_timer_get_time()` ; (b) tout cast 32 bits d'une variable `int64_t`
#  initialisee dans la MEME fonction depuis `esp_timer_get_time()`.
# ═══════════════════════════════════════════════════════════════════════════

RE_CAST_DIRECT = re.compile(r'\((?:uint32_t|unsigned|uint16_t)\)\s*\(?[^;\n]*'
                            r'esp_timer_get_time\s*\(\s*\)')
RE_DECL_H64 = re.compile(r'\bint64_t\s+(\w+)\s*=\s*esp_timer_get_time\s*\(\s*\)')
# 🔴 AJOUTE LE 2026-08-27 (revue de code) — ET C'EST UN DEFAUT QUE CETTE GATE A
#    ELLE-MEME PRODUIT. `RE_DECL_H64` exige la declaration ET l'affectation dans
#    LA MEME instruction. Le refactor de dn4-10 a hisse `int64_t maintenant = 0;`
#    hors de la boucle de re-lecture et affecte l'horloge PLUS LOIN : le site
#    `uint32_t t_us = (uint32_t)maintenant;` est devenu INVISIBLE, et la gate a
#    imprime « ⛔ n'existent plus » A PROPOS D'UN SITE QUI TRONQUE TOUJOURS et
#    qui alimente `fenetre_ms_32`. ⛔ Un audit qui annonce la disparition d'un
#    rebouclage vivant est pire que pas d'audit — et son propre docstring promet
#    de « CRIER quand il ne sait pas, jamais d'omettre en silence ».
# ⇒ On ne cherche plus un MOTIF, on resout un NOM : toute variable declaree
#   `int64_t` ET affectee depuis `esp_timer_get_time()` quelque part dans le
#   fichier est porteuse d'horloge, ou que soient les deux evenements.
RE_DECL_I64_NOM = re.compile(r'\bint64_t\s+(\w+)\s*(?:=|;|,)')
RE_AFFECT_HORLOGE = re.compile(r'\b(\w+)\s*=\s*esp_timer_get_time\s*\(\s*\)')
RE_FONCTION = re.compile(r'^[A-Za-z_][\w \t\*]*\b(\w+)\s*\([^;]*\)\s*\{', re.M)

TRONCATURES = {
    ("dn_measure.c", "uint32_t t_us = (uint32_t)esp_timer_get_time();"): (
        "OK", "ISR de vsync : horodatage pris EN TETE. Il n'alimente que des "
        "DELTAS COURTS (`dt` <= 27 ms, `ph` < 2 periodes) — la soustraction non "
        "signee absorbe l'enroulement. ⛔ Il alimentait AUSSI l'origine "
        "`s_bnc_t0_us`, et c'est LA le defaut ferme par dn4-5/AC1.2"),
    ("dn_measure.c", "s_bnc_t_wrap_us = (uint32_t)esp_timer_get_time();"): (
        "OK", "horodatage du dernier enroulement, lu en DELTA COURT uniquement "
        "(`ph = t_us - s_bnc_t_wrap_us`, borne de sanite a 2 periodes)"),
    # ⚠️ CLE MISE A JOUR LE 2026-08-27 : la ligne s'ecrivait
    #    `uint32_t t_us = (uint32_t)maintenant;` jusqu'au refactor de dn4-10, qui
    #    a hisse la declaration hors de la boucle de re-lecture. ⛔ Le site n'a
    #    PAS disparu — seule sa forme a change, et c'est precisement ce que la
    #    gate a annonce a tort comme une disparition.
    ("dn_measure.c", "t_us = (uint32_t)maintenant;"): (
        "ATTENTION", "dn4-5/AC1.2 : CONSERVE VOLONTAIREMENT, et c'est le SEUL de "
        "la liste a etre FAUX PAR CONSTRUCTION au-dela de 71,58 min. Il "
        "n'alimente plus `fenetre_ms` (passee en base int64) mais "
        "`fenetre_ms_32`, publie COMME CONTRE-EPREUVE a cote de la valeur juste. "
        "Sa faussete EST le livrable"),
    # 🆕 DECOUVERT LE 2026-08-27 par la voie « declaration et affectation
    #    SEPAREES ». ⛔ L'ancienne regex ne l'a JAMAIS vu : `up_s` est declare et
    #    affecte dans la meme instruction, mais ce cast-ci est le SECOND de la
    #    fonction et la voie d'origine ne notait que le PREMIER dans 4 000
    #    caracteres. Une gate scopee au premier site epinglait vert le suivant.
    ("dn_hist.c", "return (uint32_t)up_s < couv ? (uint32_t)up_s : couv;"): (
        "OK", "`up_s` est en SECONDES (`esp_timer_get_time() / 1000000`), donc "
        "2^32 s = 136 ans. Et la comparaison est bornee par `couv`, elle-meme "
        "construite sur le meme `up_s`"),
    ("dn_hist.c", "(uint32_t)(up_s % DN_HIST_SEAU_S);"): (
        "OK", "`up_s` est en SECONDES (`esp_timer_get_time() / 1000000`), donc "
        "2^32 s = 136 ans ; et ce site-ci est de surcroit un MODULO borne a "
        "DN_HIST_SEAU_S = 3 600"),
    ("dn_ui.c", "uint32_t s = (uint32_t)(esp_timer_get_time() / 1000000);"): (
        "OK", "des SECONDES, ⛔ pas des us : 136 ans. DEUX sites identiques "
        "(dn_ui.c:2271 et :8366), meme construction"),
    ("dn_ui.c", "uint32_t t1 = (uint32_t)(esp_timer_get_time() - t0);"): (
        "OK", "delta court mesure dans la meme fonction"),
    ("dn_ui.c", "uint32_t t2 = (uint32_t)(esp_timer_get_time() - t0);"): (
        "OK", "delta court mesure dans la meme fonction"),
    ("dn_ui.c", "uint32_t copie = (uint32_t)(t2 - t1);"): (
        "OK", "duree d'UNE copie `draw_bitmap`, entre deux horodatages voisins "
        "de la meme fonction de flush. La TRONCATURE est saine ; c'est "
        "`s_copie_us` qui l'accumule, et elle est classee ⚠️ en phase 3"),
    ("dn_ui.c", "s_attente_us += (uint32_t)(t1 - t0);"): (
        "OK", "la TRONCATURE est saine (delta court) ; c'est l'ACCUMULATION qui "
        "reboucle, et elle est classee ⚠️ en phase 3 avec sa parade"),
    ("dn_veille.c", "s_persist_us = (uint32_t)(esp_timer_get_time() - t0);"): (
        "OK", "duree d'UNE ecriture NVS, entre deux appels voisins. DEUX sites "
        "identiques (dn_veille.c:203 et :218)"),
    ("dn_touch.c", "uint32_t us = (uint32_t)dt;"): (
        "OK", "`dt` est un delta arme/desarme dans la meme sequence tactile ; "
        "les dt negatifs sont COMPTES (`s_lat_rejets`) et rejetes"),
}

RUNTIME_ATTENDU = ("dn_console.c", 2)  # (fichier, nb minimal de gardes `reboucle`)


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 78)
    print("dn4-5 / AC1.1 — AUDIT DE REBOUCLAGE — TOUT firmware/desknode/main/")
    print("=" * 78)

    fichiers = sorted(f for f in os.listdir(MAIN) if f.endswith(('.c', '.h')))
    h = hashlib.sha256()
    for f in fichiers:
        h.update(io.open(os.path.join(MAIN, f), 'rb').read())
    print("\nperimetre : %d fichiers (.c et .h) — sha256 des sources LUES : %s"
          % (len(fichiers), h.hexdigest()[:16]))
    print("commande equivalente, pour qui veut rejouer a la main :")
    print("  grep -rnE '\\\\w+(\\\\.|->)?\\\\w*\\\\s*(\\\\+\\\\+|\\\\+=)' firmware/desknode/main/*.c")

    structs = structs_du_projet()

    # ── PHASES 1 & 2 ────────────────────────────────────────────────────────
    print("\n── 1+2. BALAYAGE DES ACCUMULATIONS ET RESOLUTION DE TYPE ─────────")
    sites = {}
    n_local = 0
    non_resolus = []
    for fn in [f for f in fichiers if f.endswith('.c')]:
        nu = sans_commentaires(io.open(os.path.join(MAIN, fn), encoding='utf-8').read())
        stat = statiques(nu)
        for i, ligne in enumerate(nu.split('\n'), 1):
            for m in list(RE_ACC.finditer(ligne)) + list(RE_ACC_PRE.finditer(ligne)):
                cible = normaliser(re.sub(r'\s+', '', m.group(1)))
                base = re.sub(r'\[.*', '', re.split(r'\.|->', cible)[0])
                if base not in stat:
                    n_local += 1
                    continue
                typ, bits = resoudre(cible, stat, structs)
                if typ is None or bits is None:
                    non_resolus.append((fn, cible))
                sites.setdefault((fn, cible), [typ, bits, []])[2].append(i)

    ctrl(len(sites) > 0, "le balayage a trouve des sites",
         "%d sites persistants, %d accumulations locales ecartees"
         % (len(sites), n_local))
    ctrl(not non_resolus, "tous les types sont RESOLUS",
         "⛔ non resolus : %s" % non_resolus if non_resolus
         else "%d sites, 0 type inconnu" % len(sites))

    # ── PHASE 3 ─────────────────────────────────────────────────────────────
    print("\n── 3. CONFRONTATION A LA TABLE DECLAREE ──────────────────────────")
    manquants = sorted(k for k in sites if k not in TABLE)
    perimes = sorted(k for k in TABLE if k not in sites)
    ctrl(not manquants, "aucun site BALAYE n'est absent de la table",
         "⛔ NON CLASSES : %s" % (manquants[:6],) if manquants
         else "%d sites tous classes" % len(sites))
    ctrl(not perimes, "aucune entree de table n'est perimee",
         "⛔ n'existent plus : %s" % (perimes[:6],) if perimes else "table a jour")

    # ── LE TABLEAU, PAR CLASSE ──────────────────────────────────────────────
    print("\n── L'INVENTAIRE, CHAQUE LIGNE AVEC SON HORIZON CHIFFRE ───────────")
    rouges, attentions, bornes, oks = [], [], [], []
    for (fn, cible), (typ, bits, lignes) in sorted(sites.items()):
        if (fn, cible) not in TABLE:
            continue
        classe, cad, par_incr, motif = TABLE[(fn, cible)]
        if classe == "BORNE":
            hz, src, hz_txt = 0.0, "—", "bornee"
            hs = None  # ⛔ PAS float('inf') : « jamais » se lit « cadence
            #             humaine » dans `humain()`, et un site BORNE n'est pas
            #             un site lent — il ne cumule PAS. Deux etats distincts
            #             ne doivent pas porter le meme libelle.
        else:
            hz, src = CADENCES[cad]
            hs = horizon_s(portee(typ, bits), hz, par_incr)
            hz_txt = "%.2f Hz" % hz if hz else "humaine"
        marque = {"OK": "✅", "ATTENTION": "⚠️", "BORNE": "🔒", "ROUGE": "🔴"}[classe]
        ligne = ("%s %-14s %-24s %-9s %-10s x%-7s %-14s l.%s"
                 % (marque, fn.replace("dn_", "").replace(".c", ""), cible, typ,
                    hz_txt, par_incr,
                    "⛔ ne cumule pas" if hs is None else humain(hs),
                    ",".join(map(str, lignes[:3]))))
        {"OK": oks, "ATTENTION": attentions, "BORNE": bornes,
         "ROUGE": rouges}[classe].append((ligne, motif, hs))

    for titre, groupe, montrer_motif in (
            ("🔴 REBOUCLE SANS PARADE", rouges, True),
            ("⚠️ REBOUCLE, PARADE ECRITE", attentions, True),
            ("🔒 BORNE PAR UNE GARDE", bornes, True),
            ("✅ SURVIT A 7 JOURS", oks, False)):
        print("\n  %s — %d site(s)" % (titre, len(groupe)))
        for ligne, motif, _ in groupe:
            print("   " + ligne)
            if montrer_motif:
                print("       ↳ " + motif)

    # ── LE VERDICT SUR 7 JOURS, CALCULE, ⛔ PAS AFFIRME ─────────────────────
    print("\n── 4. LE SEUIL DE 7 JOURS (604 800 s), APPLIQUE ──────────────────")
    trop_court = [(l, m, hs) for l, m, hs in oks if hs < SEPT_JOURS_S]
    ctrl(not trop_court,
         "aucun site classe ✅ n'a un horizon < 7 jours",
         "⛔ INCOHERENTS : %s" % [l.split()[2] for l, _, _ in trop_court]
         if trop_court else "%d sites ✅, le plus court tient %s"
         % (len(oks), humain(min([hs for _, _, hs in oks]) if oks else 0)))
    ctrl(not rouges, "aucun rebouclage SANS PARADE ne subsiste",
         "⛔ %d site(s) ROUGE" % len(rouges) if rouges
         else "0 rouge — les %d ⚠️ ont tous leur parade CITEE" % len(attentions))

    # ── PHASE 4 ─────────────────────────────────────────────────────────────
    print("\n── 5. LES TRONCATURES DE L'HORLOGE 64 BITS ───────────────────────")
    vus = {}
    for fn in [f for f in fichiers if f.endswith('.c')]:
        nu = sans_commentaires(io.open(os.path.join(MAIN, fn), encoding='utf-8').read())
        lignes = nu.split('\n')

        def noter(idx):
            sig = re.sub(r'\s+', ' ', lignes[idx - 1]).strip()
            vus.setdefault((fn, sig), []).append(idx)

        for i, ligne in enumerate(lignes, 1):
            if RE_CAST_DIRECT.search(ligne):
                noter(i)
        for m in RE_DECL_H64.finditer(nu):
            nom = m.group(1)
            reste = nu[m.end():m.end() + 4000]
            mm = re.search(r'\((?:uint32_t|unsigned)\)\s*\(?\s*'
                           + re.escape(nom) + r'\b', reste)
            if mm:
                noter(nu[:m.end() + mm.start()].count('\n') + 1)

        # 🔴 SECONDE VOIE (2026-08-27) : declaration et affectation SEPAREES.
        #    On resout par le NOM, sur tout le fichier, et on note CHAQUE cast
        #    32 bits de ce nom — ⛔ pas seulement le premier dans 4 000
        #    caracteres, qui etait la seconde faiblesse de la voie ci-dessus.
        porteurs = (set(RE_DECL_I64_NOM.findall(nu))
                    & set(RE_AFFECT_HORLOGE.findall(nu)))
        for nom in sorted(porteurs):
            rc = re.compile(r'\((?:uint32_t|unsigned|uint16_t)\)\s*\(?\s*'
                            + re.escape(nom) + r'\b')
            for i, ligne in enumerate(lignes, 1):
                if rc.search(ligne):
                    noter(i)

    # 🔴 LA CONFRONTATION, ⛔ PAS UN SIMPLE COMPTAGE. Une premiere version de cet
    #    outil imprimait « 13 site(s) — tous classes ci-dessous » sous une table
    #    qui n'en declarait que 7 : un CHIFFRE JUSTE sous une PHRASE FAUSSE,
    #    c'est-a-dire le defaut exact que ce depot traque. On exige l'egalite
    #    des ensembles, dans les DEUX sens.
    inconnus = sorted(k for k in vus if k not in TRONCATURES)
    orphelins = sorted(k for k in TRONCATURES if k not in vus)
    ctrl(not inconnus, "toute troncature balayee est DECLAREE",
         "⛔ NON CLASSEES : %s" % (inconnus[:4],) if inconnus
         else "%d constructions distinctes, %d occurrences"
         % (len(vus), sum(len(v) for v in vus.values())))
    ctrl(not orphelins, "aucune entree de troncature n'est perimee",
         "⛔ n'existent plus : %s" % (orphelins[:4],) if orphelins
         else "table a jour")
    for (fn, sig), (classe, motif) in sorted(TRONCATURES.items()):
        marque = "✅" if classe == "OK" else "⚠️"
        occ = vus.get((fn, sig), [])
        print("   %s %-14s l.%-18s %s"
              % (marque, fn, ",".join(map(str, occ)), sig[:70]))
        print("       ↳ " + motif)

    # ── LE COMPTEUR FreeRTOS, QUI N'EST PAS UNE VARIABLE DU DEPOT ───────────
    fn, mini = RUNTIME_ATTENDU
    txt = io.open(os.path.join(MAIN, fn), encoding='utf-8').read()
    n_garde = txt.count("COMPTEUR REBOUCLE") + txt.count("reboucle = true")
    ctrl(n_garde >= mini,
         "`configRUN_TIME_COUNTER_TYPE` (71,58 min) reste GARDE dans %s" % fn,
         "%d marqueur(s) de garde trouve(s), %d attendu(s)" % (n_garde, mini))

    # ── AC1.2 : LE SITE QUE LA STORY DOIT AVOIR FERME ───────────────────────
    print("\n── 6. AC1.2 — LE SITE NOMME PAR LE CADRAGE EST-IL FERME ? ────────")
    mes = io.open(os.path.join(MAIN, "dn_measure.c"), encoding='utf-8').read()
    ctrl("out->fenetre_ms = (t_us - s_bnc_t0_us) / 1000u;" not in mes,
         "la formule 32 bits d'origine a DISPARU de dn_measure.c",
         "⛔ elle est encore la" if "out->fenetre_ms = (t_us - s_bnc_t0_us)" in mes
         else "remplacee par la base int64")
    ctrl("s_bnc_t0_us64" in mes and "s_bnc_arme_us64" in mes,
         "l'origine est reconstruite sur 64 bits", "ancre + origine presentes")
    hdr = io.open(os.path.join(MAIN, "dn_measure.h"), encoding='utf-8').read()
    ctrl("uint64_t fenetre_ms;" in hdr,
         "`fenetre_ms` est publie sur 64 bits", "dn_measure.h")
    ctrl("fenetre_deborde" in hdr and "fenetre_ms_32" in hdr,
         "la contre-epreuve est publiee a cote", "fenetre_ms_32 + fenetre_deborde")

    print("\n" + "=" * 78)
    print("BILAN : %d OK, %d KO" % (ok_total[0], ko_total[0]))
    print("=" * 78)
    return 1 if ko_total[0] else 0


if __name__ == "__main__":
    sys.exit(main())
