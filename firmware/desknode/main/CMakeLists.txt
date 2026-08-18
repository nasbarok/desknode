idf_component_register(
    SRCS
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
        "fonts/dn_font_14.c"
        "fonts/dn_font_28.c"
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
