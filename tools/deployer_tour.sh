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

# 🔴 LE CONTENU DU LANCEUR EST UNE **SOURCE UNIQUE** (revue dn4-8, 2026-08-21).
#    `--verifier` ne couvrait que `A_DEPOSER`, donc NI `PROVENANCE.txt` NI
#    `poser-permanence.cmd` — ce dernier etant un lanceur AUTO-ELEVATEUR
#    (`Start-Process -Verb RunAs`) pointant sur un chemin `%~dp0`. Une copie
#    editee sur la tour passait donc « OK — aucun ecart », alors que la these
#    meme de l'en-tete est « ⛔ NE PAS EDITER LES FICHIERS ICI ... l'ecart ne se
#    verrait nulle part ». Sur un poste partage, c'est un vecteur d'elevation.
# ⇒ Le texte vit ICI, il est ECRIT en mode depot et RECALCULE en mode verif.
CMD_PERMANENCE='@echo off
REM Pose la permanence LHM (tache planifiee au logon, RunLevel Highest).
REM Se releve tout seul : une invite UAC va apparaitre, il faut l'\''ACCEPTER.
REM L'\''autorite est le depot WSL - voir PROVENANCE.txt.
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "Start-Process powershell -Verb RunAs -ArgumentList '\''-NoProfile'\'','\''-ExecutionPolicy'\'','\''Bypass'\'','\''-NoExit'\'','\''-File'\'','\''%~dp0dn_lhm_tour.ps1'\'','\''-Permanence'\'','\''tache'\''"
'
VERIFIER=0
CIBLE="$CIBLE_DEFAUT"
for arg in "$@"; do
  case "$arg" in
    --verifier) VERIFIER=1 ;;
    -h|--help)  sed -n '2,30p' "${BASH_SOURCE[0]}"; exit 0 ;;
    # ⛔ TOUT CE QUI COMMENCE PAR `-` EST REFUSE (revue dn4-8, 2026-08-21).
    #    Le catch-all `*) CIBLE="$arg"` transformait n'importe quel drapeau mal
    #    tape en REPERTOIRE CIBLE : `--verify` (au lieu de `--verifier`) creait un
    #    dossier nomme « --verify » et y DEPOSAIT les fichiers, en annonçant un
    #    deploiement reussi. Un outil qui obeit a une faute de frappe ment.
    -*)         echo "  /!\ option inconnue : $arg" >&2
                echo "      options : --verifier | -h | <repertoire cible>" >&2
                exit 2 ;;
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

# 🔴 ON N'ECRIT PAS UNE PROVENANCE POUR UNE COPIE DECLAREE ABIMEE (revue dn4-8,
#    2026-08-21). `PROVENANCE.txt` et `poser-permanence.cmd` etaient emis
#    inconditionnellement, y compris apres la branche « COPIE ABIMEE » : le
#    fichier revendiquait donc un SHA pour des fichiers que le meme run venait de
#    declarer corrompus. ⛔ Une provenance qui certifie une copie cassee est pire
#    qu'aucune provenance : elle la fait passer pour bonne.
if [ "$VERIFIER" -eq 0 ] && [ "$ecarts" -ne 0 ]; then
  echo "  ⛔ PROVENANCE **NON ECRITE** : $ecarts ecart(s) sur la copie."
  echo "     Rien ne doit certifier une arborescence que ce run declare abimee."
fi
if [ "$VERIFIER" -eq 0 ] && [ "$ecarts" -eq 0 ]; then
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
  printf '%s' "$CMD_PERMANENCE" > "$CIBLE/poser-permanence.cmd"
  # 🔴 CRLF, ET C'EST OBLIGATOIRE (revue dn4-8, 2026-08-21). Le heredoc ecrivait
  #    des fins de ligne LF depuis WSL, alors que le fichier utilise une
  #    CONTINUATION `^` que `cmd.exe` ne parse de façon fiable QUE contre CRLF.
  #    En LF, le double-clic peut executer une ligne de commande TRONQUEE — et
  #    c'est une commande qui se releve en UAC.
  # ⚠️ On le fait avec `sed`, ⛔ pas `unix2dos` : cet outil n'est pas garanti
  #    present, et un deploiement qui echoue faute d'un paquet optionnel serait
  #    une dependance cachee.
  sed -i 's/$/\r/' "$CIBLE/poser-permanence.cmd"
  echo "  ecrit  : poser-permanence.cmd  (self-elevant, double-clic, CRLF)"
fi

# 🔴 LES DEUX FICHIERS **GENERES** SONT VERIFIES EUX AUSSI (revue 2026-08-21).
if [ "$VERIFIER" -eq 1 ]; then
  cmd_dst="$CIBLE/poser-permanence.cmd"
  if [ ! -f "$cmd_dst" ]; then
    echo "  MANQUE sur la tour : poser-permanence.cmd"; ecarts=$((ecarts+1))
  else
    # ⚠️ On compare APRES normalisation des fins de ligne : la copie deposee est
    #    en CRLF (obligatoire pour la continuation `^` de cmd.exe), la reference
    #    ci-dessus est en LF. Comparer les octets bruts crierait a chaque fois.
    att="$(printf '%s' "$CMD_PERMANENCE" | sha256sum | cut -c1-16)"
    vu="$(tr -d '\r' < "$cmd_dst" | sha256sum | cut -c1-16)"
    if [ "$att" = "$vu" ]; then
      echo "  identique : poser-permanence.cmd  ($vu)"
    else
      echo "  /!\ DIVERGE  : poser-permanence.cmd  attendu=$att  tour=$vu"
      echo "      ⛔ C'est le lanceur AUTO-ELEVATEUR (UAC). Une divergence ici"
      echo "         n'est pas cosmetique. Redeployer, ⛔ ne pas editer sur place."
      ecarts=$((ecarts+1))
    fi
    if ! grep -q $'\r' "$cmd_dst"; then
      echo "  /!\ poser-permanence.cmd est en LF : la continuation ^ de cmd.exe"
      echo "      peut executer une ligne TRONQUEE. Redeployer."
      ecarts=$((ecarts+1))
    fi
  fi
  # ⚠️ `PROVENANCE.txt` porte un HORODATAGE : son contenu n'est PAS comparable a
  #    l'octet, et le pretendre serait un faux controle. On verifie sa PRESENCE
  #    et qu'il vient bien de cet outil — et ON DIT ce qui n'est pas verifie.
  if [ ! -f "$CIBLE/PROVENANCE.txt" ]; then
    echo "  MANQUE sur la tour : PROVENANCE.txt"; ecarts=$((ecarts+1))
  elif ! grep -q "tools/deployer_tour.sh" "$CIBLE/PROVENANCE.txt"; then
    echo "  /!\ PROVENANCE.txt ne vient pas de cet outil"; ecarts=$((ecarts+1))
  else
    echo "  present   : PROVENANCE.txt  (⛔ contenu NON compare : il est horodate)"
  fi
fi

echo
if [ "$ecarts" -eq 0 ]; then
  echo "  OK — aucun ecart."
else
  echo "  /!\\ $ecarts ecart(s)."
fi
exit "$ecarts"
