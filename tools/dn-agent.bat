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
REM    dn-agent.bat exec            avant-plan SANS pre-vol (usage interne)
REM                                 !!! IL N'ACCEPTE PAS DE PORT. Corrige le
REM                                 2026-08-26 : l'aide annoncait "exec [port]"
REM                                 alors que :EXEC ne lit JAMAIS %SERIE% - il
REM                                 rejoue les arguments du DERNIER pre-vol,
REM                                 ecrits dans dn-agent.env.cmd. Un
REM                                 "exec COM7" partait donc sur COM3, en
REM                                 silence. Le port se choisit au pre-vol :
REM                                 "dn-agent.bat start COM7" ou "run COM7".
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
REM Les arguments 3 et 4 (duree, temoin) sont TRANSMIS : c'est la tache qui
REM porte le regime, et le temoin en fait partie. Sans ca, la cible posee
REM aurait dit autre chose que ce que l'appel demandait.
%PS% "%DN_PS1%" permanence -Serie %SERIE% -Duree %DUREE% %TEMOIN%
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

REM ===========================================================================
REM  !!! REVUE DU 2026-08-26 - CES TROIS SORTIES FAISAIENT `exit /b` DIRECTEMENT
REM      ET COURT-CIRCUITAIENT :FIN, DONC LE `pause` DU DOUBLE-CLIC.
REM      :SANSPS1 est teste AVANT le dispatch de verbe : un double-clic sur un
REM      deploiement incomplet imprimait "Redeployer depuis le depot" et
REM      REFERMAIT LA FENETRE - c'est EXACTEMENT le constat owner qui a motive
REM      le correctif du pause : "pas pu voir, la fenetre se referme direct".
REM      Un message qu'on ne peut pas lire n'est pas un message.
REM  => Elles passent toutes par :FIN, qui porte la garde double.
REM ===========================================================================
:SANSPS1
echo   /!\ dn_agent_tour.ps1 ABSENT a cote de ce .bat.
echo       Redeployer depuis le depot : tools/deployer_tour.sh
set "RC=3"
goto :FIN

:SANSENV
echo   /!\ dn-agent.env.cmd absent ou vide : le pre-vol n'a pas eu lieu.
echo       Utiliser "dn-agent.bat start" ou "dn-agent.bat run".
set "RC=3"
goto :FIN

:USAGE
echo   /!\ verbe inconnu : %VERBE%
echo       verbes : start / etat / stop / run / exec / permanence / retirer
set "RC=2"
goto :FIN

:FIN
REM  RC peut avoir ete pose par :SANSPS1 / :SANSENV / :USAGE (revue 2026-08-26).
REM  Sinon il vaut le code de la derniere commande.
if not defined RC set "RC=%ERRORLEVEL%"
REM ===========================================================================
REM  DOUBLE-CLIC : ON S'ARRETE POUR QUE L'OWNER PUISSE LIRE.
REM  Constat owner du 2026-08-26 : " pas pu voir, la fenetre se referme
REM  direct ". Un outil dont on ne peut pas lire la reponse n'est pas un
REM  outil - et la reponse qu'il donnait la etait justement le temoin
REM  anti-doublon (" DEJA LANCE ... Aucun second process ").
REM  !!! LA GARDE EST DOUBLE, ET C'EST OBLIGATOIRE : la tache au logon lance
REM      " dn-agent.bat run COM3 0 -Temoin " via cmd /c, donc %cmdcmdline%
REM      CONTIENT le chemin du .bat. Un `pause` la ferait attendre POUR
REM      TOUJOURS. On n'attend donc que si, EN PLUS, aucun argument n'a ete
REM      passe - ce qui est exactement le double-clic.
REM ===========================================================================
if not "%~1"=="" goto :SORTIE
echo %cmdcmdline% | find /i "%~nx0" >nul || goto :SORTIE
echo.
echo   (code de retour : %RC%)
pause
:SORTIE
exit /b %RC%
