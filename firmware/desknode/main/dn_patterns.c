#include "dn_patterns.h"

#include <stdio.h>
#include <string.h>

#include "dn_asset.h"
#include "dn_pins.h"
#include "esp_log.h"

static const char *TAG = "dn_mire";

#define W DN_LCD_H_RES
#define H DN_LCD_V_RES

static inline uint16_t rgb565(uint8_t r, uint8_t g, uint8_t b)
{
    return (uint16_t)(((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3));
}

/* ── Fonte 5x7, la même table que tools/gen_living_pcb.py ────────────────── */
/* Elle sert à ÉTIQUETER les mires. Une mire non étiquetée produit des
 * impressions ; une mire étiquetée produit une phrase qu'on peut écrire dans
 * un document (« la bande 4, marquée B4/GPIO21, est le bleu le plus vif »). */
#define GLYPH_W 5
#define GLYPH_H 7

static const uint8_t FONT[][GLYPH_H] = {
    {0, 0, 0, 0, 0, 0, 0},                                   /* espace */
    {0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E},              /* 0 */
    {0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E},              /* 1 */
    {0x0E, 0x11, 0x01, 0x02, 0x04, 0x08, 0x1F},              /* 2 */
    {0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E},              /* 3 */
    {0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02},              /* 4 */
    {0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E},              /* 5 */
    {0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E},              /* 6 */
    {0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08},              /* 7 */
    {0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E},              /* 8 */
    {0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C},              /* 9 */
};

/* Les quelques lettres dont les mires ont besoin. */
typedef struct {
    char c;
    uint8_t rows[GLYPH_H];
} dn_glyph_t;

static const dn_glyph_t LETTERS[] = {
    {'A', {0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11}},
    {'B', {0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E}},
    {'C', {0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E}},
    {'D', {0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E}},
    {'E', {0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F}},
    {'G', {0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F}},
    {'H', {0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11}},
    {'I', {0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x1F}},
    {'L', {0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F}},
    {'M', {0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11}},
    {'N', {0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11}},
    {'O', {0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E}},
    {'P', {0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10}},
    {'R', {0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11}},
    {'S', {0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E}},
    {'T', {0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04}},
    {'U', {0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E}},
    {'V', {0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04}},
    {'X', {0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11}},
    {'-', {0x00, 0x00, 0x00, 0x1F, 0x00, 0x00, 0x00}},
    {'/', {0x01, 0x02, 0x02, 0x04, 0x08, 0x08, 0x10}},
};

static const uint8_t *glyph_for(char c)
{
    if (c == ' ') {
        return FONT[0];
    }
    if (c >= '0' && c <= '9') {
        return FONT[1 + (c - '0')];
    }
    for (size_t i = 0; i < sizeof(LETTERS) / sizeof(LETTERS[0]); i++) {
        if (LETTERS[i].c == c) {
            return LETTERS[i].rows;
        }
    }
    return FONT[0];
}

static void put_px(uint16_t *buf, int x, int y, uint16_t c)
{
    if (x >= 0 && x < W && y >= 0 && y < H) {
        buf[y * W + x] = c;
    }
}

static void fill_rect(uint16_t *buf, int x, int y, int w, int h, uint16_t c)
{
    if (x < 0) {
        w += x;
        x = 0;
    }
    if (y < 0) {
        h += y;
        y = 0;
    }
    if (x + w > W) {
        w = W - x;
    }
    if (y + h > H) {
        h = H - y;
    }
    for (int yy = y; yy < y + h; yy++) {
        uint16_t *row = buf + (size_t)yy * W + x;
        for (int xx = 0; xx < w; xx++) {
            row[xx] = c;
        }
    }
}

static void draw_text(uint16_t *buf, int x, int y, const char *s, uint16_t color,
                      int scale)
{
    int cx = x;
    for (const char *p = s; *p; p++) {
        char c = *p;
        if (c >= 'a' && c <= 'z') {
            c = (char)(c - 'a' + 'A');
        }
        const uint8_t *g = glyph_for(c);
        for (int gy = 0; gy < GLYPH_H; gy++) {
            for (int gx = 0; gx < GLYPH_W; gx++) {
                if (g[gy] & (1 << (GLYPH_W - 1 - gx))) {
                    fill_rect(buf, cx + gx * scale, y + gy * scale, scale, scale,
                              color);
                }
            }
        }
        cx += (GLYPH_W + 1) * scale;
    }
}

/* ── Les mires ───────────────────────────────────────────────────────────── */

void dn_pattern_fill(uint16_t *buf, uint16_t color)
{
    for (size_t i = 0; i < (size_t)W * H; i++) {
        buf[i] = color;
    }
}

/*
 * MIRE DE BITS — l'instrument central d'AC1.
 *
 * ─── POURQUOI ELLE EST EN BANDES HORIZONTALES ────────────────────────────
 * La PREMIÈRE version dessinait 16 bandes VERTICALES de 30 px, coiffées d'un
 * en-tête de texte à l'échelle 2. Elle a été ÉLIMINÉE, avec son symptôme :
 * sur une dalle de 2,8", 30 px de large et des glyphes de 10x14 px sont
 * illisibles, et la lecture qu'elle a produite (« les poids FORTS de chaque
 * canal sont éteints ») a été RÉFUTÉE dans la minute par la mire de blanc
 * plein — un blanc franc et neutre, qui exige au contraire que les 16 lignes
 * fonctionnent. Un instrument qui produit une lecture que le témoin suivant
 * contredit n'est pas un instrument.
 *
 * Version retenue : 16 bandes HORIZONTALES de 40 px (16 x 40 = 640, sans
 * reste), pleine largeur, avec une zone d'étiquette noire de 156 px à gauche
 * et du texte à l'échelle 3. Chaque bande fait 324 x 40 px de couleur utile,
 * soit 14 fois la surface de la version précédente.
 *
 * Comment la lire, DE HAUT EN BAS :
 *   - bandes B0..B4  : BLEUES, de plus en plus vives ;
 *   - bandes G0..G5  : VERTES, de plus en plus vives ;
 *   - bandes R0..R4  : ROUGES, de plus en plus vives.
 *   L'étiquette donne : le signal attendu, le GPIO attendu, et le POIDS
 *   (1, 2, 4, 8, 16, 32). Le poids est là pour qu'on vérifie l'ordre sans
 *   avoir à se souvenir de quoi que ce soit : la bande marquée 16 doit être
 *   la plus vive de son groupe, celle marquée 1 la plus sombre.
 *   ⚠️ Les bandes de poids 1 et 2 sont LÉGITIMEMENT à la limite du visible
 *      (1/31 et 2/31). Sombre n'est pas éteint. C'est l'ORDRE qui prouve,
 *      pas la visibilité absolue — et c'est pour ça que la mire complémentaire
 *      `nbits` existe.
 */
static const int8_t k_expected_gpio[16] = DN_RGB_DATA_GPIOS;
static const char *const k_expected_name[16] = {
    "B0", "B1", "B2", "B3", "B4", "G0", "G1", "G2",
    "G3", "G4", "G5", "R0", "R1", "R2", "R3", "R4",
};
static const int k_expected_weight[16] = {
    1, 2, 4, 8, 16, 1, 2, 4, 8, 16, 32, 1, 2, 4, 8, 16,
};

#define DN_BITS_BAND_H (H / 16) /* 40 px, sans reste */
#define DN_BITS_LABEL_W 156

static void draw_bit_bands(uint16_t *buf, bool complement)
{
    for (int i = 0; i < 16; i++) {
        int y = i * DN_BITS_BAND_H;
        uint16_t v = (uint16_t)(1u << i);
        if (complement) {
            v = (uint16_t)(0xFFFFu & ~v);
        }
        /* bande de couleur, pleine largeur */
        fill_rect(buf, 0, y, W, DN_BITS_BAND_H, v);
        /* zone d'étiquette : noire, elle sert AUSSI de bord de référence —
         * l'œil détecte une teinte faible bien mieux le long d'une arête que
         * sur un aplat isolé */
        fill_rect(buf, 0, y, DN_BITS_LABEL_W, DN_BITS_BAND_H, 0x0000);

        char label[16];
        snprintf(label, sizeof(label), "%s %d %d", k_expected_name[i],
                 (int)k_expected_gpio[i], k_expected_weight[i]);
        draw_text(buf, 6, y + (DN_BITS_BAND_H - GLYPH_H * 3) / 2, label, 0xFFFF, 3);

        /* séparateur : 2 px noirs, pour compter les bandes sans se tromper */
        fill_rect(buf, 0, y + DN_BITS_BAND_H - 2, W, 2, 0x0000);
    }
}

static void draw_bits(uint16_t *buf) { draw_bit_bands(buf, false); }

/*
 * MIRE DE BITS COMPLÉMENTAIRE — le recoupement d'AC1.
 * La bande i porte TOUS les bits SAUF i. Chaque bande est donc quasi blanche,
 * et la bande i tire vers la teinte complémentaire du canal auquel i
 * appartient. Là où `bits` rend les poids FAIBLES difficiles à voir, `nbits`
 * rend les poids FORTS impossibles à rater : si B4 était mort, sa bande serait
 * franchement jaune. Les deux mires se recoupent, aucune ne conclut seule.
 */
static void draw_nbits(uint16_t *buf) { draw_bit_bands(buf, true); }

/*
 * MIRE DE CADRAGE — la preuve d'AC3 sur les bords.
 * Un liseré de 1 px sur les 4 côtés, une croix à chaque coin, une grille tous
 * les 80 px, et un repère d'orientation DIFFÉRENT dans chaque coin : sans lui,
 * une image tournée de 180° ou en miroir passe inaperçue.
 */
static void draw_frame(uint16_t *buf)
{
    const uint16_t fond = 0x0000;
    const uint16_t blanc = 0xFFFF;
    const uint16_t gris = 0x39E7;
    const uint16_t rouge = rgb565(255, 0, 0);
    const uint16_t vert = rgb565(0, 255, 0);
    const uint16_t bleu = rgb565(0, 0, 255);
    const uint16_t jaune = rgb565(255, 255, 0);

    dn_pattern_fill(buf, fond);

    /* grille tous les 80 px : 480 = 6 colonnes, 640 = 8 lignes */
    for (int x = 80; x < W; x += 80) {
        fill_rect(buf, x, 0, 1, H, gris);
    }
    for (int y = 80; y < H; y += 80) {
        fill_rect(buf, 0, y, W, 1, gris);
    }

    /* liseré de 1 px — si un côté manque, l'image est décalée ou tronquée */
    fill_rect(buf, 0, 0, W, 1, blanc);
    fill_rect(buf, 0, H - 1, W, 1, blanc);
    fill_rect(buf, 0, 0, 1, H, blanc);
    fill_rect(buf, W - 1, 0, 1, H, blanc);

    /* coins : une marque DIFFÉRENTE dans chacun */
    fill_rect(buf, 0, 0, 40, 40, rouge);      /* haut gauche : carré plein rouge */
    fill_rect(buf, W - 40, 0, 40, 8, vert);   /* haut droit : barre verte */
    fill_rect(buf, W - 8, 0, 8, 40, vert);
    fill_rect(buf, 0, H - 40, 8, 40, bleu);   /* bas gauche : équerre bleue */
    fill_rect(buf, 0, H - 8, 40, 8, bleu);
    for (int k = 0; k < 40; k++) {            /* bas droit : diagonale jaune */
        put_px(buf, W - 1 - k, H - 1 - k, jaune);
        put_px(buf, W - 2 - k, H - 1 - k, jaune);
    }

    /* croix au centre exact */
    fill_rect(buf, W / 2 - 40, H / 2, 80, 1, blanc);
    fill_rect(buf, W / 2, H / 2 - 40, 1, 80, blanc);

    /* étiquettes : orientation et dimensions annoncées */
    draw_text(buf, 60, 20, "HAUT", blanc, 3);
    draw_text(buf, 130, 300, "480 X 640", blanc, 4);
    draw_text(buf, 150, 340, "DESKNODE P1", gris, 2);
    draw_text(buf, 60, H - 40, "BAS", blanc, 3);
}

/*
 * RAMPE DE GRIS — détecte un bit mort ou permuté à l'intérieur d'un canal.
 * Une rampe propre est lisse ; un bit mort creuse une marche visible et
 * périodique.
 */
static void draw_gray(uint16_t *buf)
{
    for (int y = 0; y < H; y++) {
        for (int x = 0; x < W; x++) {
            uint8_t v = (uint8_t)((x * 256) / W);
            buf[(size_t)y * W + x] = rgb565(v, v, v);
        }
    }
    /* Une bande de rampes par canal, en bas, pour isoler le canal fautif. */
    for (int x = 0; x < W; x++) {
        uint8_t v = (uint8_t)((x * 256) / W);
        for (int y = H - 150; y < H - 100; y++) {
            buf[(size_t)y * W + x] = rgb565(v, 0, 0);
        }
        for (int y = H - 100; y < H - 50; y++) {
            buf[(size_t)y * W + x] = rgb565(0, v, 0);
        }
        for (int y = H - 50; y < H; y++) {
            buf[(size_t)y * W + x] = rgb565(0, 0, v);
        }
    }
    draw_text(buf, 10, 10, "GRIS", 0xFFFF, 3);
}

/*
 * LES TROIS CANAUX D'UN SEUL COUP D'ŒIL.
 *
 * Les scènes `red`/`green`/`blue` existent toujours et restent la référence
 * plein écran d'AC1. Mais les enchaîner impose de regarder au bon moment, et
 * une observation ratée coûte un aller-retour. Ici les trois canaux purs
 * cohabitent, chacun sous son étiquette : une seule observation suffit à
 * exclure la permutation R<->B ET l'échange d'octets.
 *   - permutation R<->B  : la bande marquée ROUGE apparaît bleue ;
 *   - octets échangés    : aucune bande n'est pure — le rouge 0xF800 devient
 *                          0x00F8, soit un cyan sombre.
 */
static void draw_rgb_triple(uint16_t *buf)
{
    const int band = H / 3; /* 213 px, le reste va à la dernière bande */
    struct {
        uint16_t color;
        const char *label;
        uint16_t label_color;
    } bands[3] = {
        {rgb565(255, 0, 0), "ROUGE", 0xFFFF},
        {rgb565(0, 255, 0), "VERT", 0x0000},
        {rgb565(0, 0, 255), "BLEU", 0xFFFF},
    };
    for (int i = 0; i < 3; i++) {
        int y = i * band;
        int h = (i == 2) ? (H - y) : band;
        fill_rect(buf, 0, y, W, h, bands[i].color);
        draw_text(buf, 16, y + 16, bands[i].label, bands[i].label_color, 5);
    }
}

static void draw_solid_labeled(uint16_t *buf, uint16_t color, const char *label,
                               uint16_t label_color)
{
    dn_pattern_fill(buf, color);
    /* Étiquette confinée au coin haut gauche : le reste de l'écran reste une
     * couleur PURE, ce qui est le point de la mire. */
    draw_text(buf, 8, 8, label, label_color, 3);
}

void dn_pattern_draw(uint16_t *buf, dn_scene_t scene)
{
    switch (scene) {
    case DN_SCENE_BITS:
        draw_bits(buf);
        break;
    case DN_SCENE_NBITS:
        draw_nbits(buf);
        break;
    case DN_SCENE_RGB:
        draw_rgb_triple(buf);
        break;
    case DN_SCENE_COLOR_RED:
        draw_solid_labeled(buf, rgb565(255, 0, 0), "ROUGE", 0xFFFF);
        break;
    case DN_SCENE_COLOR_GREEN:
        draw_solid_labeled(buf, rgb565(0, 255, 0), "VERT", 0x0000);
        break;
    case DN_SCENE_COLOR_BLUE:
        draw_solid_labeled(buf, rgb565(0, 0, 255), "BLEU", 0xFFFF);
        break;
    case DN_SCENE_COLOR_WHITE:
        draw_solid_labeled(buf, 0xFFFF, "BLANC", 0x0000);
        break;
    case DN_SCENE_COLOR_BLACK:
        draw_solid_labeled(buf, 0x0000, "NOIR", 0xFFFF);
        break;
    case DN_SCENE_FRAME:
        draw_frame(buf);
        break;
    case DN_SCENE_GRAY:
        draw_gray(buf);
        break;
    case DN_SCENE_ASSET:
        if (dn_asset_copy_to(buf) != ESP_OK) {
            /* Échouer en SILENCE sur un écran noir serait le pire des cas :
             * on croirait à une panne de driver. On affiche donc une mire de
             * cadrage barrée de rouge, qui dit « l'asset manque ». */
            draw_frame(buf);
            fill_rect(buf, 0, H / 2 - 30, W, 60, rgb565(255, 0, 0));
            draw_text(buf, 40, H / 2 - 12, "ASSET ABSENT", 0xFFFF, 4);
        }
        break;
    default:
        dn_pattern_fill(buf, 0x0000);
        break;
    }
}

static const char *const k_scene_names[DN_SCENE_COUNT] = {
    "bits",  "nbits", "rgb",   "red",  "green", "blue",
    "white", "black", "frame", "gray", "asset",
};

const char *dn_scene_name(dn_scene_t scene)
{
    if (scene < 0 || scene >= DN_SCENE_COUNT) {
        return "?";
    }
    return k_scene_names[scene];
}

dn_scene_t dn_scene_from_name(const char *name)
{
    if (!name) {
        return DN_SCENE_COUNT;
    }
    for (int i = 0; i < DN_SCENE_COUNT; i++) {
        if (strcmp(name, k_scene_names[i]) == 0) {
            return (dn_scene_t)i;
        }
    }
    return DN_SCENE_COUNT;
}

void dn_pattern_explain(dn_scene_t scene)
{
    switch (scene) {
    case DN_SCENE_BITS:
        ESP_LOGI(TAG,
                 "MIRE DE BITS — 16 bandes HORIZONTALES de %d px, DE HAUT EN "
                 "BAS, bande i = bit i seul.",
                 DN_BITS_BAND_H);
        ESP_LOGI(TAG, "  attendu : 5 BLEUES, puis 6 VERTES, puis 5 ROUGES.");
        ESP_LOGI(TAG, "  l'étiquette donne : signal, GPIO, POIDS.");
        ESP_LOGI(TAG, "  la bande marquée 16 (ou 32) doit être la plus VIVE de son groupe,");
        ESP_LOGI(TAG, "  celle marquée 1 la plus sombre. C'est l'ORDRE qui prouve.");
        ESP_LOGI(TAG, "  ⚠️ les poids 1 et 2 sont à la limite du visible : c'est NORMAL.");
        ESP_LOGI(TAG, "  ⚠️ ne pas conclure depuis cette mire seule — recouper avec `nbits`.");
        for (int i = 0; i < 16; i++) {
            ESP_LOGI(TAG, "  bande %2d (haut->bas) -> attendu %s sur GPIO%d, poids %d", i,
                     k_expected_name[i], (int)k_expected_gpio[i],
                     k_expected_weight[i]);
        }
        break;
    case DN_SCENE_NBITS:
        ESP_LOGI(TAG, "MIRE COMPLÉMENTAIRE — bande i = TOUS les bits SAUF i.");
        ESP_LOGI(TAG, "  Chaque bande est quasi BLANCHE ; la bande i tire vers la");
        ESP_LOGI(TAG, "  teinte complémentaire de son canal :");
        ESP_LOGI(TAG, "    un bit BLEU manquant   => la bande tire au JAUNE ;");
        ESP_LOGI(TAG, "    un bit VERT manquant   => elle tire au MAGENTA/ROSE ;");
        ESP_LOGI(TAG, "    un bit ROUGE manquant  => elle tire au CYAN.");
        ESP_LOGI(TAG, "  Plus le POIDS est fort, plus la teinte est marquée.");
        ESP_LOGI(TAG, "  C'est le recoupement de `bits` : là où `bits` rend les poids");
        ESP_LOGI(TAG, "  faibles invisibles, `nbits` rend les poids forts évidents.");
        break;
    case DN_SCENE_RGB:
        ESP_LOGI(TAG, "TROIS CANAUX PURS, empilés et étiquetés — un seul regard.");
        ESP_LOGI(TAG, "  bande ROUGE affichée bleue => canaux R et B permutés ;");
        ESP_LOGI(TAG, "  bande non pure (cyan, jaune, magenta) => octets échangés.");
        break;
    case DN_SCENE_COLOR_RED:
    case DN_SCENE_COLOR_GREEN:
    case DN_SCENE_COLOR_BLUE:
        ESP_LOGI(TAG, "COULEUR PURE — si la couleur affichée n'est pas celle annoncée");
        ESP_LOGI(TAG, "  en haut à gauche, les groupes de broches sont permutés.");
        ESP_LOGI(TAG, "  Un violet/magenta là où on attend du rouge = octets échangés.");
        break;
    case DN_SCENE_COLOR_WHITE:
        ESP_LOGI(TAG, "BLANC PLEIN — toutes les lignes de données à 1.");
        ESP_LOGI(TAG, "  Une teinte au lieu d'un blanc neutre = une ligne morte.");
        break;
    case DN_SCENE_COLOR_BLACK:
        ESP_LOGI(TAG, "NOIR PLEIN — toutes les lignes à 0.");
        ESP_LOGI(TAG, "  Sert de référence de fuite lumineuse ET de témoin :");
        ESP_LOGI(TAG, "  si le noir est identique à l'écran éteint, vérifier le rétroéclairage.");
        break;
    case DN_SCENE_FRAME:
        ESP_LOGI(TAG, "CADRAGE — preuve d'AC3 sur les bords.");
        ESP_LOGI(TAG, "  À vérifier UN PAR UN :");
        ESP_LOGI(TAG, "   1. le liseré blanc de 1 px est visible sur les QUATRE côtés ;");
        ESP_LOGI(TAG, "   2. les quatre coins portent une marque DIFFÉRENTE :");
        ESP_LOGI(TAG, "      HG carré ROUGE plein, HD équerre VERTE, BG équerre BLEUE,");
        ESP_LOGI(TAG, "      BD diagonale JAUNE. Un échange = rotation ou miroir.");
        ESP_LOGI(TAG, "   3. « HAUT » est en haut, « BAS » en bas ;");
        ESP_LOGI(TAG, "   4. la grille donne 6 colonnes x 8 lignes de 80 px, sans reste.");
        break;
    case DN_SCENE_GRAY:
        ESP_LOGI(TAG, "RAMPE — progression du noir (gauche) au blanc (droite).");
        ESP_LOGI(TAG, "  Les 3 bandes du bas isolent le canal fautif (R, V, B).");
        ESP_LOGI(TAG, "  ⚠️ CE QUI EST NORMAL ET N'EST PAS UN DÉFAUT : une fine");
        ESP_LOGI(TAG, "     alternation de lignes claires/sombres teintées VERT puis");
        ESP_LOGI(TAG, "     VIOLET. En RGB565 le vert a 6 bits contre 5 au rouge et au");
        ESP_LOGI(TAG, "     bleu : il avance deux fois plus vite dans la rampe, donc il");
        ESP_LOGI(TAG, "     prend puis rend l'avance à chaque pas. Cette alternance");
        ESP_LOGI(TAG, "     RÉGULIÈRE prouve au contraire que l'empaquetage 5-6-5 est bon.");
        ESP_LOGI(TAG, "  CE QUI SERAIT un défaut : des marches LARGES et IRRÉGULIÈRES, ou");
        ESP_LOGI(TAG, "     un endroit où la rampe REDEVIENT plus sombre en allant à droite.");
        ESP_LOGI(TAG, "  ⚠️ Du coup cette mire est un instrument GROSSIER pour l'ordre des");
        ESP_LOGI(TAG, "     bits : le bruit de quantification masque une petite permutation.");
        ESP_LOGI(TAG, "     Pour l'ordre des bits, c'est `bits` + `nbits` qui font foi.");
        break;
    case DN_SCENE_ASSET:
        ESP_LOGI(TAG, "ASSET Living PCB v0 — l'image de la partition `assets`.");
        ESP_LOGI(TAG, "  Vérifier les 4 bords (liseré vert vif) et les 4 coins :");
        ESP_LOGI(TAG, "  HG carré, HD disque, BG barre \\, BD barre /.");
        break;
    default:
        break;
    }
}
