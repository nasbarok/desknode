#!/usr/bin/env bash
#
# DeskNode — REPRENDRE LA MAIN SUR LE PORT, EN UN GESTE, DANS LES DEUX SENS.
#                                                                     (dn4-17)
# C'est le `tools/rendre-port.sh` que `dn4-5` nommait et que personne n'avait
# écrit (`deferred-work.md:1348`). Le port est EXCLUSIF : l'agent (Windows,
# COM3) et la boucle de flash (WSL, /dev/ttyACM*) ne coexistent JAMAIS.
#
#   ./tools/rendre-port.sh --vers-agent   rendre le port à Windows (l'agent)
#   ./tools/rendre-port.sh --vers-flash   reprendre la carte sous WSL (flash)
#   ./tools/rendre-port.sh --etat         ne change RIEN, dit tout
#
# ── CE QU'IL REMPLACE, ET CE QUE ÇA COÛTAIT ─────────────────────────────────
# Le rituel écrit au README : une ÉTAPE 0 (tuer les veilleurs des deux côtés)
# + 3 commandes, et **il échoue**. Un `detach` est défait en quelques secondes
# par un veilleur résiduel ⇒ l'agent trouve un COM3 fantôme
# (`FileNotFoundError`), l'état usbipd peut se bloquer en « Attached »
# orphelin, et la récupération demande de tuer les veilleurs PUIS un RESET
# physique. Le réattachement coûte 2,7–3,1 s (mesuré en dn4-3).
#
# ── TROIS RÈGLES, CHACUNE PAYÉE PAR UNE MESURE ──────────────────────────────
# 1. 🔴 LE BUSID EST RELU À CHAQUE APPEL, ⛔ JAMAIS EN DUR. Il SUIT LE PORT
#    PHYSIQUE : `usbipd list` rend `3-1` le 2026-08-26 là où `dn4-15` a compté
#    `3-7`. Les deux ont été vrais. Aucun ne l'est en dur.
# 2. 🔴 UN `detach` QUI A RENDU 0 N'A PAS FORCÉMENT TENU. Les veilleurs
#    ressuscitent en ~2 s ⇒ on RELIT après délai, et on échoue bruyamment.
# 3. 🔴 LE VERDICT EST L'ÉTAT DU PORT, ⛔ PAS LE COMPTE DE VEILLEURS TUÉS.
#    Une `CommandLine` illisible est classée « pas un veilleur » EN SILENCE
#    par `wsl-attach.sh:75-81` — mesuré le 2026-08-26 sur usbipd.exe PID 6056,
#    dont la CommandLine est VIDE. Le compte a un mode d'aveuglement MESURÉ.
#
set -uo pipefail

VID_PID="303a:1001"
USBIPD='C:\Program Files\usbipd-win\usbipd.exe'
SERIE="${DN_SERIE:-COM3}"
TOUR_WIN="${DN_TOUR_WIN:-H:\\dev\\projets\\desknode}"
# ⚠️ REVUE DU 2026-08-26 — `TOUR_WIN` ET LA CIBLE DE `deployer_tour.sh` NE SONT
#    PAS RELIEES : ici `H:\dev\projets\desknode`, la-bas
#    `/mnt/h/dev/projets/desknode`, deux notations, aucune ne lit l'autre. Un
#    depot ailleurs (cas documente a l'EMPLOI du deployeur) fait appeler ici un
#    `.bat` inexistant ; l'erreur PowerShell part dans `sed`, le code de retour
#    n'est pas teste, et la cause affichee est fausse.
# ⇒ On le VERIFIE avant de s'en servir, et on nomme les deux variables.
RACINE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# Délai de re-vérification du detach. Les veilleurs ressuscitent en ~2 s
# (README étape 2) : on regarde APRÈS, sinon on regarde avant le problème.
DELAI_REVERIF="${DN_DELAI_REVERIF:-4}"
# 🔴 REVUE DU 2026-08-26 — CETTE VARIABLE D'ENVIRONNEMENT DESARMAIT LA REGLE
#    N°2 DE L'EN-TETE DE CE SCRIPT. `DN_DELAI_REVERIF=0` (ou une valeur non
#    numerique : `sleep` echoue, et il n'y a pas de `set -e`) supprimait le
#    delai ⇒ la relecture avait lieu AVANT la resurrection des veilleurs
#    (~2 s) et l'outil declarait « le detach a TENU » sur un port qui allait
#    redevenir fantome. Une garde qu'une variable peut eteindre n'est pas une
#    garde. ⇒ Entier, et jamais sous le temps de resurrection MESURE.
case "$DELAI_REVERIF" in
  ''|*[!0-9]*) echo "ÉCHEC : DN_DELAI_REVERIF='$DELAI_REVERIF' n'est pas un entier." >&2; exit 2 ;;
esac
if [ "$DELAI_REVERIF" -lt 3 ]; then
  echo "ÉCHEC : DN_DELAI_REVERIF=$DELAI_REVERIF est SOUS le temps de resurrection" >&2
  echo "        mesuré des veilleurs (~2 s). Re-vérifier plus tôt que le problème" >&2
  echo "        ne se produit, c'est ne pas le vérifier. Minimum : 3." >&2
  exit 2
fi

PWSH="$(command -v powershell.exe || true)"
[ -z "$PWSH" ] && PWSH="/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"
if [ ! -x "$PWSH" ]; then
  echo "ÉCHEC : powershell.exe introuvable (interop WSL désactivée ?)" >&2; exit 1
fi

t0="$(date +%s.%N)"
chrono() { awk -v a="$t0" -v b="$(date +%s.%N)" 'BEGIN{printf "%.1f", b-a}'; }
dire()   { printf '  %s\n' "$*"; }
etape()  { printf '\n[%ss] %s\n' "$(chrono)" "$*"; }
crier()  { printf '  /!\\ %s\n' "$*" >&2; }

# ⚠️ `Set-Location` D'ABORD : ce script tourne depuis WSL, donc le cwd de
#    PowerShell est un chemin UNC `\\wsl.localhost\...`. Tout `cmd.exe`
#    lance de la crie « Les chemins UNC ne sont pas pris en charge » et
#    bascule ailleurs — un bruit qui ressemble a une panne et n'en est pas.
ps_win() { "$PWSH" -NoProfile -Command "Set-Location \$env:SystemRoot; $1" 2>&1 | tr -d '\r'; }

# --- les trois lectures d'état, aucune n'écrit -----------------------------
lister_usbipd() { ps_win "& '$USBIPD' list"; }

ligne_carte() {
  lister_usbipd | awk -v vp="$VID_PID" 'tolower($0) ~ vp { print; exit }'
}

busid_relu() {
  local l b
  l="$(ligne_carte)"
  [ -z "$l" ] && return 1
  b="$(printf '%s\n' "$l" | awk '{print $1}')"
  case "$b" in [0-9]*-[0-9]*) printf '%s' "$b"; return 0 ;; esac
  return 1
}

# 🔴 REVUE DU 2026-08-26 — CETTE FONCTION POUVAIT RENDRE UN **MESSAGE
#    D'ERREUR** COMME ETAT DE PORT, ET LES APPELANTS LE PRENAIENT POUR UN
#    SUCCES. `ps_win()` fusionne stderr dans stdout (`2>&1`) et jette le code
#    de retour ; la valeur 'libre'/'tenu' etait emise AVANT le
#    `finally { Dispose() }`, donc un `Dispose()` qui leve (port qui disparait
#    en cours de sonde) plaçait l'enregistrement d'erreur APRES la valeur, et
#    `tail -1` rendait le texte de l'erreur.
#    ⇒ Consequences MESUREES A LA LECTURE :
#      · `--vers-agent` etape 4 : `[ "$P" != "absent" ] && break`, puis les
#        deux tests suivants echouent ⇒ **« ✅ Le port est à Windows »** sur un
#        etat INCONNU ;
#      · `--vers-flash` etape 1 : seul `"tenu"` bloque ⇒ l'outil **attache la
#        carte à WSL** alors que `COM3` peut encore etre tenu. C'est
#        exactement le nœud mort que cet outil existe pour empecher.
# ⇒ ON MARQUE LA VALEUR, et tout ce qui n'est pas marque est `inconnu`.
#   ⛔ Plus jamais « ce que la derniere ligne contenait ».
etat_com() {   # absent | libre | tenu | fantome | inconnu
  local brut val
  brut="$(ps_win "\$n=[System.IO.Ports.SerialPort]::GetPortNames()
          if (\$n -notcontains '$SERIE') { 'DN_ETAT=absent' } else {
            \$sp = New-Object System.IO.Ports.SerialPort '$SERIE',115200
            \$sp.DtrEnable = \$false ; \$sp.RtsEnable = \$false
            try { \$sp.Open(); \$sp.Close(); 'DN_ETAT=libre' }
            catch [System.IO.FileNotFoundException] { 'DN_ETAT=fantome' }
            catch [System.UnauthorizedAccessException] { 'DN_ETAT=tenu' }
            catch { 'DN_ETAT=inconnu' }
            finally { \$sp.Dispose() } }")"
  val="$(printf '%s\n' "$brut" | sed -n 's/^DN_ETAT=\([a-z]*\)$/\1/p' | head -1)"
  case "$val" in
    absent|libre|tenu|fantome) printf '%s' "$val" ;;
    *) # ⛔ NI un etat, NI une erreur qu'on peut ignorer : on le DIT, et on
       #   rend `inconnu` — que les appelants traitent comme BLOQUANT.
       printf '%s\n' "$brut" | sed 's/^/       | /' >&2
       printf 'inconnu' ;;
  esac
}

etat_tty() {
  local tty vend prod
  for tty in /sys/class/tty/ttyACM*; do
    [ -e "$tty/device" ] || continue
    vend="$(cat "$tty/device/../idVendor" 2>/dev/null || true)"
    prod="$(cat "$tty/device/../idProduct" 2>/dev/null || true)"
    if [ "$vend" = "303a" ] && [ "$prod" = "1001" ]; then
      printf '/dev/%s' "$(basename "$tty")"; return 0
    fi
  done
  return 1
}

# --- la chasse aux veilleurs, DES DEUX CÔTÉS -------------------------------
# ⚠️ Elle NE TRANCHE RIEN : c'est l'état du port qui tranche (règle 3). Ce
#    qu'elle fait, c'est retirer la cause connue de la rechute.
tuer_veilleurs() {
  local n_win n_wsl
  n_win="$(ps_win "\$v = @(Get-CimInstance Win32_Process -Filter \"Name='usbipd.exe'\" |
             Where-Object { \$_.CommandLine -like '*--auto-attach*' })
           \$v | ForEach-Object { Stop-Process -Id \$_.ProcessId -Force }
           \$v.Count" | tail -1)"
  # 🔴 ⛔ PAS DE REPLI `echo 0` DANS LA SUBSTITUTION ICI.
  #    `pkill -c` SORT EN 1 quand il ne tue
  #    rien, ET IL A DEJA IMPRIME « 0 » : le repli en ajoutait un SECOND, la
  #    variable valait la chaine "0\n0" et le message se cassait en deux
  #    lignes. C'est le defaut D-A de `deployer_tour.sh`, re-fabrique ici —
  #    VU A L'EXECUTION le 2026-08-26. Le `||` porte sur L'AFFECTATION.
  n_wsl="$(pkill -c -f 'usbip.*auto-attach' 2>/dev/null)" || n_wsl=0
  dire "veilleurs tués : Windows=$n_win  WSL=$n_wsl"
  # 🔴 ET ON DIT CE QU'ON NE SAIT PAS. Un usbipd.exe dont la CommandLine est
  #    illisible n'a PAS pu être classé — il n'est ni tué, ni innocenté.
  local muets
  muets="$(ps_win "@(Get-CimInstance Win32_Process -Filter \"Name='usbipd.exe'\" |
             Where-Object { -not \$_.CommandLine }).Count" | tail -1)"
  if [ "${muets:-0}" != "0" ]; then
    crier "$muets usbipd.exe à CommandLine ILLISIBLE : ni tués, ni innocentés."
    crier "    (faux négatif MESURÉ le 2026-08-26 — PID 6056). Le verdict reste l'état du port."
  fi
}

resume() {
  local l
  l="$(ligne_carte)"
  dire "usbipd : ${l:-(carte $VID_PID ABSENTE du bus)}"
  dire "$SERIE  : $(etat_com)"
  dire "ttyACM : $(etat_tty || echo 'aucun')"
}

usage() {
  sed -n '2,12p' "${BASH_SOURCE[0]}" | sed 's/^# \?//'
  exit "${1:-2}"
}

SENS=""
case "${1:-}" in
  --vers-agent) SENS=agent ;;
  --vers-flash) SENS=flash ;;
  --etat)       SENS=etat ;;
  -h|--help)    usage 0 ;;
  "")           echo "ÉCHEC : préciser le sens." >&2; usage 2 ;;
  *)            echo "ÉCHEC : argument inconnu « $1 »." >&2; usage 2 ;;
esac
[ "$#" -gt 1 ] && { echo "ÉCHEC : un seul argument." >&2; usage 2; }

echo "=== rendre-port.sh — $SENS ==="

if [ "$SENS" = "etat" ]; then
  resume
  exit 0
fi

# --- le busid, RELU ---------------------------------------------------------
BUSID="$(busid_relu || true)"
if [ -z "$BUSID" ]; then
  crier "aucun périphérique $VID_PID dans 'usbipd list' — la carte est-elle branchée ?"
  lister_usbipd | sed 's/^/      /' >&2
  # ⛔ On ne devine PAS un busid. Le figer serait le piège que wsl-attach.sh
  #    documente déjà : il suit le port physique.
  exit 1
fi
dire "BUSID relu : $BUSID   (⛔ jamais en dur : il suit le port physique)"

case "$SENS" in

# ===========================================================================
agent)
  etape "1/4  Veilleurs --auto-attach (les deux côtés)"
  tuer_veilleurs

  etape "2/4  detach $BUSID"
  ps_win "& '$USBIPD' detach --busid $BUSID" | sed 's/^/     /'

  etape "3/4  Re-vérification APRÈS ${DELAI_REVERIF}s (les veilleurs ressuscitent en ~2 s)"
  sleep "$DELAI_REVERIF"
  L="$(ligne_carte)"
  dire "usbipd : ${L:-(disparue du bus)}"
  case "$L" in
    *Attached*)
      crier "LE DETACH N'A PAS TENU : la ligne est repassée à « Attached »."
      crier "    Un veilleur a survécu (peut-être à CommandLine illisible)."
      crier "    ⛔ Ne PAS lancer l'agent : il trouverait un $SERIE fantôme."
      exit 3 ;;
  esac
  case "$L" in
    *Shared*) dire "STATE = Shared — le detach a TENU." ;;
    *)        crier "STATE inattendu, ni Attached ni Shared. Ligne brute ci-dessus." ;;
  esac

  etape "4/4  VERDICT : $SERIE doit APPARAÎTRE côté Windows"
  P=""
  for _ in $(seq 1 20); do
    P="$(etat_com)"
    [ "$P" != "absent" ] && break
    sleep 0.5
  done
  dire "$SERIE : $P"
  # 🔴 REVUE DU 2026-08-26 — LE SUCCÈS ÉTAIT LA BRANCHE DE **FALL-THROUGH** :
  #    tout ce qui n'était ni « absent » ni « tenu » tombait sur le ✅, y
  #    compris un texte d'erreur PowerShell rendu par `tail -1`. ⇒ On ÉNUMÈRE
  #    les états, et l'inconnu est BLOQUANT. Un verdict ne se donne pas par
  #    défaut.
  case "$P" in
    absent)
      crier "$SERIE n'apparaît pas après 10 s. Le detach a tenu mais Windows n'énumère pas."
      exit 4 ;;
    fantome)
      crier "$SERIE est ÉNUMÉRÉ mais NE S'OUVRE PAS (FileNotFound) — c'est le COM"
      crier "    FANTÔME : un veilleur a déjà repris la carte pour WSL."
      crier "    ⛔ Ce n'est PAS « le port est à Windows »."
      dire  "usbipd : $(ligne_carte)"
      exit 4 ;;
    inconnu)
      crier "L'état de $SERIE est INCONNU (voir la sortie brute ci-dessus)."
      crier "    ⛔ On ne déclare pas un succès sur un état qu'on n'a pas lu."
      exit 4 ;;
    tenu)
      dire "(i) $SERIE existe et est DÉJÀ TENU — un agent tourne probablement déjà." ;;
    libre) : ;;
  esac
  echo
  echo "  ✅ Le port est à Windows en $(chrono) s. Lancer l'agent :"
  echo "        (sur la tour)  $TOUR_WIN\\dn-agent.bat"
  ;;

# ===========================================================================
flash)
  etape "1/4  Arrêter l'agent — et LE PROUVER (⛔ pas par un code de retour)"
  # Piège P2, mesuré sur ce poste : tout process Windows survit à la mort de
  # son lanceur (Edge headless : 416 process / 11,6 Go ; un python vivant
  # 29 min après son lanceur). Un agent qu'on CROIT mort peut tenir COM3.
  # ⚠️ REVUE DU 2026-08-26 — ON VÉRIFIE QUE LE `.bat` EXISTE, ET ON LUI PASSE
  #    LE PORT. `DN_SERIE=COM7 ./rendre-port.sh --vers-flash` arrêtait l'agent
  #    de **COM3** (valeur par défaut du `.bat`) puis vérifiait **COM7** :
  #    deux ports différents dans un même geste, sans que rien ne le dise.
  BAT_WIN="$TOUR_WIN\\dn-agent.bat"
  if ! ps_win "if (Test-Path '$BAT_WIN') { 'DN_BAT=oui' } else { 'DN_BAT=non' }" \
       | grep -q 'DN_BAT=oui'; then
    crier "dn-agent.bat INTROUVABLE sur la tour : $BAT_WIN"
    crier "    (DN_TOUR_WIN pointe-t-il la même cible que deployer_tour.sh ?)"
    crier "    ⛔ Sans lui, impossible d'arrêter l'agent PROPREMENT. Rien n'est attaché."
    exit 5
  fi
  ps_win "& '$BAT_WIN' stop $SERIE" | sed 's/^/     /'
  P="$(etat_com)"
  dire "$SERIE après stop : $P"
  # 🔴 REVUE DU 2026-08-26 — SEUL « tenu » BLOQUAIT. Tout le reste — y compris
  #    un texte d'erreur — laissait l'outil ATTACHER LA CARTE À WSL alors que
  #    le port pouvait être encore tenu côté Windows : le nœud mort que cet
  #    outil existe précisément pour empêcher.
  case "$P" in
    libre) : ;;
    tenu)
      crier "$SERIE est ENCORE TENU : l'agent (ou un autre process) ne l'a pas rendu."
      crier "    ⛔ L'attachement à WSL échouerait ou donnerait un nœud mort."
      exit 5 ;;
    absent)
      dire "(i) $SERIE n'existe plus côté Windows — la carte est déjà partie." ;;
    fantome)
      crier "$SERIE est un FANTÔME : énuméré, mais il ne s'ouvre pas."
      crier "    Un veilleur a déjà repris la carte. On repart d'une base propre :"
      crier "    ⛔ on n'attache pas par-dessus un état qu'on n'a pas nettoyé." ;;
    *)
      crier "L'état de $SERIE est INCONNU (sortie brute ci-dessus)."
      crier "    ⛔ On n'attache PAS la carte sur un état qu'on n'a pas lu."
      exit 5 ;;
  esac

  etape "2/4  Veilleurs --auto-attach (on repart d'une base propre)"
  tuer_veilleurs

  etape "3/4  wsl-attach.sh (busid relu par lui aussi)"
  "$RACINE/tools/wsl-attach.sh" 2>&1 | sed 's/^/     /'
  rc=${PIPESTATUS[0]}
  if [ "$rc" -ne 0 ]; then
    crier "wsl-attach.sh a échoué (code $rc)."
    exit 6
  fi

  etape "4/4  VERDICT : /dev/ttyACM* présent ET écrivable"
  TTY="$(etat_tty || true)"
  if [ -z "$TTY" ]; then
    crier "aucun /dev/ttyACM* rattaché à $VID_PID."
    exit 7
  fi
  dire "$(stat -c '%n  %U:%G  %A' "$TTY")"
  if [ ! -w "$TTY" ]; then
    crier "$TTY n'est PAS écrivable par $(id -un) — le flash échouerait."
    exit 8
  fi
  echo
  echo "  ✅ La carte est à WSL en $(chrono) s. Flasher :"
  echo "        cd $RACINE/firmware/hello-desknode && idf.py -p $TTY flash monitor"
  ;;
esac
