sudo apt install curl -y

#!/bin/bash

# Check if Zsh is already installed
if command -v zsh >/dev/null 2>&1; then
    echo "Zsh is already installed."
else
    echo "Zsh is not installed. Installing Zsh..."

    # Update package list and install Zsh
    sudo apt update
    sudo apt install -y zsh

    # Verify installation
    if zsh --version >/dev/null 2>&1; then
        echo "Zsh installed successfully."
    else
        echo "Failed to install Zsh."
        exit 1
    fi
fi

# Check if Zsh is already the default shell
current_shell=$(echo $SHELL)
if [[ "$current_shell" == *"zsh"* ]]; then
    echo "Zsh is already the default shell."
else
    echo "Setting Zsh as the default shell..."

    # Set Zsh as default shell
    sudo chsh -s $(which zsh) $USER

    echo "Please log out and log back in to use Zsh as your default shell."
fi
#!/bin/bash

# Function to display messages in green
function display_message {
    echo -e "\033[0;32m$1\033[0m"
}

# Check if Zsh is installed
if command -v zsh >/dev/null 2>&1; then
    display_message "Zsh is already installed."
else
    display_message "Zsh is not installed. Installing Zsh..."
    sudo apt update
    sudo apt install -y zsh

    # Verify Zsh installation
    if zsh --version >/dev/null 2>&1; then
        display_message "Zsh installed successfully."
    else
        display_message "Failed to install Zsh."
        exit 1
    fi
fi

# Check if Tilda is installed
if command -v tilda >/dev/null 2>&1; then
    display_message "Tilda is already installed."
else
    display_message "Tilda is not installed. Installing Tilda..."
    sudo apt install -y tilda

    # Verify Tilda installation
    if command -v tilda >/dev/null 2>&1; then
        display_message "Tilda installed successfully."
    else
        display_message "Failed to install Tilda."
        exit 1
    fi
fi

# Check if tmux is installed
if command -v tmux >/dev/null 2>&1; then
    display_message "Tmux is already installed."
else
    display_message "Tmux is not installed. Installing tmux..."
    sudo apt install -y tmux

    # Verify tmux installation
    if command -v tmux >/dev/null 2>&1; then
        display_message "Tmux installed successfully."
    else
        display_message "Failed to install Tmux."
        exit 1
    fi
fi

# Check if Zsh is already the default shell
current_shell=$(echo $SHELL)
if [[ "$current_shell" == *"zsh"* ]]; then
    display_message "Zsh is already the default shell."
else
    display_message "Setting Zsh as the default shell..."
    sudo chsh -s $(which zsh) $USER
    display_message "Zsh has been set as the default shell. Please log out and log back in."
fi

# Move the configuration files to the home directory
if [ -f "zsh" ]; then
    display_message "Copying zsh to ~/.zsh..."
    mv zsh ~/.zsh
else
    display_message "zsh file not found in the current directory."
fi

if [ -f "zshenv" ]; then
    display_message "Copying zshenv to ~/.zshenv..."
    mv zshenv ~/.zshenv
else
    display_message "zshenv file not found in the current directory."
fi

if [ -f "tmux.conf" ]; then
    display_message "Copying tmux.conf to ~/.tmux.conf..."
    mv tmux.conf ~/.tmux.conf
else
    display_message "tmux.conf file not found in the current directory."
fi

display_message "Setup complete! Please log out and log back in to start using Zsh as the default shell with your configurations."

sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
