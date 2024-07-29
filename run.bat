#!/bin/bash

echo "Starting Dragon API..."

# Check if python is available
if command -v python &>/dev/null; then
    PYTHON=python
else
    echo "Could not find python. Please make sure it is installed."
    exit 1
fi

# Check if pip is available
if command -v pip &>/dev/null; then
    PIP=pip
else
    echo "Could not find pip. Please make sure it is installed."
    exit 1
fi

cd "$(dirname "$0")" || exit

if [ ! -d "venv" ]; then
    echo Creating virtual environment
    $PYTHON -m venv venv

    source venv/Scripts/activate

    echo Installing dependencies
    REQUIREMENTS_FILES=$(find . -type f -name 'requirements.txt')
    for FILE in $REQUIREMENTS_FILES; do
        echo "Installing requirements from $FILE"
        $PIP install -r "$FILE" --upgrade
    done
else
    echo Activating virtual environment
    source venv/Scripts/activate
    
    # Check if "--upgrade" is passed in the arguments
    if [[ "$*" =~ "--upgrade" ]]; then
        echo "Upgrading dependencies..."
        REQUIREMENTS_FILES=$(find . -type f -name 'requirements.txt')
        for FILE in $REQUIREMENTS_FILES; do
            echo "Installing requirements from $FILE"
            $PIP install --upgrade -r "$FILE"
        done
        echo "Upgraded dependencies. Please restart the application."
        exit 0
    fi
fi

# Check if Redis is available and start the worker
if [ -n "$REDIS_HOST" ] && [[ "$*" =~ "--worker" ]]; then
    echo Starting the Redis worker
    REDIS_PORT=${REDIS_PORT:-'6379'}
    if ! [[ "$REDIS_PORT" =~ ^[0-9]+$ ]]; then
        echo "Error: REDIS_PORT is not a valid integer: $REDIS_PORT"
        exit 1
    fi
    REDIS_PASSWORD=${REDIS_PASSWORD:-''}
    RQ_WORKER_PID=""
    ## Windows workaround for running multiprocesses
    rq worker task_manager --with-scheduler --url redis://default:$REDIS_PASSWORD@$REDIS_HOST:$REDIS_PORT &
    RQ_WORKER_PID=$!
    trap "echo 'Stopping rq worker'; kill $RQ_WORKER_PID" EXIT
fi

# Start the Admin application
echo Starting the Dragon Panel application
echo TODO

# Start the application
echo "Starting the Dragon App"
uvicorn main:app --host 0.0.0.0 --port 88 "$@" --reload