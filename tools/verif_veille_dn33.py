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
    marqueur = ("    uint32_t observe_ms = s_secondes_vues * 1000u;\n"
                "    return observe_ms > delai + (uint32_t)DN_VEILLE_MARGE_SOUPCON_S * 1000u;")
    if marqueur not in src:
        ctrl(False, "MUTANT condition d'observation : site introuvable")
        return
    mut = src.replace(marqueur, "    return true;")
    libm = neuf(mut, "mutant sans observation")
    libm.dn_veille_tick(0)
    ctrl(libm.dn_veille_soupcon_appui_fantome(),
         "MUTANT : sans la condition, l'alerte sort des le 1er tick",
         "le test le voit ⇒ la garde est bien ATTEINTE")


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

    # Les SIX couleurs d'accent RELUES du descripteur, ⛔ pas recopiees ici.
    ui, _ = lire(DN_UI_C)
    accents = [int(x, 16) for x in
               re.findall(r"\.couleur = 0x([0-9a-fA-F]{6})", ui)]
    # ⚠️ SEPT et non six : `AMBIANCE` porte DEUX couleurs (la bicolore D6 —
    #    orange pour la temperature, cyan pour l'humidite).
    ctrl(len(accents) == 7,
         "les SEPT couleurs d'accent sont relues de dn_ui.c",
         " ".join("%06x" % a for a in accents))

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
    ys = sorted((g & 0xFF) for g in gris)
    ctrl(len(set(ys)) == 6,
         "a 100 %, EXACTEMENT UNE paire se confond (mesure, ⛔ pas un but)",
         "6 gris distincts sur 7 — luminances %s" % ys)

    def moy(c):
        return (((c >> 16) & 0xFF) + ((c >> 8) & 0xFF) + (c & 0xFF)) // 3
    ctrl(len(set(moy(a) for a in accents)) == 6,
         "TEMOIN : la moyenne en confond UNE AUSSI — simplement pas la meme",
         "⛔ « la moyenne confondrait, pas BT.601 » etait FAUX")

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
    ctrl(ui.count("lv_display_trigger_activity(NULL)") >= 2,
         "`lv_display_trigger_activity` est appele sur les chemins SANS doigt",
         "%d sites dans dn_ui.c" % ui.count("lv_display_trigger_activity(NULL)"))
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
    bloc_fantome(src)
    bloc_accents()
    bloc_gris()
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
