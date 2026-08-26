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
    [ValidateSet('etat', 'prevol', 'lancer', 'stop', 'permanence', 'retirer')]
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
#     Plafond disque = 2 x $LOG_MAX. La rotation a lieu AU LANCEMENT, donc
#     un run tres long peut depasser le plafond : c'est ASSUME, et le debit
#     mesure dit de combien.
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
    $tous = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue)
    [pscustomobject]@{
        Tous      = $tous
        Confirmes = @($tous | Where-Object { $_.CommandLine -and ($_.CommandLine -match 'dn_agent\.py') })
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
    try   { $sp.Open(); $sp.Close(); return 'libre' }
    catch { return 'tenu' }
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
            Move-Item -Force $f ($f + '.1')
            Dire ("journal bascule (>= " + [int]($LOG_MAX / 1MB) + " Mo) : " + (Split-Path -Leaf $f) + ".1")
        }
    }
}

# ==========================================================================
switch ($Action) {

# --------------------------------------------------------------------------
'etat' {
    Titre 'ETAT (ne change RIEN)'
    Ecrire-Etat $Serie | Out-Null
    exit 0
}

# --------------------------------------------------------------------------
# PRE-VOL : tout ce qui doit etre VRAI avant de lancer python. Il n'ecrit
# aucun process : c'est le .bat qui lance, pour que le pere de python.exe
# soit le MEME cmd.exe dans les deux regimes (double-clic ET tache) - c'est
# ce qui rend la chaine de PID d'AC6.6 lisible.
'prevol' {
    Titre 'PRE-VOL'
    if (Test-Path $ENVCMD) { Remove-Item -Force $ENVCMD }

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
    if ($p -eq 'tenu') {
        # Le compte n'a rien vu, et pourtant le port est pris : c'est
        # exactement le mode d'aveuglement de la CommandLine illisible.
        Stop2 ("Le port " + $Serie + " est TENU par un process, et AUCUN agent n'a ete reconnu.")
        foreach ($m in $i.Muets) { Stop2 ("  suspect : python.exe PID=" + $m.ProcessId + " (CommandLine ILLISIBLE)") }
        Stop2 "  => 'dn-agent.bat etat', puis arreter le tenant a la main. Rien n'est lance."
        exit 6
    }

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
    @(
        ('set "DN_PY=' + $py + '"'),
        ('set "DN_ARGS=' + ($argl -join ' ') + '"')
    ) -join "`r`n" | Set-Content -Encoding ASCII $ENVCMD
    Dire ("args : " + ($argl -join ' '))
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
    Start-Sleep -Seconds 3
    $i = Get-Instances
    if ($i.Confirmes.Count -eq 0) {
        Stop2 "Aucun agent vivant 3 s apres le lancement. Le journal dit pourquoi :"
        Stop2 ("  " + $LOG)
        if (Test-Path $LOG) { Get-Content $LOG -Tail 12 | ForEach-Object { Write-Host "    $_" } }
        exit 10
    }
    foreach ($c in $i.Confirmes) { Dire ("agent VIVANT  PID=" + $c.ProcessId) }
    Dire ("lanceur cmd.exe PID=" + $p.Id + "  (pere de python.exe)")
    Dire ("journal : " + $LOG)
    exit 0
}

# --------------------------------------------------------------------------
'stop' {
    Titre 'STOP'
    $i = Get-Instances
    if ($i.Confirmes.Count -eq 0) { Dire "aucun agent reconnu." }
    foreach ($c in $i.Confirmes) { Dire ("a arreter : PID=" + $c.ProcessId) }

    if ($i.Confirmes.Count -gt 0) {
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
        Set-Content -Encoding ASCII $DRAPEAU ("stop demande " + (Get-Date -Format 'yyyy-MM-ddTHH:mm:ssK'))
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
    Stop2 ($Serie + " est ENCORE TENU apres l'arret. Un process qu'on croit mort le tient.")
    Stop2 "  => 'dn-agent.bat etat' et regarder les CommandLine ILLISIBLES."
    exit 8
}

# --------------------------------------------------------------------------
# AC5 - la tache au logon.
'permanence' {
    Titre 'PERMANENCE (tache au logon)'
    if (-not (Test-Path $BAT)) { Stop2 ("dn-agent.bat introuvable : " + $BAT); exit 3 }
    $moi = [Security.Principal.WindowsIdentity]::GetCurrent().Name
    if (Get-ScheduledTask -TaskName $NOM_TACHE -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $NOM_TACHE -Confirm:$false
        Dire "tache existante retiree (reposee a l'identique)."
    }
    # !!! LA TACHE PORTE `-Temoin` SI ON LE LUI DEMANDE, ET C'EST UN CHOIX
    #     DE REGIME, pas un reglage de mise au point. Le temoin est le SEUL
    #     instrument qui dise ce que l'agent coute (cumul cpu_times rapporte
    #     au mural, imprime tous les 10 cycles). Sans lui dans le regime
    #     LIVRE, tout chiffre de cout decrirait un AUTRE regime que celui
    #     qui tourne. Cout : une lecture psutil toutes les 10 s, et ~1,2 Mo
    #     de journal par jour - la rotation est dimensionnee pour.
    $tem = $(if ($Temoin) { '-Temoin' } else { '' })
    $cible = '/c ""' + $BAT + '" run ' + $Serie + ' ' + $Duree + ' ' + $tem + '"'
    # !!! PAS `$action` : ce script a un PARAMETRE `$Action` avec un
    #     ValidateSet, et les variables PowerShell sont INSENSIBLES A LA
    #     CASSE. `$action = New-ScheduledTaskAction ...` declenchait donc le
    #     ValidateSet du parametre et la pose echouait avec un message qui
    #     parlait de MSFT_TaskExecAction - un diagnostic qui envoie regarder
    #     la tache alors que la faute est un nom de variable. MESURE ici.
    $acte = New-ScheduledTaskAction -Execute $env:ComSpec -Argument $cible -WorkingDirectory $RACINE
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
    $reglages = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero) `
        -StartWhenAvailable -MultipleInstances IgnoreNew
    Register-ScheduledTask -TaskName $NOM_TACHE -Action $acte -Trigger $trigger `
        -Principal $principal -Settings $reglages `
        -Description 'Lance l agent DeskNode a l ouverture de session. NON ELEVE (dn4-17 / AC5.2).' | Out-Null

    $t = Get-ScheduledTask -TaskName $NOM_TACHE -ErrorAction SilentlyContinue
    if (-not $t) { Stop2 "la tache n'a PAS ete posee."; exit 9 }
    Dire ("tache '" + $NOM_TACHE + "' POSEE | RunLevel=" + $t.Principal.RunLevel + " | etat=" + $t.State)
    Dire ("  cible : " + $env:ComSpec + " " + ($t.Actions | Select-Object -First 1).Arguments)
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
    Dire "(i) l'agent DEJA LANCE n'est pas arrete par ce retrait : 'dn-agent.bat stop'."
    exit 0
}

}
