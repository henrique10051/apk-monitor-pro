"""
Script de instalação de dependências do APK Monitor Pro
"""

import subprocess
import sys

def install_dependencies():
    """Instala todas as dependências necessárias"""
    
    dependencies = [
        "PyQt5",
        "pyinstaller"
    ]
    
    print("=" * 60)
    print("APK Monitor Pro - Instalação de Dependências")
    print("=" * 60)
    print()
    
    for package in dependencies:
        print(f"📦 Instalando {package}...")
        try:
            subprocess.check_call([
                sys.executable, 
                "-m", 
                "pip", 
                "install", 
                package,
                "--upgrade"
            ])
            print(f"✅ {package} instalado com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao instalar {package}: {e}")
            
        print()
    
    # mitmproxy OPCIONAL
    print("=" * 60)
    print("📦 Instalando mitmproxy (OPCIONAL)")
    print("⚠️  Se der erro, não tem problema! Você pode usar só logs ADB")
    print("=" * 60)
    
    try:
        subprocess.check_call([
            sys.executable,
            "-m",
            "pip",
            "install",
            "mitmproxy",
            "--upgrade"
        ])
        print("✅ mitmproxy instalado! Você poderá capturar tráfego de rede")
    except Exception as e:
        print("⚠️  mitmproxy não instalado (isso é OK!)")
        print("    Você pode usar o APK Monitor apenas com logs ADB")
        print("    Para instalar depois: pip install mitmproxy")
    
    print()
    
    print("=" * 60)
    print("✅ Instalação concluída!")
    print("=" * 60)
    print()
    print("Para executar a aplicação:")
    print("  python apk_monitor_pro.py")
    print()
    print("Para gerar o executável .exe:")
    print("  python build_exe.py")
    print()

if __name__ == "__main__":
    install_dependencies()
