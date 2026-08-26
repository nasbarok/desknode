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
#  🔴 CE QUI PART A CHANGE LE 2026-08-26 — C'EST UN **CHANGEMENT DE DOCTRINE**
#     (dn4-17), ⛔ PAS UNE LIGNE DE PLUS DANS UNE LISTE.
#     L'AGENT PART MAINTENANT SUR LA TOUR. Il y est lance par un `.bat`
#     double-cliquable, **WSL pouvant etre ETEINT** — decision owner n.2 du
#     2026-08-25 : ⛔ plus aucun chemin `\\wsl.localhost`.
#
#  CE QUI PART                          POURQUOI
#    tools/dn_lhm_tour.ps1              pilote LibreHardwareMonitor (dn4-8/D13)
#    agent/dn_agent.py                  L'AGENT — il TOURNE sur la tour
#    tools/dn-agent.bat                 le geste owner : start/stop/etat
#    tools/dn_agent_tour.ps1            la logique du lanceur + tache au logon
#
#  CE QUI RESTE DANS LE DEPOT
#    le FIRMWARE                        rien de ce qui se flashe ne part
#    les instruments WSL                dn_console.py, wsl-attach.sh,
#                                       rendre-port.sh, dn_injecteur.py — ils
#                                       ne peuvent pas tourner cote Windows
#    ⛔ tools/stub_psutil/psutil.py      IL NE DOIT JAMAIS ATTERRIR ICI : pose a
#                                       cote de dn_agent.py il MASQUERAIT le
#                                       vrai psutil, et l'agent publierait des
#                                       chiffres de STUB sans que rien ne le
#                                       dise. C'est pour ca que la liste est
#                                       EXPLICITE, jamais un `cp -r`.
# =============================================================================
set -uo pipefail

CIBLE_DEFAUT="/mnt/h/dev/projets/desknode"
RACINE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Ce qui part sur la tour. ⛔ Liste EXPLICITE : pas de `cp -r tools/`, sinon un
# instrument WSL (dn_console.py, wsl-attach.sh) atterrirait sur la tour ou il ne
# peut pas tourner, et quelqu'un finirait par essayer.
A_DEPOSER=(
  "tools/dn_lhm_tour.ps1"
  "agent/dn_agent.py"
  "tools/dn-agent.bat"
  "tools/dn_agent_tour.ps1"
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
    # ⚠️ La borne suit l'en-tete : il s'est ALLONGE en dn4-17 (changement de
    #    doctrine). Une aide tronquee au milieu d'une phrase serait le meme
    #    defaut « deux verites » a plus petite echelle.
    -h|--help)  sed -n '2,48p' "${BASH_SOURCE[0]}"; exit 0 ;;
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

# 🔴 CONTROLE ASCII-PUR — 2e REVUE (2026-08-24). LA CONTRAINTE ETAIT ECRITE,
#    LOAD-BEARING, ET **RIEN NE LA JOUAIT**. PowerShell 5.1 lit un `.ps1` UTF-8
#    SANS BOM comme de l'ANSI : un tiret cadratin y devient un guillemet
#    typographique fermant, que PowerShell accepte comme DELIMITEUR DE CHAINE.
#    Trois de ces tirets dans des commentaires ont produit 8 erreurs de syntaxe
#    en cascade (MESURE le 2026-08-21). Le delta a documente la contrainte et
#    fourni la commande de verification — mais aucun fichier du depot ne
#    l'executait. Un octet > 127 SE DEPLOYAIT DONC VERT (« OK - aucun ecart ») et
#    n'echouait qu'au parse, sur la tour, APRES l'invite UAC.
# ⚠️ CE SCRIPT EST LE SEUL OUTIL QUI EXPEDIE CE FICHIER : le controle a un sens
#    ICI, ⛔ pas dans un commentaire que personne n'execute.
verifier_ascii() {
  f="$1"
  n="$(LC_ALL=C grep -c '[^ -~	]' "$f" 2>/dev/null || true)"
  [ -z "$n" ] && n=0
  if [ "$n" -ne 0 ]; then
    echo "  /!\\ $(basename "$f") CONTIENT $n LIGNE(S) NON-ASCII."
    echo "      ⛔ PowerShell 5.1 lira ce fichier en ANSI : le parse s'effondre."
    echo "      ⇒ Corriger EN ASCII PUR dans le depot, ⛔ pas sur la tour."
    LC_ALL=C grep -n '[^ -~	]' "$f" | head -5 | sed 's/^/         /'
    return 1
  fi
  return 0
}

# 🔴 EMPREINTE **NORMALISEE POUR LES LANCEURS cmd.exe** (dn4-17 / AC1.6).
#    Un `.bat` / `.cmd` est VERSIONNE EN LF (il est ecrit depuis WSL) et
#    DEPOSE EN CRLF (obligatoire : cmd.exe ne parse pas de facon fiable une
#    continuation `^` contre du LF, et une ligne de commande TRONQUEE sur un
#    lanceur qui se releve en UAC n'est pas cosmetique). Comparer les octets
#    bruts ferait donc crier `--verifier` a CHAQUE passage, sur un ecart
#    VOULU — et une alarme qui crie toujours ne crie plus.
# ⇒ Pour ces deux extensions, et ELLES SEULES, on compare fins de ligne
#   normalisees. C'est deja ce que fait le controle de `poser-permanence.cmd`
#   (`tr -d '\r'`) : la regle est ici, une seule fois, pour tout le monde.
empreinte() {  # $1 = chemin relatif (pour l'extension), $2 = fichier a lire
  case "$1" in
    *.bat|*.cmd) tr -d '\r' < "$2" | sha256sum | cut -c1-16 ;;
    *)           sha256sum "$2" | cut -c1-16 ;;
  esac
}

# 🔴 GATE CRLF — REPAREE LE 2026-08-26 (dn4-17 / AC2), ET FACTORISEE.
#    Elle etait ecrite EN DUR pour `poser-permanence.cmd`. Elle vaut pour
#    TOUT lanceur cmd.exe depose, `dn-agent.bat` compris.
verifier_crlf() {
  f="$1"
  # 🔴 `grep -c` SORT EN 1 QUAND LE COMPTE EST 0.
  #    Le repli `|| echo 0` s'executait donc EN PLUS du `0` deja imprime par
  #    la commande de comptage : la substitution rendait la chaine "0\n0",
  #    `[ "0\n0" -ne 6 ]` ERRAIT (« integer expression expected », statut 2 =
  #    FAUX), le `if` etait faux, AUCUN ecart n'etait compte et AUCUN message
  #    n'etait imprime. MESURE le 2026-08-26 : `poser-permanence.cmd` sur la
  #    tour etait **0/6 ligne(s) en CR** — tout en LF, exactement le cas que
  #    cette gate pretend exclure — et `--verifier` n'a jamais crie dessus.
  # ⚠️ `tot` portait LE MEME defaut : masque tant que le fichier est non vide,
  #    ACTIF sur un `.cmd` de 0 octet.
  # ⇒ LA FORME CORRECTE SEPARE L'AFFECTATION DU REPLI : le `||` porte sur la
  #   COMMANDE D'AFFECTATION, ⛔ pas sur le contenu de la substitution.
  tot=$(grep -c '' "$f" 2>/dev/null) || tot=0
  avec_cr=$(grep -c $'\r$' "$f" 2>/dev/null) || avec_cr=0
  if [ "$tot" -eq 0 ] || [ "$avec_cr" -ne "$tot" ]; then
    echo "  /!\\ $(basename "$f") : $avec_cr/$tot ligne(s) en CRLF."
    echo "      ⛔ Une conversion PARTIELLE suffit a tronquer une continuation ^"
    echo "         de cmd.exe. Redeployer, ⛔ ne pas corriger sur place."
    return 1
  fi
  return 0
}

ecarts=0
for rel in "${A_DEPOSER[@]}"; do
  src="$RACINE/$rel"
  dst="$CIBLE/$(basename "$rel")"
  if [ ! -f "$src" ]; then
    echo "  /!\\ ABSENT du depot : $rel"; ecarts=$((ecarts+1)); continue
  fi
  # 🔴 LE CONTROLE ASCII PORTE SUR LA SOURCE, ET IL BLOQUE LE DEPOT. Un `.ps1`
  #    non-ASCII ne doit PAS atteindre la tour : il y echouerait au parse, apres
  #    l'invite UAC, avec un message qui n'a aucun rapport avec la cause.
  # ⛔ ET ELLE NE S'APPLIQUE **PAS** A `dn_agent.py` — L'ECART EST VOULU
  #    (dn4-17 / AC1.3). La gate existe parce que PowerShell 5.1 lit un `.ps1`
  #    UTF-8 SANS BOM comme de l'ANSI. Python 3, lui, lit UTF-8 PAR DEFAUT, et
  #    `dn_agent.py` est UTF-8 assume (`# -*- coding: utf-8 -*-` en ligne 2),
  #    avec un corps massivement accentue.
  #    ⇒ L'etendre a tous les fichiers BLOQUERAIT le depot de l'agent ; la
  #      retirer laisserait passer un `.ps1` qui casse APRES l'invite UAC.
  #    Le declencheur reste donc l'extension `.ps1`, et c'est ECRIT ici pour
  #    qu'un lecteur n'ait pas a se demander si le `.py` a ete oublie.
  case "$rel" in
    *.ps1)
      if ! verifier_ascii "$src"; then
        ecarts=$((ecarts+1)); continue
      fi ;;
  esac
  hs="$(empreinte "$rel" "$src")"
  if [ "$VERIFIER" -eq 1 ]; then
    if [ ! -f "$dst" ]; then
      echo "  MANQUE sur la tour : $(basename "$rel")"; ecarts=$((ecarts+1))
    else
      hd="$(empreinte "$rel" "$dst")"
      if [ "$hs" = "$hd" ]; then echo "  identique : $(basename "$rel")  ($hs)"
      else echo "  /!\\ DIVERGE  : $(basename "$rel")  depot=$hs  tour=$hd"; ecarts=$((ecarts+1)); fi
      # La gate CRLF couvre TOUT lanceur cmd.exe depose (AC1.6), ⛔ pas le
      # seul `poser-permanence.cmd` : un `.bat` arrive en LF si la conversion
      # de depot a saute, et c'est le meme piege de troncature.
      case "$rel" in
        *.bat|*.cmd) verifier_crlf "$dst" || ecarts=$((ecarts+1)) ;;
      esac
    fi
    continue
  fi
  cp -f "$src" "$dst"
  # 🔴 CONVERSION CRLF AU DEPOT, pour la meme raison que
  #    `poser-permanence.cmd` : `cp -f` copie A L'OCTET, donc un `.bat`
  #    versionne depuis WSL ARRIVERAIT EN LF. ⚠️ `sed`, ⛔ pas `unix2dos` :
  #    cet outil n'est pas garanti present et un deploiement qui echoue faute
  #    d'un paquet optionnel serait une dependance cachee.
  case "$rel" in
    *.bat|*.cmd) sed -i 's/$/\r/' "$dst" ;;
  esac
  hd="$(empreinte "$rel" "$dst")"
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
  # 🔴 2e REVUE (2026-08-24) — LA BRANCHE TRAITAIT L'ECRITURE, ⛔ PAS LA
  #    SUPPRESSION. `PROVENANCE.txt` et `poser-permanence.cmd` de la passe
  #    PRECEDENTE restaient intacts sur la tour : le `.cmd` auto-elevateur
  #    continuait de pointer `%~dp0dn_lhm_tour.ps1` — sur la copie CORROMPUE — et
  #    un `--verifier` ulterieur imprimait « present : PROVENANCE.txt » et
  #    « identique : poser-permanence.cmd ». La these du correctif (« une
  #    provenance qui certifie une copie cassee est pire qu'aucune provenance :
  #    elle la fait passer pour bonne ») n'etait donc PAS tenue.
  # ⇒ ON RETIRE LES DEUX. Une tour sans provenance se voit ; une tour avec une
  #   provenance perimee, non.
  for perime in "$CIBLE/PROVENANCE.txt" "$CIBLE/poser-permanence.cmd"; do
    if [ -f "$perime" ]; then
      rm -f "$perime" && echo "     retire (perime) : $(basename "$perime")"
    fi
  done
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

CE QUE FAIT dn-agent.bat (dn4-17)
  Il lance l'agent DeskNode SUR CETTE MACHINE, contre COM3, WSL pouvant etre
  ETEINT : il n'y a plus aucun chemin \\\\wsl.localhost dans le geste owner.
  Double-clic = demarrage, et un second double-clic ne cree AUCUN doublon.
  ⛔ LA LISTE DES VERBES ET LEUR EFFET SONT ECRITS DANS LE .bat LUI-MEME.
     Ils ne sont pas recopies ici : le contenu du lanceur est une SOURCE
     UNIQUE, et deux textes recopies divergent sans que rien ne le dise.
  Journal : dn-agent.log — c'est le stderr de l'agent (bilan de fin, erreurs
  d'envoi, recalages, echo console, refus firmware). Il est AJOUTE, jamais
  tronque, et bascule en .1 au-dela de 5 Mo.
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
    # 🔴 2e REVUE (2026-08-24) — `grep -q $'\r'` teste qu'AU MOINS UN `\r`
    #    existe. Un `.cmd` PARTIELLEMENT converti (une seule ligne en CRLF, la
    #    ligne de continuation `^` en LF) passait le test **et** l'empreinte
    #    (`tr -d '\r'` normalise tout) : c'est precisement la troncature que ce
    #    controle pretend exclure, sur un lanceur qui se releve en UAC.
    # ⇒ ON COMPTE. La gate vit maintenant dans `verifier_crlf()` : elle a ete
    #   REPAREE en dn4-17 (elle ne tirait jamais) et elle sert AUSSI aux
    #   lanceurs de `A_DEPOSER`. Le motif est ecrit une seule fois.
    verifier_crlf "$cmd_dst" || ecarts=$((ecarts+1))
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
    # =====================================================================
    # 🔴 ET ON LIT LE SHA QU'IL PORTE.                      (dn4-17 / AC1.5)
    #    MESURE LE 2026-08-26 : `PROVENANCE.txt` disait `55469ee` quand HEAD
    #    disait `b532574` — **128 commits** d'ecart — et `--verifier` n'a crie
    #    QUE PAR ACCIDENT : parce que `dn_lhm_tour.ps1` avait change entre
    #    temps. 🔴 Sur des fichiers IDENTIQUES il aurait imprime
    #    « OK — aucun ecart » sur une copie vieille de 128 commits.
    # ⚠️ ⛔ CE N'EST PAS UNE COMPARAISON D'OCTETS : ce fichier est HORODATE, le
    #    pretendre comparable serait un faux controle. On lit UN CHAMP.
    # =====================================================================
    sha_prov="$(sed -n 's/^[[:space:]]*HEAD[[:space:]]*:[[:space:]]*\([0-9a-fA-F]\{7,40\}\).*/\1/p' \
                  "$CIBLE/PROVENANCE.txt" | head -1)"
    if [ -z "$sha_prov" ]; then
      # 🔴 PIEGE MESURE LE 2026-08-26, ⛔ PAS SUPPOSE : avec un SHA vide,
      #    `git rev-list --count ""..HEAD` rend **0** — c'est-a-dire « a
      #    jour ». Un parseur muet publierait donc un FAUX « pas de retard ».
      echo "  /!\\ PROVENANCE.txt : aucun SHA lisible dans le champ 'HEAD :'."
      echo "      ⛔ Le retard NE PEUT PAS etre calcule — ce n'est PAS 'a jour'."
      ecarts=$((ecarts+1))
    elif ! git -C "$RACINE" cat-file -e "${sha_prov}^{commit}" 2>/dev/null; then
      echo "  /!\\ PROVENANCE.txt annonce $sha_prov, INCONNU de ce depot."
      echo "      (historique reecrit, ou copie venue d'ailleurs)"
      ecarts=$((ecarts+1))
    elif [ "$(git -C "$RACINE" rev-parse "$sha_prov")" = "$(git -C "$RACINE" rev-parse HEAD)" ]; then
      echo "  a jour    : PROVENANCE.txt = HEAD ($sha_prov)"
    else
      # `...` (trois points) : on dit les DEUX sens. Une copie deposee depuis
      # une branche que HEAD n'a pas est un ecart, pas un retard.
      lr="$(git -C "$RACINE" rev-list --left-right --count "${sha_prov}...HEAD" 2>/dev/null)"
      derriere="$(echo "$lr" | cut -f2)"
      devant="$(echo "$lr" | cut -f1)"
      echo "  /!\\ LA COPIE EST EN RETARD : PROVENANCE.txt dit $sha_prov, HEAD dit $SHA"
      echo "      $derriere commit(s) DERRIERE HEAD, $devant commit(s) que HEAD n'a pas."
      echo "      ⛔ Des fichiers identiques ne prouvent RIEN : ce qui manque, c'est"
      echo "         ce qui n'a jamais ete depose. Redeployer."
      ecarts=$((ecarts+1))
    fi
  fi
fi

echo
if [ "$ecarts" -eq 0 ]; then
  echo "  OK — aucun ecart."
else
  echo "  /!\\ $ecarts ecart(s)."
fi
exit "$ecarts"
