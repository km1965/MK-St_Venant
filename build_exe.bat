@echo off
setlocal
cd /d "%~dp0"

set "APP_NAME=Mk_Stvenant_Allievi_Strickler-Bernoulli"
set "ICON=assets\mk-st-venant-icon.ico"

echo ==========================================================
echo   Build EXE - %APP_NAME%
echo   MK-St_Venant (Allievi / Strickler-Bernoulli)
echo ==========================================================
echo.

REM Utiliser PyInstaller via le Python courant (installe sur la machine)
python -m PyInstaller --noconfirm --clean "%APP_NAME%.spec"
if errorlevel 1 (
    echo.
    echo [ERREUR] Echec du build PyInstaller.
    pause
    exit /b 1
)

echo.
echo [OK] Build termine.
echo Dossier executable : dist\%APP_NAME%\
echo Lanceur : dist\%APP_NAME%\%APP_NAME%.exe
echo.
pause
