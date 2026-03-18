@echo off
setlocal

set "ROOT=C:\Users\abhic\Documents\Playground"
set "BACKEND=%ROOT%\backend"
set "FRONTEND=%ROOT%\formsathi"

start "FormSathi Backend" powershell -NoExit -Command "Set-Location '%BACKEND%'; python -m uvicorn app.main:app --reload"
start "FormSathi Frontend" powershell -NoExit -Command "Set-Location '%FRONTEND%'; python -m http.server 5500"

timeout /t 3 /nobreak >nul
start "" http://127.0.0.1:5500/index.html
