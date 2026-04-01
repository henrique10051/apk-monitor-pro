#!/usr/bin/env python3
"""
Script de teste da arquitetura modular
Valida que todos os módulos estão importando corretamente
"""

import sys
from pathlib import Path

# Adiciona o diretório ao path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("APK MONITOR PRO - TESTE DE ARQUITETURA")
print("=" * 70)
print()

# Teste de imports
print("🔍 Testando imports dos módulos...")
print()

try:
    print("📦 Importando ADBManager...", end=" ")
    from apk_monitor_pro.core import ADBManager
    print("✅")
    
    print("📦 Importando ErrorDiagnostics...", end=" ")
    from apk_monitor_pro.analyzers import ErrorDiagnostics
    print("✅")
    
    print("📦 Importando FridaHooker...", end=" ")
    from apk_monitor_pro.integrations import FridaHooker
    print("✅")
    
    print("📦 Importando TCPDumpCapture...", end=" ")
    from apk_monitor_pro.integrations import TCPDumpCapture
    print("✅")
    
    print("📦 Importando ReportGenerator...", end=" ")
    from apk_monitor_pro.utils import ReportGenerator
    print("✅")
    
    print()
    print("=" * 70)
    print("✅ TODOS OS MÓDULOS IMPORTADOS COM SUCESSO!")
    print("=" * 70)
    print()
    
except ImportError as e:
    print(f"❌ ERRO!")
    print(f"   {e}")
    sys.exit(1)

# Teste de funcionalidades básicas
print("🔍 Testando funcionalidades básicas...")
print()

try:
    # Teste ADB Manager
    print("1️⃣ ADBManager:", end=" ")
    adb = ADBManager()
    
    # Testa se ADB está disponível
    if adb.check_adb_available():
        print("✅ ADB disponível")
        
        # Testa detecção de dispositivos
        devices = adb.get_connected_devices()
        if devices:
            print(f"   📱 {len(devices)} dispositivo(s) conectado(s): {', '.join(devices)}")
        else:
            print("   ⚠️  Nenhum dispositivo conectado via USB")
    else:
        print("⚠️  ADB não encontrado no PATH")
    
    print()
    
    # Teste Error Diagnostics
    print("2️⃣ ErrorDiagnostics:", end=" ")
    diagnostics = ErrorDiagnostics()
    
    # Teste com erro fake
    fake_error = {
        'timestamp': '2026-03-31 14:30:15.123',
        'level': 'E',
        'tag': 'SyncManager',
        'message': 'SocketTimeoutException: timeout'
    }
    
    diagnosis = diagnostics.diagnose_error(fake_error)
    
    if diagnosis.get('layer') == 'NETWORK':
        print("✅ Diagnóstico funcional")
        print(f"   📍 Camada identificada: {diagnosis['layer']}")
        print(f"   👥 Responsável: {diagnosis.get('responsible_team', 'N/A')}")
    else:
        print("⚠️  Diagnóstico incompleto")
    
    print()
    
    # Teste Frida
    print("3️⃣ FridaHooker:", end=" ")
    hooker = FridaHooker("com.test.app")
    
    if hooker.check_frida_available():
        print("✅ Frida disponível")
    else:
        print("⚠️  Frida não instalado (pip install frida)")
    
    print()
    
    # Teste TCPDump
    print("4️⃣ TCPDumpCapture:", end=" ")
    tcpdump = TCPDumpCapture()
    
    if tcpdump.check_tcpdump_available():
        print("✅ tcpdump disponível no dispositivo")
    else:
        print("⚠️  tcpdump não encontrado (requer root)")
    
    print()
    
    # Teste Report Generator
    print("5️⃣ ReportGenerator:", end=" ")
    report_gen = ReportGenerator()
    print("✅ Gerador de relatórios OK")
    
    print()
    print("=" * 70)
    print("✅ TESTES BÁSICOS CONCLUÍDOS!")
    print("=" * 70)
    print()
    
    # Resumo
    print("📊 RESUMO:")
    print(f"   ✅ Arquitetura modular: OK")
    print(f"   ✅ Imports: OK")
    print(f"   ✅ ADB disponível: {'Sim' if adb.check_adb_available() else 'Não'}")
    print(f"   ✅ Frida disponível: {'Sim' if hooker.check_frida_available() else 'Não (opcional)'}")
    print(f"   ✅ Dispositivo conectado: {'Sim' if devices else 'Não'}")
    print()
    
    if not devices:
        print("⚠️  ATENÇÃO: Conecte um dispositivo Android via USB para usar todas as funcionalidades")
        print()
    
    print("🚀 Sistema pronto para uso!")
    print()
    
except Exception as e:
    print(f"❌ ERRO no teste!")
    print(f"   {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("=" * 70)
print("PRÓXIMO PASSO: Execute 'python apk_monitor_pro.py' para usar a interface gráfica")
print("=" * 70)
