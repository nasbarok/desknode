/*
 * DeskNode — `dn_reglage` : LES RÉGLAGES D'AFFICHAGE POSÉS AU DOIGT, ET LEUR
 * PERSISTANCE. Né de `dn4-41` / AC4.
 *
 * ── 🔴 POURQUOI UN FICHIER À LUI, ET ⛔ PAS UNE POIGNÉE DE LIGNES AILLEURS ───
 *
 * **D16 est une contrainte DURE** : `dn_env.c` doit rester **HORS de la table**
 * de `tools/verif_d4_nvs_dn45.py`. L'asservissement ne persiste rien, et c'est
 * ce qui garantit **D4** — *aucune écriture NVS EN RÉGIME*. Le réglage manuel,
 * lui, DOIT survivre au reboot : sans ça, l'inconnu qui a réglé sa dalle la
 * retrouve au défaut à chaque coupure de courant.
 * ⇒ L'écrivain vit ICI, et **la classification « HORS RÉGIME » porte sur UN
 *   FICHIER dont c'est la seule raison d'être**.
 *
 * ⛔ **ET C'EST POUR ÇA QUE CE N'EST NI `dn_ui.c` NI `dn_veille.c`** :
 *   · `dn_ui.c` porte AUSSI la boucle de rendu. Le classer HORS RÉGIME serait
 *     une déclaration au fichier qui couvrirait, demain, une écriture EN
 *     RÉGIME ajoutée par quelqu'un d'autre — le défaut « gate scopée qui épingle
 *     vert le même défaut ailleurs » (`dn4-16`), payé une fois déjà.
 *   · `dn_veille.c` est **déjà** dans la table : y ajouter l'écrivain aurait
 *     rendu la gate INCAPABLE DE ROUGIR sur l'oubli de déclaration — or AC4.5
 *     exige de l'AVOIR VUE ROUGIR. Une garde qu'on ne peut pas voir échouer est
 *     décorative (`dn4-13`/AC7.5).
 *
 * ── ⛔ ÉCRITURE PAR GESTE UNIQUEMENT (D4) ────────────────────────────────────
 * Les deux fonctions `…_ecrire` ne sont appelées QUE depuis un callback de tap
 * du MENU ou depuis la console. **Aucune boucle périodique n'entre ici.** Un
 * soak sans-les-mains n'en produit AUCUNE — c'est ce que `veille` prouve déjà
 * pour ses deux clés, et l'instrument est le même : un compteur d'écritures.
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>
#include "esp_err.h"

/* Relit la NVS. ⚠️ À appeler APRÈS `nvs_flash_init()`. Absente ⇒ les défauts. */
void dn_reglage_init(void);

/*
 * 🔴 LE NIVEAU MANUEL, EN %. C'est le duty que la dalle prend quand
 * l'asservissement est DÉSARMÉ et que l'utilisateur l'a choisi au doigt.
 *
 * ⚠️ `dn_reglage_bl_manuel()` rend **-1** tant qu'AUCUN niveau n'a été choisi —
 *    un **ÉTAT**, ⛔ pas un pourcentage. C'est la même convention que
 *    `dn_env_bl_cible()`, et pour la même raison : `0` est un duty LÉGITIME
 *    (noir), donc il ne peut pas servir de sentinelle.
 */
int dn_reglage_bl_manuel(void);
esp_err_t dn_reglage_bl_manuel_ecrire(int pct);

/*
 * L'ÉTAT D'ARMEMENT VOULU PAR L'UTILISATEUR, ⛔ à ne pas confondre avec
 * `dn_env_bl_auto()` qui est l'état COURANT.
 * ⚠️ Ils DIVERGENT, et c'est voulu : sur une carte sans BH1750, l'utilisateur
 *    peut avoir demandé `auto` (préférence conservée) pendant que le firmware
 *    a DÉSARMÉ parce que la source est ABSENTE (AC3). Fusionner les deux
 *    effacerait sa préférence au premier boot sans capteur.
 */
bool dn_reglage_bl_auto_voulu(void);
esp_err_t dn_reglage_bl_auto_ecrire(bool on);

/* AC9.1 de `dn4-5`, transposé : l'instrument qui prouve D4 sur CE fichier.
 * ⛔ Un écrivain non instrumenté ne peut pas être disculpé après un soak. */
uint32_t dn_reglage_ecritures(void);
uint32_t dn_reglage_derniere_us(void);

/*
 * 🔴 L'ÉCHELLE DES CRANS MANUELS — UNE SEULE DÉFINITION, ET ELLE EST DÉRIVÉE.
 *
 * ⛔ Les valeurs ne sont écrites NULLE PART en littéral : `dn_reglage_bl_cran()`
 * les calcule entre `DN_ENV_BL_PCT_MIN` (le plancher de lisibilité MESURÉ) et
 * `DN_ENV_BL_PCT_ABS_MAX` (le maximum PHYSIQUE de la dalle). Deux endroits qui
 * énoncent les mêmes nombres finissent par diverger, et c'est l'écran qui
 * mentirait — le motif est déjà écrit au-dessus des crans de `DELAI`.
 *
 * 🔴 ET LE BAS DE L'ÉCHELLE EST LE PLANCHER DE LISIBILITÉ, ⛔ PAS 0. Motif :
 *    `bl 0` = **noir**, et un inconnu qui noircit sa dalle depuis le MENU
 *    **n'a pas de console pour revenir**. La console, elle, garde `bl 0` : c'est
 *    un geste d'opérateur outillé. ⇒ ⛔ ce n'est pas un écrêtage silencieux,
 *    c'est une échelle qui ne propose pas l'irrécupérable.
 */
#define DN_REGLAGE_BL_CRANS 4
int dn_reglage_bl_cran(int i);
