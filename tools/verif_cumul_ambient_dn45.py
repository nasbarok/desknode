#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dn4-5 / AC3.2 — LE CUMUL « EN AMBIANT LA MAJORITE DU TEMPS » NE MENT PAS.
EPROUVE EN **EXECUTANT LE PRODUIT**, DEPUIS WSL, SANS CARTE ET SANS TOUR.

======================= CE QUE CET OUTIL FAIT, ET POURQUOI ==================

Le brief exige « en Ambient LA MAJORITE DU TEMPS ». **> 50 % est un seuil**,
⛔ pas une figure de style — et jusqu'a dn4-5 il n'avait AUCUN instrument.

⛔ IL NE REJOUE RIEN. `dn_veille.c` est COMPILE EN ENTIER et APPELE, avec une
   horloge PILOTABLE. Le cumul se verifie donc sur le produit, ⛔ pas sur une
   reimplementation du calcul.

🔴 LES DEUX PIEGES QUE CETTE GATE EXISTE POUR TENIR :

   1. **LE DENOMINATEUR EN TICKS.** La tentation etait de compter
      `s_secondes_vues`. Le depot dit lui-meme, DANS SA PROPRE SORTIE CONSOLE,
      que « le tick 1 Hz ne bat pas pendant `ui off` » et que `veille now`
      passe DELIBEREMENT a cote du tick. Un cumul en ticks aurait des TROUS et
      rendrait, sur 7 jours, un pourcentage plausible et faux. Le mutant B le
      montre.

   2. **L'INTERVALLE EN COURS OUBLIE.** Un module en Ambient depuis six jours
      dont on lirait le cumul SANS ajouter l'intervalle courant publierait le
      cumul de la derniere bascule — soit « 0 % d'Ambient » sur un critere qui
      est en realite tenu. C'est le pire cas : faux, plausible, et dans le sens
      qui fait echouer a tort. Le mutant A le montre.

⚠️ ET LE CONTROLE DE SOURCE PORTE SUR TOUT LE FICHIER, ⛔ pas sur une fonction :
   le cumul n'est exact que si AUCUN chemin n'ecrit `s_mode` en direct. « Une
   gate scopee a UNE fonction peut epingler VERT le meme defaut ailleurs. »

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
DN_VEILLE_C = os.path.join(MAIN, "dn_veille.c")
DN_VEILLE_H = os.path.join(MAIN, "dn_veille.h")

ok_total = [0]
ko_total = [0]
_tmp = []

SHIMS = {
    "esp_err.h": """
#pragma once
typedef int esp_err_t;
#define ESP_OK 0
#define ESP_FAIL -1
#define ESP_ERR_INVALID_ARG 0x102
#define ESP_ERR_INVALID_STATE 0x103
#define ESP_ERR_NOT_FOUND 0x105
static inline const char *esp_err_to_name(esp_err_t e) { (void)e; return "ERR"; }
""",
    "esp_log.h": """
#pragma once
extern int g_logs;
#define ESP_LOGI(t, ...) do { g_logs++; } while (0)
#define ESP_LOGW(t, ...) do { g_logs++; } while (0)
#define ESP_LOGE(t, ...) do { g_logs++; } while (0)
#define ESP_LOGD(t, ...) do { } while (0)
""",
    "esp_timer.h": """
#pragma once
#include <stdint.h>
extern int64_t g_temps_us;
int64_t esp_timer_get_time(void);
""",
    # ⚠️ Un magasin NVS de papier : dn_veille.c persiste ses reglages. On ne
    #    mesure PAS la persistance ici (c'est dn3-3), on l'empeche seulement de
    #    faire echouer la compilation ou de planter a l'appel.
    "nvs.h": """
#pragma once
#include "esp_err.h"
#include <stdint.h>
#include <stddef.h>
#define ESP_ERR_NVS_NOT_FOUND 0x1102
#define ESP_ERR_NVS_INVALID_HANDLE 0x1103
typedef int nvs_handle_t;
typedef enum { NVS_READONLY = 0, NVS_READWRITE = 1 } nvs_open_mode_t;
esp_err_t nvs_open(const char *, nvs_open_mode_t, nvs_handle_t *);
void nvs_close(nvs_handle_t);
esp_err_t nvs_get_u8(nvs_handle_t, const char *, uint8_t *);
esp_err_t nvs_set_u8(nvs_handle_t, const char *, uint8_t);
esp_err_t nvs_get_i32(nvs_handle_t, const char *, int32_t *);
esp_err_t nvs_set_i32(nvs_handle_t, const char *, int32_t);
esp_err_t nvs_commit(nvs_handle_t);
""",
    "shim.c": """
#include "nvs.h"
#include "esp_timer.h"
int g_logs = 0;
int64_t g_temps_us = 0;
int64_t esp_timer_get_time(void) { return g_temps_us; }
esp_err_t nvs_open(const char *n, nvs_open_mode_t m, nvs_handle_t *h)
{ (void)n; (void)m; if (h) { *h = 1; } return ESP_OK; }
void nvs_close(nvs_handle_t h) { (void)h; }
esp_err_t nvs_get_u8(nvs_handle_t h, const char *k, uint8_t *v)
{ (void)h; (void)k; (void)v; return ESP_ERR_NOT_FOUND; }
esp_err_t nvs_set_u8(nvs_handle_t h, const char *k, uint8_t v)
{ (void)h; (void)k; (void)v; return ESP_OK; }
esp_err_t nvs_get_i32(nvs_handle_t h, const char *k, int32_t *v)
{ (void)h; (void)k; (void)v; return ESP_ERR_NOT_FOUND; }
esp_err_t nvs_set_i32(nvs_handle_t h, const char *k, int32_t v)
{ (void)h; (void)k; (void)v; return ESP_OK; }
esp_err_t nvs_commit(nvs_handle_t h) { (void)h; return ESP_OK; }
""",
}


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


def sans_commentaires(txt):
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


def construire(src, etiquette):
    d = tempfile.mkdtemp(prefix="dn45c_")
    _tmp.append(d)
    for nom, contenu in SHIMS.items():
        io.open(os.path.join(d, nom), "w", encoding="utf-8").write(contenu)
    shutil.copy(DN_VEILLE_H, os.path.join(d, "dn_veille.h"))
    io.open(os.path.join(d, "dn_veille.c"), "w", encoding="utf-8").write(src)
    so = os.path.join(d, "libv.so")
    r = subprocess.run(["cc", "-shared", "-fPIC", "-O0", "-I", d, "-o", so,
                        os.path.join(d, "dn_veille.c"),
                        os.path.join(d, "shim.c")],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("     ECHEC DE COMPILATION (%s) :\n%s" % (etiquette, r.stderr[:2000]))
        return None
    lib = ctypes.CDLL(so)
    lib.dn_veille_cumul.argtypes = [ctypes.POINTER(ctypes.c_int64),
                                    ctypes.POINTER(ctypes.c_int64)]
    lib.dn_veille_mode.restype = ctypes.c_int
    lib.dn_veille_reveiller.restype = ctypes.c_bool
    lib.dn_veille_reveiller.argtypes = [ctypes.c_int]
    lib.dn_veille_forcer_dormir.restype = ctypes.c_bool
    lib.dn_veille_set_armee.restype = ctypes.c_int
    lib.dn_veille_set_armee.argtypes = [ctypes.c_bool]
    return lib


ACTIF, AMBIENT = 0, 1


class Banc:
    def __init__(self, lib):
        self.lib = lib

    def t(self, s_):
        ctypes.c_int64.in_dll(self.lib, "g_temps_us").value = int(s_ * 1_000_000)

    def dormir(self):
        return self.lib.dn_veille_forcer_dormir()

    def reveiller(self):
        return self.lib.dn_veille_reveiller(0)

    def cumul(self):
        a, b = ctypes.c_int64(0), ctypes.c_int64(0)
        self.lib.dn_veille_cumul(ctypes.byref(a), ctypes.byref(b))
        return a.value // 1_000_000, b.value // 1_000_000


def scenario(b):
    """Une journee de bureau en accelere : 3 episodes Actif courts, le reste en
    Ambient, PUIS UNE LONGUE PERIODE AMBIENT SANS AUCUNE BASCULE — c'est ce
    dernier morceau qui distingue un cumul honnete d'un cumul qui oublie
    l'intervalle en cours."""
    b.lib.dn_veille_set_armee(True)
    t = 0
    for actif_s, ambient_s in ((100, 900), (200, 1800), (60, 540)):
        t += actif_s
        b.t(t)
        b.dormir()
        t += ambient_s
        b.t(t)
        b.reveiller()
    # 20 000 s d'Ambient, et ON NE REVEILLE PAS : la lecture tombe EN PLEIN
    # episode. C'est le regime du soak.
    b.t(t)
    b.dormir()
    t += 20000
    b.t(t)
    a, amb = b.cumul()
    return {"actif": a, "ambient": amb, "total": a + amb,
            "attendu_actif": 360, "attendu_ambient": 3240 + 20000, "t": t}


# ⚠️ LES DEUX MOTIFS ONT ETE REECRITS LE 2026-08-28 : `dn_veille_cumul()` et
#    `veille_poser_mode()` ont recu un seqlock en revue de code, et les motifs
#    d'origine ne s'appliquaient plus. Une gate dont le mutant ne MUTE RIEN
#    n'eprouve rien — elle sortait « motif introuvable », ce qui est le seul
#    comportement acceptable : ⛔ elle n'a PAS fait semblant de passer.
MUTANTS = {
    "A. l'intervalle en cours est oublie": (
        """    int64_t now = esp_timer_get_time();
    if (now > t_mode) {
        c[idx] += now - t_mode;
    }
    if (out_actif_us) {""",
        """    if (out_actif_us) {"""),
    "B. le cumul compte des TICKS au lieu du temps": (
        """    s_mode_gen++;
    if (now > s_t_mode_us) {
        s_cumul_us[idx] += now - s_t_mode_us;
    }
    s_t_mode_us = now;
    s_mode = m;""",
        """    s_mode_gen++;
    s_cumul_us[idx] += (int64_t)s_secondes_vues * 1000000;
    s_t_mode_us = esp_timer_get_time();
    s_mode = m;"""),
}

# 🔴 CE QU'ON A ESSAYE ET QUI NE MARCHE PAS — ECRIT PLUTOT QUE TU (2026-08-28).
#    Un mutant « le seqlock du lecteur est retire » a ete construit, il
#    s'applique et il compile — mais il rend LE MEME CHIFFRE (23 240 s) que le
#    produit. C'est NORMAL et ca ne se contourne pas : ce banc est SEQUENTIEL,
#    il appelle le lecteur puis l'ecrivain l'un apres l'autre. UNE COURSE NE
#    S'EXERCE PAS SUR UN FIL UNIQUE. ⛔ Garder ce mutant aurait donne une gate
#    ROUGE en permanence, ou pire — l'inverser pour la faire passer aurait
#    epingle VERT une absence de preuve.
# ⇒ LE SEQLOCK EST DONC VERIFIE PAR SA FORME (§3bis), ⛔ PAS PAR SON EFFET. La
#   gate le dit, et c'est la limite exacte de ce qu'elle prouve.


def main():
    print("=" * 78)
    print("dn4-5 / AC3.2 — LE CUMUL AMBIENT NE MENT PAS, ET ON L'A VU CRIER")
    print("=" * 78)
    src, sha_c = lire(DN_VEILLE_C)
    _, sha_h = lire(DN_VEILLE_H)
    print("\nsources LUES : dn_veille.c %s · dn_veille.h %s" % (sha_c, sha_h))

    print("\n── 1. LE PRODUIT COMPILE ET REPOND ───────────────────────────────")
    lib = construire(src, "produit")
    if not ctrl(lib is not None, "dn_veille.c COMPILE ET CHARGE",
                "⛔ la gate n'a RIEN pu eprouver" if lib is None else "cc -O0"):
        return 1
    b = Banc(lib)
    r = scenario(b)
    ctrl(r["actif"] == r["attendu_actif"], "le cumul ACTIF est juste",
         "%d s attendus, %d publies" % (r["attendu_actif"], r["actif"]))
    ctrl(r["ambient"] == r["attendu_ambient"], "le cumul AMBIENT est juste",
         "%d s attendus, %d publies" % (r["attendu_ambient"], r["ambient"]))
    ctrl(r["total"] == r["t"], "actif + ambient == temps mural ECOULE",
         "%d s == %d s — ⛔ aucune seconde ne se perd" % (r["total"], r["t"]))
    pct = (r["ambient"] * 100) // r["total"]
    ctrl(pct > 50, "le seuil « majorite du temps » est TRANCHABLE",
         "Ambient = %d %% sur ce scenario" % pct)

    print("\n── 2. LE CAS QUI COMPTE : LIRE EN PLEIN EPISODE AMBIENT ──────────")
    b2 = Banc(construire(src, "episode"))
    b2.lib.dn_veille_set_armee(True)
    b2.t(10)
    b2.dormir()
    b2.t(10 + 6 * 24 * 3600)      # six jours d'Ambient, AUCUNE bascule
    a2, amb2 = b2.cumul()
    ctrl(amb2 == 6 * 24 * 3600,
         "six jours d'Ambient SANS bascule sont comptes",
         "%d s attendus, %d publies" % (6 * 24 * 3600, amb2))
    ctrl(a2 == 10, "et les 10 s d'Actif d'avant ne sont pas perdues",
         "%d s" % a2)

    print("\n── 3. LE CONTROLE DE SOURCE — SUR TOUT LE FICHIER ────────────────")
    nu = sans_commentaires(src)
    # ⚠️ `=` MAIS PAS `==`. Une premiere version comptait `s_mode == DN_VEILLE_…`
    #    comme une ECRITURE et annoncait « 5 ecritures » la ou il y en a 2 : une
    #    gate qui compte des comparaisons pour des affectations rougit sur du
    #    vide, et une gate qui rougit sur du vide finit desarmee.
    ecritures = re.findall(r'\bs_mode\s*=(?!=)', nu)
    dans_poseur = re.search(
        r'static void veille_poser_mode\([^)]*\)\s*\{(.*?)\n\}', nu, re.S)
    ctrl(dans_poseur is not None, "`veille_poser_mode()` existe", "")
    # ⚠️ `volatile` ADMIS depuis la revue du 2026-08-28 : `s_mode` est lu par la
    #    tache REPL sous seqlock pendant que la tache LVGL l'ecrit, et sans
    #    `volatile` le compilateur pourrait hisser la lecture hors de la boucle
    #    de relecture. La gate n'a pas a interdire le qualificatif qui rend le
    #    seqlock valide — elle doit continuer d'interdire les ECRITURES sauvages.
    n_init = len(re.findall(
        r'static\s+(?:volatile\s+)?dn_veille_mode_t s_mode\s*=(?!=)', nu))
    n_poseur = len(re.findall(r'\bs_mode\s*=(?!=)', dans_poseur.group(1))) \
        if dans_poseur else 0
    ctrl(len(ecritures) == n_init + n_poseur,
         "⛔ AUCUNE ecriture de `s_mode` hors du poseur",
         "%d ecriture(s) : %d initialiseur + %d dans le poseur"
         % (len(ecritures), n_init, n_poseur))
    ctrl(len(ecritures) >= 2, "et le poseur ECRIT bien le mode",
         "⛔ un poseur qui n'ecrit rien passerait le controle precedent")

    print("\n── 3bis. LE SEQLOCK EXISTE — VERIFIE PAR SA FORME ────────────────")
    # 🔴 AJOUTE LE 2026-08-28 (revue de code). `s_cumul_us[]`, `s_t_mode_us` et
    #    `s_mode` sont ecrits par la tache LVGL et lus par la tache REPL SANS
    #    verrou : instantane incoherent (jusqu'a six jours d'Ambient perdus) et
    #    dechirure int64 (±71,58 min). Le remede est le seqlock de pauvre deja
    #    impose a `dn_measure_bounce_get`.
    # ⛔ CE QUE CES CONTROLES PROUVENT : que le motif est LA. ⛔ CE QU'ILS NE
    #   PROUVENT PAS : qu'il ferme la course — voir le bloc MUTANTS.
    n_gen_poseur = len(re.findall(r'\bs_mode_gen\+\+',
                                  dans_poseur.group(1) if dans_poseur else ""))
    ctrl(n_gen_poseur == 2,
         "le poseur encadre son ecriture (generation IMPAIRE pendant)",
         "%d increment(s) de `s_mode_gen` dans le poseur — il en faut "
         "EXACTEMENT 2 (avant et apres)" % n_gen_poseur)
    corps_c = re.search(r'void dn_veille_cumul\([^)]*\)\s*\{(.*?)\n\}',
                        nu, re.S)
    zc = corps_c.group(1) if corps_c else ""
    ctrl("s_mode_gen" in zc,
         "le lecteur RELIT la generation",
         "⛔ sans relecture, la copie peut etre prise a cheval sur une bascule")
    ctrl(len(re.findall(r'\bvolatile\b[^;\n]*s_cumul_us', nu)) == 1
         and len(re.findall(r'\bvolatile\b[^;\n]*s_t_mode_us', nu)) == 1
         and len(re.findall(r'\bvolatile\b[^;\n]*s_mode\s*=', nu)) == 1,
         "les trois etats partages sont `volatile`",
         "⛔ sans lui le compilateur peut hisser la lecture HORS de la boucle "
         "de relecture, ce qui VIDE le seqlock de son sens")
    ctrl("essai" in zc and ">= 3" in zc,
         "le lecteur BORNE ses essais et publie quand meme",
         "⛔ boucler sans borne sur le chemin qu'on mesure serait pire que le "
         "defaut — meme arbitrage que `dn_measure_bounce_get`")

    # 🔴 LE CONTROLE QUI PROTEGE LE CHOIX DE CONCEPTION : ni le poseur ni le
    #    lecteur ne doivent toucher au compteur de TICKS, dont le depot dit
    #    lui-meme qu'il a des trous (`ui off`, `veille now`).
    corps_cumul = re.search(
        r'void dn_veille_cumul\([^)]*\)\s*\{(.*?)\n\}', nu, re.S)
    ctrl(corps_cumul is not None, "`dn_veille_cumul()` existe", "")
    zone = (dans_poseur.group(1) if dans_poseur else "") + \
           (corps_cumul.group(1) if corps_cumul else "")
    ctrl("s_secondes_vues" not in zone,
         "⛔ le cumul n'utilise PAS le compteur de ticks",
         "le tick a des trous DOCUMENTES (`ui off`, `veille now`)")
    ctrl("esp_timer_get_time" in zone,
         "le cumul lit bien l'horloge MURALE",
         "int64, aucun enroulement avant ~292 000 ans")

    print("\n── 4. LES TEMOINS NEGATIFS — ON DOIT LES VOIR ROUGIR ─────────────")
    for cle, (avant, apres) in MUTANTS.items():
        if not ctrl(src.count(avant) == 1,
                    "mutant « %s » : la mutation s'applique" % cle[:2],
                    "⛔ motif introuvable ou multiple — LA GATE NE MUTE RIEN"
                    if src.count(avant) != 1 else "1 occurrence"):
            continue
        libm = construire(src.replace(avant, apres, 1), "mutant " + cle)
        if not ctrl(libm is not None, "mutant « %s » : compile" % cle[:2], ""):
            continue
        rm = scenario(Banc(libm))
        ctrl(rm["ambient"] != rm["attendu_ambient"],
             "mutant « %s » : VU ROUGIR" % cle[:2],
             "%s — publie %d s d'Ambient au lieu de %d"
             % (cle[3:], rm["ambient"], rm["attendu_ambient"]))

    for d in _tmp:
        shutil.rmtree(d, ignore_errors=True)
    print("\n" + "=" * 78)
    print("BILAN : %d OK, %d KO" % (ok_total[0], ko_total[0]))
    print("=" * 78)
    return 1 if ko_total[0] else 0


if __name__ == "__main__":
    sys.exit(main())
