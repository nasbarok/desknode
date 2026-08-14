# DeskNode -- Vision & Roadmap

## Objectif

Créer une plateforme de bureau basée sur ESP32-S3 servant de laboratoire
embarqué, tableau de bord tactile et base réutilisable pour Kido.

## Matériel V1

  Module                    Rôle
  ------------------------- ---------------------------------------------------
  Waveshare ESP32-S3 2.8"   Carte principale
  BME680                    Température, humidité, pression, qualité de l'air
  BH1750                    Luminosité
  TOF050C                   Distance / proximité
  INA219                    Mesure tension/courant

## Arborescence

    DeskNode/
    docs/
    firmware/
    drivers/
    screens/
    widgets/
    services/
    hardware/
    assets/
    tests/

## Roadmap

1.  Bring-up (ESP32, écran, tactile, LVGL)
2.  Drivers des capteurs
3.  Dashboard temps réel
4.  Widgets et UX
5.  Wi-Fi, OTA, REST, MQTT, Home Assistant
6.  Historique et graphiques
7.  Veille intelligente

## Dashboard V1

-   Heure
-   Température
-   Humidité
-   Pression
-   Qualité de l'air
-   Lux
-   Distance
-   Tension
-   Courant
-   Puissance

## V2

-   GPS
-   LoRa
-   Micro I2S
-   MAX98357A
-   Caméra
-   APDS9960
-   QMC5883L
-   NFC/RFID

## Bonnes pratiques

-   Un commit par fonctionnalité
-   Documenter chaque capteur
-   Photos de câblage
-   Captures d'écran
-   Code réutilisable pour Kido

## Critères de réussite

-   Tous les capteurs opérationnels
-   Dashboard fluide
-   OTA fonctionnel
-   Documentation complète
