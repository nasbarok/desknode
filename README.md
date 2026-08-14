# DeskNode

Mini-display tactile 2,8" (Waveshare **ESP32-S3-Touch-LCD-2.8B**, 480×640 IPS portrait) monté sur
la façade de la tour PC (NZXT Phantom 630). Affiche en continu 6 métriques — CPU, GPU, RAM,
réseau (via un agent Windows) + température, humidité (capteurs I²C locaux) — avec deux états
visuels (**Ambient** H24 / **Actif** au toucher) et une identité « **Living PCB** ».

## Pilotage projet

Le cockpit BMad (brief, epics, stories, sprint status) vit dans le repo `compagnon_project` :

- Brief : `compagnon_project/_bmad-output/planning-artifacts/briefs/brief-desknode-2026-08-14/`
- Epics V1 : `compagnon_project/_bmad-output/planning-artifacts/epics-desknode-v1.md`

La V1 avance par **escalier de mini-POC** (P0 toolchain → P9 endurance H24), chaque marche
fermant une question technique par la mesure. Les choix techniques (framework, transport
PC↔module, agent Windows) sont **ouverts** tant qu'un POC ne les a pas tranchés.

## Arborescence

```
docs/       vision, roadmap, notes de câblage, photos
firmware/   firmware ESP32-S3 (framework à trancher en P0)
hardware/   inventaire des breakouts, brochages, schéma V1
assets/     assets graphiques 480×640 (Living PCB, icônes, mockups)
agent/      DeskNode PC Agent (Windows)
tests/      harnais et smokes
```

## Matériel

| Module | Rôle | I²C |
|---|---|---|
| ESP32-S3-Touch-LCD-2.8B | carte + écran + tactile (16 MB flash / 8 MB PSRAM, IMU QMI8658, RTC PCF85063, buzzer) | ext. : SCL=GPIO7, SDA=GPIO15 |
| BME680 | température, humidité, pression, VOC | 0x76/0x77 |
| BH1750 | luminosité ambiante | 0x23 |
| VL53L0X | proximité / présence | 0x29 |
| INA219 | tension / courant / puissance | 0x40 |
