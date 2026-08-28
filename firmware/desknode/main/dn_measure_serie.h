#pragma once
/*
 * dn4-12 — LA MACHINE A ETATS DE SERIE CONSECUTIVE.
 *
 * ══════════════════════════════════════════════════════════════════════════
 *  CE QU'ELLE EXISTE POUR DIRE, ET QUE RIEN NE DISAIT
 * ══════════════════════════════════════════════════════════════════════════
 *
 * Le compteur de dn4-10 compte des TRAMES au-dessus d'un seuil ; il ne compte
 * JAMAIS leur CONSECUTIVITE. Il ne peut donc ni confirmer ni infirmer le
 * constat de l'owner du 2026-08-23 : « parfois ca reste dans un etat glisse
 * […] ensuite ca reglisse ». Le driver Espressif nomme ce cas « permanent
 * desync » et dit que RESTART_IN_VSYNC existe pour l'empecher
 * (esp_lcd_panel_rgb.c:1142-1148) ; nous avons desactive ce flag le 2026-08-23
 * (`4734d07`) parce qu'il FABRIQUAIT le glissement periodique. Le permanent
 * desync n'a donc plus AUCUNE parade automatique — et rien ne le mesure.
 *
 * ⇒ Cette unite mesure LA PLUS LONGUE SERIE DE TRAMES CONSECUTIVES NON SAINES.
 *
 * ══════════════════════════════════════════════════════════════════════════
 *  🔴 D1 — ELLE COMPTE DES TRAMES, ⛔ PAS DES MICROSECONDES
 * ══════════════════════════════════════════════════════════════════════════
 *
 * `esp_timer` reboucle a 2^32 us = 71,58 min — le defaut que dn4-5/AC1.2 vient
 * de fermer sur `fenetre_ms`. Un COMPTE DE TRAMES, lui, ne reboucle qu'a 2^32
 * trames, soit ~3,6 ans a 37,40 Hz. La grandeur survit donc a une nuit et a une
 * semaine PAR CONSTRUCTION, ⛔ pas par precaution.
 * La conversion en millisecondes se fait COTE CONSOLE, depuis `periode_ns`
 * (26 737 500 ns, EXACTE) — ⛔ jamais ici, et jamais dans l'ISR.
 *
 * ══════════════════════════════════════════════════════════════════════════
 *  🔴 POURQUOI UNE UNITE PURE, ET CE QUE CE CHOIX COUTE (dn4-12 / AC5.4)
 * ══════════════════════════════════════════════════════════════════════════
 *
 * Le dev tranche, et il ECRIT lequel et pourquoi. C'est l'UNITE PURE, pour
 * TROIS raisons dont la troisieme est decisive :
 *
 *  1. ⛔ AUCUN APPEL DE PLUS, AUCUN DEPLACEMENT DE CODE. Tout est
 *     `static inline` et n'inclut que <stdint.h> : le compilateur inline dans
 *     `on_vsync`. C'est ce qui protege la MARGE DE FAMINE DMA de §26 — dont le
 *     mecanisme mesure est le PLACEMENT du code, ⛔ pas son volume (1 236 o de
 *     `.text` MORT rendent une image plus grosse ET la fenetre la plus propre
 *     de toute la campagne).
 *
 *  2. La logique est isolee, donc EPROUVABLE EN PROPRE, cas par cas.
 *
 *  3. 🎯 ET C'EST LA RAISON QUI TRANCHE : ECRITE DANS `on_vsync`, LA CLASSE F
 *     (`ph_dechire`) SERAIT INEPROUVABLE SUR L'HOTE. Son declencheur est que
 *     `s_bnc_wraps` change ENTRE les deux lectures `w` et `w2`, a l'interieur
 *     de l'ISR — et il n'existe AUCUN point d'entree de coquille entre ces deux
 *     lignes (`esp_timer_get_time()` est appele bien avant). Une gate de bout
 *     en bout ne peut donc PAS la declencher. C'est exactement le sort de
 *     `ph_futur`, declare « JAMAIS VU BOUGER » dans dn4-10. L'unite pure rend
 *     E, F et G directement exercables — AC5.5(e) l'EXIGE.
 *
 * ⛔ CE QUE CE CHOIX COUTE, ET C'EST DECLARE : `dn_measure.c` acquiert un
 *    `#include "dn_measure_serie.h"`. `verif_rebouclage_dn45.py` compile
 *    `dn_measure.c` SUR L'HOTE ; un include local qu'elle ne fournit ni en
 *    copie ni en coquille TUE la gate a la COMPILATION — c'est l'incident
 *    `dn_bootcfg.h` deja paye, et le piege est toujours arme. ⇒ CET EN-TETE EST
 *    AJOUTE A `COPIES` DANS `verif_rebouclage_dn45.py`, DANS LE MEME GESTE.
 *
 * ══════════════════════════════════════════════════════════════════════════
 *  🔴 LA TABLE DES HUIT CLASSES DE TRAME, ET LE VERDICT DE CHACUNE
 * ══════════════════════════════════════════════════════════════════════════
 *
 *  Six classes de trame n'atteignent JAMAIS le site du deficit. Aucune source
 *  du depot ne les enumerait ensemble avant dn4-12. Le verdict est ecrit ICI
 *  (le code) ET dans la console (l'utilisateur ne doit pas avoir a lire le
 *  source pour savoir ce qui a ete compte).
 *
 *  | # | classe                   | condition dans on_vsync        | verdict          |
 *  |---|--------------------------|--------------------------------|------------------|
 *  | A | deficit franchi          | n==1, phase comptee, def > demi | 🔴 EN DEFAUT     |
 *  | B | saine                    | n==1, phase comptee, def <= demi| ✅ ROMPT         |
 *  | C | hors borne de sanite     | n==1, ph >= 2 periodes          | 🔴 EN DEFAUT (D2)|
 *  | D | aucun enroulement        | n==0                            | 🔴 EN DEFAUT     |
 *  | E | horodatage POSTERIEUR    | (int32_t)(t_us - tw) < 0        | ⚠️ INDETERMINEE  |
 *  | F | paire (wraps,t_wrap) dechiree | w2 != w                    | ⚠️ INDETERMINEE  |
 *  | G | deux enroulements ou plus| n >= 2                          | ⚠️ INDETERMINEE  |
 *  | H | degrossissage            | ph_ecarte < DN_PHASE_DEGROSSI   | ⛔ HORS SUJET    |
 *
 *  LE MOTIF DE CHAQUE VERDICT — ⛔ IL EST ECRIT, PAS SUPPOSE :
 *
 *  • C (`ph_rejete`) COMPTE EN DEFAUT parce que le code l'ecrit lui-meme
 *    (dn_measure.c, borne de sanite) : « 🔴 LA BORNE DE SANITE ECARTE
 *    EXACTEMENT LE GLISSEMENT RECHERCHE ». Une serie qui se romprait dessus
 *    rendrait 0 PENDANT QUE L'ECRAN EST FIGE — l'exact inverse du livrable.
 *    C'est la DECISION D2, et c'est le piege central de cette story.
 *
 *  • D (`manques`) COMPTE EN DEFAUT parce que le temoin de reference du depot
 *    (`flash on` + bounce_px != 0, mesure du 2026-08-22) rend 1 037 TRAMES SANS
 *    ENROULEMENT SUR 1 041. Si `manques` rompait la serie, le temoin le plus
 *    violent du depot rendrait une plus longue serie de ~1 pendant que la dalle
 *    est detruite : l'instrument serait AVEUGLE EXACTEMENT LA OU IL DOIT HURLER.
 *
 *  • E / F / G ROMPENT parce qu'on NE SAIT PAS si la trame etait saine. Les
 *    faire continuer FABRIQUERAIT de la duree. Rompre SOUS-ESTIME — et un
 *    minorant tient A FORTIORI. ⚠️ Le prix est publie : `rompues_indet` compte
 *    les series qu'une indeterminee a coupees (AC1.4).
 *
 *  • H ne fait NI L'UN NI L'AUTRE : avant que `ph_ref_us` soit figee, AUCUN
 *    deficit n'est calculable. La trame n'est pas soumise a la machine.
 *
 * ⚠️ CE QUE LE DEV A TRANCHE ICI, PARCE QUE LA TABLE ET SON MOTIF NE DISENT PAS
 *    TOUT A FAIT LA MEME CHOSE — ET C'EST DECLARE, ⛔ PAS TU.
 *    AC1.3 motive H par « la serie ne commence qu'apres le degrossissage ».
 *    Pris a la lettre pour TOUTES les classes, cela armerait la machine
 *    seulement une fois `ph_ref_us` figee. ⛔ CE SERAIT FAUX, ET DANGEREUX :
 *    les classes C et D ne lisent NI la reference NI le seuil. Sous `flash on`,
 *    ou 1 037 trames sur 1 041 n'ont AUCUN enroulement, le degrossissage
 *    n'avance pas (il ne se nourrit que de trames a n==1) ⇒ la machine ne
 *    s'armerait JAMAIS ⇒ « plus longue serie = 0 » pendant que la dalle est
 *    detruite. C'est mot pour mot le mode de defaillance qu'AC1.9 declare comme
 *    « l'instrument est FAUX ».
 *    ⇒ LA TABLE D'AC1.2 FAIT AUTORITE : C et D comptent TOUJOURS. Seule la
 *      classe A exige le degrossissage — donc une serie faite de A ne peut pas
 *      commencer avant la 32e trame, ce qui est ce qu'AC1.3-H et AC5.5(f)
 *      eprouvent. La console le DIT.
 *
 * ══════════════════════════════════════════════════════════════════════════
 *  ⛔ CE QUE CETTE UNITE NE MESURE PAS, ET NE POURRA PAS MESURER
 * ══════════════════════════════════════════════════════════════════════════
 *
 *  • LE NOMBRE DE RELANCES REELLEMENT JOUEES PAR LE DRIVER EST INOBSERVABLE a
 *    RESTART_IN_VSYNC=n : il relance EN INTERNE sans passer par `need_restart`
 *    (esp_lcd_panel_rgb.c:1153-1163), donc `recal` compte 1 (l'amorcage) et
 *    rien d'autre (§20bis.8). ⇒ CONTRAINTE DE CONCEPTION : on mesure la
 *    PERSISTANCE DE L'ETAT, ⛔ JAMAIS L'ECHEC DE RELANCE.
 *  • Le plancher de l'instrument reste LA MICROSECONDE, soit 16 px a 16 MHz.
 *  • Un retard COMMUN aux deux ISR s'annule et reste invisible.
 *  • La plus longue serie est un MINORANT (E/F/G rompent).
 *
 * ══════════════════════════════════════════════════════════════════════════
 *  🔴 D5 — SURETE DE CONCURRENCE, ⛔ NON NEGOCIABLE
 * ══════════════════════════════════════════════════════════════════════════
 *
 *  UN SEUL ECRIVAIN : `on_vsync`. Les champs sont des `volatile uint32_t`
 *  (lecture atomique Xtensa sur un mot aligne), lus par la tache console via le
 *  seqlock COTE LECTEUR existant. ⛔ Aucun verrou, aucune section critique,
 *  aucun ESP_LOGx, aucune division, aucun appel, aucun acces `.rodata`.
 *  « On mesure une famine : on n'allait pas la fabriquer. »
 *
 *  ⛔ ET AUCUN PLAFOND (AC1.5, precedent dn4-13). `dn_hist_rattraper()`
 *  ecretait a 120 AVANT de compter : `ui off` de 10 min et de 1 h imprimaient
 *  EXACTEMENT LA MEME PHRASE. Ici la structure qui porte la serie est un
 *  COMPTEUR, pas un tampon : deux durees differentes rendent deux nombres
 *  differents, QUELLE QUE SOIT LEUR LONGUEUR.
 */

#include <stdint.h>

/* Les trois classes EN DEFAUT, pour la COMPOSITION de la serie (AC1.6) : un
 * lecteur doit pouvoir distinguer « la DMA a lu un tampon pas encore rempli 200
 * fois de suite » (A) de « la DMA n'a pas fini une seule trame pendant 200
 * trames » (D) — deux pathologies differentes, deux remedes differents.
 * ⛔ `#define` et non `static const` : constant-folded, donc AUCUN acces
 *    `.rodata` depuis l'ISR — la `.rodata` vit en flash, et l'ISR peut tourner
 *    cache coupe pendant une ecriture flash. */
#define DN_SERIE_CL_A 0u /* deficit franchi   (ph_100pc) */
#define DN_SERIE_CL_C 1u /* hors borne sanite (ph_rejete) */
#define DN_SERIE_CL_D 2u /* aucun enroulement (manques)  */

/* ⚠️ CE N'EST PAS `dn_bounce_stats_t`, ET CA COMPTE. La structure publiee est
 *    reparsee A LA REGEX par `verif_rebouclage_dn45.py:321-339` et rebatie en
 *    ctypes : elle ne tolere QUE des scalaires de types deja mappes. Ici on est
 *    du cote de l'ETAT INTERNE, jamais publie tel quel — la copie vers
 *    `dn_bounce_stats_t` se fait champ par champ, en `uint32_t` plats. */
typedef struct {
    volatile uint32_t cur;       /* longueur de la serie EN COURS, en TRAMES */
    volatile uint32_t cur_a;     /* sa composition : classe A */
    volatile uint32_t cur_c;     /*                  classe C */
    volatile uint32_t cur_d;     /*                  classe D */
    volatile uint32_t cur_debut; /* index de trame depuis la RAZ ou elle a commence */
    volatile uint32_t max;       /* 🔴 LA PLUS LONGUE SERIE */
    volatile uint32_t max_a;
    volatile uint32_t max_c;
    volatile uint32_t max_d;
    volatile uint32_t max_debut;
    volatile uint32_t n;         /* nombre TOTAL de series (celle en cours comprise) */
    volatile uint32_t rompues;   /* series rompues par une trame INDETERMINEE */
} dn_serie_t;

/* ── LA RAZ ────────────────────────────────────────────────────────────────
 * ⛔ APPELEE DEPUIS LA BRANCHE RAZ DE L'ISR, jamais depuis la tache : la remise
 *    a zero est consommee PAR DRAPEAU, comme les 25 autres affectations de
 *    cette branche. AC1.7 exige que CHAQUE champ neuf y figure — un seul point
 *    d'entree qui les couvre tous rend l'oubli STRUCTURELLEMENT IMPOSSIBLE, et
 *    la gate le prouve champ par champ, rejouable 3 fois (AC5.5(i), mutant M4).
 * 🔴 « Un temoin se remet a zero, ou il n'est pas un temoin » (precedent
 *    `s_gardeh_cris`, qui faisait dire « ✅ elle a CRIE » a une garde muette). */
static inline void dn_serie_raz(dn_serie_t *s)
{
    s->cur = 0u;
    s->cur_a = 0u;
    s->cur_c = 0u;
    s->cur_d = 0u;
    s->cur_debut = 0u;
    s->max = 0u;
    s->max_a = 0u;
    s->max_c = 0u;
    s->max_d = 0u;
    s->max_debut = 0u;
    s->n = 0u;
    s->rompues = 0u;
}

/* ── UNE TRAME EN DEFAUT (classes A, C, D) ─────────────────────────────────
 * `idx` = index de la trame DEPUIS LA RAZ (⛔ pas un horodatage — D1).
 *
 * 🔴 LE MAXIMUM EST MIS A JOUR ICI, ⛔ PAS A LA FERMETURE DE LA SERIE. Sans ca,
 *    une serie ENCORE EN COURS a l'instant de la lecture ne serait pas dans le
 *    maximum — et c'est le cas le plus interessant de tous : un permanent
 *    desync EN TRAIN DE DURER. AC5.5(h) l'eprouve. */
static inline void dn_serie_defaut(dn_serie_t *s, uint32_t classe, uint32_t idx)
{
    if (s->cur == 0u) {
        s->cur_debut = idx;
        s->n++;
    }
    s->cur++;
    if (classe == DN_SERIE_CL_A) {
        s->cur_a++;
    } else if (classe == DN_SERIE_CL_C) {
        s->cur_c++;
    } else {
        s->cur_d++;
    }
    /* ⛔ LE COMPTAGE VIENT AVANT TOUT ECRETAGE, ET IL N'Y A PAS D'ECRETAGE
     *    (AC1.5). `dn_hist_rattraper()` posait `if (manques > 120) manques =
     *    120;` AVANT `s_rattr_trous += manques` : deux coupures d'un facteur 30
     *    imprimaient la meme phrase. Ici rien n'est jete, rien n'est borne. */
    if (s->cur > s->max) {
        s->max = s->cur;
        s->max_a = s->cur_a;
        s->max_c = s->cur_c;
        s->max_d = s->cur_d;
        s->max_debut = s->cur_debut;
    }
}

/* ── UNE TRAME QUI ROMPT LA SERIE (classe B saine, classes E/F/G indeterminees)
 * `indeterminee` != 0 ⇒ on COMPTE la rupture : une serie vraie a pu etre
 * COUPEE EN DEUX, et le lecteur doit pouvoir borner sa confiance (AC1.4).
 * ⛔ Ce nombre NE SE SOUSTRAIT PAS et NE SE RECOMPOSE PAS.
 *
 * ⚠️ On ne compte la rupture QUE si une serie courait : une indeterminee qui
 *    tombe alors que `cur == 0` ne coupe rien, et la compter gonflerait la
 *    reserve pour rien. */
static inline void dn_serie_rompt(dn_serie_t *s, uint32_t indeterminee)
{
    if (s->cur != 0u) {
        if (indeterminee) {
            s->rompues++;
        }
        s->cur = 0u;
        s->cur_a = 0u;
        s->cur_c = 0u;
        s->cur_d = 0u;
    }
}
