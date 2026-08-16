/*
 * DeskNode — le tactile : Goodix GT911 sur le bus I²C unique de la carte.
 *
 * ── CE QUE CE MODULE POSSÈDE, ET CE QU'IL EMPRUNTE ───────────────────────────
 * Il n'ouvre AUCUN bus. Le maître I²C et le TCA9554 appartiennent à
 * `dn_display` ; ce module leur demande leurs handles
 * (`dn_display_i2c_bus()` / `dn_display_tp_reset()`). Un second
 * `i2c_new_master_bus()` sur I2C_NUM_0 échouerait — le port est déjà pris.
 *
 * ── LES QUATRE CHOSES QU'IL FAUT SAVOIR AVANT DE LIRE LE .c ──────────────────
 *
 * 1. LE DRIVER NE FAIT PAS SON RESET. TP_RST est derrière l'expander, donc on
 *    passe `rst_gpio_num = -1` à `esp_lcd_touch_new_i2c_gt911()`. Avec -1, le
 *    composant SAUTE toute sa branche de reset (esp_lcd_touch_gt911.c:108-149),
 *    c'est-à-dire aussi la sélection d'adresse. La séquence est jouée ici, AVANT
 *    le `new` (cas documenté esp-bsp #130).
 *
 * 2. L'ADRESSE N'EST PAS UNE CONSTANTE, C'EST UN RÉSULTAT. Le GT911 échantillonne
 *    INT au relâchement de RST : bas => 0x5D, haut => 0x14. `dn_touch_addr()`
 *    rend celle à laquelle il a RÉPONDU, pas celle qu'on espérait.
 *
 * 3. 🔴 LE PROBE AVANT LE RESET RÉPOND DÉJÀ — MESURÉ LE 2026-08-16 SUR CETTE
 *    CARTE. Cet en-tête enseignait l'inverse (« un probe avant le reset ne voit
 *    rien, c'est le témoin négatif attendu »), repris de la story, et le
 *    livrable de dn1-4 l'a RÉFUTÉ dans le même commit : le GT911 répond à 0x5D
 *    avant toute intervention. TP_RST n'est donc pas maintenu bas quand
 *    l'expander le laisse en entrée haute impédance — le contrôleur sort de
 *    reset seul à la mise sous tension. Le « témoin négatif » annoncé n'en est
 *    pas un, et un probe qui répond avant la séquence n'est PAS une anomalie.
 *    La séquence reste indispensable, mais pour rendre l'adresse
 *    DÉTERMINISTE — pas pour réveiller le contrôleur. Les deux probes
 *    (avant/après) sont conservés et publiés par la console : c'est leur ÉCART
 *    qui informe, pas l'échec du premier. (Cette correction est un patch de la
 *    revue dn1-4 : l'ancienne phrase survivait dans les deux fichiers que ce
 *    module dit de lire en premier.)
 *
 * 4. LE MODE EVENT EST MUET EN SILENCE quand l'INT ne bat pas. C'est la classe de
 *    défaut que ce dépôt traque : rien ne plante, rien ne se loggue, le tactile
 *    est simplement mort. D'où `dn_touch_irq_count()` (témoin actif, qui compte
 *    DANS LES DEUX MODES) et `dn_touch_int_scan()` (témoin physique, qui
 *    échantillonne la broche sans rien supposer du driver).
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "esp_err.h"
#include "esp_lcd_touch.h"
#include "lvgl.h"

/*
 * Mode de lecture de l'indev LVGL. Réglable À CHAUD, et c'est délibéré :
 * l'arbitrage IRQ/polling d'AC2 doit se jouer sans reflasher, donc sans ajouter
 * le binaire comme deuxième variable (même discipline que `set core` en dn1-3).
 *
 *   EVENT : `LV_INDEV_MODE_EVENT` — le GT911 n'est lu QUE sur front INT.
 *   POLL  : `LV_INDEV_MODE_TIMER` — lu à chaque cycle LVGL (~33 ms), quoi que
 *           fasse l'INT. C'est le repli honorable : il coûte une transaction I²C
 *           par cycle et ne peut PAS être muet.
 *
 * ⚠️ Dans les deux modes l'ISR reste posée et le compteur d'IRQ continue de
 *    tourner : le témoin ne s'éteint pas quand on change de mode, sinon
 *    « le polling marche » ne dirait rien sur l'INT.
 */
typedef enum {
    DN_TOUCH_MODE_EVENT = 0,
    DN_TOUCH_MODE_POLL,
    DN_TOUCH_MODE_COUNT,
} dn_touch_mode_t;

const char *dn_touch_mode_name(dn_touch_mode_t m);
bool dn_touch_mode_from_name(const char *nom, dn_touch_mode_t *out);

/* Ce que le GT911 dit de LUI-MÊME, lu au bring-up (registres 0x8140 et
 * 0x8047-0x804D). Aucun de ces champs n'est écrit : ⛔ on LIT la config du
 * GT911, on ne la flashe pas (sa NVM a un nombre d'écritures limité, et une
 * config ratée transforme la dalle tactile en presse-papier). */
typedef struct {
    char product_id[5]; /* "911" + terminateur, tel que lu */
    uint16_t fw_version;
    uint8_t cfg_version; /* 0x8047 */
    uint16_t x_res;      /* 0x8048-0x8049, little endian */
    uint16_t y_res;      /* 0x804A-0x804B */
    uint8_t touch_max;   /* 0x804C bits 0-3 */
    uint8_t trig_mode;   /* 0x804D bits 0-1 */
    bool lue;            /* false si la lecture a échoué : les champs sont alors nuls */
} dn_touch_cfg_t;

/* Compteurs — 32 bits, même raison qu'en dn_ui.h : l'écrivain est l'ISR ou la
 * tâche LVGL, le lecteur est le REPL, et l'atomicité 64 bits inter-cœurs
 * n'existe pas sur Xtensa. Chaque champ pris isolément est juste ; l'ensemble
 * n'est pas cohérent à un événement près. */
typedef struct {
    uint32_t irq;       /* fronts INT vus par l'ISR */
    uint32_t lectures;  /* appels au read de l'indev (le coût du polling est là) */
    uint32_t appuis;    /* transitions relâché -> appuyé */
    uint32_t relaches;  /* transitions appuyé -> relâché */
    uint32_t x;         /* dernier point remonté, APRÈS swap/mirror */
    uint32_t y;
    uint32_t brut_x;    /* le même point AVANT nos transformations */
    uint32_t brut_y;
    bool appuye;        /* état courant */
} dn_touch_stats_t;

/*
 * Bring-up complet : probe témoin -> reset via expander (INT tenu bas) -> probe
 * -> création du driver -> lecture de la config.
 *
 * ⚠️ N'EST PAS FATAL. Un échec rend le code d'erreur et laisse le firmware
 *    vivre sans tactile : un écran qui s'affiche et ne répond pas au doigt est
 *    diagnosticable, un firmware qui refuse de démarrer ne l'est pas. La console
 *    dit alors POURQUOI (`touch`).
 */
esp_err_t dn_touch_init(void);

/*
 * Branche l'indev LVGL sur l'afficheur. À appeler APRÈS `dn_ui_init()` : il faut
 * un `lv_display_t` vivant. Séparé de `dn_touch_init()` parce que le bring-up
 * matériel a un sens sans LVGL (probe, adresse, INT) — et que l'ordre inverse
 * ferait dépendre le diagnostic du tactile de la bonne santé de l'UI.
 */
esp_err_t dn_touch_attach_lvgl(lv_display_t *disp);

bool dn_touch_ready(void);

/* Adresse à laquelle le GT911 a RÉPONDU (0 s'il n'a jamais répondu). */
uint8_t dn_touch_addr(void);
/* Les deux témoins du probe, tels quels. ⚠️ L'échec du premier n'est PAS attendu
 * sur cette carte — voir le point 3 de l'en-tête. */
esp_err_t dn_touch_probe_avant(void);
esp_err_t dn_touch_probe_apres(void);
/* Adresse visée par la séquence, pour confronter l'intention au résultat. */
uint8_t dn_touch_addr_visee(void);
/* Adresse vue AVANT notre séquence (0 = muet). ⚠️ MESURÉ le 2026-08-16 : sur
 * cette carte elle n'est PAS nulle — le GT911 répond déjà au boot, ce que la
 * story attendait le contraire. Voir le commentaire dans dn_touch_init(). */
uint8_t dn_touch_addr_avant(void);

void dn_touch_get_cfg(dn_touch_cfg_t *out);
void dn_touch_get_stats(dn_touch_stats_t *out);
void dn_touch_reset_stats(void);
/* Transactions I²C ratées. Non fatales par construction (voir dn_touch_read) :
 * un bus partagé par cinq composants a le droit de rater, le firmware n'a pas le
 * droit d'en mourir. Non nul = le premier chiffre à regarder. */
uint32_t dn_touch_err_i2c(void);

/* Délais de la séquence de reset, pour rejouer autre chose que les 150/50 ms de
 * la démo Waveshare sans reflasher. Ne survivent pas au reboot (pas de NVS) :
 * c'est un réglage de campagne, pas une config.
 * Console : `touch delais <bas> <haut>`, puis `touch addr` pour REJOUER la
 * séquence avec les nouvelles valeurs — les poser ne les applique pas.
 * ⚠️ Cette fonction n'a longtemps eu AUCUN appelant : trois commentaires
 * annonçaient `touch reset <bas> <haut>`, qui remettait en fait les compteurs à
 * zéro en ignorant ses arguments. Branchée par la revue dn1-4. */
esp_err_t dn_touch_set_delais(int bas_ms, int haut_ms);
void dn_touch_get_delais(int *bas_ms, int *haut_ms);

/* Nom lisible du mode de déclenchement de l'INT (registre 0x804D bits 1-0).
 * SOURCE UNIQUE : la console réécrivait cette table à la main. */
const char *dn_touch_trig_name(uint8_t m);

/*
 * ── LA PREUVE CAUSALE QUE GPIO16 EST BIEN TP_INT (AC1) ───────────────────────
 *
 * Rejoue LA SEULE SÉQUENCE DE RESET (le driver n'est pas recréé), en tenant INT
 * au niveau demandé pendant le relâchement, puis probe les DEUX adresses.
 *
 * C'est un instrument de causalité, pas d'observation : si mettre GPIO16 à 1
 * fait apparaître le GT911 à 0x14 et le remettre à 0 le ramène à 0x5D, alors
 * GPIO16 EST la broche que le GT911 échantillonne. Aucune autre broche du SoC ne
 * peut produire cet effet. Un simple « j'ai vu un front » ne prouverait que
 * l'existence d'un signal, pas son identité.
 *
 * ⚠️ PENDANT L'ESSAI LE CONTRÔLEUR EST EN RESET : les lectures de l'indev
 *    échouent, et `err_i2c` monte. C'est attendu, et c'est un témoin de plus.
 * ⚠️ L'appelant DOIT terminer par un essai à `int_haut = false` pour rendre au
 *    GT911 l'adresse que le driver connaît. La console le fait ; un appel nu ne
 *    le fait pas.
 *
 * `trouvee` reçoit l'adresse à laquelle il a répondu (0 = aucune).
 */
esp_err_t dn_touch_essai_adresse(bool int_haut, uint8_t *trouvee);

dn_touch_mode_t dn_touch_get_mode(void);
esp_err_t dn_touch_set_mode(dn_touch_mode_t m);

/*
 * Orientation — les quatre champs se règlent ENSEMBLE ou pas du tout :
 * `esp_lcd_touch` applique mirror_x/mirror_y en logiciel avec x_max/y_max comme
 * axe de symétrie (`x = x_max - x`). Changer un miroir sans son max donne des
 * coordonnées repliées sur le mauvais bord — un défaut qui ressemble à une
 * dalle mal calibrée.
 * Réglables à chaud pour la campagne des 4 coins (AC2).
 */
esp_err_t dn_touch_set_axes(bool swap_xy, bool mirror_x, bool mirror_y);
void dn_touch_get_axes(bool *swap_xy, bool *mirror_x, bool *mirror_y);

/*
 * ── LES DEUX TÉMOINS DE L'INT ────────────────────────────────────────────────
 * `dn_touch_int_level()` : niveau instantané de la broche.
 * `dn_touch_int_scan()`  : échantillonne la broche pendant `duree_ms` et compte
 *   les TRANSITIONS. C'est le témoin PHYSIQUE de TP_INT : il ne passe ni par le
 *   driver, ni par l'ISR, ni par LVGL. Si le compteur d'IRQ reste à zéro pendant
 *   qu'un doigt touche la dalle, c'est lui qui dit si la broche bat quand même
 *   (⇒ ISR mal armée) ou pas du tout (⇒ mauvais GPIO, ou INT non câblé).
 * ⚠️ Il MONOPOLISE le cœur appelant pendant `duree_ms` : c'est un instrument de
 *    campagne, pas un service de fond.
 */
int dn_touch_int_level(void);
uint32_t dn_touch_int_scan(int duree_ms, int *niveau_final);

/*
 * Vide l'état du contrôleur (registre de points) et l'état d'appui local.
 * Appelé à la reprise de LVGL : un doigt posé pendant la pause ne doit pas
 * produire un clic fantôme au retour.
 */
void dn_touch_drain(void);

/*
 * ── LA LATENCE (AC5) ─────────────────────────────────────────────────────────
 * Le chronomètre part quand l'indev remonte un APPUI (donc après la lecture I²C)
 * et s'arrête quand le cycle de rafraîchissement qui suit le changement d'écran
 * est FLUSHÉ. `dn_touch_latence_arm()` est appelé par la navigation, pas par le
 * tactile : c'est le changement d'écran qui est chronométré, pas le toucher.
 *
 * ⚠️ CE QUE CETTE MESURE NE COUVRE PAS, et qui est déclaré plutôt que fabriqué :
 *    le temps entre le contact PHYSIQUE du doigt et la lecture (jusqu'à ~33 ms
 *    en polling, borné par l'INT en mode EVENT), et le temps entre la fin du
 *    flush et le photon (jusqu'à une trame, 26,7 ms).
 */
/*
 * `t0_us` = instant d'origine (`esp_timer_get_time()`), ou 0 pour « maintenant ».
 *
 * ⚠️ L'ARMEMENT A LIEU APRÈS LA CONSTRUCTION DE LA NOUVELLE VUE, avec l'instant
 *    du clic comme origine — et pas au clic lui-même. Armer au clic laisserait
 *    le chronomètre en vol pendant le cycle LVGL en cours (celui du label 1 Hz,
 *    par exemple) : le `flush_is_last` de CE cycle-là l'arrêterait, et la
 *    « latence tap -> détail » publiée serait en réalité la fin d'un redessin
 *    sans rapport. Le chiffre serait plausible, et faux.
 */
void dn_touch_latence_arm(int64_t t0_us);
void dn_touch_latence_stop(void);
/* Désarme sans produire d'échantillon (appelée par `dn_ui_pause`) : sinon la
 * durée de la pause entrait dans le min/moy/max publié par AC5. */
void dn_touch_latence_desarm(void);
typedef struct {
    uint32_t n;
    uint32_t min_us;
    uint32_t max_us;
    uint32_t total_us; /* pour la moyenne ; reboucle à ~4295 s cumulées */
    uint32_t dernier_us;
    /* Échantillons ABANDONNÉS parce que l'instant d'armement était postérieur au
     * flush (dt < 0). Ils étaient jetés EN SILENCE : `n` divergeait du nombre
     * réel de transitions et la moyenne se calculait sur un échantillon biaisé
     * vers le bas, sans que rien ne le dise. Non nul ⇒ campagne invalide. */
    uint32_t rejets;
} dn_touch_latence_t;
void dn_touch_get_latence(dn_touch_latence_t *out);
void dn_touch_reset_latence(void);
