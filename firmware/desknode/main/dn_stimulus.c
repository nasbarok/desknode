#include "dn_stimulus.h"

#include <string.h>

#include "dn_display.h"
#include "dn_measure.h"
#include "dn_patterns.h"
#include "dn_pins.h"
#include "esp_log.h"
#include "esp_partition.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "dn_stim";

/* ═══════════════════════════════════════════════════════════════════════════
 * Stimulus de TEARING (AC5)
 * ═══════════════════════════════════════════════════════════════════════════
 * Deux images maximalement contrastées, basculées aussi vite que possible.
 * DEUX MODES, et le premier a été éliminé comme instrument principal :
 *
 *   `flip` — bascule NOIR plein / BLANC plein, la lecture littérale de l'AC.
 *     ⛔ ÉLIMINÉ comme instrument principal, avec son symptôme : à 33,6 Hz de
 *     bascule contre 37,40 Hz de rafraîchissement, l'écran « clignote
 *     violemment » et le papillotement MASQUE le déchirement qu'on cherche.
 *     L'observation rendue a été « je distingue une barre qui descend mais pas
 *     uniforme » — c'est-à-dire du tearing, mais noyé. Un instrument dont le
 *     bruit propre couvre le signal ne se garde pas. Il reste disponible parce
 *     qu'il correspond au texte de l'AC, et parce qu'il charge le pipeline de
 *     la même façon.
 *
 *   `on` (RETENU) — BARRE VERTICALE de 64 px qui balaie horizontalement, sur
 *     fond noir. C'est le test canonique du déchirement : quand la DMA change
 *     de contenu en cours de balayage, l'arête verticale de la barre se brise
 *     en TRANCHES horizontales décalées les unes des autres — un escalier, pas
 *     une barre. Le fond restant noir, il n'y a aucun papillotement plein
 *     écran pour masquer l'observation. La trame entière est redessinée à
 *     chaque pas, donc la charge sur le pipeline est la même.
 * ═══════════════════════════════════════════════════════════════════════════ */

static volatile bool s_tear_run;
static volatile dn_tear_mode_t s_tear_mode;
/* `s_tear_task` vaut NULL SI ET SEULEMENT SI aucune tâche de tearing ne vit.
 * C'est le témoin d'extinction : `s_tear_run = false` dit « on a DEMANDÉ
 * l'arrêt », pas « c'est arrêté ». Les deux ont été confondus, et ça coûtait
 * DEUX tâches simultanées — voir dn_stim_tear_start/stop plus bas. */
static TaskHandle_t s_tear_task;
/* ⚠️ HASARD CONNU, ARBITRÉ « DIFFÉRÉ » (pas corrigé) : `s_tear_hz` (double) et
 *    `s_tear_frame_us` (int64) sont écrits par la tâche de tearing sur le cœur
 *    1 et lus par la tâche console sur l'autre cœur. `volatile` empêche le
 *    compilateur de garder la valeur en registre, il n'apporte AUCUNE
 *    atomicité : sur Xtensa un 64 bits, c'est deux stores 32 bits, donc une
 *    ligne d'état peut afficher une valeur à moitié mise à jour. Conséquence
 *    bornée : un chiffre aberrant, isolé, dans un affichage d'état — jamais une
 *    corruption. La parade (portMUX ou lecture-relecture) n'a pas été prise
 *    pour ne pas ajouter de section critique dans la boucle qu'on mesure. Si un
 *    jour un Hz absurde apparaît dans une trace, c'est ICI qu'il faut regarder
 *    avant d'accuser la mesure. */
static volatile double s_tear_hz;
static volatile int64_t s_tear_frame_us;
/* Rendez-vous MANQUÉS (expiration des 100 ms), comptés par mode de
 * synchronisation. Sans ces compteurs, un `tear sync` dégradé se déroule
 * EXACTEMENT comme un `tear on` — même image, même cadence, même absence de
 * trace — et l'A/B compare « pas de sync » à « pas de sync » en croyant
 * comparer autre chose. Ils sont remontés dans la ligne d'arrêt. */
static volatile uint32_t s_tear_miss_vsync;
static volatile uint32_t s_tear_miss_fbdone;

#define DN_TEAR_BAR_W 64
/*
 * Pas de balayage, en px par trame.
 * ⚠️ VALAIT 27, avec la justification « premier avec 480 » — qui est FAUSSE :
 *    480 = 2^5 x 3 x 5 et 27 = 3^3, donc pgcd(27, 480) = 3. La barre ne
 *    visitait que 480/3 = 160 positions distinctes sur 480, et repassait
 *    indéfiniment par les mêmes — soit exactement le battement que le
 *    commentaire prétendait éviter.
 *    29 est premier et ne divise pas 480 : pgcd(29, 480) = 1, donc les 480
 *    colonnes sont TOUTES visitées avant que le motif ne se répète. C'est ce
 *    que la justification d'origine voulait dire.
 */
#define DN_TEAR_STEP 29

static void tear_task(void *arg)
{
    (void)arg;
    /* Deux compteurs distincts, et ce n'est pas du zèle : `frames` est remis à
     * zéro à chaque fenêtre d'une seconde pour calculer la cadence. S'en servir
     * aussi comme position ferait SAUTER la barre une fois par seconde — un
     * artefact de l'instrument qu'on prendrait pour une trame perdue. */
    uint32_t frames = 0; /* fenêtre de mesure de cadence */
    uint32_t step = 0;   /* position, monotone depuis le démarrage */
    int64_t t_window = esp_timer_get_time();

    while (s_tear_run) {
        int64_t t0 = esp_timer_get_time();
        uint16_t *buf = dn_display_draw_buffer();

        /* ── Générateur de trame ──────────────────────────────────────────
         * ⚠️ IL MESURAIT SA PROPRE LENTEUR. La version précédente remplissait
         *    le fond par `dn_pattern_fill()` — 307 200 stores 16 bits un par
         *    un — puis posait la barre avec un MODULO PAR PIXEL (~40 960
         *    modulos par trame), alors que `x0 + k` est borné par 479 + 64 =
         *    543 : l'enroulement ne peut toucher que les 64 dernières
         *    colonnes. Le chiffrage qui condamne cette version vient du
         *    firmware lui-même : un `memset` des mêmes 614 400 o est mesuré à
         *    23,5 ms, quand la cadence libre mesurée était de 28,9 Hz, soit
         *    34,6 ms par trame. Le goulot était le GÉNÉRATEUR, pas le pipeline
         *    d'affichage — et c'est le pipeline qu'AC5 prétend qualifier.
         *
         *    Deux corrections, aucune sur CE QUI est mesuré ni sur la
         *    structure de l'A/B :
         *      1. fond au `memset` ;
         *      2. barre découpée en AU PLUS DEUX segments contigus, le modulo
         *         sorti de la boucle interne.
         *
         *    ⚠️ `memset` écrit des OCTETS : il ne rend ces couleurs-ci que
         *       parce qu'elles sont à octets identiques (0x0000 -> 0x00,
         *       0xFFFF -> 0xFF). Toute couleur à octets différents (0xF800 par
         *       ex.) exigerait de remplir UNE ligne puis de la `memcpy` vers le
         *       bas — toujours bien plus rapide que le store par pixel, mais ce
         *       n'est pas ce code-ci.
         *
         *    ⚠️⚠️ CONSÉQUENCE SUR LES CHIFFRES DÉJÀ CONSIGNÉS : les cadences
         *       de hardware/ESP32-S3-Touch-LCD-2.8B-affichage.md §5.2
         *       (28,9 / 18,2 / 12,5 Hz) ont TOUTES été relevées avec le
         *       générateur LENT. Elles ne décrivent pas la carte, elles
         *       décrivent cette boucle-ci. ELLES SONT À REMESURER SUR LA
         *       CARTE — action owner ouverte. Ne pas les citer comme
         *       caractéristique de la dalle ni du pipeline tant que ce n'est
         *       pas refait. (Les lignes à 18,2 et 12,5 Hz cumulent en plus le
         *       défaut d'ordonnancement corrigé dans dn_measure.) */
        if (s_tear_mode == DN_TEAR_FLIP) {
            /* Bascule plein écran : fond et barre s'échangent à chaque pas. */
            uint8_t oct_fond = (step & 1) ? 0xFF : 0x00;
            uint8_t oct_barre = (step & 1) ? 0x00 : 0xFF;
            memset(buf, oct_fond, DN_FB_BYTES);
            int y = (int)((step * 23) % (DN_LCD_V_RES - 48));
            /* 48 lignes PLEINES et jointives : c'est un bloc contigu en
             * mémoire, donc un seul memset, pas 48. */
            memset(buf + (size_t)y * DN_LCD_H_RES, oct_barre,
                   (size_t)48 * DN_LCD_H_RES * sizeof(uint16_t));
        } else {
            /* Barre VERTICALE blanche qui balaie sur fond noir. L'arête
             * verticale est le détecteur : brisée en tranches => tearing. */
            int x0 = (int)((step * DN_TEAR_STEP) % DN_LCD_H_RES);
            memset(buf, 0x00, DN_FB_BYTES);
            /* Découpe en deux segments contigus : celui qui part de x0, et le
             * reste ENROULÉ à la colonne 0 quand la barre déborde à droite.
             * `w2` vaut 0 la plupart du temps. */
            int w1 = DN_TEAR_BAR_W;
            if (x0 + w1 > DN_LCD_H_RES) {
                w1 = DN_LCD_H_RES - x0;
            }
            int w2 = DN_TEAR_BAR_W - w1;
            for (int yy = 0; yy < DN_LCD_V_RES; yy++) {
                uint16_t *row = buf + (size_t)yy * DN_LCD_H_RES;
                memset(row + x0, 0xFF, (size_t)w1 * sizeof(uint16_t));
                if (w2 > 0) {
                    memset(row, 0xFF, (size_t)w2 * sizeof(uint16_t));
                }
            }
        }

        /* ── Les rendez-vous, et le VERDICT RETENU ────────────────────────
         * Ce bloc recommandait « les DEUX, chacun pris seul laisse un escalier
         * résiduel ». C'était l'inverse du verdict que tout le reste du dépôt
         * enregistre, et c'est corrigé ici :
         *
         *   - `fb_complete` SEUL (DN_TEAR_SYNC_FBDONE) est RETENU : escalier
         *     résiduel confiné aux ~15 % du haut, le meilleur des cinq ;
         *   - VSYNC seul (DN_TEAR_SYNC_VSYNC) : escalier sur la moitié de la
         *     barre — mieux que rien, moins bien que FBDONE ;
         *   - LES DEUX (DN_TEAR_SYNC_BOTH) est une RÉGRESSION MESURÉE :
         *     retour au niveau de VSYNC seul, et cadence effondrée. La branche
         *     est gardée UNIQUEMENT comme réfutation rejouable de l'intuition
         *     « deux barrières valent mieux qu'une » — jamais comme
         *     recommandation.
         *
         * Ce que chaque attente fait :
         *   1. VSYNC : place la bascule DANS le retour vertical, quand la
         *      dalle n'affiche rien — sinon le lien DMA change au milieu du
         *      balayage, `draw_bitmap` ne différant rien ;
         *   2. `on_frame_buf_complete` : décale la reprise du dessin d'une
         *      autre phase dans la trame. ⚠️ PAS « attend que la DMA ait fini
         *      de lire le tampon » — sur l'ESP32-S3 ce callback n'apporte pas
         *      cette garantie-là (démonstration et références IDF dans
         *      dn_measure.h). Le gain est observé, le mécanisme annoncé était
         *      faux.
         *
         * ⚠️ ARMER AVANT DE BASCULER : `dn_measure_arm_frame_done()` doit être
         *    appelé juste avant `dn_display_present()`, sans quoi c'est
         *    l'événement provoqué par NOTRE PROPRE bascule qu'on jette. */
        if (s_tear_mode == DN_TEAR_SYNC_VSYNC || s_tear_mode == DN_TEAR_SYNC_BOTH) {
            /* Rendez-vous manqué = ce tour de boucle s'est déroulé SANS
             * synchronisation. Silencieusement, dans la version précédente. */
            if (!dn_measure_wait_vsync(100)) {
                if (s_tear_miss_vsync == 0) {
                    ESP_LOGW(TAG,
                             "rendez-vous VSYNC MANQUÉ (100 ms) — cette trame "
                             "est passée SANS synchronisation. Une mesure qui "
                             "en accumule ne compare plus les modes annoncés.");
                }
                s_tear_miss_vsync++;
            }
        }
        if (s_tear_mode == DN_TEAR_SYNC_FBDONE || s_tear_mode == DN_TEAR_SYNC_BOTH) {
            dn_measure_arm_frame_done();
        }
        dn_display_present();
        if (s_tear_mode == DN_TEAR_SYNC_FBDONE || s_tear_mode == DN_TEAR_SYNC_BOTH) {
            if (!dn_measure_wait_frame_done(100)) {
                if (s_tear_miss_fbdone == 0) {
                    ESP_LOGW(TAG,
                             "rendez-vous fin-de-trame MANQUÉ (100 ms) — cette "
                             "trame est passée SANS synchronisation. Compté ; "
                             "le total sort dans la ligne d'arrêt.");
                }
                s_tear_miss_fbdone++;
            }
        }
        s_tear_frame_us = esp_timer_get_time() - t0;
        step++;
        frames++;

        int64_t now = esp_timer_get_time();
        if (now - t_window >= 1000000) {
            s_tear_hz = (double)frames * 1000000.0 / (double)(now - t_window);
            frames = 0;
            t_window = now;
        }
        /* Un yield de 1 tick (1 ms à CONFIG_FREERTOS_HZ=1000) : sans lui, la
         * tâche affamerait le watchdog de son cœur. C'est le seul frein — la
         * cadence reste dominée par le temps de remplissage. */
        vTaskDelay(1);
    }
    s_tear_task = NULL;
    vTaskDelete(NULL);
}

esp_err_t dn_stim_tear_start(dn_tear_mode_t mode)
{
    /* ⚠️ LA GARDE PORTE SUR `dn_stim_tear_running()`, PAS SUR `s_tear_run`.
     *    Le scénario que ça ferme, et qui était ouvert : `tear off` remet
     *    `s_tear_run` à false et rend la main même si la tâche n'est pas encore
     *    sortie (elle peut mettre plus d'une seconde à re-tester sa condition,
     *    voir plus bas). Un `tear on` immédiat repassait alors la garde,
     *    remettait `s_tear_run = true` AVANT que l'ancienne tâche ne re-teste
     *    son `while`, et ÉCRASAIT `s_tear_task` avec le handle de la nouvelle.
     *    Résultat : DEUX tâches redessinant le même framebuffer pour toujours,
     *    `s_tear_hz` qui ne veut plus rien dire, et tous les `tear off`
     *    suivants qui rendent la main aussitôt puisque la première tâche à
     *    sortir met le handle à NULL. */
    if (dn_stim_tear_running()) {
        return ESP_ERR_INVALID_STATE;
    }
    s_tear_run = true;
    s_tear_mode = mode;
    s_tear_hz = 0.0;
    s_tear_miss_vsync = 0;
    s_tear_miss_fbdone = 0;
    if (xTaskCreatePinnedToCore(tear_task, "dn_tear", 4096, NULL, 4, &s_tear_task,
                                1) != pdPASS) {
        s_tear_run = false;
        s_tear_task = NULL; /* xTaskCreate* ne garantit pas le handle en échec */
        return ESP_ERR_NO_MEM;
    }
    ESP_LOGI(TAG,
             "stimulus TEARING démarré (num_fbs=%d). Écrire dans le "
             "framebuffer VISIBLE (num_fbs=1) est le TÉMOIN POSITIF : le "
             "déchirement DOIT s'y voir, sinon l'instrument est invalide.",
             dn_display_num_fbs());
    return ESP_OK;
}

/* Budget d'attente de la sortie d'une tâche de stimulus (tearing ET flash).
 * Le pire cas n'est pas théorique : sous le stimulus FLASH d'AC6, le cache est
 * coupé pendant les effacements, et UN tour de la boucle de tearing peut coûter
 * wait_vsync(100 ms) + present() + wait_frame_done(100 ms), plus le temps
 * pendant lequel l'effacement l'a suspendue. L'ancien budget de 1 s
 * (200 x 5 ms) pouvait donc expirer sur une boucle parfaitement saine — et il
 * expirait EN SILENCE, ce qui est le vrai défaut. */
#define DN_STIM_STOP_TRIES 600 /* x 5 ms = 3 s */

esp_err_t dn_stim_tear_stop(void)
{
    if (!dn_stim_tear_running()) {
        return ESP_OK;
    }
    s_tear_run = false;
    /* Attendre la sortie EFFECTIVE de la tâche : sinon un `scene x` juste après
     * écraserait l'écran pendant que la tâche dessine encore.
     * ⚠️ ET TESTER LE RÉSULTAT DE L'ATTENTE. Cette boucle existait déjà, mais
     *    personne ne regardait si elle avait abouti : on journalisait « arrêté »
     *    quoi qu'il arrive, et `dn_stim_tear_running()` répondait false alors
     *    qu'une tâche continuait à dessiner. C'est le premier maillon du
     *    scénario à deux tâches décrit dans `dn_stim_tear_start()`. */
    for (int i = 0; i < DN_STIM_STOP_TRIES && s_tear_task; i++) {
        vTaskDelay(pdMS_TO_TICKS(5));
    }
    if (s_tear_task) {
        ESP_LOGE(TAG,
                 "stimulus TEARING : la tâche n'est PAS sortie au bout de "
                 "%d ms — elle dessine peut-être encore. NE PAS conclure sur "
                 "l'image affichée, et ne pas relancer `tear` : le démarrage "
                 "sera refusé tant que la tâche vit.",
                 DN_STIM_STOP_TRIES * 5);
        return ESP_ERR_TIMEOUT;
    }
    ESP_LOGI(TAG,
             "stimulus TEARING arrêté (cadence atteinte : %.1f Hz ; "
             "rendez-vous manqués : %lu VSYNC, %lu fin-de-trame)",
             s_tear_hz, (unsigned long)s_tear_miss_vsync,
             (unsigned long)s_tear_miss_fbdone);
    if (s_tear_miss_vsync || s_tear_miss_fbdone) {
        ESP_LOGW(TAG,
                 "⚠️ des rendez-vous ont été MANQUÉS : ces trames-là sont "
                 "passées SANS synchronisation. Un A/B qui en contient compare "
                 "peut-être « pas de sync » à « pas de sync ».");
    }
    return ESP_OK;
}

/* ⚠️ « en cours » = la TÂCHE VIT, pas « on a demandé le démarrage ».
 *    Pendant l'extinction (`s_tear_run == false` mais tâche encore vivante) on
 *    répond donc TRUE, et c'est voulu : la tâche dessine encore, donc `scene x`
 *    doit toujours être refusé et un nouveau `tear on` aussi.
 *    Fenêtre résiduelle assumée : entre `s_tear_task = NULL` et le
 *    `vTaskDelete(NULL)` qui suit immédiatement, la tâche existe encore mais on
 *    répond false. Elle ne touche plus au framebuffer dans cet intervalle. */
bool dn_stim_tear_running(void) { return s_tear_run || s_tear_task != NULL; }

void dn_stim_tear_stats(double *out_hz, int64_t *out_frame_us)
{
    if (out_hz) {
        *out_hz = s_tear_hz;
    }
    if (out_frame_us) {
        *out_frame_us = s_tear_frame_us;
    }
}

void dn_stim_tear_misses(uint32_t *out_vsync, uint32_t *out_fbdone)
{
    if (out_vsync) {
        *out_vsync = s_tear_miss_vsync;
    }
    if (out_fbdone) {
        *out_fbdone = s_tear_miss_fbdone;
    }
}

/* ═══════════════════════════════════════════════════════════════════════════
 * Stimulus d'ÉCRITURE FLASH (AC6)
 * ═══════════════════════════════════════════════════════════════════════════
 * Flash et PSRAM partagent le contrôleur : toute écriture flash suspend le
 * cache, donc le refill de la DMA d'affichage. C'est le mécanisme annoncé du
 * scintillement.
 *
 * ⛔ On écrit EXCLUSIVEMENT dans la partition `stimulus`, sous-type 0x41,
 *    prévue pour être sacrifiée. Ni `nvs` (dont la corruption coûterait un
 *    reflash complet), ni `factory`.
 * ═══════════════════════════════════════════════════════════════════════════ */

static volatile bool s_flash_run;
static TaskHandle_t s_flash_task;
static volatile uint32_t s_flash_sectors;
/* ⚠️ MÊME HASARD QUE POUR `s_tear_hz` / `s_tear_frame_us`, MÊME ARBITRAGE
 *    « DIFFÉRÉ » : `s_flash_bytes` (uint64) et `s_flash_rate` (double) sont
 *    écrits par la tâche flash sur le cœur 0 et lus par la console sur l'autre
 *    cœur. `volatile` n'apporte pas l'atomicité : sur Xtensa un 64 bits, c'est
 *    deux stores 32 bits, donc `flash` peut afficher un total à moitié mis à
 *    jour. Non corrigé sciemment — le coût (section critique dans la boucle
 *    d'écriture flash, celle-là même qui coupe le cache) dépasse celui du
 *    symptôme : un chiffre isolé et aberrant dans une ligne d'état. */
static volatile uint64_t s_flash_bytes;
static volatile double s_flash_rate;
/* Dernière cause d'arrêt. Distingue « arrêté par `flash off` » de « arrêté
 * parce que la flash a refusé une écriture » — deux états que la ligne d'état
 * rendait identiques, alors que le second invalide la mesure en cours. */
static volatile esp_err_t s_flash_err;

#define DN_STIM_SECTOR 4096

static void flash_task(void *arg)
{
    (void)arg;
    const esp_partition_t *part = esp_partition_find_first(
        ESP_PARTITION_TYPE_DATA, (esp_partition_subtype_t)0x41, "stimulus");
    if (!part) {
        ESP_LOGE(TAG, "partition « stimulus » introuvable — stimulus flash annulé");
        /* Ce chemin-ci faisait déjà le ménage correctement ; c'est le chemin
         * d'erreur de la BOUCLE, plus bas, qui l'oubliait. */
        s_flash_err = ESP_ERR_NOT_FOUND;
        s_flash_run = false;
        s_flash_task = NULL;
        vTaskDelete(NULL);
        return;
    }

    static uint8_t motif[DN_STIM_SECTOR];
    for (int i = 0; i < DN_STIM_SECTOR; i++) {
        motif[i] = (uint8_t)(i * 7 + 3);
    }

    size_t offset = 0;
    int64_t t_window = esp_timer_get_time();
    uint64_t bytes_window = 0;

    ESP_LOGI(TAG,
             "stimulus FLASH démarré : effacement+écriture de secteurs de "
             "%d o, en boucle, sur la partition « stimulus » (%lu o à "
             "0x%06lx), sans pause entre deux secteurs.",
             DN_STIM_SECTOR, (unsigned long)part->size,
             (unsigned long)part->address);

    while (s_flash_run) {
        esp_err_t err = esp_partition_erase_range(part, offset, DN_STIM_SECTOR);
        if (err == ESP_OK) {
            err = esp_partition_write(part, offset, motif, DN_STIM_SECTOR);
        }
        if (err != ESP_OK) {
            /* ⚠️ SORTIE EN ERREUR — et il FAUT lever `s_flash_run` ici.
             *    Sans ça, la tâche mourait quelques lignes plus bas en laissant
             *    le drapeau à true : `flash` annonçait « EN COURS » alors que
             *    plus rien n'écrivait, et `flash on` répondait
             *    ESP_ERR_INVALID_STATE sans qu'on puisse relancer. C'est-à-dire
             *    qu'on recréait par un chemin d'erreur le piège méthodologique
             *    même que la story a consigné : conclure sur un écran pendant
             *    qu'un stimulus supposé actif ne tournait pas. */
            ESP_LOGE(TAG,
                     "écriture flash à 0x%x refusée : %s — STIMULUS ARRÊTÉ. "
                     "Toute observation faite après cet instant est faite SANS "
                     "écriture flash : ne pas la porter au crédit d'AC6.",
                     (unsigned)offset, esp_err_to_name(err));
            s_flash_err = err;
            s_flash_run = false;
            break;
        }
        s_flash_sectors++;
        s_flash_bytes += DN_STIM_SECTOR;
        bytes_window += DN_STIM_SECTOR;

        offset += DN_STIM_SECTOR;
        if (offset + DN_STIM_SECTOR > part->size) {
            offset = 0;
        }

        int64_t now = esp_timer_get_time();
        if (now - t_window >= 1000000) {
            s_flash_rate = (double)bytes_window * 1000000.0 / (double)(now - t_window);
            bytes_window = 0;
            t_window = now;
        }
        /* 1 tick de répit : les tâches de moindre priorité doivent pouvoir
         * tourner, sinon c'est le watchdog qui interrompt la mesure. */
        vTaskDelay(1);
    }
    /* Sortie NORMALE comme sortie EN ERREUR passent ici : dans les deux cas
     * `s_flash_run` est déjà false — la sortie normale parce que
     * `dn_stim_flash_stop()` l'a levé, la sortie en erreur parce que la branche
     * d'erreur ci-dessus le lève elle-même. Aucun chemin ne laisse plus le
     * stimulus « EN COURS » alors qu'il est mort. */
    s_flash_run = false;
    s_flash_task = NULL;
    vTaskDelete(NULL);
}

esp_err_t dn_stim_flash_start(void)
{
    if (dn_stim_flash_running()) {
        return ESP_ERR_INVALID_STATE;
    }
    s_flash_run = true;
    s_flash_sectors = 0;
    s_flash_bytes = 0;
    s_flash_rate = 0.0;
    s_flash_err = ESP_OK;
    if (xTaskCreatePinnedToCore(flash_task, "dn_flash", 4096, NULL, 3,
                                &s_flash_task, 0) != pdPASS) {
        s_flash_run = false;
        s_flash_task = NULL;
        return ESP_ERR_NO_MEM;
    }
    return ESP_OK;
}

void dn_stim_flash_stop(void)
{
    if (!dn_stim_flash_running()) {
        /* Déjà arrêté. Si c'est une ERREUR qui l'a arrêté, le redire ici : un
         * `flash off` muet laisserait croire à un arrêt normal, et donc à une
         * observation faite sous stimulus. */
        if (s_flash_err != ESP_OK) {
            ESP_LOGE(TAG,
                     "stimulus FLASH déjà arrêté EN ERREUR (%s) après %lu "
                     "secteurs — les observations postérieures ont été faites "
                     "SANS écriture flash.",
                     esp_err_to_name(s_flash_err),
                     (unsigned long)s_flash_sectors);
        }
        return;
    }
    s_flash_run = false;
    /* Même défaut que côté tearing : la boucle d'attente existait, son résultat
     * n'était pas testé. Ici on le teste. */
    for (int i = 0; i < DN_STIM_STOP_TRIES && s_flash_task; i++) {
        vTaskDelay(pdMS_TO_TICKS(5));
    }
    if (s_flash_task) {
        ESP_LOGE(TAG,
                 "stimulus FLASH : la tâche n'est PAS sortie au bout de %d ms "
                 "— elle écrit peut-être encore. Ne pas conclure « sans "
                 "stimulus » sur ce qui suit.",
                 DN_STIM_STOP_TRIES * 5);
        return;
    }
    ESP_LOGI(TAG,
             "stimulus FLASH arrêté : %lu secteurs, %llu o écrits, "
             "débit soutenu %.0f o/s",
             (unsigned long)s_flash_sectors, (unsigned long long)s_flash_bytes,
             s_flash_rate);
    if (s_flash_err != ESP_OK) {
        ESP_LOGE(TAG, "…et il s'était arrêté EN ERREUR : %s",
                 esp_err_to_name(s_flash_err));
    }
}

/* Même convention que pour le tearing : « en cours » = la TÂCHE VIT. */
bool dn_stim_flash_running(void) { return s_flash_run || s_flash_task != NULL; }

esp_err_t dn_stim_flash_error(void) { return s_flash_err; }

void dn_stim_flash_stats(uint32_t *out_sectors, uint64_t *out_bytes,
                         double *out_bytes_per_s)
{
    if (out_sectors) {
        *out_sectors = s_flash_sectors;
    }
    if (out_bytes) {
        *out_bytes = s_flash_bytes;
    }
    if (out_bytes_per_s) {
        *out_bytes_per_s = s_flash_rate;
    }
}
