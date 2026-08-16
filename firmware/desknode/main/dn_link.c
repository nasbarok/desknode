/*
 * dn_link — réception et état de la liaison PC (dn2-2). Voir dn_link.h pour le
 * protocole complet et la doctrine de rejet.
 *
 * ── QUI ÉCRIT, QUI LIT — et pourquoi un spinlock et pas « volatile suffit » ──
 * L'ingestion tourne dans la tâche du transport (REPL console en branche A,
 * httpd en branche B) ; la poussée vers l'UI tourne dans la tâche dn_link ; la
 * console (`pc`) lit depuis la tâche REPL. Les COMPTEURS sont des uint32
 * (doctrine du dépôt : pas d'atomicité 64 bits inter-cœurs sur Xtensa), mais
 * l'horodatage de réception est un int64 d'esp_timer : sa lecture PEUT être
 * déchirée entre deux cœurs. D'où le portMUX autour du petit état partagé —
 * quelques dizaines de cycles, pas de travail long dessous, jamais le verrou
 * LVGL en même temps.
 */

#include "dn_link.h"

#include <string.h>

#include "esp_log.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include "dn_ui.h"

static const char *TAG = "dn_link";

static portMUX_TYPE s_mux = portMUX_INITIALIZER_UNLOCKED;

/* Compteurs : uint32, un seul écrivain par cause (la tâche du transport actif
 * pour les rejets, la tâche dn_link pour les reprises). */
static dn_link_compteurs_t s_cnt;

/* Le dernier état valide reçu — TOUT accès sous s_mux (int64 déchirable). */
static int s_valeur = -1;      /* dixièmes de %, -1 = jamais reçu */
static int64_t s_recu_us = -1; /* esp_timer_get_time() à l'acceptation */
static uint32_t s_seq;
/* ⚠️ DISTINCT de `s_recu_us < 0` (correctif de revue 2026-08-16). Le suivi du seq
 * et l'existence d'une valeur sont deux choses : `pc reset` OUBLIE le seq sans
 * tuer la liaison en cours, pour qu'une campagne relancée avec la trame d'exemple
 * du dépôt ne tombe pas en doublon et ne mesure pas du vide. */
static bool s_seq_connu;
static uint32_t s_t_ms;

/* Latence acceptation→label posé, alimentée par la tâche, lue par `pc`. */
static uint32_t s_lat_n;
static int64_t s_lat_min, s_lat_max, s_lat_somme;

/*
 * Le gabarit parse_entier() de dn_console, transposé aux champs de trame :
 * distinguer 0 d'une erreur (⛔ atoi ne le fait pas — règle du dépôt), refuser
 * tout octet non décimal, refuser le débordement au lieu d'écrêter en silence.
 * Champs non signés et bornés par construction : pas de signe accepté.
 */
static bool parse_u32_strict(const char *s, uint32_t *out)
{
    if (*s == '\0') {
        return false; /* champ VIDE ≠ zéro */
    }
    uint64_t v = 0;
    for (const char *p = s; *p; p++) {
        if (*p < '0' || *p > '9') {
            return false;
        }
        v = v * 10 + (uint64_t)(*p - '0');
        if (v > UINT32_MAX) {
            return false;
        }
    }
    *out = (uint32_t)v;
    return true;
}

static int hex_val(char c)
{
    if (c >= '0' && c <= '9') {
        return c - '0';
    }
    if (c >= 'A' && c <= 'F') {
        return c - 'A' + 10;
    }
    /* Minuscules refusées : l'agent émet en MAJUSCULES, un « 2a » est du bruit. */
    return -1;
}

bool dn_link_ingest_ligne(const char *ligne)
{
    size_t len = strlen(ligne);
    if (len > DN_LINK_LIGNE_MAX) {
        /* COMPLÈTE mais trop longue — PAS « tronquée ». Diagnostic opposé : ici
         * l'émetteur envoie plus large (v2, métrique en plus), là le transport a
         * perdu la fin. Le REPL laisse passer 128 caractères, la plage 64..128
         * est donc atteignable (correctif de revue 2026-08-16). */
        s_cnt.rejets_trop_longue++;
        return false;
    }
    if (strncmp(ligne, "$DN,", 4) != 0) {
        s_cnt.rejets_format++;
        return false;
    }

    /* La queue « *CK » d'abord : une trame coupée a perdu sa fin — c'est LE
     * symptôme « tronquée », compté à part du simple champ illisible. */
    const char *etoile = strrchr(ligne, '*');
    if (etoile == NULL) {
        s_cnt.rejets_tronquee++;
        return false;
    }
    if (etoile[1] == '\0' || etoile[2] == '\0' || etoile[3] != '\0') {
        s_cnt.rejets_tronquee++; /* « *4 » ou « *4A7 » : queue mutilée */
        return false;
    }
    int hi = hex_val(etoile[1]);
    int lo = hex_val(etoile[2]);
    if (hi < 0 || lo < 0) {
        s_cnt.rejets_format++;
        return false;
    }
    uint8_t ck = 0;
    for (const char *p = ligne + 1; p < etoile; p++) {
        ck ^= (uint8_t)*p;
    }
    if (ck != (uint8_t)(hi * 16 + lo)) {
        s_cnt.rejets_checksum++;
        return false;
    }

    /* Découpe du corps en champs. À la main et pas strtok : strtok FUSIONNE les
     * séparateurs consécutifs, donc « ,, » (champ absent) lui serait invisible. */
    char corps[DN_LINK_LIGNE_MAX + 1];
    size_t clen = (size_t)(etoile - (ligne + 1));
    memcpy(corps, ligne + 1, clen);
    corps[clen] = '\0';

    enum { NB_CHAMPS = 6 }; /* DN · ver · seq · t_ms · cpu · dixiemes */
    char *champ[NB_CHAMPS];
    int n = 0;
    champ[n++] = corps;
    for (char *p = corps; *p; p++) {
        if (*p == ',') {
            *p = '\0';
            if (n == NB_CHAMPS) {
                s_cnt.rejets_format++; /* champ EN TROP */
                return false;
            }
            champ[n++] = p + 1;
        }
    }
    if (n != NB_CHAMPS) {
        s_cnt.rejets_format++; /* champ ABSENT */
        return false;
    }

    /* La VERSION se juge avant tout le reste : une version inconnue n'est
     * jamais interprétée à moitié, même si ses champs ont l'air familiers. */
    uint32_t ver;
    if (!parse_u32_strict(champ[1], &ver)) {
        s_cnt.rejets_format++;
        return false;
    }
    if (ver != DN_LINK_PROTO_VERSION) {
        s_cnt.rejets_version++;
        return false;
    }

    uint32_t seq, t_ms, dixiemes;
    if (!parse_u32_strict(champ[2], &seq) || !parse_u32_strict(champ[3], &t_ms)) {
        s_cnt.rejets_format++;
        return false;
    }
    if (strcmp(champ[4], "cpu") != 0) {
        s_cnt.rejets_format++; /* métrique inconnue en v1 — dn4-1 versionnera */
        return false;
    }
    if (!parse_u32_strict(champ[5], &dixiemes)) {
        s_cnt.rejets_format++;
        return false;
    }
    if (dixiemes > 1000) {
        s_cnt.rejets_bornes++;
        return false;
    }

    portENTER_CRITICAL(&s_mux);
    bool premiere = !s_seq_connu;
    if (!premiere && seq == s_seq) {
        portEXIT_CRITICAL(&s_mux);
        s_cnt.doublons++; /* valeur IGNORÉE : rejouer un seq n'est pas une donnée */
        return false;
    }
    /* Le trou de seq, en arithmétique NON SIGNÉE et BORNÉE (correctif de revue
     * 2026-08-16). L'ancien test `seq > s_seq + 1` avait deux défauts atteignables
     * en UNE commande depuis l'injecteur `pc` : (1) `s_seq + 1` déborde quand
     * s_seq vaut UINT32_MAX, et toute trame suivante était alors comptée en trou,
     * pour toujours ; (2) une seule trame à seq géant faisait bondir pertes_seq de
     * ~4 milliards, rendant illisible le compteur d'une campagne AC2.
     *
     * ⚠️ ET CE QU'IL NE FAUT SURTOUT PAS FAIRE : REJETER la trame. Un agent qui
     * redémarre repart à seq=1, donc en saut ARRIÈRE — la refuser condamnerait la
     * reprise sans reboot d'AC7, que cette même story vient de prouver. Une trame
     * dont le checksum, la version et les bornes sont bons EST une donnée : on
     * l'applique, on ne lui invente pas 4 milliards de pertes, et on compte
     * l'événement pour qu'il soit lisible.
     * Non signé ⇒ un saut arrière donne une valeur énorme, donc > SAUT_MAX : les
     * deux cas (redémarrage, seq fabriqué) tombent au même endroit, et c'est juste. */
    uint32_t saut = premiere ? 1u : seq - s_seq;
    if (saut > DN_LINK_SAUT_MAX) {
        s_cnt.resynchros++; /* nouvelle session d'émetteur — PAS des pertes */
    } else if (saut > 1u) {
        s_cnt.pertes_seq += saut - 1u; /* diagnostic — la cadence ne fait pas foi */
    }
    s_seq_connu = true;
    s_valeur = (int)dixiemes;
    s_seq = seq;
    s_t_ms = t_ms;
    s_recu_us = esp_timer_get_time();
    portEXIT_CRITICAL(&s_mux);
    s_cnt.recues++;
    return true;
}

/* ── Accès à l'état ──────────────────────────────────────────────────────── */

static void etat_brut(int *valeur, int64_t *recu_us, uint32_t *seq, uint32_t *t_ms)
{
    portENTER_CRITICAL(&s_mux);
    if (valeur) {
        *valeur = s_valeur;
    }
    if (recu_us) {
        *recu_us = s_recu_us;
    }
    if (seq) {
        *seq = s_seq;
    }
    if (t_ms) {
        *t_ms = s_t_ms;
    }
    portEXIT_CRITICAL(&s_mux);
}

dn_link_etat_t dn_link_etat(void)
{
    int64_t recu;
    etat_brut(NULL, &recu, NULL, NULL);
    if (recu < 0) {
        return DN_LINK_JAMAIS;
    }
    return (esp_timer_get_time() - recu) < DN_LINK_PEREMPTION_US ? DN_LINK_VIVANTE
                                                                 : DN_LINK_MORTE;
}

const char *dn_link_etat_nom(dn_link_etat_t e)
{
    switch (e) {
    case DN_LINK_JAMAIS:
        return "jamais recue";
    case DN_LINK_VIVANTE:
        return "VIVANTE";
    case DN_LINK_MORTE:
        return "MORTE";
    default:
        return "?";
    }
}

int dn_link_valeur_dixiemes(void)
{
    int v;
    etat_brut(&v, NULL, NULL, NULL);
    return v;
}

int64_t dn_link_age_us(void)
{
    int64_t recu;
    etat_brut(NULL, &recu, NULL, NULL);
    return (recu < 0) ? -1 : esp_timer_get_time() - recu;
}

uint32_t dn_link_derniere_seq(void)
{
    uint32_t s;
    etat_brut(NULL, NULL, &s, NULL);
    return s;
}

uint32_t dn_link_dernier_t_ms(void)
{
    uint32_t t;
    etat_brut(NULL, NULL, NULL, &t);
    return t;
}

void dn_link_compteurs(dn_link_compteurs_t *out)
{
    *out = s_cnt; /* uint32 : chaque champ est atomique, la photo peut mélanger
                   * deux instants — assumé, comme les autres compteurs du dépôt */
}

void dn_link_compter_rejet(dn_link_rejet_t cause)
{
    /* Les chemins d'AVANT dn_link : le REPL a déjà découpé ou mutilé la ligne.
     * Sans ces incréments, « chaque cas est COMPTÉ » était faux par omission
     * (correctif de revue 2026-08-16). */
    portENTER_CRITICAL(&s_mux);
    if (cause == DN_LINK_REJET_TRONQUEE) {
        s_cnt.rejets_tronquee++;
    } else {
        s_cnt.rejets_format++;
    }
    portEXIT_CRITICAL(&s_mux);
}

void dn_link_reset_compteurs(void)
{
    /* ⚠️ TOUT sous le verrou (correctif de revue 2026-08-16). Le memset était fait
     * DEHORS : pendant ces 40 octets, la tâche dn_link (s_cnt.reprises++) et la
     * tâche du transport (s_cnt.rejets_*++) pouvaient être en lecture-modification-
     * écriture sur le même champ, depuis l'autre cœur. Résultat possible : un
     * compteur qui repart à 1 au lieu de 0, ou une valeur d'avant-reset ressuscitée
     * — une campagne AC2 faussée d'un cran, sans aucun signe. */
    portENTER_CRITICAL(&s_mux);
    memset(&s_cnt, 0, sizeof(s_cnt));
    s_lat_n = 0;
    s_lat_min = 0;
    s_lat_max = 0;
    s_lat_somme = 0;
    /* ⚠️ Et on OUBLIE le seq : une campagne relancée juste après avec la trame
     * d'exemple du dépôt (`$DN,1,42,…`) tombait en doublon si s_seq valait déjà 42,
     * et la campagne mesurait DU VIDE. La valeur et son horodatage, eux, survivent :
     * `pc reset` remet les compteurs à zéro, il ne tue pas la liaison en cours. */
    s_seq_connu = false;
    portEXIT_CRITICAL(&s_mux);
}

void dn_link_latence(uint32_t *n, int64_t *min_us, int64_t *moy_us, int64_t *max_us)
{
    portENTER_CRITICAL(&s_mux);
    uint32_t ln = s_lat_n;
    int64_t lmin = s_lat_min, lmax = s_lat_max, lsom = s_lat_somme;
    portEXIT_CRITICAL(&s_mux);
    if (n) {
        *n = ln;
    }
    if (min_us) {
        *min_us = lmin;
    }
    if (moy_us) {
        *moy_us = (ln > 0) ? lsom / (int64_t)ln : 0;
    }
    if (max_us) {
        *max_us = lmax;
    }
}

/* ── La tâche de poussée vers l'UI ───────────────────────────────────────────
 *
 * Période 250 ms, cadence en TEMPS ABSOLU (vTaskDelayUntil — un sleep qui
 * dérive est interdit par la méthodo). Elle ne pousse que ce qui a changé :
 * une trame fraîche, ou un changement d'état de liaison — la case CPU n'est
 * donc redessinée qu'à ~1 Hz en régime, pas à 4 Hz.
 *
 * Elle appelle dn_ui_cpu_maj(), fonction publique qui prend le verrou LVGL
 * ELLE-MÊME (règle du dépôt : l'appelant jamais). Si le verrou est occupé,
 * la poussée est réputée NON faite et sera retentée au tick suivant.
 */
static void tache_lien(void *arg)
{
    (void)arg;
    TickType_t reveil = xTaskGetTickCount();
    /* -1 ≠ tout état réel : le premier tour pousse TOUJOURS, pour que la case
     * CPU dise « jamais reçue » dès le boot au lieu du 42 % factice de dn1-4. */
    int etat_pousse = -1;
    uint32_t seq_poussee = 0;

    for (;;) {
        vTaskDelayUntil(&reveil, pdMS_TO_TICKS(250));

        int valeur;
        int64_t recu_us;
        uint32_t seq;
        etat_brut(&valeur, &recu_us, &seq, NULL);
        dn_link_etat_t etat = dn_link_etat();

        bool fraiche = (etat == DN_LINK_VIVANTE) &&
                       (etat_pousse != (int)DN_LINK_VIVANTE || seq != seq_poussee);
        if ((int)etat == etat_pousse && !fraiche) {
            continue;
        }

        /* ⚠️ L'INCRÉMENT DE `reprises` EST APRÈS LA POUSSÉE, PAS AVANT — correctif
         * de revue (2026-08-16). Il était avant, et `etat_pousse` n'était mis à jour
         * qu'après le `continue` du verrou occupé : si le verrou LVGL était tenu
         * > 1 000 ms (cas documenté du dépôt : un plein écran à `lines 8` le tient
         * ~2,1 s), le tour suivant re-détectait MORTE→VIVANTE et re-comptait. UNE
         * reprise réelle pouvait être publiée 4 à 9 fois — dans le compteur qui sert
         * précisément de PREUVE à AC7. */
        bool etait_morte = (etat_pousse == (int)DN_LINK_MORTE);

        bool label_pose = false;
        if (!dn_ui_cpu_maj(valeur, etat == DN_LINK_VIVANTE, &label_pose)) {
            continue; /* verrou LVGL non pris : on retentera dans 250 ms */
        }
        etat_pousse = (int)etat;
        if (etait_morte && etat == DN_LINK_VIVANTE) {
            s_cnt.reprises++; /* AC7 : la reprise est un événement compté, UNE fois */
        }
        if (fraiche) {
            seq_poussee = seq;
        }
        /* ⚠️ La latence ne se compte QUE si le texte a atteint un label vivant.
         * Sans `label_pose`, on chronométrait aussi les poussées où le pointeur
         * était NULL (modèle REBUILD, vue détail ouverte) ou l'UI arrêtée : un
         * instrument qui ne pouvait pas voir ce qu'il prétendait mesurer. */
        if (fraiche && label_pose) {
            int64_t lat = esp_timer_get_time() - recu_us;
            portENTER_CRITICAL(&s_mux);
            if (s_lat_n == 0 || lat < s_lat_min) {
                s_lat_min = lat;
            }
            if (s_lat_n == 0 || lat > s_lat_max) {
                s_lat_max = lat;
            }
            s_lat_somme += lat;
            s_lat_n++;
            portEXIT_CRITICAL(&s_mux);
        }
    }
}

esp_err_t dn_link_init(void)
{
    /* 4096 o de pile : dn_ui_cpu_maj formate un petit texte sous le verrou
     * LVGL, rien de gourmand. Priorité basse : la donnée PC ne doit jamais
     * passer devant le rendu. Pas d'affinité : le verrou LVGL fait la sûreté. */
    BaseType_t ok = xTaskCreate(tache_lien, "dn_link", 4096, NULL, 3, NULL);
    if (ok != pdPASS) {
        ESP_LOGE(TAG, "tache dn_link non creee");
        return ESP_ERR_NO_MEM;
    }
    return ESP_OK;
}
