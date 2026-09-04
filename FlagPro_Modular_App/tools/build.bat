@echo off
chcp 65001 > nul
echo ========================================================
echo   FlagPro Modular App - Bundler
echo ========================================================
python "%~dp0bundler.py"
echo.
pause
