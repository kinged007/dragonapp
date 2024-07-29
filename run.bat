
@echo off
setlocal
setlocal enabledelayedexpansion

:: Check if the .env file exists
if not exist ".env" (
    echo Error: .env file not found.
    exit /b 1
)

:: Load environment variables from .env file
set PROXY=
for /f "delims=" %%a in ('type .env ^| findstr /B "PROXY= REDIS_HOST="') do set %%a

:: Check if PROXY has a value
if not "!PROXY!"=="" (
    set PIP_PROXY=--proxy !PROXY!
) else (
    set PIP_PROXY=
)

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

    echo Activating virtual environment
    call venv\Scripts\activate.bat

    echo Installing dependencies
    
    for /r %%i in (requirements.txt) do (
        :: Check if 'requirements.txt' exists in the directory
        if exist "%%i" (
            echo Installing requirements from %%i
            pip install -r "%%i" !PIP_PROXY!
        )

    )

) else (
    
    echo Activating virtual environment
    call venv\Scripts\activate.bat

)


:: Check if "--upgrade" is passed in the arguments
echo %* | find "--upgrade" >nul
if %ERRORLEVEL% equ 0 (
    echo Upgrading dependencies...

    for /r %%i in (requirements.txt) do (
        :: Check if 'requirements.txt' exists in the directory
        if exist "%%i" (
            echo Upgrading requirements from %%i
            pip install --upgrade -r "%%i" !PIP_PROXY!
        )
    )

    echo Upgraded dependencies. Please restart the application.
    exit /b 0

) 


:: Check if Redis is available and start the worker
if defined REDIS_HOST (
    echo Argument: %1
    if "%~1"=="--worker" (
        echo Starting the Redis worker
        :: Default REDIS_PORT to 6379 if not set
        if not defined REDIS_PORT set REDIS_PORT=6379

        :: Check if REDIS_PORT is a valid integer
        echo %REDIS_PORT%| findstr /r "^[0-9][0-9]*$" >nul
        if errorlevel 1 (
            echo Error: REDIS_PORT is not a valid integer: %REDIS_PORT%
            exit /b 1
        )

        :: Default REDIS_PASSWORD to empty if not set
        if not defined REDIS_PASSWORD set REDIS_PASSWORD=

        :: MacOS workaround not applicable in Windows
        :: Start rq worker (adjust command as needed for Windows environment)
        start rq worker task_manager --with-scheduler --url redis://default:%REDIS_PASSWORD%@%REDIS_HOST%:%REDIS_PORT%
        :: Windows does not support trapping signals in the same way as Unix shells
        :: Manual cleanup may be required
    )
)

:: Start the Admin application
echo Starting the Dragon Panel application
echo TODO
:: Start the application
echo Starting the Dragon App
uvicorn main:app --host 0.0.0.0 --port 88 %* --reload !PIP_PROXY!