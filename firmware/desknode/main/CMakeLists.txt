# ══ dn4-14-2 / AC3.1 — LES `.c` DE POLICE SONT DÉCOUVERTS, ⛔ PLUS ÉNUMÉRÉS ═══
#
# 🔴 CE QUE CE GLOB RÉPARE, ET C'EST UN DÉFAUT MESURÉ. La liste des polices
#    était ÉCRITE À LA MAIN ci-dessous (`fonts/dn_font_14.c`, `_28`, `_33`,
#    `_56`). Ajouter une taille à `TAILLES` dans `tools/gen_font_dn.py`
#    produisait donc un `.c` que PERSONNE NE COMPILAIT — et le seul symptôme
#    était un `undefined reference` au LINK, c'est-à-dire APRÈS avoir payé la
#    régénération complète. C'est la SECONDE moitié du défaut d'AC3.1 :
#    `dn_font.h` ne DÉCLARAIT pas la police neuve (corrigé dans le générateur),
#    et CMake ne la COMPILAIT pas (corrigé ici).
# ⚠️ `CONFIGURE_DEPENDS` fait re-globber CMake À CHAQUE BUILD : sans lui, un
#    `.c` neuf resterait invisible jusqu'au prochain `idf.py reconfigure`, et on
#    aurait remplacé une liste périmée par un cache périmé.
# ⛔ CE GLOB NE CHANGE RIEN À LA DÉCISION W6 : les `.c` restent VERSIONNÉS, pas
#    produits au build. Il découvre ce qui est DANS L'ARBRE, il ne génère rien.
#    Un clone neuf SANS RÉSEAU compile toujours.
# ⚠️ LES DEUX MODES, ET CE N'EST PAS DU ZÈLE : ESP-IDF relit CE FICHIER EN
#    « SCRIPT MODE » pour résoudre les dépendances de composants
#    (`component_get_requirements.cmake`), et CMake y REFUSE `CONFIGURE_DEPENDS`
#    — « CONFIGURE_DEPENDS is invalid for script and find package modes ».
#    Sans la garde, le projet ne CONFIGURE plus du tout. Mesuré, ⛔ pas prévu.
if(CMAKE_SCRIPT_MODE_FILE)
    file(GLOB DN_FONTS "${CMAKE_CURRENT_LIST_DIR}/fonts/dn_font_*.c")
else()
    file(GLOB DN_FONTS CONFIGURE_DEPENDS
         "${CMAKE_CURRENT_LIST_DIR}/fonts/dn_font_*.c")
endif()

# ══ dn4-24 / AC3.3 — LE GLOB NE COMPILE PLUS UN `.c` ÉGARÉ EN SILENCE ════════
#
# 🔴 LE DÉFAUT. `file(GLOB fonts/dn_font_*.c)` prend TOUT ce qui porte le nom.
#    Un `dn_font_20.c` oublié par une régénération abandonnée, un
#    `dn_font_28.c.orig` renommé, une police d'essai laissée là : CMake les
#    compile, le binaire grossit, et **rien ne le dit**. Le glob a résolu le
#    défaut inverse (une liste écrite qui périme) — il a apporté le sien.
# ⛔ ON NE REVIENT PAS À UNE LISTE MANUELLE : c'est exactement ce que ce glob a
#    remplacé, et le motif est écrit ci-dessus. La parade est un CONTRÔLE.
#
# ⚖️ CE QUI FAIT AUTORITÉ : `fonts/dn_font.h`. C'est le fichier que le CODE
#    inclut ; une police qu'il ne DÉCLARE pas n'est utilisable par personne, et
#    la compiler ne peut donc que gonfler le binaire. ⛔ Ce n'est PAS
#    `tools/gen_font_dn.py` : lui dit ce qu'on SAIT produire, pas ce que
#    l'arbre PORTE ni ce que le code ATTEINT.
#
# ⚠️ LA DIRECTION INVERSE — une police déclarée dont le `.c` manque — n'est
#    volontairement PAS gardée ici : elle échoue déjà bruyamment, en
#    `undefined reference` au LINK. Le silence n'était que d'un côté.
# ── REVUE DE CODE DU 2026-08-31 — TROIS FAÇONS DONT CE CONTRÔLE PASSAIT ─────
#
# 🔴 (1) `NAME_WE` COUPE L'EXTENSION LA PLUS LONGUE, ET C'EST LE SCÉNARIO QUE
#     LE COMMENTAIRE CI-DESSUS NOMME LUI-MÊME. Mesuré sous `cmake -P` :
#         dn_font_28.orig.c  →  NAME_WE = [dn_font_28]   ⇒ DÉCLARÉE ⇒ ACCEPTÉE
#         dn_font_28.orig.c  →  NAME_WLE = [dn_font_28.orig]  ⇒ épinglée
#     La sauvegarde que le défaut cite en exemple traversait donc le contrôle
#     écrit pour elle. ⇒ le nom est désormais exigé EXACTEMENT : `dn_font_<n>.c`.
# 🔴 (2) `dn_font.h` ÉTAIT LU BRUT : un `LV_FONT_DECLARE` MORT, laissé en
#     commentaire, légitimait un orphelin. Mesuré : `/* exemple :
#     LV_FONT_DECLARE(dn_font_20) */` ajouté ⇒ un `dn_font_20.c` égaré passe
#     ET entre dans `DN_FONTS`. ⇒ les commentaires sont retirés d'abord.
# 🟠 (3) SYMÉTRIQUEMENT, `LV_FONT_DECLARE (dn_font_44)` avec une espace faisait
#     un FATAL_ERROR sur une police LÉGITIME. ⇒ l'espace est tolérée.
# ⚠️ (4) `dn_font.h` N'ÉTAIT PAS DANS `CMAKE_CONFIGURE_DEPENDS` : retirer un
#     `LV_FONT_DECLARE` sans toucher aux `.c` ne re-configurait RIEN, et
#     l'orphelin neuf restait compilé jusqu'à un build propre. Le
#     `CONFIGURE_DEPENDS` du glob ne couvre que les `.c`, ⛔ pas l'en-tête qui
#     fait autorité.
if(NOT CMAKE_SCRIPT_MODE_FILE)
    set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
                 "${CMAKE_CURRENT_LIST_DIR}/fonts/dn_font.h")
endif()
file(READ "${CMAKE_CURRENT_LIST_DIR}/fonts/dn_font.h" DN_FONT_H_TXT)
# (2) Retirer les commentaires AVANT de lire les déclarations : `/* ... */`
#     d'abord (non gourmand), puis `// ...` jusqu'à la fin de ligne.
string(REGEX REPLACE "/\\*([^*]|\\*+[^*/])*\\*+/" " " DN_FONT_H_TXT "${DN_FONT_H_TXT}")
string(REGEX REPLACE "//[^\n]*" " " DN_FONT_H_TXT "${DN_FONT_H_TXT}")
# (3) L'espace avant/dans la parenthèse est tolérée.
string(REGEX MATCHALL "LV_FONT_DECLARE[ \t]*\\([ \t]*[A-Za-z0-9_]+[ \t]*\\)"
       DN_FONTS_DECLAREES "${DN_FONT_H_TXT}")
set(DN_FONTS_CONNUES "")
foreach(d ${DN_FONTS_DECLAREES})
    string(REGEX REPLACE "LV_FONT_DECLARE[ \t]*\\([ \t]*([A-Za-z0-9_]+)[ \t]*\\)" "\\1" n "${d}")
    list(APPEND DN_FONTS_CONNUES "${n}")
endforeach()
if(DN_FONTS_CONNUES STREQUAL "")
    message(FATAL_ERROR
        "dn4-24/AC3.3 : AUCUN LV_FONT_DECLARE lu dans fonts/dn_font.h. "
        "Le controle du glob ne peut pas s'exercer — il ne passe PAS en silence.")
endif()
foreach(f ${DN_FONTS})
    get_filename_component(nom_complet "${f}" NAME)
    # (1) LE NOM EST EXIGE EXACTEMENT. ⛔ Ni NAME_WE (qui coupe `.orig.c` en
    #     `dn_font_28`), ni NAME_WLE seul : c'est la FORME du nom qui décide.
    if(NOT nom_complet MATCHES "^dn_font_[0-9]+\\.c$")
        message(FATAL_ERROR
            "dn4-24/AC3.3 (revue 2026-08-31) : fonts/${nom_complet} est ramasse "
            "par le glob mais son nom n'est pas de la forme dn_font_<n>.c.\n"
            "  ⇒ c'est un RESIDU (sauvegarde, essai, renommage). L'EFFACER ou le "
            "sortir de fonts/. ⛔ NAME_WE le faisait passer pour la police "
            "qu'il sauvegarde.")
    endif()
    string(REGEX REPLACE "\\.c$" "" n "${nom_complet}")
    if(NOT n IN_LIST DN_FONTS_CONNUES)
        message(FATAL_ERROR
            "dn4-24/AC3.3 : fonts/${n}.c est ramasse par le glob mais n'est "
            "DECLARE nulle part dans fonts/dn_font.h.\n"
            "  Polices declarees : ${DN_FONTS_CONNUES}\n"
            "  ⇒ soit c'est un residu a EFFACER, soit dn_font.h doit le "
            "declarer. ⛔ Le compiler en silence gonflait le binaire sans "
            "qu'aucun code ne puisse l'atteindre.")
    endif()
endforeach()

idf_component_register(
    SRCS
        ${DN_FONTS}
        "desknode_main.c"
        "dn_display.c"
        "dn_patterns.c"
        "dn_measure.c"
        "dn_stimulus.c"
        "dn_asset.c"
        "dn_bootcfg.c"
        "dn_console.c"
        "dn_recal.c"
        "dn_ui.c"
        "dn_touch.c"
        "dn_link.c"
        "dn_capteurs.c"
        # dn4-3 : les TROIS capteurs d'environnement locaux (BH1750, INA219,
        # VL6180X). Drivers MAISON — X5 tranché en §13.19.4 après lecture du
        # source des CINQ candidats du registre : le mieux adopté
        # (`espressif/bh1750` 2.0.0) bloque 1 000 ms par transaction, et il
        # n'existe AUCUN composant VL6180X (404 vérifié).
        # ⛔ Rien à ajouter aux REQUIRES : il n'utilise que `driver`
        #    (i2c_master), déjà listé. Aucune entrée au manifeste non plus :
        #    c'est ce qui garde le compte de 103 `ESP_ERROR_CHECK` à 103.
        # ⚠️ AUCUNE TÂCHE : il est cadencé par celle de dn_capteurs (voie C).
        "dn_env.c"
        # dn3-2 : l'heure du module (PCF85063A @ 0x51). Driver MAISON — W1
        # tranché après lecture du source des deux composants du registre :
        # `waveshare/pcf85063a` masque le bit OS (`& 0x7F`, deux sites) et
        # `espp/pcf85063` est du C++ avec deux dépendances de framework.
        # ⛔ Rien à ajouter aux REQUIRES : il n'utilise que `driver` (i2c_master),
        #    déjà listé.
        "dn_rtc.c"
        "dn_wifi.c"
        # dn3-1 : le modèle de widget, et les deux polices GÉNÉRÉES.
        # ⚠️ Les `.c` de police sont VERSIONNÉS (décision W6), pas produits au
        #    build : `lv_font_conv` est une dépendance npm absente du tableau des
        #    versions figées, et un `idf.py build` sur un clone neuf SANS RÉSEAU
        #    échouerait. Ce n'est PAS le même arbitrage que l'asset Living PCB,
        #    dont le générateur est en stdlib Python pure.
        #    Régénération : `python3 tools/gen_font_dn.py` (voir README).
        "dn_widget.c"
        "dn_hist.c"
        # dn3-3 : la VEILLE (`Ambient`) — état, délai, compteurs, persistance.
        # ⛔ Rien à ajouter aux REQUIRES : il n'utilise que `nvs_flash` (déjà
        #    listé) et `esp_timer` (déjà listé). ⚠️ Il ne touche NI LVGL, NI la
        #    dalle, NI le rétroéclairage — et c'est ce qui le rend compilable et
        #    APPELABLE sur l'hôte par `tools/verif_veille_dn33.py`, sans carte.
        #    ⛔ Ne pas y ajouter d'appel à `dn_ui`/`dn_display` : la gate
        #    cesserait de pouvoir l'exécuter, et redeviendrait décorative.
        "dn_veille.c"
        # 🔴 `dn4-41` — les reglages d'affichage poses AU DOIGT et leur
        #    persistance. ⛔ Un fichier a lui : D16 exige que `dn_env.c` reste
        #    HORS de la table de `tools/verif_d4_nvs_dn45.py`, et AC4.5 exige
        #    d'avoir VU la gate ROUGIR sur l'oubli de declaration — ce qui
        #    suppose un ecrivain dans un fichier QUI N'Y EST PAS DEJA.
        "dn_reglage.c"
        # 🔴 `dn4-42` — LA TABLE DES LANGUES. Une seule definition par chaine
        #    AFFICHEE SUR LA DALLE, depliee par X-macro en une colonne par
        #    langue. ⛔ Rien a ajouter aux REQUIRES : il n'utilise que `log`,
        #    deja tire par le composant. ⚠️ Il ne touche NI LVGL NI la dalle —
        #    c'est ce qui permet a `dn_reglage_init()` de poser la langue AVANT
        #    que la moindre scene n'existe.
        "dn_langue.c"
        # 🔴 `dn4-43` — LA DECISION DE L'ETAT DE DEMARRAGE. ⛔ AUCUN `#include`
        #    du framework : ni LVGL, ni ESP-IDF, ni meme `esp_log.h`. C'est
        #    EXACTEMENT le motif ecrit plus haut pour `dn_veille.c` — c'est ce
        #    qui permet a `tools/verif_demarrage_dn443.py` de le COMPILER en
        #    `.so` et d'APPELER ses fonctions en ctypes, avec de vrais chiffres,
        #    au lieu de les lire au `grep`. ⚠️ Et ici il n'y a meme pas de shim a
        #    ecrire, donc aucun shim a laisser deriver.
        #    ⛔ Ne rien y ajouter qui vienne du framework : la gate cesserait de
        #    pouvoir l'executer, et redeviendrait decorative.
        "dn_demarrage.c"
        # ⚠️ LES `.c` DE POLICE SONT DANS `${DN_FONTS}`, EN HAUT DE CE FICHIER —
        #    découverts par `file(GLOB … CONFIGURE_DEPENDS)`, ⛔ plus énumérés
        #    ici. Voir le motif au glob : une liste écrite à la main faisait
        #    échouer au LINK toute taille ajoutée à `TAILLES`.
        # 🔴 dn3-3 : DEUX de ces polices sont celles de la VEILLE, plage RÉDUITE
        #    (0x20-0x7F,0xB0). En Ambient le titre, l'icône et le libellé
        #    disparaissent : il ne reste que des valeurs, donc NI accents NI
        #    symboles NI FontAwesome — et c'est ce qui rend l'agrandissement
        #    abordable (97 glyphes au lieu de 259). ⚠️ Leurs DEUX tailles sont
        #    MESURÉES contre la largeur utile d'une case (201 px) : 33 px AVEC
        #    l'unité, 56 px SANS.
        #    ⛔ Ne jamais s'en servir pour du texte d'interface : un accent
        #       manquant ne produit AUCUNE erreur, juste un blanc.
        #    ⇒ C'est `DN_FONT_LISTE` (dans `fonts/dn_font.h`, générée) qui dit
        #      laquelle est d'INTERFACE et laquelle est de VEILLE.
    INCLUDE_DIRS "."
    REQUIRES
        driver
        esp_lcd
        esp_psram
        esp_timer
        nvs_flash
        spi_flash
        console
        esp_driver_i2c
        esp_driver_gpio
        # dn1-3 : LEDC pilote le rétroéclairage (GPIO6) en PWM.
        esp_driver_ledc
        # dn1-3 : esp_cache_msync() — le chemin de flush « direct » resynchronise
        # LUI-MÊME les lignes salies, au lieu de laisser draw_bitmap parcourir
        # les 614 400 o du framebuffer entier à chaque appel.
        esp_mm
        # 🔴 dn2-2, VERDICT T5 : la maquette branche B (WiFi WebSocket) n'est
        # PLUS liée. Le verrou 1 l'a tuée par la mesure : le simple LINK de
        # esp_wifi/esp_netif/esp_event/esp_http_server coûtait 53 480 o de
        # .bss en RAM interne et 583 664 o de flash ; initialisée, la pile
        # laissait 6 407 o libres (3 795 sous churn) ; la variante
        # SPIRAM_TRY_ALLOCATE_WIFI_LWIP ne démarrait pas (ESP_ERR_NO_MEM,
        # 4/16 tampons RX). Chiffres et symptômes : hardware/ §12.
        # POUR RE-MESURER : ré-ajouter ici esp_wifi, esp_netif, esp_event,
        # esp_http_server, et CONFIG_HTTPD_WS_SUPPORT=y aux defaults
        # (`rm sdkconfig && idf.py build`) — dn_wifi.c se recompile tout seul.
        # lvgl et esp_lvgl_port ne sont PAS listés ici : le gestionnaire de
        # composants ajoute tout seul à `main` les dépendances déclarées dans
        # main/idf_component.yml. Les répéter créerait deux sources de vérité,
        # et c'est déjà le cas d'esp_lcd_st7701 & co depuis dn1-2.
)
