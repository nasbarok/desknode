#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dn4-5 / AC1.2 + AC1.3 — LA FENETRE DE `flush` NE REBOUCLE PLUS, ET ON L'A VU
CRIER. EPROUVE EN **EXECUTANT LE PRODUIT**, DEPUIS WSL, SANS CARTE.

======================= CE QUE CET OUTIL FAIT, ET POURQUOI ==================

⛔ IL NE REJOUE RIEN. `dn_measure.c` est COMPILE EN ENTIER et APPELE. Les seules
   pieces de papier sont les en-tetes ESP-IDF/FreeRTOS, remplaces par des
   coquilles minimales — et l'une d'elles, `esp_timer_get_time()`, est
   PILOTABLE : c'est ce qui permet de franchir les 71,58 min sans attendre
   71,58 min. ⚠️ Le franchissement reste a confirmer SUR LA CARTE pendant le
   soak (AC3), ou la fenetre depassera le seuil pour de vrai ; cette gate-ci
   prouve la LOGIQUE, ⛔ pas le silicium, et elle le dit.

🔴 LES TEMOINS NEGATIFS SONT DES MUTATIONS COMPILEES ET EXECUTEES. On casse la
   garde, on recompile, on rappelle, et on EXIGE de voir le defaut d'origine
   revenir. Trois mutants, parce que le correctif a trois proprietes distinctes
   et qu'un seul mutant n'en couvrirait qu'une :
     A. la base 64 bits elle-meme ;
     B. la correction d'enroulement entre l'ARMEMENT et la CONSOMMATION ;
     C. le choix d'ancrer sur l'ARMEMENT plutot que sur l'INSTANT COURANT —
        c'est le mutant le plus important, parce que c'est le seul defaut qui
        serait INVISIBLE en campagne courte et FATAL en soak.

⚠️ LA STRUCTURE N'EST PAS RECOPIEE A LA MAIN : elle est PARSEE depuis
   `dn_measure.h` et reconstruite en ctypes, puis `sizeof` et `offsetof` sont
   CONFRONTES a ceux que le C calcule. Une structure recopiee derive en silence,
   et une gate qui lit les mauvais octets rend des chiffres plausibles.

Sortie : exit 0 si tout passe, 1 sinon. Publie le sha256 des sources LUES.
"""

import ctypes
import hashlib
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(RACINE, "firmware", "desknode", "main")
DN_MEASURE_C = os.path.join(MAIN, "dn_measure.c")
DN_MEASURE_H = os.path.join(MAIN, "dn_measure.h")
DN_MEASURE_SERIE_H = os.path.join(MAIN, "dn_measure_serie.h")
DN_PINS_H = os.path.join(MAIN, "dn_pins.h")

ok_total = [0]
ko_total = [0]
_tmp = []

SEUIL_US = 4294967296  # 2^32


def sans_commentaires(txt):
    """⚠️ INDISPENSABLE POUR TOUT CONTROLE QUI COMPTE. Ce depot documente
    massivement, et `dn_measure.c` CITE `esp_timer_get_time()` dans un
    commentaire juste au-dessus de l'appel reel : compter sur le texte brut
    rendait « 2 appels » la ou il y en a UN. Un instrument qui compte ce qui
    n'est pas execute fabrique un defaut — ici il a failli en fabriquer un
    contre le produit."""
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
        else:
            out.append(c)
            i += 1
    return ''.join(out)


def lire(chemin):
    with open(chemin, "rb") as f:
        brut = f.read()
    return brut.decode("utf-8"), hashlib.sha256(brut).hexdigest()[:16]


def ctrl(ok, libelle, detail=""):
    if ok:
        ok_total[0] += 1
        print("  [OK ] %-56s %s" % (libelle, detail))
    else:
        ko_total[0] += 1
        print("  [KO ] %-56s %s" % (libelle, detail))
    return ok


def tmpdir():
    d = tempfile.mkdtemp(prefix="dn45_")
    _tmp.append(d)
    return d


# ═══════════════════════════════════════════════════════════════════════════
#  LES COQUILLES
# ═══════════════════════════════════════════════════════════════════════════

SHIM_ESP_ERR = """
#pragma once
#include <stdint.h>
typedef int esp_err_t;
#define ESP_OK 0
#define ESP_FAIL -1
#define ESP_ERR_NO_MEM 0x101
#define ESP_ERR_INVALID_ARG 0x102
static inline const char *esp_err_to_name(esp_err_t e) { (void)e; return "ERR"; }
"""

SHIM_ESP_ATTR = """
#pragma once
#define IRAM_ATTR
#define DRAM_ATTR
"""

SHIM_ESP_CHECK = """
#pragma once
#include "esp_err.h"
#include "esp_log.h"
#define ESP_RETURN_ON_FALSE(a, err, tag, fmt, ...) \\
    do { if (!(a)) { return (err); } } while (0)
#define ESP_RETURN_ON_ERROR(x, tag, fmt, ...) \\
    do { esp_err_t r_ = (x); if (r_ != ESP_OK) { return r_; } } while (0)
"""

SHIM_ESP_LOG = """
#pragma once
#include <stdio.h>
extern int g_logs;
#define ESP_LOGI(t, ...) do { g_logs++; } while (0)
#define ESP_LOGW(t, ...) do { g_logs++; } while (0)
#define ESP_LOGE(t, ...) do { g_logs++; } while (0)
#define ESP_LOGD(t, ...) do { } while (0)
"""

# 🎯 L'HORLOGE PILOTABLE. C'est la seule coquille qui MENT sciemment, et c'est
#    exactement ce qu'on lui demande : franchir 2^32 us sans attendre 71,58 min.
SHIM_ESP_TIMER = """
#pragma once
#include <stdint.h>
extern int64_t g_temps_us;
int64_t esp_timer_get_time(void);
"""

SHIM_HEAP = """
#pragma once
#include <stddef.h>
#define MALLOC_CAP_SPIRAM 1
#define MALLOC_CAP_INTERNAL 2
size_t heap_caps_get_free_size(unsigned caps);
"""

SHIM_LCD_TYPES = """
#pragma once
typedef struct esp_lcd_panel_t *esp_lcd_panel_handle_t;
"""

SHIM_LCD_RGB = """
#pragma once
#include <stdbool.h>
#include <stdint.h>
#include "esp_err.h"
#include "esp_lcd_types.h"
typedef struct { int dummy; } esp_lcd_rgb_panel_event_data_t;
typedef bool (*esp_lcd_rgb_panel_vsync_cb_t)(
    esp_lcd_panel_handle_t, const esp_lcd_rgb_panel_event_data_t *, void *);
typedef struct {
    esp_lcd_rgb_panel_vsync_cb_t on_vsync;
    esp_lcd_rgb_panel_vsync_cb_t on_bounce_empty;
    esp_lcd_rgb_panel_vsync_cb_t on_bounce_frame_finish;
    esp_lcd_rgb_panel_vsync_cb_t on_frame_buf_complete;
} esp_lcd_rgb_panel_event_callbacks_t;
esp_err_t esp_lcd_rgb_panel_register_event_callbacks(
    esp_lcd_panel_handle_t, const esp_lcd_rgb_panel_event_callbacks_t *, void *);
esp_err_t esp_lcd_rgb_panel_restart(esp_lcd_panel_handle_t);
"""

SHIM_FREERTOS = """
#pragma once
#include <stdint.h>
#include <stdbool.h>
typedef int BaseType_t;
typedef unsigned UBaseType_t;
typedef uint32_t TickType_t;
#define pdTRUE 1
#define pdFALSE 0
#define pdMS_TO_TICKS(x) (x)
#define portTICK_PERIOD_MS 1
"""

SHIM_SEMPHR = """
#pragma once
#include "freertos/FreeRTOS.h"
typedef void *SemaphoreHandle_t;
SemaphoreHandle_t xSemaphoreCreateBinary(void);
BaseType_t xSemaphoreGiveFromISR(SemaphoreHandle_t, BaseType_t *);
BaseType_t xSemaphoreTake(SemaphoreHandle_t, TickType_t);
"""

SHIM_TASK = """
#pragma once
#include "freertos/FreeRTOS.h"
void vTaskDelay(TickType_t);
"""

# `dn_pins.h` est copie VERBATIM (c'est lui qui porte les timings de la dalle,
# donc DN_PERIODE_US) : il tire deux en-tetes de driver dont dn_measure.c
# n'utilise RIEN. Deux coquilles vides suffisent, et les recopier serait pire.
SHIM_I2C = """
#pragma once
#include <stdint.h>
typedef struct i2c_master_bus_t *i2c_master_bus_handle_t;
typedef struct i2c_master_dev_t *i2c_master_dev_handle_t;
"""

SHIM_IOEXP = """
#pragma once
typedef struct esp_io_expander_s esp_io_expander_t;
typedef esp_io_expander_t *esp_io_expander_handle_t;
"""

SHIM_BOOTCFG = """
#pragma once
#include <stdint.h>
/* ⚠️ COQUILLE, ⛔ PAS LE PRODUIT. `dn_measure.c` a acquis une dependance sur
 *    `dn_bootcfg.h` le 2026-08-27 pour UNE SEULE ligne de log (le rappel de
 *    `set bounce <defaut>` quand les seuils sont desarmes). Rien de ce que
 *    cette gate prouve — le rebouclage 32 bits de la fenetre — ne depend de
 *    cette valeur. On declare donc le prototype et `shim.c` en donne une
 *    definition SENTINELLE, ⛔ pas le vrai defaut : si un controle venait un
 *    jour a lire ce nombre, il lirait un chiffre impossible et le dirait. */
int dn_bootcfg_defaut_bounce_px(void);
"""

SHIM_DISPLAY = """
#pragma once
#include <stdint.h>
unsigned dn_display_bounce_px(void);
"""

# ⚠️ Le pilote de l'ISR. Il capture les callbacks que `dn_measure_attach()`
#    enregistre, EXACTEMENT comme le driver RGB le ferait — donc la gate appelle
#    la VRAIE `on_vsync`, qui est `static` et ne pourrait pas etre appelee
#    autrement. ⛔ Pas de copie de l'ISR : c'est le produit qui tourne.
SHIM_C = """
#include <stddef.h>
#include <stdlib.h>
#include "dn_measure.h"
#include "esp_lcd_panel_rgb.h"
#include "freertos/semphr.h"
#include "freertos/task.h"

int g_logs = 0;
int64_t g_temps_us = 0;

int64_t esp_timer_get_time(void) { return g_temps_us; }
size_t heap_caps_get_free_size(unsigned caps) { (void)caps; return 123456; }
unsigned dn_display_bounce_px(void) { return 9600; }

static char s_sems[8];
static int s_n_sem = 0;
SemaphoreHandle_t xSemaphoreCreateBinary(void)
{ return (SemaphoreHandle_t)&s_sems[s_n_sem++ % 8]; }
BaseType_t xSemaphoreGiveFromISR(SemaphoreHandle_t h, BaseType_t *hp)
{ (void)h; if (hp) { *hp = pdFALSE; } return pdTRUE; }
BaseType_t xSemaphoreTake(SemaphoreHandle_t h, TickType_t t)
{ (void)h; (void)t; return pdFALSE; }
void vTaskDelay(TickType_t t) { (void)t; }

static esp_lcd_rgb_panel_event_callbacks_t s_cbs;
esp_err_t esp_lcd_rgb_panel_register_event_callbacks(
    esp_lcd_panel_handle_t p, const esp_lcd_rgb_panel_event_callbacks_t *cbs,
    void *ctx)
{ (void)p; (void)ctx; s_cbs = *cbs; return ESP_OK; }
esp_err_t esp_lcd_rgb_panel_restart(esp_lcd_panel_handle_t p)
{ (void)p; return ESP_OK; }

/* Un tour de trame COMPLET : l'ISR d'enroulement puis celle de vsync, dans
 * l'ordre reel (le trans-EOF tombe AVANT VSYNC_END). */
/* ⛔ SENTINELLE, ⛔ PAS LE DEFAUT DU PRODUIT (9 600). Voir SHIM_BOOTCFG. */
int dn_bootcfg_defaut_bounce_px(void) { return -1; }

void shim_trame(void)
{
    esp_lcd_rgb_panel_event_data_t d = {0};
    if (s_cbs.on_frame_buf_complete) { s_cbs.on_frame_buf_complete(NULL, &d, NULL); }
    if (s_cbs.on_vsync) { s_cbs.on_vsync(NULL, &d, NULL); }
}
int shim_cbs_poses(void) { return s_cbs.on_vsync != NULL &&
                                  s_cbs.on_frame_buf_complete != NULL; }
size_t shim_sizeof_stats(void) { return sizeof(dn_bounce_stats_t); }
size_t shim_offset_fenetre(void) { return offsetof(dn_bounce_stats_t, fenetre_ms); }
size_t shim_offset_f32(void) { return offsetof(dn_bounce_stats_t, fenetre_ms_32); }
size_t shim_offset_deborde(void) { return offsetof(dn_bounce_stats_t, fenetre_deborde); }
"""


# ═══════════════════════════════════════════════════════════════════════════
#  LA STRUCTURE — PARSEE DEPUIS L'EN-TETE, ⛔ PAS RECOPIEE
# ═══════════════════════════════════════════════════════════════════════════

CT = {"uint8_t": ctypes.c_uint8, "int8_t": ctypes.c_int8,
      "uint16_t": ctypes.c_uint16, "int16_t": ctypes.c_int16,
      "uint32_t": ctypes.c_uint32, "int32_t": ctypes.c_int32,
      "uint64_t": ctypes.c_uint64, "int64_t": ctypes.c_int64,
      "bool": ctypes.c_bool, "int": ctypes.c_int, "unsigned": ctypes.c_uint}


def struct_depuis_entete(txt_h):
    m = re.search(r'typedef struct \{(.*?)\} dn_bounce_stats_t;', txt_h, re.S)
    if not m:
        return None, "⛔ `dn_bounce_stats_t` INTROUVABLE dans dn_measure.h"
    corps = re.sub(r'/\*.*?\*/', ' ', m.group(1), flags=re.S)
    champs = []
    for decl in corps.split(';'):
        decl = re.sub(r'\s+', ' ', decl).strip()
        if not decl:
            continue
        mm = re.match(r'([A-Za-z_]\w*) (.+)$', decl)
        if not mm or mm.group(1) not in CT:
            return None, "⛔ champ non traduisible : « %s »" % decl
        for nom in mm.group(2).split(','):
            nom = nom.strip()
            if not re.fullmatch(r'\w+', nom):
                return None, "⛔ nom de champ inattendu : « %s »" % nom
            champs.append((nom, CT[mm.group(1)]))
    return type("Bounce", (ctypes.Structure,), {"_fields_": champs}), \
        "%d champs" % len(champs)


# ═══════════════════════════════════════════════════════════════════════════
#  CONSTRUCTION
# ═══════════════════════════════════════════════════════════════════════════

# ⚠️ TABLE DES COQUILLES, HISSEE AU NIVEAU MODULE LE 2026-08-27 (revue de code).
#    Elle etait enfermee dans `construire()`, donc RIEN ne pouvait la relire — et
#    le jour ou `dn_measure.c` a acquis un `#include "dn_bootcfg.h"` pour une
#    seule ligne de log, la gate est morte a la COMPILATION en rendant
#    « [KO] la gate n'a RIEN pu eprouver », ⛔ sans nommer la cause. Elle est
#    desormais LISIBLE, et `includes_locaux_orphelins()` la confronte au produit.
SHIMS = (("esp_err.h", SHIM_ESP_ERR), ("esp_attr.h", SHIM_ESP_ATTR),
         ("esp_check.h", SHIM_ESP_CHECK), ("esp_log.h", SHIM_ESP_LOG),
         ("esp_timer.h", SHIM_ESP_TIMER), ("esp_heap_caps.h", SHIM_HEAP),
         ("esp_lcd_types.h", SHIM_LCD_TYPES),
         ("esp_lcd_panel_rgb.h", SHIM_LCD_RGB),
         ("dn_display.h", SHIM_DISPLAY),
         ("dn_bootcfg.h", SHIM_BOOTCFG),
         ("driver/i2c_master.h", SHIM_I2C),
         ("esp_io_expander.h", SHIM_IOEXP),
         ("freertos/FreeRTOS.h", SHIM_FREERTOS),
         ("freertos/semphr.h", SHIM_SEMPHR),
         ("freertos/task.h", SHIM_TASK),
         ("shim.c", SHIM_C))

# Ce que `construire()` copie VERBATIM du depot, en plus des coquilles.
# 🔴 `dn_measure_serie.h` AJOUTE LE 2026-08-28 (dn4-12) DANS LE MEME GESTE QUE
#    l'`#include` qui l'a fait naitre. C'est l'unite pure de la machine a etats
#    de serie consecutive ; sans cette ligne ET la copie dans `construire()`,
#    cette gate meurt A LA COMPILATION en rendant « la gate n'a RIEN pu
#    eprouver », ⛔ sans nommer la cause — l'incident `dn_bootcfg.h` du
#    2026-08-27, a l'identique. ⛔ Ce n'est PAS une coquille : c'est le PRODUIT,
#    copie verbatim, parce que c'est lui qu'on eprouve.
COPIES = ("dn_measure.h", "dn_pins.h", "dn_measure_serie.h")


def includes_locaux_orphelins(src_c):
    """🔴 LE CRI QUI MANQUAIT. Rend la liste des `#include "..."` de
    `dn_measure.c` que la gate ne fournit NI en copie NI en coquille. Un tel
    include tue la compilation, donc la gate entiere, et le seul symptome etait
    un `[KO]` generique. ⛔ Les includes CITES dans les commentaires ne comptent
    pas : ce depot documente massivement et en cite plusieurs."""
    fournis = set(n for n, _ in SHIMS) | set(COPIES)
    orphelins = []
    for ligne in sans_commentaires(src_c).splitlines():
        m = re.match(r'\s*#\s*include\s*"([^"]+)"', ligne)
        if m and m.group(1) not in fournis:
            orphelins.append(m.group(1))
    return orphelins


def construire(src_c, etiquette):
    d = tmpdir()
    os.makedirs(os.path.join(d, "freertos"), exist_ok=True)
    os.makedirs(os.path.join(d, "driver"), exist_ok=True)
    for nom, contenu in SHIMS:
        with io.open(os.path.join(d, nom), "w", encoding="utf-8") as f:
            f.write(contenu)
    # ⚠️ COPIES VERBATIM du depot : l'en-tete et les timings. Si l'un des deux
    #    changeait, la gate compilerait AUTRE CHOSE que le produit.
    for src in (DN_MEASURE_H, DN_PINS_H, DN_MEASURE_SERIE_H):
        shutil.copy(src, os.path.join(d, os.path.basename(src)))
    with io.open(os.path.join(d, "dn_measure.c"), "w", encoding="utf-8") as f:
        f.write(src_c)
    so = os.path.join(d, "libm.so")
    r = subprocess.run(["cc", "-shared", "-fPIC", "-O0", "-I", d, "-o", so,
                        os.path.join(d, "dn_measure.c"), os.path.join(d, "shim.c")],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("     ECHEC DE COMPILATION (%s) :\n%s" % (etiquette, r.stderr[:2500]))
        return None
    return ctypes.CDLL(so)


class Banc:
    """Un banc = une bibliotheque chargee + les accesseurs. ⚠️ Chaque mutant a
    SON banc : les statiques de `dn_measure.c` sont globales au .so, et rejouer
    deux scenarios dans le meme .so les ferait s'empoisonner."""

    def __init__(self, lib, Bounce):
        self.lib = lib
        self.Bounce = Bounce
        lib.dn_measure_attach.restype = ctypes.c_int
        lib.dn_measure_attach.argtypes = [ctypes.c_void_p]
        lib.dn_measure_bounce_get.argtypes = [ctypes.c_void_p]
        lib.shim_sizeof_stats.restype = ctypes.c_size_t
        lib.shim_offset_fenetre.restype = ctypes.c_size_t
        lib.shim_offset_f32.restype = ctypes.c_size_t
        lib.shim_offset_deborde.restype = ctypes.c_size_t
        lib.shim_cbs_poses.restype = ctypes.c_int

    def t(self, us):
        ctypes.c_int64.in_dll(self.lib, "g_temps_us").value = int(us)

    def trame(self):
        self.lib.shim_trame()

    def raz(self):
        self.lib.dn_measure_bounce_reset()

    def lire(self):
        b = self.Bounce()
        self.lib.dn_measure_bounce_get(ctypes.byref(b))
        return b


def banc(src, etiquette, Bounce):
    lib = construire(src, etiquette)
    if lib is None:
        return None
    b = Banc(lib, Bounce)
    b.lib.dn_measure_attach(None)
    return b


# ═══════════════════════════════════════════════════════════════════════════
#  LES SCENARIOS — chacun rend un dict de grandeurs, ⛔ pas un verdict.
#  C'est ce qui permet de rejouer LE MEME scenario sur un mutant et de
#  comparer : un scenario qui portait son propre verdict ne servirait qu'une
#  fois.
# ═══════════════════════════════════════════════════════════════════════════

T0 = 1_000_000  # une seconde d'uptime avant la RAZ, pour ne pas partir de 0


def scenario_franchissement(b, minutes):
    """RAZ a T0, puis on avance de `minutes` et on lit."""
    b.t(T0)
    b.trame()
    b.raz()
    b.t(T0 + 20_000)   # l'ISR consomme la RAZ ~20 ms plus tard, comme en vrai
    b.trame()
    b.t(T0 + 20_000 + int(minutes * 60 * 1_000_000))
    s = b.lire()
    return {"fenetre_ms": s.fenetre_ms, "f32": s.fenetre_ms_32,
            "deborde": bool(s.fenetre_deborde), "attendu_ms": int(minutes * 60_000)}


def scenario_enroulement(b):
    """L'ARMEMENT tombe AVANT l'enroulement 32 bits, la CONSOMMATION APRES.
    C'est le cas qui distingue une reconstruction juste d'une reconstruction
    qui se contente de recoller les bits hauts."""
    arme = SEUIL_US - 5_000
    b.t(arme)
    b.trame()
    b.raz()
    b.t(SEUIL_US + 5_000)   # +10 ms : l'ISR consomme APRES l'enroulement
    b.trame()
    b.t(SEUIL_US + 5_000 + 600 * 1_000_000)  # 10 min plus tard
    s = b.lire()
    return {"fenetre_ms": s.fenetre_ms, "attendu_ms": 600_000,
            "deborde": bool(s.fenetre_deborde)}


def scenario_long_silence(b):
    """RAZ, puis PERSONNE NE RELIT PENDANT DES HEURES. C'est le regime du soak,
    et c'est ce que casse une reconstruction ancree sur l'instant COURANT."""
    b.t(T0)
    b.trame()
    b.raz()
    b.t(T0 + 20_000)
    b.trame()
    b.t(T0 + 20_000 + 5 * 3600 * 1_000_000)  # 5 h de silence
    s = b.lire()
    return {"fenetre_ms": s.fenetre_ms, "attendu_ms": 5 * 3600 * 1000,
            "deborde": bool(s.fenetre_deborde)}


def scenario_depuis_boot(b):
    """Aucune RAZ : la fenetre DOIT etre l'uptime — ce qu'elle a toujours ete."""
    b.t(3 * 3600 * 1_000_000)  # 3 h d'uptime
    b.trame()
    s = b.lire()
    return {"fenetre_ms": s.fenetre_ms, "attendu_ms": 3 * 3600 * 1000,
            "deborde": bool(s.fenetre_deborde)}


# ═══════════════════════════════════════════════════════════════════════════
#  LES MUTANTS — trois proprietes distinctes du correctif, trois mutations
# ═══════════════════════════════════════════════════════════════════════════

MUTANTS = {
    "A. base 64 bits supprimee": (
        "    out->fenetre_ms = (uint64_t)fen_us / 1000u;",
        "    out->fenetre_ms = (uint64_t)((t_us - s_bnc_t0_us) / 1000u);"),
    "B. correction d'enroulement supprimee": (
        "            cand += 0x100000000LL;",
        "            cand += 0;"),
    "C. ancre sur l'instant COURANT au lieu de l'ARMEMENT": (
        "        int64_t cand = (s_bnc_arme_us64 & ~0xFFFFFFFFLL) | (int64_t)s_bnc_t0_us;\n"
        "        if (cand < s_bnc_arme_us64) {",
        "        int64_t cand = (maintenant & ~0xFFFFFFFFLL) | (int64_t)s_bnc_t0_us;\n"
        "        if (cand > maintenant) {"),
}


def muter(src, cle):
    avant, apres = MUTANTS[cle]
    if src.count(avant) != 1:
        return None
    return src.replace(avant, apres, 1)


def main():
    print("=" * 78)
    print("dn4-5 / AC1.2 + AC1.3 — LA FENETRE NE REBOUCLE PLUS, ET ON L'A VU CRIER")
    print("=" * 78)

    src, sha_c = lire(DN_MEASURE_C)
    txt_h, sha_h = lire(DN_MEASURE_H)
    print("\nsources LUES : dn_measure.c %s · dn_measure.h %s" % (sha_c, sha_h))
    print("⚠️ horloge PILOTEE : le franchissement des 71,58 min est prouve en")
    print("   LOGIQUE, ⛔ pas sur le silicium. La confirmation carte est AC3.")

    # ── 0. LA STRUCTURE ─────────────────────────────────────────────────────
    print("\n── 0. LA STRUCTURE, PARSEE DEPUIS L'EN-TETE ──────────────────────")
    Bounce, det = struct_depuis_entete(txt_h)
    if not ctrl(Bounce is not None, "`dn_bounce_stats_t` traduite en ctypes", det):
        return 1

    orph = includes_locaux_orphelins(src)
    ctrl(not orph,
         "aucun `#include` local de dn_measure.c n'est ORPHELIN",
         "%d fournis (coquilles + copies)" % (len(SHIMS) - 1 + len(COPIES))
         if not orph else "⛔ NI COPIE NI COQUILLE : %s ⇒ la gate NE COMPILERA PAS" % orph)

    b = banc(src, "produit", Bounce)
    if not ctrl(b is not None, "dn_measure.c COMPILE ET CHARGE",
                "⛔ la gate n'a RIEN pu eprouver" if b is None else "cc -O0"):
        return 1
    ctrl(b.lib.shim_cbs_poses() == 1,
         "`dn_measure_attach()` a bien pose les DEUX callbacks",
         "on_vsync + on_frame_buf_complete captures par la coquille")
    n_c = b.lib.shim_sizeof_stats()
    n_py = ctypes.sizeof(Bounce)
    ctrl(n_c == n_py, "sizeof(dn_bounce_stats_t) : C == ctypes",
         "%d o des deux cotes" % n_c if n_c == n_py else "🔴 C=%d ctypes=%d" % (n_c, n_py))
    for nom, f in (("fenetre_ms", b.lib.shim_offset_fenetre),
                   ("fenetre_ms_32", b.lib.shim_offset_f32),
                   ("fenetre_deborde", b.lib.shim_offset_deborde)):
        oc, op = f(), getattr(Bounce, nom).offset
        ctrl(oc == op, "offsetof(%s) : C == ctypes" % nom,
             "%d" % oc if oc == op else "🔴 C=%d ctypes=%d" % (oc, op))

    # ── 1. SOUS LE SEUIL ────────────────────────────────────────────────────
    print("\n── 1. SOUS LE SEUIL (30 min) — LES DEUX VUES DOIVENT COINCIDER ───")
    r30 = scenario_franchissement(banc(src, "30min", Bounce), 30)
    ctrl(r30["fenetre_ms"] == r30["attendu_ms"], "fenetre_ms JUSTE",
         "%d ms attendus, %d publies" % (r30["attendu_ms"], r30["fenetre_ms"]))
    ctrl(r30["f32"] == r30["attendu_ms"], "la vue 32 bits dit encore la VERITE",
         "%d ms" % r30["f32"])
    ctrl(not r30["deborde"], "aucun cri sous le seuil",
         "⛔ crier au loup a 30 min serait pire que pas de garde")

    # ── 2. AU-DELA DU SEUIL — LA CAPTURE AVANT/APRES D'AC1.2 ────────────────
    print("\n── 2. AU-DELA DU SEUIL (90 min) — LE MENSONGE EST CAPTURE ────────")
    r90 = scenario_franchissement(banc(src, "90min", Bounce), 90)
    ctrl(r90["fenetre_ms"] == r90["attendu_ms"], "fenetre_ms JUSTE au-dela de 71,58 min",
         "%d ms attendus, %d publies" % (r90["attendu_ms"], r90["fenetre_ms"]))
    ment = r90["attendu_ms"] - r90["f32"]
    ctrl(r90["f32"] < r90["attendu_ms"] and abs(ment - SEUIL_US // 1000) <= 1,
         "la vue 32 bits MENT d'exactement un enroulement",
         "elle publie %d ms au lieu de %d — soit %d ms de MOINS (2^32 us = %d ms)"
         % (r90["f32"], r90["attendu_ms"], ment, SEUIL_US // 1000))
    ctrl(r90["deborde"], "le drapeau de debordement est LEVE",
         "c'est lui qui declenche le cri de `flush`")

    print("     ╭─ LA CAPTURE D'AC1.2, LES DEUX COTES DU SEUIL ──────────────╮")
    print("     │  30 min : juste %9d ms · a l'ancienne %9d ms  │"
          % (r30["fenetre_ms"], r30["f32"]))
    print("     │  90 min : juste %9d ms · a l'ancienne %9d ms  │"
          % (r90["fenetre_ms"], r90["f32"]))
    print("     ╰────────────────────────────────────────────────────────────╯")

    # ── 3. LES CAS QUI SEPARENT UNE VRAIE RECONSTRUCTION D'UNE APPROXIMATION ─
    print("\n── 3. LES CAS DE BORD ────────────────────────────────────────────")
    renr = scenario_enroulement(banc(src, "enroulement", Bounce))
    ctrl(renr["fenetre_ms"] == renr["attendu_ms"],
         "RAZ armee AVANT l'enroulement, consommee APRES",
         "%d ms attendus, %d publies" % (renr["attendu_ms"], renr["fenetre_ms"]))
    rsil = scenario_long_silence(banc(src, "silence", Bounce))
    ctrl(rsil["fenetre_ms"] == rsil["attendu_ms"],
         "5 h de silence entre la RAZ et la lecture",
         "%d ms attendus, %d publies" % (rsil["attendu_ms"], rsil["fenetre_ms"]))
    rboot = scenario_depuis_boot(banc(src, "boot", Bounce))
    ctrl(rboot["fenetre_ms"] == rboot["attendu_ms"],
         "SANS AUCUNE RAZ, la fenetre est l'uptime",
         "%d ms attendus, %d publies" % (rboot["attendu_ms"], rboot["fenetre_ms"]))

    # ── 4. LES MUTANTS ──────────────────────────────────────────────────────
    print("\n── 4. LES TEMOINS NEGATIFS — ON DOIT LES VOIR ROUGIR ─────────────")
    attendus = {
        "A. base 64 bits supprimee":
            (lambda bb: scenario_franchissement(bb, 90),
             lambda r: r["fenetre_ms"] != r["attendu_ms"],
             "la fenetre a 90 min doit redevenir FAUSSE"),
        "B. correction d'enroulement supprimee":
            (scenario_enroulement,
             lambda r: r["fenetre_ms"] != r["attendu_ms"],
             "la RAZ a cheval sur l'enroulement doit redevenir FAUSSE"),
        "C. ancre sur l'instant COURANT au lieu de l'ARMEMENT":
            (scenario_long_silence,
             lambda r: r["fenetre_ms"] != r["attendu_ms"],
             "5 h de silence doit redevenir FAUX"),
    }
    for cle, (scen, casse, quoi) in attendus.items():
        mut = muter(src, cle)
        if not ctrl(mut is not None, "mutant « %s » : la mutation s'applique" % cle[:2],
                    "⛔ motif introuvable ou multiple — LA GATE NE MUTE RIEN"
                    if mut is None else "1 occurrence"):
            continue
        bm = banc(mut, "mutant " + cle, Bounce)
        if not ctrl(bm is not None, "mutant « %s » : compile" % cle[:2],
                    "" if bm else "⛔ ne compile pas"):
            continue
        r = scen(bm)
        ctrl(casse(r), "mutant « %s » : VU ROUGIR" % cle[:2],
             "%s — publie %d ms au lieu de %d"
             % (quoi, r["fenetre_ms"], r["attendu_ms"]))

    # ── 5. LE PRODUIT EST-IL RESTE INTACT ? ─────────────────────────────────
    print("\n── 5. L'INVARIANT DE CONCURRENCE N'A PAS BOUGE ───────────────────")
    ctrl("portENTER_CRITICAL" not in sans_commentaires(src)
         and "taskENTER_CRITICAL" not in sans_commentaires(src),
         "⛔ AUCUN verrou introduit dans dn_measure.c",
         "« on mesure une famine, on ne va pas la fabriquer »")
    # ⛔ SUR LE TEXTE DEPOUSSIERE : voir `sans_commentaires()`.
    src_nu = sans_commentaires(src)
    corps_isr = src_nu[src_nu.index("static IRAM_ATTR bool on_vsync"):
                       src_nu.index("static IRAM_ATTR bool on_frame_buf_complete")]
    hors_raz = corps_isr[corps_isr.index("} else {"):]
    ctrl("s_bnc_raz_gen" not in hors_raz,
         "le compteur de generation ne touche PAS le chemin chaud",
         "il n'existe que dans la branche RAZ de l'ISR")
    # ⚠️ DEUX PROPRIETES DISTINCTES, DEUX CONTROLES. La version d'origine les
    #    melangeait dans un `or` : elle pouvait etre VERTE parce que la premiere
    #    tenait, en n'ayant jamais eprouve la seconde — le defaut « un test vert
    #    qui n'atteint pas la garde qu'il pretend couvrir ».
    n_horloge = corps_isr.count("esp_timer_get_time")
    ctrl(n_horloge == 1, "l'ISR ne lit l'horloge QU'UNE FOIS",
         "%d appel(s) dans on_vsync" % n_horloge)
    ctrl("esp_timer_get_time" not in hors_raz,
         "et JAMAIS dans la branche du regime normal",
         "l'unique lecture est en tete, avant le if/else")

    for d in _tmp:
        shutil.rmtree(d, ignore_errors=True)
    print("\n" + "=" * 78)
    print("BILAN : %d OK, %d KO" % (ok_total[0], ko_total[0]))
    print("=" * 78)
    return 1 if ko_total[0] else 0


if __name__ == "__main__":
    sys.exit(main())
