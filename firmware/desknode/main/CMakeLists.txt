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
        # lvgl et esp_lvgl_port ne sont PAS listés ici : le gestionnaire de
        # composants ajoute tout seul à `main` les dépendances déclarées dans
        # main/idf_component.yml. Les répéter créerait deux sources de vérité,
        # et c'est déjà le cas d'esp_lcd_st7701 & co depuis dn1-2.
)
