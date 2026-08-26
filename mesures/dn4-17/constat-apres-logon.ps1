# =============================================================================
#  constat-apres-logon.ps1 - LE TEMOIN DE dn4-17 (AC5.6 + AC6.3 + AC6.6)
# =============================================================================
#  L'AUTORITE EST LE DEPOT : ~/projects/desknode/mesures/dn4-17/
#  Copie sur H: pour etre double-cliquable. Ne PAS l'editer ici.
#
#  Il ne CHANGE RIEN. Il attend que l'agent ait 190 s de vie, puis il ecrit
#  tout ce qu'il faut pour prouver :
#    - que c'est bien LA TACHE AU LOGON qui a lance l'agent (chaine de PID) ;
#    - dans quel regime le chiffre de cout a ete pris (WSL, LHM, coeurs) ;
#    - la serie complete du temoin, au MEME RANG que -23.
# =============================================================================
$ErrorActionPreference = 'Continue'
$D    = 'H:\dev\projets\desknode'
$LOG  = Join-Path $D 'dn-agent.log'
$NOM  = 'DeskNode agent'

function T($m) { Write-Output ""; Write-Output ("=== " + $m + " ===") }

Write-Output ("########## CONSTAT dn4-17 - " + (Get-Date -Format 'yyyy-MM-ddTHH:mm:ssK') + " ##########")

T 'WSL - est-il ETEINT ?'
$w = & wsl.exe -l --running 2>&1
$w | ForEach-Object { $_ -replace "`0", '' }

T 'LA TACHE'
$t = Get-ScheduledTask -TaskName $NOM -ErrorAction SilentlyContinue
if (-not $t) { Write-Output "  ABSENTE" } else {
  Write-Output ("  etat=" + $t.State + "  RunLevel=" + $t.Principal.RunLevel)
  Write-Output ("  cible : " + ($t.Actions | Select-Object -First 1).Execute + " " + ($t.Actions | Select-Object -First 1).Arguments)
  $i = $t | Get-ScheduledTaskInfo
  Write-Output ("  LastRunTime=" + $i.LastRunTime + "  LastTaskResult=" + $i.LastTaskResult)
}
$engine = $null
try {
  $svc = New-Object -ComObject Schedule.Service; $svc.Connect()
  foreach ($r in $svc.GetRunningTasks(0)) {
    if ($r.Name -eq $NOM) { $engine = $r.EnginePID; Write-Output ("  EN COURS - EnginePID=" + $r.EnginePID) }
  }
} catch { Write-Output ("  (GetRunningTasks indisponible : " + $_.Exception.Message + ")") }
if (-not $engine) { Write-Output "  (la tache n'est pas listee 'en cours')" }

T 'ON ATTEND QUE L AGENT AIT 190 s DE VIE (le rang 180 s doit exister)'
$py = $null
for ($k = 0; $k -lt 60; $k++) {
  $py = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
          Where-Object { $_.CommandLine -and ($_.CommandLine -match 'dn_agent\.py') }) | Select-Object -First 1
  if ($py) {
    $age = ((Get-Date) - $py.CreationDate).TotalSeconds
    Write-Output ("  PID=" + $py.ProcessId + "  age=" + [int]$age + " s")
    if ($age -ge 190) { break }
  } else { Write-Output "  (aucun agent vivant)" }
  Start-Sleep -Seconds 15
}

T 'LA CHAINE DE PID - AC6.6 : le process mesure est-il celui que LA TACHE a lance ?'
if (-not $py) { Write-Output "  AUCUN AGENT : rien a prouver." } else {
  $n = $py; $prof = 0
  while ($n -and $prof -lt 6) {
    Write-Output ("  [" + $prof + "] PID=" + $n.ProcessId + "  " + $n.Name + "  <- pere " + $n.ParentProcessId)
    if ($n.CommandLine) { Write-Output ("       " + $n.CommandLine) }
    if ($engine -and $n.ProcessId -eq $engine) { Write-Output "       ^^^ C'EST L ENGINE DE LA TACHE" }
    $n = Get-CimInstance Win32_Process -Filter ("ProcessId=" + $n.ParentProcessId) -ErrorAction SilentlyContinue
    $prof++
  }
  if ($engine) { Write-Output ("  EnginePID de la tache = " + $engine) }
}

T 'LE REGIME'
Write-Output ("  coeurs logiques : " + $env:NUMBER_OF_PROCESSORS)
$n = @([System.IO.Ports.SerialPort]::GetPortNames())
Write-Output ("  ports serie : " + $(if ($n.Count) { $n -join ',' } else { '(aucun)' }))
$lhm = @(Get-Process LibreHardwareMonitor -ErrorAction SilentlyContinue)
Write-Output ("  LHM : " + $lhm.Count + " processus")
try {
  $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8085/data.json' -TimeoutSec 3 -UseBasicParsing
  Write-Output ("  LHM HTTP : " + $r.StatusCode + " (" + $r.RawContentLength + " o)")
} catch { Write-Output ("  LHM HTTP : ECHEC - " + $_.Exception.Message) }
Write-Output "  --- PROVENANCE.txt ---"
Get-Content (Join-Path $D 'PROVENANCE.txt') -TotalCount 8 | ForEach-Object { Write-Output ("  " + $_) }
Write-Output "  --- marqueur de lancement ---"
if (Test-Path (Join-Path $D 'dn-agent.started')) {
  Get-Content (Join-Path $D 'dn-agent.started') | ForEach-Object { Write-Output ("  " + $_) }
} else { Write-Output "  (absent)" }

T 'LA SERIE DU TEMOIN - AC6.2 : tous les rangs, pas seulement le dernier'
if (Test-Path $LOG) {
  Get-Content $LOG | Where-Object { $_ -match 'temoin|cumul' } | ForEach-Object { Write-Output ("  " + $_) }
} else { Write-Output "  (journal absent)" }

T 'LE JOURNAL, FIN'
if (Test-Path $LOG) {
  Write-Output ("  taille : " + (Get-Item $LOG).Length + " o")
  Get-Content $LOG -Tail 25 | ForEach-Object { Write-Output ("  " + $_) }
}
Write-Output ""
Write-Output "########## FIN DU CONSTAT ##########"
