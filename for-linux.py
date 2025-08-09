import os
import subprocess
import time
import sys
from datetime import datetime

REQUIRED_LIBRARIES = ["psutil"]

def install_and_import(lib):
    try:
        __import__(lib)
        print(f"[✔] Library '{lib}' is already installed.")
    except ImportError:
        print(f"[+] Installing '{lib}' ...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", lib])

for lib in REQUIRED_LIBRARIES:
    install_and_import(lib)

import psutil

def check_adb():
    try:
        subprocess.check_output(["adb", "version"], stderr=subprocess.STDOUT)
        print("[✔] ADB is available.")
    except Exception:
        print("❌ ADB not found. Please install it manually.")
        print("➡️  Debian/Ubuntu: sudo apt install adb")
        print("➡️  Arch: sudo pacman -S android-tools")
        print("➡️  Fedora: sudo dnf install android-tools")
        sys.exit(1)

def list_mount_points():
    print("📦 Available mount points:")
    mount_points = []
    for p in psutil.disk_partitions():
        if p.mountpoint.startswith("/media") or p.mountpoint.startswith("/mnt"):
            print(f" - {p.device} mounted at {p.mountpoint}")
            mount_points.append(p.mountpoint)
    return mount_points

def select_mount_point(mounts):
    choice = input("📁 Enter path to save backup (e.g., /media/user/USB): ").strip()
    if os.path.exists(choice):
        return choice
    else:
        print("❌ Invalid path.")
        sys.exit(1)

def get_backup_folder_name(target_path):
    while True:
        folder_name = input("📂 Enter backup folder name (will be created inside the target path): ").strip()
        if not folder_name:
            print("❌ Folder name cannot be empty.")
            continue
        backup_path = os.path.join(target_path, folder_name)
        if os.path.exists(backup_path):
            overwrite = input(f"⚠️ Folder '{folder_name}' already exists. Overwrite? (y/n): ").strip().lower()
            if overwrite == 'y':
                return backup_path
            else:
                print("❎ Please enter a different folder name.")
                continue
        return backup_path

def list_android_devices():
    try:
        output = subprocess.check_output(['adb', 'devices'], encoding='utf-8')
        lines = output.strip().split('\n')[1:]
        devices = [line.split('\t')[0] for line in lines if 'device' in line]
        return devices
    except Exception:
        return []

def is_device_connected(device_id):
    devices = list_android_devices()
    return device_id in devices

def wait_for_device():
    print("🔍 Waiting for Android device (USB debugging must be ON)...")
    devices = []
    while not devices:
        devices = list_android_devices()
        if not devices:
            print("⌛ Waiting...")
            time.sleep(3)
    return devices[0]

def pull_from_android(device_id, remote_path, local_path, log_file):
    try:
        if not is_device_connected(device_id):
            raise RuntimeError("📴 Device disconnected")
        os.makedirs(local_path, exist_ok=True)
        subprocess.run(['adb', '-s', device_id, 'pull', remote_path, local_path], check=True)
        log = f"[✅ OK] Pulled {remote_path} → {local_path}"
    except Exception as e:
        log = f"[SKIP] Failed to pull {remote_path} → {local_path} | {e}"
    print(log)
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log + '\n')

def pull_cookies(device_id, local_path, log_file):
    cookie_remote_path = "/data/data/com.android.chrome/app_chrome/Default/Cookies"
    try:
        print("🍪 Attempting to pull Chrome cookies...")
        root_check = subprocess.check_output(['adb', '-s', device_id, 'shell', 'id'], encoding='utf-8')
        if 'uid=0' not in root_check:
            raise PermissionError("Device is not rooted")

        os.makedirs(local_path, exist_ok=True)
        subprocess.run(['adb', '-s', device_id, 'pull', cookie_remote_path, local_path], check=True)
        log = f"[✅ OK] Pulled cookies → {local_path}"
    except Exception as e:
        log = f"[SKIP] Cookies → {local_path} | {e}"
    print(log)
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log + '\n')

if __name__ == "__main__":
    print("📂 Preparing Android Backup System for Linux...\n")

    check_adb()

    mounts = list_mount_points()
    target_path = select_mount_point(mounts)

    backup_root = get_backup_folder_name(target_path)
    os.makedirs(backup_root, exist_ok=True)
    log_file = os.path.join(backup_root, "backup_log.txt")

    device_id = wait_for_device()
    print(f"✅ Found device: {device_id}")

    folders_to_pull = [
        "/sdcard/DCIM",
        "/sdcard/Download",
        "/sdcard/Documents",
        "/sdcard/WhatsApp",
        "/sdcard/Android/data"
    ]

    print("📥 Starting backup process...")
    for folder in folders_to_pull:
        folder_name = os.path.basename(folder)
        local_folder = os.path.join(backup_root, folder_name)

        if not is_device_connected(device_id):
            print(f"❌ Device disconnected while pulling {folder}. Exiting.")
            with open(log_file, 'a') as f:
                f.write(f"[ERROR] Device disconnected while pulling {folder}\n")
            sys.exit(1)

        pull_from_android(device_id, folder, local_folder, log_file)

    cookies_path = os.path.join(backup_root, "Cookies")
    pull_cookies(device_id, cookies_path, log_file)

    print("\n✅ Backup completed.")
    print(f"📁 Files saved at: {backup_root}")
    print(f"📝 Log saved at: {log_file}")
