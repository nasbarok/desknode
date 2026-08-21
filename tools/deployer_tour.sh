#!/usr/bin/env bash
# =============================================================================
#  deployer_tour.sh — DEPOSE l'outillage cote TOUR sur un disque Windows
# =============================================================================
#
#  POURQUOI. `dn_lhm_tour.ps1` tourne sur la tour, en PowerShell 5.1, et souvent
#  ELEVE. Le lancer depuis `\\wsl.localhost\...` marche, mais oblige a taper un
#  chemin UNC a chaque fois et rend le clic-droit « Executer en tant
#  qu'administrateur » impraticable. On depose donc une copie sur un disque
#  local de la tour.
#
#  🔴 L'AUTORITE RESTE LE DEPOT, ⛔ PAS LA COPIE.
#     La copie est un ARTEFACT DE DEPLOIEMENT. Elle porte un `PROVENANCE.txt`
#     qui dit d'ou elle vient, quand, et sous quel SHA — et ce script REVERIFIE
#     l'empreinte apres copie. ⛔ Ne jamais editer la copie : le prochain
#     deploiement l'ecrase, et l'ecart ne se verrait nulle part.
#     C'est exactement le defaut « deux vérités contradictoires » que ce depot
#     traque (checksum faux publie dans TROIS fichiers d'autorite a la fois).
#
#  EMPLOI
#    ./tools/deployer_tour.sh              # depose dans la cible par defaut
#    ./tools/deployer_tour.sh /mnt/h/dev/projets/desknode
#    ./tools/deployer_tour.sh --verifier   # ne copie RIEN, compare et rapporte
#
#  ⛔ Il ne depose QUE l'outillage cote Windows. Le firmware, l'agent et les
#     instruments WSL restent dans le depot.
# =============================================================================
set -uo pipefail

CIBLE_DEFAUT="/mnt/h/dev/projets/desknode"
RACINE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Ce qui part sur la tour. ⛔ Liste EXPLICITE : pas de `cp -r tools/`, sinon un
# instrument WSL (dn_console.py, wsl-attach.sh) atterrirait sur la tour ou il ne
# peut pas tourner, et quelqu'un finirait par essayer.
A_DEPOSER=(
  "tools/dn_lhm_tour.ps1"
)

VERIFIER=0
CIBLE="$CIBLE_DEFAUT"
for arg in "$@"; do
  case "$arg" in
    --verifier) VERIFIER=1 ;;
    -h|--help)  sed -n '2,30p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *)          CIBLE="$arg" ;;
  esac
done

echo "=== deployer_tour.sh ==="
echo "  source : $RACINE"
echo "  cible  : $CIBLE"

if [ ! -d "$(dirname "$CIBLE")" ]; then
  echo "  /!\\ Le parent de la cible n'existe pas : $(dirname "$CIBLE")"
  echo "      (le disque Windows est-il monte ? 'ls /mnt/' pour voir)"
  exit 2
fi

# --- l'etat du depot fait partie du livrable -------------------------------
SHA="$(git -C "$RACINE" rev-parse --short HEAD 2>/dev/null || echo INCONNU)"
SALE="$(git -C "$RACINE" status --porcelain 2>/dev/null | wc -l)"
echo "  HEAD   : $SHA"
if [ "$SALE" -ne 0 ]; then
  echo "  /!\\ ARBRE SALE ($SALE fichier(s)) — le SHA ci-dessus NE DECRIT PAS ce qui est copie."
fi

[ "$VERIFIER" -eq 0 ] && mkdir -p "$CIBLE"

ecarts=0
for rel in "${A_DEPOSER[@]}"; do
  src="$RACINE/$rel"
  dst="$CIBLE/$(basename "$rel")"
  if [ ! -f "$src" ]; then
    echo "  /!\\ ABSENT du depot : $rel"; ecarts=$((ecarts+1)); continue
  fi
  hs="$(sha256sum "$src" | cut -c1-16)"
  if [ "$VERIFIER" -eq 1 ]; then
    if [ ! -f "$dst" ]; then
      echo "  MANQUE sur la tour : $(basename "$rel")"; ecarts=$((ecarts+1))
    else
      hd="$(sha256sum "$dst" | cut -c1-16)"
      if [ "$hs" = "$hd" ]; then echo "  identique : $(basename "$rel")  ($hs)"
      else echo "  /!\\ DIVERGE  : $(basename "$rel")  depot=$hs  tour=$hd"; ecarts=$((ecarts+1)); fi
    fi
    continue
  fi
  cp -f "$src" "$dst"
  hd="$(sha256sum "$dst" | cut -c1-16)"
  # (!) On RELIT ce qu'on vient d'ecrire. Une copie vers un montage Windows peut
  #     echouer partiellement sans que `cp` le dise.
  if [ "$hs" = "$hd" ]; then echo "  depose : $(basename "$rel")  ($hs)"
  else echo "  /!\\ COPIE ABIMEE : $(basename "$rel")  depot=$hs  tour=$hd"; ecarts=$((ecarts+1)); fi
done

if [ "$VERIFIER" -eq 0 ]; then
  cat > "$CIBLE/PROVENANCE.txt" <<EOF
Cette arborescence est une COPIE DE DEPLOIEMENT. ⛔ L'AUTORITE EST LE DEPOT.

  depot   : ~/projects/desknode  (WSL Ubuntu)
  HEAD    : $SHA$([ "$SALE" -ne 0 ] && echo "   /!\\ ARBRE SALE au moment du depot ($SALE fichier(s)) : ce SHA ne decrit PAS ces fichiers")
  depose  : $(date -Iseconds)
  par     : tools/deployer_tour.sh

⛔ NE PAS EDITER LES FICHIERS ICI. Le prochain deploiement les ecrase, et l'ecart
   ne se verrait nulle part. Toute modification se fait dans le depot, puis :
       ~/projects/desknode/tools/deployer_tour.sh
   Pour comparer sans rien ecraser :
       ~/projects/desknode/tools/deployer_tour.sh --verifier

CE QUE FAIT dn_lhm_tour.ps1 (dn4-8 / D13)
  .\\dn_lhm_tour.ps1                          VERIFIE, ne change RIEN
  .\\dn_lhm_tour.ps1 -Poser                   installe ce qui manque + serveur web
  .\\dn_lhm_tour.ps1 -Permanence tache        tache planifiee au logon, ELEVEE
  .\\dn_lhm_tour.ps1 -Retirer                 retire la tache (ne desinstalle rien)
EOF
  echo "  ecrit  : PROVENANCE.txt"

  # Raccourci self-elevant : le geste owner en un double-clic.
  cat > "$CIBLE/poser-permanence.cmd" <<'EOF'
@echo off
REM Pose la permanence LHM (tache planifiee au logon, RunLevel Highest).
REM Se releve tout seul : une invite UAC va apparaitre, il faut l'ACCEPTER.
REM ⛔ L'autorite est le depot WSL — voir PROVENANCE.txt.
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "Start-Process powershell -Verb RunAs -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-NoExit','-File','%~dp0dn_lhm_tour.ps1','-Permanence','tache'"
EOF
  echo "  ecrit  : poser-permanence.cmd  (self-elevant, double-clic)"
fi

echo
if [ "$ecarts" -eq 0 ]; then
  echo "  OK — aucun ecart."
else
  echo "  /!\\ $ecarts ecart(s)."
fi
exit "$ecarts"
