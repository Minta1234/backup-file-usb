import os
import subprocess
import time
import sys
import platform
from datetime import datetime

# ตรวจสอบและติดตั้ง dependencies
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

# ตรวจสอบว่ารันบนระบบอะไร
IS_WINDOWS = os.name == 'nt'
IS_LINUX = platform.system() == 'Linux'

# ฟังก์ชันเช็กว่า ADB พร้อมใช้งานไหม
def check_adb():
    try:
        subprocess.check_output(["adb", "version"], stderr=subprocess.STDOUT)
        print("[✔] ADB is available.")
    except Exception as e:
        print("[❌] ADB not installed or not found in PATH.")
        if IS_LINUX:
            print("🔧 Installing ADB via package manager (Linux)...")
            subprocess.run(["sudo", "apt", "update"])
            subprocess.run(["sudo", "apt", "install", "-y", "adb"])
        elif IS_WINDOWS:
            print("📦 กรุณาติดตั้ง ADB ด้วยตนเองจาก: https://developer.android.com/tools/releases/platform-tools")
            sys.exit(1)

# แสดงไดรฟ์หรือพาร์ติชันที่เชื่อมต่อ
def list_storage_devices():
    print("📦 Connected drives or partitions:")
    drives = []
    for p in psutil.disk_partitions():
        if IS_WINDOWS:
            drives.append(p.device)
            print(f" - {p.device} ({p.mountpoint})")
        else:
            drives.append(p.mountpoint)
            print(f" - {p.mountpoint}")
    return drives

# ให้ผู้ใช้เลือกที่จัดเก็บไฟล์
def select_drive(drives):
    choice = input("📁 Enter the path to save backup (e.g., E:\\ or /media/usb): ").strip()
    if choice in drives or os.path.exists(choice):
        return choice
    else:
        print("❌ Invalid path.")
        sys.exit(1)

# ค้นหา Android Device
def list_android_devices():
    try:
        output = subprocess.check_output(['adb', 'devices'], encoding='utf-8')
        lines = output.strip().split('\n')[1:]
        devices = [line.split('\t')[0] for line in lines if 'device' in line]
        return devices
    except Exception as e:
        return []

# ดูดข้อมูลจาก Android
def pull_from_android(device_id, remote_path, local_path, log_file):
    try:
        os.makedirs(local_path, exist_ok=True)
        subprocess.run(['adb', '-s', device_id, 'pull', remote_path, local_path], check=True)
        log = f"[✅ OK] Pulled {remote_path} → {local_path}"
    except subprocess.CalledProcessError as e:
        log = f"[❌ FAIL] Pull failed: {remote_path} → {local_path} | {e}"
    except KeyboardInterrupt:
        log = f"[❌ FAIL] Interrupted during pull from {remote_path}"
    print(log)
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log + '\n')

# ตรวจว่า USB ยังต่ออยู่ไหม
def is_device_connected(device_id):
    devices = list_android_devices()
    return device_id in devices

# ------------------ MAIN ------------------ #
if __name__ == "__main__":
    print("📂 Preparing Android Backup System...\n")

    check_adb()

    # 1. เลือกพื้นที่เก็บ
    drives = list_storage_devices()
    target_path = select_drive(drives)

    # 2. สร้างโฟลเดอร์สำรอง
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = os.path.join(target_path, f"AndroidBackup_{timestamp}")
    os.makedirs(backup_root, exist_ok=True)
    log_file = os.path.join(backup_root, "backup_log.txt")

    # 3. รอจนกว่า Android จะเชื่อมต่อ
    print("🔍 Waiting for Android device (USB debugging must be enabled)...")
    android_devices = []
    while not android_devices:
        android_devices = list_android_devices()
        if not android_devices:
            print("⌛ Still waiting...")
            time.sleep(3)

    device_id = android_devices[0]
    print(f"✅ Found Android device: {device_id}")

    # 4. โฟลเดอร์ที่จะดูด
    folders_to_pull = [
        "/sdcard/DCIM",
        "/sdcard/Download",
        "/sdcard/Documents",
        "/sdcard/WhatsApp"
    ]

    print("📥 Starting backup process...")
    for folder in folders_to_pull:
        folder_name = os.path.basename(folder)
        local_folder = os.path.join(backup_root, folder_name)

        if not is_device_connected(device_id):
            print(f"❌ USB disconnected while pulling {folder}. Exiting.")
            with open(log_file, 'a') as f:
                f.write(f"[ERROR] USB disconnected while pulling {folder}\n")
            sys.exit(1)

        pull_from_android(device_id, folder, local_folder, log_file)

    print("\n✅ Backup completed.")
    print(f"📁 Files saved in: {backup_root}")
    print(f"📝 Log saved at: {log_file}")
