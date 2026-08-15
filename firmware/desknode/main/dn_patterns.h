/*
 * DeskNode — les mires de validation (AC1, Task 3).
 *
 * Ce ne sont pas des jolis dessins : ce sont des INSTRUMENTS. Chacune répond à
 * une question précise, et une seule.
 *
 *   bits    : quelle broche porte quel bit ? (la question d'AC1)
 *   colors  : y a-t-il inversion, permutation R<->B, ou échange d'octets ?
 *   frame   : l'image occupe-t-elle vraiment les 480x640 ? (la question d'AC3)
 *   gray    : la dalle rend-elle une rampe monotone ? (détecte un bit mort)
 *
 * Elles restent dans le firmware après dn1-2 : elles resserviront à chaque
 * marche, et notamment le jour où quelqu'un doutera du brochage.
 */
#pragma once

#include <stdint.h>

typedef enum {
    DN_SCENE_BITS = 0,
    DN_SCENE_NBITS,
    DN_SCENE_RGB,
    DN_SCENE_COLOR_RED,
    DN_SCENE_COLOR_GREEN,
    DN_SCENE_COLOR_BLUE,
    DN_SCENE_COLOR_WHITE,
    DN_SCENE_COLOR_BLACK,
    DN_SCENE_FRAME,
    DN_SCENE_GRAY,
    DN_SCENE_ASSET,
    DN_SCENE_COUNT,
} dn_scene_t;

const char *dn_scene_name(dn_scene_t scene);

/* Cherche une scène par son nom. Renvoie DN_SCENE_COUNT si inconnue. */
dn_scene_t dn_scene_from_name(const char *name);

/* Dessine la mire dans `buf` (307 200 pixels). Ne présente pas : c'est
 * l'appelant qui décide quand. Enregistre au passage la scène demandée, que
 * dn_pattern_last_scene() restitue. */
void dn_pattern_draw(uint16_t *buf, dn_scene_t scene);

/*
 * Dernière scène passée à dn_pattern_draw(), ou DN_SCENE_COUNT si aucune.
 *
 * POURQUOI CET ACCESSEUR EXISTE (AC4) : app_main dessine DN_SCENE_ASSET au
 * boot en appelant dn_pattern_draw + dn_display_present directement, sans
 * passer par la console. Un état « scène courante » tenu dans dn_console.c est
 * donc structurellement en retard : il annonce « aucune scène » alors qu'une
 * image est affichée depuis le démarrage, et la PREMIÈRE ligne `fps` sort
 * étiquetée `scene=-`. La source de vérité est ce module, qui sait ce qu'il a
 * dessiné ; les afficheurs d'état l'interrogent au lieu de tenir un double.
 */
dn_scene_t dn_pattern_last_scene(void);

/* Remplit `buf` d'une couleur unie. */
void dn_pattern_fill(uint16_t *buf, uint16_t color);

/* Décrit à la console CE QU'IL FAUT REGARDER, pour que l'observation soit
 * comparable d'une fois sur l'autre. Une mire sans grille de lecture produit
 * des impressions, pas des mesures. */
void dn_pattern_explain(dn_scene_t scene);
