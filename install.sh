#!/bin/bash

# Path to your run.sh script
RUN_SCRIPT_PATH="./run.sh"

# Make the run.sh script executable
chmod +x $RUN_SCRIPT_PATH

# Check the default shell
if [[ $SHELL == *"zsh"* ]]; then
    # Add the alias to the .zshrc file
    echo "alias dragon='bash $RUN_SCRIPT_PATH'" >> ~/.zshrc
    # Reload the .zshrc file
    source ~/.zshrc
elif [[ $SHELL == *"bash"* ]]; then
    # Add the alias to the .bashrc file
    echo "alias dragon='bash $RUN_SCRIPT_PATH'" >> ~/.bashrc
    # Reload the .bashrc file
    source ~/.bashrc
fi

echo "Installation complete. You can now use the 'dragon' command to run your app."