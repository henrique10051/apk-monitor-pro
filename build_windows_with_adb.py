"""
Build Windows com ADB EMBUTIDO
Baixa platform-tools e inclui no executável
"""

import sys
import subprocess
import urllib.request
import zipfile
from pathlib import Path
import shutil

print("=" * 70)
print("APK MONITOR PRO - BUILD WINDOWS (COM ADB)")
print("=" * 70)
print()

if not sys.platform.startswith('win'):
    print("❌ Este script é apenas para Windows!")
    sys.exit(1)

# 1. Instala PyInstaller
print("1️⃣ Verificando PyInstaller...")
try:
    import PyInstaller
except ImportError:
    print("   Instalando PyInstaller...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

print()

# 2. Baixa Platform Tools (ADB)
print("2️⃣ Baixando Platform Tools (ADB)...")
platform_tools_url = "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"
platform_tools_zip = "platform-tools.zip"
platform_tools_dir = Path("platform-tools")

if not platform_tools_dir.exists():
    print(f"   Baixando de: {platform_tools_url}")
    urllib.request.urlretrieve(platform_tools_url, platform_tools_zip)
    
    print("   Extraindo...")
    with zipfile.ZipFile(platform_tools_zip, 'r') as zip_ref:
        zip_ref.extractall(".")
    
    Path(platform_tools_zip).unlink()
    print("   ✅ Platform Tools baixado!")
else:
    print("   ✅ Platform Tools já existe")

print()

# 3. Build com ADB incluído
print("3️⃣ Gerando .exe com ADB embutido...")

cmd = [
    "pyinstaller",
    "--name=APKMonitorPro",
    "--onefile",
    "--clean",
    "--noconfirm",
    "--hidden-import=apk_monitor_pro.core.adb_manager",
    "--hidden-import=apk_monitor_pro.analyzers.error_diagnostics",
    "--hidden-import=apk_monitor_pro.integrations.frida_hook",
    "--hidden-import=apk_monitor_pro.integrations.tcpdump_capture",
    "--hidden-import=apk_monitor_pro.utils.report_generator",
    "--add-data=apk_monitor_pro;apk_monitor_pro",
    "--add-binary=platform-tools/adb.exe;adb",  # EMBUTE ADB!
    "--add-binary=platform-tools/AdbWinApi.dll;adb",
    "--add-binary=platform-tools/AdbWinUsbApi.dll;adb",
    "apk_monitor_pro.py"
]

print("   Compilando...")
subprocess.check_call(cmd)

print()
print("=" * 70)
print("✅ BUILD CONCLUÍDO COM ADB EMBUTIDO!")
print("=" * 70)
print()

exe_path = Path("dist/APKMonitorPro.exe")

if exe_path.exists():
    size_mb = exe_path.stat().st_size / (1024 * 1024)
    print(f"📦 Executável: {exe_path.absolute()}")
    print(f"💾 Tamanho: {size_mb:.1f} MB")
    print()
    print("✅ ADB INCLUÍDO! Não precisa instalar separadamente!")
    print()
    print("🚀 DISTRIBUIR:")
    print("   Envie apenas APKMonitorPro.exe")
    print("   Usuário NÃO precisa instalar ADB!")
    print()
else:
    print("❌ Build falhou!")
    sys.exit(1)

print("=" * 70)
