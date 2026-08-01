@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
    set PYTHON_CMD=py
) else (
    set PYTHON_CMD=python
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating Python environment...
    %PYTHON_CMD% -m venv .venv
    if errorlevel 1 goto :error
)

call ".venv\Scripts\activate.bat"
if errorlevel 1 goto :error

python -m pip install --upgrade pip
if errorlevel 1 goto :error

pip install -r requirements.txt
if errorlevel 1 goto :error

echo.
echo Starting Luna Reports
echo Build: Monthly Arc Engine v2.6
echo Folder: %CD%
echo Open: http://localhost:8511/reports
echo.

start "" /B cmd /c "timeout /t 3 /nobreak >nul & start \"\" http://localhost:8511/reports"
streamlit run app.py --server.port 8511
goto :end

:error
echo.
echo Launch failed. Confirm Python 3.10 or newer is installed.
pause

:end
endlocal
