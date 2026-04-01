"""
Build para macOS - Gera APKMonitorPro.app
"""

import os
import sys
import subprocess
from pathlib import Path

print("=" * 70)
print("APK MONITOR PRO - BUILD macOS (.app)")
print("=" * 70)
print()

# Verifica se está no macOS
if sys.platform != 'darwin':
    print("❌ Este script é apenas para macOS!")
    sys.exit(1)

# 1. Instala PyInstaller se necessário
print("1️⃣ Verificando PyInstaller...")
try:
    import PyInstaller
    print("   ✅ PyInstaller instalado")
except ImportError:
    print("   ⚠️  Instalando PyInstaller...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

print()

# 2. Build
print("2️⃣ Gerando .app bundle...")

cmd = [
    "pyinstaller",
    "--name=APKMonitorPro",
    "--windowed",  # Gera .app
    "--onefile",
    "--clean",
    "--noconfirm",
    "--hidden-import=apk_monitor_pro.core.adb_manager",
    "--hidden-import=apk_monitor_pro.analyzers.error_diagnostics",
    "--hidden-import=apk_monitor_pro.integrations.frida_hook",
    "--hidden-import=apk_monitor_pro.integrations.tcpdump_capture",
    "--hidden-import=apk_monitor_pro.utils.report_generator",
    "--add-data=apk_monitor_pro:apk_monitor_pro",
    "apk_monitor_pro.py"
]

print(f"   Executando: pyinstaller...")
subprocess.check_call(cmd)

print()
print("=" * 70)
print("✅ BUILD CONCLUÍDO!")
print("=" * 70)
print()

# Verifica resultado
app_path = Path("dist/APKMonitorPro.app")
exe_path = Path("dist/APKMonitorPro")

if app_path.exists():
    print(f"📦 .app bundle: {app_path.absolute()}")
    print()
    print("🚀 COMO USAR:")
    print("   1. Vá para a pasta 'dist'")
    print("   2. Clique duplo em 'APKMonitorPro.app'")
    print("   OU arraste para /Applications")
    print()
    print("⚠️  Se macOS bloquear:")
    print("   1. System Preferences > Security & Privacy")
    print("   2. Clique 'Open Anyway'")
    print()
    print("   OU via terminal:")
    print("   xattr -cr dist/APKMonitorPro.app")
    print()
elif exe_path.exists():
    print(f"📦 Executável: {exe_path.absolute()}")
    print()
    print("🚀 COMO USAR:")
    print("   ./dist/APKMonitorPro")
    print()
else:
    print("❌ Build falhou!")
    sys.exit(1)

print("=" * 70)
