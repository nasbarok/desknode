/* DeskNode — `dn_langue` : implémentation. Motifs complets dans `dn_langue.h`. */

#include "dn_langue.h"

#include <string.h>

#include "esp_log.h"

static const char *TAG = "dn_langue";

/*
 * LES COLONNES, DÉPLIÉES DE LA MÊME LISTE QUE L'ÉNUMÉRATION.
 *
 * ⚠️ L'ORDRE DES TABLEAUX SUIT `dn_langue_t` — anglais d'abord (le DÉFAUT).
 *    Les intervertir ferait parler français par défaut sans qu'aucune ligne ne
 *    change, et sans qu'aucun test ne bronche. C'est pourquoi la gate confronte
 *    l'ordre de l'énumération de `dn_langue.h` à celui de ce tableau-ci.
 * ⚠️ L'indice 0 (`DN_T_AUCUN`) est laissé NULL par le désignateur : c'est la
 *    sentinelle « rien à dire », ⛔ pas une chaîne vide.
 */
static const char *const k_txt[DN_LANGUE_N][DN_T_N] = {
    [DN_LANGUE_EN] = {
#define X(nom, en, fr) [DN_T_##nom] = en,
        DN_TXT_LISTE(X)
#undef X
    },
    [DN_LANGUE_FR] = {
#define X(nom, en, fr) [DN_T_##nom] = fr,
        DN_TXT_LISTE(X)
#undef X
    },
};

/* Le NOM de chaque clé — pour que l'audit puisse DIRE laquelle est fautive.
 * ⛔ Sans lui, l'audit publierait « la clé 47 est vide », et l'auteur
 *    compterait des lignes à la main. */
static const char *const k_nom_cle[DN_T_N] = {
    [DN_T_AUCUN] = "AUCUN",
#define X(nom, en, fr) [DN_T_##nom] = #nom,
    DN_TXT_LISTE(X)
#undef X
};

/*
 * 🔴 LE DÉFAUT EST L'ANGLAIS, ET IL EST ÉCRIT ICI **UNE FOIS**.
 *    `DN_LANGUE_EN` valant 0, un état non initialisé rendrait déjà l'anglais —
 *    ⛔ mais on ne s'appuie PAS sur ça : une valeur d'énumération qui change
 *    ferait basculer le défaut en silence. Le défaut est POSÉ.
 */
static dn_langue_t s_langue = DN_LANGUE_EN;

/* Les codes du sélecteur. ⛔ NON TRADUITS (AC2.4) : « FR » et « EN » se lisent
 * dans les deux langues, et écrire « Langue » à un anglophone serait exactement
 * le défaut que cette story corrige. */
static const char *const k_code[DN_LANGUE_N] = {
    [DN_LANGUE_EN] = "EN",
    [DN_LANGUE_FR] = "FR",
};

const char *dn_t_l(dn_langue_t l, dn_txt_t cle)
{
    if (l < 0 || l >= DN_LANGUE_N || cle <= DN_T_AUCUN || cle >= DN_T_N) {
        return NULL; /* ⛔ « rien à dire », ⛔ pas "" — voir dn_langue.h */
    }
    return k_txt[l][cle];
}

const char *dn_t(dn_txt_t cle) { return dn_t_l(s_langue, cle); }

const char *dn_t_fr(dn_txt_t cle) { return dn_t_l(DN_LANGUE_FR, cle); }

dn_langue_t dn_langue(void) { return s_langue; }

void dn_langue_set(dn_langue_t l)
{
    if (l < 0 || l >= DN_LANGUE_N) {
        /* ⛔ LE DÉPÔT REFUSE, IL N'ÉCRÊTE PAS. Un index hors bornes écrêté sur
         * l'anglais ferait passer une NVS corrompue pour un choix. */
        ESP_LOGW(TAG, "langue %d HORS BORNES — IGNOREE (⛔ pas ecretee). La "
                      "langue reste « %s ».",
                 (int)l, k_code[s_langue]);
        return;
    }
    s_langue = l;
}

const char *dn_langue_code(dn_langue_t l)
{
    return (l >= 0 && l < DN_LANGUE_N) ? k_code[l] : NULL;
}

dn_langue_t dn_langue_de_code(const char *code)
{
    if (!code) {
        return DN_LANGUE_N;
    }
    for (int i = 0; i < DN_LANGUE_N; i++) {
        if (strcasecmp(code, k_code[i]) == 0) {
            return (dn_langue_t)i;
        }
    }
    return DN_LANGUE_N; /* ⛔ un ÉTAT « inconnu », pas un repli silencieux */
}

int dn_langue_audit(void)
{
    /*
     * ⚠️ CE QU'IL NE CHERCHE PAS : un trou. La X-macro rend un trou
     *    IMPOSSIBLE À COMPILER (`X()` prend trois arguments).
     * ⚠️ CE QU'IL CHERCHE : ce que le compilateur ne voit pas — une traduction
     *    **VIDE**, qui compile et n'affiche RIEN. C'est le seul trou qui reste
     *    possible, et il serait INVISIBLE sur la dalle (un label vide n'a l'air
     *    de rien, il a l'air d'un espace).
     */
    int defauts = 0;
    for (int c = DN_T_AUCUN + 1; c < DN_T_N; c++) {
        for (int l = 0; l < DN_LANGUE_N; l++) {
            const char *s = k_txt[l][c];
            if (s == NULL) {
                /* Structurellement inatteignable via la X-macro — gardé quand
                 * même : si quelqu'un ajoute un jour une colonne à la main, ce
                 * serait ICI que ça se verrait, ⛔ pas sur la dalle. */
                ESP_LOGE(TAG, "clé DN_T_%s : traduction %s ABSENTE (NULL).",
                         k_nom_cle[c], k_code[l]);
                defauts++;
            } else if (s[0] == '\0') {
                ESP_LOGE(TAG, "clé DN_T_%s : traduction %s VIDE — elle "
                              "compilerait et n'afficherait RIEN.",
                         k_nom_cle[c], k_code[l]);
                defauts++;
            }
        }
    }
    ESP_LOGI(TAG, "table : %d clés x %d langue(s), %d defaut(s) · langue "
                  "courante « %s » (defaut = « %s »)",
             (int)DN_T_N - 1, (int)DN_LANGUE_N, defauts, k_code[s_langue],
             k_code[DN_LANGUE_EN]);
    return defauts;
}
