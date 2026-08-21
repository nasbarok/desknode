<#
=============================================================================
 dn_lhm_tour.ps1 -- POSE ET VERIFIE LA TOUR POUR dn4-8 (LibreHardwareMonitor)
=============================================================================

 ROLE. dn4-8 / D13 : LibreHardwareMonitor tourne en permanence sur la tour et
 `dn_agent.py` LIT ses valeurs. L'agent ne fait AUCUN Ring0 lui-meme.
 Ce script pose cette dependance d'infrastructure, et surtout : IL LA VERIFIE.

 (!) C'EST UN INSTRUMENT, PAS LE PRODUIT. Meme regle que
     `mesure_grandeurs_dn46.py` : ne PAS le faire dependre de `dn_agent.py`,
     et ne PAS faire dependre l'agent de lui. L'agent doit tourner sur une tour
     provisionnee a la main aussi bien que par ce script.

 (!) IL TOURNE SUR LE POWERSHELL DE LA TOUR (5.1), pas en WSL. Depuis WSL :
     powershell.exe -NoProfile -ExecutionPolicy Bypass -File \\wsl.localhost\Ubuntu\home\nasbarok\projects\desknode\tools\dn_lhm_tour.ps1

 EMPLOI
   .\dn_lhm_tour.ps1                          # VERIFIE, ne change RIEN (defaut)
   .\dn_lhm_tour.ps1 -Poser                   # installe ce qui manque + serveur web
   .\dn_lhm_tour.ps1 -Poser -Permanence tache # + tache planifiee au logon, elevee
   .\dn_lhm_tour.ps1 -Retirer                 # retire la tache. NE DESINSTALLE RIEN.
   .\dn_lhm_tour.ps1 -Json                    # sortie machine

 IDEMPOTENT : -Poser rejoue sans dommage. Chaque action dit ce qu'elle a
 trouve AVANT d'agir, et rien n'est fait en silence.

 -----------------------------------------------------------------------------
 CE QUE CE SCRIPT REFUSE DE FAIRE, ET POURQUOI
 -----------------------------------------------------------------------------
 * Il ne conclut JAMAIS "le driver marche" depuis `sc query PawnIO`.
   Un driver qui tourne pendant que LHM n'est PAS eleve donne un arbre SANS
   capteurs Super I/O -- donc sans ventilos boitier ni CPU -- et `sc query`
   dirait RUNNING quand meme. Le seul test qui voit ce defaut-la est
   FONCTIONNEL : y a-t-il au moins un capteur `/lpc/...` dans l'arbre ?
   (mesure dn4-8 du 2026-08-21 : `/lpc/nct6792d/...` sur MSI X99A MPOWER)
 * Il ne conclut JAMAIS "0 tr/min = sonde absente". Une sonde a 0 EXISTE.
   Deux ventilos de cette tour sont a 0, et c'est AC3 (l'oreille de l'owner)
   qui dira si c'est un en-tete non branche ou un ventilo a l'arret.
 * Il ne PUBLIE PAS de duree comme un cout de regime. Les millisecondes qu'il
   imprime sont UN TIR, amorcage compris. Le cout se mesure en AC2, avec son
   critere d'elimination ecrit AVANT.

 -----------------------------------------------------------------------------
 FAITS MESURES LE 2026-08-21 SUR `DESKTOP-08RT3CL` -- utiles a la relecture
 -----------------------------------------------------------------------------
 * winget `LibreHardwareMonitor.LibreHardwareMonitor` 0.9.6 est le build
   .NET FRAMEWORK (portable zip), et il DECLARE `namazso.PawnIO` en dependance.
 * `.NET Framework 4.8.09037` present. `dotnet` present (runtimes 6 et 7) mais
   PAS .NET 10 => le build `.NET.10.zip` ne tournerait pas. (!) La note de
   dn2-2 "dotnet absent de la tour" est REFUTEE ; sa conclusion tient.
 * L'option native "Run On Windows Startup" de LHM cree ELLE-MEME une tache
   planifiee nommee `LibreHardwareMonitor`, RunLevel Highest, LogonType
   InteractiveToken -- MAIS seulement si LHM tourne ELEVE. Sinon elle retombe
   sur HKCU\...\Run, qui n'est PAS eleve : c'est ce qui explique le bug connu
   "l'option revient a off". (source : UI/StartupManager.cs)
   => La tache posee par ce script porte le MEME nom et la MEME action :
      LHM la reconnait comme sa propre option native.
 * `/data.json` en 0.9.6 rend TOUT en chaines LOCALISEES, `RawValue` COMPRIS
   ("34,8 degC", "668 RPM"). `/metrics` rend de vrais nombres, point decimal,
   unites de base. (!) Ne pas se fier a la doc de `master`, qui est en avance.
=============================================================================
#>

[CmdletBinding()]
param(
    [switch] $Poser,
    [ValidateSet('aucune', 'tache')]
    [string] $Permanence = 'aucune',
    [switch] $Retirer,
    [int]    $Port = 8085,
    [switch] $Json
)

$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'

# --- Constantes mesurees / imposees ------------------------------------------
$PKG_LHM    = 'LibreHardwareMonitor.LibreHardwareMonitor'
$PKG_PAWNIO = 'namazso.PawnIO'
$NOM_TACHE  = 'LibreHardwareMonitor'   # (!) le nom EXACT que StartupManager cherche
$CLE_RUN    = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'

$R = [ordered]@{}      # le rapport machine
$script:Anomalies = @()

function Dire([string]$m) { if (-not $Json) { Write-Host $m } }
function Titre([string]$m) { Dire ''; Dire ("=== " + $m + " ===") }
function Note([string]$cle, $val) { $R[$cle] = $val }
function Alerte([string]$m) { $script:Anomalies += $m; Dire ("  /!\ " + $m) }

# (!) LHM rend ses valeurs en chaines LOCALISEES ("43,0 degC" avec le signe degre
#     en UTF-8). Ce script est souvent pilote DEPUIS WSL, et le signe degre s'y
#     casse en "?". Un instrument qui rend du texte abime fait douter de sa mesure
#     pour rien : on desaccentue la SORTIE, jamais la valeur qu'on note.
function Ascii([string]$t) {
    if ($null -eq $t) { return '' }
    $t = $t -replace [char]0x00B0, 'deg'
    return ($t -replace '[^\x20-\x7E]', '')
}

# =============================================================================
# 0. Contexte
# =============================================================================
Titre 'CONTEXTE'
$estEleve = ([Security.Principal.WindowsPrincipal] `
        [Security.Principal.WindowsIdentity]::GetCurrent()
).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
Note 'eleve' $estEleve

$os = Get-CimInstance Win32_OperatingSystem
$cm = Get-CimInstance Win32_BaseBoard
Note 'hote'       $env:COMPUTERNAME
Note 'os'         ($os.Caption + ' build ' + $os.BuildNumber)
Note 'carte_mere' ($cm.Manufacturer + ' ' + $cm.Product)
Note 'powershell' $PSVersionTable.PSVersion.ToString()

Dire ("  hote        : " + $env:COMPUTERNAME)
Dire ("  os          : " + $os.Caption + " build " + $os.BuildNumber)
Dire ("  carte mere  : " + $cm.Manufacturer + " " + $cm.Product)
Dire ("  powershell  : " + $PSVersionTable.PSVersion)
Dire ("  eleve       : " + $estEleve)
if (-not $estEleve) {
    Dire "  (i) NON ELEVE : la verification marche, mais -Poser et -Permanence NE POURRONT PAS agir."
}

# =============================================================================
# 1. Prerequis d'installation
# =============================================================================
Titre 'PREREQUIS'

$winget = (Get-Command winget -ErrorAction SilentlyContinue)
Note 'winget' $(if ($winget) { $winget.Source } else { $null })
Dire ("  winget            : " + $(if ($winget) { $winget.Source } else { 'ABSENT' }))
if (-not $winget) { Alerte "winget est ABSENT : -Poser ne pourra pas installer." }

$ndp = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full' -ErrorAction SilentlyContinue
Note 'net_framework' $(if ($ndp) { $ndp.Version } else { $null })
Dire ("  .NET Framework    : " + $(if ($ndp) { $ndp.Version } else { 'ABSENT' }))
if (-not $ndp) { Alerte "Pas de .NET Framework v4 : le build LHM retenu ne tournerait pas." }

# (!) On regarde .NET 10 SEULEMENT pour dire quel build serait viable -- le build
#     retenu est celui du Framework, et il ne depend pas de `dotnet`.
$dotnet = Get-Command dotnet -ErrorAction SilentlyContinue
$net10 = $false
if ($dotnet) {
    $net10 = [bool](& $dotnet.Source --list-runtimes 2>$null |
        Where-Object { $_ -match '^Microsoft\.WindowsDesktop\.App 10\.' })
}
Note 'dotnet_present' ([bool]$dotnet)
Note 'net10_desktop'  $net10
Dire ("  dotnet            : " + $(if ($dotnet) { 'present' } else { 'absent' }) +
      " | .NET 10 Desktop : " + $(if ($net10) { 'oui' } else { 'non' }))
Dire "  => build retenu   : .NET Framework (LibreHardwareMonitor.zip), (!) pas le .NET.10.zip"

# =============================================================================
# 2. POSE (installation)
# =============================================================================
function Test-PaquetInstalle([string]$id) {
    if (-not $winget) { return $false }
    $s = winget list --id $id --exact --accept-source-agreements 2>&1 | Out-String
    return ($s -match [regex]::Escape($id))
}

if ($Poser) {
    Titre 'POSE'
    if (-not $estEleve) {
        Alerte "-Poser demande sans elevation : PawnIO est un driver noyau, il declenchera une invite UAC."
    }
    foreach ($id in @($PKG_PAWNIO, $PKG_LHM)) {
        if (Test-PaquetInstalle $id) {
            Dire ("  deja installe, rien a faire : " + $id)
        }
        else {
            Dire ("  installation : " + $id + " ...")
            winget install --id $id --exact `
                --accept-package-agreements --accept-source-agreements 2>&1 | Out-String | Out-Null
            if (Test-PaquetInstalle $id) { Dire ("  OK : " + $id) }
            else { Alerte ("ECHEC d'installation : " + $id) }
        }
    }
}

# =============================================================================
# 3. Etat de l'installation
# =============================================================================
Titre 'INSTALLATION'

$svc = Get-Service -Name 'PawnIO' -ErrorAction SilentlyContinue
Note 'pawnio_etat' $(if ($svc) { $svc.Status.ToString() } else { $null })
Dire ("  PawnIO (driver)   : " + $(if ($svc) { $svc.Status } else { 'ABSENT' }))
if (-not $svc) { Alerte "PawnIO ABSENT : sans lui, pas de Super I/O -- donc pas de ventilos boitier/CPU." }
elseif ($svc.Status -ne 'Running') { Alerte ("PawnIO est '" + $svc.Status + "', pas 'Running'.") }

$exe = $null
$racine = Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Packages'
if (Test-Path $racine) {
    $exe = Get-ChildItem -Path $racine -Recurse -Filter 'LibreHardwareMonitor.exe' `
        -ErrorAction SilentlyContinue | Select-Object -First 1
}
Note 'lhm_exe'     $(if ($exe) { $exe.FullName } else { $null })
Note 'lhm_version' $(if ($exe) { $exe.VersionInfo.FileVersion } else { $null })
Dire ("  LHM exe           : " + $(if ($exe) { $exe.FullName } else { 'INTROUVABLE' }))
if ($exe) { Dire ("  LHM version       : " + $exe.VersionInfo.FileVersion) }
else { Alerte "LibreHardwareMonitor.exe introuvable sous WinGet\Packages." }

$proc = @(Get-Process -Name 'LibreHardwareMonitor' -ErrorAction SilentlyContinue)
Note 'lhm_processus' $proc.Count
Dire ("  LHM en cours      : " + $proc.Count + " processus")

# =============================================================================
# 4. Serveur web : activation par la CONFIG (et non par le menu)
# =============================================================================
if ($Poser -and $exe) {
    Titre 'SERVEUR WEB'
    $cfg = [IO.Path]::ChangeExtension($exe.FullName, '.config')
    # (!) `LibreHardwareMonitor.config` -- a NE PAS confondre avec
    #     `LibreHardwareMonitor.exe.config`, qui est la config .NET.
    Dire ("  config LHM        : " + $cfg)

    if ($proc.Count -gt 0) {
        Dire "  fermeture propre de LHM (c'est CloseMainWindow qui lui fait ecrire sa config)..."
        foreach ($p in $proc) { [void]$p.CloseMainWindow() }
        Start-Sleep -Seconds 4
        $reste = @(Get-Process -Name 'LibreHardwareMonitor' -ErrorAction SilentlyContinue)
        if ($reste.Count -gt 0) {
            Alerte "CloseMainWindow n'a pas suffi : Stop-Process. LHM n'ecrira PAS sa config (reglages du tour perdus)."
            $reste | Stop-Process -Force
            Start-Sleep -Seconds 2
        }
    }

    if (Test-Path $cfg) { [xml]$doc = Get-Content -Path $cfg -Raw }
    else {
        Dire "  (i) config absente : creation minimale"
        [xml]$doc = '<?xml version="1.0" encoding="utf-8"?><configuration><appSettings /></configuration>'
    }
    $app = $doc.SelectSingleNode('/configuration/appSettings')
    if ($null -eq $app) { $app = $doc.CreateElement('appSettings'); [void]$doc.DocumentElement.AppendChild($app) }

    function SetCle([string]$k, [string]$v) {
        $n = $app.SelectSingleNode("add[@key='$k']")
        if ($null -eq $n) {
            $n = $doc.CreateElement('add'); [void]$n.SetAttribute('key', $k); [void]$app.AppendChild($n)
            Dire ("    + " + $k + " = " + $v)
        }
        else { Dire ("    ~ " + $k + " = " + $v + "   (etait: " + $n.GetAttribute('value') + ")") }
        [void]$n.SetAttribute('value', $v)
    }
    SetCle 'runWebServerMenuItem'  'true'
    SetCle 'listenerPort'          "$Port"
    SetCle 'authenticationEnabled' 'false'
    $doc.Save($cfg)
    Dire "  config ecrite."

    Start-Process -FilePath $exe.FullName
    Dire "  LHM relance (il herite de l'elevation de CE processus)."
    Start-Sleep -Seconds 8
}

# =============================================================================
# 5. LE TEST QUI COMPTE : l'arbre des capteurs
# =============================================================================
Titre 'SONDES'

$base = "http://localhost:$Port"
$data = $null
foreach ($chemin in @('/data.json', '/metrics')) {
    $t0 = [Diagnostics.Stopwatch]::StartNew()
    try {
        $rep = Invoke-WebRequest -Uri ($base + $chemin) -UseBasicParsing -TimeoutSec 20
        $t0.Stop()
        Dire ("  GET " + $chemin.PadRight(11) + " : HTTP " + $rep.StatusCode +
              " | " + $rep.RawContentLength + " o | " + $t0.ElapsedMilliseconds + " ms (UN TIR, (!) pas un cout de regime)")
        Note ('http' + ($chemin -replace '[^a-z]', '')) $rep.StatusCode
        if ($chemin -eq '/data.json') { $data = $rep.Content | ConvertFrom-Json }
    }
    catch {
        $t0.Stop()
        Dire ("  GET " + $chemin.PadRight(11) + " : ECHEC -- " + $_.Exception.Message)
        Note ('http' + ($chemin -replace '[^a-z]', '')) $null
    }
}

if ($null -eq $data) {
    Alerte "Le serveur web ne repond pas : impossible de conclure sur les sondes. (LHM lance ? -Poser fait ?)"
    Note 'sondes_temperature' $null
    Note 'sondes_ventilateur' $null
    Note 'superio' $null
}
else {
    $plats = New-Object System.Collections.ArrayList
    function Aplatir($n) {
        if ($n.PSObject.Properties.Name -contains 'SensorId') { [void]$plats.Add($n) }
        foreach ($c in $n.Children) { Aplatir $c }
    }
    foreach ($c in $data.Children) { Aplatir $c }

    $temps = @($plats | Where-Object { $_.Type -eq 'Temperature' })
    $fans  = @($plats | Where-Object { $_.Type -eq 'Fan' })
    $lpc   = @($plats | Where-Object { $_.SensorId -like '/lpc/*' })

    Note 'sondes_total'       $plats.Count
    Note 'sondes_temperature' $temps.Count
    Note 'sondes_ventilateur' $fans.Count
    Note 'superio'            ($lpc.Count -gt 0)

    Dire ("  capteurs          : " + $plats.Count + " au total")
    Dire ("  temperatures      : " + $temps.Count)
    Dire ("  ventilateurs      : " + $fans.Count)

    # --- LE test fonctionnel du driver ---
    if ($lpc.Count -gt 0) {
        $puce = ($lpc[0].SensorId -split '/')[2]
        Note 'superio_puce' $puce
        Dire ("  Super I/O         : LU (" + $puce + ", " + $lpc.Count + " capteurs)")
    }
    else {
        Note 'superio_puce' $null
        Alerte "AUCUN capteur /lpc/ : le Super I/O n'est PAS lu. Ventilos boitier et CPU INDISPONIBLES. Cause la plus probable : LHM ne tourne pas ELEVE (le driver, lui, peut tres bien tourner)."
    }

    if ($fans.Count -gt 0) {
        Dire "  --- ventilateurs, tels quels ---"
        foreach ($f in $fans) {
            Dire ("    " + $f.SensorId.PadRight(30) + " " + (Ascii $f.Text).PadRight(10) + " " + (Ascii $f.Value))
        }
        $zero = @($fans | Where-Object { $_.Value -match '^\s*0\s' })
        if ($zero.Count -gt 0) {
            Dire ("  (i) " + $zero.Count + " ventilateur(s) a 0 : la SONDE EXISTE. '0' n'est PAS 'absente'.")
            Dire "      En-tete non branche ou ventilo a l'arret ? => AC3, a l'oreille de l'owner."
        }
    }
    if ($temps.Count -gt 0) {
        $cpu = @($temps | Where-Object { $_.SensorId -like '/intelcpu/*' -or $_.SensorId -like '/amdcpu/*' })
        $pkg = ($cpu | Where-Object { $_.Text -eq 'CPU Package' } | Select-Object -First 1)
        Dire ("  temperatures CPU  : " + $cpu.Count +
              $(if ($pkg) { " (dont " + (Ascii $pkg.Value) + " en CPU Package)" } else { " (!) aucun 'CPU Package'" }))
    }
}

# =============================================================================
# 6. Permanence
# =============================================================================
Titre 'PERMANENCE'

function Get-TacheLhm { Get-ScheduledTask -TaskName $NOM_TACHE -ErrorAction SilentlyContinue }

if ($Retirer) {
    if (-not $estEleve) { Alerte "-Retirer demande sans elevation : impossible." }
    elseif (Get-TacheLhm) {
        Unregister-ScheduledTask -TaskName $NOM_TACHE -Confirm:$false
        Dire "  tache retiree. (!) LHM N'EST PAS DESINSTALLE, PawnIO non plus."
    }
    else { Dire "  aucune tache a retirer." }
}
elseif ($Permanence -eq 'tache') {
    if (-not $exe) { Alerte "Permanence demandee mais LHM introuvable." }
    elseif (-not $estEleve) { Alerte "Permanence 'tache' demande l'elevation (RunLevel Highest)." }
    else {
        if (Get-TacheLhm) { Unregister-ScheduledTask -TaskName $NOM_TACHE -Confirm:$false; Dire "  tache existante retiree (repose a l'identique)." }
        # (!) On reproduit EXACTEMENT ce que StartupManager.CreateTask() fait :
        #     meme nom, RunLevel Highest, LogonType Interactive, action = l'exe.
        #     => LHM affichera son option native comme ACTIVEE.
        $action    = New-ScheduledTaskAction -Execute $exe.FullName
        $trigger   = New-ScheduledTaskTrigger -AtLogOn -User ([Security.Principal.WindowsIdentity]::GetCurrent().Name)
        $principal = New-ScheduledTaskPrincipal -UserId ([Security.Principal.WindowsIdentity]::GetCurrent().Name) `
            -LogonType Interactive -RunLevel Highest
        $reglages  = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries `
            -DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero) -StartWhenAvailable
        Register-ScheduledTask -TaskName $NOM_TACHE -Action $action -Trigger $trigger `
            -Principal $principal -Settings $reglages `
            -Description 'Starts LibreHardwareMonitor on Windows startup. (dn4-8 / D13)' | Out-Null
        Dire "  tache posee."
    }
}

$tache = Get-TacheLhm
Note 'tache_presente' ([bool]$tache)
if ($tache) {
    $niveau = $tache.Principal.RunLevel
    $cible  = ($tache.Actions | Select-Object -First 1).Execute
    Note 'tache_runlevel' "$niveau"
    Note 'tache_cible'    $cible
    Dire ("  tache '" + $NOM_TACHE + "' : PRESENTE | RunLevel=" + $niveau + " | etat=" + $tache.State)
    Dire ("    cible : " + $cible)
    if ("$niveau" -ne 'Highest') {
        Alerte "La tache n'est PAS en RunLevel Highest : LHM demarrera sans elevation, donc SANS Super I/O."
    }
    if ($exe -and $cible -and ($cible.Trim('"') -ne $exe.FullName)) {
        Alerte "La tache ne pointe pas sur l'exe trouve : LHM ne reconnaitra pas son option native."
    }
}
else {
    Dire ("  tache '" + $NOM_TACHE + "' : ABSENTE")
}

$run = (Get-ItemProperty -Path $CLE_RUN -Name $NOM_TACHE -ErrorAction SilentlyContinue)
Note 'cle_run' $(if ($run) { $run.$NOM_TACHE } else { $null })
if ($run) {
    Dire ("  cle HKCU\...\Run  : PRESENTE -> " + $run.$NOM_TACHE)
    Alerte "Une cle Run existe : c'est le repli NON ELEVE de LHM. Elle lancerait LHM sans Super I/O, en doublon de la tache."
}

if (-not $tache -and -not $run) {
    Dire "  (i) AUCUNE permanence : LHM ne redemarrera pas tout seul. C'est une DECISION OWNER, pas un oubli."
}

# =============================================================================
# 7. Defender
# =============================================================================
Titre 'DEFENDER'
try {
    $depuis = (Get-Date).AddHours(-1)
    $det = @(Get-MpThreatDetection -ErrorAction Stop | Where-Object { $_.InitialDetectionTime -gt $depuis })
    Note 'defender_detections_1h' $det.Count
    Dire ("  detections (1 h)  : " + $det.Count)
    if ($det.Count -gt 0) {
        Alerte "Defender a detecte quelque chose dans la derniere heure : verifier que le driver n'est pas en quarantaine."
        foreach ($d in $det) { Dire ("    " + $d.InitialDetectionTime + " : " + ($d.Resources -join ', ')) }
    }
}
catch {
    Note 'defender_detections_1h' $null
    Dire "  (i) Get-MpThreatDetection indisponible : NON VERIFIE (et ce n'est pas 'aucune detection')."
}

# =============================================================================
# 8. Verdict
# =============================================================================
Titre 'VERDICT'
$pret = ($R['pawnio_etat'] -eq 'Running') -and ($R['superio'] -eq $true) -and
        ($R['sondes_ventilateur'] -gt 0) -and ($R['httpdatajson'] -eq 200)
Note 'pret_pour_agent' $pret
Note 'anomalies' $script:Anomalies

if ($pret) { Dire "  LA TOUR EXPOSE SES SONDES : driver charge, Super I/O lu, ventilateurs vus, interface repond." }
else { Dire "  LA TOUR N'EST PAS PRETE. Voir les /!\ ci-dessus." }

if (-not $R['tache_presente'] -and -not $R['cle_run']) {
    Dire "  (i) PERMANENCE NON POSEE : au prochain redemarrage, il n'y aura plus rien."
    Dire "      => .\dn_lhm_tour.ps1 -Permanence tache   (en administrateur)"
}
if ($script:Anomalies.Count -gt 0) {
    Dire ("  " + $script:Anomalies.Count + " anomalie(s) relevee(s).")
}
Dire ""
Dire "  (!) LA PERMANENCE NE SE PROUVE PAS PAR CETTE SORTIE : elle se prouve en"
Dire "      REDEMARRANT LA TOUR et en rejouant ce script SANS rien lancer a la main."

if ($Json) { $R | ConvertTo-Json -Depth 4 }
exit $(if ($pret) { 0 } else { 1 })
