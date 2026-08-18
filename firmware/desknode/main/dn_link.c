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

/*
 * ── L'ÉTAT, PAR MÉTRIQUE (dn4-1) — TOUT accès sous s_mux (int64 déchirable) ──
 *
 * 🔴 CINQ VALEURS, CINQ HORLOGES, MAIS UN SEUL SUIVI DE SEQ. Le motif est dans
 *    `dn_link.h` : `seq` numérote les trames de l'AGENT (émetteur unique), pas
 *    celles d'une métrique. Le suivre par métrique compterait 4 « pertes » à
 *    chaque tour de cinq trames — le compteur de diagnostic deviendrait un
 *    générateur de bruit.
 */
typedef struct {
    int v1;         /* dixièmes, -1 = jamais reçue */
    int v2;         /* dixièmes, valable si v2_connue */
    bool v2_connue; /* W10 : la trame portait-elle une 2ᵉ grandeur ? */
    int64_t recu_us;
    uint32_t seq;   /* seq de la trame qui a posé cette valeur */
} dn_link_etat_m_t;

/* ⚠️ Initialisation EXPLICITE, métrique par métrique : un état statique naît
 * IGNORANT, jamais à un zéro qui ressemble à une mesure. Même règle que
 * `DN_VAL_ABSENTE = 0` dans `dn_widget.h`. ⛔ Pas d'initialiseur de PLAGE
 * (`[0 ... N-1]`) : c'est une extension GCC, et une table nommée se relit. */
static dn_link_etat_m_t s_m[DN_LINK_METRIQUES] = {
    [DN_LINK_M_CPU] = {.v1 = -1, .recu_us = -1},
    [DN_LINK_M_GPU] = {.v1 = -1, .recu_us = -1},
    [DN_LINK_M_RAM] = {.v1 = -1, .recu_us = -1},
    [DN_LINK_M_NET] = {.v1 = -1, .recu_us = -1},
    [DN_LINK_M_DISK] = {.v1 = -1, .recu_us = -1},
};

/*
 * ── LA TABLE DES MÉTRIQUES — LE SEUL POINT D'AJOUT (patron `k_desc[]`) ───────
 *
 * Ajouter une métrique au protocole, c'est ajouter UNE ligne ici. ⛔ Aucun
 * `if (m == …)` dans le parseur : il branche sur la TABLE, jamais sur un nom.
 *
 * `max1`/`max2` sont les plafonds de PLAUSIBILITÉ, en dixièmes de l'unité. Ils
 * ne sont pas décoratifs : au-delà, la trame part en `rejets_bornes` au lieu
 * d'écrire un chiffre absurde à l'écran. ⚠️ Ils sont LARGES à dessein — leur
 * rôle est d'attraper un émetteur cassé, pas de juger la tour.
 *
 * `v2_attendue` distingue deux silences que rien d'autre ne distingue :
 *   · `disk` n'a PAS de 2ᵉ grandeur — son absence est NORMALE ;
 *   · `gpu` en a une (°C) — son absence veut dire « la source ne la donne pas »,
 *     et c'est une information, pas un format invalide.
 */
static const struct {
    const char *nom;    /* tel qu'il circule SUR LE FIL */
    uint32_t max1;
    uint32_t max2;
    bool v2_attendue;
    const char *unite1;
    const char *unite2;
} k_metriques[DN_LINK_METRIQUES] = {
    [DN_LINK_M_CPU] = {"cpu", 1000u, 1000u, true, "%", "GHz"},
    [DN_LINK_M_GPU] = {"gpu", 1000u, 1500u, true, "%", "degC"},
    [DN_LINK_M_RAM] = {"ram", 1000u, 40000u, true, "%", "Go"},
    [DN_LINK_M_NET] = {"net", 1000000u, 1000000u, true, "Mb/s", "Mb/s"},
    /* W2 TRANCHÉ PAR LA MESURE le 2026-08-18 : `disk` porte un DÉBIT, pas un
     * taux d'occupation. Session réelle de 16 min à 1 Hz sur la tour, critère
     * écrit AVANT : le débit change de texte 93,3 % du temps (étendue
     * 268,4 Mo/s), l'occupation 0,0 % (54,9 % du premier au dernier
     * échantillon, étendue NULLE au dixième de point). Une case de six doit
     * bouger. */
    [DN_LINK_M_DISK] = {"disk", 1000000u, 0u, false, "Mo/s", NULL},
};

/* Le dernier état valide reçu, TOUTES MÉTRIQUES CONFONDUES — diagnostic global
 * pour `pc`, ⛔ jamais un critère de case. */
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

    /*
     * ── LES TROIS VERROUS EN DUR DE dn2-2 SONT OUVERTS ICI (dn4-1 / AC2) ─────
     *   1. `NB_CHAMPS = 6` figé      -> 6 OU 7, selon la version ET la trame
     *   2. `ver != 1` rejeté         -> 1 et 2 acceptées, le reste compté
     *   3. `strcmp(champ[4],"cpu")`  -> une TABLE de métriques
     * ⚠️ Ce sont bien TROIS verrous du PARSEUR, pas « juste l'agent ».
     * 🔴 ET AUCUN COMPTEUR NE CHANGE DE SENS : un champ en trop reste `format`,
     *    une version inconnue reste `version`, une métrique inconnue reste
     *    `format`, une valeur hors plafond reste `bornes`. La campagne de bruit
     *    d'AC2 doit incrémenter le compteur attendu ET LUI SEUL.
     */
    enum { NB_CHAMPS_MAX = 7 }; /* DN · ver · seq · t_ms · metrique · v1 [· v2] */
    enum { NB_CHAMPS_MIN = 6 };
    char *champ[NB_CHAMPS_MAX];
    int n = 0;
    champ[n++] = corps;
    for (char *p = corps; *p; p++) {
        if (*p == ',') {
            *p = '\0';
            if (n == NB_CHAMPS_MAX) {
                s_cnt.rejets_format++; /* champ EN TROP */
                return false;
            }
            champ[n++] = p + 1;
        }
    }
    if (n < NB_CHAMPS_MIN) {
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
    if (ver < DN_LINK_PROTO_VERSION_MIN || ver > DN_LINK_PROTO_VERSION) {
        s_cnt.rejets_version++;
        return false;
    }
    /* 🔴 v1 RESTE v1 — 6 CHAMPS, PAS 7. Accepter une v1 à 7 champs serait
     *    « interpréter à moitié » une trame dont l'émetteur ne connaît pas la
     *    grammaire élargie : c'est exactement ce que la doctrine de version
     *    interdit. Une v1 élargie est un émetteur qui ment sur sa version. */
    if (ver == 1u && n != NB_CHAMPS_MIN) {
        s_cnt.rejets_format++;
        return false;
    }

    uint32_t seq, t_ms;
    if (!parse_u32_strict(champ[2], &seq) || !parse_u32_strict(champ[3], &t_ms)) {
        s_cnt.rejets_format++;
        return false;
    }

    /* La MÉTRIQUE, par la table — ⛔ aucun `strcmp` nommé en dur. */
    int im = -1;
    for (int i = 0; i < DN_LINK_METRIQUES; i++) {
        if (strcmp(champ[4], k_metriques[i].nom) == 0) {
            im = i;
            break;
        }
    }
    if (im < 0) {
        s_cnt.rejets_format++; /* métrique inconnue */
        return false;
    }
    /* v1 ne connaît QUE `cpu` : une v1 annonçant `gpu` est un émetteur qui se
     * trompe de version, pas une extension. */
    if (ver == 1u && im != DN_LINK_M_CPU) {
        s_cnt.rejets_format++;
        return false;
    }

    uint32_t v1, v2 = 0;
    bool v2_connue = (n == NB_CHAMPS_MAX);
    if (!parse_u32_strict(champ[5], &v1)) {
        s_cnt.rejets_format++;
        return false;
    }
    if (v2_connue && !parse_u32_strict(champ[6], &v2)) {
        s_cnt.rejets_format++;
        return false;
    }
    /* Une 2ᵉ grandeur envoyée pour une métrique qui n'en a PAS est un défaut de
     * format, pas une donnée en trop qu'on jetterait en silence. */
    if (v2_connue && !k_metriques[im].v2_attendue) {
        s_cnt.rejets_format++;
        return false;
    }
    if (v1 > k_metriques[im].max1 ||
        (v2_connue && v2 > k_metriques[im].max2)) {
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
    int64_t maintenant = esp_timer_get_time();
    s_m[im].v1 = (int)v1;
    s_m[im].v2 = (int)v2;
    s_m[im].v2_connue = v2_connue;
    s_m[im].recu_us = maintenant;
    s_m[im].seq = seq;
    s_seq = seq;
    s_t_ms = t_ms;
    s_recu_us = maintenant;
    portEXIT_CRITICAL(&s_mux);
    s_cnt.recues++;
    return true;
}

/* ── La table des métriques, RELUE — jamais récitée ailleurs ─────────────── */

const char *dn_link_metrique_nom(dn_link_metrique_t m)
{
    if (m < 0 || m >= DN_LINK_METRIQUES) {
        return "?";
    }
    return k_metriques[m].nom;
}

const char *dn_link_metrique_unite(dn_link_metrique_t m, int grandeur)
{
    if (m < 0 || m >= DN_LINK_METRIQUES) {
        return NULL;
    }
    return grandeur == 0 ? k_metriques[m].unite1 : k_metriques[m].unite2;
}

bool dn_link_metrique_v2_attendue(dn_link_metrique_t m)
{
    return (m >= 0 && m < DN_LINK_METRIQUES) && k_metriques[m].v2_attendue;
}

/* ── Accès à l'état ──────────────────────────────────────────────────────── */

static dn_link_etat_t etat_depuis(int64_t recu_us, int64_t maintenant)
{
    if (recu_us < 0) {
        return DN_LINK_JAMAIS;
    }
    return (maintenant - recu_us) < DN_LINK_PEREMPTION_US ? DN_LINK_VIVANTE
                                                          : DN_LINK_MORTE;
}

bool dn_link_vue(dn_link_metrique_t m, dn_link_vue_t *out)
{
    if (m < 0 || m >= DN_LINK_METRIQUES || !out) {
        return false;
    }
    /* 🔴 UN SEUL PASSAGE SOUS LE VERROU pour les cinq champs. Les lire par cinq
     *    appels laisserait afficher une valeur neuve avec un âge périmé (ou
     *    l'inverse) — le même motif que le verrou unique de `dn_ui_ambiance_maj`,
     *    transposé à la lecture. */
    portENTER_CRITICAL(&s_mux);
    dn_link_etat_m_t e = s_m[m];
    portEXIT_CRITICAL(&s_mux);
    int64_t maintenant = esp_timer_get_time();
    out->etat = etat_depuis(e.recu_us, maintenant);
    out->v1 = e.v1;
    out->v2 = e.v2;
    out->v2_connue = e.v2_connue;
    out->age_us = (e.recu_us < 0) ? -1 : maintenant - e.recu_us;
    out->seq = e.seq;
    return true;
}

dn_link_etat_t dn_link_etat_metrique(dn_link_metrique_t m)
{
    dn_link_vue_t v;
    if (!dn_link_vue(m, &v)) {
        return DN_LINK_JAMAIS;
    }
    return v.etat;
}

static void etat_brut(int *valeur, int64_t *recu_us, uint32_t *seq, uint32_t *t_ms)
{
    portENTER_CRITICAL(&s_mux);
    if (valeur) {
        *valeur = s_m[DN_LINK_M_CPU].v1;
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

/*
 * LE RÉSUMÉ GLOBAL — VIVANTE dès qu'UNE métrique est fraîche.
 * ⛔ NE JAMAIS EN JUGER UNE CASE : avec cinq métriques, quatre cases mortes
 *    hériteraient du « VIVANTE » de la cinquième. C'est `dn_link_etat_metrique`
 *    qui décide d'une case, et c'est écrit dans `dn_link.h`.
 */
dn_link_etat_t dn_link_etat(void)
{
    int64_t maintenant = esp_timer_get_time();
    bool une_vivante = false, une_connue = false;
    portENTER_CRITICAL(&s_mux);
    for (int i = 0; i < DN_LINK_METRIQUES; i++) {
        if (s_m[i].recu_us < 0) {
            continue;
        }
        une_connue = true;
        if ((maintenant - s_m[i].recu_us) < DN_LINK_PEREMPTION_US) {
            une_vivante = true;
        }
    }
    portEXIT_CRITICAL(&s_mux);
    if (!une_connue) {
        return DN_LINK_JAMAIS;
    }
    return une_vivante ? DN_LINK_VIVANTE : DN_LINK_MORTE;
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
/* W4 — voir `dn_link.h`. Défaut GROUPÉ : c'est le régime nominal, celui que la
 * baseline §16.1 décrit et que la prédiction d'AC7 chiffre. */
static bool s_etale;

void dn_link_set_etalement(bool etale)
{
    s_etale = etale;
}

bool dn_link_etalement(void)
{
    return s_etale;
}

/* Ce qui a DÉJÀ été poussé, par métrique. `-1` ≠ tout état réel : le premier
 * tour pousse TOUJOURS, pour qu'une case dise « jamais reçue » dès le boot au
 * lieu de garder le factice de sa construction. */
static int s_etat_pousse[DN_LINK_METRIQUES] = {-1, -1, -1, -1, -1};
static uint32_t s_seq_poussee[DN_LINK_METRIQUES];

/* Rend true si la métrique a été poussée (ou n'avait rien à pousser) ; false si
 * le verrou LVGL n'a pas été pris — l'appelant retentera. */
static bool pousser_metrique(int i, bool *a_pousse)
{
    *a_pousse = false;

    dn_link_vue_t v;
    if (!dn_link_vue((dn_link_metrique_t)i, &v)) {
        return true;
    }
    bool fraiche = (v.etat == DN_LINK_VIVANTE) &&
                   (s_etat_pousse[i] != (int)DN_LINK_VIVANTE ||
                    v.seq != s_seq_poussee[i]);
    if ((int)v.etat == s_etat_pousse[i] && !fraiche) {
        return true; /* rien de neuf : ⛔ ne PAS reposer un texte identique */
    }

    /* ⚠️ L'INCRÉMENT DE `reprises` EST APRÈS LA POUSSÉE, PAS AVANT — correctif
     * de revue (2026-08-16). Il était avant, et `etat_pousse` n'était mis à jour
     * qu'après le `continue` du verrou occupé : si le verrou LVGL était tenu
     * > 1 000 ms (cas documenté du dépôt : un plein écran à `lines 8` le tient
     * ~2,1 s), le tour suivant re-détectait MORTE→VIVANTE et re-comptait. UNE
     * reprise réelle pouvait être publiée 4 à 9 fois — dans le compteur qui sert
     * précisément de PREUVE à AC7.
     * ⚠️ dn4-1 : ce compteur est GLOBAL et il le reste. Avec cinq métriques qui
     *    reviennent ensemble, une reprise de l'AGENT compterait CINQ fois si on
     *    l'incrémentait par métrique — le sur-comptage exact que dn2-2 a corrigé,
     *    simplement déplacé. Seule la métrique CPU l'incrémente : elle est
     *    toujours présente, en v1 comme en v2. */
    bool etait_morte = (s_etat_pousse[i] == (int)DN_LINK_MORTE);

    bool label_pose = false;
    if (!dn_ui_pc_maj((dn_link_metrique_t)i, &v, &label_pose)) {
        return false; /* verrou LVGL non pris : on retentera au prochain réveil */
    }
    *a_pousse = true;
    s_etat_pousse[i] = (int)v.etat;
    if (etait_morte && v.etat == DN_LINK_VIVANTE && i == DN_LINK_M_CPU) {
        s_cnt.reprises++; /* AC7 : la reprise est un événement compté, UNE fois */
    }
    if (fraiche) {
        s_seq_poussee[i] = v.seq;
    }
    /* ⚠️ La latence ne se compte QUE si le texte a atteint un label vivant.
     * Sans `label_pose`, on chronométrait aussi les poussées où le pointeur
     * était NULL (modèle REBUILD, vue détail ouverte) ou l'UI arrêtée : un
     * instrument qui ne pouvait pas voir ce qu'il prétendait mesurer. */
    if (fraiche && label_pose && v.age_us >= 0) {
        int64_t lat = v.age_us;
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
    return true;
}

static void tache_lien(void *arg)
{
    (void)arg;
    TickType_t reveil = xTaskGetTickCount();
    int tourniquet = 0; /* branche ÉTALÉE : par où on reprend au réveil suivant */

    for (;;) {
        vTaskDelayUntil(&reveil, pdMS_TO_TICKS(250));

        if (!s_etale) {
            /* GROUPÉ : tout ce qui a changé part dans le MÊME réveil, donc dans
             * le même cycle LVGL. C'est le régime que l'agent produit. */
            for (int i = 0; i < DN_LINK_METRIQUES; i++) {
                bool pousse;
                pousser_metrique(i, &pousse);
            }
            continue;
        }

        /* ÉTALÉ : AU PLUS UNE métrique par réveil, en tourniquet. On avance le
         * tourniquet même quand la métrique n'avait rien à dire — sinon une
         * métrique muette bloquerait le tour et l'étalement deviendrait un
         * blocage. ⚠️ Une métrique est donc rafraîchie toutes les ~1,25 s. */
        for (int essai = 0; essai < DN_LINK_METRIQUES; essai++) {
            int i = tourniquet;
            tourniquet = (tourniquet + 1) % DN_LINK_METRIQUES;
            bool pousse = false;
            if (!pousser_metrique(i, &pousse)) {
                /* ⚠️ Verrou LVGL occupé : on REMET le tourniquet sur `i`, sinon
                 * cette métrique-là serait SAUTÉE d'un tour entier — et un
                 * verrou tenu longtemps (un `build_scene()` en cours) la ferait
                 * sauter à chaque fois qu'il coïncide avec son tour. */
                tourniquet = i;
                break;
            }
            if (pousse) {
                break; /* UNE seule poussée par réveil — c'est tout le levier */
            }
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
