"""
Script de teste rápido - APK Monitor Pro
Verifica se todas as dependências estão instaladas e funcionando
"""

import sys
import subprocess


def test_python_version():
    """Testa versão do Python"""
    print("🔍 Testando versão do Python...")
    version = sys.version_info
    
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - INCOMPATÍVEL")
        print("   Necessário Python 3.8 ou superior")
        return False


def test_adb():
    """Testa se ADB está instalado"""
    print("\n🔍 Testando ADB...")
    
    try:
        result = subprocess.run(
            ["adb", "version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            print(f"✅ ADB encontrado - {version}")
            return True
        else:
            print("❌ ADB não está funcionando corretamente")
            return False
            
    except FileNotFoundError:
        print("❌ ADB não encontrado no PATH")
        print("   Instale Android Platform Tools:")
        print("   https://developer.android.com/studio/releases/platform-tools")
        return False
    except Exception as e:
        print(f"❌ Erro ao testar ADB: {e}")
        return False


def test_adb_devices():
    """Testa se há dispositivos conectados"""
    print("\n🔍 Verificando dispositivos conectados...")
    
    try:
        result = subprocess.run(
            ["adb", "devices"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        lines = result.stdout.strip().split('\n')
        devices = [line for line in lines[1:] if line.strip() and 'device' in line]
        
        if devices:
            print(f"✅ {len(devices)} dispositivo(s) conectado(s):")
            for device in devices:
                print(f"   - {device}")
            return True
        else:
            print("⚠️  Nenhum dispositivo conectado via ADB")
            print("   Conecte um dispositivo Android via USB e ative depuração USB")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao verificar dispositivos: {e}")
        return False


def test_dependencies():
    """Testa se as dependências Python estão instaladas"""
    print("\n🔍 Testando dependências Python...")
    
    dependencies = {
        'PyQt5': 'Interface gráfica',
        'mitmproxy': 'Proxy MITM',
    }
    
    all_ok = True
    
    for package, description in dependencies.items():
        try:
            __import__(package)
            print(f"✅ {package:15} - OK ({description})")
        except ImportError:
            print(f"❌ {package:15} - NÃO INSTALADO ({description})")
            all_ok = False
            
    if not all_ok:
        print("\n⚠️  Instale as dependências com:")
        print("   python install_dependencies.py")
        
    return all_ok


def test_network():
    """Testa conectividade de rede"""
    print("\n🔍 Testando conectividade de rede...")
    
    try:
        import socket
        
        # Pega IP local
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        
        print(f"✅ IP local: {local_ip}")
        print(f"   Configure este IP no proxy do Android")
        return True
        
    except Exception as e:
        print(f"⚠️  Erro ao obter IP: {e}")
        return False


def main():
    """Executa todos os testes"""
    print("=" * 70)
    print("APK MONITOR PRO - TESTE DE SISTEMA")
    print("=" * 70)
    print()
    
    results = []
    
    # Testes
    results.append(("Python", test_python_version()))
    results.append(("ADB", test_adb()))
    results.append(("Dispositivos", test_adb_devices()))
    results.append(("Dependências", test_dependencies()))
    results.append(("Rede", test_network()))
    
    # Resumo
    print("\n" + "=" * 70)
    print("RESUMO DOS TESTES")
    print("=" * 70)
    
    for test_name, result in results:
        status = "✅ OK" if result else "❌ FALHOU"
        print(f"{test_name:20} {status}")
    
    print()
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("🎉 Tudo funcionando! Você pode executar:")
        print("   python apk_monitor_pro.py")
    else:
        print("⚠️  Alguns testes falharam. Corrija os problemas acima.")
        
        if not results[2][1]:  # Se não tem dispositivos
            print("\n📱 PRÓXIMOS PASSOS:")
            print("1. Conecte o dispositivo Android via USB")
            print("2. Ative 'Depuração USB' nas opções de desenvolvedor")
            print("3. Execute 'adb devices' e aceite a autorização no celular")
            
        if not results[3][1]:  # Se faltam dependências
            print("\n📦 INSTALAR DEPENDÊNCIAS:")
            print("   python install_dependencies.py")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
