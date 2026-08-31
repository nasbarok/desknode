/*
 * dn_capteurs — lecture du BME680 sur le bus I²C partagé (dn2-1, P4).
 * Le POURQUOI de chaque choix est dans dn_capteurs.h ; ici, le COMMENT.
 *
 * ⚠️ Ce fichier porte 12 correctifs de la revue de code adversariale du
 *    2026-08-17 (3 couches). Chacun est signalé « CR 2026-08-17 » à l'endroit
 *    où il agit, avec le symptôme qui l'a fait trouver — la règle du dépôt étant
 *    que les erreurs réfutées restent écrites avec leur réfutation.
 *
 * ─── dn4-5 / AC6 : L'AFFICHAGE A UN CYCLE DE RETARD, ET C'EST ASSUMÉ ────────
 *
 * 🔴 LE FAIT, MESURÉ : la boucle « data ready » du composant SORT DÈS LA
 *    PREMIÈRE ITÉRATION, alors que la conversion 8x/8x/1x demande **~41 ms** ;
 *    le cycle, lui, se mesure à **25-26 ms**. ⇒ **chaque cycle DÉCLENCHE une
 *    conversion et LIT LA PRÉCÉDENTE.** L'écran montre donc l'air d'il y a
 *    `DN_CAPT_PERIODE_MS`, soit **5 s**.
 *
 * ✅ TÉMOIN POSITIF DÉJÀ MESURÉ : `capteurs gaz on` ajoute **300 ms** de chauffe
 *    et **le cycle reste à 26 ms** pendant que la température dérive de 26,0 à
 *    26,2 °C. Si le cycle attendait la conversion, il aurait sauté à ~341 ms.
 *
 * ⛔ ET LE CORRECTIF N'EST **PAS** D'ATTENDRE LA CONVERSION. Attendre coûterait
 *    **41 ms bloqués** par cycle, **341 ms** gaz allumé — sur une tâche qui
 *    partage le bus I²C avec l'horloge et le tactile. Le correctif est de
 *    **déclencher au cycle N et lire au cycle N+1 EN CONNAISSANCE DE CAUSE**, et
 *    de LE DIRE. C'est ce que fait la ligne `DN_CAPT_RETARD_TXT` ci-dessous.
 *    ⚠️ *« Anodin à 5 s, PAS anodin pour une story qui touche à la cadence. »*
 *
 * ⚠️ LA PHRASE EST DÉFINIE **UNE SEULE FOIS** (`DN_CAPT_RETARD_TXT`) et le
 *    docblock la cite. Deux vérités qui divergent en silence, c'est le défaut
 *    que ce dépôt traque depuis `dn4-8` — une gate
 *    (`tools/verif_bme680_retard_dn45.py`) refuse qu'elles s'écartent.
 */
#include "dn_capteurs.h"
#include "dn_env.h"

#include <math.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#include "bme680.h"
#include "dn_display.h"
#include "dn_pins.h"
#include "dn_ui.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "dn_capt";

/*
 * dn4-5 / AC6.1 — LA PHRASE, DÉFINIE ICI ET NULLE PART AILLEURS.
 * ⛔ Ne pas la recopier : le docblock de ce fichier la CITE, et une gate vérifie
 *    que les deux ne s'écartent pas.
 */
#define DN_CAPT_RETARD_TXT                                                    \
    "l'affichage a UN CYCLE DE RETARD (5 s) sur le capteur : la boucle "      \
    "« data ready » sort a la 1re iteration alors que la conversion 8x/8x/1x " \
    "demande ~41 ms, et le cycle mesure 25-26 ms. Chaque cycle DECLENCHE une " \
    "conversion et LIT LA PRECEDENTE. C'est ASSUME, pas subi : attendre "     \
    "couterait 41 ms bloques par cycle (341 ms gaz allume) sur la tache qui " \
    "partage le bus I2C."

/* ⚠️ portMUX et non un mutex : ces champs sont lus par la console (cœur 0) et
 * écrits par la tâche de lecture. Les int64 sont DÉCHIRABLES sur Xtensa (deux
 * stockages 32 bits) — `volatile` n'y change rien. Leçon du ledger dn1-2.
 * 🔴 CR 2026-08-17 : l'injecteur de fautes et la demande de gaz ÉCHAPPAIENT à ce
 * verrou — les trois seuls champs partagés du fichier à le faire, dans un fichier
 * qui s'ouvre sur un commentaire expliquant pourquoi il ne faut pas. `xTaskCreate`
 * ne pose aucune affinité de cœur : les deux tâches peuvent tourner en parallèle,
 * et `--s_faute_restants` est une lecture-modification-écriture. Ils y sont
 * rentrés. */
static portMUX_TYPE s_mux = portMUX_INITIALIZER_UNLOCKED;

const char *dn_capt_retard_txt(void) { return DN_CAPT_RETARD_TXT; }

static bme680_handle_t s_dev;
static uint8_t s_chip_id;
static uint8_t s_variant;
/* 🔴 dn4-2 (2026-08-20) — DEUX DIAGNOSTICS OPPOSES VIVAIENT DANS LA MEME VALEUR.
 * `relever_identite()` ecrivait `s_chip_id = 0` quand la LECTURE ECHOUAIT, soit
 * exactement ce qu'aurait rendu un capteur ayant REPONDU 0x00. Le message publie
 * affirmait alors « chip id 0x00 » — c'est-a-dire une AFFIRMATION SUR LE CAPTEUR,
 * alors que le capteur n'avait rien dit. Mesure du 2026-08-20 : le bandeau
 * annoncait « identite INATTENDUE : chip id 0x00 » pendant que `i2c lire 77 D0`
 * rendait `61` quelques secondes plus tard, scan a 8/8. ⇒ C'est la faute que ce
 * depot a DEJA corrigee deux fois (tronquee/trop_longue en dn2-2, puis
 * err_i2c/err_donnee DANS CE FICHIER au CR du 2026-08-17) — appliquee aux
 * compteurs de REGIME, jamais a l'identification au BOOT. */
static bool s_id_lue; /* la LECTURE a abouti (⛔ ne dit rien de la VALEUR) */
/* 🔴 CR dn4-2 (2026-08-20) — TROIS ETATS, PAS DEUX, ET LE 3e MANQUAIT.
 * `s_id_lue` seul ne distinguait pas « la transaction a ECHOUE » de « aucune
 * lecture n'a ete TENTEE » (bus absent, ou `add_device` refuse). `capteurs`
 * affirmait donc « la transaction I2C a ECHOUE » sur une carte ou aucune
 * transaction n'avait eu lieu — le meme genre d'affirmation-sur-rien que le
 * correctif d'origine venait de retirer du bandeau. */
static bool s_id_tentee; /* une lecture a ete TENTEE dans le dernier releve */
/* 🔴 CR dn4-2 — LE VARIANT GARDAIT LE DEFAUT QUE LE CHIP ID VENAIT DE PERDRE.
 * `s_variant = 0` sur echec, alors que 0x00 est la valeur LEGITIME du BME680
 * (0x01 = BME688). Un variant rate faisait donc imprimer « variant 0x00 =>
 * BME680 » avec aplomb sur un octet jamais recu — et un BME688 au variant
 * instable passait silencieusement pour un BME680. Deux lignes sous le
 * correctif, dans la meme fonction. */
static bool s_variant_lu;
/* Signature du dernier verdict d'identite PUBLIE, pour ne le republier que
 * quand il CHANGE : la reprise tourne toutes les 60 s et le REPL EST le
 * transport PC. 0 = rien publie encore. */
static uint16_t s_id_sig_publiee;
/* Le 3e message de la REPRISE ne se dit qu'une fois : la reprise tourne
 * toutes les 60 s et un echec d'ouverture permanent noierait le transport. */
static bool s_reprise_echec_dit;
static bool s_gaz = DN_CAPT_GAZ_DEFAUT;
/* 🔴 « le chauffeur tourne mais la mesure n'est pas encore utilisable » — un
 * TROISIÈME état, ajouté en revue de code le 2026-08-20. Sans lui, `capteurs`
 * affirmait « chauffeur COUPE (defaut) » pour toute valeur absente, y compris
 * juste après un `capteurs gaz on` : l'inverse de ce que l'opérateur venait de
 * commander, et rien pour distinguer les deux. */
static bool s_gaz_attente;
static bool s_gaz_demande = DN_CAPT_GAZ_DEFAUT;

static int s_temp_dx = DN_CAPT_DX_ABSENT; /* dixièmes de °C */
static int s_hum_dx = DN_CAPT_DX_ABSENT;  /* dixièmes de %RH */
/* 🔴 dn4-3 : mesurée depuis dn2-1, JETÉE jusqu'ici. Voir dn_capteurs.h. */
static int s_pression_dx = DN_CAPT_DX_ABSENT;      /* dixièmes de hPa, CONVERTIS */
static int s_pression_brut_dx = DN_CAPT_DX_ABSENT; /* dixièmes de l'unité DU DRIVER */
static dn_capt_p_unite_t s_pression_unite = DN_CAPT_P_UNITE_INCONNUE;
static bool s_pression_unite_dite;
/* 🔴 Le verdict d'unité ABERRANTE se journalise UNE fois mais ⛔ NE VERROUILLE
 * PAS `s_pression_unite_dite` — sinon une première lecture aberrante à froid
 * empêchait à vie l'annonce de l'unité réelle (revue de code 2026-08-20). */
static bool s_pression_aberrante_dite;
/* 🔴 dn4-3 : la resistance MOX brute, en ohms. ⛔ PAS un indice de qualite
 * d'air — voir le docblock de `dn_capt_gaz_ohms()`. */
static int s_gaz_ohms = DN_CAPT_DX_ABSENT;
static int s_iaq_brut = DN_CAPT_DX_ABSENT;
static int64_t s_lu_us = -1;
static int64_t s_cadence_us = -1; /* écart mesuré entre les deux dernières */
static int64_t s_cycle_us = -1;
static dn_capt_compteurs_t s_cnt;
static bool s_a_deja_lu; /* au moins une valeur valide publiée depuis le boot */
static bool s_degrade;   /* on ne publie plus de valeur valide */
/* Les trois registres de config RELUS dans le capteur, et ce que l'init y a posé.
 * L'écart entre les deux est le seul moyen de voir qu'il a redémarré. */
static uint8_t s_reg_hum, s_reg_meas, s_reg_cfg;
static uint8_t s_att_hum, s_att_meas, s_att_cfg;
static bool s_conforme;
/* 🔴 CR 2026-08-17 — « NON CONFORME » ≠ « pas de verdict ». Voir dn_capteurs.h. */
static bool s_conf_dispo;
static i2c_master_dev_handle_t s_brut; /* accès registre nu, hors driver */
/*
 * 🔴 LE SUIVI DE REPRISE NE DOIT PAS DÉPENDRE DE L'HORODATAGE — correctif du
 * 2026-08-17, trouvé en jouant l'AC7 sur la carte.
 *
 * La première version déduisait « on était muet » de `dn_capt_etat()`, qui se
 * calcule à partir de `s_lu_us`. Or la réparation d'un capteur qui a perdu sa
 * config EFFACE `s_lu_us` (c'est ce qui fait passer les cases à « -- »). L'état
 * tombait donc à JAMAIS et non à MUET, et la reprise n'était JAMAIS comptée :
 * **le code de réparation aveuglait le compteur censé prouver qu'il répare.**
 * Constat qui l'a révélé : reprise vue à l'écran, `reprises : 0` au compteur.
 *
 * Deux drapeaux indépendants, écrits uniquement par la tâche :
 */
static dn_capt_faute_t s_faute;
static int s_faute_restants;

/*
 * 🔴 CR 2026-08-17 — LA BOUCLE DE RÉPARATION ÉTAIT SANS BORNE, ET ELLE FUYAIT.
 *
 * `bme680_init()` du composant retenu alloue ses coefficients d'étalonnage
 * (`calloc`, bme680.c:969) puis, sur QUATRE chemins d'échec ultérieurs, libère
 * le handle **sans libérer ces coefficients** (bme680.c:1007-1011). La fuite est
 * en amont — mais c'est NOTRE boucle qui la transformait en fuite continue :
 * `config_verifier_et_reparer()` rappelait `bme680_init()` toutes les 5 s, sans
 * compteur d'échecs, sans espacement, sans arrêt. Un capteur bloqué en état
 * fantôme une nuit entière = des milliers d'allocations perdues contre 109 Ko de
 * RAM interne libre, et la panne serait sortie ailleurs, sans rapport visible.
 * ⇒ Trois échecs consécutifs suffisent à conclure : on cesse d'insister et on
 *   repasse sur la cadence lente de re-tentative. Entrée au ledger pour le
 *   signalement amont (k0i05/esp_bme680 1.2.7).
 */
#define DN_CAPT_RECONF_ECHECS_MAX 3
static int s_reconf_echecs;

static void invalider_identite(void); /* def. plus bas — voir CR du 2026-08-24 */

/*
 * 🔴 CR 2026-08-17 — UNE INIT RATÉE ÉTAIT DÉFINITIVE, ET C'EST LE CAS NORMAL.
 *
 * `bme680_init()` n'était appelée qu'une fois, depuis `dn_capteurs_init()`. Si la
 * carte démarrait pendant que le contact était momentanément ouvert — le cas que
 * §13.5/§13.6 bis documentent comme NORMAL sur ce montage, et qui a coûté la
 * moitié de la séance — le module restait à `JAMAIS` **pour toujours**, quel que
 * soit le nombre de re-branchements : la garde de config, la reconfiguration et
 * `reprises` sont tous en aval d'un handle que seul un boot réussi créait.
 * ⇒ La tâche retente, à cadence lente (un capteur absent ne doit pas sonder le
 *   bus partagé toutes les 5 s : chaque tentative est un `i2c_master_probe` de
 *   500 ms de timeout sur le bus que le GT911 pole 30 fois par seconde).
 */
#define DN_CAPT_REINIT_CYCLES 12 /* 12 × 5 s = une tentative par minute */
static int s_cycles_avant_reinit;
/* 🔴 `dn4-41` / AC2 — LE COMPTE QUI PORTE LE VERDICT « ABSENT ».
 * Ré-ouvertures CONSÉCUTIVES échouées, constatées sur `relever_identite()` —
 * une **lecture de registre**, ⛔ jamais un scan. Remis à 0 dès qu'une identité
 * BME680 est lue ⇒ le verdict est RÉVERSIBLE.
 * ⚠️ La tentative du BOOT ne l'alimente PAS (AC2.3, fenêtre froide). */
static uint32_t s_reouv_echecs;
static bool s_etait_absent; /* pour ne compter `absences` qu'aux TRANSITIONS */
/*
 * ══ 🔴 `dn4-41` / AC9.2 — LE TÉMOIN D'INHIBITION LOGICIELLE ══════════════════
 * Armé, il fait ÉCHOUER la lecture d'identité et FERME le driver — l'état
 * « aucun device » du point de vue du code. ⇒ exerce le backoff, le seuil, la
 * transition, `absences`, la réversibilité et les quatre phrases, à coût NUL.
 * ⛔ SA LIMITE, ÉCRITE ICI : ni NACK, ni timeout, ni condition de bus. Il exerce
 *   LE CHEMIN DE CODE, ⛔ pas le matériel — même limite que l'injecteur
 *   `capteurs simuler` (§13.11), et pour la même raison.
 * ⚠️ Il pose `s_id_tentee = true` / `s_id_lue = false`, ⛔ PAS `invalider_identite()` :
 *    « rien n'a été tenté » et « on a demandé, rien n'a répondu » sont DEUX
 *    diagnostics opposés, et seul le second alimente le verdict. Se tromper ici
 *    rendrait le témoin MUET — il n'aurait rien prouvé, en vert.
 */
static bool s_inhibe;

/*
 * 🔴 CR 2026-08-17 — DISCRIMINER LE TIMEOUT DE DONNÉE DU TIMEOUT DE TRANSPORT.
 *
 * `bme680_get_data()` rend `ESP_ERR_TIMEOUT` depuis DEUX endroits opposés :
 *   · sa boucle d'attente « data ready », qui court 1 500 ms
 *     (`BME680_DATA_POLL_TIMEOUT_MS`, bme680.c:1060-1061) — atteinte APRÈS que
 *     les lectures I²C du registre de statut ont RÉUSSI : le capteur répond très
 *     bien, c'est sa conversion qui n'arrive pas. C'est `err_donnee` ;
 *   · un timeout de verrou de bus dans une transaction — le capteur, lui, n'a
 *     rien pu dire. C'est `err_i2c`.
 * L'ancien code rangeait les deux dans `err_i2c`, sous la légende « le capteur ne
 * repond plus (fil, soudure) » — donc **`err_donnee` ne pouvait jamais quitter 0**
 * et la console envoyait l'opérateur vérifier un câblage parfaitement sain. C'est
 * la leçon de dn2-2 (« tronquée » vs « trop longue ») refaite à l'identique, dans
 * le code écrit pour ne pas la refaire.
 * ⇒ Le discriminant est la DURÉE, qu'on mesure déjà : seule la boucle data-ready
 *   peut consommer la fenêtre entière. Seuil sous les 1 500 ms nominales pour
 *   absorber la granularité du tick.
 */
#define DN_CAPT_SEUIL_POLL_US 1400000

/*
 * Bornes de PLAUSIBILITÉ PHYSIQUE, pas de confort.
 *
 * Le BME680 est spécifié −40..+85 °C et 0..100 %RH. Une valeur hors de là n'est
 * pas « une pièce inhabituelle » : c'est une lecture corrompue, un capteur qui
 * n'a pas fini sa conversion, ou un octet perdu sur le bus. On la REJETTE avec
 * son compteur plutôt que de l'afficher — une case qui montre −273 °C envoie
 * chercher la panne dans l'UI alors qu'elle est sur le fil.
 * ⚠️ CR 2026-08-17 : `dn_ui_ambiance_maj` porte les MÊMES chiffres, et son
 *    commentaire affirmait qu'ils étaient « DIFFÉRENTS ». Ils ne le sont pas, et
 *    un commentaire qui affirme un invariant que le code ne tient pas est pire
 *    que pas de commentaire. Corrigé des deux côtés : ce sont les bornes
 *    PHYSIQUES, l'UI les reprend telles quelles et le dit.
 */
#define DN_CAPT_TEMP_MIN_DX (-400)
#define DN_CAPT_TEMP_MAX_DX 850
#define DN_CAPT_HUM_MIN_DX 0
#define DN_CAPT_HUM_MAX_DX 1000

const char *dn_capt_etat_nom(dn_capt_etat_t e)
{
    switch (e) {
    case DN_CAPT_JAMAIS:
        return "jamais lu";
    case DN_CAPT_VIVANT:
        return "VIVANT";
    case DN_CAPT_MUET:
        return "MUET";
    case DN_CAPT_ABSENT:
        return "ABSENT";
    default:
        return "?";
    }
}

static int64_t lu_us(void)
{
    portENTER_CRITICAL(&s_mux);
    int64_t v = s_lu_us;
    portEXIT_CRITICAL(&s_mux);
    return v;
}

dn_capt_etat_t dn_capt_etat(void)
{
    portENTER_CRITICAL(&s_mux);
    int64_t lu = s_lu_us;
    bool deja = s_a_deja_lu;
    uint32_t echecs = s_reouv_echecs; /* MÊME section critique : un couple
                                       * (âge, échecs) lu en deux fois peut
                                       * n'avoir jamais existé (CR dn4-2). */
    portEXIT_CRITICAL(&s_mux);
    /* 🔴 `dn4-41` — L'ABSENCE DOMINE, ET AVANT `lu < 0`.
     * Sur une carte nue, `s_lu_us` reste à -1 pour toujours : laisser `JAMAIS`
     * gagner rendrait `ABSENT` structurellement inatteignable — le mode de panne
     * « l'état existe mais aucun chemin n'y mène ». C'est aussi le diagnostic le
     * plus SPÉCIFIQUE : ⛔ ne pas envoyer chercher une panne apparue en route
     * quelqu'un qui n'a simplement rien branché. */
    if (echecs >= DN_CAPT_ABSENT_SEUIL) {
        return DN_CAPT_ABSENT;
    }
    if (lu < 0) {
        /* ⚠️ « jamais lu » et « on lisait, on ne lit plus » sont DEUX diagnostics
         * opposés — l'un envoie chercher un cablage, l'autre une panne apparue en
         * route. L'invalidation d'une valeur fausse efface l'horodatage (c'est ce
         * qui fait passer les cases a « -- »), donc `lu < 0` ne suffit PLUS a
         * conclure « jamais ». Constat du 2026-08-17 : la console annonçait
         * « jamais lu » apres 157 lectures reussies. `s_a_deja_lu` tranche. */
        return deja ? DN_CAPT_MUET : DN_CAPT_JAMAIS;
    }
    return (esp_timer_get_time() - lu) < DN_CAPT_PEREMPTION_US ? DN_CAPT_VIVANT
                                                               : DN_CAPT_MUET;
}

int dn_capt_temperature_dixiemes(void)
{
    portENTER_CRITICAL(&s_mux);
    int v = s_temp_dx;
    portEXIT_CRITICAL(&s_mux);
    return v;
}

int dn_capt_humidite_dixiemes(void)
{
    portENTER_CRITICAL(&s_mux);
    int v = s_hum_dx;
    portEXIT_CRITICAL(&s_mux);
    return v;
}

int dn_capt_pression_dixiemes(void)
{
    portENTER_CRITICAL(&s_mux);
    int v = s_pression_dx;
    portEXIT_CRITICAL(&s_mux);
    return v;
}

int dn_capt_pression_brut_dixiemes(void)
{
    portENTER_CRITICAL(&s_mux);
    int v = s_pression_brut_dx;
    portEXIT_CRITICAL(&s_mux);
    return v;
}

int dn_capt_gaz_ohms(void)
{
    portENTER_CRITICAL(&s_mux);
    int v = s_gaz_ohms;
    portEXIT_CRITICAL(&s_mux);
    return v;
}

bool dn_capt_gaz_en_attente(void)
{
    portENTER_CRITICAL(&s_mux);
    bool v = s_gaz_attente;
    portEXIT_CRITICAL(&s_mux);
    return v;
}

int dn_capt_iaq_brut(void)
{
    portENTER_CRITICAL(&s_mux);
    int v = s_iaq_brut;
    portEXIT_CRITICAL(&s_mux);
    return v;
}

dn_capt_p_unite_t dn_capt_pression_unite(void)
{
    portENTER_CRITICAL(&s_mux);
    dn_capt_p_unite_t u = s_pression_unite;
    portEXIT_CRITICAL(&s_mux);
    return u;
}

const char *dn_capt_pression_unite_nom(dn_capt_p_unite_t u)
{
    switch (u) {
    case DN_CAPT_P_UNITE_HPA:       return "hPa (le driver tient sa promesse)";
    case DN_CAPT_P_UNITE_PA:        return "Pa (l'etiquette du driver MENT)";
    case DN_CAPT_P_UNITE_ABERRANTE: return "ABERRANTE — ni hPa ni Pa";
    default:                        return "INCONNUE — aucune lecture";
    }
}

int64_t dn_capt_age_us(void)
{
    int64_t lu = lu_us();
    return (lu < 0) ? -1 : esp_timer_get_time() - lu;
}

int64_t dn_capt_duree_cycle_us(void)
{
    portENTER_CRITICAL(&s_mux);
    int64_t v = s_cycle_us;
    portEXIT_CRITICAL(&s_mux);
    return v;
}

int64_t dn_capt_cadence_reelle_us(void)
{
    portENTER_CRITICAL(&s_mux);
    int64_t v = s_cadence_us;
    portEXIT_CRITICAL(&s_mux);
    return v;
}

void dn_capt_compteurs(dn_capt_compteurs_t *out)
{
    portENTER_CRITICAL(&s_mux);
    *out = s_cnt;
    portEXIT_CRITICAL(&s_mux);
}

void dn_capt_reset_compteurs(void)
{
    /* ⚠️ On garde la VALEUR et son horodatage : remettre les compteurs à zéro ne
     * doit pas tuer la lecture en cours. Correctif de revue dn2-2 transposé
     * (`pc reset` avait le défaut inverse et sabotait ses propres campagnes). */
    portENTER_CRITICAL(&s_mux);
    memset(&s_cnt, 0, sizeof(s_cnt));
    portEXIT_CRITICAL(&s_mux);
}

const char *dn_capt_faute_nom(dn_capt_faute_t f)
{
    switch (f) {
    case DN_CAPT_FAUTE_MUET:
        return "MUET (le capteur ne repond plus)";
    case DN_CAPT_FAUTE_BORNES:
        return "BORNES (valeur hors plage physique)";
    case DN_CAPT_FAUTE_CONFIG:
        return "CONFIG (capteur fantome : repond mais a perdu sa config)";
    default:
        return "aucune";
    }
}

dn_capt_faute_t dn_capt_faute_active(void)
{
    portENTER_CRITICAL(&s_mux);
    dn_capt_faute_t f = s_faute;
    portEXIT_CRITICAL(&s_mux);
    return f;
}

int dn_capt_faute_restants(void)
{
    portENTER_CRITICAL(&s_mux);
    int n = s_faute_restants;
    portEXIT_CRITICAL(&s_mux);
    return n;
}

esp_err_t dn_capt_simuler(dn_capt_faute_t f, int cycles)
{
    if (cycles < 0 || cycles > 600) {
        return ESP_ERR_INVALID_ARG;
    }
    portENTER_CRITICAL(&s_mux);
    if (f == DN_CAPT_FAUTE_AUCUNE || cycles == 0) {
        s_faute_restants = 0;
        s_faute = DN_CAPT_FAUTE_AUCUNE;
    } else {
        s_faute = f;
        s_faute_restants = cycles;
    }
    portEXIT_CRITICAL(&s_mux);
    return ESP_OK;
}

uint8_t dn_capt_reg_ctrl_hum(void) { return s_reg_hum; }
uint8_t dn_capt_reg_ctrl_meas(void) { return s_reg_meas; }
uint8_t dn_capt_reg_config(void) { return s_reg_cfg; }
bool dn_capt_config_conforme(void) { return s_conforme; }
bool dn_capt_config_verdict_dispo(void) { return s_conf_dispo; }

uint8_t dn_capt_chip_id(void) { return s_chip_id; }
/* 🔴 dn4-2 : SANS CECI, `capteurs` continuerait d'imprimer « chip id 0x00 » sur
 * une lecture ECHOUEE — le mensonge se serait DEPLACE du bandeau vers la console
 * au lieu d'etre corrige. Rend FAUX quand la transaction n'a pas abouti. */
bool dn_capt_identite_lue(void) { return s_id_lue; }
/* 🔴 CR dn4-2 : le 3e etat. FAUX = aucune lecture n'a ete tentee. */
bool dn_capt_identite_tentee(void) { return s_id_tentee; }
uint8_t dn_capt_variant(void) { return s_variant; }
/* 🔴 CR dn4-2 : FAUX = le variant n'a pas ete lu. ⛔ 0x00 est une valeur
 * LEGITIME (BME680), donc la valeur seule ne peut pas porter l'echec. */
bool dn_capt_variant_lu(void) { return s_variant_lu; }
/* Lecture ATOMIQUE des quatre champs d'identite. ⚠️ Les lire un par un
 * laissait la console observer un etat A DEMI mis a jour : le chemin
 * d'echec ecrit `s_chip_id = 0` PUIS `s_id_lue = false`, et un `capteurs`
 * qui atterrissait entre les deux imprimait « chip id 0x00 … A REPONDU,
 * mais ce n'est PAS un BME680 » — la phrase exacte que ce correctif
 * existe pour rendre impossible. */
void dn_capt_identite_snapshot(bool *tentee, bool *lue, uint8_t *chip,
                               bool *var_lu, uint8_t *var)
{
    portENTER_CRITICAL(&s_mux);
    if (tentee) { *tentee = s_id_tentee; }
    if (lue) { *lue = s_id_lue; }
    if (chip) { *chip = s_chip_id; }
    if (var_lu) { *var_lu = s_variant_lu; }
    if (var) { *var = s_variant; }
    portEXIT_CRITICAL(&s_mux);
}

bool dn_capt_gaz_actif(void)
{
    portENTER_CRITICAL(&s_mux);
    bool g = s_gaz;
    portEXIT_CRITICAL(&s_mux);
    return g;
}

esp_err_t dn_capt_set_gaz(bool actif)
{
    if (!s_dev) {
        return ESP_ERR_INVALID_STATE;
    }
    portENTER_CRITICAL(&s_mux);
    s_gaz_demande = actif;
    portEXIT_CRITICAL(&s_mux);
    return ESP_OK;
}

/*
 * La configuration, ligne par ligne — même discipline qu'une ligne de
 * sdkconfig.defaults : une ligne, une raison.
 *
 * ⚠️ CR 2026-08-17 : ces valeurs sont AUSSI ce que la console imprime sur sa ligne
 *    « demande ». Elle portait un littéral codé en dur juste à côté de la ligne
 *    « config LUE » — c'est-à-dire l'ombre logicielle que §13.10 venait d'exclure,
 *    remise une ligne plus bas. Les libellés vivent maintenant dans le .h, à côté
 *    des constantes qu'ils décrivent, et les deux se changent ensemble.
 */
static bme680_config_t config_voulue(bool gaz)
{
    bme680_config_t c = {
        .i2c_address = DN_BME680_ADDR,
        /* ⚠️ 400 kHz et non les 100 kHz par défaut du composant : une
         * transaction 4× plus courte occupe 4× moins longtemps un bus dont la
         * DMA du panneau se dispute déjà le SoC (§11.4). Et c'est la fréquence
         * que NOS autres devices demandent (dn_pins.h). */
        .i2c_clock_speed = DN_I2C_FREQ_HZ,
        /* FORCED : une mesure, puis retour en sommeil. C'est le mode qui
         * consomme et chauffe le MOINS — les deux comptent ici (§ DN_CAPT_GAZ). */
        .power_mode = BME680_POWER_MODE_FORCED,
        /* IIR sur 3 échantillons : lisse le bruit de conversion sans retarder
         * une vraie variation d'ambiance. ⚠️ Ce n'est PAS le « lissage » que le
         * brief demande (moyenne d'affichage) — celui-là reste explicitement
         * absent, comme en dn2-2, et se solde en dn4-3. (⚠️ CR du 2026-08-24 :
         * cette ligne disait « dn4-1 », qui est `superseded` depuis le
         * 2026-08-18 — etiquette prospective sur une story morte.) */
        .iir_filter = BME680_IIR_FILTER_3,
        .standby_time = BME680_STANDBY_TIME_NONE, /* sans objet en FORCED */
        /* La pression n'est PAS au dashboard (brief : six widgets figés). On ne
         * la SAUTE pas pour autant : la compensation de température du BME680
         * s'appuie sur la chaîne de mesure complète, et 1× coûte le minimum. */
        .pressure_oversampling = BME680_PRESSURE_OVERSAMPLING_1X,
        /* 8× sur les deux grandeurs AFFICHÉES : c'est là qu'on paie pour de la
         * stabilité, et nulle part ailleurs. */
        .temperature_oversampling = BME680_TEMPERATURE_OVERSAMPLING_8X,
        .humidity_oversampling = BME680_HUMIDITY_OVERSAMPLING_8X,
        .gas_enabled = gaz,
        /* Sans objet quand gas_enabled=false, mais posés : si l'A/B de T9
         * rallume le gaz, il doit le faire dans les conditions du DÉFAUT du
         * composant (300 °C / 300 ms), sinon on comparerait deux choses
         * différentes et le delta ne voudrait rien dire. */
        .heater_temperature = 300,
        .heater_duration = 300,
        .heater_profile_size = 1,
    };
    return c;
}

/*
 * Lit les deux registres d'identité SANS le driver, par le bus nu.
 *
 * Pourquoi avant `bme680_init()` : ce dernier refuse si chip_id != 0x61, mais il
 * ne dit pas CE QU'IL A LU. Or « 0x60 » (BME280) et « 0x58 » (BMP280) sont des
 * diagnostics précis — un module vendu « BME680 » qui n'en est pas. Un refus
 * muet enverrait chercher la panne du côté du câblage, qu'on vient justement de
 * prouver bon.
 */
static void relever_identite(i2c_master_bus_handle_t bus)
{
    /* 🔴 CR dn4-2 (2026-08-20) — L'INVALIDATION SE FAIT EN ENTREE, ET C'EST LE
     * CORRECTIF QUI REND LE GARDE-FOU REEL.
     * Les sorties anticipees (bus NULL, `add_device` refuse) laissaient DEBOUT le
     * verdict du releve PRECEDENT. `identite_est_bme680()` le relisait alors comme
     * s'il etait frais, et `ouvrir_driver()` partait sur une transaction QUI N'A
     * JAMAIS EU LIEU — donc exactement le chemin d'`abort()` que le garde-fou
     * pretend fermer. Scenario atteignable : boot OK (chip id 0x61) mais
     * `ouvrir_driver()` echoue ⇒ s_dev NULL ; a la reprise 60 s plus tard,
     * `add_device` echoue (heap interne) ⇒ retour sans aucune lecture, et le
     * 0x61 du boot sert de laissez-passer.
     * ⇒ Tant qu'une lecture n'a pas abouti DANS CET APPEL, il n'y a PAS
     *   d'identite. La regle est la meme que pour la config relue dans le capteur
     *   (§13.10) : on CONSTATE, on ne se souvient pas. */
    /* 🔴 CR dn4-2 du 2026-08-24 — L'INVALIDATION ETAIT FAITE EN ENTREE, DONC
     * OBSERVABLE PENDANT 400 ms. Le snapshot atomique ferme l'etat « a demi
     * ecrit » ; il ne fermait PAS l'etat « deliberement efface », qui durait le
     * temps des deux transactions (2 x 200 ms) et se rouvrait toutes les 60 s
     * (reprise) ou toutes les 5 s (chemin degrade), pendant que le REPL tourne en
     * permanence. Taper `capteurs` dans la fenetre imprimait « AUCUNE transaction
     * n'a ete TENTEE (bus I2C absent, ou ouverture du device refusee) » SUR UNE
     * CARTE DONT LE BUS EST PRESENT et dont le device vient d'etre ouvert —
     * la meme classe d'affirmation-sur-rien que le tri-etat existe pour supprimer.
     * ⇒ L'invalidation descend sur les SORTIES ANTICIPEES. Le garde-fou est
     *   intact (aucun chemin ne sort en laissant un verdict PERIME), et il n'y a
     *   plus d'etat intermediaire visible : soit l'ancien verdict, soit le neuf. */
    if (!bus) {
        invalider_identite();
        return; /* rien n'a ete TENTE — et `s_id_tentee` faux le dit exactement */
    }
    if (s_inhibe) {
        /* 🔴 `dn4-41` — TEMOIN D'INHIBITION. ⚠️ `tentee = true, lue = false` :
         * on simule « la transaction a EU LIEU et rien n'a acquitte », ⛔ pas
         * « rien n'a ete tente ». Voir le docblock de `s_inhibe`. */
        portENTER_CRITICAL(&s_mux);
        s_id_tentee = true;
        s_id_lue = false;
        s_chip_id = 0;
        s_variant_lu = false;
        s_variant = 0;
        portEXIT_CRITICAL(&s_mux);
        return;
    }
    i2c_device_config_t cfg = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address = DN_BME680_ADDR,
        .scl_speed_hz = DN_I2C_FREQ_HZ,
    };
    i2c_master_dev_handle_t dev = NULL;
    if (i2c_master_bus_add_device(bus, &cfg, &dev) != ESP_OK) {
        invalider_identite();
        return; /* idem : pas de transaction, donc pas d'identite */
    }

    /* ⚠️ Les octets atterrissent dans des LOCALES, pas dans les statiques que la
     * console lit : `&s_chip_id` en tampon RX laissait observer une identite a
     * demi mise a jour pendant les 200 ms de la transaction. */
    uint8_t chip = 0, variant = 0;
    uint8_t reg = DN_BME680_REG_CHIP_ID;
    bool chip_ok =
        (i2c_master_transmit_receive(dev, &reg, 1, &chip, 1, 200) == ESP_OK);
    reg = DN_BME680_REG_VARIANT;
    bool var_ok =
        (i2c_master_transmit_receive(dev, &reg, 1, &variant, 1, 200) == ESP_OK);

    /* ⚠️ Le retour est LU : `i2c_master_bus_rm_device()` REFUSE tant que le bus
     * est en transaction (`status <= I2C_STATUS_START`, esp_driver_i2c
     * i2c_master.c:1216) — et ce test precede la prise du verrou de bus, alors
     * que le GT911 le sonde ~30x/s. Un refus ne libere NI le device NI son entree
     * de liste : c'est une fuite definitive et silencieuse. On la DIT. */
    esp_err_t rm = i2c_master_bus_rm_device(dev);
    if (rm != ESP_OK) {
        ESP_LOGW(TAG,
                 "retrait du device d'identite REFUSE (%s) — un device fantome "
                 "reste sur le bus. ⚠️ Course connue avec le sondage du GT911 ; "
                 "sans consequence immediate, mais elle FUIT.",
                 esp_err_to_name(rm));
    }

    portENTER_CRITICAL(&s_mux);
    s_id_tentee = true;
    s_id_lue = chip_ok;
    s_chip_id = chip_ok ? chip : 0;
    s_variant_lu = var_ok;
    s_variant = var_ok ? variant : 0;
    portEXIT_CRITICAL(&s_mux);
}

/* Efface le verdict d'identite. ⛔ Appelee sur les SORTIES ANTICIPEES de
 * `relever_identite()` uniquement — jamais en entree : voir le CR du 2026-08-24
 * dans cette fonction. */
static void invalider_identite(void)
{
    portENTER_CRITICAL(&s_mux);
    s_id_tentee = false;
    s_id_lue = false;
    s_chip_id = 0;
    s_variant_lu = false;
    s_variant = 0;
    portEXIT_CRITICAL(&s_mux);
}

/*
 * 🔴 `dn4-41` / AC2 — LE VERDICT « ABSENT », ET CE QUI LE FAIT BOUGER.
 *
 * ⛔ CE QUI NE LE FAIT PAS BOUGER : le scan `i2c`, `i2c_master_probe()`, et
 * `i2c_master_bus_add_device()`. Aucun des trois ne QUALIFIE :
 *   · le scan fabrique des faux positifs (~15 adresses fantomes en ~20 scans,
 *     dont `0x76` — l'adresse du BME680 — capteur DEBRANCHE) ;
 *   · au cycle 1 de l'A/B a froid, il annoncait `8 stables / 0 instable`
 *     PENDANT que le GT911 etait a 55,5 % d'erreurs ;
 *   · `add_device()` alloue un descripteur, il ne parle a personne.
 * ⇒ Seule la LECTURE DU REGISTRE D'IDENTITE tranche — *« le scan DECOUVRE ;
 *   seule une transaction de DONNEE QUALIFIE »* (§13.17.1).
 *
 * ⚠️ TROIS ISSUES, ET ELLES NE SE VALENT PAS :
 *   · `s_id_lue`                -> quelque chose a REPONDU  ⇒ ⛔ PAS absent ;
 *   · `s_id_tentee && !s_id_lue`-> on a demande, rien n'a acquitte ⇒ ECHEC ;
 *   · `!s_id_tentee`            -> RIEN N'A ETE TENTE (bus NULL, `add_device`
 *     refuse) ⇒ ⛔ ON NE COMPTE PAS. Compter ici accuserait un capteur dont
 *     personne n'a demande de nouvelles — la meme faute que le 4e cas de
 *     `journaliser_identite()` a ete ecrit pour supprimer (CR dn4-2).
 */
static void verdict_absence_maj(void)
{
    portENTER_CRITICAL(&s_mux);
    bool tentee = s_id_tentee;
    bool lue = s_id_lue;
    portEXIT_CRITICAL(&s_mux);

    if (!tentee) {
        return; /* rien n'a ete TENTE : ⛔ aucune conclusion */
    }

    if (lue) {
        portENTER_CRITICAL(&s_mux);
        bool sortait = s_etait_absent;
        s_reouv_echecs = 0;
        s_etait_absent = false;
        portEXIT_CRITICAL(&s_mux);
        if (sortait) {
            ESP_LOGW(TAG, "BME680 : n'est PLUS absent — une lecture d'identite a "
                          "abouti. Le verdict est retire.");
        }
        return;
    }

    portENTER_CRITICAL(&s_mux);
    if (s_reouv_echecs < UINT32_MAX) {
        s_reouv_echecs++;
    }
    uint32_t n = s_reouv_echecs;
    bool transition = (n >= DN_CAPT_ABSENT_SEUIL) && !s_etait_absent;
    if (transition) {
        s_etait_absent = true;
        s_cnt.absences++;
    }
    portEXIT_CRITICAL(&s_mux);
    if (transition) {
        /* Dit UNE fois par entree en absence. ⛔ Pas toutes les 60 s : c'est
         * exactement le pave que `dn4-2` a sorti du transport PC. */
        ESP_LOGW(TAG,
                 "BME680 @ 0x%02X : ABSENT — %lu lectures d'identite "
                 "consecutives ont echoue (>= %d). ⛔ Ce n'est PAS « muet » : "
                 "rien n'acquitte sur le bus. Les cases disent « -- », la source "
                 "RESTE ARMEE et une seule lecture valide annule le verdict.",
                 DN_BME680_ADDR, (unsigned long)n, DN_CAPT_ABSENT_SEUIL);
    }
}

void dn_capt_inhiber(bool on)
{
    s_inhibe = on;
    if (on && s_dev) {
        /* ⚠️ SANS CETTE FERMETURE LE TEMOIN NE PROUVE RIEN : tant que `s_dev`
         * tient, la boucle lit la DONNEE (qui, elle, aboutit) et le verdict est
         * remis a zero a chaque cycle — le seuil ne serait JAMAIS atteint.
         * ⇒ On rend le module a l'etat qu'un capteur absent produit : pas de
         *   driver, donc branche de backoff, donc lecture d'identite, donc
         *   verdict. ⛔ C'est le meme menage que le chemin degrade fait deja. */
        bme680_delete(s_dev);
        s_dev = NULL;
    }
    if (!on) {
        /* ⛔ On ne re-ouvre PAS ici : c'est la branche de backoff qui le fera,
         * dans au plus 60 s, PAR LE CHEMIN NORMAL. Rouvrir depuis le REPL
         * emprunterait un chemin que la carte ne prend jamais toute seule. */
        ESP_LOGW(TAG, "temoin d'inhibition DESARME — la reprise passera par la "
                      "branche de backoff (au plus %d s), ⛔ pas par le REPL.",
                 (DN_CAPT_REINIT_CYCLES * DN_CAPT_PERIODE_MS) / 1000);
    } else {
        ESP_LOGW(TAG, "temoin d'inhibition ARME — ⛔ ceci n'exerce NI NACK NI "
                      "timeout NI le bus, seulement le CHEMIN DE CODE.");
    }
}

bool dn_capt_inhibe(void)
{
    return s_inhibe;
}

uint32_t dn_capt_absent_delai_s(void)
{
    return (uint32_t)((DN_CAPT_ABSENT_SEUIL * DN_CAPT_REINIT_CYCLES
                       * DN_CAPT_PERIODE_MS)
                      / 1000);
}

uint32_t dn_capt_reouv_echecs(void)
{
    portENTER_CRITICAL(&s_mux);
    uint32_t n = s_reouv_echecs;
    portEXIT_CRITICAL(&s_mux);
    return n;
}

/* Signature du verdict d'identite, pour ne republier que ce qui CHANGE.
 * ⚠️ CR dn4-2 du 2026-08-24 — DEUX DEFAUTS CORRIGES ICI.
 * (1) ELLE IGNORAIT LA VALEUR DU VARIANT. Elle agregeait `s_variant_lu` (le
 *     BOOLEEN « on a lu ») et jamais `s_variant` (la VALEUR) : une bascule
 *     BME680 <-> BME688 (0x00 -> 0x01) rendait donc la MEME signature et n'etait
 *     JAMAIS republiee — alors que c'est exactement l'ambiguite pour laquelle
 *     `s_variant_lu` a ete introduit, deux lignes plus haut, dans le meme commit.
 * (2) LA SENTINELLE ET UNE SIGNATURE LEGITIME COLLISIONNAIENT. La fonction
 *     rendait 0 quand tentee=false, lue=false, variant_lu=false, chip_id=0 —
 *     c'est-a-dire l'etat « aucune transaction tentee » — or 0 est AUSSI la
 *     valeur de remise a zero apres une reprise reussie. Consequence : apres une
 *     reprise, une rechute en « bus absent / device refuse » donnait
 *     `sig == s_id_sig_publiee == 0` et `journaliser_identite()` n'etait JAMAIS
 *     appele : le 4e cas ajoute par ce meme correctif etait MUET sur le chemin de
 *     reprise, dans le scenario qu'il decrit.
 * ⇒ Le bit 0x8000 est TOUJOURS pose : aucune signature reelle ne vaut plus 0,
 *   donc 0 redevient une sentinelle sans ambiguite. */
static uint16_t identite_signature(void)
{
    return (uint16_t)(0x8000 | (s_id_tentee ? 0x4000 : 0) |
                      (s_id_lue ? 0x2000 : 0) | (s_variant_lu ? 0x1000 : 0) |
                      ((uint16_t)(s_variant & 0x0F) << 8) | s_chip_id);
}

/* 🔴 LE GARDE-FOU QUI MANQUAIT, ET DONT L'INTENTION ETAIT DEJA ECRITE.
 * Le docblock de `relever_identite()` dit « pourquoi AVANT bme680_init() » — mais
 * son resultat ne DECIDAIT rien : `ouvrir_driver()` etait appele quoi qu'il
 * arrive, et le composant TIERS `k0i05__esp_bme680` enveloppe ses lectures I2C
 * dans `ESP_ERROR_CHECK` (bme680.c:433, chemin NOMINAL d'init). Un hoquet de bus
 * y devenait donc un `abort()`, donc — avec CONFIG_ESP_SYSTEM_PANIC_PRINT_HALT=y —
 * un CPU HALTE, donc PLUS DE CONSOLE : l'outil de diagnostic disparaissait au
 * moment precis ou il servait. Mesure du 2026-08-20 : 6 demarrages a froid rates
 * sur 7 a huit devices, la plupart en carte haltee.
 * ⚠️ Le sondage INFORMAIT ; il PROTEGE desormais. */
static bool identite_est_bme680(void)
{
    return s_id_lue && s_chip_id == DN_BME680_CHIP_ID;
}

static void journaliser_identite(void)
{
    const char *quoi = s_chip_id == DN_BME680_CHIP_ID
                           ? (!s_variant_lu ? "BME680 ou BME688 — variant NON LU"
                              : s_variant == DN_BME680_VARIANT_688 ? "BME688"
                                                                   : "BME680")
                       : s_chip_id == 0x60 ? "BME280 — PAS de gaz"
                       : s_chip_id == 0x58 ? "BMP280 — NI gaz NI humidite"
                                           : "INCONNU";
    /* 🔴 CR dn4-2 : QUATRIEME CAS. « aucune lecture tentee » n'est pas « la
     * lecture a echoue » — envoyer l'operateur verifier une adresse quand aucune
     * transaction n'a eu lieu, c'est encore affirmer sur un capteur muet. */
    if (!s_id_tentee) {
        ESP_LOGE(TAG,
                 "identite NON RELEVEE @ 0x%02X — ⛔ AUCUNE transaction n'a ete "
                 "TENTEE (bus I2C absent, ou ouverture du device refusee). Ce "
                 "n'est ni « il a repondu 0x00 » ni « il n'a pas repondu » : on "
                 "n'a rien demande. Le driver ne sera PAS ouvert.",
                 DN_BME680_ADDR);
    } else if (!s_id_lue) {
        /* 🔴 TROISIEME CAS, AJOUTE EN dn4-2 : la LECTURE a echoue. ⛔ Ne RIEN
         * affirmer sur le capteur — il n'a rien dit. Publier « chip id 0x00 »
         * ici envoyait chercher un mauvais composant alors que le bus etait en
         * cause, et le message se contredisait lui-meme en ajoutant « le cablage
         * n'est pas en cause si le scan voit 0x77 ». */
        ESP_LOGE(TAG,
                 "identite NON LUE @ 0x%02X — la transaction I2C a ECHOUE. ⛔ Ce "
                 "n'est PAS « le capteur a repondu 0x00 » : il n'a rien repondu. "
                 "Verifier par `i2c` (l'adresse est-elle la ?) puis `i2c lire "
                 "%02X D0` (repond-elle 0x%02X ?). Le driver ne sera PAS ouvert.",
                 DN_BME680_ADDR, DN_BME680_ADDR, DN_BME680_CHIP_ID);
    } else if (s_chip_id == DN_BME680_CHIP_ID) {
        /* ⚠️ Le variant ne s'affirme que s'il a ete LU : 0x00 est la valeur
         * legitime du BME680, donc un variant rate se lirait comme un verdict. */
        if (s_variant_lu) {
            ESP_LOGI(TAG, "identite : chip id 0x%02X, variant 0x%02X => %s @ 0x%02X",
                     s_chip_id, s_variant, quoi, DN_BME680_ADDR);
        } else {
            ESP_LOGW(TAG,
                     "identite : chip id 0x%02X @ 0x%02X, mais le VARIANT n'a PAS "
                     "ete lu — ⛔ ne PAS conclure « BME680 » : 0x00 est sa valeur "
                     "legitime, et un BME688 se lirait pareil. Trancher par "
                     "`i2c lire %02X F0`.",
                     s_chip_id, DN_BME680_ADDR, DN_BME680_ADDR);
        }
    } else {
        ESP_LOGE(TAG,
                 "identite INATTENDUE : chip id 0x%02X (attendu 0x%02X) => %s. "
                 "Le capteur A REPONDU, mais ce n'est pas le bon composant. Le "
                 "driver ne sera PAS ouvert.",
                 s_chip_id, DN_BME680_CHIP_ID, quoi);
    }
}

/* Lit un registre par le bus NU. Le driver n'expose pas de lecture générique et
 * ses getters décodent en champs de bits — or ici on veut l'OCTET BRUT, celui
 * qu'on peut comparer et imprimer sans interprétation. */
static bool lire_reg(uint8_t reg, uint8_t *out)
{
    if (!s_brut) {
        return false;
    }
    return i2c_master_transmit_receive(s_brut, &reg, 1, out, 1, 200) == ESP_OK;
}

/*
 * La configuration ATTENDUE, relue dans le capteur JUSTE APRÈS que le driver l'a
 * posée : on n'invente pas la valeur de référence, on la CONSTATE.
 *
 * 🔴 CR 2026-08-17 — LES TROIS LECTURES SONT DÉSORMAIS TESTÉES, ET C'EST UN
 * DÉFAUT MAJEUR QUI TOMBE. Leurs valeurs de retour étaient IGNORÉES et
 * `s_conforme = true` posé quand même. Une seule lecture perdue au boot laissait
 * son octet de référence à `0x00` (statique jamais écrit) ⇒ la garde trouvait un
 * écart À CHAQUE CYCLE, rappelait `bme680_init()` toutes les 5 s, invalidait la
 * valeur à chaque fois : cases figées à « -- », `reconfigs` sans fin, et le
 * diagnostic accusait un capteur en parfait état.
 * ⚠️ Et ce n'est pas théorique sur CE bus : la story a MESURÉ que le sondage
 *    produit des faux négatifs et que trois composants soudés ont raté une
 *    confirmation dans la même séance (§13.6 bis). Une transaction qui se perd
 *    ici est un événement attendu, pas une hypothèse d'école.
 * ⇒ Si l'une des trois échoue, il n'y a PAS de référence, donc PAS de verdict —
 *   et la garde le dit au lieu de fabriquer un diagnostic.
 */
static bool lire_reference_config(void)
{
    uint8_t h = 0, m = 0, c = 0;
    if (!lire_reg(0x72, &h) || !lire_reg(0x74, &m) || !lire_reg(0x75, &c)) {
        s_conf_dispo = false;
        s_conforme = false;
        ESP_LOGW(TAG, "reference de configuration NON LUE — la garde de "
                      "reconfiguration reste INERTE, et `capteurs` le dira "
                      "(« verdict indisponible », pas « NON CONFORME »)");
        return false;
    }
    s_att_hum = h;
    s_att_meas = m;
    s_att_cfg = c;
    s_reg_hum = h;
    s_reg_meas = m;
    s_reg_cfg = c;
    s_conforme = true;
    s_conf_dispo = true;
    ESP_LOGI(TAG, "config relue dans le capteur : 0x72=%02X 0x74=%02X 0x75=%02X", h,
             m, c);
    return true;
}

/* Ouvre le driver et relève sa référence de configuration. Rendue réutilisable
 * par le correctif de re-tentative : le boot et la reprise passent par le MÊME
 * chemin, sinon la reprise finirait par diverger du boot sans que rien ne le
 * dise. */
static bool ouvrir_driver(i2c_master_bus_handle_t bus)
{
    /* 🔴 CR dn4-2 — CEINTURE. Le 3e site d'appel passait `dn_display_i2c_bus()`
     * SANS test NULL, et `bme680_init()` le recevait tel quel. Le refus se pose
     * ici une fois pour les trois chemins. */
    if (!bus) {
        ESP_LOGE(TAG, "ouverture REFUSEE : le bus I2C n'existe pas "
                      "(dn_display_init() n'a pas tourne). ⛔ Le driver tiers "
                      "n'est PAS appele.");
        return false;
    }
    portENTER_CRITICAL(&s_mux);
    bool gaz = s_gaz;
    portEXIT_CRITICAL(&s_mux);

    bme680_config_t cfg = config_voulue(gaz);
    bme680_handle_t neuf = NULL;
    esp_err_t err = bme680_init(bus, &cfg, &neuf);
    if (err != ESP_OK || !neuf) {
        ESP_LOGE(TAG, "bme680_init a echoue (%s)", esp_err_to_name(err));
        return false;
    }
    if (s_dev) {
        bme680_delete(s_dev); /* ⚠️ sinon on fuit un device sur le bus a chaque reset */
    }
    s_dev = neuf;
    lire_reference_config();
    return true;
}

/* Applique la valeur aux cases 4 (TEMP.) et 5 (HUMIDITE) du dashboard.
 * ⚠️ dn_ui prend le verrou LVGL LUI-MÊME ; on ne le prend jamais ici.
 *
 * 🔴 CR 2026-08-17 — LE RETOUR EST ENFIN LU, ET UNE POUSSÉE PERDUE EST COMPTÉE.
 * `dn_ui_ambiance_maj()` rend `false` **sans rien avoir modifié** quand le verrou
 * LVGL n'a pas pu être pris en 1 000 ms — cas réel du dépôt, un plein écran à
 * `lines 8` le tient ~2,1 s. L'ancien appel jetait ce retour et passait `NULL` en
 * `label_pose` : la valeur était perdue en silence, l'écran restait périmé 5 s de
 * plus, et AUCUN compteur ne le disait. Le patron de référence, lui, retente
 * (`dn_link.c` : « verrou LVGL non pris : on retentera dans 250 ms »).
 * ⚠️ AC8 exige de reproduire la DISTINCTION valeur de retour / `label_pose`, pas
 *    seulement la signature.
 */
static void pousser_ui(void)
{
    dn_capt_etat_t e = dn_capt_etat();
    bool valide = (e == DN_CAPT_VIVANT);
    int t = dn_capt_temperature_dixiemes();
    int h = dn_capt_humidite_dixiemes();
    bool pose = false;

    if (dn_ui_ambiance_maj(t, h, valide, &pose)) {
        return;
    }
    /* Une seule re-tentative, courte : la période est de 5 s, on a le temps, mais
     * boucler sans fin sous un verrou tenu par un plein écran ferait de cette
     * tâche un second demandeur permanent sur le même mutex. */
    vTaskDelay(pdMS_TO_TICKS(250));
    if (dn_ui_ambiance_maj(t, h, valide, &pose)) {
        return;
    }
    portENTER_CRITICAL(&s_mux);
    s_cnt.pousses_ratees++;
    portEXIT_CRITICAL(&s_mux);
    ESP_LOGW(TAG, "verrou LVGL indisponible 2 fois — poussee perdue, l'ecran garde "
                  "l'affichage du cycle precedent pendant %d ms",
             DN_CAPT_PERIODE_MS);
}

/*
 * 🔴 LE CAPTEUR PEUT REDÉMARRER SOUS NOS PIEDS — MESURÉ LE 2026-08-17.
 *
 * Couper son 3V3 quelques secondes remet les trois registres de configuration à
 * 0x00 : suréchantillonnages SKIPPED, mode SLEEP, filtre OFF. Le handle logiciel,
 * lui, survit intact — et `bme680_get_data()` continue de RÉUSSIR. La compensation
 * Bosch, alimentée par des ADC non configurés, produit alors **32,8 °C et 100 %RH**.
 *
 * ⚠️ CE QUI REND CE DÉFAUT MÉCHANT, ET POURQUOI AUCUNE GARDE EXISTANTE NE L'ATTRAPE :
 *   · ce n'est PAS une erreur de transport — le capteur répond parfaitement ;
 *   · ce n'est PAS une valeur aberrante — 32,8 °C et 100 %RH sont physiquement
 *     plausibles, donc les bornes les acceptent ;
 *   · ce n'est PAS un silence — l'état reste VIVANT, la péremption ne se déclenche
 *     jamais, et `reprises` reste à 0.
 * L'AC7 protège contre « le capteur se tait et la case fige ». Le vrai mode de
 * panne est « le capteur répond avec du n'importe quoi », et il fallait le geste
 * physique de l'owner pour le faire apparaître.
 *
 * ⇒ On RELIT la config à chaque cycle et on la RÉ-APPLIQUE si elle a disparu.
 *   Le cycle de la reconfiguration est déclaré INVALIDE : la première conversion
 *   qui suit part d'un capteur qu'on vient de reprogrammer.
 *
 * ⚠️ CR 2026-08-17 : la faute injectée est passée en PARAMÈTRE et n'est plus relue
 *    dans la globale. L'ancienne version lisait `s_faute`, que le bloc d'injection
 *    venait de remettre à `AUCUNE` sur son dernier cycle : `capteurs simuler
 *    config 1` n'injectait RIEN, et `config n` n'injectait que n−1 fois — pendant
 *    que `muet` et `bornes`, qui capturaient la cause en local, en faisaient n.
 *    Les trois injecteurs n'étaient donc pas comparables, ce qui défaisait
 *    exactement la fonction de non-régression qu'on leur demande.
 */
static bool config_verifier_et_reparer(dn_capt_faute_t faute_du_cycle)
{
    uint8_t h = 0, m = 0, c = 0;
    if (!s_conf_dispo) {
        return true; /* pas de référence, pas de verdict — et `capteurs` le dit */
    }
    if (!lire_reg(0x72, &h) || !lire_reg(0x74, &m) || !lire_reg(0x75, &c)) {
        return true; /* le bus a échoué : c'est err_i2c qui parlera, pas ici */
    }
    /* ⚠️ Les 2 bits de POIDS FAIBLE de 0x74 sont le MODE, que le driver change à
     * chaque mesure forcée (sleep -> forced -> sleep). Les comparer ferait crier
     * la garde à chaque cycle. On ne compare que les suréchantillonnages. */
    s_reg_hum = h;
    s_reg_meas = m;
    s_reg_cfg = c;
    s_conforme = ((h & 0x07) == (s_att_hum & 0x07)) &&
                 ((m & 0xFC) == (s_att_meas & 0xFC)) &&
                 ((c & 0x1C) == (s_att_cfg & 0x1C));
    if (faute_du_cycle == DN_CAPT_FAUTE_CONFIG) {
        /* On ment sur le VERDICT, pas sur la lecture : les octets imprimés par
         * `capteurs` restent les vrais. Sinon l'injecteur fabriquerait aussi le
         * diagnostic, et on ne testerait plus rien. */
        s_conforme = false;
    }
    if (s_conforme) {
        s_reconf_echecs = 0;
        return true;
    }

    ESP_LOGE(TAG,
             "🔴 LE CAPTEUR A PERDU SA CONFIGURATION (0x72=%02X 0x74=%02X 0x75=%02X, "
             "attendu %02X/%02X/%02X) — il a redemarre. Ses valeurs etaient FAUSSES "
             "et PLAUSIBLES.",
             h, m, c, s_att_hum, s_att_meas, s_att_cfg);

    /*
     * 🔴 CR 2026-08-17 — ON INVALIDE **AVANT** DE TENTER LA RÉPARATION, ET SUR
     * TOUS LES CHEMINS.
     *
     * L'ancienne version n'invalidait que dans la branche de SUCCÈS. Quand la
     * reconfiguration échouait — le cas que §13.10 a mesuré, en boucle tant que
     * le vrai 3,3 V n'était pas revenu — `s_lu_us` gardait un horodatage récent,
     * `dn_capt_etat()` rendait VIVANT, et `pousser_ui()` re-poussait **en BLANC,
     * comme valides**, les 32,8 °C / 100 %RH que le firmware venait de prouver
     * faux. Pendant les trois cycles de la péremption. Et l'`ESP_LOGE` de la même
     * ligne affirmait « les cases vont passer a « -- » ».
     * ⇒ La valeur est fausse dès l'instant où la config a disparu. Elle tombe ici,
     *   avant toute tentative, quelle que soit la suite.
     */
    portENTER_CRITICAL(&s_mux);
    s_cnt.reconfigs++;
    s_temp_dx = DN_CAPT_DX_ABSENT;
    s_hum_dx = DN_CAPT_DX_ABSENT;
    /* ⚠️ La pression s'invalide AVEC les deux autres : elle vient du même
     * capteur, et un capteur qui a perdu sa configuration ne rend pas une
     * pression plus fiable qu'une température.
     * ⛔ L'UNITÉ, elle, ne se ré-interroge PAS : c'est une propriété du DRIVER,
     *   pas de la lecture. La rendre INCONNUE ici ferait ré-annoncer le verdict
     *   à chaque reconfiguration, et un log qui se répète cesse d'être lu. */
    s_pression_dx = DN_CAPT_DX_ABSENT;
    s_pression_brut_dx = DN_CAPT_DX_ABSENT;
    /* 🔴 LE GAZ ET L'IAQ TOMBENT AUSSI — corrigé en revue de code le
     * 2026-08-20. Ces deux champs, ajoutés par `dn4-3`, étaient les SEULS que
     * cette fonction n'invalidait pas : `capteurs` imprimait « pression :
     * JAMAIS LUE » juste à côté d'une résistance de gaz d'AVANT la
     * reconfiguration, présentée comme courante. ⛔ Le préambule ci-dessus
     * énonce la règle qu'ils enfreignaient : « La valeur est fausse dès
     * l'instant où la config a disparu. » */
    s_gaz_ohms = DN_CAPT_DX_ABSENT;
    s_iaq_brut = DN_CAPT_DX_ABSENT;
    s_gaz_attente = s_gaz;
    s_lu_us = -1;
    portEXIT_CRITICAL(&s_mux);
    s_degrade = true;

    if (s_reconf_echecs >= DN_CAPT_RECONF_ECHECS_MAX) {
        /* Voir DN_CAPT_RECONF_ECHECS_MAX : insister coûte une fuite par tentative
         * dans le composant tiers, et n'a rien produit trois fois de suite. */
        return false;
    }
    /* 🔴 CR dn4-2 (2026-08-20) — LE TROISIEME CHEMIN, ET C'EST CELUI QUI TOURNE
     * EN REGIME. Le garde-fou `identite_est_bme680()` n'etait pose que sur l'init
     * et sur la reprise. CELUI-CI est appele depuis `tache_capteurs()` a chaque
     * cycle de 5 s, et il se declenche EXACTEMENT dans le cas FANTOME (§13.10) :
     * une puce qui acquitte mais a perdu ses registres — c'est-a-dire une puce
     * dont l'alimentation est marginale. Y appeler `ouvrir_driver()` sans rien
     * verifier revenait a jouer a pile ou face avec les 26 `ESP_ERROR_CHECK` de
     * `k0i05__esp_bme680` (bme680.c:432-465) : un hoquet de bus y devient un
     * `abort()`, donc — CONFIG_ESP_SYSTEM_PANIC_PRINT_HALT=y — un CPU HALTE,
     * donc PLUS DE CONSOLE, chez l'owner, en marche.
     * ⛔ Et le bus n'etait pas teste NULL ici, alors qu'il l'est aux deux autres.
     * ⚠️ Le releve d'identite coute 2 transactions I2C, uniquement sur ce chemin
     *    DEGRADE, et il est borne par DN_CAPT_RECONF_ECHECS_MAX. */
    i2c_master_bus_handle_t bus_rep = dn_display_i2c_bus();
    relever_identite(bus_rep); /* invalide en entree : pas de verdict perime */
    /* 🔴 `dn4-41` — ⛔ CE CHEMIN N'ALIMENTE **PAS** LE VERDICT « ABSENT », ET
     * C'EST DELIBERE. Il est DEGRADE, donc cadence toutes les **5 s** : y
     * brancher `verdict_absence_maj()` ferait tomber `ABSENT` a **10 s**
     * d'uptime, c'est-a-dire EN PLEINE FENETRE FROIDE — le faux positif exact
     * qu'AC2.3 existe pour interdire.
     * ✅ Et le verdict reste ATTEIGNABLE : au-dela de
     *   `DN_CAPT_RECONF_ECHECS_MAX`, ce chemin ferme `s_dev`, et la branche de
     *   backoff (une tentative par MINUTE) prend le relais. ⛔ Ne pas « reparer »
     *   ce silence : c'est la marge de la fenetre froide. */
    if (!identite_est_bme680()) {
        /* 🔴 CR dn4-2 du 2026-08-24 — CE CHEMIN N'AVAIT PAS RECU L'ANTI-INONDATION
         * QUE LE CHEMIN A 60 s A RECUE, ET IL EST 6x PLUS RAPIDE. Il appelait
         * `journaliser_identite()` EN DIRECT, sans passer par la signature. Or
         * DN_CAPT_RECONF_ECHECS_MAX compte des echecs CONSECUTIFS et se remet a 0
         * a tout cycle conforme : sur un capteur FANTOME INTERMITTENT (§13.10) —
         * un cycle bon, un cycle perdu, en alternance — la butee ne se ferme
         * JAMAIS, et le pave multi-lignes partait toutes les 10 s indefiniment
         * DANS LE REPL, QUI EST LE TRANSPORT PC. Le correctif avait juge ce meme
         * pave intolerable a 60 s sur l'autre chemin. */
        uint16_t sig_deg = identite_signature();
        if (sig_deg != s_id_sig_publiee) {
            s_id_sig_publiee = sig_deg;
            journaliser_identite();
        }
        if (++s_reconf_echecs >= DN_CAPT_RECONF_ECHECS_MAX) {
            ESP_LOGE(TAG,
                     "reconfiguration ECHOUEE %d fois de suite — on CESSE "
                     "d'insister. ⛔ L'identite n'est PAS etablie : le driver "
                     "tiers n'a PAS ete appele, et c'est voulu (il briquerait la "
                     "carte sur un `abort()` sans console).",
                     s_reconf_echecs);
        }
        return false;
    }
    if (!ouvrir_driver(bus_rep)) {
        if (++s_reconf_echecs >= DN_CAPT_RECONF_ECHECS_MAX) {
            ESP_LOGE(TAG,
                     "reconfiguration ECHOUEE %d fois de suite — on CESSE d'insister "
                     "(chaque tentative fuit ~40 o dans le composant). Les cases "
                     "restent a « -- ». Reprise a la prochaine lecture valide, ou "
                     "`reboot`.",
                     s_reconf_echecs);
        }
        return false;
    }
    s_reconf_echecs = 0;
    ESP_LOGW(TAG, "capteur RECONFIGURE — le cycle courant est declare invalide, la "
                  "premiere conversion part d'une puce qu'on vient de reprogrammer");
    return false;
}

static void tache_capteurs(void *arg)
{
    (void)arg;
    TickType_t reveil = xTaskGetTickCount();

    while (1) {
        /* Cadence en TEMPS ABSOLU : vTaskDelayUntil ne dérive pas, contrairement
         * à un vTaskDelay qui ajouterait la durée de la mesure à chaque tour —
         * et la mesure dure des centaines de millisecondes. */
        vTaskDelayUntil(&reveil, pdMS_TO_TICKS(DN_CAPT_PERIODE_MS));

        /*
         * 🔴 dn4-3 (voie C, §13.19.4) — LES TROIS CAPTEURS D'ENVIRONNEMENT SONT
         * CADENCÉS ICI, ET LA POSITION DE CET APPEL N'EST PAS UN DÉTAIL DE STYLE.
         *
         * Le reste de cette boucle est truffé de `continue` sur chaque chemin
         * d'erreur du BME680. Un appel placé en FIN de corps serait donc SAUTÉ
         * à chaque erreur — c'est-à-dire précisément pendant la dégradation du
         * bus à froid (55,5 % d'erreurs mesurées, §13.17.1), le seul moment où
         * la tolérance qu'on prétend livrer se mesure.
         * ⇒ AVANT toute branche. La cadence de dn_env en devient DÉTERMINISTE,
         *   indépendante d'un BME680 qui peut bloquer jusqu'à 1 500 ms.
         *
         * ⛔ dn_env ne crée AUCUNE tâche et ne contient AUCUN `vTaskDelay` : son
         *   coût sur ce cycle est borné par ses timeouts I²C (100 ms).
         */
        dn_env_cycle();

        /* Bascule du gaz demandée à chaud (A/B de T9) : appliquée ICI, entre
         * deux cycles, jamais au milieu d'une conversion. */
        portENTER_CRITICAL(&s_mux);
        bool gaz_demande = s_gaz_demande;
        bool gaz_courant = s_gaz;
        portEXIT_CRITICAL(&s_mux);
        if (gaz_demande != gaz_courant && s_dev) {
            /*
             * ⚠️ LE GAZ TIENT DANS DEUX REGISTRES, PAS UN — et les deux comptent :
             *   · gas0 (0x70) porte `heater_disabled` — la plaque chauffante ;
             *   · gas1 (0x71) porte `gas_conversion_enabled` — la conversion.
             * Couper la conversion en laissant le chauffeur allumé chaufferait le
             * die pour RIEN, ce qui est exactement le biais qu'on cherche à
             * supprimer. Les deux se posent ensemble.
             *
             * ⚠️ LECTURE-MODIFICATION-ÉCRITURE, jamais une écriture sèche : ces
             * registres portent AUSSI `heater_setpoint` et le MSB du standby.
             * Écrire une union construite à la main les remettrait à zéro en
             * silence — le genre d'effet de bord qu'on ne voit que trois mesures
             * plus tard.
             */
            bme680_control_gas0_register_t g0;
            bme680_control_gas1_register_t g1;
            esp_err_t e0 = bme680_get_control_gas0_register(s_dev, &g0);
            esp_err_t e1 = bme680_get_control_gas1_register(s_dev, &g1);
            if (e0 == ESP_OK && e1 == ESP_OK) {
                g0.bits.heater_disabled = !gaz_demande;
                g1.bits.gas_conversion_enabled = gaz_demande;
                e0 = bme680_set_control_gas0_register(s_dev, g0);
                e1 = bme680_set_control_gas1_register(s_dev, g1);
            }
            if (e0 == ESP_OK && e1 == ESP_OK) {
                portENTER_CRITICAL(&s_mux);
                s_gaz = gaz_demande;
                portEXIT_CRITICAL(&s_mux);
                ESP_LOGW(TAG,
                         "chauffage gaz %s — ⚠️ la temperature met du temps a se "
                         "stabiliser : ne pas lire le delta sur le cycle suivant",
                         gaz_demande ? "ACTIVE (le die chauffe)" : "coupe");
            } else {
                portENTER_CRITICAL(&s_mux);
                s_gaz_demande = s_gaz; /* échec : on ne ment pas sur l'état */
                portEXIT_CRITICAL(&s_mux);
                ESP_LOGE(TAG, "bascule du chauffage gaz REFUSEE par le capteur "
                              "(gas0 %s, gas1 %s)",
                         esp_err_to_name(e0), esp_err_to_name(e1));
            }
        }

        /*
         * 🔴 CR 2026-08-17 — DEUX DÉFAUTS TOMBENT ICI, ET ILS SE COMPOSAIENT.
         *
         * (a) L'ancien `if (!s_dev) { continue; }` sautait AVANT tout
         *     `pousser_ui()`. Combiné au fait que `s_vive_texte[]` de dn_ui avait
         *     perdu son initialiseur `"--"`, les cases TEMP./HUMIDITE restaient
         *     **VIDES POUR TOUJOURS** quand le capteur était absent — pendant que
         *     `desknode_main.c` ET ce fichier journalisaient « les cases resteront
         *     « -- » ». Le firmware promettait l'inverse de ce qu'il faisait, sur
         *     le scénario même dont la story parle.
         * (b) L'init n'était tentée qu'une fois : un contact ouvert au boot
         *     condamnait le module jusqu'au reboot. Voir DN_CAPT_REINIT_CYCLES.
         */
        if (!s_dev) {
            pousser_ui(); /* les cases DISENT « -- » — c'est la promesse tenue */
            if (--s_cycles_avant_reinit <= 0) {
                s_cycles_avant_reinit = DN_CAPT_REINIT_CYCLES;
                i2c_master_bus_handle_t bus = dn_display_i2c_bus();
                /* 🔴 dn4-2 — L'ORDRE ETAIT INVERSE ICI, ET C'ETAIT PIRE QU'AU BOOT :
                 * `ouvrir_driver()` etait appele AVANT `relever_identite()`, donc
                 * le driver TIERS partait sans qu'AUCUNE verification ait eu lieu.
                 * ⇒ Meme un boot reussi pouvait se faire briquer a la reprise
                 * suivante, UNE MINUTE plus tard, par la meme perturbation.
                 * L'identite se releve MAINTENANT d'abord, et elle DECIDE. */
                relever_identite(bus); /* teste `bus` NULL lui-meme */
                /* 🔴 `dn4-41` / AC2 — LE SEUL SITE QUI ALIMENTE LE VERDICT.
                 * ⚠️ Il est DANS la branche de backoff, donc appele UNE FOIS
                 *    PAR MINUTE, ⛔ pas a chaque cycle de 5 s : c'est ce qui
                 *    donne au seuil de 2 sa valeur de 120 s (AC2.3).
                 * ⛔ Et il est APRES `relever_identite()`, jamais avant : le
                 *    verdict se prend sur la transaction QUI VIENT D'AVOIR
                 *    LIEU — *« on CONSTATE, on ne se souvient pas »*. */
                verdict_absence_maj();
                /* 🔴 CR dn4-2 — LE VERDICT NE SE REPUBLIE QUE QUAND IL CHANGE.
                 * `journaliser_identite()` est sorti de la branche de succes en
                 * dn4-2 : sur une carte sans capteur — ou apres un demarrage a
                 * froid, que §13.16.16 dit rate a chaque fois — il injectait donc
                 * son pave de 4 lignes TOUTES LES 60 s, indefiniment, DANS LE
                 * TRANSPORT PC. ⛔ Le REPL EST le transport, et la fragilite du
                 * pilote face aux lignes est deja au ledger. */
                uint16_t sig = identite_signature();
                if (sig != s_id_sig_publiee) {
                    s_id_sig_publiee = sig;
                    journaliser_identite();
                }
                if (identite_est_bme680()) {
                    if (ouvrir_driver(bus)) {
                        ESP_LOGW(TAG, "capteur REAPPARU — il ne repondait pas au "
                                      "boot. La lecture reprend au cycle suivant.");
                        s_id_sig_publiee = 0; /* la prochaine anomalie se redira */
                        /* 🔴 CR dn4-2 du 2026-08-24 — CE REARMEMENT MANQUAIT, ALORS
                         * QUE SON JUMEAU DE LA LIGNE AU-DESSUS EXISTAIT. Aucune
                         * ecriture `= false` n'existait dans le fichier => apres une
                         * PREMIERE recuperation, tout refus PERMANENT ulterieur de
                         * `bme680_init()` etait definitivement SILENCIEUX. C'est
                         * exactement le trou (« un echec d'ouverture PERMANENT s'y
                         * lisait comme un controle d'identite sain suivi de
                         * silence ») que le bloc ci-dessous a ete ecrit pour
                         * boucher — et qui se rouvrait des la 2e panne. */
                        s_reprise_echec_dit = false;
                    } else if (!s_reprise_echec_dit) {
                        /* 🔴 CR dn4-2 — LE 3e MESSAGE MANQUAIT ICI. Le chemin
                         * d'init en a un (« ouverture du driver refusee ») ; la
                         * reprise n'en avait pas, et un echec d'ouverture
                         * PERMANENT s'y lisait comme un controle d'identite sain
                         * suivi de silence. Dit UNE fois, pas toutes les minutes. */
                        s_reprise_echec_dit = true;
                        ESP_LOGE(TAG,
                                 "identite BONNE (chip id 0x%02X) mais "
                                 "`bme680_init()` REFUSE — ⛔ ce n'est PAS un "
                                 "probleme d'identite ni de cablage. Les cases "
                                 "restent a « -- ». Ce message ne se repetera pas.",
                                 s_chip_id);
                    }
                }
            }
            continue;
        }

        /* Faute injectée : elle emprunte EXACTEMENT les chemins d'erreur réels,
         * compteurs compris. Décrémentée ici, une fois par cycle.
         * ⚠️ La cause est capturée en LOCAL et transmise à qui en a besoin — voir
         *    l'en-tête de config_verifier_et_reparer(). */
        dn_capt_faute_t faute = DN_CAPT_FAUTE_AUCUNE;
        portENTER_CRITICAL(&s_mux);
        if (s_faute_restants > 0) {
            faute = s_faute;
            if (--s_faute_restants == 0) {
                s_faute = DN_CAPT_FAUTE_AUCUNE;
            }
        }
        int restants = s_faute_restants;
        portEXIT_CRITICAL(&s_mux);
        if (faute != DN_CAPT_FAUTE_AUCUNE && restants == 0) {
            ESP_LOGW(TAG, "faute simulee « %s » TERMINEE", dn_capt_faute_nom(faute));
        }
        if (faute == DN_CAPT_FAUTE_MUET) {
            s_degrade = true;
            portENTER_CRITICAL(&s_mux);
            s_cnt.err_i2c++;
            portEXIT_CRITICAL(&s_mux);
            pousser_ui();
            continue;
        }
        if (faute == DN_CAPT_FAUTE_BORNES) {
            s_degrade = true;
            portENTER_CRITICAL(&s_mux);
            s_cnt.err_bornes++;
            portEXIT_CRITICAL(&s_mux);
            pousser_ui();
            continue;
        }

        /* AVANT de croire la moindre valeur : le capteur est-il toujours celui
         * qu'on a configuré ? (voir l'en-tête de config_verifier_et_reparer) */
        if (!config_verifier_et_reparer(faute)) {
            pousser_ui(); /* les cases disent « -- » : on ne publie pas du faux */
            continue;
        }

        int64_t t0 = esp_timer_get_time();
        /* 🔴 `= {0}` AJOUTÉ EN REVUE DE CODE LE 2026-08-20. `bme680_get_data()`
         * ne remplit PAS tous les champs de score sur tous les chemins :
         * `bme680_compute_iaq()` laisse `gas_score` non assigné dans la bande
         * 9 000..13 500 Ω, et `humidity_score` non assigné dès que l'humidité
         * sort de 10..90 (sa dernière branche teste l'impossible
         * `adjusted_humi < 10 && adjusted_humi > 90`). ⇒ `d.iaq_score` pouvait
         * porter du RÉSIDU DE PILE, et la console le rendait en `%d`. */
        bme680_data_t d = {0};
        esp_err_t err = bme680_get_data(s_dev, &d);
        int64_t duree = esp_timer_get_time() - t0;

        if (err != ESP_OK) {
            s_degrade = true;
            /* ⚠️ DEUX SEAUX, PAS UN. Un échec de transport (NACK, bus occupé : le
             * capteur ne répond plus — fil, soudure) et un échec de donnée (il
             * répond mais la conversion n'arrive jamais) sont des diagnostics
             * OPPOSÉS. dn2-2 a payé pour l'avoir appris sur « tronquée » vs
             * « trop longue ». Le discriminant est la DURÉE — voir
             * DN_CAPT_SEUIL_POLL_US, et le symptôme qui l'a imposé. */
            bool poll_epuise =
                (err == ESP_ERR_TIMEOUT) && (duree >= DN_CAPT_SEUIL_POLL_US);
            portENTER_CRITICAL(&s_mux);
            if (poll_epuise) {
                s_cnt.err_donnee++;
            } else {
                s_cnt.err_i2c++;
            }
            portEXIT_CRITICAL(&s_mux);
            if (poll_epuise) {
                ESP_LOGW(TAG,
                         "conversion JAMAIS prete apres %lld ms — le capteur REPOND, "
                         "le cablage n'est pas en cause (err_donnee)",
                         (long long)(duree / 1000));
            }
            pousser_ui(); /* la péremption peut être passée : les cases doivent le dire */
            continue;
        }

        int t_dx = (int)lroundf(d.air_temperature * 10.0f);
        int h_dx = (int)lroundf(d.relative_humidity * 10.0f);

        /*
         * 🔴 dn4-3 — LA PRESSION CESSE D'ÊTRE JETÉE (X2 / AC6).
         *
         * Le BME680 la mesure à chaque cycle (P 1x) et ce module la JETAIT depuis
         * dn2-1, parce qu'aucun des six widgets du brief ne la portait. Le brief
         * la nomme pourtant comme TROISIÈME candidat à la 6ᵉ case, et — à la
         * différence du lux — elle vient du MÊME capteur que T et RH, donc elle
         * n'a PAS le conflit de verdict unique de `dn_ui_ambiance_maj()`.
         * ⚠️ Décision owner du 2026-08-20 : « mesure la pression d'abord, puis on
         *    tranche ». Elle est donc PUBLIÉE et INSTRUMENTÉE, ⛔ pas affichée.
         *
         * BORNES ET LEUR SOURCE (AC10) : Bosch BME680, plage de mesure
         * **300..1100 hPa**. ⛔ Hors plage, la pression seule devient ABSENTE —
         * elle NE FAIT PAS tomber la lecture T/H. C'est délibéré : cette story
         * ne doit pas pouvoir éteindre la seule case vivante pour une grandeur
         * qu'elle ne fait qu'instruire. ⇒ elle n'a donc PAS de seau à elle, et
         * si X2 la retient pour une case, il faudra lui en donner un.
         */
        float p_brut = d.barometric_pressure;
        /* 🔴 GARDE AJOUTÉE EN REVUE DE CODE LE 2026-08-20 : `p_brut` n'est PAS
         * borné ici (le test de plage vient plus bas), et sur débordement
         * `lroundf` rend `LONG_MIN` — soit exactement `INT32_MIN`, soit
         * `DN_CAPT_DX_ABSENT`. La brute aberrante devenait donc indistinguable
         * de « jamais lue », et `capteurs` imprimait « JAMAIS LUE » pour une
         * lecture QUI A EU LIEU : ça écrase la distinction à TROIS états que la
         * console vient d'être écrite pour créer. ⇒ on borne à ±(sentinelle+1). */
        int p_brut_dx;
        if (!isfinite(p_brut) || p_brut * 10.0f >= 2147483647.0f ||
            p_brut * 10.0f <= -2147483647.0f) {
            p_brut_dx = (p_brut > 0.0f) ? INT32_MAX : (DN_CAPT_DX_ABSENT + 1);
        } else {
            p_brut_dx = (int)lroundf(p_brut * 10.0f);
        }

        /*
         * 🔴 L'UNITÉ SE DÉTERMINE PAR LA MAGNITUDE, ET ELLE S'ANNONCE.
         * ⛔ Pas de division par 100 « parce que c'est sûrement des Pa » : les
         *    deux hypothèses ont des plages DISJOINTES (300..1100 contre
         *    30 000..110 000), donc la mesure tranche seule, sans ambiguïté.
         *    Si la valeur ne tombe dans NI l'une NI l'autre, on ne publie RIEN
         *    et on le DIT — ⛔ jamais une conversion au jugé.
         */
        dn_capt_p_unite_t unite = DN_CAPT_P_UNITE_ABERRANTE;
        int p_dx = DN_CAPT_DX_ABSENT;
        if (p_brut >= DN_CAPT_PRESSION_MIN_HPA &&
            p_brut <= DN_CAPT_PRESSION_MAX_HPA) {
            unite = DN_CAPT_P_UNITE_HPA;
            p_dx = p_brut_dx;
        } else if (p_brut >= DN_CAPT_PRESSION_MIN_HPA * 100.0f &&
                   p_brut <= DN_CAPT_PRESSION_MAX_HPA * 100.0f) {
            unite = DN_CAPT_P_UNITE_PA;
            /* Pa -> dixièmes de hPa : 101325 Pa => 10132 (1013,2 hPa) */
            p_dx = (int)lroundf(p_brut / 10.0f);
        }
        /* 🔴 CORRIGÉ EN REVUE DE CODE LE 2026-08-20, DEUX DÉFAUTS DANS UN TEST :
         *   (1) `unite != DN_CAPT_P_UNITE_INCONNUE` était DU CODE MORT — `unite`
         *       est initialisée à ABERRANTE et ne reçoit jamais qu'HPA ou PA ;
         *   (2) le verdict se figeait sur la PREMIÈRE lecture, ABERRANTE
         *       COMPRISE. Si la première conversion post-boot-à-froid rendait du
         *       n'importe quoi, le firmware journalisait une fois « ni des hPa
         *       ni des Pa » et n'annonçait JAMAIS l'unité correcte quand les
         *       lectures se stabilisaient — alors que l'annonce unique EST le
         *       livrable.
         * ⇒ une valeur ABERRANTE se journalise (une fois, pour le diagnostic)
         *   mais ⛔ NE VERROUILLE PAS le verdict : seule une unité RECONNUE le
         *   fait. */
        bool aberrante = (unite == DN_CAPT_P_UNITE_ABERRANTE);
        if (!s_pression_unite_dite && !(aberrante && s_pression_aberrante_dite)) {
            if (aberrante) {
                s_pression_aberrante_dite = true;
            } else {
                s_pression_unite_dite = true;
            }
            if (unite == DN_CAPT_P_UNITE_PA) {
                ESP_LOGW(TAG,
                         "pression : le driver annonce des HECTO-PASCALS "
                         "(bme680.h:363) mais rend %.1f — c'est du PASCAL. "
                         "L'etiquette MENT, la conversion est faite ici et elle "
                         "est ANNONCEE. Un facteur 100 pris en silence est "
                         "exactement ce qui a publie « 4 614,8 lx » pour 46 148.",
                         p_brut);
            } else if (unite == DN_CAPT_P_UNITE_ABERRANTE) {
                ESP_LOGW(TAG,
                         "pression : valeur BRUTE %.1f — ni des hPa (300..1100) "
                         "ni des Pa (30000..110000). ⛔ RIEN n'est publie, et "
                         "`capteurs` imprime la brute pour qu'on puisse la "
                         "diagnostiquer au lieu de la deviner.",
                         p_brut);
            } else {
                ESP_LOGI(TAG, "pression : unite HECTO-PASCAL confirmee par la "
                              "magnitude (%.1f) — le driver tient sa promesse.",
                         p_brut);
            }
        }

        if (t_dx < DN_CAPT_TEMP_MIN_DX || t_dx > DN_CAPT_TEMP_MAX_DX ||
            h_dx < DN_CAPT_HUM_MIN_DX || h_dx > DN_CAPT_HUM_MAX_DX) {
            s_degrade = true;
            portENTER_CRITICAL(&s_mux);
            s_cnt.err_bornes++;
            portEXIT_CRITICAL(&s_mux);
            /* ⚠️ CR 2026-08-17 : `abs()` était appliqué au dixième de température
             * mais PAS à celui d'humidité. Ce log ne se déclenche QUE sur une
             * valeur hors bornes, donc un h_dx négatif est l'entrée attendue :
             * il imprimait « -5,-5 % », la malformation même que dn_ui venait de
             * corriger. Les deux signes se traitent maintenant pareil. */
            ESP_LOGW(TAG, "valeurs hors plage physique : %d,%d C / %d,%d %% — rejetees",
                     t_dx / 10, abs(t_dx % 10), h_dx / 10, abs(h_dx % 10));
            pousser_ui();
            continue;
        }

        /* Une valeur valide part d'ici. Si on était dégradé ET qu'on avait déjà
         * lu au moins une fois, c'est une REPRISE — quelle qu'ait été la cause
         * (silence, valeur hors bornes, ou perte de configuration). */
        bool reprise = s_degrade && s_a_deja_lu;
        s_degrade = false;
        s_reconf_echecs = 0;

        int64_t maintenant = esp_timer_get_time();
        portENTER_CRITICAL(&s_mux);
        /* Cadence EFFECTIVE, celle qu'AC7 demande : l'écart réellement observé
         * entre deux lectures valides, pas la constante de compilation. Une tâche
         * qui dérive ou qui saute des cycles doit pouvoir se voir. */
        s_cadence_us = (s_lu_us >= 0) ? (maintenant - s_lu_us) : -1;
        s_temp_dx = t_dx;
        s_hum_dx = h_dx;
        s_pression_dx = p_dx;
        s_pression_brut_dx = p_brut_dx;
        /* ⚠️ Le composant ne remplit `gas_resistance` que si le chauffeur
         * tourne. Gaz coupe ⇒ ABSENT, ⛔ pas 0 : zero ohm serait une
         * valeur PHYSIQUE (un court-circuit), donc un mensonge plausible. */
        /* ⚠️ `s_gaz` et NON `gaz_courant` : ce dernier a été lu en TÊTE de cycle,
         * AVANT que la bascule demandée à chaud soit appliquée. L'utiliser ferait
         * publier ABSENT pendant tout le cycle qui vient d'allumer le chauffeur —
         * un trou d'un cycle qu'on lirait comme un capteur muet. */
        /* 🔴 `gas_valid` ET `heater_stable`, ⛔ PAS SEULEMENT NOTRE PROPRE
         * DEMANDE — corrigé en revue de code le 2026-08-20. `s_gaz` est le
         * drapeau de ce que l'OPÉRATEUR a demandé, ⛔ pas un état de mesure. Le
         * composant remplit `gas_valid` et `heater_stable` depuis les bits
         * d'état de l'ADC, et ni l'un ni l'autre n'était lu : au premier cycle
         * après `capteurs gaz on`, la plaque n'est pas à 300 °C, `adc_gas ≈ 0`,
         * et la compensation rend ~12,9 MΩ. Ce chiffre était imprimé ET poussé
         * dans W2, où il fixait le min/max de toute la fenêtre. */
        bool gaz_utilisable = s_gaz && d.gas_valid && d.heater_stable;
        s_gaz_ohms = gaz_utilisable ? (int)lroundf(d.gas_resistance)
                                    : DN_CAPT_DX_ABSENT;
        s_iaq_brut = gaz_utilisable ? (int)d.iaq_score : DN_CAPT_DX_ABSENT;
        s_gaz_attente = s_gaz && !gaz_utilisable;
        s_pression_unite = unite;
        s_lu_us = maintenant;
        s_cycle_us = duree;
        s_cnt.lectures++;
        s_a_deja_lu = true;
        if (reprise) {
            s_cnt.reprises++;
        }
        /* 🔴 `dn4-41` / AC2.4 — LE VERDICT EST REVERSIBLE, ET C'EST LE CHEMIN
         * LE PLUS FORT POUR LE RETIRER : une lecture de DONNEE vient d'aboutir.
         * ⛔ Un « absent » definitif serait exactement le defaut qu'a paye
         *   `dn2-1` (« les cases restaient VIDES a vie »). */
        bool sortait_absence = s_etait_absent;
        s_reouv_echecs = 0;
        s_etait_absent = false;
        portEXIT_CRITICAL(&s_mux);
        if (sortait_absence) {
            ESP_LOGW(TAG, "BME680 : n'est PLUS absent — une lecture de donnee a "
                          "abouti. Le verdict est retire.");
        }

        /* 🔴 W2 (AC6) — la pression est instrumentée DANS LES DEUX FORMATAGES
         * qu'elle pourrait recevoir, parce que c'est justement la précision qui
         * est en jeu (AC11 : ⛔ aucune décimale que la source ne porte).
         * Et la TEMPÉRATURE sert de TÉMOIN DE CONTRÔLE : c'est une grandeur
         * DÉJÀ AFFICHÉE dans une case livrée, donc son W2 dit ce que « bouger
         * assez » vaut sur cette carte, dans cette pièce. ⛔ Sans témoin, un
         * verdict W2 n'est qu'un nombre comparé à un seuil venu d'ailleurs. */
        if (p_dx != DN_CAPT_DX_ABSENT) {
            dn_w2_echantillon(DN_W2_PRESSION_ENT, (p_dx + 5) / 10);
            dn_w2_echantillon(DN_W2_PRESSION_DIX, p_dx);
        }
        dn_w2_echantillon(DN_W2_TEMPERATURE_DIX, t_dx);
        /* ⚠️ Echantillonnee SEULEMENT quand le chauffeur tourne : sinon on
         * compterait des absences comme des mesures, et l'instrument dirait
         * « ca ne bouge pas » d'un capteur qui n'est pas allume. */
        int g_ohms = dn_capt_gaz_ohms();
        if (g_ohms != DN_CAPT_DX_ABSENT) {
            /* En kilo-ohms : la resistance MOX va de ~5 000 a ~500 000 ohms, et
             * W2 juge la valeur AFFICHEE — personne n'afficherait 6 chiffres. */
            dn_w2_echantillon(DN_W2_GAZ_KOHM, g_ohms / 1000);
        }

        pousser_ui();
    }
}

esp_err_t dn_capteurs_init(void)
{
    i2c_master_bus_handle_t bus = dn_display_i2c_bus();
    if (!bus) {
        ESP_LOGE(TAG, "bus I2C absent — dn_display_init() n'a pas tourne");
        return ESP_ERR_INVALID_STATE;
    }

    relever_identite(bus);
    /* 🔴 `dn4-41` / AC2.3 — ⛔ LA TENTATIVE DU BOOT NE COMPTE PAS, ET C'EST LA
     * CONDITION MEME DE LA GARANTIE DES 120 s. A froid, **la lecture d'identite
     * echoue TOUJOURS** (A/B de six cycles, §13.17.1) et le bus se retablit
     * SEUL vers T+~60 s. La compter ferait tomber le verdict a 60 s au lieu de
     * 120 — sur un capteur SOUDE. ⛔ Ne pas ajouter `verdict_absence_maj()` ici. */
    journaliser_identite();

    /* Handle NU, ouvert AVANT le driver : il sert à relire les registres de
     * config sans passer par le driver, il doit survivre à une reconstruction de
     * s_dev, et `ouvrir_driver()` en a besoin pour relever sa référence. */
    i2c_device_config_t brut = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address = DN_BME680_ADDR,
        .scl_speed_hz = DN_I2C_FREQ_HZ,
    };
    if (i2c_master_bus_add_device(bus, &brut, &s_brut) != ESP_OK) {
        ESP_LOGW(TAG, "acces registre nu indisponible — la garde de "
                      "reconfiguration sera INERTE, et elle le dira");
        s_brut = NULL;
    }

    /* 🔴 dn4-2 : LE DRIVER TIERS N'EST PLUS APPELE SUR UNE IDENTITE NON ETABLIE.
     * `identite_est_bme680()` est FAUX aussi bien quand la lecture a echoue que
     * quand un autre composant a repondu — dans les DEUX cas, ouvrir le driver
     * revient a jouer a pile ou face avec un `abort()` (voir son docblock).
     * ⚠️ Et le repli existe DEJA et il est propre : cases a « -- », nouvelle
     * tentative toutes les minutes, `capteurs` qui explique. On l'emprunte. */
    if (!identite_est_bme680() || !ouvrir_driver(bus)) {
        /* ⚠️ NON FATAL, et la tâche démarre QUAND MÊME : elle publiera « -- »
         * dans les cases, retentera l'ouverture toutes les minutes, et `capteurs`
         * dira pourquoi. Un capteur muet ne doit pas priver l'opérateur de l'outil
         * qui explique son silence. */
        ESP_LOGE(TAG, "capteur INJOIGNABLE au boot (%s) — les cases afficheront "
                      "« -- » et une nouvelle tentative aura lieu toutes les %d s",
                 /* 🔴 CR dn4-2 du 2026-08-24 — CE SELECTEUR N'AVAIT QUE TROIS CAS
                  * ALORS QUE `journaliser_identite()` EN A QUATRE. Quand
                  * `i2c_master_bus_add_device` echoue — le scenario que le
                  * correctif nomme lui-meme — `journaliser_identite()` imprimait
                  * correctement « AUCUNE transaction n'a ete TENTEE », puis cet
                  * ESP_LOGE imprimait « identite NON LUE » trois lignes plus bas,
                  * SUR LE MEME BOOT : deux affirmations contradictoires, dont une
                  * est celle que le correctif existe pour supprimer. */
                 !s_id_tentee             ? "AUCUNE transaction TENTEE"
                 : !s_id_lue              ? "identite NON LUE"
                 : s_chip_id != DN_BME680_CHIP_ID ? "identite INATTENDUE"
                                          : "ouverture du driver refusee",
                 (DN_CAPT_REINIT_CYCLES * DN_CAPT_PERIODE_MS) / 1000);
        s_dev = NULL;
    } else {
        portENTER_CRITICAL(&s_mux);
        bool gaz = s_gaz;
        portEXIT_CRITICAL(&s_mux);
        ESP_LOGI(TAG,
                 "BME680 pret @ 0x%02X — %s, T/H %s, P %s, IIR %s, gaz %s, "
                 "cadence %d ms, peremption %lld ms",
                 DN_BME680_ADDR, DN_CAPT_MODE_TXT, DN_CAPT_OSR_TH_TXT,
                 DN_CAPT_OSR_P_TXT, DN_CAPT_IIR_TXT, gaz ? "ACTIF" : "coupe",
                 DN_CAPT_PERIODE_MS, (long long)(DN_CAPT_PEREMPTION_US / 1000));
        /* dn4-5/AC6.1 : ⛔ un retard qu'on connait et qu'on ne dit pas est un
         * mensonge d'interface. Il est DIT ici, a chaque demarrage du module. */
        ESP_LOGI(TAG, "  " DN_CAPT_RETARD_TXT);
        if (!DN_CAPT_GAZ_DEFAUT) {
            ESP_LOGI(TAG,
                     "  (gaz coupe DELIBEREMENT : sa plaque a 300 C chaufferait le "
                     "die qui porte le thermometre, pour une donnee hors des 6 "
                     "widgets du brief. A/B jouable a chaud : `capteurs gaz on`)");
        }
    }
    s_cycles_avant_reinit = DN_CAPT_REINIT_CYCLES;

    BaseType_t ok = xTaskCreate(tache_capteurs, "dn_capt", 4096, NULL, 3, NULL);
    if (ok != pdPASS) {
        /*
         * 🔴 CR 2026-08-17 — LE MÉNAGE EST FAIT, SINON LE MODULE MENT.
         * L'ancien chemin rendait ESP_ERR_NO_MEM en laissant `s_dev` non-NULL :
         * aucune tâche ne tournait, donc rien n'était jamais appliqué, mais
         * `dn_capt_set_gaz()` — qui ne teste que `s_dev` — répondait ESP_OK et la
         * console confirmait « chauffage gaz DEMANDE au prochain cycle », pour un
         * cycle qui n'arriverait jamais.
         */
        ESP_LOGE(TAG, "xTaskCreate a echoue — RAM interne insuffisante. Le module "
                      "se DESARME entierement : `capteurs` refusera au lieu "
                      "d'acquitter dans le vide.");
        if (s_dev) {
            bme680_delete(s_dev);
            s_dev = NULL;
        }
        if (s_brut) {
            i2c_master_bus_rm_device(s_brut);
            s_brut = NULL;
        }
        s_conf_dispo = false;
        s_conforme = false;
        return ESP_ERR_NO_MEM;
    }
    return ESP_OK;
}
