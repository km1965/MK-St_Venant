@echo off
title MK-St_Venant - Ingenierie Hydraulique
echo ========================================================
echo   Lancement de MK-St_Venant (CustomTkinter GUI)
echo   Automatisation & Verification des Ventouses et Vidanges
echo ========================================================
echo.
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Une erreur s'est produite lors de l'execution.
    pause
)
