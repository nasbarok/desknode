#requires -Version 5.1
<#
=============================================================================
  dn_agent_tour.ps1 - pilote l'agent DeskNode SUR LA TOUR          (dn4-17)
=============================================================================

  POURQUOI. Le module DeskNode vit desormais en permanence sur le bureau.
  L'owner veut lancer / arreter l'agent DEPUIS WINDOWS, en double-cliquant
  `dn-agent.bat`, WSL POUVANT ETRE ETEINT - et reprendre la carte quand il
  veut flasher. Ce script porte la logique ; le .bat n'est qu'un lanceur.

  !!! L'AUTORITE EST LE DEPOT (~/projects/desknode), PAS CETTE COPIE.
      Ce fichier est depose par `tools/deployer_tour.sh`. Ne PAS l'editer
      ici : le prochain deploiement l'ecrase et l'ecart ne se verrait nulle
      part. Voir PROVENANCE.txt.

  EMPLOI (via dn-agent.bat, qui passe le verbe en 1er argument)
      dn-agent.bat            = start        lance l'agent s'il ne tourne pas
      dn-agent.bat etat                      ne change RIEN, dit tout
      dn-agent.bat stop                      arrete l'agent et LE PROUVE
      dn-agent.bat run                       lance EN AVANT-PLAN (la tache)
      dn-agent.bat permanence                pose la tache au logon
      dn-agent.bat retirer                   retire la tache

  LE PORT DE LHM (dn8-3)
      dn-agent.bat run COM3 0 "" 127.0.0.1:8086
      .\dn_agent_tour.ps1 prevol -Lhm 127.0.0.1:8086
      => l'adresse traverse dn-agent.bat -> ce script -> DN_ARGS -> l'agent
         (--lhm HOTE:PORT). Sans -Lhm, elle reste LUE dans dn_agent.py.
      /!\ La 4e place (le temoin) doit etre OCCUPEE : `""` si pas de temoin.

  L'ATTENTE DE LHM AU LOGON (dn4-48)
      dn-agent.bat run COM3 0 "" "" 300
      .\dn_agent_tour.ps1 prevol -AttenteLhm 300
      => le pre-vol ATTEND LHM, borne a -AttenteLhm SECONDES (defaut 300),
         au lieu de refuser aussitot. Si LHM n'arrive pas dans la borne, le
         pre-vol CONTINUE et l'agent DEMARRE QUAND MEME : champs LHM a " -- ".
      /!\ `0` = aucune attente. Une valeur NEGATIVE est REFUSEE (exit 3),
          !!! jamais repliee en silence sur le defaut.
      /!\ LA 5e PLACE (l'adresse LHM) DOIT ETRE OCCUPEE ELLE AUSSI : `""`
          si vous n'en voulez pas, sinon cmd.exe lit la borne en %5.

=============================================================================
  L'INSTRUMENT EST LE COMPTE **ET** L'ETAT DU PORT.        (dn4-17 / AC3.4)
=============================================================================
  Un `Win32_Process` peut rendre une **CommandLine VIDE** : MESURE le
  2026-08-26 sur ce poste (usbipd.exe PID 6056 - ProcessId lisible,
  CommandLine vide). Un filtre `-like '*dn_agent*'` classe alors le process
  "pas l'agent", EN SILENCE. Le meme faux negatif existe deja dans
  `wsl-attach.sh:75-81` pour la chasse aux veilleurs.
  => On compte TROIS choses, et on les imprime TOUTES :
       1. les python.exe DONT la CommandLine porte dn_agent.py  (confirmes)
       2. les python.exe dont la CommandLine est ILLISIBLE      (muets)
       3. l'etat de COM3 : absent / libre / tenu                (le verdict)
  Le marqueur de lancement (`dn-agent.started`) dit ce que le lanceur CROIT.
  !!! Il ne remplace aucun des trois : le compte et le port disent ce qui EST.

=============================================================================
  ET UN PROCESS QU'ON CROIT MORT PEUT TENIR COM3.            (piege P2)
=============================================================================
  Sur ce poste : Edge headless a laisse 416 process / 11,6 Go survivre a la
  mort de son lanceur, et un python detache a vecu 29 min apres la fin du
  sien. => `stop` ne rend JAMAIS un code de retour comme preuve : il
  RE-OUVRE COM3, et c'est l'ouverture qui fait foi.
=============================================================================
#>
[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet('etat', 'prevol', 'lancer', 'tache', 'stop', 'permanence', 'poser', 'retirer')]
    [string]$Action = 'etat',

    [string]$Serie = 'COM3',
    [int]$Duree = 0,
    [switch]$Temoin,
    [string]$Python = '',

    # !!! dn8-3 - LE PORT DE LHM EST UNE CONFIGURATION **SUPPORTEE**, ET
    #     NI CE SCRIPT NI dn-agent.bat NE SAVAIENT LA PASSER A L'AGENT.
    #     Le trou etait MESURE : `--lhm` existe dans agent/dn_agent.py
    #     (l.3506, durci sur quatre refus) et comptait **ZERO**
    #     occurrence dans les deux outils. Le produit l'ecrivait
    #     lui-meme, dans le message du refus dur : " une configuration
    #     SUPPORTEE que NI ce script NI dn-agent.bat ne savent encore
    #     passer a l'agent ".
    #     /!\ [string] NU, SANS [ValidateSet] : ce fichier n'en porte
    #     qu'UN (celui du verbe), et une gate REFUSE le second - un
    #     ensemble ambigu n'est pas un ensemble.
    [string]$Lhm = '',

    # !!! dn4-48 - LHM QUI MONTE APRES LE LOGON N'EST PLUS UN REFUS, IL EST
    #     UNE **ATTENTE BORNEE**. Le defaut est MESURE (2026-09-12) : la tache
    #     a tire a 18:13:13 et rendu 12 pendant que LHM montait a 18:13:34 -
    #     21 s trop tard -, et la reprise du Planificateur N'A PAS TIRE.
    #     => ce pre-vol ATTEND, et s'il n'a rien vu au bout de la borne il
    #        CONTINUE : l'agent demarre, champs LHM a " -- ". Le produit sait
    #        deja faire ca (agent/dn_agent.py : AUCUNE grandeur LHM en
    #        position 0), et il le faisait DEJA quand LHM meurt en route.
    #     /!\ [int] NU, SANS [ValidateSet] : ce fichier n'en porte qu'UN
    #     (celui du verbe), et une gate REFUSE le second - un ensemble
    #     ambigu n'est pas un ensemble. La borne se VALIDE plus bas.
    [int]$AttenteLhm = 300
)

$ErrorActionPreference = 'Continue'

$RACINE  = Split-Path -Parent $MyInvocation.MyCommand.Path
$AGENT   = Join-Path $RACINE 'dn_agent.py'
$BAT     = Join-Path $RACINE 'dn-agent.bat'
$LOG     = Join-Path $RACINE 'dn-agent.log'
$SORTIE  = Join-Path $RACINE 'dn-agent.out'
$MARQUE  = Join-Path $RACINE 'dn-agent.started'
$DRAPEAU = Join-Path $RACINE 'dn-agent.stop'
$ENVCMD  = Join-Path $RACINE 'dn-agent.env.cmd'
$NOM_TACHE = 'DeskNode agent'
$USBIPD  = 'C:\Program Files\usbipd-win\usbipd.exe'

# !!! ROTATION DU JOURNAL - DECISION ECRITE, PAS SUBIE.          (AC3.6)
#     Un agent permanent ecrit 24 h/24 : un fichier qui grossit sans fin est
#     une panne differee. Le debit REEL est mesure et publie dans
#     hardware/ESP32-S3-Touch-LCD-2.8B-liaison-pc.md (dn4-17).
#     Politique : a CHAQUE pre-vol, si le journal depasse $LOG_MAX octets il
#     est bascule en `.1` (UNE seule generation, l'ancienne est ecrasee).
# !!! CORRIGE LE 2026-08-26 (revue) - LE PLAFOND ANNONCE ETAIT FAUX D'UN
#     FACTEUR 2, ET IL ETAIT PUBLIE QUATRE FOIS (ici, ?25.9 du dossier,
#     PROVENANCE.txt et le ledger). La rotation porte sur DEUX fichiers
#     ($LOG **et** $SORTIE), chacun avec UNE generation `.1` :
#         plafond = 2 fichiers x 2 generations x $LOG_MAX = 4 x $LOG_MAX = 20 Mo.
#     /!\ $SORTIE reste a 0 o dans le regime livre (`--serie COM3`) : le
#     plafond n'est atteignable qu'en `--stdout`, ou le debit n'a PAS ete
#     mesure. C'est dit, pas masque.
#     La rotation a lieu AU LANCEMENT, donc un run tres long peut depasser le
#     plafond : c'est ASSUME, et le debit mesure dit de combien.
$LOG_MAX = 5MB

# !!! LE PAS DE L'ATTENTE DE LHM - ET L'ATTENTE N'EST JAMAIS UN GEL MUET.
#     Chaque tour IMPRIME une ligne (ecoule / borne), pour que le double-clic
#     ET le journal de la tache disent tous deux ce qui se passe. Une fenetre
#     qui ne bouge pas pendant cinq minutes est indiscernable d'un blocage :
#     c'est exactement le constat owner qui a fait ecrire le `pause` du .bat.
$LHM_PAS = 5
# !!! ET LE PAS S'ADAPTE A LA BORNE : **AU MOINS DIX TOURS**, quelle que soit
#     elle. Une borne de 6 s sondee DEUX fois n'est pas une attente, c'est un
#     tirage au sort - et c'est pourtant ce que donnerait un pas FIXE de 5 s.
#     Le pas ne depasse donc jamais le dixieme de la borne, ni $LHM_PAS, et il
#     ne descend jamais sous la seconde.
#       borne 300 s => pas 5 s  (60 tours, le regime livre)
#       borne  60 s => pas 5 s  (12 tours)
#       borne   6 s => pas 1 s  ( 6 tours)
#     (!) C'est AUSSI ce qui rend le banc de `tools/verif_lhm_ps_dn83.py`
#         payable : il rejoue le pre-vol a chaque mutant, et un pas fixe de
#         5 s lui coutait un multiple de ce que la campagne peut depenser.
function Pas-Attente ([int]$Borne) {
    $p = [Math]::Min($LHM_PAS, [int]($Borne / 10))
    if ($p -lt 1) { return 1 }
    return $p
}

function Dire   ([string]$m) { Write-Host "  $m" }
function Titre  ([string]$m) { Write-Host ""; Write-Host "=== $m ===" }
function Alerte ([string]$m) { Write-Host "  /!\ $m" -ForegroundColor Yellow }
function Stop2  ([string]$m) { Write-Host "  /!\ $m" -ForegroundColor Red }

# --------------------------------------------------------------------------
# -Lhm : UNE VALEUR MALFORMEE EST **REFUSEE**, !!! JAMAIS REPLIEE EN SILENCE.
# --------------------------------------------------------------------------
# !!! LE REPLI SILENCIEUX EST LE DEFAUT QUE agent/dn_agent.py A DEJA PAYE
#     QUATRE FOIS (revues des 2026-08-21 et 2026-08-24) : `--lhm "hote:"`,
#     `--lhm "[::1]xyz:9000"`, un port non entier et un hote vide rendaient
#     tous LE PORT PAR DEFAUT, en silence - l'operateur croyait avoir pose
#     une adresse, et le diagnostic accusait ensuite LHM.
#     => ICI AUSSI on REFUSE, et on dit la forme attendue.
# !!! ON NE RECOPIE AUCUNE VALEUR PAR DEFAUT : quand -Lhm est absent,
#     l'adresse reste celle que le bloc LHM **LIT DANS L'AGENT**. Figer un
#     defaut ici ferait DEUX sources de verite, et la seconde pourrirait en
#     silence - c'est le patron ecrit dans tools\dn_lhm_tour.ps1.
# !!! L'IPv6 NU EST REFUSE, COMME DANS L'AGENT : `::1` se decouperait en
#     hote `:` et port `1`, une adresse acceptee EN SILENCE sous une autre.
$LhmHoteForce = $null
$LhmPortForce = $null
# !!! $LhmSonde : la sonde a-t-elle REELLEMENT vise cette adresse ? Sans lui,
#     l'outil passerait --lhm a l'agent APRES avoir saute la sonde.
$LhmSonde = $false
if ($Lhm) {
    # !!! DEUX FORMES, COMME agent/dn_agent.py : [HOTE]:PORT (RFC 3986, la
    #     seule forme NON AMBIGUE pour IPv6) et HOTE:PORT. Le wrapper ne doit
    #     pas etre PLUS ETROIT que la grammaire qu'il alimente : l'agent a une
    #     branche dediee aux crochets, et la refuser ici rendait injouable une
    #     adresse que l'agent ACCEPTE.
    # !!! L'IPv6 NU RESTE REFUSE : `::1` se decouperait en hote `:` port `1`.
    $m = [regex]::Match($Lhm, '^(?:\[([^\]\s]+)\]|([^:\s\[\]]+)):([0-9]+)$')
    if (-not $m.Success) {
        Stop2 ("-Lhm invalide : '" + $Lhm + "'. Attendu : HOTE:PORT (ex. 127.0.0.1:8086).")
        Stop2 "  !!! Une adresse malformee n'est PAS repliee sur le defaut : ce"
        Stop2 "      repli silencieux ferait sonder une AUTRE adresse que celle"
        Stop2 "      demandee, et le diagnostic accuserait LHM. Rien n'est lance."
        Stop2 "  (!) IPv6 nu refuse : ':' sans port et hote vide le sont aussi."
        exit 3
    }
    $portTxt = $m.Groups[3].Value
    # !!! BORNER **AVANT** DE CASTER. MESURE : `-Lhm 127.0.0.1:99999999999`
    #     faisait lever [int] par .NET (Impossible de convertir la valeur)
    #     PUIS imprimait " port  hors de 1..65535 " avec un port VIDE : le
    #     diagnostic ne nommait plus la valeur fautive. On teste la LONGUEUR
    #     d'abord (-or court-circuite), donc aucun cast ne deborde.
    if ($portTxt.Length -gt 5 -or [int64]$portTxt -lt 1 -or [int64]$portTxt -gt 65535) {
        Stop2 ("-Lhm : port " + $portTxt + " hors de 1..65535.")
        exit 3
    }
    $LhmHoteForce = $(if ($m.Groups[1].Success) { $m.Groups[1].Value }
                      else { $m.Groups[2].Value })
    $LhmPortForce = [int]$portTxt
}

# --------------------------------------------------------------------------
# -AttenteLhm : UNE BORNE NEGATIVE EST **REFUSEE NOMMEMENT**.       (dn4-48)
# --------------------------------------------------------------------------
# !!! MEME REGLE QUE -Lhm QUINZE LIGNES PLUS HAUT, ET POUR LE MEME MOTIF : un
#     repli silencieux sur le defaut ferait ATTENDRE 300 s a quelqu'un qui a
#     demande AUTRE CHOSE, et le diagnostic accuserait ensuite LHM. `0` est
#     une valeur LEGITIME (aucune attente) ; le negatif, lui, ne veut RIEN
#     dire et il est dit plutot que devine.
if ($AttenteLhm -lt 0) {
    Stop2 ("-AttenteLhm invalide : " + $AttenteLhm + ". Attendu : un nombre de")
    Stop2 "  SECONDES >= 0 (0 = AUCUNE attente ; le defaut est 300)."
    Stop2 "  !!! Une borne negative n'est PAS repliee sur le defaut : ce repli"
    Stop2 "      silencieux ferait attendre une duree que personne n'a demandee."
    exit 3
}

# !!! L'ETAT DE LHM VOYAGE PAR L'ETAT ECRIT, !!! JAMAIS PAR LE CODE DE SORTIE
#     DU PRE-VOL. Motif ecrit en entier au bloc LHM, plus bas : `dn-agent.bat`
#     fait `if errorlevel 1 goto :FIN` en `:RUN`, donc tout code non nul
#     AVORTERAIT le lancement que cette marche existe pour permettre.
# !!! LA VALEUR PAR DEFAUT EST CELLE DE L'IGNORANCE : tant que le bloc LHM
#     n'a pas tourne, on ne sait RIEN - et une ignorance n'est pas un ecart.
# !!! CE DRAPEAU EST **LU**, ET IL EST LA SEULE SOURCE DU JETON QUE `etat` ET
#     `poser` CHERCHENT DANS dn-agent.started. Un drapeau ecrit et jamais relu
#     serait un commentaire deguise en code : celui-ci COMMANDE la ligne `lhm`
#     du marqueur, donc les deux verbes qui en dependent.
$LhmDegrade = $false
$LhmEtatMarque = 'non sonde (le pre-vol n''a pas atteint le bloc LHM)'
# Le jeton, ecrit UNE fois. Les trois lecteurs (le marqueur, `etat`, `poser`)
# le partagent : une chaine recopiee a trois endroits pourrirait en silence.
$MARQUE_DEGRADE = 'DEMARRAGE DEGRADE'

# --------------------------------------------------------------------------
# Python : celui de la TOUR, jamais un stub, jamais le relais du Store.
# --------------------------------------------------------------------------
function Trouver-Python {
    $cands = @()
    if ($Python)        { $cands += $Python }
    if ($env:DN_PYTHON) { $cands += $env:DN_PYTHON }
    $cands += (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python313\python.exe')
    $base = Join-Path $env:LOCALAPPDATA 'Programs\Python'
    if (Test-Path $base) {
        Get-ChildItem $base -Directory -ErrorAction SilentlyContinue |
            Sort-Object Name -Descending | ForEach-Object {
                $cands += (Join-Path $_.FullName 'python.exe')
            }
    }
    $w = (& where.exe python.exe 2>$null)
    if ($w) { $cands += @($w) }
    foreach ($c in $cands) {
        if (-not $c) { continue }
        # Le relais du Microsoft Store est un STUB de 0 octet qui ouvre une
        # page web au lieu de lancer Python. Il ne doit jamais etre retenu.
        if ($c -like '*WindowsApps*') { continue }
        if (Test-Path $c) { return (Resolve-Path $c).Path }
    }
    return $null
}

# --------------------------------------------------------------------------
# Les trois temoins.
# --------------------------------------------------------------------------
function Get-Instances {
    # !!! REVUE DU 2026-08-26 - DEUX DEFAUTS CORRIGES ICI.
    #  (1) LE FILTRE NE VOYAIT QUE `python.exe`. Un agent lance par
    #      `pythonw.exe` ou `py.exe` etait invisible POUR LA GARDE ANTI-DOUBLON
    #      **ET** POUR `stop` - or `etat`/`stop` sont l'instrument de l'owner
    #      pour savoir si quelque chose tient la carte.
    #  (2) `-match 'dn_agent\.py'` N'ETAIT PAS ANCRE : il matchait n'importe
    #      quelle ligne de commande CONTENANT ce texte (un serveur de langage,
    #      un `python -c`, un outil voisin). Consequences mesurees : `prevol`
    #      sortait en 4 (" DEJA LANCE "), `lancer` mappe 4 -> 0, donc le
    #      double-clic ANNONCAIT UN SUCCES SANS QU'AUCUN AGENT NE DEMARRE ; et
    #      `stop` posait le drapeau puis faisait `taskkill /F` SUR UN PROCESS
    #      PYTHON ETRANGER.
    # => On ancre sur LE CHEMIN DE **CET** AGENT. Ce qui porte `dn_agent.py`
    #    mais vient d'AILLEURS est compte a part et NOMME, jamais tue : `stop`
    #    signale par un drapeau LOCAL a $RACINE, il n'a aucun moyen de
    #    demander proprement l'arret d'un agent d'un autre deploiement.
    $tous = @(Get-CimInstance Win32_Process `
                -Filter "Name='python.exe' OR Name='pythonw.exe' OR Name='py.exe'" `
                -ErrorAction SilentlyContinue)
    $motif = [regex]::Escape($AGENT)
    [pscustomobject]@{
        Tous      = $tous
        Confirmes = @($tous | Where-Object { $_.CommandLine -and ($_.CommandLine -match $motif) })
        Etrangers = @($tous | Where-Object { $_.CommandLine -and ($_.CommandLine -notmatch $motif) -and ($_.CommandLine -match 'dn_agent\.py') })
        Muets     = @($tous | Where-Object { -not $_.CommandLine })
    }
}

function Get-EtatPort ([string]$Port) {
    $noms = @([System.IO.Ports.SerialPort]::GetPortNames())
    if ($noms -notcontains $Port) { return 'absent' }
    $sp = New-Object System.IO.Ports.SerialPort $Port, 115200
    # (!) DTR/RTS a FALSE **AVANT** open() : sous Windows pyserial les pose a
    #     l'ouverture et la sequence RESET la puce (mesure dn2-2, trois
    #     sessions perdues avant le diagnostic). L'agent porte la meme parade
    #     en dn_agent.py:1904-1906. Une sonde d'etat ne doit pas rebooter la
    #     carte pour dire si le port est libre.
    $sp.DtrEnable = $false
    $sp.RtsEnable = $false
    # !!! REVUE DU 2026-08-26 - `catch { 'tenu' }` REPLIAIT **TOUT** ECHEC SUR
    #     UN SEUL ETAT, Y COMPRIS LE `COM3` FANTOME QUE CE DEPOT DOCUMENTE :
    #     le port est ENUMERE mais `Open()` leve `FileNotFoundException` parce
    #     qu'un veilleur `--auto-attach` a rendu la carte a WSL. Il n'y a alors
    #     AUCUN process qui le tient - et trois sites imprimaient pourtant la
    #     mauvaise cause : `prevol` exit 6 (" TENU par un process "),
    #     `--vers-flash` exit 5 (" l'agent ne l'a pas rendu "), `stop` exit 8
    #     (" un process qu'on croit mort le tient "). Le type d'exception etait
    #     disponible aux trois, et jete.
    try   { $sp.Open(); $sp.Close(); return 'libre' }
    catch [System.IO.FileNotFoundException] { return 'fantome' }
    catch [System.UnauthorizedAccessException] { return 'tenu' }
    catch { return 'inconnu' }
    finally { $sp.Dispose() }
}

function Get-LigneUsbipd {
    if (-not (Test-Path $USBIPD)) { return '(usbipd-win absent)' }
    $l = @(& $USBIPD list 2>&1 | Where-Object { $_ -match '303a:1001' })
    if ($l.Count -eq 0) { return '(carte 303a:1001 ABSENTE du bus)' }
    return (($l | ForEach-Object { ($_ -replace '\s+', ' ').Trim() }) -join ' | ')
}

function Ecrire-Etat ([string]$Port) {
    $i = Get-Instances
    $p = Get-EtatPort $Port
    Dire ("python.exe vivants : " + $i.Tous.Count +
          "  (portant dn_agent.py : " + $i.Confirmes.Count +
          " | CommandLine ILLISIBLE : " + $i.Muets.Count + ")")
    foreach ($c in $i.Confirmes) { Dire ("  agent  PID=" + $c.ProcessId + "  " + $c.CommandLine) }
    foreach ($m in $i.Muets)     { Alerte ("python.exe PID=" + $m.ProcessId + " : CommandLine ILLISIBLE - ne peut PAS etre exclu") }
    Dire ("port " + $Port + " : " + $p)
    Dire ("usbipd : " + (Get-LigneUsbipd))
    if (Test-Path $MARQUE) { Dire ("marqueur : " + ((Get-Content $MARQUE -Raw) -replace '\r?\n', ' ')) }
    else                   { Dire  "marqueur : absent" }
    Dire ("journal : " + $(if (Test-Path $LOG) { "" + (Get-Item $LOG).Length + " o  " + $LOG } else { "absent" }))
    # !!! dn4-48 - UN AGENT QUI TOURNE **SANS** LHM SE DIT ICI, ET PAS
    #     SEULEMENT AU PRE-VOL. Le bandeau du pre-vol passe une fois, dans une
    #     fenetre que la tache au logon n'ouvre meme pas ; `etat` est
    #     l'instrument que l'owner rejoue QUAND IL VEUT. Sans cette lecture,
    #     " la temperature du CPU reste a -- " n'aurait aucune surface
    #     interrogeable, et le diagnostic accuserait la carte.
    #     (!) LA SOURCE EST LE MARQUEUR ECRIT PAR LE PRE-VOL, !!! pas une
    #         seconde sonde : re-sonder ici dirait l'etat de MAINTENANT, et la
    #         question posee est " avec quoi cet agent-la a-t-il demarre ? ".
    if ((Test-Path $MARQUE) -and
        (((Get-Content $MARQUE -Raw) -replace '\r?\n', ' ') -match $MARQUE_DEGRADE)) {
        if ($i.Confirmes.Count -gt 0) {
            Alerte "CET AGENT TOURNE **SANS** LibreHardwareMonitor (demarrage degrade)."
        } else {
            Alerte "LE DERNIER LANCEMENT S'EST FAIT SANS LibreHardwareMonitor."
        }
        Alerte "  La temperature du CPU et les trois vitesses de ventilateur restent"
        Alerte "  a ' -- ' ; TOUT LE RESTE est publie. !!! Ce n'est PAS une panne de"
        Alerte "  l'agent, et ce n'est PAS la carte : LHM n'a pas repondu au pre-vol."
        Alerte "  => LE GESTE : .\tools\dn_lhm_tour.ps1 -Poser -Permanence tache"
        Alerte "     puis 'dn-agent.bat stop' et 'dn-agent.bat start' pour les"
        Alerte "     recuperer SANS attendre la prochaine ouverture de session."
    }
    return [pscustomobject]@{ Inst = $i; Port = $p }
}

# --------------------------------------------------------------------------
# LA SURFACE WINDOWS DU DEMARRAGE DEGRADE - msg.exe, ET RIEN D'AUTRE. (dn4-48)
# --------------------------------------------------------------------------
# !!! D8 DIT QUE L'AGENT N'A " NI ELEVATION, NI DRIVER, NI .NET ", et c'est LA
#     MOITIE DE PHRASE QUI FAIT ENTRER LHM DANS LE PERIMETRE V1. Toute surface
#     ajoutee ici s'y conforme, donc DEUX candidats tombent d'eux-memes :
#       . NotifyIcon exige System.Windows.Forms, c'est-a-dire .NET ;
#       . un toast WinRT exige .NET, ou un module tiers (BurntToast), donc une
#         DEPENDANCE NEUVE - et ce fichier n'en prend aucune.
#     msg.exe, lui, vit dans System32, n'exige NI l'un NI l'autre pour la
#     session courante, et il est l'un des trois que l'arbitrage owner nomme.
# !!! SON DEFAUT EST CONNU, ET IL SE **DECLARE** : msg.exe est ABSENT des
#     editions Familiales de Windows. On ne laisse alors PAS croire qu'on a
#     prevenu - on DIT qu'aucune surface n'etait disponible, et le motif reste
#     au bandeau, dans dn-agent.started et dans 'dn-agent.bat etat'.
#     (!) UNE IGNORANCE N'EST PAS UN ECART : le code de retour ne bouge PAS.
# !!! C'EST LE **MECANISME** QUI EST ARBITRE ICI, PAS LA PROPRIETE. La
#     propriete - " l'humain apprend le POURQUOI sans le demander " - survit a
#     un autre mecanisme si l'owner en prefere un.
function Prevenir-Windows ([string]$Texte) {
    $racineWin = $(if ($env:SystemRoot) { $env:SystemRoot } else { 'C:\Windows' })
    $msg = Join-Path $racineWin 'System32\msg.exe'
    if (-not (Test-Path $msg)) {
        Alerte "AUCUNE SURFACE DE NOTIFICATION : msg.exe est ABSENT de cette"
        Alerte ("  edition de Windows (" + $msg + ").")
        Alerte "  !!! Le POURQUOI ci-dessus n'a donc atteint PERSONNE hors de cette"
        Alerte "      console. Il reste ECRIT dans dn-agent.started, et"
        Alerte "      'dn-agent.bat etat' le redit a la demande."
        return $false
    }
    # (!) LA CIBLE EST L'UTILISATEUR COURANT, PAS `*` : `msg *` vise TOUTES les
    #     sessions de la machine et demande des droits que cet agent n'a pas.
    $cible = $(if ($env:USERNAME) { $env:USERNAME } else { 'console' })
    & $msg $cible '/TIME:120' $Texte 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Alerte ("msg.exe a rendu " + $LASTEXITCODE + " : la notification n'a PAS")
        Alerte "  ete remise. Le motif reste au bandeau ci-dessus, dans"
        Alerte "  dn-agent.started et dans 'dn-agent.bat etat'."
        return $false
    }
    Dire "le POURQUOI a ete pousse a la session Windows (msg.exe)."
    return $true
}

function Rotation-Journal {
    foreach ($f in @($LOG, $SORTIE)) {
        if ((Test-Path $f) -and ((Get-Item $f).Length -ge $LOG_MAX)) {
            # !!! REVUE DU 2026-08-26 - L'ECHEC DE `Move-Item` ETAIT MUET.
            #     Avec $ErrorActionPreference = 'Continue', un journal encore
            #     tenu en ecriture par un agent survivant faisait ECHOUER le
            #     renommage SANS QUE RIEN NE LE DISE : le fichier continuait de
            #     grossir et la politique de plafond cessait de tenir, en
            #     silence. Une politique qu'on ne sait pas appliquer doit CRIER.
            try {
                Move-Item -Force -ErrorAction Stop $f ($f + '.1')
                Dire ("journal bascule (>= " + [int]($LOG_MAX / 1MB) + " Mo) : " + (Split-Path -Leaf $f) + ".1")
            } catch {
                Alerte ("ROTATION IMPOSSIBLE sur " + (Split-Path -Leaf $f) + " : " + $_.Exception.Message)
                Alerte "  => le journal VA CONTINUER DE GROSSIR. Un process le tient-il encore ?"
                Alerte "     'dn-agent.bat etat' pour voir les CommandLine illisibles."
            }
        }
    }
}

# ==========================================================================
switch ($Action) {

# --------------------------------------------------------------------------
'etat' {
    Titre 'ETAT (ne change RIEN)'
    Ecrire-Etat $Serie | Out-Null
    # !!! REVUE DU 2026-08-26 - `etat` NE DISAIT JAMAIS SI LA TACHE AU LOGON
    #     EXISTE. C'est pourtant la SEULE piece d'etat PERSISTANTE que cette
    #     story livre (AC5), et le seul moyen de la lire etait `permanence`...
    #     qui la RE-POSE. Un instrument documente " dit tout, ne change RIEN "
    #     doit dire la tache, sinon l'owner n'a aucun moyen NON DESTRUCTIF de
    #     savoir si son agent redemarrera au prochain logon.
    $t = Get-ScheduledTask -TaskName $NOM_TACHE -ErrorAction SilentlyContinue
    if ($t) {
        $info = $t | Get-ScheduledTaskInfo
        Dire ("tache au logon : POSEE | RunLevel=" + $t.Principal.RunLevel +
              " | etat=" + $t.State + " | dernier tir=" + $info.LastRunTime)
        Dire ("  action : " + ($t.Actions | Select-Object -First 1).Execute + " " +
              ($t.Actions | Select-Object -First 1).Arguments)
        if (("" + ($t.Actions | Select-Object -First 1).Arguments) -notmatch '-Temoin') {
            Alerte "la tache est posee SANS -Temoin : l'agent qu'elle lance n'aura PAS"
            Alerte "  l'instrument de cout. La re-verification 'gratuite au prochain"
            Alerte "  logon' du dossier (?25.15) n'aura donc PAS LIEU."
        }
    } else {
        Dire "tache au logon : ABSENTE (l'agent ne redemarrera pas seul)."
    }
    exit 0
}

# --------------------------------------------------------------------------
# PRE-VOL : tout ce qui doit etre VRAI avant de lancer python. Il n'ecrit
# aucun process : c'est le .bat qui lance, pour que le pere de python.exe
# soit le MEME cmd.exe dans les deux regimes (double-clic ET tache) - c'est
# ce qui rend la chaine de PID d'AC6.6 lisible.
'prevol' {
    Titre 'PRE-VOL'
    # !!! REVUE DU 2026-08-26 - LA SUPPRESSION DE $ENVCMD ETAIT LA **PREMIERE**
    #     INSTRUCTION, DONC AVANT LES EXIT 3/4/5/6. Un pre-vol qui ECHOUE
    #     detruisait le registre de lancement de l'agent **QUI TOURNE**.
    #     Signature VERIFIEE en vrai ce jour-la : `dn-agent.started` disait
    #     " lance : 10:17:30 ", l'agent tournait encore, et `dn-agent.env.cmd`
    #     n'existait plus - le verbe documente `dn-agent.bat exec` tombait donc
    #     dans `:SANSENV`. => ON NE DETRUIT QU'AU MOMENT DE RE-ECRIRE, plus bas.

    if (-not (Test-Path $AGENT)) {
        Stop2 ("dn_agent.py ABSENT a cote du .bat : " + $AGENT)
        Stop2 "  => redeployer depuis le depot : tools/deployer_tour.sh"
        exit 3
    }
    $py = Trouver-Python
    if (-not $py) {
        Stop2 "Aucun python.exe utilisable trouve sur la tour."
        Stop2 "  => poser DN_PYTHON=<chemin> ou passer -Python <chemin>"
        exit 3
    }
    Dire ("python : " + $py)
    & $py -c "import psutil, serial" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Stop2 "Ce python n'a pas psutil et/ou pyserial."
        Stop2 ("  => " + $py + " -m pip install psutil pyserial")
        exit 3
    }

    # --- LHM : LE PREREQUIS DUR ------------------------------- (dn7-5)
    # !!! ARBITRAGE OWNER DU 2026-09-10, VERBATIM : " LHM est-il un prerequis
    #     DUR !!! car sinon la dalle sert a rien ". => CE PRE-VOL REFUSE.
    #     L'option " confort declare " est ECARTEE.
    #
    # !!! ~~CE PRE-VOL REFUSE~~ - AMENDE LE 2026-09-12 (dn4-48), SUR UNE
    #     MESURE, ET L'ANCIENNE REDACTION EST BARREE PLUTOT QU'EFFACEE : elle
    #     etait EXACTE le 2026-09-10, et l'effacer effacerait ce que ce
    #     fichier savait ce jour-la.
    #     CE QUI A CHANGE, ET C'EST UN FAIT, PAS UN AVIS : au redemarrage du
    #     2026-09-12 la tache au logon a tire a 18:13:13 et rendu 12 pendant
    #     que le process LHM montait a 18:13:34 - !!! 21 s trop tard -, et la
    #     parade `RestartCount 3 / RestartInterval PT1M` N'A PAS TIRE
    #     (LastRunTime FIGE a 18:13:13, releve a 18:25). La dalle est restee
    #     MORTE, en silence, TOUTE la session, sur une machine SAINE.
    #     => LE REFUS EST REMPLACE PAR UNE **ATTENTE BORNEE** (-AttenteLhm,
    #        defaut 300 s) SUIVIE, A L'ECHEANCE, D'UN **DEMARRAGE DEGRADE**.
    #     !!! ET CE N'EST PAS UN RECUL SUR L'ARBITRAGE DU 2026-09-10 : le
    #        refus dur allait CONTRE LA CONCEPTION DU PRODUIT. agent/dn_agent.py
    #        pose AUCUNE grandeur LHM en position 0, precisement pour qu'une
    #        source LHM absente n'empeche RIEN - tolerance DEJA acquise quand
    #        LHM meurt EN COURS DE ROUTE (" une source morte meurt SEULE "),
    #        et refusee au seul cas du DEMARRAGE. L'asymetrie est ce qui a
    #        emporte l'arbitrage owner du 2026-09-12.
    # !!! LE PRE-VOL DEGRADE REND **0**, ET C'EST LOAD-BEARING.
    #     `tools/dn-agent.bat:112` fait `if errorlevel 1 goto :FIN` juste apres
    #     le pre-vol en `:RUN` - LE CHEMIN DE LA TACHE AU LOGON. Un pre-vol
    #     degrade qui rendrait 12 ferait sauter `:EXEC` : l'agent NE
    #     DEMARRERAIT PAS, c'est-a-dire EXACTEMENT la panne que cette marche
    #     repare, deplacee d'un cran. => la degradation est une DONNEE D'ETAT
    #     (dn-agent.started, `etat`, le bandeau), !!! jamais un code de retour.
    #     Le verbe `poser`, lui, LIT cet etat et rend `12` a la page : la, le
    #     code est une information rendue a un appelant qui sait la lire.
    # !!! LA PLACE EST CHOISIE : APRES les dependances, AVANT le compte
    #     d'instances - donc AVANT TOUTE DESTRUCTION D'ETAT. C'est le motif
    #     ecrit vingt lignes plus haut : un pre-vol qui echoue ne casse rien.
    # !!! L'ADRESSE EST **LUE DANS L'AGENT**, JAMAIS RECOPIEE ICI. Meme patron
    #     que tools\dn_lhm_tour.ps1 (l.122-128) : figer la valeur ferait DEUX
    #     sources de verite, et la seconde pourrirait EN SILENCE le jour ou
    #     l'owner joue un autre port. $AGENT est deja verifie plus haut.
    # !!! ET C'EST LE CHEMIN DE MESURES QUI TRANCHE, PAS LE PROCESSUS. Le
    #     serveur web de LHM vient de sa CONFIG XML, pas de son lancement : un
    #     LHM ouvert SANS serveur rendrait " 1 process " et un chemin de
    #     mesures MORT. Le compter serait un FAUX VERT.
    # (!) AUCUNE ELEVATION ICI : c'est un GET sur la boucle locale. C'est LHM
    #     qui coute l'elevation, pas DeskNode - et la tache de cet agent reste
    #     limitee (voir le bloc de `tache`, plus bas).
    # (!) -CaseSensitive, ET C'EST MESURE : Select-String est INSENSIBLE
    #     par defaut, la lecture Python de la meme adresse est SENSIBLE.
    #     Un `lhm_port` minuscule serait lu par l'un et pas par l'autre :
    #     la page dirait ' non testable ' pendant que ce pre-vol REFUSE.
    #     Le cote Python a raison - la constante est en MAJUSCULES.
    $lhmHote = $null; $lhmPort = $null; $lhmChemin = $null
    $mH = Select-String -CaseSensitive -Path $AGENT -Pattern '^LHM_HOTE\s*=\s*"([^"]+)"'   | Select-Object -First 1
    $mP = Select-String -CaseSensitive -Path $AGENT -Pattern '^LHM_PORT\s*=\s*(\d+)'       | Select-Object -First 1
    $mC = Select-String -CaseSensitive -Path $AGENT -Pattern '^LHM_CHEMIN\s*=\s*"([^"]+)"' | Select-Object -First 1
    if ($mH) { $lhmHote   = $mH.Matches[0].Groups[1].Value }
    if ($mP) { $lhmPort   = [int]$mP.Matches[0].Groups[1].Value }
    if ($mC) { $lhmChemin = $mC.Matches[0].Groups[1].Value }
    if ($null -eq $lhmHote -or $null -eq $lhmPort -or $null -eq $lhmChemin) {
        # (!) UNE IGNORANCE N'EST PAS UN ECART. On ne sait pas OU interroger
        #     LHM : on le DIT, et on ne refuse pas sur ce qu'on n'a pas mesure.
        Alerte "Adresse de LHM introuvable dans dn_agent.py : sonde IMPOSSIBLE."
        Alerte "  => ce n'est PAS ' LHM absent ', et cela ne bloque rien ici."
    } else {
        # !!! dn8-3 - -Lhm SURCHARGE CE QUI VIENT D'ETRE **LU DANS L'AGENT**,
        #     et il ne le remplace QUE s'il a ete donne. L'ordre compte : on
        #     LIT d'abord (donc la lecture reste la source), on surcharge
        #     ensuite. C'est ce qui garde " une seule source de verite "
        #     quand personne ne passe -Lhm, c'est-a-dire dans le regime livre.
        if ($null -ne $LhmPortForce) {
            Dire ("-Lhm : la sonde vise " + $LhmHoteForce + ":" + $LhmPortForce +
                  " (l'agent recevra --lhm " + $Lhm + ")")
            $lhmHote = $LhmHoteForce
            $lhmPort = $LhmPortForce
            $LhmSonde = $true
        }
        $lhmUrl = "http://" + $lhmHote + ":" + $lhmPort + $lhmChemin
        $lhmVu = $false
        # !!! UN 200 NE SUFFIT PAS, ET C'EST MESURE : /metrics sur ce port
        #     est L'ADRESSE LA PLUS BANALE D'UN EXPORTATEUR PROMETHEUS.
        #     Un service voisin rendrait la sonde VERTE, l'agent demarrerait,
        #     et la temperature du CPU resterait a " -- " pour toujours -
        #     meme famille de faux vert que compter le processus.
        #     => le CORPS doit porter le prefixe que l'agent lui-meme exige
        #        (dn_agent.py : `if not ligne.startswith("lhm_")`).
        # !!! L'ATTENTE BOUCLE SUR **CETTE** SONDE, ELLE N'EN INTRODUIT AUCUNE
        #     AUTRE - et ce n'est pas une economie, c'est la propriete. Le
        #     paragraphe ci-dessus dit pourquoi le CORPS tranche ; une seconde
        #     sonde " juste pour attendre ", plus laxiste, rouvrirait
        #     EXACTEMENT le trou de l'exportateur Prometheus voisin : on
        #     attendrait un 200 nu, puis on repartirait en croyant avoir LHM.
        # !!! ET L'ATTENTE N'EST JAMAIS UN GEL MUET : chaque tour IMPRIME sa
        #     ligne (ecoule / borne). Une fenetre immobile cinq minutes est
        #     indiscernable d'un blocage, et le journal de la tache serait muet
        #     sur la seule chose qui explique le retard.
        # (!) `-AttenteLhm 0` ne fait AUCUN tour d'attente : la sonde tire une
        #     fois, et l'echeance est atteinte immediatement.
        $lhmT0 = Get-Date
        $lhmEcoule = 0
        while ($true) {
            try {
                $rep = Invoke-WebRequest -Uri $lhmUrl -UseBasicParsing -TimeoutSec 3
                if ($rep.StatusCode -eq 200 -and
                    [string]$rep.Content -cmatch '(?m)^lhm_') { $lhmVu = $true }
            } catch { }
            if ($lhmVu) { break }
            $lhmEcoule = [int]((Get-Date) - $lhmT0).TotalSeconds
            if ($lhmEcoule -ge $AttenteLhm) { break }
            Dire ("LHM : pas encore la sur " + $lhmUrl + " - on ATTEND (" +
                  $lhmEcoule + " s / " + $AttenteLhm + " s).")
            # (!) ON NE DORT JAMAIS AU-DELA DE L'ECHEANCE : sans ce bornage, une
            #     borne de 3 s couterait 5 s de sommeil, et le pre-vol
            #     ANNONCERAIT une borne qu'il ne tient pas.
            $pas = Pas-Attente $AttenteLhm
            $reste = $AttenteLhm - $lhmEcoule
            if ($reste -lt $pas) { $pas = $reste }
            if ($pas -lt 1) { $pas = 1 }
            Start-Sleep -Seconds $pas
        }
        if (-not $lhmVu) {
            # !!! CE BLOC NE REFUSE PLUS : il DECLARE un DEMARRAGE DEGRADE et
            #     le pre-vol CONTINUE. Le bandeau nomme LHM, ce qui tombe sans
            #     lui, et le geste - les trois moities que le refus portait
            #     deja. Ce qui change, c'est la CONSEQUENCE.
            $LhmDegrade = $true
            $LhmEtatMarque = ("ABSENT (attendu " + $lhmEcoule +
                              " s sur une borne de " + $AttenteLhm + " s)")
            Alerte ("DEMARRAGE DEGRADE : LibreHardwareMonitor est reste INJOIGNABLE")
            Alerte ("  sur " + $lhmUrl + " apres " + $lhmEcoule +
                    " s d'attente (borne : " + $AttenteLhm + " s).")
            Alerte "  (ou il repond, mais ce n'est PAS LUI : le corps ne porte"
            Alerte "   aucune ligne ` lhm_ `, celle que l'agent exige.)"
            Alerte "  CE QUI TOMBE SANS LUI : la temperature du CPU et les trois"
            Alerte "  vitesses de ventilateur resteront a ' -- '. C'est LHM qui"
            Alerte "  lit ces sondes-la, et LUI SEUL. !!! TOUT LE RESTE EST"
            Alerte "  PUBLIE - le % CPU, les GHz, les Mo/s et la case AMBIANCE"
            Alerte "  n'en dependent pas : la dalle reste VIVANTE."
            Alerte "  => LE GESTE : .\tools\dn_lhm_tour.ps1 -Poser -Permanence tache"
            Alerte "     (ce script demande des droits administrateur ; cet"
            Alerte "      agent-ci, non. Sans argument il VERIFIE et ne change"
            Alerte "      RIEN.) Puis 'dn-agent.bat stop' et 'dn-agent.bat start'"
            Alerte "      pour recuperer les quatre grandeurs SANS attendre la"
            Alerte "      prochaine ouverture de session."
            Alerte "  (!) SI LHM TOURNE MAIS ECOUTE AILLEURS, CE CONSTAT EST"
            Alerte "      QUAND MEME LE BON, et sa parade est ailleurs : cette"
            Alerte "      sonde vise LHM_PORT de agent/dn_agent.py, et rien"
            Alerte "      d'autre. Un port different est une configuration"
            Alerte "      SUPPORTEE (dn_lhm_tour.ps1 -Port <n>), ET DEPUIS"
            Alerte "      dn8-3 LES DEUX OUTILS SAVENT LA PASSER :"
            # !!! CORRIGE LE 2026-09-12, ET C'EST UNE MESURE, PAS UN AVIS :
            #     ces deux lignes portaient `\"\"` et `.\\`, c'est-a-dire du
            #     quoting de C, PAS de PowerShell. Le seul echappement d'une
            #     chaine entre guillemets doubles est l'accent GRAVE ; `\` y est
            #     LITTERAL. Resultat JOUE dans powershell.exe 5.1 : la 1re ligne
            #     sortait TRONQUEE a ` run COM3 0 \ ` - la moitie qui porte
            #     l'adresse DISPARAISSAIT, en silence (le reste partait dans
            #     `$args`, qu'une fonction simple avale sans rien dire) - et la
            #     2de affichait un DOUBLE antislash. Le geste publie etait donc
            #     INJOUABLE, dans le seul message qui sert a le jouer.
            #     => on double les guillemets, comme PowerShell l'exige.
            Alerte "        dn-agent.bat run COM3 0 """" 127.0.0.1:<port>"
            Alerte "        .\dn_agent_tour.ps1 prevol -Lhm 127.0.0.1:<port>"
            Alerte "      (la 4e place, le temoin, doit etre OCCUPEE.)"
            Alerte "      => soit -Lhm, soit aligner LHM_PORT sur le port"
            Alerte "      REELLEMENT ecoute, soit rejouer dn_lhm_tour.ps1"
            Alerte "      SANS -Port pour revenir au defaut."
            Alerte "  !!! L'AGENT EST LANCE QUAND MEME, et c'est le changement du"
            Alerte "  2026-09-12 : une dalle a quatre champs vides bat une dalle"
            Alerte "  MORTE. Voir README.md, section de l'ecart declare."
            # !!! LE POURQUOI PART SUR UNE SURFACE **COTE WINDOWS**, parce que
            #     la tache au logon n'ouvre AUCUNE console : sans ca, ce
            #     bandeau n'atteindrait personne le jour ou il compte.
            #     (!) Le retour est JETE EXPRES : une surface absente est
            #         DECLAREE par la fonction, et une ignorance n'est pas un
            #         ecart - le code de retour du pre-vol ne bouge PAS.
            $null = Prevenir-Windows ("DeskNode : l'agent a demarre SANS " +
                "LibreHardwareMonitor (injoignable sur " + $lhmUrl + " apres " +
                $lhmEcoule + " s). La temperature du CPU et les trois vitesses " +
                "de ventilateur resteront a ' -- ' ; tout le reste est publie. " +
                "Le geste : tools\dn_lhm_tour.ps1 -Poser -Permanence tache, " +
                "puis dn-agent.bat stop et dn-agent.bat start.")
        } else {
            $LhmEtatMarque = ("repond 200 sur " + $lhmUrl)
            Dire ("LHM : " + $lhmUrl + " repond 200.")
        }
    }
    # --- fin du prerequis LHM -----------------------------------------

    # --- instance unique : le compte D'ABORD, le port ENSUITE. ------------
    $i = Get-Instances
    if ($i.Confirmes.Count -gt 0) {
        Alerte ("DEJA LANCE : " + $i.Confirmes.Count + " agent(s) vivant(s). Aucun second process ne sera cree.")
        foreach ($c in $i.Confirmes) { Dire ("  PID=" + $c.ProcessId) }
        exit 4
    }
    $p = Get-EtatPort $Serie
    # (!) AC3.7 : un port ABSENT se DIT. L'agent, lui, bouclerait sur son
    #     backoff en repetant FileNotFoundError sans jamais expliquer que la
    #     carte est simplement attachee a WSL.
    if ($p -eq 'absent') {
        Stop2 ("Le port " + $Serie + " N'EXISTE PAS cote Windows.")
        Stop2 "  La carte est probablement ATTACHEE A WSL. Pour la rendre a Windows :"
        Stop2 "      (depuis WSL)  ./tools/rendre-port.sh --vers-agent"
        Dire  ("usbipd : " + (Get-LigneUsbipd))
        exit 5
    }
    if ($p -eq 'fantome') {
        # !!! CAUSE DISTINCTE, NOMMEE DEPUIS LA REVUE DU 2026-08-26. Le port est
        #     ENUMERE mais `Open()` leve FileNotFound : la carte a ete rendue a
        #     WSL par un veilleur `--auto-attach`. AUCUN process ne le tient -
        #     l'ancien code disait pourtant " TENU par un process ", ce qui
        #     envoyait chercher un coupable qui n'existe pas.
        Stop2 ("Le port " + $Serie + " est un FANTOME : il est enumere, mais il ne s'ouvre pas.")
        Stop2 "  La carte a ete REPRISE par WSL (veilleur --auto-attach), !!! aucun process ne la tient."
        Stop2 "  => (depuis WSL)  ./tools/rendre-port.sh --vers-agent"
        Dire  ("usbipd : " + (Get-LigneUsbipd))
        exit 5
    }
    if ($p -eq 'inconnu') {
        Stop2 ("Le port " + $Serie + " ne s'ouvre pas, pour une cause NON RECONNUE.")
        Stop2 "  !!! Ce n'est ni 'absent', ni 'fantome', ni un refus d'acces. Rien n'est lance."
        Stop2 "  => 'dn-agent.bat etat', puis regarder le journal."
        exit 6
    }
    if ($p -eq 'tenu') {
        # Le compte n'a rien vu, et pourtant le port est pris : c'est
        # exactement le mode d'aveuglement de la CommandLine illisible.
        Stop2 ("Le port " + $Serie + " est TENU par un process, et AUCUN agent n'a ete reconnu.")
        foreach ($m in $i.Muets) { Stop2 ("  suspect : PID=" + $m.ProcessId + " (CommandLine ILLISIBLE)") }
        foreach ($e in $i.Etrangers) { Stop2 ("  suspect : PID=" + $e.ProcessId + " (un dn_agent.py d'un AUTRE deploiement)") }
        Stop2 "  => 'dn-agent.bat etat', puis arreter le tenant a la main. Rien n'est lance."
        exit 6
    }

    if (Test-Path $ENVCMD) { Remove-Item -Force $ENVCMD }   # (voir le bloc en tete de 'prevol')
    Rotation-Journal
    # !!! UN DRAPEAU PERIME TUERAIT LE NOUVEL AGENT AU PREMIER CYCLE. On le
    #     retire ICI, avant de lancer, et pas seulement a la fin de `stop` :
    #     un `stop` interrompu en laisserait un derriere lui.
    if (Test-Path $DRAPEAU) { Remove-Item -Force $DRAPEAU }
    $argl = @('--serie', $Serie, '--stop-si', $DRAPEAU)
    # !!! ELEMENT PARENTHESE : en PowerShell LA VIRGULE LIE PLUS FORT QUE
    #     `+` (le motif mesure le 2026-08-26, vingt lignes plus bas).
    # !!! ON NE PASSE QUE CE QU'ON A SONDE. Si l'adresse de LHM n'a pas pu
    #     etre lue dans dn_agent.py, la sonde est SAUTEE (simple Alerte) :
    #     passer quand meme --lhm annoncerait un prerequis VERIFIE qui ne
    #     l'est pas. Les deux moities sont donc COHERENTES, ou on refuse.
    if ($Lhm) {
        if (-not $LhmSonde) {
            Stop2 "-Lhm a ete demande, mais l'adresse de LHM n'a PAS pu etre"
            Stop2 "  lue dans dn_agent.py : la sonde n'a donc PAS eu lieu."
            Stop2 "  Passer --lhm sans avoir sonde annoncerait un prerequis"
            Stop2 "  VERIFIE qui ne l'est pas. Rien n'est lance."
            exit 3
        }
        $argl += @('--lhm', $Lhm)
    }
    if ($Temoin)      { $argl += '--temoin' }
    if ($Duree -gt 0) { $argl += @('--duree', "$Duree") }
    $regime = $(if ($env:DN_REGIME) { $env:DN_REGIME } else { 'inconnu' })
    # !!! CHAQUE ELEMENT EST PARENTHESE, ET CE N'EST PAS COSMETIQUE.
    #    En PowerShell LA VIRGULE LIE PLUS FORT QUE `+` : sans parentheses,
    #    `@('a' + $x, 'b' + $y)` se parse en `'a' + $x + ('"','b') + $y`,
    #    l'array est APLATI avec $OFS (un ESPACE) et les deux lignes n'en font
    #    qu'UNE. MESURE le 2026-08-26 : dn-agent.env.cmd est sorti sur une
    #    seule ligne, le second `set` n'a jamais ete execute, et python a
    #    recu "...\set" comme nom de script.
    @(
        ("lance   : " + (Get-Date -Format 'yyyy-MM-ddTHH:mm:ssK')),
        ("regime  : " + $regime),
        ("python  : " + $py),
        ("agent   : " + $AGENT),
        ("args    : " + ($argl -join ' ')),
        # !!! dn4-48 - LA DEGRADATION VOYAGE PAR L'ETAT ECRIT, !!! JAMAIS PAR
        #     LE CODE DE SORTIE (motif en entier au bloc LHM). C'est CETTE
        #     ligne que `etat` relit, et c'est elle que `poser` interroge pour
        #     rendre `12` a la page. Un agent lance par la tache au logon
        #     n'ouvre AUCUNE console : sans trace sur disque, " pourquoi la
        #     temperature reste a -- " n'aurait aucune reponse.
        ("lhm     : " + $(if ($LhmDegrade) { $MARQUE_DEGRADE + " - " }
                          else { "" }) + $LhmEtatMarque),
        ("coeurs  : " + $env:NUMBER_OF_PROCESSORS)
    ) -join "`r`n" | Set-Content -Encoding ASCII $MARQUE

    # Le .bat relit ces variables : pas de parsing de sortie, pas de
    # devinette de guillemets.
    # !!! REVUE DU 2026-08-26 - LES ARGUMENTS ETAIENT JOINTS **SANS
    #     GUILLEMETS**, et `dn-agent.bat` les expanse nu (`%DN_ARGS%`).
    #     `--stop-si` porte `Join-Path $RACINE 'dn-agent.stop'` : TOUT
    #     REPERTOIRE DE DEPLOIEMENT CONTENANT UN ESPACE tronquait le chemin,
    #     argparse rendait "unrecognized arguments", et `lancer` concluait
    #     "Aucun agent vivant" en renvoyant vers un journal qui ne nomme pas
    #     la cause. Le commentaire juste au-dessus revendique pourtant "pas de
    #     devinette de guillemets" : on les MET, ici, une fois.
    #     /!\ On ne cite QUE ce qui en a besoin : un `--temoin` entre guillemets
    #     resterait correct, mais la ligne publiee dans le marqueur doit rester
    #     lisible pour l'owner.
    $argsCites = ($argl | ForEach-Object {
        if ($_ -match '[\s"]') { '"' + ($_ -replace '"','""') + '"' } else { $_ }
    }) -join ' '
    @(
        ('set "DN_PY=' + $py + '"'),
        ('set "DN_ARGS=' + $argsCites + '"')
    ) -join "`r`n" | Set-Content -Encoding ASCII $ENVCMD
    Dire ("args : " + $argsCites)
    Dire "pre-vol OK"
    exit 0
}

# --------------------------------------------------------------------------
# LANCER = pre-vol VISIBLE, puis detachement. Le pre-vol s'affiche dans la
# fenetre du double-clic : si COM3 est absent, l'owner LE VOIT au lieu de
# regarder un journal se remplir de FileNotFoundError.
'lancer' {
    $ps1  = $MyInvocation.MyCommand.Path
    $tem  = $(if ($Temoin) { '-Temoin' } else { '' })
    # !!! TRANSMIS, sinon le pre-vol FILS sonderait l'adresse de l'agent
    #     pendant que l'agent, lui, recevrait --lhm : deux adresses.
    $lhmArg = $(if ($Lhm) { @('-Lhm', $Lhm) } else { @() })
    # !!! LA BORNE EST TRANSMISE **TOUJOURS**, contrairement a -Lhm : c'est un
    #     [int] qui a un DEFAUT, donc " absent " et " 300 " sont indiscernables
    #     du cote fils. Ne pas la passer ferait attendre au pre-vol FILS la
    #     valeur par defaut pendant que le pere en annonce une autre - deux
    #     bornes, comme il y avait deux adresses avant dn8-3.
    $attArg = @('-AttenteLhm', $AttenteLhm)
    # =====================================================================
    # !!! REVUE DU 2026-08-26 - LA GARDE ANTI-DOUBLON EST UN SCAN **TOCTOU**.
    #     `prevol` tourne dans un powershell SEPARE ; entre son
    #     `Get-CimInstance` et l'apparition de `python.exe` dans la table des
    #     process il y a : la fin du pre-vol, `Start-Process`, le demarrage de
    #     cmd.exe puis celui de CPython - DES SECONDES. Deux double-clics dans
    #     cette fenetre voyaient tous deux `Confirmes = 0` et lancaient tous
    #     deux. L'agent n.2 echouait ensuite a ouvrir COM3 et restait VIVANT en
    #     backoff infini, a remplir le journal.
    #     /!\ Et le 3e temoin existait sans jamais servir de garde : $MARQUE
    #     (dn-agent.started) est ECRIT par prevol et LU seulement pour
    #     l'affichage.
    # => UN MUTEX NOMME MACHINE-WIDE serialise pre-vol + lancement + preuve.
    #    Le 2e double-clic attend, puis son pre-vol voit l'agent du 1er et
    #    refuse proprement.
    # /!\ CE QUE CE MUTEX NE FAIT PAS, ET ON LE DIT : il ne couvre que les
    #     lancements passant par CE verbe. Un agent demarre autrement (la
    #     tache via `:RUN`, un python lance a la main) n'est PAS serialise -
    #     le compte ET l'etat du port restent les instruments, comme AC3.4
    #     l'exige. La fenetre est RETRECIE, pas supprimee.
    # =====================================================================
    $cree = $false
    $mutex = New-Object System.Threading.Mutex($true, 'Global\DeskNodeAgentLancement', [ref]$cree)
    if (-not $cree) {
        Dire "un autre lancement est en cours - on attend qu'il finisse (30 s max)..."
        if (-not $mutex.WaitOne(30000)) {
            Stop2 "Un autre lancement tient le verrou depuis plus de 30 s. Rien n'est lance."
            Stop2 "  => 'dn-agent.bat etat' pour voir ce qui tourne."
            exit 11
        }
    }
    try {
        $code = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $ps1 prevol `
                    -Serie $Serie -Duree $Duree @lhmArg @attArg $tem
        $code | ForEach-Object { Write-Host $_ }
        if ($LASTEXITCODE -eq 4) { exit 0 }   # deja lance : AUCUN doublon, et ce
                                              # n'est pas une erreur.
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

        Titre 'LANCEMENT'
        $suite = '"' + $BAT + '" exec ' + $Serie
        $p = Start-Process -FilePath $env:ComSpec -ArgumentList @('/c', $suite) `
                -WindowStyle Hidden -PassThru
        # !!! REVUE DU 2026-08-26 - L'ATTENTE ETAIT UN `Start-Sleep 3` SUIVI
        #     D'UN SEUL CONTROLE. Sur un H: lent (montage reseau, disque qui
        #     se reveille), CPython n'est pas encore dans la table : le script
        #     annoncait "Aucun agent vivant" et renvoyait vers un journal, ALORS
        #     QUE L'AGENT ETAIT EN TRAIN DE MONTER. `stop` sondait deja, lui.
        $i = $null
        $t0 = Get-Date
        while (((Get-Date) - $t0).TotalSeconds -lt 10) {
            $i = Get-Instances
            if ($i.Confirmes.Count -gt 0) { break }
            Start-Sleep -Milliseconds 250
        }
        if ($i.Confirmes.Count -eq 0) {
            Stop2 "Aucun agent vivant 10 s apres le lancement. Le journal dit pourquoi :"
            Stop2 ("  " + $LOG)
            if (Test-Path $LOG) { Get-Content $LOG -Tail 12 | ForEach-Object { Write-Host "    $_" } }
            Stop2 "  /!\ Si le journal est VIDE ou n'a pas bouge, l'echec est ANTERIEUR a"
            Stop2 "      python : le .bat a pu sortir sur :SANSPS1 ou :SANSENV, dont les"
            Stop2 "      messages partent dans une console CACHEE. Rejouer a la main :"
            Stop2 ('        cmd /c "' + $BAT + '" exec ' + $Serie)
            exit 10
        }
        foreach ($c in $i.Confirmes) { Dire ("agent VIVANT  PID=" + $c.ProcessId) }
        Dire ("lanceur cmd.exe PID=" + $p.Id + "  (pere de python.exe)")
        Dire ("journal : " + $LOG)
        exit 0
    } finally {
        $mutex.ReleaseMutex() | Out-Null
        $mutex.Dispose()
    }
}

# --------------------------------------------------------------------------
# TACHE = ce que la tache planifiee appelle. Elle n'existe QUE pour que le
# quoting reste DANS PowerShell, ou il est controlable.
# !!! ET POUR QUE LA FENETRE CONSOLE DISPARAISSE. MESURE le 2026-08-26 :
#     avec `cmd.exe` en action directe, la tache ouvre une fenetre console
#     qui reste a l'ecran TOUT LE TEMPS DU RUN (MainWindowHandle=65826
#     releve sur le cmd.exe de la tache, 812 s apres le logon). Un agent
#     PERMANENT qui laisse une fenetre ouverte 24 h/24 est un defaut du
#     produit, pas un detail. L'action passe donc par
#     `powershell -WindowStyle Hidden`, qui cache la console de TOUT l'arbre.
# -- La chaine de PID reste lisible - elle gagne juste un maillon :
#     engine -> powershell.exe -> cmd.exe (le .bat) -> python.exe
'tache' {
    # !!! LA PLACE DU TEMOIN EST **TOUJOURS OCCUPEE**, ET C'EST OBLIGATOIRE
    #     DEPUIS QU'UN 5e ARGUMENT EXISTE : `run COM3 0  8086` ferait lire
    #     8086 en %4 (le temoin) et RIEN en %5. On pose `""`, que le .bat
    #     deshabille par `%~4`.
    $tem = $(if ($Temoin) { '-Temoin' } else { '""' })
    # !!! ET LA 5e PLACE (l'adresse LHM) EST OCCUPEE A SON TOUR, POUR LA MEME
    #     RAISON, DEPUIS QU'UN 6e ARGUMENT EXISTE (dn4-48) : `run COM3 0 "" 300`
    #     ferait lire 300 en %5 - l'ADRESSE de LHM -, `-Lhm 300` serait REFUSE
    #     par la validation de forme, et la borne partirait en silence.
    $lhmPos = $(if ($Lhm) { $Lhm } else { '""' })
    & $env:ComSpec /c ('"' + $BAT + '" run ' + $Serie + ' ' + $Duree + ' ' + $tem + ' ' + $lhmPos + ' ' + $AttenteLhm)
    exit $LASTEXITCODE
}

# --------------------------------------------------------------------------
'stop' {
    Titre 'STOP'
    $i  = Get-Instances
    $p0 = Get-EtatPort $Serie
    if ($i.Confirmes.Count -eq 0) { Dire "aucun agent reconnu." }
    foreach ($c in $i.Confirmes) { Dire ("a arreter : PID=" + $c.ProcessId) }
    foreach ($m in $i.Muets)     { Alerte ("PID=" + $m.ProcessId + " : CommandLine ILLISIBLE - ne peut PAS etre exclu.") }
    foreach ($e in $i.Etrangers) { Alerte ("PID=" + $e.ProcessId + " : dn_agent.py d'un AUTRE deploiement - !!! ni signale, ni tue.") }

    # =====================================================================
    # !!! REVUE DU 2026-08-26 - LE DRAPEAU ETAIT GATE SUR `Confirmes > 0`,
    #     C'EST-A-DIRE REFUSE EXACTEMENT DANS LE CAS D'AVEUGLEMENT SUR LEQUEL
    #     TOUT L'EN-TETE DE CE FICHIER EST BATI. Chemin concret : agent VIVANT
    #     dont la `CommandLine` est ILLISIBLE (faux negatif MESURE, PID 6056)
    #     => Confirmes = 0 => " aucun agent reconnu " => LE DRAPEAU N'EST
    #     JAMAIS POSE => `exit 8`, " arreter le tenant a la main ", ET LE BILAN
    #     EST PERDU.
    #     Or poser le drapeau coute UNE ECRITURE DE FICHIER, et `dn_agent.py`
    #     teste LE FICHIER, !!! pas l'identite de l'appelant : l'agent muet se
    #     serait arrete PROPREMENT.
    # => ON POSE LE DRAPEAU DES QU'IL Y A QUELQUE CHOSE A ARRETER : un agent
    #    reconnu, OU un process muet, OU un port simplement TENU.
    #    !!! Le `taskkill` de repli, lui, ne vise QUE les `Confirmes` : on ne
    #    tue jamais un process qu'on n'a pas identifie.
    # =====================================================================
    $aTenter = ($i.Confirmes.Count -gt 0) -or ($i.Muets.Count -gt 0) -or ($p0 -eq 'tenu')
    if (($i.Confirmes.Count -eq 0) -and $aTenter) {
        Dire "aucun agent RECONNU, mais quelque chose tient le port : on pose quand meme le"
        Dire "  drapeau - un arret propre coute une ecriture, et il sauve le bilan."
    }
    if ($aTenter) {
        # =================================================================
        # 1) LE DRAPEAU D'ABORD - ET C'EST LE SEUL ARRET **PROPRE**.
        #    MESURE le 2026-08-26 : `taskkill /PID` (poli) NE TUE PAS cet
        #    agent (encore vivant apres 5 s), et le repli `/F` est un
        #    TerminateProcess que personne ne peut intercepter => le bilan
        #    de fin - trames emises, erreurs d'envoi, recalages, bruit
        #    d'echo, refus firmware - etait PERDU A CHAQUE ARRET (0 octet
        #    ajoute au journal). Detache ou en tache planifiee, l'agent n'a
        #    PAS DE CONSOLE : il n'y a pas de Ctrl+C a envoyer.
        #    => `--stop-si` (dn_agent.py) lit ce fichier une fois par cycle
        #       et sort par son try/finally, qui IMPRIME le bilan.
        # =================================================================
        $avant = 0
        if (Test-Path $LOG) { $avant = (Get-Item $LOG).Length }
        # !!! REVUE DU 2026-08-26 - L'ECRITURE N'ETAIT PAS VERIFIEE, et le
        #     message " drapeau pose " etait INCONDITIONNEL. Avec
        #     $ErrorActionPreference = 'Continue', un H: decroche / en lecture
        #     seule / plein laissait le script AFFIRMER avoir demande l'arret
        #     propre, attendre 8 s pour rien, puis passer au `taskkill /F`.
        Set-Content -Encoding ASCII -ErrorAction SilentlyContinue $DRAPEAU `
            ("stop demande " + (Get-Date -Format 'yyyy-MM-ddTHH:mm:ssK'))
        if (-not (Test-Path $DRAPEAU)) {
            Stop2 ("LE DRAPEAU N'A PAS PU ETRE ECRIT : " + $DRAPEAU)
            Stop2 "  !!! L'arret propre est IMPOSSIBLE (cible en lecture seule, decrochee, pleine ?)."
            Stop2 "     Le bilan de fin SERA PERDU si on force. Rien n'est force ici."
            exit 4
        }
        Dire "drapeau pose : arret PROPRE demande (le bilan de fin doit sortir)"
        $t0 = Get-Date
        while (((Get-Date) - $t0).TotalSeconds -lt 8) {
            if ((Get-Instances).Confirmes.Count -eq 0) { break }
            Start-Sleep -Milliseconds 250
        }
        $apres = 0
        if (Test-Path $LOG) { $apres = (Get-Item $LOG).Length }
        if ((Get-Instances).Confirmes.Count -eq 0) {
            Dire ("arret propre en " + [int](((Get-Date) - $t0).TotalSeconds) + " s ; bilan ecrit : " + ($apres - $avant) + " o")
        }

        # 2) REPLI, et il est DECLARE : on perd le bilan, on le dit.
        foreach ($c in (Get-Instances).Confirmes) {
            Alerte ("PID=" + $c.ProcessId + " vivant apres 8 s : le drapeau n'a pas ete lu.")
            & taskkill.exe /PID $c.ProcessId 2>&1 | Out-Null
        }
        $t0 = Get-Date
        while (((Get-Date) - $t0).TotalSeconds -lt 5) {
            if ((Get-Instances).Confirmes.Count -eq 0) { break }
            Start-Sleep -Milliseconds 250
        }
        foreach ($c in (Get-Instances).Confirmes) {
            Alerte ("PID=" + $c.ProcessId + " : arret FORCE. LE BILAN DE FIN EST PERDU.")
            & taskkill.exe /F /PID $c.ProcessId 2>&1 | Out-Null
        }
        Start-Sleep -Milliseconds 500
    }
    # Le drapeau est retire DANS TOUS LES CAS : un drapeau oublie tuerait le
    # prochain agent des son premier cycle.
    if (Test-Path $DRAPEAU) { Remove-Item -Force $DRAPEAU }
    if (Test-Path $MARQUE)  { Remove-Item -Force $MARQUE }

    # 2) LA PREUVE. Un code de retour ne prouve rien (piege P2).
    Titre 'PREUVE : ON RE-OUVRE LE PORT'
    $etat = Ecrire-Etat $Serie
    if ($etat.Port -eq 'libre') {
        Dire ("OK - " + $Serie + " se REOUVRE : le port est rendu.")
        exit 0
    }
    if ($etat.Port -eq 'absent') {
        Alerte ($Serie + " n'existe plus cote Windows (carte debranchee ou reattachee a WSL).")
        Alerte "  L'agent est arrete, mais CE N'EST PAS la preuve demandee par AC3.3."
        exit 7
    }
    if ($etat.Port -eq 'fantome') {
        # Distingue depuis la revue du 2026-08-26 : le port est enumere mais ne
        # s'ouvre pas. !!! Ce n'est PAS " un process le tient ".
        Alerte ($Serie + " est un FANTOME : enumere, mais il ne s'ouvre pas.")
        Alerte "  Un veilleur a rendu la carte a WSL. L'agent est arrete, mais ce n'est"
        Alerte "  PAS la preuve d'AC3.3 (qui exige une OUVERTURE QUI REUSSIT)."
        exit 7
    }
    if ($etat.Port -eq 'inconnu') {
        Stop2 ($Serie + " ne s'ouvre pas, pour une cause NON RECONNUE.")
        Stop2 "  !!! On ne conclut ni 'rendu' ni 'tenu'. => 'dn-agent.bat etat'."
        exit 8
    }
    Stop2 ($Serie + " est ENCORE TENU apres l'arret. Un process qu'on croit mort le tient.")
    Stop2 "  => 'dn-agent.bat etat' et regarder les CommandLine ILLISIBLES."
    exit 8
}

# --------------------------------------------------------------------------
# AC5 - la tache au logon.
'permanence' {
    Titre 'PERMANENCE (tache au logon)'
    if (-not (Test-Path $BAT)) { Stop2 ("dn-agent.bat introuvable : " + $BAT); exit 3 }
    # =====================================================================
    # !!! REVUE DU 2026-08-26 - LA POSE VERIFIAIT LE RunLevel ET L'ABSENCE DE
    #     CLE Run (deux bons controles), MAIS NI LE PORT, NI LA PRESENCE DE
    #     L'AGENT, NI LE TEMOIN. `dn-agent.bat permanence CMO3 0 -Temoin`
    #     rendait donc "tache POSEE | RunLevel=Limited" et exit 0 - puis
    #     ECHOUAIT A CHAQUE LOGON, sans console, dans un journal que rien ne
    #     signale. C'est la classe "un outil qui obeit a une faute de frappe",
    #     celle que deployer_tour.sh a explicitement corrigee, re-fabriquee ici.
    # =====================================================================
    if ($Serie -notmatch '^COM[0-9]+$') {
        Stop2 ("Port invalide : '" + $Serie + "'. Attendu : COM<n> (ex. COM3).")
        Stop2 "  !!! Une tache posee sur un port qui n'existe pas echoue a CHAQUE"
        Stop2 "      logon, en silence. Rien n'est pose."
        exit 3
    }
    if (-not (Test-Path $AGENT)) {
        Stop2 ("dn_agent.py introuvable a cote du .bat : " + $AGENT)
        Stop2 "  => redeployer d'abord : tools/deployer_tour.sh"
        exit 3
    }
    $etatPort = Get-EtatPort $Serie
    if ($etatPort -eq 'absent') {
        Alerte ($Serie + " n'existe pas cote Windows EN CE MOMENT.")
        Alerte "  La tache est quand meme posee (la carte peut revenir), mais si le"
        Alerte "  port n'est pas la au logon, l'agent NE DEMARRERA PAS - voir le"
        Alerte "  redemarrage automatique configure plus bas."
    }
    if (-not $Temoin) {
        Alerte "TACHE POSEE SANS -Temoin : l'agent n'aura PAS son instrument de cout."
        Alerte "  Le dossier (25.15) fait dependre du temoin sa re-verification"
        Alerte "  'gratuite et automatique au prochain logon'. Sans lui, elle N'A PAS LIEU."
        Alerte "  => 'dn-agent.bat permanence COM3 0 -Temoin' pour le regime complet."
    }
    $moi = [Security.Principal.WindowsIdentity]::GetCurrent().Name
    # !!! REVUE DU 2026-08-26 - ON NE DETRUIT PLUS AVANT DE SAVOIR REPOSER.
    #     `Unregister` puis `Register` traitait bien le cas "posee deux fois",
    #     mais DETRUISAIT UNE TACHE QUI MARCHAIT si le `Register` echouait
    #     ensuite (strategie de groupe, port invalide, service indisponible) :
    #     le message final "la tache n'a PAS ete posee" etait juste, et
    #     l'ancienne, elle, avait deja disparu.
    #     => `Set-ScheduledTask` met a jour EN PLACE quand elle existe.
    $existante = Get-ScheduledTask -TaskName $NOM_TACHE -ErrorAction SilentlyContinue
    # !!! LA TACHE PORTE `-Temoin` SI ON LE LUI DEMANDE, ET C'EST UN CHOIX
    #     DE REGIME, pas un reglage de mise au point. Le temoin est le SEUL
    #     instrument qui dise ce que l'agent coute (cumul cpu_times rapporte
    #     au mural, imprime tous les 10 cycles). Sans lui dans le regime
    #     LIVRE, tout chiffre de cout decrirait un AUTRE regime que celui
    #     qui tourne. Cout : une lecture psutil toutes les 10 s, et ~1,2 Mo
    #     de journal par jour - la rotation est dimensionnee pour.
    $tem = $(if ($Temoin) { '-Temoin' } else { '' })
    # !!! L'ACTION EST `powershell -WindowStyle Hidden`, - PLUS `cmd.exe` NU.
    #     Motif MESURE ci-dessus (action 'tache') : en action directe, cmd.exe
    #     laisse une fenetre console OUVERTE tout le temps du run.
    #     Bonus : tout le quoting delicat vit dans le .ps1, l'action ne porte
    #     qu'UN chemin entre guillemets.
    $ps1 = Join-Path $RACINE 'dn_agent_tour.ps1'
    # !!! SANS CA, UNE TOUR DONT LHM ECOUTE AILLEURS REDEVIENDRAIT MUETTE A
    #     CHAQUE LOGON : la tache rejouerait le pre-vol sur l'adresse LUE
    #     dans l'agent, et le refus dur (exit 12) tomberait sur une machine
    #     SAINE. C'est le cas que le message du refus NOMME depuis dn7-5.
    $lhmCible = $(if ($Lhm) { ' -Lhm ' + $Lhm } else { '' })
    # !!! dn4-48 - ET LA TACHE PORTE LA **BORNE D'ATTENTE**, sinon le seul
    #     chemin qui en a besoin - la tache au logon, celle qui court apres
    #     LHM - serait le seul a ne pas la recevoir. C'est le tir qui a rendu
    #     `12` le 2026-09-12.
    $attCible = ' -AttenteLhm ' + $AttenteLhm
    $cible = '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "' +
             $ps1 + '" tache -Serie ' + $Serie + ' -Duree ' + $Duree + ' ' + $tem + $lhmCible + $attCible
    # !!! PAS `$action` : ce script a un PARAMETRE `$Action` avec un
    #     ValidateSet, et les variables PowerShell sont INSENSIBLES A LA
    #     CASSE. `$action = New-ScheduledTaskAction ...` declenchait donc le
    #     ValidateSet du parametre et la pose echouait avec un message qui
    #     parlait de MSFT_TaskExecAction - un diagnostic qui envoie regarder
    #     la tache alors que la faute est un nom de variable. MESURE ici.
    $acte = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $cible -WorkingDirectory $RACINE
    $trigger = New-ScheduledTaskTrigger -AtLogOn -User $moi
    # =====================================================================
    # !!! `-RunLevel Limited`, ET C'EST **VOULU**.        (dn4-17 / AC5.2)
    #     Le modele de cette tache est `dn_lhm_tour.ps1:456-465`, qui pose
    #     `-RunLevel Highest`. CE N'EST PAS UNE OMISSION ICI, C'EST L'ECART.
    #     Highest est JUSTE pour LHM : Super I/O, PawnIO, Ring0.
    #     Il est FAUX pour l'agent : D8 dit qu'il n'a "ni elevation, ni
    #     driver, ni .NET", et c'est LA MOITIE DE PHRASE QUI REND LHM
    #     ACCEPTABLE dans le perimetre V1 (amendement D13, dn_agent.py:5-16).
    #     Elever l'agent detruirait la these de son propre en-tete.
    #     => Un lecteur qui compare les deux scripts n'a pas a deviner
    #        lequel est l'erreur : il n'y en a pas, les deux sont voulus.
    #     Consequence utile : `Limited` + LogonType Interactive s'enregistre
    #     SANS UAC. Le geste owner est un double-clic, sans invite.
    # =====================================================================
    $principal = New-ScheduledTaskPrincipal -UserId $moi -LogonType Interactive -RunLevel Limited
    # !!! REVUE DU 2026-08-26 - LA TACHE N'AVAIT NI -RestartCount NI
    #     -RestartInterval. Si elle tire pendant que la carte est attachee a
    #     WSL, `prevol` sort en 5, `:RUN` fait `if errorlevel 1 goto :FIN`, la
    #     tache se termine - ET L'AGENT EST ABSENT TOUTE LA SESSION, en
    #     silence, sans aucune reprise. La 1re moitie du critere n.4 du brief
    #     ("l'agent demarre avec la session") echouait donc FERMEE ET MUETTE.
    #     /!\ -StartWhenAvailable couvre un HORAIRE manque, PAS un RUN echoue :
    #     ce n'etait pas le bon reglage pour ce cas.
    #     3 reprises a 1 min : de quoi couvrir un `--vers-agent` joue juste
    #     apres le logon, sans boucler indefiniment sur une carte debranchee.
    # =====================================================================
    # !!! 2026-09-10 (dn7-5) - LE REFUS DUR CREE UNE **COURSE AU LOGON**, ET
    #     ELLE EST ECRITE PLUTOT QUE TUE. Depuis cette date, `prevol` REFUSE
    #     quand LHM est injoignable (exit 12). Or les deux permanences tirent
    #     sur le MEME evenement et ne sont PAS symetriques :
    #       . la tache LHM      : AtLogOn, ELEVEE   (dn_lhm_tour.ps1:462-470)
    #       . la tache de l'agent : AtLogOn, NON elevee (juste au-dessus)
    #     => si LHM monte APRES l'agent, le pre-vol de l'agent refuse alors
    #        que la machine est SAINE trente secondes plus tard.
    #     LA PARADE EXISTE DEJA, ET C'EST LE REGLAGE CI-DESSOUS : 3 reprises
    #     a 1 minute. ELLE PORTE SA BORNE, ET C'EST LE PRIX ECRIT DE
    #     L'ARBITRAGE : au-dela de ~3 MINUTES, l'agent est ABSENT TOUTE LA
    #     SESSION, en silence. C'est la meme borne que celle du port attache
    #     a WSL, deux paragraphes plus haut - un seul mecanisme, deux causes.
    #     (!) NE PAS "corriger" en montant -RestartCount sans mesure : ce
    #         reglage a ete choisi pour ne PAS boucler indefiniment, et le
    #         relever deplacerait le cout au lieu de le supprimer.
    #
    # !!! ANNOTE LE 2026-09-12 (dn4-48) - LE BLOC CI-DESSUS RESTE, ET IL EST
    #     TOUJOURS EXACT SUR LA COURSE ; C'EST SA **PARADE** QUI A ETE
    #     REFUTEE PAR LA MESURE. Releve sur un VRAI redemarrage le
    #     2026-09-12 : la tache a tire UNE SEULE FOIS, a 18:13:13, rendu 12,
    #     et a 18:25 - bien au-dela des ~3 minutes annoncees ici -
    #     `LastRunTime` valait TOUJOURS 18:13:13 et `NextRunTime` etait VIDE.
    #     AUCUNE reprise n'a eu lieu. La borne de " ~3 min " decrivait un
    #     DELAI ; le fait mesure est qu'il n'y a eu AUCUNE reprise du tout.
    #     (!) LE MECANISME N'EST PAS ETABLI, ET C'EST DIT : le journal qui le
    #         montrerait (Microsoft-Windows-TaskScheduler/Operational) est
    #         ETEINT sur cette tour, donc " aucun evenement " est une propriete
    #         de LA METHODE, pas du Planificateur.
    #     => dn4-48 NE TOUCHE PAS a ce reglage - le relever deplacerait le
    #        cout, comme l'ecrit la ligne ci-dessus. Elle SUPPRIME LA
    #        DEPENDANCE a cette parade : le pre-vol ATTEND LHM, puis demarre
    #        degrade. La reprise reste une seconde ligne de defense pour les
    #        AUTRES causes (port attache a WSL), et c'est pour ca qu'on la
    #        garde ENTIERE.
    # =====================================================================
    $reglages = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero) `
        -StartWhenAvailable -MultipleInstances IgnoreNew `
        -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
    if ($existante) {
        Set-ScheduledTask -TaskName $NOM_TACHE -Action $acte -Trigger $trigger `
            -Principal $principal -Settings $reglages -ErrorAction SilentlyContinue | Out-Null
        Dire "tache existante MISE A JOUR en place (aucune fenetre sans tache)."
    } else {
        Register-ScheduledTask -TaskName $NOM_TACHE -Action $acte -Trigger $trigger `
            -Principal $principal -Settings $reglages `
            -Description 'Lance l agent DeskNode a l ouverture de session. NON ELEVE (dn4-17 / AC5.2).' | Out-Null
    }

    $t = Get-ScheduledTask -TaskName $NOM_TACHE -ErrorAction SilentlyContinue
    if (-not $t) { Stop2 "la tache n'a PAS ete posee."; exit 9 }
    Dire ("tache '" + $NOM_TACHE + "' POSEE | RunLevel=" + $t.Principal.RunLevel + " | etat=" + $t.State)
    $argsPoses = "" + ($t.Actions | Select-Object -First 1).Arguments
    Dire ("  cible : " + ($t.Actions | Select-Object -First 1).Execute + " " + $argsPoses)
    # !!! REVUE DU 2026-08-26 - ON COMPARE, on ne se contente plus d'IMPRIMER.
    #     Imprimer les arguments poses laissait au lecteur le soin de reperer
    #     qu'ils differaient de ce qu'il avait demande.
    if ($argsPoses -notmatch ('-Serie\s+' + [regex]::Escape($Serie))) {
        Stop2 ("La tache posee ne porte PAS -Serie " + $Serie + ".")
        exit 9
    }
    if ($Temoin -and ($argsPoses -notmatch '-Temoin')) {
        Stop2 "-Temoin a ete demande mais la tache posee ne le porte PAS."
        exit 9
    }
    # !!! ON COMPARE, on ne se contente pas d'IMPRIMER - meme regle que
    #     -Serie et -Temoin ci-dessus. Une tache posee sur une AUTRE adresse
    #     que celle demandee echouerait a CHAQUE logon, en silence.
    if ($Lhm -and ($argsPoses -notmatch ('-Lhm\s+' + [regex]::Escape($Lhm)))) {
        Stop2 ("-Lhm " + $Lhm + " a ete demande mais la tache posee ne le porte PAS.")
        exit 9
    }
    # !!! MEME REGLE POUR LA BORNE : une tache posee sans elle rejouerait le
    #     DEFAUT a chaque logon, et quelqu'un qui a choisi 600 s croirait
    #     l'avoir pose. La comparaison est ANCREE sur un mot, sinon `-AttenteLhm
    #     30` serait satisfaite par une tache qui porte `300`.
    if ($argsPoses -notmatch ('-AttenteLhm\s+' + [regex]::Escape("$AttenteLhm") + '\b')) {
        Stop2 ("-AttenteLhm " + $AttenteLhm + " a ete demande mais la tache posee ne le porte PAS.")
        exit 9
    }
    if ("$($t.Principal.RunLevel)" -ne 'Limited') {
        Stop2 "RunLevel n'est PAS Limited : c'est un DEFAUT ici (voir le bloc AC5.2 ci-dessus)."
        exit 9
    }
    # !!! AUCUNE cle HKCU\...\Run.                            (AC5.5)
    #     `dn_lhm_tour.ps1:494-496` la signale deja comme une ANOMALIE pour
    #     LHM ("repli NON ELEVE ... en doublon de la tache"). En poser une
    #     ici creerait DEUX lanceurs pour un agent dont AC3.2 promet ZERO
    #     doublon. On ne la pose pas, et on VERIFIE qu'elle n'existe pas.
    $cle = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
    $run = Get-ItemProperty -Path $cle -Name $NOM_TACHE -ErrorAction SilentlyContinue
    if ($run) { Stop2 "Une cle HKCU\...\Run existe pour cet agent : DEUX lanceurs. A retirer."; exit 9 }
    Dire "aucune cle HKCU\...\Run : un seul lanceur."
    exit 0
}

# --------------------------------------------------------------------------
# POSER = **ACTIVER**, ET C'EST LA COMPOSITION DE 'permanence' ET DE 'lancer'.
# !!! LE TROU EST MESURE, PAS SUPPOSE (dn7-6, 2026-09-10) : sur les SEPT
#     verbes de ce fichier, AUCUN n'ACTIVE.
#       . 'permanence' POSE la tache, mais son declencheur est -AtLogOn SEUL
#         => rien ne demarre avant la PROCHAINE ouverture de session ;
#       . 'lancer' DEMARRE l'agent, mais il ne touche PAS au Planificateur
#         => rien ne SURVIT a la session.
#     " Activer " a une definition observable : l'agent tourne MAINTENANT et
#     il tournera DEMAIN. Chaque moitie seule est FAUSSE, et un inconnu qui
#     clique " activer " sur l'une des deux verrait soit rien se passer, soit
#     tout disparaitre au reboot.
# !!! IL NE REDECLARE **AUCUN** REGLAGE DE TACHE, ET C'EST LA PROPRIETE :
#     -RunLevel Limited, -AtLogOn et la reprise viennent AVEC le bloc
#     reemploye. C'est ce qui tient NFR7.5 PAR CONSTRUCTION plutot que par une
#     consigne qu'on pourrait oublier - et la garde vivante de 'permanence'
#     (RunLevel != Limited => exit 9) rougirait si quelqu'un l'elevait.
# !!! LE PATRON EXISTE DEJA : 'lancer' s'auto-invoque en sous-processus pour
#     jouer 'prevol' et RELAIE son code. On reemploie, on n'invente pas.
'poser' {
    Titre 'ACTIVER (permanence, puis demarrage)'
    $moiPs1 = $MyInvocation.MyCommand.Path
    $tem = $(if ($Temoin) { '-Temoin' } else { '' })
    # !!! -Python EST **TRANSMIS**, sinon il est SILENCIEUSEMENT PERDU.
    #     Quelqu'un qui choisit son interpreteur pour 'poser' verrait la tache
    #     posee sur un AUTRE Python que celui qu'il a nomme - et il n'aurait
    #     aucun moyen de le savoir.
    $py = $(if ($Python) { @('-Python', $Python) } else { @() })
    # !!! MEME MOTIF QUE -Python : non transmis, il serait SILENCIEUSEMENT
    #     PERDU, et la tache posee viserait une AUTRE adresse que demandee.
    $lhmArg = $(if ($Lhm) { @('-Lhm', $Lhm) } else { @() })
    # !!! MEME MOTIF ENCORE : non transmise, la borne serait SILENCIEUSEMENT
    #     PERDUE, et la tache posee attendrait AUTRE CHOSE que ce qui a ete
    #     demande. Elle part TOUJOURS (voir `lancer`).
    $attArg = @('-AttenteLhm', $AttenteLhm)

    Titre 'POSER LA PERMANENCE'
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $moiPs1 permanence `
        -Serie $Serie -Duree $Duree @py @lhmArg @attArg $tem | ForEach-Object { Write-Host $_ }
    # !!! `$null` N'EST PAS `0`, ET `exit $null` REND **0**.
    #     Si powershell.exe n'a pas pu etre lance du tout, $LASTEXITCODE reste
    #     $null : le test `-ne 0` est VRAI, on tombe dans la branche d'echec,
    #     et `exit $null` sort en **0** - la page annonce alors " l'outil a
    #     rendu 0 " sur un geste qui n'a RIEN fait. Un SUCCES FAUX, qui est
    #     pire qu'un echec. => on le nomme `3`, comme les autres " rien n'a
    #     pu etre lance " de ce fichier.
    $codePermanence = $(if ($null -eq $LASTEXITCODE) { 3 } else { $LASTEXITCODE })
    if ($codePermanence -ne 0) {
        # Le code est RELAYE TEL QUEL : 3 (outil ou agent introuvable, port
        # invalide) et 9 (tache non conforme) disent deja ce qui s'est passe,
        # et les traduire ferait perdre l'information.
        Stop2 ("la permanence n'a PAS ete posee (code " + $codePermanence + ").")
        Stop2 "  => RIEN n'a ete demarre : activer sans permanence serait une"
        Stop2 "     moitie de geste, et elle ne survivrait pas a la session."
        exit $codePermanence
    }

    Titre 'DEMARRER MAINTENANT'
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $moiPs1 lancer `
        -Serie $Serie -Duree $Duree @py @lhmArg @attArg $tem | ForEach-Object { Write-Host $_ }
    # !!! MEME GARDE : $null vaudrait 0, donc " demarre " sur rien.
    $codeLancer = $(if ($null -eq $LASTEXITCODE) { 3 } else { $LASTEXITCODE })

    # !!! ON **MESURE**, on ne deduit PAS du message : c'est la meme regle que
    #     'retirer', qui redemande la tache au systeme plutot que de croire sa
    #     propre sortie.
    $i = Get-Instances
    if ($i.Confirmes.Count -gt 0) {
        foreach ($c in $i.Confirmes) { Dire ("agent VIVANT  PID=" + $c.ProcessId) }
        Dire ("tache '" + $NOM_TACHE + "' posee, et l'agent tourne MAINTENANT.")
        # =================================================================
        # !!! dn4-48 - `12` CHANGE D'EMETTEUR **ET DE SENS**, ET IL RESTE
        #     UNIQUE DANS CE FICHIER.
        #     AVANT : le bloc LHM du pre-vol, et il voulait dire " REFUS -
        #     l'agent n'est PAS lance ". Ce sens-la est ANNOTE, pas efface :
        #     il est barre a sa date dans le bloc LHM, plus haut.
        #     MAINTENANT : ce verbe-ci, et il veut dire " POSEE et **VIVANTE**,
        #     mais SANS LHM ". C'est la seule place ou le code peut encore
        #     dire quelque chose : `poser` est appele PAR LA PAGE, qui SAIT
        #     lire une table de codes (installeur/dn_installeur.py,
        #     CODES_POSER) - le pre-vol, lui, est appele par un `.bat` qui
        #     avorterait le lancement sur tout code non nul.
        #     (!) LA SOURCE EST L'ETAT ECRIT PAR LE PRE-VOL, !!! pas une
        #         nouvelle sonde : c'est l'agent QUI TOURNE qu'on qualifie, et
        #         re-sonder ici dirait l'etat de MAINTENANT.
        #     !!! CE N'EST NI UN SUCCES NI UN ECHEC - meme famille que `13` :
        #         les DEUX moities ont eu lieu, et la dalle EST vivante.
        # =================================================================
        if ((Test-Path $MARQUE) -and
            (((Get-Content $MARQUE -Raw) -replace '\r?\n', ' ') -match $MARQUE_DEGRADE)) {
            Alerte "LA PERMANENCE EST POSEE ET L'AGENT TOURNE, mais SANS"
            Alerte "  LibreHardwareMonitor : il est reste injoignable pendant toute"
            Alerte "  l'attente du pre-vol."
            Alerte "  !!! RIEN N'A ECHOUE : la tache est posee, l'agent est vivant,"
            Alerte "      la dalle se remplit. Seules la temperature du CPU et les"
            Alerte "      trois vitesses de ventilateur resteront a ' -- '."
            Alerte "  => LE GESTE : .\tools\dn_lhm_tour.ps1 -Poser -Permanence tache"
            Alerte "     puis 'dn-agent.bat stop' et 'dn-agent.bat start'."
            exit 12
        }
        exit 0
    }
    if (($codeLancer -eq 0) -or ($codeLancer -eq 10)) {
        # !!! LA MOITIE QUI A REUSSI EST **DITE**, ET ELLE A SON PROPRE CODE.
        #     Rendre 0 mentirait ; rendre le code de 'lancer' effacerait une
        #     permanence POSEE ET VERIFIEE. Ni un succes ni un echec total :
        #     les deux seraient FAUX.
        #     Le code 13 a ete MESURE LIBRE dans ce fichier (0,3..12 servent).
        Stop2 "LA PERMANENCE EST POSEE ET VERIFIEE, mais AUCUN agent n'est vivant."
        Stop2 "  => la tache repartira a la PROCHAINE ouverture de session ;"
        Stop2 "     ce qui n'a pas eu lieu, c'est le demarrage IMMEDIAT."
        Stop2 ("  Le journal dit pourquoi : " + $LOG)
        exit 13
    }
    Stop2 ("permanence POSEE ; le demarrage a rendu " + $codeLancer + " - relaye tel quel.")
    exit $codeLancer
}

# --------------------------------------------------------------------------
'retirer' {
    Titre 'RETRAIT DE LA TACHE'
    if (Get-ScheduledTask -TaskName $NOM_TACHE -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $NOM_TACHE -Confirm:$false
    } else { Dire "aucune tache a retirer." }
    # Le retrait se VERIFIE. (AC5.4)
    if (Get-ScheduledTask -TaskName $NOM_TACHE -ErrorAction SilentlyContinue) {
        Stop2 "la tache est TOUJOURS presente apres Unregister."
        exit 9
    }
    Dire ("tache '" + $NOM_TACHE + "' ABSENTE - retrait verifie.")
    # !!! REVUE DU 2026-08-26 - CETTE PHRASE AFFIRMAIT CE QU'ELLE NE VERIFIAIT
    #     PAS. Toute la chaine de l'agent (powershell -> cmd -> python) EST
    #     l'arbre d'action de l'instance de tache en cours, et le Planificateur
    #     termine generalement l'instance en cours quand la definition est
    #     desenregistree. => ON MESURE, on n'affirme plus.
    $apres = Get-Instances
    if ($apres.Confirmes.Count -gt 0) {
        Dire ("(i) l'agent est TOUJOURS vivant apres le retrait (" + $apres.Confirmes.Count + " process).")
        foreach ($c in $apres.Confirmes) { Dire ("      PID=" + $c.ProcessId) }
        Dire "    Pour l'arreter PROPREMENT (le bilan sort) : 'dn-agent.bat stop'."
    } else {
        Alerte "L'AGENT N'EST PLUS LA APRES LE RETRAIT."
        Alerte "  Le Planificateur a termine l'arbre d'action de la tache : le bilan"
        Alerte "  de fin est PERDU (TerminateProcess, aucun --stop-si lu)."
        Alerte "  => la prochaine fois, jouer 'dn-agent.bat stop' AVANT 'retirer'."
    }
    exit 0
}

}
