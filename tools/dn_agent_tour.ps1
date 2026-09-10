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
    [ValidateSet('etat', 'prevol', 'lancer', 'tache', 'stop', 'permanence', 'retirer')]
    [string]$Action = 'etat',

    [string]$Serie = 'COM3',
    [int]$Duree = 0,
    [switch]$Temoin,
    [string]$Python = ''
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

function Dire   ([string]$m) { Write-Host "  $m" }
function Titre  ([string]$m) { Write-Host ""; Write-Host "=== $m ===" }
function Alerte ([string]$m) { Write-Host "  /!\ $m" -ForegroundColor Yellow }
function Stop2  ([string]$m) { Write-Host "  /!\ $m" -ForegroundColor Red }

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
    return [pscustomobject]@{ Inst = $i; Port = $p }
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
        $lhmUrl = "http://" + $lhmHote + ":" + $lhmPort + $lhmChemin
        $lhmVu = $false
        # !!! UN 200 NE SUFFIT PAS, ET C'EST MESURE : /metrics sur ce port
        #     est L'ADRESSE LA PLUS BANALE D'UN EXPORTATEUR PROMETHEUS.
        #     Un service voisin rendrait la sonde VERTE, l'agent demarrerait,
        #     et la temperature du CPU resterait a " -- " pour toujours -
        #     meme famille de faux vert que compter le processus.
        #     => le CORPS doit porter le prefixe que l'agent lui-meme exige
        #        (dn_agent.py : `if not ligne.startswith("lhm_")`).
        try {
            $rep = Invoke-WebRequest -Uri $lhmUrl -UseBasicParsing -TimeoutSec 3
            if ($rep.StatusCode -eq 200 -and
                [string]$rep.Content -cmatch '(?m)^lhm_') { $lhmVu = $true }
        } catch { }
        if (-not $lhmVu) {
            Stop2 ("LibreHardwareMonitor est INJOIGNABLE sur " + $lhmUrl)
            Stop2 "  (ou il repond, mais ce n'est PAS LUI : le corps ne porte"
            Stop2 "   aucune ligne ` lhm_ `, celle que l'agent exige.)"
            Stop2 "  CE QUI TOMBE SANS LUI : la temperature du CPU et les trois"
            Stop2 "  vitesses de ventilateur ne seront JAMAIS publiees. C'est"
            Stop2 "  LHM qui lit ces sondes-la, et LUI SEUL."
            Stop2 "  => LE GESTE : .\tools\dn_lhm_tour.ps1 -Poser -Permanence tache"
            Stop2 "     (ce script demande des droits administrateur ; cet"
            Stop2 "      agent-ci, non. Sans argument il VERIFIE et ne change"
            Stop2 "      RIEN.)"
            Stop2 "  (!) SI LHM TOURNE MAIS ECOUTE AILLEURS, CE REFUS EST"
            Stop2 "      QUAND MEME LE BON, et sa parade est ailleurs : cette"
            Stop2 "      sonde vise LHM_PORT de agent/dn_agent.py, et rien"
            Stop2 "      d'autre. Un port different est une configuration"
            Stop2 "      SUPPORTEE (dn_lhm_tour.ps1 -Port <n>) que NI ce"
            Stop2 "      script NI dn-agent.bat ne savent encore passer a"
            Stop2 "      l'agent. => soit aligner LHM_PORT sur le port"
            Stop2 "      REELLEMENT ecoute, soit rejouer dn_lhm_tour.ps1"
            Stop2 "      SANS -Port pour revenir au defaut."
            Stop2 "  L'AGENT N'EST PAS LANCE : la dalle sans ces valeurs n'est"
            Stop2 "  pas le produit. Voir README.md, section de l'ecart declare."
            exit 12
        }
        Dire ("LHM : " + $lhmUrl + " repond 200.")
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
                    -Serie $Serie -Duree $Duree $tem
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
    $tem = $(if ($Temoin) { '-Temoin' } else { '' })
    & $env:ComSpec /c ('"' + $BAT + '" run ' + $Serie + ' ' + $Duree + ' ' + $tem)
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
    $cible = '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "' +
             $ps1 + '" tache -Serie ' + $Serie + ' -Duree ' + $Duree + ' ' + $tem
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
