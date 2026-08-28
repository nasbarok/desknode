#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dn4-12 / AC5 — LA MACHINE A ETATS DE SERIE CONSECUTIVE EST PROUVEE SANS CARTE.
EPROUVE EN **COMPILANT ET EN APPELANT LE PRODUIT**, DEPUIS WSL.

======================= CE QUE CET OUTIL FAIT, ET POURQUOI ==================

⛔ IL NE REJOUE RIEN, ET CE N'EST PAS UN DETAIL. Un archetype A (relecture de
   source + mutants en memoire) NE SOLDERAIT PAS cet AC : la propriete a
   epingler est un COMPORTEMENT, ⛔ pas une forme. Le depot a deja paye un
   harnais qui REJOUAIT au lieu d'EXTRAIRE ET D'APPELER.

🎯 DEUX ETAGES, ET LES DEUX SONT LE PRODUIT :

   ETAGE 1 — L'UNITE PURE. `dn_measure_serie.h` est compile tel quel et ses
     trois fonctions sont appelees directement. C'est le SEUL etage qui peut
     exercer la CLASSE F (`ph_dechire`) : son declencheur est que `s_bnc_wraps`
     change ENTRE les deux lectures `w` et `w2`, a l'interieur de l'ISR, et il
     n'existe AUCUN point d'entree de coquille entre ces deux lignes. C'est
     exactement le sort de `ph_futur`, declare « JAMAIS VU BOUGER » par dn4-10 —
     et c'est la raison qui a fait choisir l'unite pure (AC5.4).

   ETAGE 2 — L'ISR REELLE. `dn_measure.c` est COMPILE EN ENTIER et sa vraie
     `on_vsync` est appelee via les callbacks que `dn_measure_attach()`
     enregistre. C'est ce qui prouve LE BRANCHEMENT : qu'une trame sans
     enroulement arrive bien en classe D, qu'une phase >= 2 periodes arrive bien
     en classe C, etc. Un etage 1 vert avec un branchement faux serait une gate
     « verte sur du code faux » — le depot en a deja epingle une.

🎯 LA TABLE `SHIMS` EST **REPRISE** DE `verif_rebouclage_dn45.py`, ⛔ PAS
   REINVENTEE. Seize coquilles y sont deja ecrites et eprouvees ; en recopier
   une variante ferait deriver les deux gates en silence, et la seconde
   compilerait AUTRE CHOSE que la premiere.

🔴 CINQ MUTANTS, CHACUN VU ROUGIR, SORTIE CAPTUREE (`--mutant <n>`). ⛔ Aucun
   n'est derriere un drapeau optionnel qu'aucun runner ne passe : ils tournent
   TOUS dans la passe nominale. Precedent `verif_verrou_lvgl_dn413.py`, ou UN
   controle n'a JAMAIS ete vu rougir.

⚠️ CE QUE CETTE GATE NE COUVRE PAS — AC5.7, ecrit ICI et ⛔ pas seulement dans
   la story :
     • RIEN sur le comportement sous ISR REELLE : ici les callbacks sont appeles
       depuis une tache Linux, en sequence, sans preemption ni cache coupe.
     • RIEN sur la CONCURRENCE : l'invariant « un seul ecrivain » est verifie
       par LECTURE (aucun autre site n'ecrit `s_bnc_serie`), ⛔ pas par course.
     • RIEN sur les VALEURS DE PHASE produites par le silicium : les phases sont
       posees par cette gate, donc elle prouve la LOGIQUE, ⛔ pas la dalle.
     • RIEN sur la CLASSE F en bout de chaine (voir etage 1 ci-dessus).
     • ⛔ ELLE NE RECITE AUCUNE VALEUR DU REMEDE : pas un chiffre de campagne
       n'est ecrit en dur ici comme s'il etait une propriete du code.

Sortie : `N OK / M KO`, exit 0 si tout passe. Publie le sha256 des sources LUES.
"""

import ctypes
import io
import os
import re
import shutil
import subprocess
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(RACINE, "tools")
MAIN = os.path.join(RACINE, "firmware", "desknode", "main")
sys.path.insert(0, TOOLS)

# 🎯 ⛔ ON NE REINVENTE PAS LES SEIZE COQUILLES. On importe la gate qui les
#    porte deja. Elle est protegee par `if __name__ == "__main__"`, donc
#    l'import n'execute rien.
import verif_rebouclage_dn45 as reb  # noqa: E402

DN_MEASURE_C = os.path.join(MAIN, "dn_measure.c")
DN_MEASURE_H = os.path.join(MAIN, "dn_measure.h")
DN_SERIE_H = os.path.join(MAIN, "dn_measure_serie.h")

ok_total = [0]
ko_total = [0]

# Les constantes DERIVEES du produit, ⛔ pas des nombres magiques. Elles sont
# RELUES de `dn_pins.h` / `dn_measure.c` plus bas et confrontees a ces valeurs :
# si le panneau change, la gate le DIT au lieu de mesurer a cote.
PERIODE_US = 26738  # DN_US_POUR_LIGNES(690) — arrondi au plus proche
T_DEMI_US = 775     # DN_US_POUR_LIGNES(9600 / 480) = 20 lignes
DEGROSSI = 32       # DN_PHASE_DEGROSSI

# Les phases de travail. `PH_REF` est celle du degrossissage, donc la reference.
PH_REF = 2000        # ⇒ ph_ref_us = 2000 us
PH_SAINE = 1900      # deficit 100 <= 775  ⇒ classe B
PH_DEFAUT = 1000     # deficit 1000 > 775  ⇒ classe A
PH_REJETEE = 60000   # >= 2 x 26738        ⇒ classe C

# L'ordre des champs de `dn_serie_t`, tel que la coquille de l'etage 1 les
# publie. ⛔ Il est ECRIT ici et VERIFIE contre l'en-tete (controle 0.3) : une
# gate qui lit les mauvais octets rend des chiffres plausibles.
CHAMPS_UNITE = ("cur", "cur_a", "cur_c", "cur_d", "cur_debut",
                "max", "max_a", "max_c", "max_d", "max_debut", "n", "rompues")


def ctrl(ok, libelle, detail=""):
    if ok:
        ok_total[0] += 1
        print("  [OK ] %-58s %s" % (libelle, detail))
    else:
        ko_total[0] += 1
        print("  [KO ] %-58s %s" % (libelle, detail))
    return ok


# ═══════════════════════════════════════════════════════════════════════════
#  ETAGE 1 — L'UNITE PURE, COMPILEE ET APPELEE
# ═══════════════════════════════════════════════════════════════════════════

PILOTE_UNITE = """
#include "dn_measure_serie.h"

/* ⚠️ COQUILLE DE PILOTAGE, ⛔ PAS UNE COPIE DE LA LOGIQUE. Elle ne fait
 *    qu'exposer les trois fonctions `static inline` du produit et publier
 *    l'etat. Toute la logique eprouvee est celle de `dn_measure_serie.h`. */
static dn_serie_t s;

void u_raz(void) { dn_serie_raz(&s); }
void u_defaut(unsigned classe, unsigned idx) { dn_serie_defaut(&s, classe, idx); }
void u_rompt(unsigned indeterminee) { dn_serie_rompt(&s, indeterminee); }

void u_lire(uint32_t *o)
{
    o[0] = s.cur;       o[1] = s.cur_a;  o[2] = s.cur_c;
    o[3] = s.cur_d;     o[4] = s.cur_debut;
    o[5] = s.max;       o[6] = s.max_a;  o[7] = s.max_c;
    o[8] = s.max_d;     o[9] = s.max_debut;
    o[10] = s.n;        o[11] = s.rompues;
}

unsigned u_cl_a(void) { return DN_SERIE_CL_A; }
unsigned u_cl_c(void) { return DN_SERIE_CL_C; }
unsigned u_cl_d(void) { return DN_SERIE_CL_D; }
"""


class Unite:
    """L'etage 1 : `dn_measure_serie.h` compile seul, appele directement."""

    def __init__(self, lib):
        self.lib = lib
        lib.u_defaut.argtypes = [ctypes.c_uint, ctypes.c_uint]
        lib.u_rompt.argtypes = [ctypes.c_uint]
        lib.u_lire.argtypes = [ctypes.POINTER(ctypes.c_uint32)]
        self.CL_A = lib.u_cl_a()
        self.CL_C = lib.u_cl_c()
        self.CL_D = lib.u_cl_d()
        lib.u_raz()

    def defaut(self, classe, idx):
        self.lib.u_defaut(classe, idx)

    def rompt(self, indeterminee):
        self.lib.u_rompt(1 if indeterminee else 0)

    def raz(self):
        self.lib.u_raz()

    def lire(self):
        buf = (ctypes.c_uint32 * len(CHAMPS_UNITE))()
        self.lib.u_lire(buf)
        return dict(zip(CHAMPS_UNITE, list(buf)))


def unite(src_serie_h, etiquette):
    d = reb.tmpdir()
    with io.open(os.path.join(d, "dn_measure_serie.h"), "w",
                 encoding="utf-8") as f:
        f.write(src_serie_h)
    with io.open(os.path.join(d, "pilote.c"), "w", encoding="utf-8") as f:
        f.write(PILOTE_UNITE)
    so = os.path.join(d, "libu.so")
    r = subprocess.run(["cc", "-shared", "-fPIC", "-O0", "-I", d, "-o", so,
                        os.path.join(d, "pilote.c")],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("     ECHEC DE COMPILATION (%s) :\n%s" % (etiquette,
                                                        r.stderr[:2000]))
        return None
    return Unite(ctypes.CDLL(so))


# ═══════════════════════════════════════════════════════════════════════════
#  ETAGE 2 — `dn_measure.c` EN ENTIER, SA VRAIE `on_vsync` APPELEE
# ═══════════════════════════════════════════════════════════════════════════

# ⚠️ Le pilote de `verif_rebouclage_dn45.py` n'expose que `shim_trame()`, qui
#    joue enroulement PUIS vsync au MEME instant. Pour trancher les huit classes
#    il faut les DEUX ISR SEPAREMENT et a des instants CHOISIS. On AJOUTE deux
#    entrees a la MEME coquille, ⛔ on n'en ecrit pas une seconde.
SHIM_C_PLUS = reb.SHIM_C + """
/* dn4-12 : les deux ISR, separement, pour choisir la PHASE de chaque trame. */
void shim_wrap(void)
{
    esp_lcd_rgb_panel_event_data_t d = {0};
    if (s_cbs.on_frame_buf_complete) { s_cbs.on_frame_buf_complete(NULL, &d, NULL); }
}
void shim_vsync(void)
{
    esp_lcd_rgb_panel_event_data_t d = {0};
    if (s_cbs.on_vsync) { s_cbs.on_vsync(NULL, &d, NULL); }
}
"""


def construire_carte(src_c, src_h, src_serie_h, etiquette):
    """Comme `reb.construire()`, mais avec les sources MUTABLES passees en
    argument (dn_measure.c, dn_measure.h ET dn_measure_serie.h) et la coquille
    etendue. ⛔ Les seize coquilles viennent de `reb.SHIMS`, verbatim."""
    d = reb.tmpdir()
    os.makedirs(os.path.join(d, "freertos"), exist_ok=True)
    os.makedirs(os.path.join(d, "driver"), exist_ok=True)
    for nom, contenu in reb.SHIMS:
        c = SHIM_C_PLUS if nom == "shim.c" else contenu
        with io.open(os.path.join(d, nom), "w", encoding="utf-8") as f:
            f.write(c)
    shutil.copy(reb.DN_PINS_H, os.path.join(d, "dn_pins.h"))
    for nom, contenu in (("dn_measure.h", src_h),
                         ("dn_measure_serie.h", src_serie_h),
                         ("dn_measure.c", src_c)):
        with io.open(os.path.join(d, nom), "w", encoding="utf-8") as f:
            f.write(contenu)
    so = os.path.join(d, "libm.so")
    r = subprocess.run(["cc", "-shared", "-fPIC", "-O0", "-I", d, "-o", so,
                        os.path.join(d, "dn_measure.c"),
                        os.path.join(d, "shim.c")],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("     ECHEC DE COMPILATION (%s) :\n%s" % (etiquette,
                                                        r.stderr[:2500]))
        return None
    return ctypes.CDLL(so)


class Carte:
    """L'etage 2 : la VRAIE `on_vsync` du produit, pilotee trame par trame.

    ⚠️ Chaque instance a SON `.so` : les statiques de `dn_measure.c` sont
       globales au module, et rejouer deux scenarios dans le meme .so les ferait
       s'empoisonner (regle heritee de `verif_rebouclage_dn45.py`)."""

    def __init__(self, lib, Bounce):
        self.lib = lib
        self.Bounce = Bounce
        lib.dn_measure_attach.restype = ctypes.c_int
        lib.dn_measure_attach.argtypes = [ctypes.c_void_p]
        lib.dn_measure_bounce_get.argtypes = [ctypes.c_void_p]
        self.now = 1_000_000  # 1 s d'uptime : ⛔ on ne part pas de 0
        self.t(self.now)
        lib.dn_measure_attach(None)

    def t(self, us):
        ctypes.c_int64.in_dll(self.lib, "g_temps_us").value = int(us)

    def raz(self):
        self.lib.dn_measure_bounce_reset()

    def lire(self):
        b = self.Bounce()
        self.lib.dn_measure_bounce_get(ctypes.byref(b))
        return b

    # ── LES HUIT CLASSES, UNE METHODE PAR CLASSE ────────────────────────────
    def _avance(self):
        self.now += PERIODE_US

    def phase(self, ph):
        """Une trame a UN enroulement, de phase `ph` us. ⇒ classe A, B, C ou H
        selon `ph` et l'etat du degrossissage."""
        self._avance()
        self.t(self.now - ph)
        self.lib.shim_wrap()
        self.t(self.now)
        self.lib.shim_vsync()

    def manque(self):
        """AUCUN enroulement dans la trame ⇒ n == 0 ⇒ CLASSE D."""
        self._avance()
        self.t(self.now)
        self.lib.shim_vsync()

    def futur(self):
        """Horodatage d'enroulement POSTERIEUR a l'entree de l'ISR de vsync
        ⇒ CLASSE E. C'est l'entrelacement des deux ISR, reproduit en posant
        l'horloge a l'envers."""
        self._avance()
        self.t(self.now + 1000)
        self.lib.shim_wrap()
        self.t(self.now)
        self.lib.shim_vsync()

    def double(self):
        """DEUX enroulements dans la trame ⇒ n >= 2 ⇒ CLASSE G."""
        self._avance()
        self.t(self.now - PH_REF)
        self.lib.shim_wrap()
        self.lib.shim_wrap()
        self.t(self.now)
        self.lib.shim_vsync()

    def degrossir(self):
        """Les 32 trames qui FIGENT la reference (classe H). ⛔ Aucune ne doit
        ouvrir de serie : avant `ph_ref_us`, aucun deficit n'est calculable."""
        for _ in range(DEGROSSI):
            self.phase(PH_REF)


def carte(src_c, src_h, src_serie_h, etiquette, Bounce):
    lib = construire_carte(src_c, src_h, src_serie_h, etiquette)
    if lib is None:
        return None
    return Carte(lib, Bounce)


# ═══════════════════════════════════════════════════════════════════════════
#  LES MUTATIONS — chacune est un DEFAUT REEL, deja paye ou explicitement
#  interdit par une decision. ⛔ Aucune n'est une faute de frappe cosmetique.
# ═══════════════════════════════════════════════════════════════════════════

MUTANTS = {
    # M1 — LE DEFAUT EXACT DE `dn_hist_rattraper()` (precedent dn4-13) :
    #      l'ecretage pose AVANT le comptage. `ui off` de 10 min et de 1 h
    #      imprimaient EXACTEMENT la meme phrase.
    "M1": ("serie_h",
           "    s->cur++;",
           "    if (s->cur > 120u) { s->cur = 120u; }\n    s->cur++;",
           "l'ecretage pose AVANT le comptage"),
    # M2 — LA DECISION D2 RENVERSEE : `ph_rejete` (classe C) romprait la serie.
    #      Elle rendrait 0 PENDANT QUE L'ECRAN EST FIGE.
    "M2": ("measure_c",
           "dn_serie_defaut(&s_bnc_serie, DN_SERIE_CL_C, idx_trame);",
           "dn_serie_rompt(&s_bnc_serie, 0u);",
           "la classe C ROMPT la serie au lieu de la continuer (D2)"),
    # M3 — UNE INDETERMINEE QUI CONTINUE LA SERIE EN SILENCE : elle
    #      FABRIQUERAIT de la duree, et la reserve d'AC1.4 resterait a zero.
    "M3": ("serie_h",
           "    if (s->cur != 0u) {\n        if (indeterminee) {",
           "    if (indeterminee) { return; }\n    if (s->cur != 0u) {\n        if (indeterminee) {",
           "une INDETERMINEE continue la serie en silence"),
    # M4 — UN CHAMP NEUF OUBLIE DANS LA RAZ : le compteur ne se remet JAMAIS a
    #      zero. « Un temoin se remet a zero, ou il n'est pas un temoin. »
    "M4": ("serie_h",
           "    s->max = 0u;\n",
           "",
           "un champ neuf OUBLIE dans la branche RAZ"),
    # M5 — UN CHAMP NEUF SOUS UNE FORME QUE `struct_depuis_entete()` NE SAIT PAS
    #      TRADUIRE. `verif_rebouclage_dn45.py` doit CRIER, ⛔ pas mourir en
    #      silence. (C'est la contrainte dure (a) d'AC5.3, epinglee par un temoin.)
    "M5": ("measure_h",
           "    uint32_t ser_max;",
           "    uint32_t ser_max[4];",
           "un champ neuf NON TRADUISIBLE par le miroir ctypes"),
}


def muter(src, cle):
    _, avant, apres, _ = MUTANTS[cle]
    n = src.count(avant)
    return (src.replace(avant, apres, 1) if n else src), n


# ═══════════════════════════════════════════════════════════════════════════
#  LES NEUF CAS D'AC5.5
# ═══════════════════════════════════════════════════════════════════════════

def cas_unite(u, titre=""):
    """(a)(b)(e)(g)(h)(i) au niveau de l'UNITE — le seul etage qui peut exercer
    la CLASSE F. Rend un dict de grandeurs, ⛔ pas un verdict : c'est ce qui
    permet de rejouer LE MEME scenario sur un mutant et de comparer."""
    out = {}

    # (a) une serie de UNE trame
    u.raz()
    u.defaut(u.CL_A, 40)
    u.rompt(False)
    out["a_max"] = u.lire()["max"]
    out["a_n"] = u.lire()["n"]

    # (b) une serie LONGUE (>= 500 trames)
    u.raz()
    for i in range(700):
        u.defaut(u.CL_A, 40 + i)
    out["b_max"] = u.lire()["max"]
    out["b_debut"] = u.lire()["max_debut"]

    # (b bis) 🔴 LA MEME EPREUVE A UNE TROISIEME LONGUEUR — ⛔ ET C'EST ELLE QUI
    #    EPINGLE L'ECRETAGE. « 700 se lit 700 » ne suffit pas : un plafond a 121
    #    laisse passer ce controle des que la borne est au-dessus. Le critere de
    #    dn4-13 est « DEUX DUREES DIFFERENTES RENDENT DEUX NOMBRES DIFFERENTS »
    #    (135 vs 29), et c'est cette paire-la qu'on mesure.
    u.raz()
    for i in range(200):
        u.defaut(u.CL_A, 40 + i)
    out["b2_max"] = u.lire()["max"]

    # ⚠️ (a) ET (b) SONT LA MEME EPREUVE A DEUX REGIMES, ET C'EST DELIBERE :
    #    `verif_hist_dn413.py` BENISSAIT un trou parce que ses quatre cas
    #    etaient tous du meme regime. Une gate qui teste UN SEUL regime benit
    #    le trou. On exige donc que les deux nombres DIFFERENT.

    # (e) une serie rompue par CHACUNE des trois indeterminees, compteur verifie
    u.raz()
    for k in range(3):
        u.defaut(u.CL_A, 100 + k * 10)
        u.defaut(u.CL_A, 101 + k * 10)
        u.rompt(True)          # E, puis F, puis G — l'unite ne les distingue
        # pas : c'est l'etage 2 qui prouve que les trois y arrivent.
    s = u.lire()
    out["e_rompues"] = s["rompues"]
    out["e_max"] = s["max"]
    out["e_n"] = s["n"]
    # ⚠️ une indeterminee qui tombe alors qu'AUCUNE serie ne court ne rompt
    #    rien, et ne doit donc RIEN compter.
    u.raz()
    u.rompt(True)
    u.rompt(True)
    out["e_rompues_a_vide"] = u.lire()["rompues"]

    # (g) DEUX series successives, la SECONDE la plus longue
    u.raz()
    for i in range(5):
        u.defaut(u.CL_D, 10 + i)
    u.rompt(False)
    for i in range(40):
        u.defaut(u.CL_C, 200 + i)
    u.rompt(False)
    s = u.lire()
    out["g_max"] = s["max"]
    out["g_debut"] = s["max_debut"]
    out["g_c"] = s["max_c"]
    out["g_d"] = s["max_d"]
    out["g_n"] = s["n"]

    # (h) une serie EN COURS au moment de la lecture — le max l'inclut DEJA
    u.raz()
    for i in range(9):
        u.defaut(u.CL_D, 1 + i)
    u.rompt(False)
    for i in range(25):
        u.defaut(u.CL_A, 50 + i)
    s = u.lire()               # ⛔ PAS de rupture avant la lecture
    out["h_cur"] = s["cur"]
    out["h_max"] = s["max"]

    # (i) la RAZ : tout revient a zero, et le temoin est REJOUABLE 3 fois
    rejouable = []
    for _ in range(3):
        u.raz()
        z = u.lire()
        rejouable.append(all(v == 0 for v in z.values()))
        for i in range(12):
            u.defaut(u.CL_A, 5 + i)
        rejouable.append(u.lire()["max"] == 12)
    out["i_rejouable"] = all(rejouable)
    u.raz()
    out["i_apres_raz_tout_nul"] = sorted(set(u.lire().values())) == [0]
    (void_titre) = titre
    return out


def cas_carte(c):
    """(c)(d)(f) + le BRANCHEMENT des huit classes, a travers la VRAIE ISR."""
    out = {}

    # (f) LE DEGROSSISSAGE : aucune serie ne commence avant la 32e trame
    c.raz()
    c.phase(PH_REF)            # consomme la RAZ
    c.degrossir()
    b = c.lire()
    out["f_max_apres_degrossi"] = b.ser_max
    out["f_n_apres_degrossi"] = b.ser_n
    out["f_ph_ref"] = b.ph_ref_us
    out["f_t_demi"] = b.t_demi_us
    out["f_ecarte"] = b.ph_ecarte

    # classe B (saine) : le deficit reste sous le seuil ⇒ rien ne s'ouvre
    for _ in range(5):
        c.phase(PH_SAINE)
    b = c.lire()
    out["b_max"] = b.ser_max
    out["b_100pc"] = b.ph_100pc

    # classe A : le deficit franchit le seuil ⇒ la serie court
    for _ in range(12):
        c.phase(PH_DEFAUT)
    b = c.lire()
    out["A_max"] = b.ser_max
    out["A_compo_a"] = b.ser_max_a
    out["A_cur"] = b.ser_courante
    out["A_100pc"] = b.ph_100pc
    out["A_debut"] = b.ser_max_debut
    c.phase(PH_SAINE)          # on referme

    # (c) une serie contenant des trames de CLASSE C (`ph_rejete`)
    # 🔴 RAZ + DEGROSSISSAGE AVANT CHAQUE CLASSE : sans ca, la serie de 12
    #    trames de classe A ci-dessus reste le maximum et le cas ne mesure RIEN
    #    (il ne pourrait pas non plus voir son mutant rougir).
    c.raz()
    c.phase(PH_REF)
    c.degrossir()
    for _ in range(7):
        c.phase(PH_REJETEE)
    b = c.lire()
    out["c_max"] = b.ser_max
    out["c_compo_c"] = b.ser_max_c
    out["c_rejete"] = b.ph_rejete
    c.phase(PH_SAINE)

    # (d) une serie contenant des trames de CLASSE D (`manques`)
    c.raz()
    c.phase(PH_REF)
    c.degrossir()
    for _ in range(21):
        c.manque()
    b = c.lire()
    out["d_max"] = b.ser_max
    out["d_compo_d"] = b.ser_max_d
    out["d_manques"] = b.manques
    c.phase(PH_SAINE)

    # CLASSE E — horodatage POSTERIEUR : rompt ET est comptee
    c.raz()
    c.phase(PH_REF)
    c.degrossir()
    for _ in range(4):
        c.phase(PH_DEFAUT)
    c.futur()
    b = c.lire()
    out["E_futur"] = b.ph_futur
    out["E_rompues"] = b.ser_rompues_indet
    out["E_cur"] = b.ser_courante
    out["E_max"] = b.ser_max

    # CLASSE G — deux enroulements : rompt ET est comptee
    for _ in range(6):
        c.phase(PH_DEFAUT)
    c.double()
    b = c.lire()
    out["G_doubles_ec"] = b.ph_doubles_ecartes
    out["G_rompues"] = b.ser_rompues_indet
    out["G_cur"] = b.ser_courante
    out["G_max"] = b.ser_max

    # LA COMPOSITION SEPARE DEUX PATHOLOGIES — c'est la raison d'etre d'AC1.6
    c.raz()
    c.phase(PH_REF)
    c.degrossir()
    for _ in range(30):
        c.phase(PH_DEFAUT)     # 30 x A
    for _ in range(9):
        c.manque()             # 9 x D, DANS LA MEME SERIE
    b = c.lire()
    out["compo_max"] = b.ser_max
    out["compo_a"] = b.ser_max_a
    out["compo_d"] = b.ser_max_d
    out["compo_c"] = b.ser_max_c

    # LA RAZ, VUE A TRAVERS L'ISR : elle est CONSOMMEE PAR L'ISR, ⛔ pas ici
    c.raz()
    b = c.lire()
    out["raz_en_attente"] = bool(b.raz_en_attente)
    out["raz_max_avant_vsync"] = b.ser_max     # ⛔ pas encore consommee
    c.phase(PH_REF)
    b = c.lire()
    out["raz_max_apres_vsync"] = b.ser_max
    out["raz_gen"] = b.raz_gen
    return out


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 78)
    print("dn4-12 / AC5 — LA PLUS LONGUE SERIE, PROUVEE SANS CARTE")
    print("=" * 78)

    src_c, h_c = reb.lire(DN_MEASURE_C)
    src_h, h_h = reb.lire(DN_MEASURE_H)
    src_s, h_s = reb.lire(DN_SERIE_H)
    print("\nsources LUES : dn_measure.c %s · dn_measure.h %s · "
          "dn_measure_serie.h %s" % (h_c, h_h, h_s))
    print("⚠️ PORTEE : cette gate prouve la LOGIQUE de la machine a etats et son")
    print("   BRANCHEMENT dans l'ISR. ⛔ RIEN sur le silicium, RIEN sur la")
    print("   concurrence, RIEN sur les valeurs de phase reelles. Voir l'en-tete.")

    # ── 0. LE PRODUIT COMPILE ET SE CHARGE ─────────────────────────────────
    print("\n── 0. LES DEUX ETAGES COMPILENT ET SE CHARGENT ───────────────────")
    Bounce, msg = reb.struct_depuis_entete(src_h)
    ctrl(Bounce is not None, "`dn_bounce_stats_t` traduite en ctypes", msg)
    if Bounce is None:
        return 1
    manquants = [c for c in ("ser_max", "ser_max_a", "ser_max_c", "ser_max_d",
                             "ser_max_debut", "ser_n", "ser_rompues_indet",
                             "ser_courante", "raz_gen")
                 if not hasattr(Bounce, c)]
    ctrl(not manquants, "les NEUF champs publies de dn4-12 sont dans l'en-tete",
         "manquants : %s" % (manquants or "aucun"))

    u = unite(src_s, "unite nominale")
    ctrl(u is not None, "ETAGE 1 : `dn_measure_serie.h` COMPILE ET CHARGE",
         "cc -O0, trois `static inline` exposees")
    if u is None:
        return 1
    # ⚠️ L'ORDRE DES CHAMPS EST VERIFIE CONTRE L'EN-TETE, ⛔ pas suppose : une
    #    gate qui lit les mauvais octets rend des chiffres plausibles.
    m = re.search(r'typedef struct \{(.*?)\} dn_serie_t;', src_s, re.S)
    dans_h = re.findall(r'volatile\s+uint32_t\s+(\w+)\s*;',
                        re.sub(r'/\*.*?\*/', ' ', m.group(1), flags=re.S))
    ctrl(tuple(dans_h) == CHAMPS_UNITE,
         "l'ORDRE des 12 champs de `dn_serie_t` == celui que la gate lit",
         "en-tete : %s" % ", ".join(dans_h))

    c = carte(src_c, src_h, src_s, "carte nominale", Bounce)
    ctrl(c is not None, "ETAGE 2 : `dn_measure.c` COMPILE, `on_vsync` ATTACHEE",
         "cc -O0, la VRAIE ISR est appelee par la coquille")
    if c is None:
        return 1

    # ── 1. LES CONSTANTES DU PRODUIT, ⛔ PAS DES NOMBRES MAGIQUES ──────────
    print("\n── 1. LES CONSTANTES SONT CELLES DU PRODUIT ──────────────────────")
    b0 = c.lire()
    ctrl(b0.t_demi_us == T_DEMI_US,
         "`t_demi_us` relu du produit == le seuil que la gate vise",
         "%lu us (bounce 9 600 px ⇒ 20 lignes)" % b0.t_demi_us)
    ctrl(b0.periode_ns == 26737500,
         "`periode_ns` relue du produit (EXACTE, ⛔ pas tronquee)",
         "%lu ns" % b0.periode_ns)
    ctrl(PERIODE_US == (b0.periode_ns + 500) // 1000,
         "la periode que la gate AVANCE == celle du produit, arrondie",
         "%d us — ⛔ pas un nombre magique" % PERIODE_US)
    ctrl(b0.ph_degrossi_n == DEGROSSI,
         "`ph_degrossi_n` relu du produit == %d" % DEGROSSI,
         "%lu trames" % b0.ph_degrossi_n)

    # ── 2. LES NEUF CAS D'AC5.5 ────────────────────────────────────────────
    print("\n── 2. LES NEUF CAS D'AC5.5 ───────────────────────────────────────")
    U = cas_unite(u)
    C = cas_carte(c)

    ctrl(U["a_max"] == 1 and U["a_n"] == 1,
         "(a) une serie de UNE trame est comptee 1",
         "max=%d · series=%d" % (U["a_max"], U["a_n"]))
    ctrl(U["b_max"] == 700 and U["b_debut"] == 40,
         "(b) une serie LONGUE (700 trames) n'est ni ecretee ni plafonnee",
         "max=%d, debut=#%d — ⛔ aucun plafond" % (U["b_max"], U["b_debut"]))
    ctrl(U["a_max"] != U["b_max"] and U["b2_max"] != U["b_max"]
         and U["b2_max"] == 200,
         "🔴 TROIS DUREES DIFFERENTES ⇒ TROIS NOMBRES DIFFERENTS",
         "1 · %d · %d — le critere d'acceptation minimum (dn4-13 : 135 vs 29)"
         % (U["b2_max"], U["b_max"]))
    ctrl(C["c_max"] == 7 and C["c_compo_c"] == 7 and C["c_rejete"] == 7,
         "(c) une serie de CLASSE C (`ph_rejete`) COURT — D2",
         "max=%d, dont C=%d · ph_rejete=%d"
         % (C["c_max"], C["c_compo_c"], C["c_rejete"]))
    ctrl(C["d_max"] == 21 and C["d_compo_d"] == 21,
         "(d) une serie de CLASSE D (`manques`) COURT",
         "max=%d, dont D=%d · manques=%d"
         % (C["d_max"], C["d_compo_d"], C["d_manques"]))
    ctrl(U["e_rompues"] == 3 and U["e_max"] == 2,
         "(e) TROIS ruptures par indeterminee, COMPTEES",
         "rompues=%d · max=%d (chaque serie faisait 2 trames)"
         % (U["e_rompues"], U["e_max"]))
    ctrl(U["e_rompues_a_vide"] == 0,
         "(e) une indeterminee HORS SERIE ne compte AUCUNE rupture",
         "elle ne coupe rien : la compter gonflerait la reserve pour rien")
    ctrl(C["E_futur"] == 1 and C["E_rompues"] == 1 and C["E_cur"] == 0,
         "(e) CLASSE E dans l'ISR REELLE : rompt ET est comptee",
         "ph_futur=%d · rompues=%d · en cours=%d"
         % (C["E_futur"], C["E_rompues"], C["E_cur"]))
    ctrl(C["G_doubles_ec"] == 1 and C["G_rompues"] == 2 and C["G_cur"] == 0,
         "(e) CLASSE G dans l'ISR REELLE : rompt ET est comptee",
         "ph_doubles_ecartes=%d · rompues=%d · en cours=%d"
         % (C["G_doubles_ec"], C["G_rompues"], C["G_cur"]))
    ctrl(C["f_max_apres_degrossi"] == 0 and C["f_n_apres_degrossi"] == 0,
         "(f) AUCUNE serie ne commence pendant le degrossissage",
         "%d trames ecartees, ph_ref FIGEE a %d us, max=%d"
         % (C["f_ecarte"], C["f_ph_ref"], C["f_max_apres_degrossi"]))
    ctrl(C["A_debut"] > DEGROSSI,
         "(f) la premiere serie de CLASSE A commence APRES la 32e trame",
         "debut = trame #%d" % C["A_debut"])
    ctrl(U["g_max"] == 40 and U["g_n"] == 2 and U["g_c"] == 40
         and U["g_d"] == 0 and U["g_debut"] == 200,
         "(g) deux series : le MAXIMUM suit la SECONDE",
         "max=%d (C=%d, D=%d) debut=#%d · %d series"
         % (U["g_max"], U["g_c"], U["g_d"], U["g_debut"], U["g_n"]))
    ctrl(U["h_cur"] == 25 and U["h_max"] == 25,
         "(h) une serie EN COURS est DEJA dans le maximum",
         "en cours=%d · max=%d (la precedente faisait 9)"
         % (U["h_cur"], U["h_max"]))
    ctrl(U["i_rejouable"] and U["i_apres_raz_tout_nul"],
         "(i) la RAZ remet les 12 champs a zero — REJOUABLE 3 fois",
         "« un temoin se remet a zero, ou il n'est pas un temoin »")

    # ── 3. LE BRANCHEMENT DES HUIT CLASSES, DANS L'ISR REELLE ──────────────
    print("\n── 3. LE BRANCHEMENT DES HUIT CLASSES, DANS L'ISR REELLE ─────────")
    ctrl(C["b_max"] == 0 and C["b_100pc"] == 0,
         "CLASSE B (saine) : elle ROMPT, rien ne s'ouvre",
         "max=%d · ph_100pc=%d" % (C["b_max"], C["b_100pc"]))
    ctrl(C["A_max"] == 12 and C["A_compo_a"] == 12 and C["A_100pc"] == 12,
         "CLASSE A (deficit franchi) : la serie COURT",
         "max=%d, dont A=%d · ph_100pc=%d"
         % (C["A_max"], C["A_compo_a"], C["A_100pc"]))
    ctrl(C["compo_max"] == 39 and C["compo_a"] == 30 and C["compo_d"] == 9
         and C["compo_c"] == 0,
         "🎯 LA COMPOSITION SEPARE DEUX PATHOLOGIES DANS UNE MEME SERIE",
         "39 trames = 30 A + 9 D + 0 C — deux remedes differents")
    ctrl(C["raz_en_attente"] and C["raz_max_avant_vsync"] != 0,
         "la RAZ est DIFFEREE : lue dans la foulee, elle n'a RIEN remis",
         "raz_en_attente=%s · max encore a %d"
         % (C["raz_en_attente"], C["raz_max_avant_vsync"]))
    ctrl(C["raz_max_apres_vsync"] == 0,
         "…et l'ISR la CONSOMME au vsync suivant",
         "max=%d apres une trame · %d RAZ consommee(s)"
         % (C["raz_max_apres_vsync"], C["raz_gen"]))

    # ── 4. LES CINQ MUTANTS — ON DOIT LES VOIR ROUGIR ──────────────────────
    print("\n── 4. LES CINQ MUTANTS — ON DOIT LES VOIR ROUGIR ─────────────────")
    for cle in ("M1", "M2", "M3", "M4", "M5"):
        cible, _, _, libelle = MUTANTS[cle]
        base = {"serie_h": src_s, "measure_c": src_c, "measure_h": src_h}[cible]
        mute, n = muter(base, cle)
        if not ctrl(n >= 1, "mutant %s : la mutation s'applique" % cle,
                    "%d occurrence(s) — %s" % (n, libelle)):
            continue

        if cle == "M5":
            # 🔴 CE MUTANT-LA NE S'EXECUTE PAS : il epingle que le MIROIR de
            #    `verif_rebouclage_dn45.py` CRIE au lieu de mourir en silence.
            # ⚠️ LA CONTRAINTE (a) D'AC5.3 A **DEUX** CHEMINS DE REFUS, et une
            #    gate qui n'en eprouve qu'un benit l'autre : le TABLEAU (le nom
            #    n'est plus un identifiant) et le TYPE NON MAPPE (`size_t` &
            #    consorts). On exige les DEUX, et que le cri NOMME le coupable —
            #    « la gate n'a RIEN pu eprouver » est exactement le message
            #    muet qui a coute une journee le 2026-08-27.
            B2, msg2 = reb.struct_depuis_entete(mute)
            ctrl(B2 is None and "ser_max" in msg2,
                 "mutant M5a (TABLEAU) : VU ROUGIR, et le cri NOMME le champ",
                 "le miroir CRIE — « %s »" % msg2)
            mute_t = src_h.replace("    uint32_t ser_max;",
                                   "    size_t ser_max;", 1)
            B3, msg3 = reb.struct_depuis_entete(mute_t)
            ctrl(B3 is None and "ser_max" in msg3,
                 "mutant M5b (TYPE NON MAPPE) : VU ROUGIR, et le cri NOMME",
                 "le miroir CRIE — « %s »" % msg3)
            continue

        if cible == "serie_h":
            u2 = unite(mute, "mutant " + cle)
            if not ctrl(u2 is not None, "mutant %s : compile" % cle, ""):
                continue
            U2 = cas_unite(u2)
            if cle == "M1":
                # 🔴 LA PROPRIETE CASSEE, ⛔ PAS LA VALEUR DU PLAFOND : deux
                #    durees de rapport 3,5 (200 et 700 trames) cessent de se
                #    distinguer. C'est mot pour mot le defaut de dn4-13, ou
                #    `ui off` de 10 min et de 1 h imprimaient la MEME phrase.
                ctrl(U2["b_max"] == U2["b2_max"] and U2["b_max"] < U["b_max"],
                     "mutant M1 : VU ROUGIR",
                     "200 et 700 trames rendent LE MEME nombre (%d) — la duree "
                     "est EFFACEE avant d'etre comptee (nominal : %d vs %d)"
                     % (U2["b_max"], U["b2_max"], U["b_max"]))
            elif cle == "M3":
                ctrl(U2["e_rompues"] == 0 and U2["e_max"] > U["e_max"],
                     "mutant M3 : VU ROUGIR",
                     "rompues=%d (au lieu de %d) et la serie GONFLE a %d (au "
                     "lieu de %d) : la duree est FABRIQUEE"
                     % (U2["e_rompues"], U["e_rompues"], U2["e_max"],
                        U["e_max"]))
            elif cle == "M4":
                ctrl(not U2["i_apres_raz_tout_nul"] or not U2["i_rejouable"],
                     "mutant M4 : VU ROUGIR",
                     "un champ ne revient pas a zero apres la RAZ ⇒ le temoin "
                     "n'est plus rejouable")
        else:
            c2 = carte(mute, src_h, src_s, "mutant " + cle, Bounce)
            if not ctrl(c2 is not None, "mutant %s : compile" % cle, ""):
                continue
            C2 = cas_carte(c2)
            if cle == "M2":
                ctrl(C2["c_max"] < C["c_max"] and C2["c_compo_c"] == 0,
                     "mutant M2 : VU ROUGIR",
                     "7 trames HORS BORNE rendent max=%d (au lieu de %d) et "
                     "C=%d : ZERO pendant que l'ecran est fige"
                     % (C2["c_max"], C["c_max"], C2["c_compo_c"]))

    # ── 5. L'INVARIANT DE CONCURRENCE (D5) N'A PAS BOUGE ───────────────────
    print("\n── 5. L'INVARIANT DE CONCURRENCE (D5) N'A PAS BOUGE ──────────────")
    nu = reb.sans_commentaires(src_c)
    isr = nu[nu.index("static IRAM_ATTR bool on_vsync"):]
    isr = isr[:isr.index("static IRAM_ATTR bool on_frame_buf_complete")]
    for interdit, quoi in (("portENTER_CRITICAL", "section critique"),
                           ("xSemaphoreTake", "prise de semaphore"),
                           ("ESP_LOG", "log")):
        ctrl(interdit not in isr,
             "⛔ AUCUN(E) %s ajoute(e) dans `on_vsync`" % quoi,
             "« on mesure une famine, on n'allait pas la fabriquer »")
    # 🔴 CE CONTROLE-CI A SON TEMOIN, PARCE QU'UNE GATE QU'AUCUN TEST N'A VUE
    #    CRIER EST DECORATIVE. La premiere version passait un `re.sub` inutile
    #    et je ne l'avais JAMAIS vue rougir : elle aurait pu etre verte pour la
    #    mauvaise raison. On l'exerce dans LES DEUX SENS.
    def sans_div(txt):
        return "/" not in txt and "%" not in txt
    ctrl(sans_div(isr), "⛔ AUCUNE division ni modulo dans `on_vsync`",
         "la conversion trames -> ms se fait COTE CONSOLE (D1)")
    ctrl(not sans_div(isr.replace("s->cur++", "s->cur += n / 2")
                      if "s->cur++" in isr else isr + "\nx = a / b;"),
         "…et ce controle SAIT crier (temoin negatif)",
         "une division injectee dans le corps est ATTRAPEE")
    # 🔴 UN SEUL ECRIVAIN : `s_bnc_serie` n'est ecrit QUE par l'ISR. Les trois
    #    fonctions de l'unite prennent un pointeur, donc on cherche les sites
    #    d'appel HORS `on_vsync`.
    hors_isr = nu.replace(isr, "")
    ecrivains = [l.strip() for l in hors_isr.splitlines()
                 if re.search(r'dn_serie_(raz|defaut|rompt)\s*\(', l)]
    ctrl(not ecrivains, "🔴 UN SEUL ECRIVAIN : `s_bnc_serie` n'est ecrit QUE "
         "par `on_vsync`", "aucun appel hors ISR (%d trouve(s))"
         % len(ecrivains))
    lectures = len(re.findall(r'out->ser_\w+\s*=', nu))
    ctrl(lectures == 8,
         "les 8 champs de serie sont copies DANS la boucle gardee",
         "%d affectations `out->ser_*` dans `dn_measure_bounce_get()`"
         % lectures)

    for d in reb._tmp:
        shutil.rmtree(d, ignore_errors=True)
    print("\n" + "=" * 78)
    print("BILAN : %d OK / %d KO" % (ok_total[0], ko_total[0]))
    print("=" * 78)
    return 1 if ko_total[0] else 0


if __name__ == "__main__":
    sys.exit(main())
