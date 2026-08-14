#!/usr/bin/env bash
#
# DeskNode — rend la carte visible depuis WSL (voie C, usbipd).
#
# À rejouer après CHAQUE `wsl --shutdown`, reboot Windows, ou débranchement de la
# carte. Les quatre gestes qu'il enchaîne sont les quatre coûts récurrents de la
# voie C, mesurés en dn1-1 :
#
#   1. charger vhci-hcd + cdc-acm   -> ne survivent pas à un arrêt de WSL, et
#                                      /etc/modules-load.d/ est INOPÉRANT ici
#                                      (systemd est offline sur cette machine)
#   2. attacher le BUSID            -> ne survit pas à un débranchement
#   3. attendre /dev/ttyACM0        -> l'énumération n'est pas instantanée
#   4. sudo chmod 666               -> udev ne tourne pas : aucune règle ne le fera
#
# Usage :  ./tools/wsl-attach.sh           attachement simple
#          ./tools/wsl-attach.sh --auto    + ré-attachement automatique après un reset de la puce
#
# Quand faut-il --auto ? Mesuré en dn1-1, et ce n'est PAS ce qu'on croit :
#   - un FLASH ne ré-énumère pas l'USB : l'attachement simple y survit, --auto est inutile ;
#   - un vrai RESET DE LA PUCE (bouton RESET, ou `esptool --after watchdog-reset`) ré-énumère
#     l'USB et FAIT TOMBER l'attachement simple. Là, --auto le rétablit tout seul en ~6 s.
# ⚠️ Dans les deux cas, --auto ne restaure QUE le périphérique : les droits retombent à
#    root:root crw------- et le chmod est à refaire. Le plus simple est de rejouer ce script.
#
set -euo pipefail

AUTO=""
if [ "${1:-}" = "--auto" ]; then AUTO="--auto-attach"; fi

VID_PID="303a:1001"          # USB natif de l'ESP32-S3 (Serial/JTAG) — mesuré, pas déduit
PORT="/dev/ttyACM0"
USBIPD='C:\Program Files\usbipd-win\usbipd.exe'

echo "1/4  Chargement des modules noyau USB…"
sudo modprobe vhci-hcd
sudo modprobe cdc-acm

echo "2/4  Recherche du BUSID de la carte ($VID_PID)…"
# On relit le BUSID à chaque fois : il change si la carte est branchée sur un
# autre port USB physique. Le figer dans le script serait un piège.
busid="$(powershell.exe -NoProfile -Command "& '$USBIPD' list" 2>/dev/null \
         | tr -d '\r' \
         | awk -v vp="$VID_PID" 'tolower($0) ~ vp { print $1; exit }')"

if [ -z "${busid:-}" ]; then
    echo "ÉCHEC : aucun périphérique $VID_PID dans 'usbipd list'." >&2
    echo "        La carte est-elle branchée ? Est-elle déjà attachée à WSL ?" >&2
    exit 1
fi
echo "     BUSID = $busid"

if [ -n "$AUTO" ]; then
    echo "3/4  Attachement à WSL (mode --auto-attach, processus résident)…"
    # --auto-attach ne rend jamais la main : on le détache dans un processus Windows
    # caché, sinon il bloquerait ce script.
    powershell.exe -NoProfile -Command \
        "Start-Process -FilePath '$USBIPD' -ArgumentList 'attach','--wsl','--auto-attach','--busid','$busid' -WindowStyle Hidden" \
        >/dev/null 2>&1
else
    echo "3/4  Attachement à WSL…"
    # 'attach' est idempotent en pratique : s'il est déjà attaché, il le dit et sort
    # en erreur — ce n'est pas fatal si le port est déjà là.
    powershell.exe -NoProfile -Command "& '$USBIPD' attach --wsl --busid $busid" 2>&1 \
        | tr -d '\r' | sed 's/^/     /' || true
fi

for _ in $(seq 1 20); do
    [ -e "$PORT" ] && break
    sleep 0.5
done

if [ ! -e "$PORT" ]; then
    echo "ÉCHEC : $PORT n'est pas apparu après 10 s." >&2
    echo "        Vérifier 'usbipd list' (état attendu : Attached)." >&2
    exit 1
fi

echo "4/4  Ouverture des droits sur $PORT…"
# udev ne tourne pas (systemd offline) : une règle udev ne se déclencherait JAMAIS.
# Le chmod explicite est la seule voie, et il est à rejouer à chaque attachement.
sudo chmod 666 "$PORT"

echo
echo "Prêt : $(stat -c '%n  %U:%G  %A' "$PORT")"
if [ -n "$AUTO" ]; then
    echo "Mode --auto : le périphérique se ré-attachera seul après un reset de la puce,"
    echo "              mais les droits, eux, retombent — rejouer ce script pour les rouvrir."
fi
echo "Boucle :  cd firmware/hello-desknode && idf.py -p $PORT flash monitor"
