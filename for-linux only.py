import os
import subprocess
import time
import sys
from datetime import datetime

def install_dependencies_linux():
    print("📦 ตรวจสอบ adb และ psutil...")

    # ติดตั้ง adb ถ้ายังไม่ได้ติดตั้ง
    try:
        subprocess.run(["adb", "version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("✅ adb ติดตั้งแล้ว")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("📦 ติดตั้ง adb ผ่าน apt...")
        subprocess.run(["sudo", "apt", "update"], check=True)
        subprocess.run(["sudo", "apt", "install", "-y", "adb"], check=True)

    # ตรวจสอบ psutil แบบ system-wide
    try:
        import psutil
        print("✅ psutil ติดตั้งแล้ว")
    except ImportError:
        # ตรวจสอบว่าใช้ Linux ที่ไม่อนุญาต pip system-wide
        print("📦 ตรวจสอบการติดตั้ง psutil...")
        try:
            # ใช้ apt แทน pip
            subprocess.run(["sudo", "apt", "install", "-y", "python3-psutil"], check=True)
            import psutil  # ทดสอบอีกครั้ง
        except Exception as e:
            print(f"❌ ติดตั้ง psutil ไม่สำเร็จ: {e}")
            print("💡 คุณอาจต้องใช้ virtual environment หรือ pipx ในระบบ Linux ที่จำกัด pip")
            sys.exit(1)

def list_storage_devices():
    import psutil
    print("📦 รายการไดรฟ์ที่ mount อยู่:")
    drives = []
    for p in psutil.disk_partitions():
        drives.append(p.mountpoint)
        print(f" - {p.mountpoint}")
    return drives

def select_drive(drives):
    choice = input("🧭 ระบุ path สำหรับเก็บ backup (เช่น /media/usb): ").strip()
    if choice in drives or os.path.exists(choice):
        return choice
    else:
        print("❌ path ไม่ถูกต้อง")
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
    return device_id in list_android_devices()

def pull_from_android(device_id, remote_path, local_path, log_file):
    try:
        if not is_device_connected(device_id):
            raise RuntimeError("📴 อุปกรณ์ถูกถอดออก")
        os.makedirs(local_path, exist_ok=True)
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
