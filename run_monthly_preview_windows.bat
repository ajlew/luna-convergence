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

set LUNA_EDITOR_PREVIEW=0
set LUNA_PUBLIC_YEARLY=0
set LUNA_MONTHLY_PREVIEW_BYPASS=1

echo.
echo Starting Luna Private Monthly Preview
echo Build: Luna Daily + Monthly Production Pass v2.9.2
echo Folder: %CD%
echo Payment: BYPASSED FOR MONTHLY REVIEW ONLY
echo Yearly: HIDDEN
echo Open: http://localhost:8514/monthly-preview
echo.

start "" /B cmd /c "timeout /t 3 /nobreak >nul & start \"\" http://localhost:8514/monthly-preview"
streamlit run app.py --server.port 8514
goto :end

:error
echo.
echo Launch failed. Confirm Python 3.10 or newer is installed.
pause

:end
endlocal
