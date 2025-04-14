@echo off
cd /d "%~dp0"

echo ----------------------------------
echo [1/5] Creating/Activating Virtual Environment...
echo ----------------------------------

IF NOT EXIST "venv\" (
    python -m venv venv
)

call venv\Scripts\activate.bat

echo ----------------------------------
echo [2/5] Installing Dependencies...
echo ----------------------------------

pip install -r requirements.txt

echo ----------------------------------
echo [3/5] Loading Environment Variables from .env...
echo ----------------------------------

REM Load .env variables manually (only simple KEY=VALUE pairs, no quotes/spaces)
for /f "usebackq tokens=1,* delims==" %%A in (.env) do (
    set "%%A=%%B"
)

echo ----------------------------------
echo [4/5] Starting Flask Server...
echo ----------------------------------

start http://127.0.0.1:5000
flask run

echo ----------------------------------
echo [5/5] Press any key to exit...
echo ----------------------------------
pause
