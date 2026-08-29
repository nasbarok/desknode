#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dn3-3 — LA VEILLE NE MENT NI SUR SON DÉLAI, NI SUR SES PANNES, NI SUR SES GRIS.
ÉPROUVÉ EN **EXÉCUTANT LE PRODUIT**, DEPUIS WSL, SANS CARTE ET SANS TOUR.

======================= CE QUE CET OUTIL FAIT, ET POURQUOI ==================

⛔ IL NE REJOUE RIEN. La règle du dépôt est écrite : *« une gate EXTRAIT ET
   APPELLE le code testé ; un harnais qui réimplémente ce qu'il teste est
   décoratif »*. Ici :

   · `dn_veille.c` est COMPILÉ EN ENTIER et APPELÉ. Il n'inclut que `nvs.h` et
     `esp_log.h` — deux coquilles minimales suffisent, et c'est précisément
     pour ça que ce module ne touche NI LVGL, NI la dalle, NI le
     rétroéclairage. La coquille NVS est un vrai petit magasin clé/valeur en
     RAM : elle permet d'éprouver la persistance ET le repli sur défaut
     JOURNALISÉ d'AC7.4, ⛔ pas seulement le chemin nominal.

   · `dn_widget_desaturer()` est **EXTRAITE VERBATIM** de `dn_widget.c` (le
     fichier du dépôt, non modifié), compilée et appelée. ⚠️ Si la fonction
     n'est plus trouvable sous ce nom, LA GATE ÉCHOUE BRUYAMMENT — un renommage
     silencieux ne doit pas rendre la gate verte sur du vide.

🔴 LES TÉMOINS NÉGATIFS SONT DES MUTATIONS **COMPILÉES ET EXÉCUTÉES**. On casse
   la garde, on recompile, on rappelle, et on EXIGE de voir le défaut d'origine
   revenir. Une garde dont on n'a pas vu l'absence faire échouer quelque chose
   ne prouve rien — et « un test peut être VERT sans ATTEINDRE la garde qu'il
   prétend couvrir » est un défaut que ce dépôt a déjà payé.

⚠️ ET LES CONTRÔLES DE TABLE SONT `grep`ÉS SUR **TOUT LE FICHIER**, ⛔ pas sur
   la seule fonction visée : « une gate scopée à UNE fonction peut épingler VERT
   le même défaut ailleurs ».

Sortie : exit 0 si tout passe, 1 sinon. Publie le sha256 des sources LUES.
"""

import ctypes
import hashlib
import importlib.util
import os
import re
import subprocess
import sys
import tempfile

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(RACINE, "firmware", "desknode", "main")
DN_VEILLE_C = os.path.join(MAIN, "dn_veille.c")
DN_VEILLE_H = os.path.join(MAIN, "dn_veille.h")
DN_WIDGET_C = os.path.join(MAIN, "dn_widget.c")
DN_UI_C = os.path.join(MAIN, "dn_ui.c")
DN_UI_H = os.path.join(MAIN, "dn_ui.h")
DN_TOUCH_C = os.path.join(MAIN, "dn_touch.c")
DN_CONSOLE_C = os.path.join(MAIN, "dn_console.c")
DN_ENV_H_P = os.path.join(MAIN, "dn_env.h")
PARTITIONS = os.path.join(RACINE, "firmware", "desknode", "partitions.csv")

ok_total = [0]
ko_total = [0]
_tmp = []


def lire(chemin):
    with open(chemin, "rb") as f:
        brut = f.read()
    return brut.decode("utf-8"), hashlib.sha256(brut).hexdigest()[:16]


def ctrl(ok, libelle, detail=""):
    if ok:
        ok_total[0] += 1
        print("  [OK ] %-58s %s" % (libelle, detail))
    else:
        ko_total[0] += 1
        print("  [KO ] %-58s %s" % (libelle, detail))
    return ok


# ── LES SITES D'APPEL, ⛔ PAS LES MENTIONS EN COMMENTAIRE ────────────────────
_RE_COMMENTAIRES_C = re.compile(r"/\*.*?\*/|//[^\n]*", re.S)


def sites_appel(src, jeton):
    """Compte les SITES D'APPEL de `jeton`, ⛔ pas ses mentions en commentaire.

    🔴 CORRIGÉ EN REVUE DE CODE LE 2026-08-28 — LE VERDICT TENAIT, L'ÉTIQUETTE
       MENTAIT. Le contrôle d'AC4.5 faisait un `src.count(...)` nu et publiait
       « 4 sites dans dn_ui.c » là où il y a **3 appels** et **1 mention dans
       un commentaire** (`dn_ui.c`, le bloc au-dessus de `nav_activite_console`).
       Le seuil étant 2, le verdict restait juste — mais ce dépôt traite une
       étiquette qui ment comme un défaut à part entière (`dn_widget.h`), et
       c'est ce même travers qu'il vient de corriger sur `w2 reset` (`156b507`).
    ⛔ Et le compte n'est PAS récité : il est RELU de la source à chaque appel.
    """
    return _RE_COMMENTAIRES_C.sub("", src).count(jeton)


def tmpdir():
    d = tempfile.mkdtemp(prefix="dn33_")
    _tmp.append(d)
    return d


# ═══════════════════════════════════════════════════════════════════════════
#  LES COQUILLES — le strict minimum, et rien de plus
# ═══════════════════════════════════════════════════════════════════════════

SHIM_ESP_ERR = r"""
#pragma once
#include <stdint.h>
typedef int esp_err_t;
#define ESP_OK 0
#define ESP_FAIL -1
#define ESP_ERR_INVALID_ARG 0x102
#define ESP_ERR_NOT_FOUND   0x105
const char *esp_err_to_name(esp_err_t e);
"""

SHIM_ESP_LOG = r"""
#pragma once
#include <stdio.h>
/* On COMPTE les journalisations par niveau : AC7.4 exige qu'un repli sur défaut
 * soit JOURNALISÉ, et « il retombe sur le défaut » ne se prouve pas en lisant
 * seulement la valeur — un repli SILENCIEUX rendrait la même valeur. */
extern int g_logw, g_loge, g_logi;
#define ESP_LOGW(tag, ...) do { g_logw++; } while (0)
#define ESP_LOGE(tag, ...) do { g_loge++; } while (0)
#define ESP_LOGI(tag, ...) do { g_logi++; } while (0)
"""

# Un vrai petit magasin clé/valeur : sans lui, la persistance et le repli sur
# valeur ABERRANTE ne seraient pas éprouvables.
SHIM_NVS = r"""
#pragma once
#include <string.h>
#include "esp_err.h"
#define ESP_ERR_NVS_NOT_FOUND 0x1102
typedef int nvs_handle_t;
typedef enum { NVS_READONLY = 0, NVS_READWRITE = 1 } nvs_open_mode_t;
esp_err_t nvs_open(const char *ns, nvs_open_mode_t m, nvs_handle_t *out);
esp_err_t nvs_get_i32(nvs_handle_t h, const char *k, int32_t *out);
esp_err_t nvs_set_i32(nvs_handle_t h, const char *k, int32_t v);
esp_err_t nvs_commit(nvs_handle_t h);
void nvs_close(nvs_handle_t h);
/* Pilotage depuis le test — ⛔ pas utilisé par le produit. */
void t_nvs_reset(void);
void t_nvs_poser(const char *k, int32_t v);
int  t_nvs_lire(const char *k, int32_t *out);
void t_nvs_absent(int on);
"""

SHIM_ESP_TIMER = r"""
#pragma once
#include <stdint.h>
/* `dn_veille.c` chronomètre ses écritures NVS (le coût est payé dans la tâche
 * LVGL au tap MENU, donc il se publie). Sur l'hôte, une horloge monotone
 * SUFFIT : ⛔ cette gate ne prétend RIEN mesurer du coût réel, qui dépend de la
 * flash et du cache — c'est la carte qui le dira. */
int64_t esp_timer_get_time(void);
"""

SHIM_C = r"""
#include <stdint.h>
#include <string.h>
#include <stdio.h>
#include "esp_err.h"
#include "nvs.h"
int g_logw, g_loge, g_logi;
const char *esp_err_to_name(esp_err_t e) { (void)e; return "SHIM"; }
static int64_t s_t;
int64_t esp_timer_get_time(void) { return (s_t += 1000); }

#define NMAX 16
static char s_k[NMAX][20];
static int32_t s_v[NMAX];
static int s_n;
static int s_absent;   /* 1 = le namespace n'existe pas (clone neuf) */

void t_nvs_reset(void) { s_n = 0; s_absent = 0; }
void t_nvs_absent(int on) { s_absent = on; }
void t_nvs_poser(const char *k, int32_t v) {
    for (int i = 0; i < s_n; i++) if (!strcmp(s_k[i], k)) { s_v[i] = v; return; }
    snprintf(s_k[s_n], sizeof(s_k[0]), "%s", k); s_v[s_n] = v; s_n++;
}
int t_nvs_lire(const char *k, int32_t *out) {
    for (int i = 0; i < s_n; i++) if (!strcmp(s_k[i], k)) { *out = s_v[i]; return 1; }
    return 0;
}
esp_err_t nvs_open(const char *ns, nvs_open_mode_t m, nvs_handle_t *out) {
    (void)ns; (void)m;
    if (s_absent) return ESP_ERR_NOT_FOUND;
    *out = 1; return ESP_OK;
}
esp_err_t nvs_get_i32(nvs_handle_t h, const char *k, int32_t *out) {
    (void)h;
    return t_nvs_lire(k, out) ? ESP_OK : ESP_ERR_NVS_NOT_FOUND;
}
esp_err_t nvs_set_i32(nvs_handle_t h, const char *k, int32_t v) {
    (void)h; t_nvs_poser(k, v); return ESP_OK;
}
esp_err_t nvs_commit(nvs_handle_t h) { (void)h; return ESP_OK; }
void nvs_close(nvs_handle_t h) { (void)h; }
"""


def construire_veille(src_veille, etiquette):
    """Compile `dn_veille.c` (ou une MUTATION) en .so et rend le handle ctypes."""
    d = tmpdir()
    txt_h, _ = lire(DN_VEILLE_H)
    with open(os.path.join(d, "dn_veille.h"), "w", encoding="utf-8") as f:
        f.write(txt_h)
    for nom, contenu in (("esp_err.h", SHIM_ESP_ERR), ("esp_log.h", SHIM_ESP_LOG),
                         ("esp_timer.h", SHIM_ESP_TIMER), ("nvs.h", SHIM_NVS),
                         ("shim.c", SHIM_C)):
        with open(os.path.join(d, nom), "w", encoding="utf-8") as f:
            f.write(contenu)
    with open(os.path.join(d, "dn_veille.c"), "w", encoding="utf-8") as f:
        f.write(src_veille)
    so = os.path.join(d, "libv.so")
    r = subprocess.run(
        ["cc", "-shared", "-fPIC", "-O0", "-I", d, "-o", so,
         os.path.join(d, "dn_veille.c"), os.path.join(d, "shim.c")],
        capture_output=True, text=True)
    if r.returncode != 0:
        print("ÉCHEC DE COMPILATION (%s) :\n%s" % (etiquette, r.stderr[:3000]))
        return None
    return ctypes.CDLL(so)


def api_veille(lib):
    # ⚠️ UN ECHEC DE COMPILATION DOIT **ROUGIR**, ⛔ PAS EXPLOSER EN TRACEBACK :
    #    une gate qui plante ne dit pas « KO », elle dit « je n'ai pas tourne ».
    #    Les deux se lisent tres differemment dans un dossier de mesure.
    if lib is None:
        ctrl(False, "compilation du module", "⛔ la gate n'a RIEN pu eprouver")
        return None
    lib.dn_veille_doit_dormir.restype = ctypes.c_bool
    lib.dn_veille_doit_dormir.argtypes = [ctypes.c_bool, ctypes.c_int,
                                          ctypes.c_uint32, ctypes.c_uint32]
    lib.dn_veille_tick.restype = ctypes.c_int
    lib.dn_veille_tick.argtypes = [ctypes.c_uint32]
    lib.dn_veille_armee.restype = ctypes.c_bool
    lib.dn_veille_cran.restype = ctypes.c_int
    lib.dn_veille_cran_min.restype = ctypes.c_int
    lib.dn_veille_cran_min.argtypes = [ctypes.c_int]
    lib.dn_veille_cran_index.restype = ctypes.c_int
    lib.dn_veille_cran_index.argtypes = [ctypes.c_int]
    lib.dn_veille_delai_ms.restype = ctypes.c_uint32
    lib.dn_veille_mode.restype = ctypes.c_int
    lib.dn_veille_reveiller.restype = ctypes.c_bool
    lib.dn_veille_reveiller.argtypes = [ctypes.c_int]
    lib.dn_veille_soupcon_appui_fantome.restype = ctypes.c_bool
    lib.dn_veille_set_cran.restype = ctypes.c_int
    lib.dn_veille_set_cran.argtypes = [ctypes.c_int]
    lib.dn_veille_set_armee.restype = ctypes.c_int
    lib.dn_veille_set_armee.argtypes = [ctypes.c_bool]
    lib.dn_veille_set_pct.restype = ctypes.c_int
    lib.dn_veille_set_pct.argtypes = [ctypes.c_int]
    return lib


ACTIF, AMBIENT = 0, 1
RIEN, DORMIR = 0, 1


def logw(lib):
    return ctypes.c_int.in_dll(lib, "g_logw").value


# ═══════════════════════════════════════════════════════════════════════════
#  1. LA GARDE DE BASCULE — bornes exactes, puis MUTANT
# ═══════════════════════════════════════════════════════════════════════════

def bloc_garde(src):
    print("\n── 1. LA GARDE DE BASCULE (AC3.1, AC3.3, AC3.4) ────────────────────")
    lib = api_veille(construire_veille(src, "nominal"))
    if lib is None:
        return
    D = 60000  # cran 1 min

    ctrl(not lib.dn_veille_doit_dormir(True, ACTIF, D - 1, D),
         "delai - 1 ms  ⇒  on NE dort PAS")
    ctrl(lib.dn_veille_doit_dormir(True, ACTIF, D, D),
         "delai EXACT   ⇒  on dort",
         "c'est `>=`, et c'est ce qui donne la fenetre [60 ; 61] s")
    ctrl(lib.dn_veille_doit_dormir(True, ACTIF, D + 1, D),
         "delai + 1 ms  ⇒  on dort")
    ctrl(not lib.dn_veille_doit_dormir(False, ACTIF, D * 10, D),
         "veille DESARMEE ⇒ la bascule n'arrive JAMAIS (AC3.4)")
    ctrl(not lib.dn_veille_doit_dormir(True, AMBIENT, D * 10, D),
         "deja en Ambient ⇒ pas de seconde bascule")
    ctrl(not lib.dn_veille_doit_dormir(True, ACTIF, D * 10, 0),
         "delai NUL ⇒ REFUS, ⛔ pas une bascule au premier tick")

    # ── LE MUTANT : `>=` devient `>` ───────────────────────────────────────
    mut = src.replace("return inactivite_ms >= delai_ms;",
                      "return inactivite_ms > delai_ms;")
    if mut == src:
        ctrl(False, "MUTANT `>=` -> `>` : site introuvable",
             "la garde a ete reecrite : cette gate ne la couvre plus")
        return
    libm = api_veille(construire_veille(mut, "mutant >"))
    if libm is None:
        return
    survit = libm.dn_veille_doit_dormir(True, ACTIF, D, D)
    ctrl(not survit,
         "MUTANT `>=` -> `>` : le test le VOIT (rougit sur delai exact)",
         "un mutant survivant = le test n'atteint pas la ligne")


# ═══════════════════════════════════════════════════════════════════════════
#  2. LES QUATRE CRANS ET LES DÉFAUTS D'USINE (D-5, D-8, AC3.2, AC7.5)
# ═══════════════════════════════════════════════════════════════════════════

def bloc_crans(src):
    print("\n── 2. LES QUATRE CRANS ET LES DEFAUTS D'USINE (D-5, D-8) ───────────")
    lib = api_veille(construire_veille(src, "nominal"))
    if lib is None:
        return
    lib.t_nvs_reset()
    lib.t_nvs_absent(1)
    lib.dn_veille_init()

    attendus = [1, 3, 5, 10]
    lus = [lib.dn_veille_cran_min(i) for i in range(4)]
    ctrl(lus == attendus, "les QUATRE crans sont 1/3/5/10 min", str(lus))
    ctrl(lib.dn_veille_cran_min(-1) == -1 and lib.dn_veille_cran_min(4) == -1,
         "hors bornes ⇒ -1, ⛔ pas un cran voisin")
    ctrl(lib.dn_veille_cran_index(7) == -1,
         "7 min ⇒ REFUS (-1), ⛔ pas d'ecretage vers 5",
         "le depot refuse et explique, il n'ecrete pas")
    ctrl(lib.dn_veille_cran_index(10) == 3, "10 min ⇒ index 3")

    ctrl(lib.dn_veille_armee() is True,
         "DEFAUT D'USINE : veille = ON (D-8)",
         "sinon le critere n°1 du brief serait faux a la sortie de boite")
    ctrl(lib.dn_veille_cran() == 1 and lib.dn_veille_delai_ms() == 180000,
         "DEFAUT D'USINE : delai = 3 min = 180 000 ms (D-8)",
         "ni le piege du 1 min, ni celui du 10 min")
    ctrl(logw(lib) >= 1,
         "namespace absent ⇒ le repli sur defaut est JOURNALISE (AC7.4)",
         "un defaut silencieux fausserait une mesure sans qu'on le sache")


# ═══════════════════════════════════════════════════════════════════════════
#  3. LA PERSISTANCE ET LE REPLI SUR VALEUR ABERRANTE (AC7.1, AC7.3, AC7.4)
# ═══════════════════════════════════════════════════════════════════════════

def bloc_nvs(src):
    print("\n── 3. PERSISTANCE ET REPLI SUR ABERRANT (AC7) ──────────────────────")
    lib = api_veille(construire_veille(src, "nominal"))
    if lib is None:
        return

    # (a) aller-retour : régler, « rebooter », relire
    lib.t_nvs_reset()
    lib.dn_veille_init()
    lib.dn_veille_set_cran(2)          # 5 min
    lib.dn_veille_set_armee(True)
    v = ctypes.c_int32(0)
    a = lib.t_nvs_lire(b"veille_dly", ctypes.byref(v))
    ctrl(a == 1 and v.value == 2, "le cran est ECRIT en NVS", "veille_dly = %d" % v.value)
    b_ = lib.t_nvs_lire(b"veille_on", ctypes.byref(v))
    ctrl(b_ == 1 and v.value == 1, "l'armement est ECRIT en NVS")

    # « reboot » : un binaire NEUF relit le magasin qu'on vient de remplir
    lib2 = api_veille(construire_veille(src, "apres reboot"))
    lib2.t_nvs_reset()
    lib2.t_nvs_poser(b"veille_dly", 2)
    lib2.t_nvs_poser(b"veille_on", 1)
    lib2.dn_veille_init()
    ctrl(lib2.dn_veille_cran() == 2 and lib2.dn_veille_armee() is True,
         "APRES REBOOT : 5 min / ON relus tels quels (AC7.3)")

    # (b) valeurs ABERRANTES : repli sur le défaut ET journalisation
    lib3 = api_veille(construire_veille(src, "aberrant"))
    lib3.t_nvs_reset()
    lib3.t_nvs_poser(b"veille_dly", 99)
    lib3.t_nvs_poser(b"veille_on", 42)
    lib3.dn_veille_init()
    ctrl(lib3.dn_veille_cran() == 1,
         "cran ABERRANT (99) ⇒ repli sur le defaut (3 min)")
    ctrl(lib3.dn_veille_armee() is True,
         "armement ABERRANT (42) ⇒ repli sur le defaut (ON)",
         "⛔ surtout pas un `!= 0` qui ferait passer 42 pour un ON delibere")
    ctrl(logw(lib3) >= 2,
         "les DEUX replis sont JOURNALISES (AC7.4)",
         "%d avertissements" % logw(lib3))

    # ── MUTANT : le `!= 0` silencieux, celui qu'on a refusé d'écrire ───────
    mut = src.replace("if (v == 0 || v == 1) {", "if (1) {")
    if mut == src:
        ctrl(False, "MUTANT `v==0||v==1` : site introuvable")
        return
    libm = api_veille(construire_veille(mut, "mutant !=0"))
    if libm is None:
        return
    libm.t_nvs_reset()
    libm.t_nvs_poser(b"veille_on", 42)
    libm.t_nvs_poser(b"veille_dly", 1)
    libm.dn_veille_init()
    # Avec la mutation, 42 est accepté et journalisé NULLE PART.
    ctrl(logw(libm) < 2,
         "MUTANT : sans la garde, 42 passe SANS avertissement — le test le voit",
         "%d avertissements au lieu de >= 2" % logw(libm))


# ═══════════════════════════════════════════════════════════════════════════
#  4. LE TICK, LA BASCULE ET SON ANNULATION (AC3.6, AC8.1)
# ═══════════════════════════════════════════════════════════════════════════

def bloc_tick(src):
    print("\n── 4. LE TICK, LA BASCULE ET SON ANNULATION ────────────────────────")
    lib = api_veille(construire_veille(src, "nominal"))
    if lib is None:
        return
    lib.t_nvs_reset()
    lib.t_nvs_poser(b"veille_dly", 0)   # 1 min
    lib.t_nvs_poser(b"veille_on", 1)
    lib.dn_veille_init()

    # 59 ticks sous le délai : rien.
    actions = [lib.dn_veille_tick(i * 1000) for i in range(60)]
    ctrl(all(a == RIEN for a in actions),
         "59 s d'inactivite ⇒ AUCUNE bascule")
    ctrl(lib.dn_veille_mode() == ACTIF, "on est toujours en ACTIF")

    a = lib.dn_veille_tick(60000)
    ctrl(a == DORMIR, "a 60 000 ms ⇒ DORMIR")
    ctrl(lib.dn_veille_mode() == AMBIENT, "l'etat a bascule en AMBIENT")
    a = lib.dn_veille_tick(61000)
    ctrl(a == RIEN, "le tick suivant ne re-bascule PAS")

    # Le réveil.
    ctrl(lib.dn_veille_reveiller(1) is True, "reveil ⇒ true (l'etat a change)")
    ctrl(lib.dn_veille_reveiller(1) is False,
         "second reveil ⇒ FALSE, ⛔ pas un reveil de plus",
         "l'appelant ne doit pas annoncer un reveil qui n'a pas eu lieu")

    # L'annulation (async refusée par LVGL).
    lib.dn_veille_tick(120000)
    ctrl(lib.dn_veille_mode() == AMBIENT, "re-bascule apres reveil")
    lib.dn_veille_annuler_bascule()
    ctrl(lib.dn_veille_mode() == ACTIF,
         "annulation ⇒ retour a ACTIF",
         "⛔ pas d'etiquette AMBIENT sur un ecran reste en couleurs")

    class C(ctypes.Structure):
        _fields_ = [("mode", ctypes.c_int), ("armee", ctypes.c_bool),
                    ("cran", ctypes.c_int), ("delai_ms", ctypes.c_uint32),
                    ("inactivite_ms", ctypes.c_uint32),
                    ("inactivite_max_ms", ctypes.c_uint32),
                    ("bascules", ctypes.c_uint32), ("reveils", ctypes.c_uint32),
                    ("rebases", ctypes.c_uint32),
                    ("annulations", ctypes.c_uint32),
                    ("secondes_vues", ctypes.c_uint32),
                    ("origine", ctypes.c_int)]
    c = C()
    lib.dn_veille_compteurs(ctypes.byref(c))
    ctrl(c.annulations == 1, "l'annulation est COMPTEE", "annulations = %d" % c.annulations)
    ctrl(c.bascules == 1,
         "la bascule annulee est RETRANCHEE du compteur",
         "bascules = %d (2 tentees, 1 annulee)" % c.bascules)
    ctrl(c.inactivite_max_ms == 120000,
         "l'inactivite MAXIMALE est retenue", "%d ms" % c.inactivite_max_ms)

    # 🔴 AC3.3 — L'ECART EST **LATCHE**, ⛔ PAS RELU DE `s_inactivite_ms` (que le
    #    tick ECRASE a la seconde suivante, veille ou pas). C'est ce latch qui
    #    rend la fenetre [delai ; delai+1 s] tranchable — un sondage depuis
    #    l'hote y ajouterait sa propre seconde.
    lib.dn_veille_bascule_ecart_ms.restype = ctypes.c_uint32
    lib.dn_veille_bascule_ecart_ms.argtypes = [ctypes.c_int]
    lib.dn_veille_bascule_ecarts_n.restype = ctypes.c_uint32
    ctrl(lib.dn_veille_bascule_ecarts_n() == 1,
         "AC3.3 : UN echantillon d'ecart apres la bascule annulee",
         "la 2e a ete ANNULEE, donc son echantillon est RETIRE")
    ctrl(lib.dn_veille_bascule_ecart_ms(0) == 60000,
         "…et il vaut 60 000 ms, la valeur du tick QUI A BASCULE",
         "⛔ pas la valeur courante, que les ticks suivants ecrasent")
    ctrl(lib.dn_veille_bascule_ecart_ms(3) == 0 and
         lib.dn_veille_bascule_ecart_ms(-1) == 0,
         "hors bornes ⇒ 0, et l'appelant DOIT le lire « pas mesure »")

    # 🔴 LE TEMOIN : chaque tick ECRASE `inactivite_ms`, JAMAIS le latch.
    #    C'est exactement pourquoi le latch existe, et on le PROUVE plutot que
    #    de l'affirmer.
    # ⚠️ 30 000 ms et ⛔ PAS une grande valeur : au-dessus du delai le tick
    #    RE-BASCULERAIT et pousserait un NOUVEL echantillon — le temoin
    #    mesurerait alors sa propre bascule. (Premiere version de ce controle :
    #    999 000 ms, et il a rougi pour cette raison exacte.)
    lib.dn_veille_tick(30000)
    lib.dn_veille_compteurs(ctypes.byref(c))
    ctrl(c.inactivite_ms == 30000 and lib.dn_veille_bascule_ecart_ms(0) == 60000,
         "TEMOIN : `inactivite_ms` a bouge, l'ecart LATCHE n'a PAS bouge",
         "30 000 vs 60 000 — sans le latch, AC3.3 publierait la valeur courante")

    # `veille reset` ne touche NI les réglages NI le mode.
    lib.dn_veille_tick(120000)
    lib.dn_veille_reset()
    lib.dn_veille_compteurs(ctypes.byref(c))
    ctrl(c.bascules == 0 and c.secondes_vues == 0, "`reset` vide les compteurs")
    ctrl(c.armee is True and c.cran == 0,
         "`reset` ⛔ NE TOUCHE PAS les deux reglages")
    ctrl(c.mode == AMBIENT,
         "`reset` ⛔ NE TOUCHE PAS le mode",
         "le remettre a ACTIF ferait diverger l'etat annonce de l'ecran")


# ════════════════════════════════════════════════════════════════════════════
#  4 bis. L'ANNEAU PORTE SON CONTEXTE — DEFAUT MESURE SUR LA CARTE LE 2026-08-25
#
#  La console jugeait chaque ecart latche contre le delai EN VIGUEUR A LA
#  LECTURE. Un ecart de 60 400 ms, latche a 1 min, s'affichait « HORS de
#  [delai ; delai+1 s] » des que le cran passait a 10 min. ⇒ Une etiquette qui
#  ment, sur l'instrument qui SOLDE AC3.3.
#  Et un second cas, mesure lui aussi : armer / baisser le cran / `veille reset`
#  alors que l'inactivite DEPASSE DEJA le delai fait basculer au premier tick,
#  qui latche l'inactivite VRAIE — 178 270 ms pour un cran de 1 min. La bascule
#  est CORRECTE ; la fenetre ne s'y applique pas.
# ════════════════════════════════════════════════════════════════════════════

def _anneau_neuf(s, etiq, cran=0, on=1):
    l = api_veille(construire_veille(s, etiq))
    if l is None:
        return None
    l.t_nvs_reset()
    l.t_nvs_poser(b"veille_dly", cran)
    l.t_nvs_poser(b"veille_on", on)
    l.dn_veille_init()
    l.dn_veille_bascule_ecart_ms.restype = ctypes.c_uint32
    l.dn_veille_bascule_ecart_ms.argtypes = [ctypes.c_int]
    l.dn_veille_bascule_delai_ms.restype = ctypes.c_uint32
    l.dn_veille_bascule_delai_ms.argtypes = [ctypes.c_int]
    l.dn_veille_bascule_jugeable.restype = ctypes.c_bool
    l.dn_veille_bascule_jugeable.argtypes = [ctypes.c_int]
    l.dn_veille_bascule_ecarts_n.restype = ctypes.c_uint32
    l.dn_veille_persist_n.restype = ctypes.c_uint32
    return l


def bloc_anneau_contexte(src):
    print("\n── 4 bis. L'ANNEAU PORTE SON CONTEXTE (defaut mesure) ─────────────")

    # ── A. LE DELAI EST LATCHE **AVEC** L'ECHANTILLON ────────────────────────
    lib = _anneau_neuf(src, "A / delai latche")
    if lib is None:
        return
    lib.dn_veille_tick(1000)        # SOUS le seuil ⇒ la garde s'AMORCE
    lib.dn_veille_tick(60000)       # franchit ⇒ latch
    ctrl(lib.dn_veille_bascule_ecarts_n() == 1, "A : un echantillon latche")
    ctrl(lib.dn_veille_bascule_delai_ms(0) == 60000,
         "A : le DELAI ARME est latche avec l'ecart",
         "sans lui, l'echantillon ne se juge contre rien")
    ctrl(lib.dn_veille_bascule_jugeable(0) is True,
         "A : un franchissement AMORCE est JUGEABLE")
    lib.dn_veille_set_cran(3)       # 10 min
    ctrl(lib.dn_veille_delai_ms() == 600000, "A : le cran COURANT a bien change")
    ctrl(lib.dn_veille_bascule_delai_ms(0) == 60000,
         "🔴 A : l'echantillon garde SON delai — ⛔ PAS le courant",
         "C'EST LE DEFAUT : 60 400 ms latches a 1 min etaient affiches HORS "
         "apres passage a 10 min")

    # ── B. LE PREMIER TICK APRES ARMEMENT N'EST PAS JUGEABLE ────────────────
    lib = _anneau_neuf(src, "B / arme tard", on=0)
    if lib is None:
        return
    lib.dn_veille_tick(300000)      # inactivite deja 5x le delai, mais DESARMEE
    lib.dn_veille_set_armee(True)
    lib.dn_veille_tick(301000)      # 1er tick arme ⇒ bascule IMMEDIATE
    ctrl(lib.dn_veille_bascule_ecarts_n() == 1, "B : la bascule a bien eu lieu")
    ctrl(lib.dn_veille_bascule_ecart_ms(0) == 301000,
         "B : l'ecart latche est l'inactivite VRAIE",
         "⛔ pas le delai : la bascule est correcte, elle n'est pas 'a l'heure'")
    ctrl(lib.dn_veille_bascule_jugeable(0) is False,
         "🔴 B : …et il est NON JUGEABLE",
         "178 270 ms releves en seance pour un cran de 1 min — un 🔴 sur ce "
         "cas accuserait un comportement CORRECT")

    # ── C. CHANGER DE CRAN DESAMORCE ────────────────────────────────────────
    lib = _anneau_neuf(src, "C / cran baisse")
    if lib is None:
        return
    lib.dn_veille_tick(1000)        # amorce sur le cran 1 min
    lib.dn_veille_set_cran(3)       # 10 min ⇒ DESAMORCE
    lib.dn_veille_tick(600000)      # franchit le NOUVEAU seuil, sans re-amorcage
    ctrl(lib.dn_veille_bascule_jugeable(0) is False,
         "C : changer de cran DESAMORCE la garde")

    # ── D. …ET UN TICK SOUS LE NOUVEAU SEUIL LA RE-AMORCE ───────────────────
    lib = _anneau_neuf(src, "D / re-amorcage")
    if lib is None:
        return
    lib.dn_veille_tick(1000)
    lib.dn_veille_set_cran(3)
    lib.dn_veille_tick(500000)      # SOUS 600 000 ⇒ RE-AMORCE
    lib.dn_veille_tick(600000)
    ctrl(lib.dn_veille_bascule_jugeable(0) is True,
         "D : un tick SOUS le nouveau seuil RE-AMORCE la garde",
         "⛔ le desamorcage n'est pas definitif, sinon plus rien ne serait jugeable")

    # ── E. AC8.3 : `veille reset` remet AUSSI le compteur NVS a zero ────────
    lib = _anneau_neuf(src, "E / reset AC8.3")
    if lib is None:
        return
    lib.dn_veille_set_cran(2)       # 5 min — une ECRITURE NVS
    ctrl(lib.dn_veille_persist_n() >= 1, "E : une ecriture NVS est COMPTEE")
    lib.dn_veille_reset()
    ctrl(lib.dn_veille_persist_n() == 0,
         "🔴 E : AC8.3 — `veille reset` remet AUSSI ce compteur a zero",
         "il y echappait : la sortie melangeait compteurs remis a zero et "
         "compteur CUMULATIF, ce que le depot a deja paye sur `*cris` (dn4-13)")
    lib.dn_veille_tick(600000)      # 600 000 > 300 000 ⇒ bascule immediate
    ctrl(lib.dn_veille_bascule_jugeable(0) is False,
         "E : …et `veille reset` DESAMORCE la garde",
         "l'inactivite, elle, n'est PAS remise a zero : c'est LVGL qui la tient")

    # ── F. UNE ANNULATION N'EST PAS UN RE-ARMEMENT ──────────────────────────
    lib = _anneau_neuf(src, "F / annulation")
    if lib is None:
        return
    lib.dn_veille_tick(1000)
    lib.dn_veille_tick(60000)
    ctrl(lib.dn_veille_bascule_jugeable(0) is True, "F : la bascule est jugeable")
    lib.dn_veille_annuler_bascule()
    ctrl(lib.dn_veille_bascule_ecarts_n() == 0,
         "F : l'annulation RETIRE l'echantillon — et son contexte avec")
    lib.dn_veille_tick(61000)       # re-bascule
    ctrl(lib.dn_veille_bascule_jugeable(0) is True,
         "F : la garde REPREND son amorcage apres une annulation",
         "⛔ une annulation n'est pas un re-armement : sans ca, la tentative "
         "suivante serait marquee non jugeable a tort")

    # ── G. LES DEUX MUTANTS, COMPILES ET VUS ROUGIR ─────────────────────────
    # ⚠️ Un test peut etre VERT sans ATTEINDRE la ligne qu'il pretend couvrir.
    #    On MUTE le produit et on exige que le verdict BASCULE.
    mut1 = src.replace("s_inact_bascule_jugeable[i] = s_garde_amorcee;",
                       "s_inact_bascule_jugeable[i] = true;")
    ctrl(mut1 != src, "G : la mutation 1 (jugeable toujours vrai) s'applique",
         "⛔ une mutation qui ne s'applique pas ne prouve RIEN")
    libm = _anneau_neuf(mut1, "mutant jugeable=true", on=0)
    if libm is not None:
        libm.dn_veille_tick(300000)
        libm.dn_veille_set_armee(True)
        libm.dn_veille_tick(301000)
        ctrl(libm.dn_veille_bascule_jugeable(0) is True,
             "G : MUTANT 1 — le controle B ROUGIT",
             "un mutant survivant voudrait dire que B n'atteint pas la ligne")

    mut2 = src.replace("s_inact_bascule_delai_ms[i] = delai;",
                       "s_inact_bascule_delai_ms[i] = 0;")
    ctrl(mut2 != src, "G : la mutation 2 (delai non latche) s'applique")
    libm2 = _anneau_neuf(mut2, "mutant delai=0")
    if libm2 is not None:
        libm2.dn_veille_tick(1000)
        libm2.dn_veille_tick(60000)
        ctrl(libm2.dn_veille_bascule_delai_ms(0) != 60000,
             "G : MUTANT 2 — le controle A ROUGIT",
             "le latch du delai est bien la ligne que A eprouve")


# ════════════════════════════════════════════════════════════════════════════
#  4 ter. LA 6e PISTE W2 SUR LA CASE `CPU` (dn3-3 / AC2.1)
#
#  AC2.1 N'AVAIT AUCUN INSTRUMENT : `dn_w2_echantillon()` avait cinq appelants,
#  TOUS des capteurs locaux. Cette piste-ci porte une case NOURRIE PAR LE PC.
#  ⛔ ET W2 N'AVAIT JAMAIS ETE GATE DU TOUT — aucun `verif_*.py` ne le touchait.
#  Le bloc EXTRAIT VERBATIM l'accumulateur de `dn_env.c` et l'APPELLE.
# ════════════════════════════════════════════════════════════════════════════

DN_ENV_C = os.path.join(MAIN, "dn_env.c")
DN_ENV_H = os.path.join(MAIN, "dn_env.h")
DN_CONSOLE_C = os.path.join(MAIN, "dn_console.c")

RE_W2_BLOC = re.compile(
    r"static dn_w2_t s_w2\[DN_W2_NB\];.*?\nvoid dn_w2_reset\(void\)\n\{.*?\n\}\n",
    re.S)
RE_W2_ENUM = re.compile(r"typedef enum \{\s*\n\s*DN_W2_LUX.*?\} dn_w2_id_t;", re.S)
RE_W2_STRUCT = re.compile(r"typedef struct \{\s*\n\s*uint32_t n;.*?\} dn_w2_t;", re.S)

SHIM_W2 = """
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
typedef int portMUX_TYPE;
#define portMUX_INITIALIZER_UNLOCKED 0
#define portENTER_CRITICAL(m) ((void)(m))
#define portEXIT_CRITICAL(m)  ((void)(m))
static portMUX_TYPE s_mux = portMUX_INITIALIZER_UNLOCKED;
"""


def _w2_construire(bloc_c, enum_c, struct_c, per_ms, cpu_ms, etiquette):
    """Compile L'ACCUMULATEUR EXTRAIT (ou une MUTATION) et rend le handle."""
    d = tmpdir()
    txt = (SHIM_W2
           + "#define DN_ENV_PERIODE_MS %d\n" % per_ms
           + "#define DN_W2_CADENCE_CPU_MS %d\n" % cpu_ms
           + enum_c + "\n" + struct_c + "\n" + bloc_c + "\n")
    with open(os.path.join(d, "w2.c"), "w", encoding="utf-8") as f:
        f.write(txt)
    so = os.path.join(d, "libw2.so")
    r = subprocess.run(["cc", "-shared", "-fPIC", "-O0", "-o", so,
                        os.path.join(d, "w2.c")], capture_output=True, text=True)
    if r.returncode != 0:
        print("ÉCHEC DE COMPILATION (%s) :\n%s" % (etiquette, r.stderr[:1500]))
        return None
    lib = ctypes.CDLL(so)
    lib.dn_w2_echantillon.argtypes = [ctypes.c_int, ctypes.c_int32]
    lib.dn_w2_desamorcer.argtypes = [ctypes.c_int]
    lib.dn_w2_cadence_ms.restype = ctypes.c_uint32
    lib.dn_w2_cadence_ms.argtypes = [ctypes.c_int]
    lib.dn_w2_nom.restype = ctypes.c_char_p
    lib.dn_w2_nom.argtypes = [ctypes.c_int]
    return lib


class W2(ctypes.Structure):
    _fields_ = [("n", ctypes.c_uint32),
                ("mn", ctypes.c_int32), ("mx", ctypes.c_int32),
                ("changements", ctypes.c_uint32),
                ("ruptures", ctypes.c_uint32),
                ("somme", ctypes.c_int64),
                ("somme_carres", ctypes.c_int64)]


def _w2_lire(lib, i):
    w = W2()
    lib.dn_w2_lire(ctypes.c_int(i), ctypes.byref(w))
    return w


def bloc_w2_cpu():
    print("\n── 4 ter. LA 6e PISTE W2 SUR `CPU` (AC2.1) ─────────────────────")
    ec, sha_c = lire(DN_ENV_C)
    eh, sha_h = lire(DN_ENV_H)
    mb = RE_W2_BLOC.search(ec)
    me = RE_W2_ENUM.search(eh)
    ms = RE_W2_STRUCT.search(eh)
    if not ctrl(mb is not None and me is not None and ms is not None,
                "l'accumulateur W2 est EXTRAIT de dn_env.c/.h",
                "dn_env.c sha %s · dn_env.h sha %s" % (sha_c, sha_h)):
        print("        ⛔ Extraction impossible : cette gate ne couvre PLUS rien.")
        print("           ⛔ Ne pas la neutraliser — la reparer.")
        return

    mper = re.search(r"#define DN_ENV_PERIODE_MS\s+(\d+)", eh)
    mcpu = re.search(r"#define DN_W2_CADENCE_CPU_MS\s+(\d+)", eh)
    if not ctrl(mper is not None and mcpu is not None,
                "les DEUX cadences sont RELUES de l'en-tete",
                "⛔ jamais recopiees dans la gate"):
        return
    per_ms, cpu_ms = int(mper.group(1)), int(mcpu.group(1))
    ctrl(cpu_ms == 1000,
         "la cadence CPU vaut 1 000 ms, ⛔ pas %d" % per_ms,
         "a 5 s, 60 s ne font que 12 echantillons ⇒ 11 transitions, et le PAS "
         "du denominateur (9,1 %) DEPASSE le seuil de taux (10 %)")

    bloc, enum_c, struct_c = mb.group(0), me.group(0), ms.group(0)
    lib = _w2_construire(bloc, enum_c, struct_c, per_ms, cpu_ms, "nominal")
    if not ctrl(lib is not None, "il compile tel quel sur l'hote"):
        return

    NB = enum_c.count(",") and None
    ctrl("DN_W2_CPU_DIX" in enum_c, "la piste `DN_W2_CPU_DIX` EXISTE")
    idx_cpu = 5

    # ── A. LE TEXTE, PAS LA SOURCE ──────────────────────────────────────────
    lib.dn_w2_reset()
    for v in (421, 421, 421):
        lib.dn_w2_echantillon(idx_cpu, v)
    w = _w2_lire(lib, idx_cpu)
    ctrl(w.n == 3 and w.changements == 0,
         "A : trois valeurs IDENTIQUES ⇒ 0 changement",
         "n=%d chg=%d — deux valeurs egales rendent le MEME texte" % (w.n, w.changements))

    lib.dn_w2_reset()
    for v in (421, 422, 422, 430):
        lib.dn_w2_echantillon(idx_cpu, v)
    w = _w2_lire(lib, idx_cpu)
    ctrl(w.n == 4 and w.changements == 2 and w.mn == 421 and w.mx == 430,
         "A : les changements de TEXTE sont comptes, et min/max suivent",
         "n=%d chg=%d min=%d max=%d" % (w.n, w.changements, w.mn, w.mx))

    # ── B. LA RUPTURE DE CHAINE ─────────────────────────────────────────────
    lib.dn_w2_reset()
    lib.dn_w2_echantillon(idx_cpu, 400)
    lib.dn_w2_desamorcer(idx_cpu)      # sortie d'Ambient
    lib.dn_w2_echantillon(idx_cpu, 900)  # reprise : valeur TRES differente
    w = _w2_lire(lib, idx_cpu)
    ctrl(w.changements == 0,
         "🔴 B : l'echantillon qui SUIT une rupture n'est PAS un changement",
         "400 → [rupture] → 900 : rien ne relie ces deux instants (chg=%d)" % w.changements)
    ctrl(w.ruptures == 1, "B : la rupture est COMPTEE", "ruptures=%d" % w.ruptures)
    ctrl(w.n == 2, "B : ⛔ aucun echantillon n'est JETE", "n=%d" % w.n)

    # ── C. L'IDEMPOTENCE — LE PIEGE QUI RENDRAIT LE DENOMINATEUR NEGATIF ────
    lib.dn_w2_reset()
    lib.dn_w2_echantillon(idx_cpu, 400)
    for _ in range(50):
        lib.dn_w2_desamorcer(idx_cpu)   # 50 ticks hors Ambient
    lib.dn_w2_echantillon(idx_cpu, 500)
    w = _w2_lire(lib, idx_cpu)
    ctrl(w.ruptures == 1,
         "🔴 C : 50 desamorcages d'affilee ne comptent QU'UNE rupture",
         "ruptures=%d — sans l'idempotence, une nuit en Actif en compterait "
         "des dizaines de milliers et n-1-ruptures partirait SOUS ZERO" % w.ruptures)

    lib.dn_w2_reset()
    lib.dn_w2_desamorcer(idx_cpu)       # rupture AVANT tout echantillon
    w = _w2_lire(lib, idx_cpu)
    ctrl(w.ruptures == 0,
         "C : rompre une chaine INEXISTANTE ne compte rien", "ruptures=%d" % w.ruptures)

    # ── D. `reset` REMET TOUT, RUPTURES COMPRISES ──────────────────────────
    lib.dn_w2_reset()
    lib.dn_w2_echantillon(idx_cpu, 1)
    lib.dn_w2_desamorcer(idx_cpu)
    lib.dn_w2_reset()
    w = _w2_lire(lib, idx_cpu)
    ctrl(w.n == 0 and w.changements == 0 and w.ruptures == 0,
         "D : `w2 reset` remet n, changements ET ruptures a zero")

    # ── E. LE NOM NE MENT PAS SUR SA CADENCE ────────────────────────────────
    #    Les deux sont LUS DU PRODUIT et confrontes : c'est une gate d'ETIQUETTE.
    ok = True
    detail = []
    for i in range(6):
        nom = lib.dn_w2_nom(i).decode("utf-8", "replace")
        cad = lib.dn_w2_cadence_ms(i)
        attendu = "@%ds" % (cad // 1000)
        if attendu not in nom:
            ok = False
        detail.append("%s=%dms" % (attendu, cad))
    ctrl(ok, "🔴 E : le NOM de chaque piste porte SA cadence, et elles CONCORDENT",
         " · ".join(detail) + " — un tableau qui aligne des taux de cadences "
         "differentes sans le dire est une etiquette qui ment")

    # ── F. LE SITE D'ECHANTILLONNAGE EST UNIQUE, ET GARDE PAR AMBIENT ──────
    ui, _ = lire(DN_UI_C)
    n_sites = ui.count("dn_w2_echantillon(DN_W2_CPU_DIX")
    ctrl(n_sites == 1,
         "F : UN SEUL site echantillonne la piste CPU",
         "%d site(s) — deux sites doubleraient la cadence en silence" % n_sites)
    ctrl(re.search(r"dn_veille_mode\(\) == DN_VEILLE_AMBIENT[^;]*?\n?[^;]*?"
                   r"dn_w2_echantillon\(DN_W2_CPU_DIX", ui, re.S) is not None,
         "F : il est GARDE par `dn_veille_mode() == DN_VEILLE_AMBIENT`",
         "AC2.1 dit « en Ambient » — et sous agent reel il n'y a plus de "
         "console pour delimiter la fenetre")
    ctrl("dn_w2_desamorcer(DN_W2_CPU_DIX)" in ui,
         "F : …et la chaine est BRISEE hors Ambient / sur valeur invalide")

    # ── G. LE DENOMINATEUR RETIRE LES RUPTURES, DANS LA CONSOLE ────────────
    cons, _ = lire(DN_CONSOLE_C)
    # 🔴 REECRIT EN REVUE DE CODE LE 2026-08-28 — CES DEUX CONTROLES EPINGLAIENT
    #    `n - 1 - ruptures`, QUI RETRANCHAIT UNE RUPTURE DE TROP DANS LE CAS
    #    NORMAL. `ruptures` est TERMINALE (`dn_w2_desamorcer`), donc le nombre
    #    d'EPISODES vaut `ruptures + 1` seulement tant que le dernier est OUVERT.
    #    Lu HORS Ambient — le cas normal, puisque sortir d'Ambient desamorce —
    #    tous les episodes sont clos et le denominateur juste est `n - ruptures`.
    ctrl("uint32_t episodes = w.ruptures + (w.amorce ? 1u : 0u);" in cons,
         "G : le denominateur compte les EPISODES, ⛔ pas les ruptures + 1",
         "`ruptures` est TERMINALE : +1 seulement si la chaine est OUVERTE")
    ctrl("(w.n > episodes) ? (w.n - episodes) : 0u" in cons,
         "G : …et le taux vaut chg / (n - episodes)")
    ctrl("out->amorce = s_w2_amorce[id];" in ec,
         "G : `amorce` est LU DANS LA MEME SECTION CRITIQUE que les compteurs",
         "lu apres coup, il decrirait un autre instant que le `n` qu'il corrige")
    ctrl("if (taux > 100u) {" in cons,
         "G : un taux > 100 % est DIT, ⛔ pas publie",
         "`changements` est un sous-ensemble des transitions : c'est impossible")
    # ⚠️ MUTANT TEXTUEL : on remet l'ancienne formule et on EXIGE que les deux
    #    controles ci-dessus rougissent. Sans lui, on aurait remplace un
    #    critere par un autre sans jamais voir le nouveau echouer.
    _mut_den = cons.replace(
        "uint32_t episodes = w.ruptures + (w.amorce ? 1u : 0u);",
        "uint32_t episodes = 1u + w.ruptures;")
    ctrl(("uint32_t episodes = w.ruptures + (w.amorce ? 1u : 0u);"
          not in _mut_den) and ("uint32_t episodes = 1u + w.ruptures;"
                                in _mut_den),
         "G : MUTANT « 1u + w.ruptures » — le critere le voit",
         "vu rougir : l'ancienne formule ne satisfait plus le controle")

    # ── H. LES DEUX MUTANTS, COMPILES ET VUS ROUGIR ────────────────────────
    m1 = bloc.replace("if (s_w2_amorce[id] && v != s_w2_prec[id]) {",
                      "if (v != s_w2_prec[id]) {")
    ctrl(m1 != bloc, "H : la mutation 1 (garde d'amorcage retiree) s'applique")
    lm = _w2_construire(m1, enum_c, struct_c, per_ms, cpu_ms, "mutant sans amorce")
    if lm is not None:
        lm.dn_w2_reset()
        lm.dn_w2_echantillon(idx_cpu, 400)
        lm.dn_w2_desamorcer(idx_cpu)
        lm.dn_w2_echantillon(idx_cpu, 900)
        wm = _w2_lire(lm, idx_cpu)
        ctrl(wm.changements == 1,
             "H : MUTANT 1 — le controle B ROUGIT",
             "la rupture serait comptee comme un changement (chg=%d)" % wm.changements)

    m2 = bloc.replace("    if (s_w2_amorce[id]) {\n        s_w2_amorce[id] = false;\n"
                      "        s_w2[id].ruptures++;\n    }",
                      "    s_w2_amorce[id] = false;\n    s_w2[id].ruptures++;")
    ctrl(m2 != bloc, "H : la mutation 2 (idempotence retiree) s'applique")
    lm2 = _w2_construire(m2, enum_c, struct_c, per_ms, cpu_ms, "mutant non idempotent")
    if lm2 is not None:
        lm2.dn_w2_reset()
        lm2.dn_w2_echantillon(idx_cpu, 400)
        for _ in range(50):
            lm2.dn_w2_desamorcer(idx_cpu)
        wm2 = _w2_lire(lm2, idx_cpu)
        ctrl(wm2.ruptures == 50,
             "H : MUTANT 2 — le controle C ROUGIT",
             "50 ruptures pour UNE sortie d'Ambient (ruptures=%d)" % wm2.ruptures)


# ═══════════════════════════════════════════════════════════════════════════
#  5. LE SOUPÇON D'APPUI FANTÔME (AC8.2) — et son MUTANT
# ═══════════════════════════════════════════════════════════════════════════

def bloc_fantome(src):
    print("\n── 5. LE SOUPCON D'APPUI FANTOME (AC8.2) ───────────────────────────")

    def neuf(s, etiq):
        l = api_veille(construire_veille(s, etiq))
        l.t_nvs_reset()
        l.t_nvs_poser(b"veille_dly", 0)  # 1 min
        l.t_nvs_poser(b"veille_on", 1)
        l.dn_veille_init()
        return l

    lib = neuf(src, "nominal")
    # Le GT911 est collé : l'inactivité reste à ~0, quoi qu'il arrive.
    for _ in range(30):
        lib.dn_veille_tick(0)
    ctrl(not lib.dn_veille_soupcon_appui_fantome(),
         "a 30 s d'observation (< delai) ⇒ PAS d'alerte",
         "⛔ crier au loup au boot serait pire que pas de garde")
    for _ in range(40):
        lib.dn_veille_tick(0)
    ctrl(lib.dn_veille_soupcon_appui_fantome(),
         "a 70 s (> delai + %d s) et inactivite collee a 0 ⇒ ALERTE" % 5,
         "c'est la panne que le scan I2C NE VOIT PAS")

    # Contre-épreuve : régime NORMAL, l'alerte ne sort pas.
    lib2 = neuf(src, "regime normal")
    for i in range(70):
        lib2.dn_veille_tick(i * 1000)
    ctrl(not lib2.dn_veille_soupcon_appui_fantome(),
         "regime NORMAL (une bascule a eu lieu) ⇒ pas d'alerte")

    # ── MUTANT : on retire la condition d'observation ──────────────────────
    # 🔴 MARQUEUR MIS A JOUR EN REVUE DE CODE LE 2026-08-28. L'ancien visait
    #    `s_secondes_vues * 1000u`, qui DEBORDAIT un uint32 a ~49,7 jours — sur
    #    un module dont le critere n°1 est « une semaine H24 ». La comparaison se
    #    fait desormais EN SECONDES, et la fenetre part du DERNIER REVEIL.
    marqueur = ("    uint32_t seuil_s = (delai / 1000u) + "
                "(uint32_t)DN_VEILLE_MARGE_SOUPCON_S;\n"
                "    return s_secondes_depuis_reveil > seuil_s;")
    if marqueur not in src:
        ctrl(False, "MUTANT condition d'observation : site introuvable")
        return
    mut = src.replace(marqueur, "    return true;")
    libm = neuf(mut, "mutant sans observation")
    libm.dn_veille_tick(0)
    ctrl(libm.dn_veille_soupcon_appui_fantome(),
         "MUTANT : sans la condition, l'alerte sort des le 1er tick",
         "le test le voit ⇒ la garde est bien ATTEINTE")

    # ── 🔴 LA FENETRE PART DU DERNIER REVEIL, ET UN `veille now` NE L'ETEINT
    #    PLUS (revue du 2026-08-28). AVANT, `s_bascules > 0` desarmait le
    #    detecteur DEFINITIVEMENT — or `s_consommer` (`dn_touch.c`) ne se pose
    #    QU'EN AMBIENT, donc APRES au moins une bascule : le detecteur
    #    s'eteignait exactement quand il devenait utile.
    lib3 = neuf(src, "apres un veille now")
    ctrl(lib3.dn_veille_forcer_dormir(),
         "une bascule FORCEE est acceptee (veille armee, on est ACTIF)")
    ctrl(lib3.dn_veille_reveiller(0), "…puis on reveille")
    for _ in range(70):
        lib3.dn_veille_tick(0)
    ctrl(lib3.dn_veille_soupcon_appui_fantome(),
         "APRES un `veille now` + reveil, l'alerte SORT quand meme",
         "⛔ AVANT, UN SEUL `veille now` eteignait le detecteur pour de bon")

    # ⚠️ TEMOIN NEGATIF DU MEME MECANISME : une bascule AUTOMATIQUE, elle, DOIT
    #    eteindre l'alerte — sinon on aurait remplace un aveuglement par un
    #    detecteur qui crie sur un module parfaitement sain.
    lib4 = neuf(src, "bascule automatique")
    for i in range(70):
        lib4.dn_veille_tick(i * 1000)
    ctrl(not lib4.dn_veille_soupcon_appui_fantome(),
         "…mais une bascule AUTOMATIQUE l'eteint bien",
         "⛔ sinon le detecteur crierait sur un module sain")

    # ⚠️ ET LA FENETRE SE REARME AU REVEIL : c'est ce qui rend le detecteur
    #    utile APRES la premiere veille, la ou la panne se produit reellement.
    ctrl(lib4.dn_veille_reveiller(0), "on reveille apres la bascule auto")
    for _ in range(70):
        lib4.dn_veille_tick(0)
    ctrl(lib4.dn_veille_soupcon_appui_fantome(),
         "REVEIL puis doigt colle ⇒ l'alerte SORT (fenetre re-armee)",
         "🎯 c'est LE cas que l'ancienne garde ne pouvait PAS voir")


# ═══════════════════════════════════════════════════════════════════════════
#  6. LA DÉSATURATION DES ACCENTS — EXTRAITE DU `.c` ET APPELÉE (AC9.4)
# ═══════════════════════════════════════════════════════════════════════════

RE_DESAT = re.compile(
    r"uint32_t dn_widget_desaturer\(uint32_t rgb, int pct\)\s*\{.*?\n\}",
    re.S)


def bloc_accents():
    print("\n── 6. LA DESATURATION DES ACCENTS (AC9.4) ──────────────────────────")
    src, sha = lire(DN_WIDGET_C)
    m = RE_DESAT.search(src)
    if not ctrl(m is not None,
                "`dn_widget_desaturer()` EXTRAITE de dn_widget.c",
                "sha %s" % sha):
        print("        ⛔ La fonction a ete renommee ou fusionnee : cette gate")
        print("           ne couvre plus rien. ⛔ Ne pas la neutraliser.")
        return
    d = tmpdir()
    with open(os.path.join(d, "d.c"), "w", encoding="utf-8") as f:
        f.write("#include <stdint.h>\n" + m.group(0) + "\n")
    so = os.path.join(d, "libd.so")
    r = subprocess.run(["cc", "-shared", "-fPIC", "-O0", "-o", so,
                        os.path.join(d, "d.c")], capture_output=True, text=True)
    if not ctrl(r.returncode == 0, "elle compile telle quelle sur l'hote",
                r.stderr[:200]):
        return
    lib = ctypes.CDLL(so)
    lib.dn_widget_desaturer.restype = ctypes.c_uint32
    lib.dn_widget_desaturer.argtypes = [ctypes.c_uint32, ctypes.c_int]

    # ══════════════════════════════════════════════════════════════════════
    # 🔴 dn4-14 / AC6.1-6.2 — CETTE GATE MESURAIT AUTRE CHOSE QUE CE QU'ELLE
    #    DISAIT, ET ELLE ETAIT VERTE. Elle faisait un `re.findall` sur TOUT
    #    `dn_ui.c` et rendait SEPT valeurs, en ecrivant que la 7e etait
    #    « cyan pour l'humidite » de la bicolore D6. MESURE le 2026-08-29 :
    #    les six premieres sont bien les cases (l.575, 703, 796, 828, 965,
    #    1116) mais la 7e est `k_demo_desc.couleur` (0x35d6e8, l.10139) — LA
    #    METRIQUE FICTIVE DE DEMO. ⇒ elle mesurait une couleur que PERSONNE
    #    NE VOIT, et ne couvrait PAS l'humidite, qui vaut `0x67e8f9`
    #    (`DET_COURBE_COUL_HUM`). Les deux valeurs coincidaient par accident
    #    d'arithmetique : c'est ce qui a laisse la gate verte.
    #    ⛔ CE N'EST PAS UN DETAIL DE PERIMETRE : le defaut « une gate VERTE
    #      sur du code faux » applique A LA GATE ELLE-MEME.
    # ⇒ LE JEU DEVIENT CE QUI EST REELLEMENT PEINT : les 6 cases + l'humidite.
    #   Le descripteur de DEMO est EXCLU en scopant le regex au bloc `k_desc[]`
    #   (⛔ pas en retirant « la derniere » : ca se re-casserait a la prochaine
    #   `.couleur` ajoutee n'importe ou dans le fichier).
    # ══════════════════════════════════════════════════════════════════════
    ui, _ = lire(DN_UI_C)
    mk = re.search(r"static const dn_widget_desc_t k_desc\[DN_UI_METRIQUES\] = \{"
                   r".*?\n\};", ui, re.S)
    if not ctrl(mk is not None,
                "le bloc `k_desc[]` est LOCALISE dans dn_ui.c",
                "⛔ sans lui le regex ramasserait aussi `k_demo_desc`"):
        return
    cases = [int(x, 16) for x in
             re.findall(r"\.couleur = 0x([0-9a-fA-F]{6})", mk.group(0))]
    ctrl(len(cases) == 6,
         "les SIX couleurs de CASE sont relues du bloc `k_desc[]`",
         " ".join("%06x" % a for a in cases))

    # ⚠️ TEMOIN NEGATIF : le descripteur de DEMO doit etre HORS du jeu. Sans ce
    #    controle, une future `.couleur` glissee dans `k_desc[]` par erreur
    #    passerait, et surtout on ne saurait pas que l'exclusion opere.
    mdemo = re.search(r"k_demo_desc = \{.*?\n\};", ui, re.S)
    demo = (int(re.search(r"\.couleur = 0x([0-9a-fA-F]{6})",
                          mdemo.group(0)).group(1), 16) if mdemo else None)
    ctrl(demo is not None and demo not in cases,
         "TEMOIN : la couleur de la metrique FICTIVE (`k_demo_desc`) est EXCLUE",
         "0x%06x — elle etait comptee comme 7e accent avant dn4-14"
         % (demo if demo is not None else 0))

    # La 7e, LA VRAIE : l'accent de l'humidite d'AMBIANCE (bicolore D6).
    mh = re.search(r"#define\s+DET_COURBE_COUL_HUM\s+0x([0-9a-fA-F]{6})", ui)
    if not ctrl(mh is not None,
                "l'accent de l'HUMIDITE est relu de `DET_COURBE_COUL_HUM`",
                "⛔ pas recopie ici"):
        return
    hum = int(mh.group(1), 16)
    accents = cases + [hum]
    ctrl(len(accents) == 7,
         "⇒ SEPT accents REELLEMENT PEINTS : 6 cases + l'humidite",
         "%s + hum %06x" % (" ".join("%06x" % a for a in cases), hum))

    # ── dn4-14 / AC6.5 — UNE COULEUR ET SON COMMENTAIRE NE PEUVENT PLUS
    #    DIVERGER. Precedent : AC10.1 epingle deja `.couleur = 0x3b82f6, /* VERT`
    #    (un BLEU annonce vert). `RAM` est le prochain candidat : dn4-14 peut
    #    changer sa valeur, et son commentaire dit « ROSE — dn4-4 ».
    #    ⛔ LE CRITERE N'EST PAS « le commentaire dit rose » — ca se perimerait
    #      au premier changement, c.-a-d. reproduirait le defaut. Le critere est
    #      « si le commentaire NOMME une teinte, la valeur DOIT etre de cette
    #      famille » : rose/magenta ⇒ R > B > G ; violet ⇒ B >= R > G.
    mram = re.search(r"\.couleur = 0x([0-9a-fA-F]{6}),\s*/\* ([A-ZÉÈÀ]+)", mk.group(0))
    # ⚠️ dn4-14 (seance) : « CLAIR » entre au dictionnaire parce que `DISQUE`
    #    est devenue un clair neutre. ⛔ Sans lui la boucle SAUTE l'entree
    #    (`if nom not in fam: continue`) et le controle serait VERT en ne
    #    verifiant RIEN — exactement la classe de defaut que cette gate traque.
    fam = {"CLAIR":  lambda r, g, b: min(r, g, b) > 200 and (max(r, g, b) - min(r, g, b)) < 40,
           "ROSE":   lambda r, g, b: r > b > g,
           "MAGENTA": lambda r, g, b: r > b > g,
           "VIOLET": lambda r, g, b: b >= r > g,
           "ORANGE": lambda r, g, b: r > g > b,
           "CYAN":   lambda r, g, b: b >= g > r,
           "BLEU":   lambda r, g, b: b > g >= r,
           "ROUGE":  lambda r, g, b: r > g and r > b,
           "VERT":   lambda r, g, b: g > r and g > b}
    for m2 in re.finditer(r"\.couleur = 0x([0-9a-fA-F]{6}),\s*/\*+\s*([A-Z\u00c0-\u00dc]{3,8})",
                          mk.group(0)):
        v = int(m2.group(1), 16)
        nom = m2.group(2)
        if nom not in fam:
            continue
        r, g, b = (v >> 16) & 0xFF, (v >> 8) & 0xFF, v & 0xFF
        ctrl(fam[nom](r, g, b),
             "AC6.5 : 0x%06x est annoncee « %s » et l'EST (R%d G%d B%d)"
             % (v, nom, r, g, b),
             "⛔ un commentaire qui survit a la valeur qu'il decrit est un "
             "defaut au meme titre qu'un chiffre faux")

    ctrl(all(lib.dn_widget_desaturer(a, 0) == a for a in accents),
         "pct = 0 ⇒ la teinte est INTACTE")

    gris = [lib.dn_widget_desaturer(a, 100) for a in accents]
    tous_gris = all((g >> 16) == ((g >> 8) & 0xFF) == (g & 0xFF) for g in gris)
    ctrl(tous_gris, "pct = 100 ⇒ R = G = B (gris PUR)",
         " ".join("%06x" % g for g in gris))

    # ══════════════════════════════════════════════════════════════════════
    # 🔴 LE FAIT MESURE QUI A FAIT CORRIGER LE PRODUIT (2026-08-25).
    #    Le commentaire d'origine de `dn_widget_desaturer()` affirmait qu'une
    #    MOYENNE des trois canaux confondrait le cyan de GPU et le rose de RAM,
    #    et que BT.601 les separait. C'ETAIT L'INVERSE : BT.601 les rend TOUS
    #    LES DEUX a 160/255, et c'est la moyenne qui les separe (161 / 180).
    #    ⇒ Le motif faux a ete corrige DANS LE SOURCE, et le defaut est passe
    #      de 100 a 95. Cette gate epingle desormais LA MESURE, ⛔ pas la
    #      croyance : « un motif faux dans un commentaire est un defaut au meme
    #      titre qu'un chiffre faux ».
    # ══════════════════════════════════════════════════════════════════════
    def _paires(vals, etiq):
        return [(etiq[i], etiq[j], vals[i])
                for i in range(len(vals)) for j in range(i + 1, len(vals))
                if vals[i] == vals[j]]

    etiq = ["CPU", "GPU", "RAM", "RESEAU", "DISQUE", "AMBIANCE", "AMB-humidite"]
    ys = [(g & 0xFF) for g in gris]
    coll_bt = _paires(ys, etiq)
    # ⚠️ RE-MESURE dn4-14 SUR LE JEU CORRIGE (2026-08-29) : la propriete TIENT
    #    — la substitution demo -> humidite ne change RIEN a 100 % en BT.601,
    #    la paire confondue reste `GPU`/`RAM` a 160. Luminances mesurees :
    #    [121, 127, 153, 160, 160, 172, 195].
    # ⛔ CE N'EST PAS UN BUT : c'est un CONSTAT epingle. Si un changement de
    #   palette le fait passer a ZERO paire, la gate ROUGIT SUR UNE
    #   AMELIORATION — et alors on RE-ECRIT le nombre AVEC SON MOTIF, on ne
    #   « l'ajuste » pas. Le nom de la paire est imprime pour que la relecture
    #   sache LAQUELLE, ⛔ pas seulement combien.
    ctrl(len(coll_bt) == 1,
         "a 100 %, EXACTEMENT UNE paire se confond (mesure, ⛔ pas un but)",
         "%s — luminances %s"
         % (", ".join("%s/%s a %d" % c for c in coll_bt) or "AUCUNE",
            sorted(ys)))

    def moy(c):
        return (((c >> 16) & 0xFF) + ((c >> 8) & 0xFF) + (c & 0xFF)) // 3
    mv = [moy(a) for a in accents]
    coll_moy = _paires(mv, etiq)
    # ══════════════════════════════════════════════════════════════════════
    # 🔴 dn4-14 / AC6.4 — CE TEMOIN A BASCULE, ET C'EST LA CORRECTION DU JEU
    #    QUI L'A FAIT BASCULER, ⛔ PAS UN CHANGEMENT DE PALETTE.
    #    Il affirmait « la moyenne en confond UNE AUSSI — simplement pas la
    #    meme », et il etait VERT. MESURE le 2026-08-29 : la paire qu'il
    #    comptait etait `CPU` / **la metrique FICTIVE de demo** (166) — ⛔ pas
    #    `CPU`/humidite. Sur le jeu REELLEMENT PEINT, la moyenne ne confond
    #    RIEN : 7 valeurs distinctes (145, 156, 158, 161, 166, 180, 194).
    #    ⇒ La phrase d'origine de `dn_widget_desaturer()` (« la moyenne
    #      confondrait, BT.601 separe ») est donc fausse ENCORE PLUS FORT
    #      qu'on ne le croyait, et DANS L'AUTRE SENS : sur les accents reels,
    #      c'est BT.601 qui confond (GPU/RAM) et la moyenne qui separe tout.
    #    ⛔ ET CE N'EST PAS UNE RAISON DE CHANGER LA FONCTION : le produit
    #      tourne au defaut 95 %, ou les SEPT restent distincts avec un ecart
    #      chromatique de 10/255. L'ecart BT.601/moyenne n'existe qu'a 100 %,
    #      un regime que le produit n'emploie pas. C'est un FAIT A ECRIRE,
    #      ⛔ pas un correctif a faire.
    # ══════════════════════════════════════════════════════════════════════
    ctrl(len(coll_moy) == 0,
         "TEMOIN : sur le jeu REEL, la moyenne ne confond RIEN (BT.601, si)",
         "moyennes %s — l'ancien « elle en confond une aussi » comptait "
         "la couleur de DEMO" % sorted(mv))

    # ── LE DEFAUT DU PRODUIT DOIT, LUI, TOUT SEPARER ──────────────────────
    m = re.search(r"static int s_accent_amb_pct = (\d+);", src)
    if ctrl(m is not None, "le defaut `s_accent_amb_pct` est relu du source"):
        defaut = int(m.group(1))
        gd = [lib.dn_widget_desaturer(a, defaut) for a in accents]
        ctrl(len(set(gd)) == 7,
             "AU DEFAUT (%d %%), les SEPT accents restent DISTINCTS" % defaut,
             "⇒ le piege n°6 (rendre deux choses indiscernables) est ferme")
        def dchroma(x, y):
            """Distance max-canal entre deux couleurs — l'ecart que l'oeil voit
            le plus vite sur un aplat uni."""
            return max(abs(((x >> 16) & 0xFF) - ((y >> 16) & 0xFF)),
                       abs(((x >> 8) & 0xFF) - ((y >> 8) & 0xFF)),
                       abs((x & 0xFF) - (y & 0xFF)))
        chroma = min(dchroma(gd[i], gd[j])
                     for i in range(len(gd)) for j in range(i + 1, len(gd)))
        ctrl(chroma >= 4,
             "…avec un ecart chromatique minimal de %d/255" % chroma,
             "invisible a l'oeil, mais l'information est GARDEE")


# ═══════════════════════════════════════════════════════════════════════════
#  7. LES TROIS GRIS D'AMBIENT — le piège nommé d'avance (AC9.3)
# ═══════════════════════════════════════════════════════════════════════════

def luminance(c):
    return (((c >> 16) & 0xFF) * 77 + ((c >> 8) & 0xFF) * 150 +
            (c & 0xFF) * 29) >> 8


def bloc_gris():
    print("\n── 7. LES TROIS GRIS D'AMBIENT (AC9.3, piege n°6) ──────────────────")
    src, sha = lire(DN_WIDGET_C)

    amb = {}
    for k, v in re.findall(
            r"\[(DN_VAL_[A-Z]+)\]\s*=\s*0x([0-9a-fA-F]{6})", src):
        amb[k] = int(v, 16)
    ctrl(len(amb) == 3, "les TROIS tons d'Ambient sont declares", str(sorted(amb)))
    if len(amb) != 3:
        return

    actif = {}
    for nom, cle in (("W_COL_REELLE", "DN_VAL_REELLE"),
                     ("W_COL_SIMULEE", "DN_VAL_SIMULEE"),
                     ("W_COL_ABSENTE", "DN_VAL_ABSENTE")):
        m = re.search(r"#define\s+%s\s+0x([0-9a-fA-F]{6})" % nom, src)
        if m:
            actif[cle] = int(m.group(1), 16)
    ctrl(len(actif) == 3, "les TROIS tons d'Actif sont relus", str(sorted(actif)))

    for etiq, table in (("Ambient", amb), ("Actif", actif)):
        vals = list(table.values())
        ctrl(len(set(vals)) == 3,
             "%s : les 3 regimes sont DISTINCTS" % etiq,
             " ".join("%06x" % v for v in vals))
        ls = sorted(luminance(v) for v in vals)
        ecart = min(ls[1] - ls[0], ls[2] - ls[1])
        ctrl(ecart >= 24,
             "%s : ecart de luminance minimal >= 24/255" % etiq,
             "min %d (luminances %s)" % (ecart, ls))

    # ══════════════════════════════════════════════════════════════════════
    # 🔴 LES GRIS D'AMBIENT DOIVENT ETRE **RGB565-NEUTRES** — CONSTAT OWNER 2026-08-25
    #
    #    « les 6 cases sont pleines en VERT sur fond noir », alors que
    #    l'instrument lisait `couleur 1E1E1E` sur l'objet et disait VRAI. En
    #    RGB565 le canal VERT porte 6 bits, le rouge et le bleu 5 : un gris
    #    R=G=B ne survit pas a la quantification. `0x1E1E1E` sort en R24 G28 B24
    #    — +4 de vert sur le canal que l'oeil pese a 59 %.
    # ⛔ Cette garde existe pour que ca ne puisse pas revenir EN SILENCE : rien
    #    dans un build, ni dans une relecture de source, ne l'aurait vu. Il a
    #    fallu la dalle, et un test au ROUGE PUR pour ecarter le rendu.
    # ══════════════════════════════════════════════════════════════════════
    def rgb565(v8):
        r5, g6 = v8 >> 3, v8 >> 2
        return ((r5 << 3) | (r5 >> 2), (g6 << 2) | (g6 >> 4))

    for cle, val in sorted(amb.items()):
        r8, g8, b8 = (val >> 16) & 0xFF, (val >> 8) & 0xFF, val & 0xFF
        if not (r8 == g8 == b8):
            continue  # pas un gris : la question ne se pose pas
        R, G = rgb565(r8)
        ctrl(-1 <= G - R <= 1,
             "Ambient %s (%06X) est RGB565-NEUTRE"
             % (cle.replace("DN_VAL_", ""), val),
             "rendu R%d G%d B%d, ecart vert %+d" % (R, G, R, G - R))

    m = re.search(r"#define W_AMB_CASE_BG 0x([0-9a-fA-F]{6})", src)
    if ctrl(m is not None, "`W_AMB_CASE_BG` est relu du source"):
        v = int(m.group(1), 16)
        R, G = rgb565((v >> 16) & 0xFF)
        # 🔴 POUR UN APLAT **PLEIN**, LE CRITERE EST **L'EGALITE STRICTE**, ⛔ PAS
        #    « |G-R| <= 1 » — ET C'EST L'OEIL QUI L'A IMPOSE.
        #    `202020` satisfait le critere a +/-1 et l'owner l'a quand meme vu
        #    « vert plus fonce » (2026-08-25). Sur cette dalle, `scene gray`
        #    montre que la rampe entiere tire — vert dans les sombres, violet
        #    dans les clairs. Les SEULES valeurs vraiment neutres sont les
        #    extremites : le noir et le blanc.
        # ⛔ Ne pas relacher ce critere : trois valeurs ont ete essayees SUR LA
        #    DALLE avant qu'il tienne.
        ctrl(G == R,
             "l'aplat de case (%06X) est EXACTEMENT neutre" % v,
             "rendu R%d G%d B%d — `1E` sortait a +4, `20` a -1 et tirait ENCORE"
             % (R, G, R))

    # ⚠️ LE TEMOIN : la valeur d'origine DOIT echouer au meme critere. Une garde
    #    qu'on n'a pas vue rejeter quelque chose ne prouve rien.
    R, G = rgb565(0x1E)
    ctrl(G - R > 1,
         "TEMOIN 1 : `1E1E1E` — 1re valeur essayee — ECHOUE",
         "rendu R%d G%d B%d, ecart vert %+d ⇒ vu VERT a l'oeil" % (R, G, R, G - R))
    R, G = rgb565(0x20)
    ctrl(G != R,
         "TEMOIN 2 : `202020` — 2e valeur essayee — ECHOUE AUSSI",
         "rendu R%d G%d B%d ⇒ vu « vert plus fonce » : le critere a +/-1 ne "
         "suffisait PAS" % (R, G, R))

    # 🔴 LE PIÈGE : le gris du VIVANT ne doit PAS être celui de l'ABSENCE.
    ctrl(amb["DN_VAL_REELLE"] != actif["DN_VAL_ABSENTE"],
         "le VIVANT en Ambient ≠ `W_COL_ABSENTE` (0x9a9a9a)",
         "sinon « vivant » redevient indiscernable de « mort » (2026-08-18)")
    ctrl(luminance(amb["DN_VAL_REELLE"]) > luminance(amb["DN_VAL_ABSENTE"]),
         "en Ambient, le VIVANT est plus CLAIR que l'ABSENT")

    # ⚠️ ANGLE MORT : la convention ne doit exister QU'A UN ENDROIT.
    #    On grep TOUT le fichier, ⛔ pas la seule fonction visee.
    # 🔴 ON DECOUPE LE FICHIER EN FONCTIONS ET ON REGARDE **LESQUELLES**
    #    TOUCHENT LA TABLE. ⛔ Pas un simple compte de sites : un seuil numerique
    #    aurait ete VERT le jour ou une seconde fonction en aurait pris trois de
    #    plus — « une gate scopee a UNE fonction peut epingler VERT le meme
    #    defaut ailleurs ».
    bornes = []
    for m in re.finditer(r"^[A-Za-z_][\w \*]*?([a-z_][a-z_0-9]*)\s*\([^;{]*\)\s*\{",
                         src, re.M):
        bornes.append((m.start(), m.group(1)))
    porteuses = set()
    # ⚠️ ⛔ PAS `s_gris_amb\[DN_VAL_` tout court : ca attraperait la TAILLE du
    #    tableau (`[DN_VAL_REGIME_COUNT]`) dans sa declaration, qui n'est pas
    #    un site de LECTURE. La gate s'accusait elle-meme.
    for m in re.finditer(r"s_gris_amb\[DN_VAL_(?:REELLE|SIMULEE|ABSENTE)\]", src):
        prec = [b for b in bornes if b[0] < m.start()]
        porteuses.add(prec[-1][1] if prec else "<hors fonction>")
    ctrl(porteuses == {"dn_val_regime_couleur"},
         "UNE SEULE fonction lit `s_gris_amb[DN_VAL_*]`",
         "porteuses : %s" % (", ".join(sorted(porteuses)) or "aucune"))

    for f, chemin in (("dn_ui.c", DN_UI_C),):
        txt, _ = lire(chemin)
        ctrl("W_COL_REELLE" not in txt and "s_gris_amb" not in txt,
             "%s ne redefinit AUCUNE couleur de regime" % f,
             "la convention vit dans dn_val_regime_couleur() et nulle part ailleurs")


# ═══════════════════════════════════════════════════════════════════════════
#  8. LE RECOMPTE DE LA PARTITION (AC1.1, AC1.4)
# ═══════════════════════════════════════════════════════════════════════════

DN_FONT_33 = os.path.join(MAIN, "fonts", "dn_font_33.c")
DN_FONT_56 = os.path.join(MAIN, "fonts", "dn_font_56.c")


def bloc_identite_ambient():
    """dn3-3 — L'IDENTITE VISUELLE D'AMBIENT (decision owner du 2026-08-25).

    Verbatim : « tout passe en nuance de noir blanc, titre et icones
    disparaissent, chiffres agrandis, blanc sur fond noir et sur fond gris
    fonce ». Chacun de ces cinq points est epingle ici, parce qu'aucun ne se
    voit dans un build vert.
    """
    print("\n── 10. L'IDENTITE VISUELLE D'AMBIENT (owner, 2026-08-25) ───────────")
    wc, _ = lire(DN_WIDGET_C)
    ui, _ = lire(DN_UI_C)

    # (1) le titre, l'icone et le badge sont MASQUABLES sans reconstruction
    ctrl("lv_obj_t *titre;" in lire(os.path.join(MAIN, "dn_widget.h"))[0],
         "le TITRE est retenu dans `dn_widget_t`",
         "sans pointeur, le masquer exigerait 307-322 ms de reconstruction")
    m = re.search(r"void dn_widget_veille_appliquer\(.*?\n\}", wc, re.S)
    if ctrl(m is not None, "`dn_widget_veille_appliquer()` existe"):
        corps = m.group(0)
        ctrl("w->titre" in corps and "w->icone" in corps and "w->badge" in corps,
             "elle masque titre + icone + badge",
             "les trois que l'owner a nommes")
        ctrl("LV_OBJ_FLAG_HIDDEN" in corps and "build_scene" not in corps,
             "…par un DRAPEAU, ⛔ pas par une reconstruction")
        ctrl("aplat(w->racine)" in corps,
             "le retour en ACTIF repasse par `aplat()`, ⛔ ne le recopie pas",
             "une copie divergerait au premier `widget opa`")

    # (2) composer() laisse tomber icone ET PREFIXE en Ambient
    m = re.search(r"static void composer\(.*?\n\}", wc, re.S)
    if ctrl(m is not None, "`composer()` est trouvable"):
        corps = m.group(0)
        i_amb = corps.find("if (s_ambient)")
        i_px = corps.find("dn_widget_prefixe")
        ctrl(i_amb >= 0 and i_px > i_amb,
             "la branche AMBIENT sort AVANT le prefixe",
             "🔴 c'est le prefixe qui plafonnait l'agrandissement a +2 %")
        ctrl('snprintf(out, n, "--")' in corps,
             "…et l'ABSENCE reste « -- », ⛔ jamais une case vide")

    # (3) le voile d'Ambient est le NOIR PLEIN, et sans un octet d'asset
    ctrl("static uint8_t s_voile_opa_amb = 255;" in ui,
         "le voile d'Ambient vaut 255 — le NOIR PLEIN demande par l'owner")
    r = subprocess.run(["git", "-C", RACINE, "diff", "--stat", "HEAD", "--",
                        "assets/"], capture_output=True, text=True)
    ctrl(r.returncode == 0 and r.stdout.strip() == "",
         "…et AUCUN octet n'a ete ajoute a `assets/` (AC1.1)",
         "le fond noir est obtenu par un levier EXISTANT, la voie (b) tient")

    # (4) LES POLICES DE VEILLE NE PORTENT AUCUN SYMBOLE — verifie DANS LE `.c`
    #     ⚠️ C'est le controle qui protege le budget : embarquer FontAwesome a
    #     56 px couterait 61 glyphes JAMAIS dessines, a quatre fois le prix du 28.
    spec = importlib.util.spec_from_file_location(
        "g", os.path.join(RACINE, "tools", "gen_font_dn.py"))
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    for chemin, taille in ((DN_FONT_33, 33), (DN_FONT_56, 56)):
        if not os.path.isfile(chemin):
            ctrl(False, "dn_font_%d.c existe" % taille)
            continue
        src, sha = lire(chemin)
        cps, _ = gen.codepoints_du_c(src, chemin)
        syms = [cp for cp in cps if cp >= 0xF000]
        ctrl(not syms, "dn_font_%d : AUCUN symbole FontAwesome" % taille,
             "sha %s · %d codepoints portes" % (sha, len(cps)))
        ctrl(0xB0 in cps, "dn_font_%d : le DEGRE (U+00B0) est present" % taille,
             "« 61,0 °C » le porte — son absence serait SILENCIEUSE")
        ctrl(all(c in cps for c in range(0x30, 0x3A)),
             "dn_font_%d : les dix chiffres sont presents" % taille)
        ctrl(0xE9 not in cps,
             "dn_font_%d : ⛔ PAS d'accent latin-1 (plage reduite tenue)" % taille,
             "164 codepoints jamais dessines tripleraient la facture")

    # (5) les tailles sont celles qui ont ete MESUREES
    gsrc, _ = lire(os.path.join(RACINE, "tools", "gen_font_dn.py"))
    ctrl("TAILLES_VEILLE = (33, 56)" in gsrc,
         "les deux tailles du generateur sont 33 et 56",
         "33 = plafond AVEC unite (168 px) · 56 = SANS (90 px), mesures carte")
    ctrl("&dn_font_33 : &dn_font_56" in wc.replace("\n", " ").replace("  ", " ")
         or ("dn_font_33" in wc and "dn_font_56" in wc),
         "`font_val()` commute entre les deux selon l'unite")

    # (6) LES TROIS GRIS RESTENT DISTINCTS **MALGRE** le monochrome
    #     🔴 C'est le piege du « tout blanc » : le badge « SIMULE » est MASQUE en
    #     Ambient, donc le gris est le SEUL signal qui reste.
    ctrl("w->badge" in wc and "LV_OBJ_FLAG_HIDDEN" in wc,
         "le badge « SIMULE » est masque en Ambient",
         "⇒ le gris devient le SEUL signal du regime")


def bloc_assets():
    print("\n── 8. LE RECOMPTE DE LA PARTITION `assets` (AC1) ───────────────────")
    txt, sha = lire(PARTITIONS)
    m = re.search(r"^assets,\s*data,\s*0x40,\s*(0x[0-9a-fA-F]+),\s*(0x[0-9a-fA-F]+)",
                  txt, re.M)
    if not ctrl(m is not None, "la ligne `assets` est RELUE de partitions.csv",
                "sha %s" % sha):
        return
    taille = int(m.group(2), 16)
    asset = 480 * 640 * 2 + 16
    ctrl(taille == 0x100000, "partition `assets` = 1 048 576 o", "%d o" % taille)
    ctrl(taille - asset == 434160, "libre = 434 160 o", "%d o" % (taille - asset))
    ctrl(2 * asset > taille,
         "DEUX declinaisons NE TIENNENT PAS",
         "%d o > %d o — depassement %d o" % (2 * asset, taille, 2 * asset - taille))
    ctrl(2 * asset == 1228832,
         "le chiffre EXACT de deux declinaisons est 1 228 832 o",
         "⚠️ la story ecrit 1 228 816 : elle compte UN pied pour deux assets")
    ctrl(3 * asset == 1843248,
         "TROIS declinaisons = 1 843 248 o (le chiffre de la story est JUSTE)")
    # ⛔ AC1.1 : le fichier ne doit PAS avoir bougé.
    r = subprocess.run(["git", "-C", RACINE, "diff", "--stat", "--",
                        "firmware/desknode/partitions.csv"],
                       capture_output=True, text=True)
    ctrl(r.returncode == 0 and r.stdout.strip() == "",
         "`partitions.csv` est INCHANGE (AC1.1)",
         r.stdout.strip() or "git diff --stat vide")


# ═══════════════════════════════════════════════════════════════════════════
#  9. LES INSTRUMENTS QUE CETTE STORY REND VRAIS (AC5.4, AC5.5, AC10)
# ═══════════════════════════════════════════════════════════════════════════

def bloc_verite():
    print("\n── 9. LES ETIQUETTES NE MENTENT PLUS (AC5.4, AC5.5, AC10) ──────────")
    ui, _ = lire(DN_UI_C)
    uih, _ = lire(DN_UI_H)
    tc, _ = lire(DN_TOUCH_C)

    ctrl('return "MENU (zone morte — W3)"' not in ui,
         "`dn_ui_zone_nom` ne rend plus « MENU (zone morte — W3) »")
    ctrl(re.search(r'if \(zone == DN_UI_ZONE_MENU\) \{[^}]*return "MENU";', ui, re.S)
         is not None,
         "elle rend « MENU »")

    ctrl("s_menu_taps++;" in ui,
         "`s_menu_taps` a un site d'INCREMENT ⇒ il n'est plus structurellement nul")
    ctrl("on_menu_clic" in ui and "on_menu_clic,\n" in ui.replace("  ", " ") or
         "on_menu_clic," in ui,
         "le bandeau MENU recoit un callback NON NUL")
    # ⚠️ ⛔ PAS « la phrase a disparu » : le NOUVEAU docblock la CITE, pour dire
    #    ce qu'il corrige. Le critere est donc l'affirmation ORIGINALE, celle
    #    qui portait le compteur au present.
    ctrl("aucun site\n *    n'incrémente ce compteur" not in uih,
         "l'affirmation « aucun site n'incremente ce compteur » est PARTIE")
    # ⚠️ LE CRITERE EST LA **PHRASE ENTIERE** DE L'ORIGINAL, ⛔ pas un fragment :
    #    le nouveau docblock CITE les fragments pour dire ce qu'il corrige, et un
    #    critere sur le fragment aurait rougi sur sa propre correction.
    ctrl("il ne peut plus monter, et `nav` le dit" not in uih,
         "…ainsi que la phrase entiere « il ne peut plus monter, et `nav` le dit »")
    ctrl("IL MONTE" in uih,
         "le docblock dit desormais que le compteur MONTE",
         "⛔ un contrat d'en-tete qui decrit l'inverse du produit est la forme "
         "la plus durable du defaut")

    # AC10.1 — le `/* VERT */` sur un bleu.
    ctrl(re.search(r"\.couleur = 0x3b82f6,\s*/\* VERT", ui) is None,
         "AC10.1 : plus de `/* VERT */` sur `0x3b82f6` (qui est un BLEU)")
    ctrl("BLEU VIF" in ui, "le commentaire dit desormais BLEU VIF")

    # AC4.5 — trigger_activity sur les chemins console.
    _n_app = sites_appel(ui, "lv_display_trigger_activity(NULL)")
    ctrl(_n_app >= 2,
         "`lv_display_trigger_activity` est appele sur les chemins SANS doigt",
         "%d SITES D'APPEL dans dn_ui.c (commentaires exclus)" % _n_app)
    # ⚠️ TEMOIN : le compte doit IGNORER une mention en commentaire. Sans lui, on
    #    republierait le defaut de l'etiquette qu'on vient de corriger.
    ctrl(sites_appel("/* lv_display_trigger_activity(NULL) */\n"
                     "  lv_display_trigger_activity(NULL);\n"
                     "  // lv_display_trigger_activity(NULL)\n",
                     "lv_display_trigger_activity(NULL)") == 1,
         "…et le compte IGNORE les mentions en commentaire",
         "mutant textuel : 3 occurrences, 1 seul SITE — vu rendre 1")
    ctrl(ui.count("lv_display_trigger_activity(NULL)") > _n_app,
         "…temoin de cablage : dn_ui.c porte bien au moins une MENTION en commentaire",
         "brut %d > sites %d — sinon ce controle ne prouverait rien"
         % (ui.count("lv_display_trigger_activity(NULL)"), _n_app))
    ctrl("lv_display_trigger_activity(NULL)" in tc,
         "…et pendant un contact CONSOMME (sinon on se rendort doigt pose)")

    # 🔴 DEFAUT TROUVE **SUR LA CARTE** LE 2026-08-25, ET EPINGLE ICI POUR QU'IL
    #    NE REVIENNE PAS EN SILENCE.
    #    `veille wake` imprimait « Actif. » et le module RETOMBAIT en Ambient au
    #    tick suivant : l'horloge d'inactivite de LVGL ne se remet a zero que sur
    #    un `PRESSED`, donc la garde retrouvait aussitot `inactivite >= delai`.
    #    La console ANNONCAIT un etat qui ne tenait pas une seconde.
    #    ⇒ Le rebase doit vivre DANS le chemin de reveil, ⛔ pas seulement dans
    #      `nav_activite_console()` : sinon il ne couvre que la navigation.
    m = re.search(r"static bool veille_reveil_nolock\(.*?\n\}", ui, re.S)
    if ctrl(m is not None, "`veille_reveil_nolock()` est trouvable"):
        corps = m.group(0)
        ctrl("lv_display_trigger_activity(NULL)" in corps,
             "UN REVEIL REPART D'UN DELAI NEUF — quelle que soit l'origine",
             "⛔ sinon `veille wake` se fait re-endormir au tick suivant")
        # ⚠️ ET **APRES** le changement d'etat : avant, il rebaserait l'horloge
        #    meme quand le reveil n'a pas eu lieu (course), donc repousserait une
        #    bascule legitime sans qu'aucun compteur ne le dise.
        i_rev = corps.find("dn_veille_reveiller(origine)")
        i_act = corps.find("lv_display_trigger_activity(NULL)")
        ctrl(i_rev >= 0 and i_act > i_rev,
             "…et le rebase vient APRES `dn_veille_reveiller()`",
             "avant, il repousserait une bascule legitime sur une course")

    # AC3.6 — la bascule passe par lv_async_call.
    ctrl("lv_async_call(veille_dormir_async" in ui,
         "AC3.6 : la bascule Actif->Ambient passe par `lv_async_call`",
         "⛔ jamais directement depuis le callback de timer")

    # D-7 — le tap de réveil est consommé, et le verrou tient jusqu'au relâchement.
    ctrl("s_consommer = true;" in tc and "s_consommer = false;" in tc,
         "D-7 : le contact de reveil est CONSOMME, et LATCHE jusqu'au relachement")
    ctrl(tc.count("if (s_consommer)") >= 2,
         "…y compris sur le chemin d'ERREUR I2C",
         "%d sites — le pire moment pour laisser fuir un tap" % tc.count("if (s_consommer)"))

    # AC5.2 — les DEUX modèles portent la 3e vue.
    ctrl("s_scr_menu = lv_obj_create(NULL);" in ui,
         "AC5.2 : le modele SCREENS porte une 3e racine")
    ctrl("build_menu(scr);" in ui,
         "AC5.2 : le modele REBUILD construit la vue MENU")
    ctrl("s_scr_dash && s_scr_detail && s_scr_menu" in ui,
         "…et la garde SCREENS exige les TROIS racines",
         "avec deux, `nav menu` aurait `lv_obj_clean` une racine PERMANENTE")

    # ── AC10.4 — L'ETIQUETTE DE `w2 reset` NE PEUT PLUS SE PERIMER ──────────
    # 🔴 TROUVE EN SEANCE LE 2026-08-27, AU `grep` DE L'ANGLE MORT, ⛔ PAS A
    #    L'OEIL ET PAS PAR LA GATE : `w2 reset` annoncait « LES CINQ PISTES »
    #    alors que dn3-3 en avait ajoute une SIXIEME (`DN_W2_CPU_DIX`).
    #    ⚠️ Le reset, lui, couvrait bien les six (`memset` sur des tableaux
    #    dimensionnes `DN_W2_NB`) ⇒ l'instrument etait JUSTE et SON ETIQUETTE
    #    MENTAIT — le defaut a part entiere que `dn_widget.h:165` nomme.
    # ⛔ LE CRITERE N'EST PAS « le message dit SIX » : ca se perimerait a la 7e
    #    piste, c'est-a-dire qu'il reproduirait le defaut qu'il pretend fermer.
    #    Le critere est « le compte est RELU de `DN_W2_NB` ».
    cc, sha_cc = lire(DN_CONSOLE_C)
    eh2, _ = lire(DN_ENV_H_P)

    def _etiquette_w2(src):
        """LA MEME predicate pour le produit ET pour le mutant.

        ⛔ Elle ne rejoue pas la logique du firmware : elle LIT la ligne que le
           firmware imprime. Rend None si la ligne a disparu (⇒ la gate ne
           couvre plus rien, et elle le DIT au lieu de passer verte).
        """
        m = re.search(r'printf\("accumulateurs W2 remis a zero[^;]*;', src, re.S)
        if m is None:
            return None
        ligne = m.group(0)
        return (re.search(r"LES\s+[A-Z\u00c0-\u00dc]{2,7}\s+PISTES", ligne) is None,
                "DN_W2_NB" in ligne)

    reel = _etiquette_w2(cc)
    if ctrl(reel is not None,
            "AC10.4 : le message de `w2 reset` est TROUVABLE",
            "dn_console.c sha %s" % sha_cc):
        ctrl(reel[0],
             "…il n'ecrit PLUS le compte en toutes lettres",
             "ecrire « SIX » ne ferait que DEPLACER la date de peremption")
        ctrl(reel[1],
             "…il RELIT le compte de `DN_W2_NB`",
             "⛔ un compte recite se perime a la piste suivante")

        # MUTANT TEXTUEL — la MEME predicate, sur le source d'AVANT le correctif.
        # ⚠️ Un mutant survivant voudrait dire que la garde n'atteint pas la
        #    ligne : ce depot a deja paye un test VERT qui n'atteignait pas sa
        #    garde. On le fait donc ROUGIR, et on le regarde.
        mut = re.sub(r'printf\("accumulateurs W2 remis a zero[^;]*;',
                     'printf("accumulateurs W2 remis a zero (LES CINQ PISTES).\\n");',
                     cc, count=1, flags=re.S)
        mm = _etiquette_w2(mut)
        ctrl(mm is not None and mm == (False, False),
             "mutant « LES CINQ PISTES » : les DEUX criteres rougissent",
             "vu rougir : %r" % (mm,))

    # ⚠️ ET LA GATE VERIFIE DE QUOI ELLE PARLE : `DN_W2_NB` doit bien CLORE une
    #    enumeration qui porte la 6e piste. Sans ca, « relu de l'enum » serait
    #    un mot, ⛔ pas une propriete.
    m_enum = re.search(r"DN_W2_CPU_DIX,\s*\n\s*DN_W2_NB,", eh2)
    ctrl(m_enum is not None,
         "…et `DN_W2_NB` clot bien l'enum qui porte `DN_W2_CPU_DIX`",
         "⛔ sinon le compte relu ne serait pas celui des pistes")


def main():
    print("=" * 78)
    print("dn3-3 — VERIFICATION DE LA VEILLE, EN EXECUTANT LE PRODUIT")
    print("=" * 78)
    if subprocess.run(["cc", "--version"], capture_output=True).returncode != 0:
        sys.exit("ÉCHEC : `cc` est introuvable — cette gate COMPILE le produit.")

    src, sha = lire(DN_VEILLE_C)
    print("source : dn_veille.c  sha256[:16] = %s  (%d lignes)"
          % (sha, src.count("\n") + 1))

    bloc_garde(src)
    bloc_crans(src)
    bloc_nvs(src)
    bloc_tick(src)
    bloc_anneau_contexte(src)
    bloc_w2_cpu()
    bloc_fantome(src)
    bloc_accents()
    bloc_gris()
    bloc_identite_ambient()
    bloc_assets()
    bloc_verite()

    print("\n" + "=" * 78)
    print("BILAN : %d OK · %d KO" % (ok_total[0], ko_total[0]))
    print("=" * 78)
    if ko_total[0]:
        print("\n⛔ CE QUE CETTE GATE NE PROUVE **PAS** :")
        print("   · rien de ce qui se voit A L'OEIL (le gris, le voile, le %);")
        print("   · aucune latence (t1/t2 se mesurent SUR LA CARTE, AC4);")
        print("   · l'appui fantome REEL (la garde est armee, pas PROVOQUEE).")
    sys.exit(1 if ko_total[0] else 0)


if __name__ == "__main__":
    main()
