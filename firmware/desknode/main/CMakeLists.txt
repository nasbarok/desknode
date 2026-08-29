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
