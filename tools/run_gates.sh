#!/usr/bin/env bash
# ═════════════════════════════════════════════════════════════════════════════
# tools/run_gates.sh — dn4-24 / AC1
#
#   UNE COMMANDE PASSE TOUTES LES GATES, ET AUCUNE N'EST SAUTEE EN SILENCE.
#
#   Usage :  bash tools/run_gates.sh [--silencieux] [--cockpit <chemin>] [-h|--help]
#   Sortie :  0  toutes VERTES, ou NON-JOUABLES declarees ET conformes
#             1  au moins une ROUGE, ou la table des NON-JOUABLES est perimee,
#                malformee, ou dementie par le comportement de la gate
#
# ── LES QUATRE REGLES QUI FONT CE SCRIPT ────────────────────────────────────
#
# (1) LES GATES SONT DECOUVERTES PAR GLOB, ⛔ JAMAIS ENUMEREES.
#     Motif paye : le depot portait 21 gates pendant qu'un dossier en comptait
#     20, et personne ne l'a vu. Une liste ecrite se perime le jour ou on
#     ajoute une gate — c'est-a-dire le jour ou elle compte le plus.
#
# (2) UNE GATE NON-JOUABLE EST **DECLAREE ICI, AVEC SON MOTIF**,
#     ⛔ JAMAIS INFEREE D'UN CODE DE RETOUR.
#     Si « rc != 0 et != 1 ⇒ non-jouable » etait la regle, une gate qui plante
#     sur une vraie faute (traceback ⇒ rc=1, timeout ⇒ rc=124, segfault ⇒
#     rc=139) deviendrait « non-jouable » en silence. Ici, tout rc non nul
#     d'une gate NON DECLAREE est ROUGE.
#
# (3) LA DECLARATION EST ELLE-MEME FALSIFIABLE, **DANS LES DEUX SENS**.
#     Chaque NON-JOUABLE porte un TEMOIN (le chemin dont la PRESENCE la rendrait
#     jouable) ET un RC ATTENDU. Si le temoin apparait, le script JOUE la gate
#     avec ses arguments. Sinon il la joue QUAND MEME, sans argument, et EXIGE
#     le rc declare : c'est ainsi qu'on verifie qu'elle est encore une gate.
#     ⚠️ Une declaration qui ne correspond plus a aucune gate du glob, qui est
#        MALFORMEE, ou dont le rc attendu est DEMENTI, fait SORTIR EN 1.
#
#     🔴 REVUE DE CODE DU 2026-08-31 — CE QUI A ETE MESURE ICI :
#        · une declaration a champs VIDES (`"g.py|||"`) sautait une gate ROUGE
#          en silence et pour toujours : `[ ! -e "" ]` est TOUJOURS vrai, et les
#          regles (2)/(3) ci-dessus etaient de la PROSE, pas des controles ;
#        · `verif_sr03.py` remplacee par `print(...); sys.exit(0)` produisait
#          une sortie IDENTIQUE : une gate declaree n'etait jamais jouee, donc
#          jamais confrontee a ce que sa declaration AFFIRME d'elle.
#        ⇒ les champs sont valides au demarrage, et la gate est JOUEE.
#
# (4) ⛔ AUCUNE SORTIE N'EST REDIRIGEE VERS LE PUITS.
#     La sortie de chaque gate est CAPTUREE et n'est imprimee QUE SUR ECHEC.
#     Une sortie jetee fait disparaitre le motif du rouge, et on se retrouve
#     avec un « ca casse » sans piece. Le controle `garde_puits` ci-dessous
#     relit CE FICHIER et refuse de tourner s'il y trouve une REDIRECTION.
#
#     🔴 REVUE DE CODE DU 2026-08-31 — LA GARDE AVAIT TROIS DEFAUTS, DONT UN
#        QUI LA RENDAIT INCAPABLE D'ECHOUER :
#        · elle relisait `${BASH_SOURCE[0]}` APRES le `cd` a la racine. Invoquee
#          depuis `tools/`, le chemin relatif ne resolvait plus, `grep` echouait,
#          et `|| true` + `${n:-0}` transformaient l'ECHEC DE LECTURE en
#          « 0 redirection ». Mesure : une vraie pollution `> /dev/null` plantee
#          dans le script passait VERTE selon le repertoire d'appel ;
#        · elle rougissait sur une simple MENTION de la chaine, ce qui rendait
#          impossible de documenter sa propre regle ;
#        · ⚠️ ELLE RESTE CONTOURNABLE par une variable — `P="/dev/""null"` puis
#          `> "$P"` — et ce n'est PAS refermable par une lecture statique. C'est
#          ecrit ici plutot que tu : cette garde attrape l'ETOURDERIE, ⛔ pas
#          quelqu'un qui veut la contourner.
#        ⇒ le chemin du source est resolu en ABSOLU AVANT le `cd`, l'echec de
#          lecture est FATAL, et seule une vraie REDIRECTION est epinglee.
#
# (5) 🔴 UN `rc` DEDIE DIT « PREREQUIS ABSENT », ⛔ IL NE SE DEDUIT PAS.
#     Ajoute par `dn4-39` le 2026-09-02, et voici ce qui l'a rendu necessaire.
#
#     MESURE — `bash tools/run_gates.sh` dans un CLONE NEUF avec un `HOME`
#     ETRANGER (la seule configuration qui reproduit un runner) rend
#     **21 VERTE / 5 ROUGE / 1 NON-JOUABLE**, contre **25/1/1** sur le poste de
#     l'auteur. Les rouges se rangent en trois causes, et AUCUNE ne parle du
#     code : (A) le cockpit de planification n'est pas clone · (B)
#     `managed_components/` est gitignore · (C) une gate lit deux chemins
#     ABSOLUS de la machine de l'auteur — celle-la est VERTE dans le clone et
#     ROUGE sur un runner, elle se LIT dans le code.
#
#     🔴 LE PROBLEME : ces gates rendaient toutes **rc=1** sans leur prerequis,
#     c'est-a-dire LA MEME VALEUR QUE LEUR ROUGE. Declarer `rc attendu = 1`
#     aurait produit une declaration satisfaite AUSSI BIEN par « le terrain
#     manque » que par « j'ai trouve un defaut » ⇒ la regle (3) tombait A VIDE.
#     Le mecanisme de la seule NON-JOUABLE d'alors ne marchait que par chance :
#     `verif_sr03.py` sort en **2** sur son message d'usage, distinguable de 1.
#
#     ⇒ LES GATES CONCERNEES RENDENT DESORMAIS **rc=4**, AVEC LEUR MOTIF.
#       0 = vert · 1 = un VRAI defaut trouve · 2 = message d'usage
#       (`verif_sr03.py`, publie dans le README) · 3 = MUTANT PERIME
#       (`verif_paliers_dn441.py`, l. 127 — deja pris, LU dans le code, ⛔ pas
#       suppose) · **4 = PREREQUIS ABSENT**. ⛔ pas 124 (le `timeout` ci-dessous),
#       ⛔ pas >= 126 ni 128+N (conventions du shell et signaux).
#
#     🔴 ET L'ORDRE EST UNE REGLE : **un VRAI defaut l'emporte sur un prerequis
#     absent**. Une gate qui trouve un KO rend 1 MEME si un prerequis manque.
#     Sans ca, un prerequis absent masquerait un rouge — et « rc attendu = 4 »
#     redeviendrait satisfiable par un defaut.
#
#     ⚠️ LE CHAMP « arguments » ACCEPTE LE JETON LITTERAL `AUCUN`, et c'est
#     necessaire : 4 des 6 gates declarees ne prennent AUCUN argument, et un
#     champ VIDE est interdit depuis la revue du 2026-08-31 (il sautait une gate
#     rouge en silence). `AUCUN` est un CHOIX ECRIT, ⛔ pas un trou.
# ═════════════════════════════════════════════════════════════════════════════
set -uo pipefail

# ── (4) LE SOURCE EST RESOLU EN ABSOLU **AVANT** TOUT `cd` ──────────────────
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"
MOI="$(basename "$SRC")"

RACINE="$(cd "$(dirname "$SRC")/.." && pwd)"
cd "$RACINE" || exit 1

SILENCIEUX=0
COCKPIT=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --silencieux) SILENCIEUX=1 ;;
    --cockpit)
      shift
      [ "$#" -gt 0 ] || { echo "--cockpit attend un chemin" >&2; exit 2; }
      # 🔴 REVUE 2026-09-02 — UN CHEMIN FAUX ETAIT ACCEPTE PUIS JETE EN SILENCE.
      #    Temoin absent ⇒ `declaree` restait a 1 ⇒ `--cockpit` n'etait JAMAIS
      #    transmis ⇒ la gate retombait sur son COCKPIT_DEFAUT et mesurait un
      #    depot que personne n'avait demande. Une coquille d'une lettre rendait
      #    deux « DECLARATION DEMENTIE » et rc 1, sans un mot sur le chemin.
      #    ⛔ Une chaine VIDE aussi : `${COCKPIT:-…}` la traite comme « absent ».
      if [ -z "$1" ] || [ ! -d "$1" ]; then
        echo "--cockpit : chemin inexistant ou vide — '$1'" >&2
        echo "  ⛔ Un chemin faux serait JETE en silence et la gate mesurerait" >&2
        echo "     un AUTRE depot. On echoue FERME plutot que de mesurer a cote." >&2
        exit 2
      fi
      COCKPIT="$1"
      ;;
    # ⚠️ dn4-39 — L'AIDE S'ANCRE PAR **CONTENU**, ⛔ PLUS PAR NUMERO DE LIGNE.
    #    `sed -n '2,60p'` tronquait deja la fin de la regle (4), et toute ligne
    #    ajoutee a l'en-tete aggravait la coupe EN SILENCE. On imprime de la
    #    premiere barre a la barre de fermeture — c'est le meme defaut de classe
    #    que le §9 du cockpit, ancre par numero, que cette story solde par
    #    ailleurs.
    # 🔴 REVUE 2026-09-02 — L'ANCRE PRENAIT LA **PREMIERE** BARRE VENUE.
    #    Ajouter une section a l'en-tete retronquait l'aide EN SILENCE ; en
    #    retirer la barre de fermeture imprimait TOUT LE SCRIPT comme aide.
    #    ⇒ on borne a la DERNIERE barre de l'en-tete, et on VERIFIE qu'on l'a.
    -h|--help)
      fin=$(awk 'NR>1 && /^# ═══/ { l = NR } /^[^#]/ && NR > 1 { exit } END { print l+0 }' "$SRC")
      if [ "${fin:-0}" -lt 2 ]; then
        echo "aide indisponible : barre de fermeture introuvable dans $SRC" >&2; exit 2
      fi
      sed -n "2,${fin}p" "$SRC" || { echo "aide indisponible : $SRC illisible" >&2; exit 2; }
      echo
      echo "⚠️ La TABLE des NON-JOUABLES ne vit PAS dans cet en-tete : elle est"
      echo "   dans le corps du script, sous 'NON_JOUABLES=('. Pour la lire :"
      echo "   sed -n '/^NON_JOUABLES=(/,/^)/p' $SRC"
      exit 0 ;;
    *) echo "argument inconnu : $1" >&2; exit 2 ;;
  esac
  shift
done

# ── (4) GARDE : ce script ne doit contenir AUCUNE REDIRECTION vers le puits ──
# ⛔ On epingle une REDIRECTION (`> /dev/null`, `2>/dev/null`, `&>/dev/null`),
#    ⛔ pas une mention : la regle doit pouvoir s'ecrire dans son propre fichier.
# L'aiguille est CONCATENEE pour que le motif ne se declenche pas sur lui-meme.
garde_puits() {
  local cible="/dev/""null"
  local motif="[0-9]*[>&]>?[[:space:]]*${cible}"
  local n rc
  # ⚠️ LES LIGNES DE COMMENTAIRE SONT EXCLUES, et ce n'est pas une complaisance :
  #    sans ca, ce fichier ne peut pas DOCUMENTER sa propre regle — la revue du
  #    2026-08-31 a vu la garde rougir sur les trois exemples ecrits dans son
  #    en-tete. Une redirection en commentaire n'est pas une redirection.
  #    ⛔ Un commentaire de FIN DE LIGNE sur une ligne de code reste scanne :
  #    la garde echoue FERME.
  # ⚠️ `awk` sort en 2 sur un fichier illisible — un controle qui ne peut pas
  #    lire ne dit PAS « rien a signaler ». Le rc est capture EXPLICITEMENT.
  n=$(awk -v m="$motif" '!/^[[:space:]]*#/ && $0 ~ m { c++ } END { print c+0 }' "$SRC"); rc=$?
  if [ "$rc" -ge 2 ] || [ ! -r "$SRC" ]; then
    echo "[KO ] $MOI : source ILLISIBLE ($SRC) — la garde du puits ne peut pas s'exercer." >&2
    echo "      ⛔ Un controle qui ne peut pas lire ne dit PAS « rien a signaler »." >&2
    return 1
  fi
  if [ "${n:-0}" -ne 0 ]; then
    echo "[KO ] $MOI contient $n redirection(s) vers le puits — AC1.4 l'interdit." >&2
    echo "      Une sortie jetee, c'est un rouge sans motif. CAPTURER, imprimer sur echec." >&2
    return 1
  fi
  return 0
}

garde_puits || exit 1

# ── (4bis) GARDE : LA TABLE DES NON-JOUABLES NE SUBSTITUE RIEN ──────────────
#
# 🔴 DEFAUT MESURE LE 2026-09-02, SUR LE PREMIER RUN REEL DE LA CI (`dn4-39`).
#    Les elements du tableau sont entre GUILLEMETS DOUBLES — donc un accent
#    grave y est une SUBSTITUTION DE COMMANDE, ⛔ pas de la typographie. Les six
#    motifs ecrits ce jour-la en contenaient : le runner a REELLEMENT lance
#    `idf.py reconfigure`, `HOME`, `dn_ok`, `dn5-3` et `rc` — visible dans le
#    journal du run 33640427810 :
#        tools/run_gates.sh: line 172: idf.py: command not found
#    ⇒ ET LE TEXTE ETAIT VIDE A LEUR PLACE. Cinq motifs sur six ont ete publies
#      MUTILES, en silence : « elle RELIT  dans  (c'est ce qui garantit que
#      vaut le trou de LVGL) ». Un motif qui perd ses noms ne dit plus rien —
#      c'est exactement le « rouge sans son motif » que la regle (4) interdit.
#
# ⛔ CE N'EST PAS UN DETAIL DE TYPOGRAPHIE : c'est de l'EXECUTION. Quiconque
#    ecrira une entree future avec des accents graves — le reflexe naturel, tout
#    ce depot cite en accents graves — fera tourner du code sans le savoir.
# ⇒ La garde epingle l'accent grave ET `$(` DANS LE BLOC DE LA TABLE, et refuse
#   de demarrer. ⚠️ `${...}` reste permis : c'est ainsi que les temoins passent
#   par HOME plutot que par un chemin absolu.
# ⚠️ Comme `garde_puits`, elle echoue FERME sur un source illisible, et elle
#    exclut les lignes de COMMENTAIRE — sans quoi ce paragraphe la ferait rougir.
garde_table() {
  local n rc
  # 🔴 REVUE DE CODE DU 2026-09-02 — CETTE GARDE AVAIT DEUX TROUS, ET LE PREMIER
  #    LUI OTAIT SA RAISON D'ETRE :
  #
  #    (a) ELLE TOURNAIT **APRES** L'AFFECTATION DE LA TABLE. Bash developpe les
  #        guillemets doubles AU MOMENT DE L'AFFECTATION ; la garde, elle, relit
  #        le FICHIER. Mesure : une entree portant `touch /tmp/PREUVE` faisait
  #        imprimer « refuse de demarrer », rc 1 — ET /tmp/PREUVE EXISTAIT DEJA.
  #        L'en-tete promettait un refus AVANT. Elle ne bloquait que la 2e fois.
  #        ⇒ LES DEUX GARDES SONT DESORMAIS APPELEES AVANT TOUTE AFFECTATION DE
  #          LA TABLE. Leur position dans ce fichier EST le correctif : ⛔ ne pas
  #          les redescendre sous `NON_JOUABLES=(`.
  #
  #    (b) `gsub(/\$\{[^}]*\}/, "", ligne)` effacait les accolades ET LEUR
  #        CONTENU ⇒ `${VAR:-$(cmd)}` disparaissait EN ENTIER, substitution
  #        comprise. Mesure : sur 2 lignes portant une substitution, elle en
  #        epinglait 1 — et la commande imbriquee TOURNAIT
  #        (`${DN_ABSENT:-$(touch …)}` ⇒ champ = « motif SUBSTITUE suite »).
  #        ⇒ seul un `${…}` DONT LE CONTENU EST SUR est retire : un nom de
  #          variable, eventuellement suivi d'un defaut qui ne porte lui-meme ni
  #          accent grave ni `$(`.
  #
  #    ⚠️ ET UN FAUX POSITIF, CORRIGE LUI AUSSI : une entree en QUOTES SIMPLES ne
  #       peut RIEN substituer, et la garde la refusait quand meme — elle poussait
  #       donc a RETIRER les noms des motifs, la degradation qu'elle previent.
  #       Une ligne dont le premier caractere non blanc est `'` est SURE.
  n=$(awk '
        /^NON_JOUABLES=\(/ { dedans = 1; next }
        dedans && /^\)/     { dedans = 0 }
        dedans && $0 !~ /^[[:space:]]*#/ {
          ligne = $0
          if (ligne ~ /^[[:space:]]*'"'"'/) next        # quotes simples : rien ne substitue
          # on ne retire QUE les ${...} surs : ${NOM} ou ${NOM:-defaut} sans
          # accent grave ni $( dans le defaut. Tout le reste RESTE visible.
          while (match(ligne, /\$\{[A-Za-z_][A-Za-z0-9_]*(:[-=?+][^}`]*)?\}/)) {
            morceau = substr(ligne, RSTART, RLENGTH)
            if (index(morceau, "$(") > 0) break        # defaut piege : on ne retire pas
            ligne = substr(ligne, 1, RSTART - 1) substr(ligne, RSTART + RLENGTH)
          }
          if (ligne ~ /`/ || ligne ~ /\$\(/) c++
        }
        END { print c+0 }
      ' "$SRC"); rc=$?
  if [ "$rc" -ge 2 ] || [ ! -r "$SRC" ]; then
    echo "[KO ] $MOI : source ILLISIBLE ($SRC) — la garde de la table ne peut pas s'exercer." >&2
    return 1
  fi
  if [ "${n:-0}" -ne 0 ]; then
    echo "[KO ] $MOI : $n ligne(s) de la table NON_JOUABLES portent une SUBSTITUTION." >&2
    echo "      Un accent grave ou un \$( dans un champ EXECUTE une commande et VIDE" >&2
    echo "      le texte a sa place — mesure le 2026-09-02, run 33640427810." >&2
    echo "      ⇒ ecrire les noms EN CLAIR. Seul \${VAR} est permis." >&2
    return 1
  fi
  return 0
}

garde_table || exit 1

# ── (4ter) GARDE : AUCUN ACCENT GRAVE DANS DU CODE, OU QUE CE SOIT ──────────
#
# 🔴 TROUVE PENDANT LA REVUE DU 2026-09-02, EN ECRIVANT LE CORRECTIF LUI-MEME.
#    `garde_table` ne scanne QUE le bloc `NON_JOUABLES=(...)`. En redigeant le
#    message de KO du jeton AUCUN, un accent grave a ete ecrit dans un `echo` en
#    guillemets doubles — DEHORS du bloc, donc invisible a la garde. C'est
#    l'angle mort que la revue avait nomme (« un futur TEMOIN_X=$(cmd) pose hors
#    du bloc scanne »), et il s'est materialise dans le meme geste.
#
# ⇒ REGLE : ce depot n'utilise JAMAIS l'accent grave comme substitution. Toute
#   substitution s'ecrit `$( )`. Un accent grave sur une ligne de CODE est donc
#   toujours une erreur — soit de la typographie qui va s'EXECUTER, soit une
#   substitution ecrite a l'ancienne.
# ⚠️ Les programmes `awk` sont en QUOTES SIMPLES : rien n'y substitue, et ils
#    ont besoin de l'accent grave comme motif. Ils sont donc sautes, et la borne
#    est le delimiteur du here-string, ⛔ pas une liste de numeros de ligne.
# ⚠️ Les COMMENTAIRES sont sautes, comme pour les deux autres gardes : sans ca,
#    ce paragraphe ferait rougir sa propre garde.
garde_accent_grave() {
  local n rc
  n=$(awk '
        /^[[:space:]]*#/            { next }          # commentaire
        /awk[[:space:]]*.$/          { dans_awk = 1; next }
        dans_awk && /^[[:space:]]*.[[:space:]]*"\$SRC"\)/ { dans_awk = 0; next }
        dans_awk                    { next }          # programme awk, quotes simples
        /`/                         { c++; print "      l." NR " : " $0 > "/dev/stderr" }
        END { print c+0 }
      ' "$SRC"); rc=$?
  if [ "$rc" -ge 2 ] || [ ! -r "$SRC" ]; then
    echo "[KO ] $MOI : source ILLISIBLE ($SRC) — la garde de l'accent grave ne peut pas s'exercer." >&2
    return 1
  fi
  if [ "${n:-0}" -ne 0 ]; then
    echo "[KO ] $MOI : $n ligne(s) de CODE portent un accent grave." >&2
    echo "      Un accent grave en guillemets doubles EXECUTE une commande." >&2
    echo "      ⇒ ecrire le nom EN CLAIR, ou passer par \$( ) si c'est voulu." >&2
    return 1
  fi
  return 0
}

garde_accent_grave || exit 1

# ── (2)(3) TABLE DES NON-JOUABLES ───────────────────────────────────────────
# format :  <gate> | <motif> | <chemin temoin> | <arguments si le temoin est la> | <rc attendu sans temoin>
# Le TEMOIN est le chemin dont la presence rendrait la gate jouable. Tant qu'il
# n'existe pas, la gate est jouee SANS ARGUMENT et doit rendre <rc attendu> —
# son message d'usage. Des qu'il existe, elle est jouee AVEC ses arguments, et
# son rouge eventuel compte comme un rouge.
#
# ── LES TEMOINS, ET POURQUOI ILS SONT ECRITS AINSI (dn4-39) ────────────────
#
# ⛔ AUCUN CHEMIN ABSOLU ICI. Ecrire `/home/<quelqu-un>/…` dans ce runner
#    fabriquerait exactement le defaut que `dn5-3` doit solder — un outil qui ne
#    marche que sur une machine. Les temoins de cockpit passent donc par `HOME`.
#
# ⚠️ `TEMOIN_COCKPIT` SUIT `--cockpit` quand il est donne : sans ca, deplacer le
#    cockpit et le passer en argument aurait fait declarer NON-JOUABLES deux
#    gates parfaitement jouables — un skip silencieux par la porte de derriere.
TEMOIN_COCKPIT="${COCKPIT:-${HOME:-/nonexistent}/projects/compagnon_project}"
#
# ⚠️ `TEMOIN_COCKPIT_ABS` NE SUIT PAS `--cockpit`, ET C'EST DELIBERE :
#    `verif_dossier_d5_dn45.py` n'a PAS d'option `--cockpit`, elle lit deux
#    chemins ABSOLUS ecrits en dur (l. 47-48). Lui donner le temoin de
#    `--cockpit` la ferait declarer jouable alors qu'elle ne lirait pas ce
#    dossier-la. ⛔ LIMITE ECRITE : sur une machine TIERCE ou `~/projects/
#    compagnon_project` existerait, le temoin serait present et la gate serait
#    JOUEE — elle rougirait alors sur ses chemins absolus. C'est le sens
#    CONSERVATEUR (echouer fort), ⛔ pas un skip. `dn5-3` ferme ce coin.
TEMOIN_COCKPIT_ABS="${HOME:-/nonexistent}/projects/compagnon_project"
#
# `managed_components/` est GITIGNORE (186 Mo) et repeuple par
# `idf.py reconfigure`. Le temoin est RELATIF : il vit dans le clone.
# 🔴 REVUE 2026-09-02 — LA BORNE PAR GATE DOIT TENIR **SOUS** CELLE DU JOB.
#    `gates.yml` accorde `timeout-minutes: 20` au job ; l'ancien `timeout 1800`
#    (30 min) etait donc INATTEIGNABLE en CI : GitHub tuait le job avant, et on
#    perdait le BILAN, la liste des ROUGES et la sortie capturee que la regle (4)
#    exige d'imprimer — le run devenant `cancelled`, ⛔ pas `failure`.
#    Mesure du poste : 63 s pour les 27 gates. 600 s laisse un facteur ~9.
TIMEOUT_GATE="${DN_TIMEOUT_GATE:-600}"

# 🔴 REVUE 2026-09-02 — UN TEMOIN PLUS GROSSIER QUE LE PREREQUIS FABRIQUE UN
#    ROUGE. `[ -e "$temoin" ]` sur le REPERTOIRE est vrai des qu'il existe —
#    vide, partiel, ou meme si c'est un fichier. La gate etait alors « jouee »,
#    rendait 4 (prerequis absent) et le runner l'imprimait `[ROUGE] rc=4` : la
#    valeur qui, partout ailleurs, veut dire « pas un rouge ».
#    ⇒ CHAQUE TEMOIN EST LE FICHIER QUE SA GATE LIT VRAIMENT. Un arbre LVGL
#      partiel (reconfigure interrompu, arborescence LVGL changee entre v8 et
#      v9) declare donc la gate NON-JOUABLE au lieu de la faire rougir.
TEMOIN_LVGL_VEILLE="firmware/desknode/managed_components/lvgl__lvgl/scripts/built_in_font/built_in_font_gen.py"
TEMOIN_LVGL_HIST="firmware/desknode/managed_components/lvgl__lvgl/src/widgets/chart/lv_chart.h"
TEMOIN_LVGL="firmware/desknode/managed_components/lvgl__lvgl"

NON_JOUABLES=(
  "verif_sr03.py|le PDF [AN] AN4545 (VL6180X, DocID026571 Rev 1) n'est PAS au depot : document StMicroelectronics, ⛔ non redistribuable. La gate l'attend en argument et sort en 2 sur son message d'usage — rc=2 n'est PAS un rouge.|tools/fixtures/AN4545.pdf|tools/fixtures/AN4545.pdf firmware/desknode/main/dn_console.c|2"
  "verif_dossier_dn415.py|CAUSE A — le cockpit de planification est un depot PRIVE, ⛔ jamais clone a cote du code. Sans lui la gate n'a AUCUNE occurrence a arbitrer. ⚠️ La ou le cockpit EST la elle rend 17 OK / 10 KO sur le CONTENU : ⛔ une CI ne verra JAMAIS ces 10 KO, et elle ne pretend pas les garder.|${TEMOIN_COCKPIT}|AUCUN|4"
  "verif_ledger_dn416.py|CAUSE A — le cockpit de planification est un depot PRIVE, ⛔ jamais clone. Sans lui il n'y a ni ledger ni tracker a confronter. ⚠️ le controle dn_ok (« le depot code EST desknode ») reste un CONTROLE : son echec reste un ROUGE, ⛔ pas un prerequis.|${TEMOIN_COCKPIT}|AUCUN|4"
  "verif_dossier_d5_dn45.py|CAUSE C — elle lit DEUX chemins ABSOLUS de la machine de l'auteur (l. 47-48) ⇒ ⛔ la variable HOME n'y peut rien : VERTE dans un clone neuf, et 1 OK / 7 KO sur un runner. Le seul des six rouges qu'aucune mesure prise depuis ce poste ne pouvait montrer — il se LIT dans le code. La reparation des chemins est portee par dn5-3, ⛔ pas ici.|${TEMOIN_COCKPIT_ABS}|AUCUN|4"
  "verif_veille_dn33.py|CAUSE B — managed_components/ est GITIGNORE (186 Mo, repeuple par: idf.py reconfigure) et porte le generateur AMONT de LVGL. ⛔ 2 blocs sur 18 ne sont pas exerces ; TOUT LE RESTE EST JOUE. Elle disait deja le bon motif et le remede — il lui manquait le rc.|${TEMOIN_LVGL_VEILLE}|AUCUN|4"
  "verif_harnais_dn413.py|CAUSE B — sans l'arbre LVGL le corpus C est INCOMPLET, et la chasse aux renvois FANTOMES accusait tools/dn_police.py de citer des fonctions QUI EXISTENT (lv_text_get_width est defini dans lvgl__lvgl/src/misc/lv_text.c). ⛔ Un diagnostic FAUX publie automatiquement. Elle DECLARE desormais, elle n'accuse plus — et ⛔ elle ne devient PAS aveugle la ou l'arbre est la.|${TEMOIN_LVGL}|AUCUN|4"
  "verif_hist_dn413.py|CAUSE B — elle RELIT LV_CHART_POINT_NONE dans lv_chart.h (c'est ce qui garantit que DN_HIST_TROU vaut le trou de LVGL) et PLANTAIT en FileNotFoundError NU : un rouge sans motif ni remede. Elle echoue FERME desormais, sur le modele de verif_veille_dn33.py.|${TEMOIN_LVGL_HIST}|AUCUN|4"
)

# ── (1) DECOUVERTE PAR GLOB ─────────────────────────────────────────────────
shopt -s nullglob
GATES=(tools/verif_*.py)
shopt -u nullglob

if [ "${#GATES[@]}" -eq 0 ]; then
  echo "[KO ] aucune gate trouvee par le glob tools/verif_*.py — le depot est-il complet ?" >&2
  exit 1
fi

# ── (3) LA TABLE DES NON-JOUABLES EST VALIDEE AVANT D'ETRE CRUE ─────────────
declare -A EXISTE=()
declare -A DECLAREE=()
for g in "${GATES[@]}"; do EXISTE["$(basename "$g")"]=1; done

PERIMEES=0
for d in "${NON_JOUABLES[@]}"; do
  # 5 champs EXACTEMENT, tous non vides. Un `|` dans un motif casse le
  # decoupage : mieux vaut le dire que produire un temoin qui vaut du texte.
  nchamps=$(awk -F'|' '{print NF}' <<<"$d")
  if [ "$nchamps" -ne 5 ]; then
    echo "[KO ] declaration NON-JOUABLE MALFORMEE ($nchamps champs au lieu de 5) : $d" >&2
    echo "      ⛔ Un '|' dans le motif casse le decoupage et fabrique un faux temoin." >&2
    PERIMEES=$((PERIMEES + 1)); continue
  fi
  IFS='|' read -r c_nom c_motif c_temoin c_args c_rc <<<"$d"
  vide=""
  [ -n "$c_nom" ]    || vide="$vide nom"
  [ -n "$c_motif" ]  || vide="$vide motif"
  [ -n "$c_temoin" ] || vide="$vide temoin"
  [ -n "$c_args" ]   || vide="$vide arguments"
  [ -n "$c_rc" ]     || vide="$vide rc_attendu"
  if [ -n "$vide" ]; then
    echo "[KO ] declaration NON-JOUABLE a CHAMP(S) VIDE(S) :$vide — '$c_nom'" >&2
    echo "      ⛔ Un champ vide sauterait la gate en silence, et pour toujours." >&2
    PERIMEES=$((PERIMEES + 1)); continue
  fi
  # 🔴 REVUE 2026-09-02 — AC39.4.c EXIGEAIT DE DECLARER TOUT JETON INTRODUIT,
  #    ET `AUCUN` EN EST UN : il n'a AUCUN ECHAPPEMENT. Une gate dont le champ
  #    « arguments » vaudrait litteralement `AUCUN` serait jouee SANS argument,
  #    en silence — le motif que ce depot a deja paye (« le jeton d'exemption
  #    d'une gate n'a aucun echappement : le citer l'accorde »).
  #    ⛔ On ne peut pas l'echapper sans casser les 4 declarations qui s'en
  #      servent. ⇒ ON LE DECLARE, et on REFUSE la seule collision possible :
  #      un champ qui commence par `AUCUN` sans etre EXACTEMENT `AUCUN`.
  #      Un vrai argument nomme AUCUN s'ecrit `./AUCUN`.
  if [ "$c_args" != "${c_args#AUCUN}" ] && [ "$c_args" != "AUCUN" ]; then
    echo "[KO ] declaration NON-JOUABLE : champ arguments AMBIGU ('$c_args') pour '$c_nom'" >&2
    echo "      AUCUN est le jeton « aucun argument » et n'a pas d'echappement." >&2
    echo "      ⇒ un argument reel qui commence par AUCUN s'ecrit './AUCUN...'." >&2
    PERIMEES=$((PERIMEES + 1)); continue
  fi
  if ! [[ "$c_rc" =~ ^[0-9]+$ ]]; then
    echo "[KO ] declaration NON-JOUABLE : rc attendu non numerique ('$c_rc') pour '$c_nom'" >&2
    PERIMEES=$((PERIMEES + 1)); continue
  fi
  # 🔴 REVUE 2026-09-02 — UN DOUBLON PASSAIT LES CINQ CONTROLES ET LA SECONDE
  #    LIGNE N'AVAIT AUCUN EFFET : `champ_de` rend le PREMIER element qui
  #    correspond. Mettre la table a jour en AJOUTANT une ligne laissait donc
  #    l'ANCIENNE en vigueur, sans un mot — meme classe que le « champ vide »
  #    solde le 2026-08-31.
  if [ -n "${DECLAREE[$c_nom]:-}" ]; then
    echo "[KO ] la table declare '$c_nom' DEUX FOIS — seule la 1re ligne compte." >&2
    echo "      ⛔ Un doublon laisse l'ANCIENNE declaration en vigueur en silence." >&2
    PERIMEES=$((PERIMEES + 1)); continue
  fi
  DECLAREE["$c_nom"]=1
  if [ -z "${EXISTE[$c_nom]:-}" ]; then
    echo "[KO ] la table des NON-JOUABLES declare '$c_nom', qui n'existe plus dans tools/verif_*.py." >&2
    echo "      Une declaration perimee cache une gate disparue. Corriger la table." >&2
    PERIMEES=$((PERIMEES + 1))
  fi
done

champ_de() {  # $1 = basename, $2 = index de champ (2..5) ; imprime le champ
  local d
  for d in "${NON_JOUABLES[@]}"; do
    [ "${d%%|*}" = "$1" ] || continue
    awk -F'|' -v k="$2" '{print $k}' <<<"$d"
    return 0
  done
  return 1
}

# ── LA PASSE ────────────────────────────────────────────────────────────────
N_VERTE=0; N_ROUGE=0; N_NJ=0
ROUGES=()
T_DEBUT=$(date +%s)

echo "═══ $MOI — ${#GATES[@]} gates decouvertes par glob ═══"
echo

for g in "${GATES[@]}"; do
  nom="$(basename "$g")"
  declaree=0; motif=""; temoin=""; rc_att=""
  ARGS=()

  if motif="$(champ_de "$nom" 2)"; then
    declaree=1
    temoin="$(champ_de "$nom" 3)"
    rc_att="$(champ_de "$nom" 5)"
    if [ -e "$temoin" ]; then
      # Le temoin est la : la gate REDEVIENT jouable, avec ses arguments.
      # ⚠️ dn4-39 — LE JETON LITTERAL `AUCUN` VEUT DIRE « aucun argument ».
      #    4 des 6 gates declarees n'en prennent pas, et un champ VIDE est
      #    interdit (il sautait une gate rouge en silence, revue du 2026-08-31).
      #    ⇒ le choix est ECRIT dans la table, ⛔ ce n'est pas un trou.
      a4="$(champ_de "$nom" 4)"
      [ "$a4" = "AUCUN" ] || read -r -a ARGS <<<"$a4"
      printf '[  temoin  ] %-38s %s est present ⇒ la gate est JOUEE\n' "$g" "$temoin"
      declaree=0   # elle est traitee comme une gate ordinaire
    fi
  fi

  # (3) Une gate declaree NON-JOUABLE est jouee QUAND MEME, sans argument :
  #     c'est le seul moyen de verifier qu'elle est encore une gate.
  # 🔴 REVUE 2026-09-02 — LA CAPACITE ETAIT DETECTEE PAR UN grep SUR LE TEXTE,
  #    COMMENTAIRES COMPRIS. Rien ne distinguait un `add_argument("--cockpit")`
  #    d'une citation en prose — et ce depot cite TOUT. Une future gate qui
  #    MENTIONNE l'option aurait recu un argument inconnu ⇒ argparse sort en 2
  #    ⇒ ROUGE, avec pour seul motif un message d'usage.
  #    ⇒ on epingle la DECLARATION argparse, ⛔ plus la chaine nue.
  if [ "$declaree" -eq 0 ] && [ -n "$COCKPIT" ] \
     && grep -q -- 'add_argument("--cockpit"' "$g"; then
    ARGS+=(--cockpit "$COCKPIT")
  fi

  t0=$(date +%s)
  if [ "${#ARGS[@]}" -eq 0 ]; then
    sortie="$(timeout "$TIMEOUT_GATE" python3 "$g" 2>&1)"; rc=$?
  else
    sortie="$(timeout "$TIMEOUT_GATE" python3 "$g" "${ARGS[@]}" 2>&1)"; rc=$?
  fi
  t1=$(date +%s)

  if [ "$declaree" -eq 1 ]; then
    if [ "$rc" -eq "$rc_att" ]; then
      printf '[NON-JOUABLE] %-38s rc=%-3s (attendu) temoin absent : %s\n' "$g" "$rc" "$temoin"
      [ "$SILENCIEUX" -eq 1 ] || printf '              motif : %s\n' "$motif"
      N_NJ=$((N_NJ + 1))
    else
      N_ROUGE=$((N_ROUGE + 1))
      ROUGES+=("$g (rc=$rc, la declaration NON-JOUABLE annonce $rc_att)")
      printf '[ROUGE      ] %-38s rc=%-3s ⛔ DECLARATION DEMENTIE (attendu %s)\n' "$g" "$rc" "$rc_att"
      echo "┌── sortie de $g ─────────────────────────────────────────"
      printf '%s\n' "$sortie" | sed 's/^/│ /'
      echo "└──────────────────────────────────────────────────────────"
      echo "  ⛔ La gate ne se comporte plus comme sa declaration l'affirme."
      echo "     Soit elle a change, soit la table est a corriger — ⛔ pas a ignorer."
    fi
    continue
  fi

  if [ "$rc" -eq 0 ]; then
    N_VERTE=$((N_VERTE + 1))
    printf '[VERTE      ] %-38s rc=0   %4ss\n' "$g" "$((t1 - t0))"
  else
    N_ROUGE=$((N_ROUGE + 1))
    ROUGES+=("$g (rc=$rc)")
    printf '[ROUGE      ] %-38s rc=%-3s %4ss\n' "$g" "$rc" "$((t1 - t0))"
    # (4) la sortie n'est imprimee QUE MAINTENANT, c'est-a-dire sur echec.
    echo "┌── sortie de $g ─────────────────────────────────────────"
    printf '%s\n' "$sortie" | sed 's/^/│ /'
    echo "└──────────────────────────────────────────────────────────"
  fi
done

T_FIN=$(date +%s)
echo
echo "BILAN : $N_VERTE VERTE, $N_ROUGE ROUGE, $N_NJ NON-JOUABLE sur ${#GATES[@]} gates ($((T_FIN - T_DEBUT))s)"

if [ "$PERIMEES" -ne 0 ]; then
  echo "⛔ $PERIMEES declaration(s) NON-JOUABLE invalide(s) — corriger la table du script."
fi
if [ "$N_ROUGE" -ne 0 ]; then
  echo "⛔ ROUGES :"
  for r in "${ROUGES[@]}"; do echo "   · $r"; done
fi

if [ "$N_ROUGE" -ne 0 ] || [ "$PERIMEES" -ne 0 ]; then
  exit 1
fi
exit 0
