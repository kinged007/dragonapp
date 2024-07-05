#!/bin/bash

echo "Starting Dragon API..."

# if ! command -v python3 &> /dev/null;
# then
#     echo Python3 is not installed
#     exit 1
# fi

# Check if python3 is available
if command -v python3 &>/dev/null; then
    PYTHON=python3
# Check if python is available
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo "Could not find python or python3. Please make sure they are installed."
    exit 1
fi

# Check if pip3 is available
if command -v pip3 &>/dev/null; then
    PIP=pip3
# Check if pip is available
elif command -v pip &>/dev/null; then
    PIP=pip
else
    echo "Could not find pip or pip3. Please make sure they are installed."
    exit 1
fi

cd "$(dirname "$0")" || exit

if [ ! -d "venv" ];
then
    echo Creating virtual environment
    $PYTHON -m venv venv

    . venv/bin/activate

    echo Installing dependencies
    REQUIREMENTS_FILES=$(find . -type f -name 'requirements.txt')
    # $PIP install -r requirements.txt --upgrade
    for FILE in $REQUIREMENTS_FILES; do
        echo "Installing requirements from $FILE"
        $PIP install -r $FILE --upgrade
    done
    
    # $PIP install -r vendor/gpt-researcher/requirements.txt --upgrade
    
else

    echo Activating virtual environment
    . venv/bin/activate
    
    # Check if "--upgrade" is passed in the arguments
    if [[ "${@}" =~ "--upgrade" ]]; then
        echo "Upgrading dependencies..."
        # $PIP install --upgrade -r requirements.txt
        REQUIREMENTS_FILES=$(find . -type f -name 'requirements.txt')
        for FILE in $REQUIREMENTS_FILES; do
            echo "Installing requirements from $FILE"
            $PIP install --upgrade -r $FILE
        done
        # $PIP install --upgrade -r vendor/gpt-researcher/requirements.txt
        echo "Upgraded dependencies. Please restart the application."
        exit 0
    fi
fi

# Check if Redis is available and start the worker
if [ -n "$REDIS_HOST" ] && [[ "${@}" =~ "--worker" ]]; then
    echo Starting the Redis worker
    # echo "$REDIS_HOST $REDIS_PORT $REDIS_PASSWORD"
    REDIS_PORT=${REDIS_PORT:-'6379'}
    if ! [[ "$REDIS_PORT" =~ ^[0-9]+$ ]]; then
        echo "Error: REDIS_PORT is not a valid integer: $REDIS_PORT"
        exit 1
    fi
    REDIS_PASSWORD=${REDIS_PASSWORD:-''}
    RQ_WORKER_PID=""
    ## MacOS workaround for running multiprocesses
    export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
    rq worker task_manager --with-scheduler --url redis://default:$REDIS_PASSWORD@$REDIS_HOST:$REDIS_PORT &
    RQ_WORKER_PID=$!
    trap "echo 'Stopping rq worker'; kill $RQ_WORKER_PID" EXIT
fi

# Start the Admin application
echo Starting the Dragon Panel application
echo TODO

# Start the application
echo "Starting the Dragon App"
# $PYTHON main.py "$@"
uvicorn main:app --host 0.0.0.0 --port 88 "$@" --reload
