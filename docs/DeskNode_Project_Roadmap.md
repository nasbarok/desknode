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

🔴 **CETTE LISTE EST PÉRIMÉE — ⛔ NE PAS LA CITER COMME SPEC.** Conservée comme trace de
l'intention d'origine (2026-08-14), **barrée** parce qu'elle a été remplacée par une décision, pas
par un oubli. Correct-course du **2026-08-20**.

-   ~~Heure~~
-   ~~Température~~
-   ~~Humidité~~
-   ~~Pression~~
-   ~~Qualité de l'air~~
-   ~~Lux~~
-   ~~Distance~~
-   ~~Tension~~
-   ~~Courant~~
-   ~~Puissance~~

*(dix entrées, dont une place pour chacun des trois capteurs)*

✅ **CE QUI FAIT FOI** : l'**addendum §1** du brief fige la grille **À SIX CASES**, et **les six
sont prises** :

> `CPU` · `GPU` · `RAM` · `RÉSEAU` · `DISQUE` · `AMBIANCE`

⇒ **Les trois capteurs branchés en `dn4-2` (BH1750, TOF050C-VL6180X, INA219) n'ont AUCUNE case.**
Ils sont **sur le bus et qualifiés** depuis le 2026-08-20 ; leur emploi est la question de
**`dn4-3`** — *« que gagnent-ils, et à quoi les dépense-t-on ? »* — et y répondre suppose d'**en
retirer une** ou de les loger ailleurs qu'en case du dashboard.

🔴 **RÉPONDU PAR AJOUT LE 2026-08-20 — `dn4-3` A TRANCHÉ, ET DANS LE SENS NÉGATIF POUR LA GRILLE.**
⛔ *(Cette entrée est restée ouverte alors que la story était close : relevé en revue de code.)*
✅ **DÉCISION OWNER : AUCUNE 3ᵉ grandeur, la case `AMBIANCE` reste à deux.** ⇒ **la grille à six ne
bouge pas, aucune case n'est retirée, `dn_ui.c` n'a PAS été touché** — et c'est le résultat le plus
sûr de la story pour la seule case vivante quand la tour dort.
**Les quatre candidats ont été mesurés au MÊME instrument** (`w2` : étendue ≥ 5 · taux de changement
du TEXTE ≥ 10 % · σ ≥ 1), sur les mêmes fenêtres, avec la **température comme témoin de contrôle** :

| Candidat | Sort | Motif **mesuré** |
|---|---|---|
| **Pression** | ⛔ éliminée | **1 hPa d'étendue en 17 min**, taux **1 %** — et elle n'avait pourtant PAS le conflit de verdict unique : c'est la mesure qui la tue, pas la conception |
| **ALS VL6180X** | ⛔ éliminé | réponse **strictement binaire** sur 7 points d'intégration — comparateur saturé, pas une intégration |
| **Gaz / qualité d'air** | ⛔ éliminé | **aucune réponse à deux bouffées** ; `iaq_score` inutilisable (3 défauts lus au source) ; coûte **+0,5 °C / −1,4 pt de RH** sur les deux grandeurs de la même case |
| **Lux BH1750** | ⛔ **non retenu — et ce n'est PAS un échec de qualification** | il **QUALIFIE largement** (jusqu'à **2 228 / 95 % / 568**). ⚠️ **C'est justement l'argument contre** : **10 à 70× la référence `FAN_RPM`** — un chiffre qui change 95 % du temps entre 0 et 2 438 serait **agitant** dans une case. **W2 est un seuil PLANCHER, ⛔ pas un optimum** |

🔴 **CE QUE LE REPLI COÛTE, ET IL FAUT L'ÉCRIRE** : le différenciateur *« PC éteint »* **n'est PAS
réparé par la grille** — `AMBIANCE` reste la seule case vivante quand la tour dort, avec ses deux
grandeurs, **exactement comme avant `dn4-3`**.
✅ **Il est réparé AILLEURS, et c'est mesuré** : **le rétroéclairage suit la pièce** (BH1750 → LEDC,
8 % à ≤ 20 lx, 100 % à ≥ 600 lx). ⚠️ **Mais ce n'est PAS une donnée affichée**, et le dire fait
partie du repli.
⇒ **L'emploi des trois capteurs est donc : le BH1750 pilote le rétroéclairage · l'INA219 et le
VL6180X sont lus en régime, instrumentés et gardés contre le fantôme, sans rien afficher.**
⚠️ **Et l'INA219 ne mesure PAS le rail du module** : `Vin+`/`Vin−` ne sont pas câblés — tranché
**NON par la mesure** (X3), `dn4-5` devra mesurer la consommation autrement.

⚠️ **TROIS ENTRÉES SONT MORTES AUTREMENT QUE PAR LE COMPTE, et c'est la part qui ne se devine pas :**

| Entrée | Pourquoi elle est morte |
|---|---|
| **Pression** · **Qualité de l'air** | Elles viennent du BME680, dont **le gaz est coupé DÉLIBÉRÉMENT** (**D7**) : sa plaque à 300 °C chaufferait le die qui porte le thermomètre, pour une donnée hors des six widgets. A/B jouable à chaud : `capteurs gaz on` |
| **Distance** | Plafonnée à **100 mm GARANTIS** (TOF050C-VL6180X), ⛔ pas aux « 50 cm » de l'annonce revendeur — mesuré et tranché le 2026-08-20 |

⚠️ **Heure** n'est pas morte : elle vit **dans la barre**, pas dans une case — et elle affiche
**« --:-- HEURE NON POSÉE »** tant que l'oscillateur RTC a décroché (`OS = 1`), ⛔ jamais une heure
fausse.

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
