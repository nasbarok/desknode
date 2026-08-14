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
#   3. trouver /dev/ttyACM<n>       -> l'énumération n'est pas instantanée, et
#                                      l'index n'est PAS garanti d'être 0
#   4. sudo chown                   -> udev ne tourne pas : aucune règle ne le fera
#
# Usage :  ./tools/wsl-attach.sh              attachement simple
#          ./tools/wsl-attach.sh --auto       + ré-attachement automatique après un reset de la puce
#          ./tools/wsl-attach.sh --stop-auto  arrête les processus --auto-attach résidents
#
# Quand faut-il --auto ? Mesuré en dn1-1, et ce n'est PAS ce qu'on croit :
#   - un FLASH ne ré-énumère pas l'USB : l'attachement simple y survit, --auto est inutile ;
#   - un vrai RESET DE LA PUCE (bouton RESET, ou `esptool.py --after watchdog_reset`) ré-énumère
#     l'USB et FAIT TOMBER l'attachement simple. Là, --auto le rétablit tout seul en ~6 s.
# ⚠️ Dans les deux cas, --auto ne restaure QUE le périphérique : les droits retombent à
#    root:root crw------- et le chown est à refaire. Le plus simple est de rejouer ce script.
# ⚠️ Un processus --auto-attach vivant REPREND la carte après un `usbipd detach` : il faut donc
#    `--stop-auto` avant de passer à la voie A (flash depuis Windows), sinon COM3 ne revient pas.
#
set -euo pipefail

VID_PID="303a:1001"          # USB natif de l'ESP32-S3 (Serial/JTAG) — mesuré, pas déduit
VID="303a"                   # les deux moitiés séparément, pour l'identification par sysfs
PID="1001"
USBIPD='C:\Program Files\usbipd-win\usbipd.exe'

usage() {
    cat <<EOF
Usage :  $0              attachement simple
         $0 --auto       + ré-attachement automatique après un reset de la puce
         $0 --stop-auto  arrête les processus --auto-attach résidents
EOF
    exit "${1:-2}"
}

AUTO=""
STOP_AUTO=""
case "${1:-}" in
    "")           ;;
    --auto)       AUTO="1" ;;
    --stop-auto)  STOP_AUTO="1" ;;
    -h|--help)    usage 0 ;;
    *)            echo "ÉCHEC : argument inconnu « $1 »." >&2; usage 2 ;;
esac
if [ "$#" -gt 1 ]; then
    echo "ÉCHEC : un seul argument accepté (reçu : $*)." >&2
    usage 2
fi

# `powershell.exe` n'est dans le PATH que si l'interop WSL a peuplé l'environnement.
# Un shell volontairement vidé (`env -i bash --noprofile --norc`, le cas du rejeu à
# froid d'AC7) ne l'a pas : on retombe alors sur le chemin absolu.
PWSH="$(command -v powershell.exe || true)"
if [ -z "$PWSH" ]; then
    PWSH="/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"
fi
if [ ! -x "$PWSH" ]; then
    echo "ÉCHEC : powershell.exe est introuvable (ni dans le PATH, ni en $PWSH)." >&2
    echo "        L'interop WSL->Windows est-elle active ? (/etc/wsl.conf, [interop])" >&2
    exit 1
fi

# Ne tue QUE les usbipd lancés avec --auto-attach : le service usbipd tourne sous le
# même nom d'exécutable et ne doit surtout pas être arrêté.
stop_auto_attach() {
    "$PWSH" -NoProfile -Command \
        "Get-CimInstance Win32_Process -Filter \"Name='usbipd.exe'\" |
         Where-Object { \$_.CommandLine -like '*--auto-attach*' } |
         ForEach-Object { Stop-Process -Id \$_.ProcessId -Force; 'arrêté PID ' + \$_.ProcessId }" \
        2>&1 | tr -d '\r' | sed 's/^/     /'
}

if [ -n "$STOP_AUTO" ]; then
    echo "Arrêt des processus usbipd --auto-attach résidents…"
    stop_auto_attach
    echo "Fait. La carte reste attachée jusqu'au prochain reset de la puce."
    exit 0
fi

echo "1/4  Chargement des modules noyau USB…"
for mod in vhci-hcd cdc-acm; do
    if ! sudo modprobe "$mod"; then
        echo "ÉCHEC : impossible de charger le module « $mod »." >&2
        echo "        Le noyau WSL doit être compilé avec CONFIG_USBIP_VHCI_HCD et CONFIG_USB_ACM." >&2
        exit 1
    fi
done

echo "2/4  Recherche de la carte ($VID_PID) dans 'usbipd list'…"
# On relit le BUSID à chaque fois : il change si la carte est branchée sur un
# autre port USB physique. Le figer dans le script serait un piège.
# ⚠️ L'affectation est SÉPARÉE de la vérification : sous `set -e`, un pipeline en
# échec tuerait le script avant tout message si les deux étaient fusionnés.
listing=""
if ! listing="$("$PWSH" -NoProfile -Command "& '$USBIPD' list" 2>&1)"; then
    echo "ÉCHEC : 'usbipd list' n'a pas abouti. Sortie brute :" >&2
    printf '%s\n' "$listing" | tr -d '\r' | sed 's/^/        /' >&2
    echo "        usbipd-win est-il installé ? ($USBIPD)" >&2
    exit 1
fi
listing="$(printf '%s\n' "$listing" | tr -d '\r')"

ligne="$(printf '%s\n' "$listing" | awk -v vp="$VID_PID" 'tolower($0) ~ vp { print; exit }' || true)"
if [ -z "$ligne" ]; then
    echo "ÉCHEC : aucun périphérique $VID_PID dans 'usbipd list'." >&2
    echo "        La carte est-elle branchée ? (un périphérique déjà attaché y figure aussi)" >&2
    printf '%s\n' "$listing" | sed 's/^/        /' >&2
    exit 1
fi

busid="$(printf '%s\n' "$ligne" | awk '{print $1}')"
case "$busid" in
    [0-9]*-[0-9]*) ;;
    *) echo "ÉCHEC : BUSID inattendu « $busid » extrait de : $ligne" >&2; exit 1 ;;
esac
echo "     BUSID = $busid"

case "$ligne" in
    *"Not shared"*)
        echo "ÉCHEC : la carte est « Not shared » — le 'bind' manque." >&2
        echo "        Dans une PowerShell ÉLEVÉE : usbipd bind --busid $busid" >&2
        echo "        (une seule fois : le bind est persistant, il survit aux reboots)" >&2
        exit 1
        ;;
esac

if [ -n "$AUTO" ]; then
    echo "3/4  Attachement à WSL (mode --auto-attach, processus résident)…"
    # Un --auto-attach déjà vivant sur ce BUSID rendrait le nouveau inutile et les
    # empilerait à chaque rejeu du script : on nettoie avant d'en lancer un.
    stop_auto_attach
    # --auto-attach ne rend jamais la main : on le détache dans un processus Windows
    # caché, sinon il bloquerait ce script.
    "$PWSH" -NoProfile -Command \
        "Start-Process -FilePath '$USBIPD' -ArgumentList 'attach','--wsl','--auto-attach','--busid','$busid' -WindowStyle Hidden" \
        2>&1 | tr -d '\r' | sed 's/^/     /'
elif printf '%s\n' "$ligne" | grep -q 'Attached'; then
    echo "3/4  Déjà attachée à WSL — rien à faire."
else
    echo "3/4  Attachement à WSL…"
    # 'attach' est idempotent en pratique : s'il est déjà attaché, il le dit et sort
    # en erreur — ce n'est pas fatal si le port est déjà là.
    "$PWSH" -NoProfile -Command "& '$USBIPD' attach --wsl --busid $busid" 2>&1 \
        | tr -d '\r' | sed 's/^/     /' || true
fi

# On ne cherche PAS /dev/ttyACM0 en dur : l'index dépend de ce qui est déjà énuméré,
# et surtout un nœud SURVIVANT à un reset (gardé ouvert par un moniteur) existe encore
# alors que le périphérique est mort. Le seul test fiable est l'identité en sysfs :
# elle disparaît avec le périphérique, contrairement au nœud dans /dev.
trouver_port() {
    local tty vend prod
    for tty in /sys/class/tty/ttyACM*; do
        [ -e "$tty/device" ] || continue
        vend="$(cat "$tty/device/../idVendor" 2>/dev/null || true)"
        prod="$(cat "$tty/device/../idProduct" 2>/dev/null || true)"
        if [ "$vend" = "$VID" ] && [ "$prod" = "$PID" ]; then
            echo "/dev/$(basename "$tty")"
            return 0
        fi
    done
    return 1
}

PORT=""
for _ in $(seq 1 20); do
    PORT="$(trouver_port || true)"
    [ -n "$PORT" ] && [ -e "$PORT" ] && break
    PORT=""
    sleep 0.5
done

if [ -z "$PORT" ]; then
    echo "ÉCHEC : aucun /dev/ttyACM* rattaché à $VID_PID après 10 s." >&2
    echo "        Vérifier 'usbipd list' (état attendu : Attached) et 'dmesg | tail'." >&2
    exit 1
fi

echo "4/4  Ouverture des droits sur $PORT…"
# udev ne tourne pas (systemd offline) : une règle udev ne se déclencherait JAMAIS.
# Le chown explicite est la seule voie, et il est à rejouer à chaque attachement.
# `chown` plutôt que `chmod 666` : le besoin est de donner le port à CET utilisateur,
# pas de l'ouvrir en écriture à tous les comptes de la distribution.
sudo chown "$(id -un)" "$PORT"
sudo chmod u+rw "$PORT"

etat="$(stat -c '%n  %U:%G  %A' "$PORT")"
echo
echo "Prêt : $etat"
if [ -n "$AUTO" ]; then
    echo "Mode --auto : le périphérique se ré-attachera seul après un reset de la puce,"
    echo "              mais les droits, eux, retombent — rejouer ce script pour les rouvrir."
    echo "              Pour l'arrêter (indispensable avant la voie A) :  $0 --stop-auto"
fi
echo "Boucle :  cd ~/projects/desknode/firmware/hello-desknode && idf.py -p $PORT flash monitor"
