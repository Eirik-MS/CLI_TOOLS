import os
import subprocess
import shutil
import json
import configparser
import urllib.request
from pathlib import Path
from InquirerPy import inquirer
from InquirerPy.separator import Separator
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
import argparse

# === Config ===
CONFIG_FILE = "./config/usb_tool_default.conf"
ICON_URLS = {
    "ubuntu": "https://assets.ubuntu.com/v1/29985a98-ubuntu-logo32.png",
    "kali": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6b/Kali-dragon-icon.svg/256px-Kali-dragon-icon.svg.png",
    "windows": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5f/Windows_logo_-_2021.svg/256px-Windows_logo_-_2021.svg.png"
}
VENTOY_ICON_DIR = "ventoy/icons"
MOUNT_VENTOY = "/mnt/ventoy"
MOUNT_KALI = "/mnt/kali_persistence"
MOUNT_WTG = "/mnt/wtg"

def run_cmd(cmd, sudo=False):
    if sudo:
        cmd = "sudo " + cmd
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}\n{result.stderr}")
    return result.stdout.strip()

def get_removable_drives():
    drives = []
    output = run_cmd("lsblk -J -o NAME,RM,SIZE,MODEL")
    data = json.loads(output)
    for device in data['blockdevices']:
        if device['rm'] == True and not device['name'].startswith("loop"):
            drives.append({
                "name": device["name"],
                "size": device["size"],
                "model": device.get("model", ""),
                "path": f"/dev/{device['name']}"
            })
    return drives

def get_file(prompt_text, default=None):
    if default and os.path.isfile(default):
        return default
    while True:
        path = inquirer.filepath(message=prompt_text).execute()
        if os.path.isfile(path):
            return path
        else:
            print("❌ Invalid file path. Try again.")

def get_disk_size_gb(device_path):
    size_str = run_cmd(f"lsblk -bno SIZE {device_path}")
    return int(size_str) / (1024**3)

def download_file(url, dest):
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), BarColumn(), TimeRemainingColumn()) as progress:
        task = progress.add_task(f"Downloading {os.path.basename(dest)}", total=None)
        urllib.request.urlretrieve(url, dest)
        progress.update(task, completed=1)

def install_ventoy(usb_dev):
    run_cmd("wget -qO- https://github.com/ventoy/Ventoy/releases/latest/download/ventoy-x86_64.tar.gz | tar xz")
    ventoy_folder = next(Path('.').glob('ventoy-*'))
    os.chdir(ventoy_folder)
    run_cmd(f"./Ventoy2Disk.sh -i {usb_dev} -y", sudo=True)
    os.chdir("..")
    return f"{usb_dev}1"

def mount_partition(partition, mount_point):
    os.makedirs(mount_point, exist_ok=True)
    run_cmd(f"mount {partition} {mount_point}", sudo=True)

def unmount_partition(mount_point):
    run_cmd(f"umount {mount_point}", sudo=True)

def create_partition(usb_dev, part_num, size_gb, type_code):
    script = f"""
n
p
{part_num}

+{size_gb}G
t
{part_num}
{type_code}
w
"""
    run_cmd(f"echo '{script}' | fdisk {usb_dev}", sudo=True)

def format_partition(partition, fs_type, label):
    if fs_type == "ext4":
        run_cmd(f"mkfs.ext4 -L {label} {partition}", sudo=True)
    elif fs_type == "ntfs":
        run_cmd(f"mkfs.ntfs -f -L {label} {partition}", sudo=True)

def setup_kali_persistence(partition):
    run_cmd(f"mkfs.ext4 -L persistence {partition}", sudo=True)
    mount_partition(partition, MOUNT_KALI)
    run_cmd('echo "/ union" | sudo tee /mnt/kali_persistence/persistence.conf > /dev/null', sudo=True)
    unmount_partition(MOUNT_KALI)

def copy_with_progress(src, dst):
    total = os.path.getsize(src)
    with Progress(SpinnerColumn(), BarColumn(), "[progress.percentage]{task.percentage:>3.1f}%", TimeRemainingColumn()) as progress:
        task = progress.add_task(f"Copying {os.path.basename(src)}...", total=total)
        with open(src, 'rb') as fsrc, open(dst, 'wb') as fdst:
            while chunk := fsrc.read(1024 * 1024):
                fdst.write(chunk)
                progress.update(task, advance=len(chunk))

def setup_ventoy_json(mount_dir, iso_names):
    ventoy_config = {
        "theme": {
            "gfxmode": "1024x768"
        },
        "image_class": [],
        "theme_legacy": {
            "classes": {}
        }
    }

    for name in iso_names:
        key = Path(name).stem.lower()
        icon_path = f"/ventoy/icons/{key}.png"
        ventoy_config["image_class"].append({"image": f"/{name}", "class": key})
        ventoy_config["theme_legacy"]["classes"][key] = {"icon": icon_path}

    icon_dir = os.path.join(mount_dir, "ventoy", "icons")
    os.makedirs(icon_dir, exist_ok=True)
    for key, url in ICON_URLS.items():
        icon_file = os.path.join(icon_dir, f"{key}.png")
        if not os.path.exists(icon_file):
            download_file(url, icon_file)

    with open(os.path.join(mount_dir, "ventoy", "ventoy.json"), "w") as f:
        json.dump(ventoy_config, f, indent=4)

def load_config():
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
        paths = config['paths']
        urls = config['urls']
        part = config['partition']
        return {
            "paths": dict(paths),
            "urls": dict(urls),
            "kali_size": int(part.get("kali_size_gb", 12)),
            "wtg_size": int(part.get("wtg_size_gb", 32))
        }
    return {}

def ensure_file(path, url):
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        download_file(url, path)
    return path

def main(headless=False):
    config = load_config()

    drives = get_removable_drives()
    if not drives:
        print("❌ No removable drives found.")
        return

    choices = [{"name": f"{d['path']} - {d['size']} - {d['model']}", "value": d['path']} for d in drives]
    usb_dev = drives[0]['path'] if headless else inquirer.select(message="Select the USB drive to use:", choices=choices + [Separator(), "Cancel"]).execute()

    # Load paths and download if missing
    iso_paths = {}
    for key in ["ubuntu_iso", "kali_iso", "windows_iso", "wtg_img"]:
        local = config["paths"].get(key)
        url = config["urls"].get(key)
        if not local:
            local = get_file(f"Select {key.replace('_', ' ').title()}")
        path = ensure_file(local, url)
        iso_paths[key] = path

    total_size_gb = get_disk_size_gb(usb_dev)
    kali_size = config.get("kali_size", 12)
    min_free_space = 8
    max_wtg_size = total_size_gb - kali_size - min_free_space
    wtg_size = config.get("wtg_size", min(32, int(max_wtg_size)))

    if not headless:
        wtg_size = float(inquirer.text(
            message=f"Enter size (GB) for Windows To Go partition [max {max_wtg_size:.1f}]:",
            default=str(wtg_size),
            validate=lambda val: val.replace('.', '', 1).isdigit() and float(val) <= max_wtg_size
        ).execute())

    ventoy_space = total_size_gb - kali_size - wtg_size
    print(f"\n📦 Partition Plan:")
    print(f"  • Ventoy + ISOs + Free space: ~{ventoy_space:.1f} GB")
    print(f"  • Kali persistence: {kali_size} GB")
    print(f"  • Windows To Go: {wtg_size:.1f} GB\n")

    if not headless:
        confirm = inquirer.confirm(message="Proceed with installation? This will ERASE the USB.", default=False).execute()
        if not confirm:
            print("❌ Cancelled.")
            return

    # Proceed
    ventoy_partition = install_ventoy(usb_dev)
    mount_partition(ventoy_partition, MOUNT_VENTOY)

    print("📤 Copying ISOs and WTG image...")
    for key, src in iso_paths.items():
        copy_with_progress(src, os.path.join(MOUNT_VENTOY, os.path.basename(src)))

    create_partition(usb_dev, 3, kali_size, "83")
    setup_kali_persistence(f"{usb_dev}3")

    create_partition(usb_dev, 4, wtg_size, "07")
    format_partition(f"{usb_dev}4", "ntfs", "WTG")
    mount_partition(f"{usb_dev}4", MOUNT_WTG)
    copy_with_progress(iso_paths["wtg_img"], os.path.join(MOUNT_WTG, os.path.basename(iso_paths["wtg_img"])))
    unmount_partition(MOUNT_WTG)

    setup_ventoy_json(MOUNT_VENTOY, [os.path.basename(p) for p in iso_paths.values()])
    unmount_partition(MOUNT_VENTOY)

    print("\n✅ Done! Your USB stick is ready to boot all OSes with persistence and icons.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ventoy Multi-Boot USB Setup Tool")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode using config file only")
    args = parser.parse_args()
    main(headless=args.headless)
