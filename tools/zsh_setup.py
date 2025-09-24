import os
import subprocess
import shutil
import configparser
from InquirerPy import inquirer
from rich import print

def run(cmd, sudo=False):
    if sudo:
        cmd = "sudo " + cmd
    subprocess.run(cmd, shell=True, check=True)

def is_installed(binary):
    return shutil.which(binary) is not None

def install_package(name):
    if not is_installed(name):
        print(f"[bold yellow]Installing {name}...[/bold yellow]")
        run(f"sudo apt install -y {name}", sudo=True)
    else:
        print(f"[green]{name} is already installed.[/green]")

def setup_zsh_default():
    current_shell = os.environ.get("SHELL", "")
    if "zsh" in current_shell:
        print("[green]Zsh is already the default shell.[/green]")
    else:
        print("[bold yellow]Setting Zsh as default shell...[/bold yellow]")
        run(f"chsh -s $(which zsh) {os.environ['USER']}", sudo=True)
        print("[green]Please log out and log back in to apply changes.[/green]")

def install_oh_my_zsh():
    print("[bold cyan]Installing Oh My Zsh...[/bold cyan]")
    run('sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"')

def install_prezto():
    print("[bold cyan]Installing Prezto...[/bold cyan]")
    run("git clone --recursive https://github.com/sorin-ionescu/prezto.git ~/.zprezto")
    run("zsh -c 'setopt EXTENDED_GLOB && for rcfile in ~/.zprezto/runcoms/^README.md(.N); do ln -s $rcfile ~/.${rcfile:t}; done'")

def install_starship():
    print("[bold cyan]Installing Starship prompt...[/bold cyan]")
    run("curl -sS https://starship.rs/install.sh | sh -s -- -y")
    zshrc = os.path.expanduser("~/.zshrc")
    with open(zshrc, "a") as f:
        f.write('\n# Starship prompt\n')
        f.write('eval "$(starship init zsh)"\n')

def copy_dotfile(src_name, dest_name):
    if os.path.exists(src_name):
        dest_path = os.path.expanduser(dest_name)
        if os.path.exists(dest_path):
            backup = dest_path + ".backup"
            print(f"[yellow]Backing up existing {dest_name} to {backup}[/yellow]")
            shutil.move(dest_path, backup)
        print(f"[cyan]Installing {src_name} to {dest_name}[/cyan]")
        shutil.copy(src_name, dest_path)

def main():
    print("[bold]ZSH Shell Setup Tool[/bold]")

    # Install basic tools
    install_package("zsh")
    install_package("tmux")
    install_package("tilda")
    setup_zsh_default()

    choice = inquirer.select(
        message="Choose your Zsh environment:",
        choices=[
            "Oh My Zsh",
            "Prezto",
            "Starship (prompt only)",
            "Skip framework setup"
        ]
    ).execute()

    if choice == "Oh My Zsh":
        install_oh_my_zsh()
    elif choice == "Prezto":
        install_prezto()
    elif choice == "Starship (prompt only)":
        install_starship()

    # Copy configs if available
    copy_dotfile("zshenv", "~/.zshenv")
    copy_dotfile("tmux.conf", "~/.tmux.conf")

    print("\n[bold green]✔ Done! Log out and back in to use your new shell environment.[/bold green]")

if __name__ == "__main__":
    main()
