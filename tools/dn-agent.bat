@echo off
setlocal EnableExtensions
REM ===========================================================================
REM  dn-agent.bat - lance / arrete l'agent DeskNode DEPUIS WINDOWS   (dn4-17)
REM ===========================================================================
REM  Double-clic = "start". WSL PEUT ETRE ETEINT : ce fichier et dn_agent.py
REM  sont des COPIES LOCALES posees par tools/deployer_tour.sh. On ne passe
REM  JAMAIS par \\wsl.localhost (decision owner n.2 du 2026-08-25).
REM
REM  !!! L'AUTORITE EST LE DEPOT (~/projects/desknode). Ne PAS editer ici.
REM
REM  VERBES
REM    dn-agent.bat                 start  (double-clic)
REM    dn-agent.bat etat            dit tout, ne change RIEN
REM    dn-agent.bat stop            arrete, et le PROUVE en rouvrant le port
REM    dn-agent.bat run  [port] [duree] [temoin]   avant-plan (la tache)
REM    dn-agent.bat exec [port]     avant-plan SANS pre-vol (usage interne)
REM    dn-agent.bat permanence      pose la tache au logon (NON ELEVEE)
REM    dn-agent.bat retirer         retire la tache
REM
REM  !!! AUCUNE CONTINUATION DE LIGNE (accent circonflexe) ICI.
REM      poser-permanence.cmd en porte une, et le depot a paye le piege : en
REM      LF, cmd.exe peut executer une ligne de commande TRONQUEE. Ce fichier
REM      est depose en CRLF par deployer_tour.sh, ET il evite le motif.
REM ===========================================================================

set "DN_DIR=%~dp0"
if "%DN_DIR:~-1%"=="\" set "DN_DIR=%DN_DIR:~0,-1%"
set "DN_PS1=%DN_DIR%\dn_agent_tour.ps1"
set "DN_ENV=%DN_DIR%\dn-agent.env.cmd"
set "DN_LOG=%DN_DIR%\dn-agent.log"
set "DN_OUT=%DN_DIR%\dn-agent.out"
set "PS=powershell -NoProfile -ExecutionPolicy Bypass -File"

set "VERBE=%~1"
if not defined VERBE set "VERBE=start"
set "SERIE=%~2"
if not defined SERIE set "SERIE=COM3"
set "DUREE=%~3"
if not defined DUREE set "DUREE=0"
set "TEMOIN=%~4"

if not exist "%DN_PS1%" goto :SANSPS1

if /I "%VERBE%"=="etat"       goto :ETAT
if /I "%VERBE%"=="stop"       goto :STOP
if /I "%VERBE%"=="permanence" goto :PERM
if /I "%VERBE%"=="retirer"    goto :RETIRER
if /I "%VERBE%"=="start"      goto :START
if /I "%VERBE%"=="run"        goto :RUN
if /I "%VERBE%"=="exec"       goto :EXEC
goto :USAGE

:ETAT
%PS% "%DN_PS1%" etat -Serie %SERIE%
goto :FIN

:STOP
%PS% "%DN_PS1%" stop -Serie %SERIE%
goto :FIN

:PERM
%PS% "%DN_PS1%" permanence -Serie %SERIE%
goto :FIN

:RETIRER
%PS% "%DN_PS1%" retirer -Serie %SERIE%
goto :FIN

:START
REM Le pre-vol s'affiche ICI, dans la fenetre du double-clic : si COM3 est
REM absent, l'owner LE VOIT. C'est ensuite seulement qu'on detache.
set "DN_REGIME=double-clic (detache)"
%PS% "%DN_PS1%" lancer -Serie %SERIE% -Duree %DUREE% %TEMOIN%
goto :FIN

:RUN
REM Avant-plan : c'est ce que la tache au logon appelle. Le pere de
REM python.exe est donc CE cmd.exe, vivant tout le temps du run - c'est ce
REM qui rend la chaine de PID lisible (AC6.6).
set "DN_REGIME=tache au logon (avant-plan)"
%PS% "%DN_PS1%" prevol -Serie %SERIE% -Duree %DUREE% %TEMOIN%
if errorlevel 1 goto :FIN
goto :EXEC

:EXEC
if not exist "%DN_ENV%" goto :SANSENV
call "%DN_ENV%"
if not defined DN_PY goto :SANSENV
REM 2>> et 1>> : on AJOUTE, on ne tronque pas. Le bilan de fin de l'agent
REM (trames emises, erreurs d'envoi, recalages, echo, refus firmware) est le
REM seul instrument qui dit si la liaison va bien : une tache planifiee n'a
REM pas de console, sans cette redirection il serait PERDU. (AC3.6)
"%DN_PY%" "%DN_DIR%\dn_agent.py" %DN_ARGS% 1>>"%DN_OUT%" 2>>"%DN_LOG%"
goto :FIN

:SANSPS1
echo   /!\ dn_agent_tour.ps1 ABSENT a cote de ce .bat.
echo       Redeployer depuis le depot : tools/deployer_tour.sh
exit /b 3

:SANSENV
echo   /!\ dn-agent.env.cmd absent ou vide : le pre-vol n'a pas eu lieu.
echo       Utiliser "dn-agent.bat start" ou "dn-agent.bat run".
exit /b 3

:USAGE
echo   /!\ verbe inconnu : %VERBE%
echo       verbes : start / etat / stop / run / exec / permanence / retirer
exit /b 2

:FIN
exit /b %ERRORLEVEL%
