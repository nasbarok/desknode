/*
 * DeskNode — console série, pour ne PAS reflasher entre deux observations.
 *
 * AC1 demande plusieurs mires, AC4 la même mesure dans plusieurs
 * configurations, AC5 et AC6 des A/B. Reflasher entre chaque, c'est 6 s de
 * flash mais surtout un binaire différent à chaque fois — une variable de plus
 * qu'on ne contrôle pas. Ici : UN binaire, des commandes.
 *
 * Elle parle sur l'USB-Serial/JTAG, donc dans `idf.py monitor` : on tape la
 * commande dans le même terminal que celui où l'on lit le log.
 */
#pragma once

#include "esp_err.h"

esp_err_t dn_console_start(void);

/* Affiche l'aide et l'état courant. Appelé aussi au boot, pour que la première
 * chose visible au moniteur soit ce qu'on peut faire. */
void dn_console_banner(void);
