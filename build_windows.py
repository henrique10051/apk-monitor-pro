"""
Build para Windows - Gera APKMonitorPro.exe
"""

import os
import sys
import subprocess
from pathlib import Path

print("=" * 70)
print("APK MONITOR PRO - BUILD WINDOWS (.exe)")
print("=" * 70)
print()

# Verifica se está no Windows
if not sys.platform.startswith('win'):
    print("❌ Este script é apenas para Windows!")
    print("   Use build_macos.py no macOS")
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
print("2️⃣ Gerando .exe...")

cmd = [
    "pyinstaller",
    "--name=APKMonitorPro",
    "--onefile",  # Arquivo único
    "--windowed",  # Sem console
    "--clean",
    "--noconfirm",
    "--hidden-import=apk_monitor_pro.core.adb_manager",
    "--hidden-import=apk_monitor_pro.analyzers.error_diagnostics",
    "--hidden-import=apk_monitor_pro.integrations.frida_hook",
    "--hidden-import=apk_monitor_pro.integrations.tcpdump_capture",
    "--hidden-import=apk_monitor_pro.utils.report_generator",
    "--add-data=apk_monitor_pro;apk_monitor_pro",  # Separador ; no Windows
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
exe_path = Path("dist/APKMonitorPro.exe")

if exe_path.exists():
    size_mb = exe_path.stat().st_size / (1024 * 1024)
    print(f"📦 Executável: {exe_path.absolute()}")
    print(f"💾 Tamanho: {size_mb:.1f} MB")
    print()
    print("🚀 COMO USAR:")
    print("   1. Vá para a pasta 'dist'")
    print("   2. Clique duplo em 'APKMonitorPro.exe'")
    print()
    print("💡 DISTRIBUIR:")
    print("   Envie apenas o arquivo APKMonitorPro.exe")
    print("   Não precisa de Python instalado!")
    print()
    print("⚠️  REQUISITOS:")
    print("   - ADB (Android Debug Bridge) instalado")
    print("   - Dispositivo Android conectado via USB")
    print()
else:
    print("❌ Build falhou!")
    sys.exit(1)

print("=" * 70)
