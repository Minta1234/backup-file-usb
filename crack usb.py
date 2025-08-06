import os
import subprocess
import time
import psutil
from datetime import datetime

# --- List available drives/partitions ---
def list_storage_devices():
    print("📦 Connected drives or partitions:")
    drives = []
    partitions = psutil.disk_partitions()
    if os.name == 'nt':
        for p in partitions:
            drives.append(p.device)
            print(f" - {p.device} ({p.mountpoint})")
    else:
        for p in partitions:
            drives.append(p.mountpoint)
            print(f" - {p.mountpoint}")
    return drives

# --- Let user select a drive/path ---
def select_drive(drives):
    choice = input("🧭 Enter the drive/path to save backup (e.g., E:\\ or /media/usb): ").strip()
    if choice in drives or os.path.exists(choice):
        return choice
    else:
        print("❌ Invalid drive/path")
        exit(1)

# --- List connected Android devices via ADB ---
def list_android_devices():
    try:
        output = subprocess.check_output(['adb', 'devices'], encoding='utf-8')
        lines = output.strip().split('\n')[1:]
        devices = [line.split('\t')[0] for line in lines if 'device' in line]
        return devices
    except Exception as e:
        print(f"[ERROR] ADB not available or not installed: {e}")
        return []

# --- Pull data from Android device ---
def pull_from_android(device_id, remote_path, local_path, log_file):
    try:
        os.makedirs(local_path, exist_ok=True)
        subprocess.run(['adb', '-s', device_id, 'pull', remote_path, local_path], check=True)
        log = f"[✅ OK] Pulled {remote_path} → {local_path}"
    except subprocess.CalledProcessError as e:
        log = f"[❌ FAIL] Failed to pull {remote_path} → {local_path} | {e}"
    print(log)
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log + '\n')

# --- MAIN ---
if __name__ == "__main__":
    print("📂 Preparing system for Android backup...")

    # 1. Let user select storage location
    drives = list_storage_devices()
    target_drive = select_drive(drives)

    # 2. Create backup folder
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = os.path.join(target_drive, f"AndroidBackup_{timestamp}")
    os.makedirs(backup_root, exist_ok=True)
    log_file = os.path.join(backup_root, "backup_log.txt")

    # 3. Wait until an Android device is connected
    print("🔍 Searching for Android devices... Please connect your device with USB debugging enabled.")
    android_devices = []
    while not android_devices:
        android_devices = list_android_devices()
        if not android_devices:
            print("⌛ No device found yet... Waiting for connection.")
            time.sleep(3)

    device_id = android_devices[0]
    print(f"\n✅ Found Android device: {device_id}")
    print("📥 Starting data pull from device...")

    # 4. List of folders to pull
    folders_to_pull = [
        "/sdcard/DCIM",
        "/sdcard/Download",
        "/sdcard/Documents",
        "/sdcard/WhatsApp"
    ]

    # 5. Pull all data into one backup folder (subfolders created for each)
    for folder in folders_to_pull:
        folder_name = os.path.basename(folder)
        local_path = os.path.join(backup_root, folder_name)
        pull_from_android(device_id, folder, local_path, log_file)

    print("\n✅ Backup completed successfully.")
    print(f"📁 Files saved to: {backup_root}")
    print(f"📝 Log file: {log_file}")
