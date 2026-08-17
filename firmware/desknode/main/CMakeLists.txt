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
        "dn_wifi.c"
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
