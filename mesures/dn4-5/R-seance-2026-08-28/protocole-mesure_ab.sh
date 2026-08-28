#!/usr/bin/env bash
# A/B du chemin chaud LVGL — protocole IDENTIQUE des deux cotes.
# ⛔ Une capture `cpu brut` INCOMPLETE (sans `total`) est REJETEE et REJOUEE :
#    reconstruire le total a partir d'IDLE1 fabriquerait un chiffre.
set -u
E="$1"; D=/tmp/claude-1000/-home-nasbarok-projects-compagnon-project/0103c285-23d0-44d4-8c6e-e6f162e1249f/scratchpad
C="python3 /home/nasbarok/projects/desknode/tools/dn_console.py --timeout 25"
cd /home/nasbarok/projects/desknode

cpu_sur() {   # $1 = fichier de sortie ; jusqu'a 4 essais
  for i in 1 2 3 4; do
    $C "cpu brut" > "$1" 2>&1
    if grep -qE '^IDLE0' "$1" && grep -qE '^total' "$1"; then return 0; fi
  done
  echo "  ⛔ capture cpu INCOMPLETE apres 4 essais : $1" >&2
  return 1
}

$C "anim off"     >/dev/null 2>&1
$C "flush reset"  >/dev/null 2>&1
$C "anim on"      >/dev/null 2>&1
cpu_sur "$D/$E-cpu1.txt" || exit 1
$C --listen 30    >/dev/null 2>&1
cpu_sur "$D/$E-cpu2.txt" || exit 1
$C "flush"        > "$D/$E-flush.txt" 2>&1
$C "anim off"     >/dev/null 2>&1
grep -q "aire cumulée" "$D/$E-flush.txt" || { echo "  ⛔ capture flush INCOMPLETE : $E" >&2; exit 1; }
echo "capture $E : OK"
