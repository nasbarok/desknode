#!/usr/bin/env bash
# ═════════════════════════════════════════════════════════════════════════════
# tools/run_gates.sh — dn4-24 / AC1
#
#   UNE COMMANDE PASSE TOUTES LES GATES, ET AUCUNE N'EST SAUTEE EN SILENCE.
#
#   Usage :  bash tools/run_gates.sh [--silencieux] [--cockpit <chemin>] [--temoin-appariement] [-h|--help]
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
#     ⚠️ UNE QUATRIEME CAUSE EST AJOUTEE LE 2026-09-09 PAR `dn7-3`, ET ELLE EST
#        DEFINIE **ICI**, avec les trois autres — une lettre que personne ne
#        peut chercher n'est pas une categorie, c'est un sigle :
#        **(D) UN MOTEUR D'EXECUTION EST UN PREREQUIS DE BANC, ⛔ PAS UNE
#        DEPENDANCE DU DEPOT.** Une gate qui LANCE un banc a besoin de
#        l'interprete de ce banc. Le depot, lui, n'en a pas besoin : rien de ce
#        qu'il livre ne s'execute avec. ⇒ le moteur absent ⛔ n'est PAS un
#        rouge, et ⛔ surtout PAS un vert — la gate rend son 4, et la regle (3)
#        la joue QUAND MEME pour verifier qu'elle rend bien ce 4.
#        🔴 UNE GATE VERTE SUR UN BANC QUI N'A PAS TOURNE SERAIT PIRE QUE PAS
#        DE GATE : elle certifierait un comportement que personne n'a mesure.
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

# 🔴 dn5-6 / CONSTAT (3) — 2026-09-05 : LE `cwd` DE L'APPELANT EST GARDE AVANT
#    LE `cd`, PARCE QUE C'EST LUI QUI DONNE SON SENS A UN CHEMIN RELATIF.
#    MESURE (`mesures/dn5-6/T1-filtre-10-constats.txt`, constat 3) : depuis
#    `~/projects`, `--cockpit compagnon_project` sortait en **2** sur
#    « chemin inexistant » a propos d'un chemin **QUI EXISTE** — la validation
#    tombait APRES ce `cd` et ⛔ ne normalisait jamais. Et pire, l'homonyme
#    `--cockpit tools` (qui n'existe PAS depuis `~/projects` mais existe SOUS
#    la racine) etait **accepte en silence** : la passe a demarre, mesuree.
CWD_APPELANT="$PWD"

# ═══ dn5-6 / CONSTAT (4) — LE DETECTEUR QUI FAIT AUTORITE ═══════════════════
#
# 🔴 UN `grep` NE DISTINGUE PAS UN COMMENTAIRE D'UN CODE, et ce depot CITE
#    tout. La revue du 2026-09-02 avait epingle `add_argument("--cockpit"` pour
#    ne plus mordre sur la chaine nue — mais une PROSE qui cite exactement cette
#    forme la dupe encore, et une declaration en GUILLEMETS SIMPLES ou COUPEE
#    lui echappe. Les deux fautes ont ete REPLANTEES et VUES le 2026-09-05.
# ⇒ ON DEMANDE A PYTHON. L'arbre syntaxique voit les trois formes reelles et
#   n'est ⛔ PAS dupe par un commentaire — mesure, ⛔ pas argument.
# ⚠️ Le grep d'origine est GARDE, et les deux sont APPARIES : toute divergence
#    est SIGNALEE. C'est elle qui dira, le jour venu, qu'une gate a change de
#    forme — un controle qui ne peut pas rougir n'est pas un controle.
AST_COCKPIT='
import ast, sys
try:
    a = ast.parse(open(sys.argv[1], encoding="utf-8", errors="replace").read(),
                  filename=sys.argv[1])
except (SyntaxError, OSError, UnicodeDecodeError):
    sys.exit(2)                      # ⛔ indecidable : ⛔ pas « non »
for n in ast.walk(a):
    if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and n.func.attr == "add_argument"):
        for x in n.args:
            if isinstance(x, ast.Constant) and x.value == "--cockpit":
                sys.exit(0)
sys.exit(1)
'

RACINE="$(cd "$(dirname "$SRC")/.." && pwd)"
cd "$RACINE" || exit 1

SILENCIEUX=0
COCKPIT=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --silencieux) SILENCIEUX=1 ;;
    # ═══ dn5-6 / NFR7 — LE TEMOIN QUI **REPLANTE** LA FAUTE DU CONSTAT (4) ══
    #
    # ⛔ UN TEMOIN QUI DEBRANCHE LA GARDE NE PROUVE QUE SON EXISTENCE.
    #    Celui-ci ECRIT trois gates de synthese dans un repertoire temporaire,
    #    dont DEUX portent la faute historique (guillemets simples, et
    #    declaration coupee), et il exige que l'appariement les VOIE.
    # ⚠️ Il est HORS de la passe : `run_gates.sh` sans argument ne le joue
    #    jamais, et la CI non plus. C'est un outil de PREUVE, ⛔ pas un mode.
    --temoin-appariement)
      _t="$(mktemp -d)" || exit 2
      printf 'import argparse\nap=argparse.ArgumentParser()\nap.add_argument("--cockpit")\n' > "$_t/litteral.py"
      printf 'import argparse\nap=argparse.ArgumentParser()\nap.add_argument(%s--cockpit%s)\n' "'" "'" > "$_t/simple.py"
      printf 'import argparse\nap=argparse.ArgumentParser()\nap.add_argument(\n    "--cockpit")\n' > "$_t/coupe.py"
      printf 'import argparse\n# on cite add_argument("--cockpit" en prose\nap=argparse.ArgumentParser()\n' > "$_t/prose.py"
      _ko=0
      _att() {   # $1=fichier $2=large attendu $3=etroit attendu $4=ecart attendu
        local e=0 l=0
        grep -q -- 'add_argument("--cockpit"' "$_t/$1" && e=1
        python3 -c "$AST_COCKPIT" "$_t/$1" && l=1
        local d=0; [ "$e" -ne "$l" ] && d=1
        if [ "$l" -eq "$2" ] && [ "$e" -eq "$3" ] && [ "$d" -eq "$4" ]; then
          printf '  [OK ] %-14s large=%s etroit=%s divergence=%s\n' "$1" "$l" "$e" "$d"
        else
          printf '  [KO ] %-14s large=%s (attendu %s) etroit=%s (attendu %s) divergence=%s (attendu %s)\n' \
                 "$1" "$l" "$2" "$e" "$3" "$d" "$4"
          _ko=$((_ko + 1))
        fi
      }
      echo "TEMOIN dn5-6 / constat (4) — L'APPARIEMENT VOIT-IL LA FAUTE REPLANTEE ?"
      _att litteral.py 1 1 0     # la forme d'aujourd'hui : vue des deux cotes
      _att simple.py   1 0 1     # 🔴 FAUTE REPLANTEE : le grep etroit est AVEUGLE
      _att coupe.py    1 0 1     # 🔴 FAUTE REPLANTEE : idem
      _att prose.py    0 1 1     # 🔴 le grep etroit est DUPE par une citation
      rm -rf "$_t"
      echo "TEMOIN : $((4 - _ko)) OK, $_ko KO"
      [ "$_ko" -eq 0 ] || exit 1
      exit 0
      ;;
    --cockpit)
      shift
      [ "$#" -gt 0 ] || { echo "--cockpit attend un chemin" >&2; exit 2; }
      # 🔴 REVUE 2026-09-02 — UN CHEMIN FAUX ETAIT ACCEPTE PUIS JETE EN SILENCE.
      #    Temoin absent ⇒ `declaree` restait a 1 ⇒ `--cockpit` n'etait JAMAIS
      #    transmis ⇒ la gate retombait sur son COCKPIT_DEFAUT et mesurait un
      #    depot que personne n'avait demande. Une coquille d'une lettre rendait
      #    deux « DECLARATION DEMENTIE » et rc 1, sans un mot sur le chemin.
      #    ⛔ Une chaine VIDE aussi : `${COCKPIT:-…}` la traite comme « absent ».
      # 🔴 dn5-6 / CONSTAT (3) — LE CHEMIN EST RESOLU CONTRE LE `cwd` DE
      #    L'APPELANT, PUIS NORMALISE EN ABSOLU. Un relatif veut dire ce que
      #    l'appelant croit qu'il veut dire, ⛔ pas ce que la racine en fait.
      case "$1" in
        /*) _ck="$1" ;;
        *)  _ck="$CWD_APPELANT/$1" ;;
      esac
      if [ -z "$1" ] || [ ! -d "$_ck" ]; then
        echo "--cockpit : chemin inexistant ou vide — '$1'" >&2
        echo "  resolu contre le cwd de l'appelant ⇒ '$_ck'" >&2
        echo "  ⛔ Un chemin faux serait JETE en silence et la gate mesurerait" >&2
        echo "     un AUTRE depot. On echoue FERME plutot que de mesurer a cote." >&2
        echo "  ⚠️ Un relatif se lit depuis VOTRE cwd ($CWD_APPELANT)," >&2
        echo "     ⛔ pas depuis la racine du depot — un homonyme sous la" >&2
        echo "     racine passait sinon EN SILENCE (mesure dn5-6, constat 3)." >&2
        exit 2
      fi
      # ⇒ ABSOLU ET NORMALISE : ce qui part aux gates ne depend plus d'un cwd.
      # 🔴 REVUE DU 2026-09-05 — SANS LA GARDE `||`, CE `cd` RETOMBAIT SUR LE
      #    DEFAUT QU'IL REPARE : un repertoire qui EXISTE (`-d` vrai) mais dans
      #    lequel on ne peut pas ENTRER (droits, course) laissait `COCKPIT`
      #    **VIDE**, et la passe continuait ⇒ toutes les gates mesuraient leur
      #    `COCKPIT_DEFAUT` **en silence**, c'est-a-dire le constat (4) exactement.
      # ⚠️ ⛔ PAS DE REDIRECTION VERS LE PUITS ICI — la garde `garde_puits` de ce
      #    fichier (AC1.4) l'interdit, et elle m'a attrape : un `2>/dev/null`
      #    posé ici a fait REFUSER TOUTE LA PASSE. C'est la bonne regle : le
      #    message d'erreur du `cd` doit RESTER VISIBLE. Ce qu'on garde, c'est
      #    que `COCKPIT` ne reste pas VIDE — la sortie, elle, se lit.
      COCKPIT="$(cd "$_ck" && pwd)"
      if [ -z "$COCKPIT" ]; then
        echo "--cockpit : repertoire INACCESSIBLE (il existe, on n'y entre pas) — '$_ck'" >&2
        echo "  ⛔ On echoue FERME : un COCKPIT vide ferait mesurer un AUTRE depot." >&2
        exit 2
      fi
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
# ⚠️ REVUE DE CODE dn4-44 (2026-09-03) — CE TEMOIN EST UN **REPERTOIRE**, ET LA
#    REGLE ECRITE 20 LIGNES PLUS HAUT DIT « CHAQUE TEMOIN EST LE FICHIER QUE SA
#    GATE LIT VRAIMENT ». MESURE : `--cockpit <repertoire vide>` ⇒ le temoin
#    existe ⇒ les gates de cockpit sont JOUEES ⇒ elles rendent 4 (prerequis
#    absent) ⇒ le runner imprime `[ROUGE] rc=4`, la valeur qui partout ailleurs
#    veut dire « pas un rouge ».
# 🔴 LE CORRECTIF A ETE ESSAYE ET **RETIRE**, ET C'EST ECRIT PLUTOT QUE TU : un
#    temoin FICHIER fait declarer la gate NON-JOUABLE, or une gate declaree est
#    rejouee **SANS ARGUMENT** (choix delibere de `dn4-39`, ligne « (3) ») ⇒
#    elle retombe sur son cockpit PAR DEFAUT, qui existe sur le poste ⇒ rc=0 ⇒
#    `DECLARATION DEMENTIE`. Le correctif fabriquait un FAUX NEGATIF la ou il
#    corrigeait un faux positif.
# ⇒ LA VRAIE CAUSE EST AILLEURS : c'est la branche ORDINAIRE qui classe tout
#   `rc != 0` en ROUGE, alors que le contrat reserve `4` a « prerequis absent,
#   ⛔ pas un verdict sur le code ». La corriger touche les 29 gates et le
#   dessin de `dn4-39` ⇒ ⛔ HORS PERIMETRE de dn4-44, verse au ledger avec son
#   porteur plutot que corrige en passant.
#
# ═══ dn5-3 / AC3.3.g — 2026-09-04 : `TEMOIN_COCKPIT_ABS` EST RETIRE ═════════
#
# ⚠️ ⛔ CECI N'EST PAS UNE SUPPRESSION MUETTE (NFR3) : voici ce que ce temoin
#    gardait, et pourquoi il n'a plus lieu d'etre.
#
# CE QU'IL DISAIT — texte d'origine, ⛔ pas reecrit :
#    « `TEMOIN_COCKPIT_ABS` NE SUIT PAS `--cockpit`, ET C'EST DELIBERE :
#      `verif_dossier_d5_dn45.py` n'a PAS d'option `--cockpit`, elle lit deux
#      chemins ABSOLUS ecrits en dur (l. 47-48). Lui donner le temoin de
#      `--cockpit` la ferait declarer jouable alors qu'elle ne lirait pas ce
#      dossier-la. ⛔ LIMITE ECRITE : sur une machine TIERCE ou
#      `~/projects/compagnon_project` existerait, le temoin serait present et la
#      gate serait JOUEE — elle rougirait alors sur ses chemins absolus. C'est
#      le sens CONSERVATEUR (echouer fort), ⛔ pas un skip. `dn5-3` ferme ce
#      coin. »
#
# CE QUI L'A PERIME — `dn5-3`, le 2026-09-04 : la gate fait desormais deriver sa
#    racine de `__file__` et prend le cockpit en ARGUMENT. Les deux chemins
#    absolus n'existent plus. ⇒ la premisse du temoin (« elle n'a PAS d'option
#    `--cockpit` ») est FAUSSE depuis ce jour, et la LIMITE ECRITE qu'il portait
#    — « sur une machine tierce elle serait jouee et rougirait sur ses chemins
#    absolus » — n'a plus d'objet : il n'y a plus de chemin absolu.
# ⇒ Sa declaration suit maintenant `${TEMOIN_COCKPIT}`, comme les trois autres
#    gates du cockpit. Un temoin REFERENCE PAR RIEN est de la meme famille que
#    le « champ vide » soldé le 2026-08-31 : il se RETIRE.
#
# 🔴 CORRIGE A LA REVUE DE CODE DU 2026-09-04 — ⛔ CE QUI PRECEDE N'EST PAS
#    EFFACE, MAIS DEUX DE SES PHRASES SONT TROP FORTES, ET C'EST MESURE.
#
#  (1) « la LIMITE ECRITE n'a plus d'objet : il n'y a plus de chemin absolu ».
#      ⛔ LA LIMITE SURVIT — seule sa CAUSE a change. Sur une machine tierce ou
#      un repertoire de ce nom existe SANS etre le cockpit, le temoin est
#      present, la gate est JOUEE, et elle est ROUGE : ⛔ plus « sur ses chemins
#      absolus », mais sur `⛔ FICHIER INTROUVABLE`. MESURE le 2026-09-04 avec
#      un repertoire VIDE en `--cockpit` : rc **1**, `BILAN : 5 OK, 2 KO`.
#      ⇒ le sens CONSERVATEUR (echouer fort) est INCHANGE, et c'etait le point.
#
#  (2) « comme les trois autres gates du cockpit ». ⛔ PAS SUR CE CAS-LA. Meme
#      repertoire vide : `verif_ledger_dn416.py` rend **4**,
#      `verif_campagne_dn440.py` rend **4**, `verif_dossier_dn415.py` rend
#      **1**, et `verif_dossier_d5_dn45.py` rend **1**. ⇒ elle s'aligne sur UNE
#      de ses soeurs, ⛔ pas sur trois. MOTIF : son prerequis se juge sur
#      `os.path.isdir(cockpit)` seul, la ou `dn416`/`dn440` exigent un FICHIER
#      attendu. Un repertoire qui existe sans etre le cockpit passe donc le
#      prerequis et ressort en verdict sur le DOSSIER.
#
#  ⚠️ LA CI N'EST PAS TOUCHEE, et c'est pour ca que le code ⛔ n'est PAS change
#     ici (arbitrage owner du 2026-09-04, voie (b)) : sur un runner le repertoire
#     n'existe pas du tout ⇒ temoin absent ⇒ la gate rend son `rc=4` declare.
#     Le durcissement du prerequis AU FICHIER reecrirait une CONDITION de
#     controle ⇒ NFR7 exigerait un mutant qui REPLANTE. ⇒ ecrit ici, ⛔ pas fait
#     en passant.
#
# `managed_components/` est GITIGNORE (186 Mo) et repeuple par
# `idf.py reconfigure`. Le temoin est RELATIF : il vit dans le clone.
# 🔴 REVUE 2026-09-02 — LA BORNE PAR GATE DOIT TENIR **SOUS** CELLE DU JOB.
#    `gates.yml` accorde `timeout-minutes: 20` au job ; l'ancien `timeout 1800`
#    (30 min) etait donc INATTEIGNABLE en CI : GitHub tuait le job avant, et on
#    perdait le BILAN, la liste des ROUGES et la sortie capturee que la regle (4)
#    exige d'imprimer — le run devenant `cancelled`, ⛔ pas `failure`.
#    Mesure du poste : 63 s pour les 27 gates. 600 s laisse un facteur ~9.
#    ⚠️ RE-MESURE dn4-44 (2026-09-03), ⛔ LIGNE D'ORIGINE NON EFFACEE : depuis
#    l'entree de `verif_campagne_dn440.py` au glob, le balayage porte 29 gates
#    et la campagne est A ELLE SEULE la plus chere du depot. Le plafond reste
#    tres large. ⛔ AUCUN CHIFFRE N'EST RECOPIE ICI, ET C'EST DELIBERE : le
#    total s'imprime sur la ligne `BILAN` a chaque tir, il varie d'un tir a
#    l'autre, et un nombre ecrit dans un commentaire se perime le jour ou l'on
#    ajoute une gate — c'est-a-dire le jour ou il compte. ⇒ la ligne de BILAN
#    est la seule source ; l'ARGUMENT du plafond, lui, se relit a chaque ajout.
# 🔴 RELEVE A **900 s** LE 2026-09-12 (`dn4-48`), SUR UNE MESURE, ET LES
#    LIGNES CI-DESSUS ⛔ NE SONT PAS EFFACEES — elles disent l'argument tel
#    qu'il etait, et c'est lui qui a cesse d'etre vrai.
#    L'ARGUMENT DE 2026-09-02 (« 600 s laisse un facteur ~9 ») etait PERIME
#    AVANT cette marche : au releve T0 du 2026-09-12, `verif_campagne_dn56.py`
#    consommait **588 s** sur un plafond de 600 — **2 % de marge**, ⛔ pas un
#    facteur 9. Elle rejoue CHAQUE mutant de CHAQUE gate du depot ; toute gate
#    qui gagne un mutant, ou dont un tir coute une seconde de plus, la pousse
#    dehors.
#    CE QUE `dn4-48` Y A AJOUTE, ET C'EST ASSUME : `tools/verif_lhm_ps_dn83.py`
#    joue desormais un **troisieme** sens (le RETARD), et porte 13 mutants au
#    lieu de 11. Mesure : un tir du banc passe de ~7 s a ~16 s, et
#    `verif_campagne_dn56.py` de 588 s a **677 s**.
#    ⚠️ LE COUT A ETE REDUIT D'ABORD, ⛔ le plafond n'a ete releve qu'ENSUITE :
#       le pas d'attente du produit est DERIVE de la borne (au moins dix
#       tours), les bornes du banc sont PETITES, et chaque stub attend que le
#       port soit RENDU. Sans ca le tir coutait 21 s, ⛔ pas 16.
#    ⚠️ LA REGLE DU 2026-09-02 TIENT TOUJOURS : **900 s reste SOUS les 20 min
#       du job** (`gates.yml`), donc la borne par gate demeure ATTEIGNABLE en
#       CI et le `BILAN` sort. ⛔ Et la CI ne paie PAS le surcout : sans hote
#       PowerShell, `verif_lhm_ps_dn83.py` y est NON-JOUABLE et ⛔ ne declare
#       AUCUN mutant, donc `dn56` n'en rejoue aucun.
#    🎯 CE QUI FERMERAIT LE SUJET POUR DE BON — et ce n'est ⛔ PAS ce
#       relevement, qui DEPLACE le cout : un decoupage de `dn56` qui cesse de
#       rejouer TOUS les mutants de TOUTES les gates dans un seul tir. C'est
#       au ledger, porteur `epic-dn8`, motif `LE VRAI PLAFOND`.
TIMEOUT_GATE="${DN_TIMEOUT_GATE:-900}"

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

# 🔴 dn7-3 — LE MOTEUR JavaScript EST UN PREREQUIS, ⛔ PAS UNE DEPENDANCE DU
#    DEPOT. `tools/verif_banc_langue_dn73.py` lance un banc qui EXECUTE le
#    `<script>` de `installeur/index.html` : sans moteur, il n'y a rien a
#    jouer. ⇒ la gate rend son `rc=4` declare, et elle est portee NON-JOUABLE.
#    ⚠️ LE TEMOIN EST **DERIVE**, ⛔ pas ecrit en dur : `command -v node` rend
#       le chemin REEL du binaire, quel qu'il soit ; le repli est un chemin qui
#       n'existe pas, pour que `[ -e ]` soit FAUX et ⛔ pas vide — un temoin
#       vide sauterait la gate en silence, et pour toujours.
#    🔴 ⛔ UNE GATE VERTE SUR UN BANC QUI N'A PAS TOURNE SERAIT PIRE QUE PAS DE
#       GATE : c'est pourquoi la gate rend 4 au lieu de 0, et pourquoi la regle
#       (3) la joue QUAND MEME pour verifier qu'elle rend bien ce 4.
#    ⛔ ET ⛔ SANS REDIRECTION VERS LE PUITS : la regle (4) de ce script
#       l'interdit, et sa garde relit CE FICHIER. `command -v` n'ecrit
#       rien sur la sortie d'erreur quand il ne trouve pas — la
#       redirection etait INUTILE en plus d'etre interdite. MESURE : la
#       garde a refuse de tourner tant qu'elle etait la.
# ⚠️ ANNOTE LE 2026-09-12 (`dn8-2`) — **`TEMOIN_NODE` EST RETIRE, ET C'EST CE
#    FICHIER QUI L'EXIGE** : « Un temoin REFERENCE PAR RIEN est de la meme
#    famille que le champ vide solde le 2026-08-31 : il se RETIRE. » Depuis que
#    la gate du banc a DEUX prerequis, sa ligne suit `${TEMOIN_BANC_HTTP}`
#    ci-dessous, et ⛔ plus AUCUNE entree de la table ne citait `TEMOIN_NODE`.
#    ⛔ Le paragraphe ci-dessus n'est PAS efface : il dit pourquoi un temoin se
#    **DERIVE** plutot que de s'ecrire en dur, et c'est exactement ce que fait
#    son remplacant — sur une CONJONCTION de deux prerequis au lieu d'un.

# 🔴 dn8-2 — LE TEMOIN DE LA GATE DU BANC EST **DERIVE DES DEUX PREREQUIS**, ⛔
#    plus du seul moteur. MESURE DU 2026-09-12 : depuis que cette gate lie le
#    VRAI serveur du produit sur 127.0.0.1:0 pour que le banc lui parle par
#    HTTP, elle a DEUX prerequis — et le temoin n'en couvrait qu'un. Une boucle
#    locale filtree (politique, conteneur durci) lui faisait donc rendre 4 avec
#    le temoin PRESENT, et le runner l'imprimait `[ROUGE] rc=4` : la valeur qui,
#    partout ailleurs dans ce fichier, veut dire « ⛔ pas un rouge ».
#    ⚠️ UN TEMOIN EST UN **FICHIER**, et « la boucle locale accepte un bind »
#       n'en est pas un. ⇒ on DERIVE un chemin : celui du moteur quand les DEUX
#       prerequis tiennent, un chemin qui n'existe pas sinon. C'est exactement le
#       patron de `TEMOIN_NODE` ci-dessus, applique a une conjonction.
#    ⛔ ET ⛔ SANS REDIRECTION VERS LE PUITS : la regle (4) de ce fichier
#       l'interdit, et sa garde relit CE FICHIER. Le refus est CAPTURE en Python
#       et rendu comme un CHEMIN, ⛔ jamais comme une trace sur l'erreur standard.
TEMOIN_BANC_HTTP="$(python3 -c 'import shutil, socket
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    s.close()
    print(shutil.which("node") or "/nonexistent/node-absent")
except OSError:
    print("/nonexistent/bind-refuse")' || echo /nonexistent/python3-absent)"

# 🔴 dn8-3 — LE TEMOIN DE LA GATE DE POLARITE LHM EST **DERIVE**, ET IL
#    ESSAIE **PLUSIEURS NOMS**. C'est LA lecon de cette marche, et elle est
#    MESUREE le 2026-09-12 :
#        shutil.which("powershell")     ⇒ None
#        shutil.which("powershell.exe") ⇒ le chemin REEL
#    ⇒ le ledger a publie CINQ FOIS « il faudrait un hote PowerShell, que
#      le WSL de la tour n'a pas ». C'etait un **NOM**, ⛔ pas une absence,
#      et `powershell.exe` 5.1.19041.6456 repond rc=0 depuis ce WSL.
#    ⚠️ UN TEMOIN EST UN **FICHIER** : on rend le chemin du premier hote
#       trouve, et un chemin qui n'existe pas sinon — pour que [ -e ] soit
#       FAUX et ⛔ pas vide (un temoin vide sauterait la gate en silence).
#    ⛔ ET ⛔ SANS REDIRECTION VERS LE PUITS : la regle (4) l'interdit, et sa
#       garde relit CE FICHIER.
#    🔴 CORRIGE LE 2026-09-12 (revue) — LE TEMOIN NE COUVRAIT QU'UN PREREQUIS
#       SUR TROIS. La gate rend 4 depuis TROIS : l'hote PowerShell, un `bind`
#       accepte, et un dossier temporaire VISIBLE DE WINDOWS. La ou
#       `powershell.exe` resout mais qu'un des deux autres manque, le temoin
#       existait, la gate etait JOUEE, et son 4 s'imprimait `[ROUGE] rc=4` — la
#       valeur qui, partout ailleurs ici, veut dire « ⛔ pas un rouge ». C'est
#       EXACTEMENT le defaut que `TEMOIN_BANC_HTTP` a ferme vingt lignes plus
#       haut le meme jour. ⇒ le temoin derive de la CONJONCTION.
#    ⚠️ `wslpath` EST EXIGE : sans lui ⛔ aucun chemin ne se traduit pour
#       PowerShell, et un `pwsh` **Linux** sur un runner rendrait le temoin
#       PRESENT sur une machine qui ⛔ ne peut pas jouer ce banc.
TEMOIN_POWERSHELL="$(python3 -c 'import os, shutil, socket, subprocess, sys
def absent(m):
    print("/nonexistent/" + m)
    sys.exit(0)
ps = None
for n in ("powershell.exe", "pwsh.exe", "powershell", "pwsh"):
    ps = shutil.which(n)
    if ps:
        break
if not ps:
    absent("powershell-absent")
if not shutil.which("wslpath"):
    absent("wslpath-absent")
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    s.close()
except OSError:
    absent("bind-refuse")
d = ""
try:
    r = subprocess.run([ps, "-NoProfile", "-Command", "$env:TEMP"], timeout=25,
                       stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    w = subprocess.run(["wslpath", "-u",
                        r.stdout.decode("utf-8", "replace").strip()], timeout=25,
                       stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    d = w.stdout.decode("utf-8", "replace").strip()
except Exception:
    d = ""
if not d or not os.path.isdir(d):
    absent("temp-windows-absent")
print(ps)' || echo /nonexistent/python3-absent)"

NON_JOUABLES=(
  "verif_sr03.py|le PDF [AN] AN4545 (VL6180X, DocID026571 Rev 1) n'est PAS au depot : document StMicroelectronics, ⛔ non redistribuable. La gate l'attend en argument et sort en 2 sur son message d'usage — rc=2 n'est PAS un rouge.|tools/fixtures/AN4545.pdf|tools/fixtures/AN4545.pdf firmware/desknode/main/dn_console.c|2"
  "verif_dossier_dn415.py|CAUSE A — le cockpit de planification est un depot PRIVE, ⛔ jamais clone a cote du code. Sans lui la gate n'a AUCUNE occurrence a arbitrer. ⚠️ La ou le cockpit EST la elle rend 17 OK / 10 KO sur le CONTENU : ⛔ une CI ne verra JAMAIS ces 10 KO, et elle ne pretend pas les garder.|${TEMOIN_COCKPIT}|AUCUN|4"
  "verif_ledger_dn416.py|CAUSE A — le cockpit de planification est un depot PRIVE, ⛔ jamais clone. Sans lui il n'y a ni ledger ni tracker a confronter. ⚠️ le controle dn_ok (« le depot code EST desknode ») reste un CONTROLE : son echec reste un ROUGE, ⛔ pas un prerequis.|${TEMOIN_COCKPIT}|AUCUN|4"
  "verif_dossier_d5_dn45.py|CAUSE A — le cockpit de planification est un depot PRIVE, ⛔ jamais clone a cote du code. dn5-3 (2026-09-04) a fait deriver sa racine de __file__ et rendu le cockpit PARAMETRABLE : sans lui, elle joue les 4 fichiers faisant autorite DU CLONE et ANNONCE les 2 qu'elle n'a pas pu controler, puis rend 4. Un vrai KO trouve dans la moitie jouee rend 1, dans cet ordre. ⚠️ AVANT dn5-3 c'etait une CAUSE C : deux chemins ABSOLUS, VERTE dans un clone neuf pose sur cette machine, 1 OK / 7 KO sur un runner. ⛔ Ce n'est plus vrai, et la ligne le DIT plutot que de l'effacer.|${TEMOIN_COCKPIT}|AUCUN|4"
  "verif_boitier_dn64.py|CAUSE A — le cockpit de planification est un depot PRIVE, ⛔ jamais clone a cote du code. La MOITIE DEPOT joue toujours (la place, les deux comptes, la notice, la roadmap, le CHANGELOG) ; sans le cockpit, les DEUX controles qui lisent le ledger et le tracker sont DECLARES non joues avec leur motif — ⛔ ni joues, ni comptes verts — et la gate rend 4. ⚠️ ⛔ AUCUN COMPTE OK/KO N'EST PUBLIE ICI, ET C'EST DELIBERE : la declaration voisine de verif_dossier_dn415.py en annonce un qui est FAUX depuis qu'un controle a ete ajoute chez elle, et ce defaut est deja au ledger (porteur epic-dn4). ⛔ On ne reproduit pas le defaut qu'on vient de declarer. Le seul compte qui fait foi est la ligne BILAN du tir.|${TEMOIN_COCKPIT}|AUCUN|4"
  "verif_veille_dn33.py|CAUSE B — managed_components/ est GITIGNORE (186 Mo, repeuple par: idf.py reconfigure) et porte le generateur AMONT de LVGL. ⛔ 2 blocs sur 18 ne sont pas exerces ; TOUT LE RESTE EST JOUE. Elle disait deja le bon motif et le remede — il lui manquait le rc.|${TEMOIN_LVGL_VEILLE}|AUCUN|4"
  "verif_harnais_dn413.py|CAUSE B — sans l'arbre LVGL le corpus C est INCOMPLET, et la chasse aux renvois FANTOMES accusait tools/dn_police.py de citer des fonctions QUI EXISTENT (lv_text_get_width est defini dans lvgl__lvgl/src/misc/lv_text.c). ⛔ Un diagnostic FAUX publie automatiquement. Elle DECLARE desormais, elle n'accuse plus — et ⛔ elle ne devient PAS aveugle la ou l'arbre est la.|${TEMOIN_LVGL}|AUCUN|4"
  "verif_campagne_dn440.py|CAUSE A — elle MUTE le ledger et le tracker du cockpit dans une COPIE jetable : sans ce depot PRIVE elle n'a rien a muter, et son compte « controles gardes par rien » ne veut plus rien dire puisque aucune gate ne tourne. ⚠️ dn4-44 : elle est entree au glob (decision owner du 2026-09-03) precisement parce que RIEN ne l'invoquait — une regle que rien n'applique est une regle qui pourrira.|${TEMOIN_COCKPIT}|AUCUN|4"
  "verif_banc_langue_dn73.py|CAUSE D — le moteur JavaScript node est un PREREQUIS DE BANC, ⛔ pas une dependance du depot : cette gate lance tools/banc_langue_dalle_dn73.mjs, qui EXECUTE le script de la page installeur/index.html contre un port de banc d'essai et rejoue les lignes de la matrice d'entrees-sorties de dn7-3 (⚠️ ce texte disait NEUF lignes : le banc en joue 39 sans base et 42 avec, releve du 2026-09-12 — le compte qui fait foi est CAS_ATTENDUS dans la gate, ⛔ jamais une phrase d'ici), plus les chemins que trois revues ont nommes. Sans moteur il n'y a rien a jouer, et une gate VERTE sur un banc qui n'a pas tourne serait PIRE que pas de gate. ⇒ elle rend 4 avec son motif, et la regle (3) la joue QUAND MEME pour verifier qu elle rend bien ce 4. 🔴 DEPUIS dn8-2 CETTE GATE A DEUX PREREQUIS, ET LE TEMOIN LES COUVRE DESORMAIS TOUS LES DEUX : elle lie le VRAI serveur du produit sur 127.0.0.1:0 pour que le banc lui parle par HTTP, et une boucle locale filtree lui fait rendre 4 AUSSI. ⚠️ LA LIGNE D'ORIGINE DISAIT ICI QUE LE TEMOIN NE COUVRAIT PAS CE SECOND PREREQUIS, et que ce cas sortirait en ROUGE rc=4 au lieu de NON-JOUABLE : c'etait VRAI le 2026-09-11 et c'est CORRIGE le 2026-09-12 — le temoin est DERIVE des deux (voir TEMOIN_BANC_HTTP plus haut), et un temoin reste un FICHIER.|${TEMOIN_BANC_HTTP}|AUCUN|4"
  "verif_harnais_dn81.py|CAUSE A — le cockpit de planification est un depot PRIVE, ⛔ jamais clone a cote du code. Les 94 CIBLES d'ancre 📍 que (c2) rejoue, portees par 86 lignes, vivent dans son ledger (⚠️ 87 lignes portent le glyphe ; la 87e est de la PROSE qui le cite entre accents graves, et ancres_du l'ecarte — le « 87 » ecrit ici d'abord comptait des LIGNES pour des CIBLES) : sans lui, (c2) n'a AUCUNE population. ⚠️ (c1) et (c3), eux, sont JOUABLES dans un clone nu — mais la gate ⛔ ne se coupe PAS en deux : un verdict partiel publie sous la meme ligne de BILAN serait indiscernable d'un verdict complet, et c'est le defaut que dn8-1 existe pour fermer. ⇒ elle rend 4 EN AMONT, et le dit. ⛔ CE N'EST PAS UN SKIP : la regle (3) la joue QUAND MEME pour verifier qu'elle rend bien ce 4.|${TEMOIN_COCKPIT}|AUCUN|4"
  "verif_lhm_ps_dn83.py|CAUSE E — il n'existe AUCUN hote PowerShell sur un runner Linux, et cette gate EXECUTE le pre-vol de tools/dn_agent_tour.ps1 dans un vrai powershell.exe pour eprouver la sonde LHM dans les TROIS sens, et depuis dn4-48 (2026-09-12) le pre-vol ⛔ NE REFUSE PLUS : il ATTEND LHM puis DEMARRE QUAND MEME. ⇒ DEGRADE : ⛔ pas 12, bandeau qui NOMME LHM, et au moins un tour d'attente imprime · PASSANT : ⛔ pas 12, ligne passante, et ⛔ aucune attente sous -AttenteLhm 0 · RETARD : le stub monte APRES le pre-vol, qui ATTEND puis PASSE — le cas MESURE du 2026-09-12, rejoue. ⚠️ 12 reste le discriminant, mais comme INTERDIT : il a change d'emetteur pour le verbe poser. Sans hote, il n'y a rien a jouer, et une gate VERTE sur un banc qui n'a pas tourne serait PIRE que pas de gate. ⇒ elle rend 4 avec son motif, et la regle (3) la joue QUAND MEME pour verifier qu'elle rend bien ce 4. 🔴 LE TEMOIN ESSAIE PLUSIEURS NOMS, et c'est le fond de cette marche : which(powershell) rend None la ou which(powershell.exe) rend le chemin — le ledger a publie CINQ FOIS une IMPOSSIBILITE qui etait une propriete de sa METHODE de recherche. ⚠️ ELLE A TROIS PREREQUIS — l'hote, un bind accepte pour le stub, et un dossier temporaire VISIBLE DE WINDOWS — et TOUS LES TROIS rendent 4. Depuis la revue du 2026-09-12 le temoin derive de leur CONJONCTION, wslpath compris : la ligne d'origine disait qu'il ne couvrait que le premier, et ce cas sortait alors en ROUGE rc=4 au lieu de NON-JOUABLE.|${TEMOIN_POWERSHELL}|AUCUN|4"
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
ECARTS_COCKPIT=()          # dn5-6 / constat (4) — l'appariement des detections
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
  # ═══ dn5-6 / CONSTAT (4) — 2026-09-05 ═══════════════════════════════════
  # 🔴 LA DETECTION ETAIT UNE **CHAINE LITTERALE**, ET ELLE EST AVEUGLE A DEUX
  #    FORMES QUE PYTHON ACCEPTE : les GUILLEMETS SIMPLES et la declaration
  #    COUPEE. Une gate ecrite ainsi ne recevrait PAS `--cockpit` et
  #    **mesurerait son COCKPIT_DEFAUT EN SILENCE**.
  # 🔬 MESURE DU 2026-09-05 (`mesures/dn5-6/T1-filtre-10-constats.txt`) :
  #    · les **4** gates qui declarent `--cockpit` portent TOUTES la forme
  #      litterale ⇒ **le bord n'est PAS atteint**, ⛔ aucun rouge ne peut le
  #      montrer aujourd'hui ;
  #    · ⛔ **LE PRECEDENT QUE LA REVUE DE `dn5-3` CITAIT EST REFUTE** :
  #      `add_argument("--csv",` de `thermique_ventilos_dn48.py` replie ses
  #      ARGUMENTS SUIVANTS, ⛔ pas le nom de l'option — le grep LA VOIT ;
  #    · 🎯 **MAIS UN PRECEDENT REEL EXISTE AILLEURS** : `gen_living_pcb.py`
  #      declare `--out-bin`, `--out-png`, `--byte-order`, `--seed` en
  #      GUILLEMETS SIMPLES. La convention dangereuse vit bien dans l'arbre,
  #      ⛔ pas la ou on la designait.
  # ⇒ ON APPARIE : une detection LARGE (les deux quotes, sur une ou plusieurs
  #   lignes) et la detection ETROITE d'origine. **Toute divergence est
  #   SIGNALEE et rougit la passe** — c'est le seul moyen que le jour ou une
  #   gate sera ecrite autrement, quelqu'un le VOIE.
  # ⛔ CE N'EST PAS UN CONTROLE QUI SE TAIT : il tourne a CHAQUE passe, meme
  #   sans `--cockpit`, sinon il ne garderait rien la ou ca compte (la CI).
  # 🔴 REVUE DU 2026-09-05 — TROIS TROUS ETAIENT OUVERTS ICI :
  #    (i) tout `rc` autre que 0 ou 2 (python3 absent, tue par un signal) se
  #        lisait comme « ne declare PAS `--cockpit` » ⇒ ⛔ aucun rouge ;
  #    (ii) un fichier INDECIDABLE qui porte AUSSI la chaine litterale poussait
  #        DEUX entrees et gonflait le compte de divergences publie ;
  #    (iii) `ast.parse` sans `filename=` imprimait
  #        `<unknown>:185: SyntaxWarning …` — un avertissement ANONYME, sur
  #        chaque passe, qui ne nomme pas le fichier fautif.
  etroit=0; large=0
  grep -q -- 'add_argument("--cockpit"' "$g" && etroit=1
  python3 -c "$AST_COCKPIT" "$g"; _rc_ast=$?
  case "$_rc_ast" in
    0) large=1 ;;
    1) ;;
    2) ECARTS_COCKPIT+=("$g (⛔ INDECIDABLE : le fichier ne s'analyse pas — on ne conclut RIEN)") ;;
    *) ECARTS_COCKPIT+=("$g (⛔ rc AST INATTENDU=$_rc_ast — python3 absent ou tue ; ⛔ on ne conclut RIEN)") ;;
  esac
  # ⇒ UNE SEULE entree par gate : l'indecidable a deja parle, on n'y ajoute pas
  #   une divergence calculee sur une detection qui n'a rien pu decider.
  if [ "$_rc_ast" -eq 0 ] || [ "$_rc_ast" -eq 1 ]; then
    if [ "$etroit" -ne "$large" ]; then
      ECARTS_COCKPIT+=("$g (declaration vue par la detection LARGE=$large, ETROITE=$etroit)")
    fi
  fi
  if [ "$declaree" -eq 0 ] && [ -n "$COCKPIT" ] && [ "$large" -eq 1 ]; then
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
# 🔴 dn5-6 / CONSTAT (4) — L'APPARIEMENT SE DIT, MEME QUAND IL EST BON.
#    Un controle muet quand tout va bien ne se distingue pas d'un controle
#    mort : on imprime le compte APPARIE, ⛔ pas seulement l'ecart.
echo "appariement --cockpit : ${#ECARTS_COCKPIT[@]} divergence(s) entre la detection LARGE (quotes simples/doubles, declaration coupee) et la detection ETROITE d'origine"
if [ "${#ECARTS_COCKPIT[@]}" -ne 0 ]; then
  echo "⛔ DIVERGENCE(S) DE DECLARATION --cockpit — une gate peut mesurer un AUTRE depot EN SILENCE :"
  for e in "${ECARTS_COCKPIT[@]}"; do echo "   · $e"; done
fi
if [ "$N_ROUGE" -ne 0 ]; then
  echo "⛔ ROUGES :"
  for r in "${ROUGES[@]}"; do echo "   · $r"; done
fi

if [ "$N_ROUGE" -ne 0 ] || [ "$PERIMEES" -ne 0 ] || [ "${#ECARTS_COCKPIT[@]}" -ne 0 ]; then
  exit 1
fi
exit 0
