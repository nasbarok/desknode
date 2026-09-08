@echo off
REM Double-cliquez CE fichier apres avoir rouvert votre session.
REM Il ne change RIEN. Il attend ~3 min que l'agent ait de quoi mesurer,
REM puis il ecrit tout dans constat-apres-logon.txt, a cote.
setlocal
set "D=%~dp0"
echo.
echo   Constat dn4-17 en cours... il attend que l'agent ait 190 s de vie.
echo   Ne fermez pas cette fenetre. Elle se signalera toute seule.
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%D%constat-apres-logon.ps1" > "%D%constat-apres-logon.txt" 2>&1
echo.
echo   FINI. Rapport ecrit dans :
echo       %D%constat-apres-logon.txt
echo.
pause
