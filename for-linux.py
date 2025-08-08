import os
import subprocess
import time
import sys
from datetime import datetime

# ไลบรารีที่ต้องใช้
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
        print("🔧 Installing ADB via apt...")
        subprocess.run(["sudo", "apt", "update"], check=True)
        subprocess.run(["sudo", "apt", "install", "-y", "adb"], check=True)

def list_storage_devices():
    print("📦 Connected drives or partitions:")
    drives = []
    for p in psutil.disk_partitions():
        drives.append(p.mountpoint)
        print(f" - {p.mountpoint}")
    return drives

def select_drive(drives):
    choice = input("📁 Enter the path to save backup (e.g., /media/usb): ").strip()
    if choice in drives or os.path.exists(choice):
        return choice
    else:
        print("❌ Invalid path.")
        sys.exit(1)

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

    drives = list_storage_devices()
    target_path = select_drive(drives)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = os.path.join(target_path, f"AndroidBackup_{timestamp}")
    os.makedirs(backup_root, exist_ok=True)
    log_file = os.path.join(backup_root, "backup_log.txt")

    print("🔍 Waiting for Android device (enable USB debugging)...")
    android_devices = []
    while not android_devices:
        android_devices = list_android_devices()
        if not android_devices:
            print("⌛ Still waiting for device...")
            time.sleep(3)

    device_id = android_devices[0]
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
    print(f"📝 Log saved at: {log_file}")        os.makedirs(local_path, exist_ok=True)
        subprocess.run(['adb', '-s', device_id, 'pull', remote_path, local_path], check=True)
        log = f"[✅ OK] Pulled {remote_path} → {local_path}"
    except Exception as e:
        log = f"[❌ FAIL] {remote_path} → {local_path} | {e}"
        print(log)
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log + '\n')
        raise
    print(log)
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log + '\n')

if __name__ == "__main__":
    print("📂 Preparing Android backup system for Linux...")

    install_dependencies_linux()

    drives = list_storage_devices()
    target_drive = select_drive(drives)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = os.path.join(target_drive, f"AndroidBackup_{timestamp}")
    os.makedirs(backup_root, exist_ok=True)
    log_file = os.path.join(backup_root, "backup_log.txt")

    print("🔍 รออุปกรณ์ Android (เปิด USB debugging)...")
    android_devices = []
    while not android_devices:
        android_devices = list_android_devices()
        if not android_devices:
            print("⌛ ยังไม่พบอุปกรณ์ รอสักครู่...")
            time.sleep(3)

    device_id = android_devices[0]
    print(f"✅ ตรวจพบอุปกรณ์: {device_id}")
    print("📥 เริ่มดึงข้อมูล...")

    folders_to_pull = [
        "/sdcard/DCIM",
        "/sdcard/Download",
        "/sdcard/Documents",
        "/sdcard/WhatsApp"
    ]

    try:
        for folder in folders_to_pull:
            folder_name = os.path.basename(folder)
            local_path = os.path.join(backup_root, folder_name)
            pull_from_android(device_id, folder, local_path, log_file)
    except Exception as e:
        print(f"🛑 Backup หยุดทำงาน: {e}")
        sys.exit(1)

    print("\n✅ Backup เสร็จสมบูรณ์")
    print(f"📁 ข้อมูลถูกเก็บไว้ที่: {backup_root}")
    print(f"📝 Log ไฟล์: {log_file}")
