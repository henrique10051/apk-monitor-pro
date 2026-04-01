# ✅ VALIDAÇÃO DA ARQUITETURA

## 📁 Estrutura Correta:

```
apk_monitor_pro/
├── __init__.py                    ✅ Criado
├── core/
│   ├── __init__.py               ✅ Criado
│   └── adb_manager.py            ✅ Criado
├── analyzers/
│   ├── __init__.py               ✅ Criado
│   └── error_diagnostics.py     ✅ Criado
├── integrations/
│   ├── __init__.py               ✅ Criado
│   ├── frida_hook.py            ✅ Criado
│   └── tcpdump_capture.py       ✅ Criado
└── utils/
    ├── __init__.py               ✅ Criado
    └── report_generator.py      ✅ Criado
```

## 🧪 TESTE 1: Validar Estrutura

Execute no terminal:

```bash
python test_architecture.py
```

**Resultado esperado:**
```
✅ TODOS OS MÓDULOS IMPORTADOS COM SUCESSO!
✅ TESTES BÁSICOS CONCLUÍDOS!
```

---

## 🧪 TESTE 2: Importar Módulos

Teste manualmente no Python:

```python
# Teste 1: Import do pacote principal
import apk_monitor_pro
print(apk_monitor_pro.__version__)  # Deve mostrar: 2.0.0

# Teste 2: Import de módulos individuais
from apk_monitor_pro.core import ADBManager
from apk_monitor_pro.analyzers import ErrorDiagnostics
from apk_monitor_pro.integrations import FridaHooker, TCPDumpCapture
from apk_monitor_pro.utils import ReportGenerator

print("✅ Todos os imports funcionaram!")
```

---

## 🧪 TESTE 3: Funcionalidades Básicas

### Teste ADB Manager:
```python
from apk_monitor_pro.core import ADBManager

adb = ADBManager()

# Verifica ADB
print(adb.check_adb_available())  # True se ADB está no PATH

# Lista dispositivos
devices = adb.get_connected_devices()
print(f"Dispositivos: {devices}")

# Pega PID da APK (se estiver rodando)
pid = adb.get_package_pid("it.overit.amplawfm")
print(f"PID: {pid}")
```

### Teste Error Diagnostics:
```python
from apk_monitor_pro.analyzers import ErrorDiagnostics

diagnostics = ErrorDiagnostics()

# Erro fake para teste
fake_error = {
    'timestamp': '2026-03-31 14:30:15',
    'level': 'E',
    'tag': 'SyncManager',
    'message': 'SocketTimeoutException: Read timed out'
}

# Diagnostica
diagnosis = diagnostics.diagnose_error(fake_error)

print(f"Camada: {diagnosis['layer']}")  # NETWORK
print(f"Responsável: {diagnosis['responsible_team']}")  # INFRA/REDE
print(f"Causa Raiz: {diagnosis['root_cause']}")
```

### Teste Report Generator:
```python
from apk_monitor_pro.utils import ReportGenerator

gen = ReportGenerator()

# Gera relatório de teste
errors = [fake_error]
logs = []
queries = []

html = gen.generate_dev_report(errors, logs, queries)
print(f"HTML gerado: {len(html)} caracteres")

# Salva para visualizar
with open("test_report.html", "w") as f:
    f.write(html)

print("✅ Abra test_report.html no navegador!")
```

---

## 🧪 TESTE 4: Proxy Auto-Config

**IMPORTANTE:** Requer dispositivo Android conectado via USB

```python
from apk_monitor_pro.core import ADBManager

adb = ADBManager()

# Método 1: ADB Reverse (simples)
success = adb.configure_proxy_reverse(8888)
print(f"Proxy ADB Reverse: {'✅ OK' if success else '❌ Falhou'}")

# Método 2: iptables (requer root)
result = adb.configure_proxy_iptables(8888)
print(f"Proxy iptables: {'✅ OK' if result['success'] else '❌ Falhou'}")

if not result['success']:
    print(f"Erros: {result['errors']}")
```

---

## 🧪 TESTE 5: Filtro PID Rígido

**IMPORTANTE:** Requer APK rodando no dispositivo

```python
from apk_monitor_pro.core import ADBManager

adb = ADBManager()

# MODO RÍGIDO: Apenas PID específico
try:
    process = adb.start_logcat_filtered(
        package_name="it.overit.amplawfm",
        log_level="I",
        strict_mode=True  # ← RÍGIDO
    )
    
    print("✅ Logcat filtrado por PID iniciado!")
    print("   Apenas logs da APK selecionada aparecerão")
    
    # Lê alguns logs
    import time
    for i in range(10):
        line = process.stdout.readline()
        print(line.strip())
        time.sleep(0.1)
    
    process.terminate()
    
except Exception as e:
    print(f"❌ Erro: {e}")
    print("   Certifique-se que a APK está rodando!")
```

---

## ✅ CHECKLIST DE VALIDAÇÃO

Marque conforme completa:

- [ ] ✅ Estrutura de pastas criada corretamente
- [ ] ✅ Todos os `__init__.py` criados
- [ ] ✅ `test_architecture.py` passa sem erros
- [ ] ✅ Imports manuais funcionam
- [ ] ✅ ADB disponível e funcionando
- [ ] ✅ Dispositivo Android conectado
- [ ] ✅ Consegue pegar PID da APK
- [ ] ✅ Filtro por PID funciona
- [ ] ✅ Diagnóstico de erro funciona
- [ ] ✅ Gerador de relatório funciona
- [ ] ✅ Proxy auto-config funciona (ADB Reverse)
- [ ] ✅ Proxy iptables funciona (se tiver root)
- [ ] ✅ Frida instalado (opcional)
- [ ] ✅ tcpdump instalado (opcional)

---

## 🚨 PROBLEMAS COMUNS

### Problema: "ModuleNotFoundError: No module named 'apk_monitor_pro'"

**Solução:**
```bash
# Certifique-se de estar na pasta correta
cd /caminho/para/pasta/com/apk_monitor_pro

# Ou adicione ao PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/caminho/para/pasta"
```

### Problema: "ADB não encontrado"

**Solução:**
```bash
# Adicione ADB ao PATH
# Windows: Adicione C:\platform-tools ao PATH
# Linux/Mac: export PATH=$PATH:/path/to/platform-tools
```

### Problema: "Device unauthorized"

**Solução:**
1. Aceite a mensagem no dispositivo Android
2. Execute: `adb kill-server && adb start-server`

### Problema: "PID não encontrado"

**Solução:**
1. Certifique-se que a APK está RODANDO
2. Abra a APK no dispositivo
3. Execute: `adb shell ps | grep overit` para confirmar

---

## 📊 RESULTADO ESPERADO

Se todos os testes passaram:

```
✅ Estrutura: OK
✅ Imports: OK
✅ ADB: OK
✅ Dispositivo: Conectado
✅ PID Detection: OK
✅ Filtro Rígido: OK
✅ Diagnóstico: OK
✅ Relatórios: OK
✅ Proxy: OK

🎉 ARQUITETURA 100% FUNCIONAL!
```

---

## 🚀 PRÓXIMO PASSO

Agora você pode:

1. **Usar módulos standalone:**
   ```python
   from apk_monitor_pro.core import ADBManager
   # Use diretamente em scripts
   ```

2. **Aguardar interface gráfica completa:**
   - Integra todos os módulos
   - UI profissional
   - Botões para cada funcionalidade

**Quer que eu crie a UI agora?** 🎨
