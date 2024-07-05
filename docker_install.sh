#!/bin/bash

echo "Installing Requirements for Docker..."

# Since we are using a python:3.10 image, we can safely assume pip is available as 'pip'
# and Python is available as 'python'.

cd "$(dirname "$0")" || exit

# echo "Installing/Upgrading dependencies from the main requirements.txt"
# pip install --no-cache-dir -r requirements.txt --upgrade

echo "Installing/Upgrading dependencies from requirements.txt files"
REQUIREMENTS_FILES=$(find . -type f -name 'requirements.txt')
for FILE in $REQUIREMENTS_FILES; do
    echo "Installing requirements from $FILE"
    pip install --no-cache-dir -r $FILE --upgrade
done

echo "Done. You can now start the Docker container."