
@echo off

echo Starting Dragon API...

:: Check if python is available
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Could not find python. Please make sure it is installed.
    exit /b 1
)

:: Check if pip is available
where pip >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Could not find pip. Please make sure it is installed.
    exit /b 1
)

cd %~dp0

if not exist "venv" (
    echo Creating virtual environment
    python -m venv venv
)

echo Activating virtual environment
call venv\Scripts\activate.bat

:: Check if "--upgrade" is passed in the arguments
echo %* | find "--upgrade" >nul
if %ERRORLEVEL% eq 0 (
    echo Upgrading dependencies...
    for /r %%i in (requirements.txt) do (
        echo Installing requirements from %%i
        pip install --upgrade -r %%i
    )
    echo Upgraded dependencies. Please restart the application.
    exit /b 0
) else (
    echo Installing dependencies
    for /r %%i in (requirements.txt) do (
        echo Installing requirements from %%i
        pip install -r %%i
    )
)

:: Start the Admin application
echo Starting the Dragon Panel application
echo TODO

:: Start the application
echo Starting the Dragon App
uvicorn main:app --host 0.0.0.0 --port 88 %* --reload