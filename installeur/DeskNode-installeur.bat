@echo off
setlocal EnableExtensions
REM ===========================================================================
REM  DeskNode-installeur.bat - LE SEUL POINT D'ENTREE               (dn7-1)
REM ===========================================================================
REM  Double-clic = la page d'installation s'ouvre dans le navigateur, servie
REM  depuis CETTE machine sur une adresse en http://127.0.0.1:<port tire>.
REM
REM  VERBES
REM    DeskNode-installeur.bat            sert la page et l'ouvre
REM    DeskNode-installeur.bat verifier   pre-vol SEUL, puis sort avec son code
REM
REM  !!! POURQUOI UN .bat ET **PAS** UN .ps1 - CE N'EST PAS UNE PREFERENCE.
REM      MESURE le 2026-09-08 sur la machine de reference : Get-ExecutionPolicy
REM      rend `Restricted`, et les CINQ portees sont `Undefined`. Un .ps1
REM      double-clique est donc REFUSE, Marque du Web ou pas. Le depot porte
REM      deja la parade et elle est eprouvee : tools/dn-agent.bat l.41 lance
REM      PowerShell en -NoProfile -ExecutionPolicy Bypass -File. On l'IMITE.
REM      !!! Ce drapeau porte sur le processus lance ICI et ne change RIEN a la
REM      machine : aucune politique n'est ecrite, rien n'est installe.
REM
REM  !!! AUCUNE ELEVATION, ET C'EST UNE EXIGENCE, PAS UN OUBLI. Rien de ce que
REM      cet installeur fait n'a besoin de droits administrateur : servir un
REM      port haut de la boucle locale, non ; arreter l'agent (un fichier pose
REM      a cote de lui), non ; retirer une tache planifiee POSEE EN SESSION
REM      UTILISATEUR, non. L'outil appele pose sa tache en RunLevel Limited et
REM      traite le contraire comme un DEFAUT : un installeur eleve ferait
REM      echouer l'outil qui existe deja.
REM
REM  !!! SI CE FICHIER A ETE TELECHARGE, Windows lui pose la Marque du Web et
REM      peut afficher " Fichier ouvert - Avertissement de securite ". LE GESTE
REM      QUI LEVE CA : clic droit sur le fichier > Proprietes > cocher
REM      " Debloquer " en bas de l'onglet General > OK. C'est tout, et ca ne
REM      demande aucun droit administrateur.
REM
REM  !!! AUCUNE CONTINUATION DE LIGNE (accent circonflexe) ICI, et ce fichier
REM      est en CRLF : en LF, cmd.exe peut executer une ligne TRONQUEE. Le
REM      depot a deja paye ce piege (voir tools/dn-agent.bat l.29-32).
REM ===========================================================================

set "DN_DIR=%~dp0"
if "%DN_DIR:~-1%"=="\" set "DN_DIR=%DN_DIR:~0,-1%"
set "DN_PY_SCRIPT=%DN_DIR%\dn_installeur.py"
set "DN_PAGE=%DN_DIR%\index.html"

if not exist "%DN_PY_SCRIPT%" goto :SANSSCRIPT
if not exist "%DN_PAGE%" goto :SANSPAGE

REM -- Trouver Python : d'abord le lanceur `py -3`, ensuite `python`. --------
REM !!! AUCUN BLOC ENTRE PARENTHESES ICI : dans un bloc, cmd.exe developpe les
REM     variables A L'ANALYSE, donc un `set` suivi d'un test dans le MEME bloc
REM     lit la valeur d'AVANT. On enchaine des `goto`, comme dn-agent.bat.
set "PY="
py -3 -c "import sys" >nul 2>nul
if not errorlevel 1 set "PY=py -3"
if defined PY goto :PYTROUVE
python -c "import sys" >nul 2>nul
if not errorlevel 1 set "PY=python"
:PYTROUVE
if not defined PY goto :SANSPYTHON

set "VERBE=%~1"
if /I "%VERBE%"=="verifier" goto :VERIFIER
if defined VERBE goto :USAGE

%PY% "%DN_PY_SCRIPT%"
set "RC=%ERRORLEVEL%"
goto :FIN

:VERIFIER
REM Le pre-vol SEUL : il dit ce qui manque, il donne le geste, et il rend un
REM code de retour NON NUL si une dependance de l'agent manque (6). C'est
REM l'instrument mecanique de l'ecart declare, jouable sans ouvrir de fenetre.
%PY% "%DN_PY_SCRIPT%" --verifier
set "RC=%ERRORLEVEL%"
goto :FIN

:SANSPYTHON
echo.
echo   /!\ PYTHON 3 EST INTROUVABLE SUR CETTE MACHINE.
echo.
echo       Ce n'est pas une panne de DeskNode : c'est un ECART DECLARE de
echo       cette version. Tant que l'agent n'est pas livre en executable
echo       autonome, il faut Python 3.
echo.
echo       LE GESTE, EXACTEMENT :
echo         1. Ouvrir https://www.python.org/downloads/windows/
echo         2. Telecharger Python 3 (Windows installer, 64-bit)
echo         3. Dans la premiere fenetre de l'installeur, COCHER
echo            " Add python.exe to PATH " AVANT de cliquer Install
echo         4. Fermer cette fenetre, puis relancer ce fichier
echo.
echo       Porteur du retour a un seul telechargement : l'agent en
echo       executable autonome, prevu en V0.2.
echo.
set "RC=3"
goto :FIN

:SANSSCRIPT
echo.
echo   /!\ dn_installeur.py ABSENT a cote de ce fichier.
echo       Le dossier " installeur " est incomplet : re-telecharger ou
echo       re-cloner le depot, et relancer ce fichier depuis ce dossier.
echo.
set "RC=3"
goto :FIN

:SANSPAGE
echo.
echo   /!\ index.html ABSENT a cote de ce fichier.
echo       Le dossier " installeur " est incomplet : re-telecharger ou
echo       re-cloner le depot, et relancer ce fichier depuis ce dossier.
echo.
set "RC=3"
goto :FIN

:USAGE
echo.
echo   /!\ argument inconnu : %VERBE%
echo       emplois : DeskNode-installeur.bat            (sert la page)
echo                 DeskNode-installeur.bat verifier   (pre-vol seul)
echo.
set "RC=2"
goto :FIN

:FIN
if not defined RC set "RC=%ERRORLEVEL%"
REM ===========================================================================
REM  DOUBLE-CLIC : ON S'ARRETE POUR QUE LE MESSAGE SOIT LISIBLE. La garde est
REM  la meme que celle de tools/dn-agent.bat, et pour la meme raison mesuree :
REM  " pas pu voir, la fenetre se referme direct ". On n'attend QUE si aucun
REM  argument n'a ete passe ET si la ligne de commande porte ce fichier -
REM  c'est-a-dire exactement le double-clic.
REM ===========================================================================
if not "%~1"=="" goto :SORTIE
echo %cmdcmdline% | find /i "%~nx0" >nul || goto :SORTIE
echo.
echo   (code de retour : %RC%)
pause
:SORTIE
exit /b %RC%
