# 🚀 APK Monitor Pro - Versão Profissional Completa

## Arquitetura Modular Avançada

```
apk_monitor_pro/
├── core/
│   └── adb_manager.py         ✅ Gerenciamento ADB com filtro PID
│
├── analyzers/
│   └── error_diagnostics.py   ✅ Diagnóstico de causa raiz
│
├── integrations/
│   ├── frida_hook.py          ✅ Hooking com Frida
│   └── tcpdump_capture.py     ✅ Captura de pacotes
│
└── utils/
    └── report_generator.py    ✅ Relatórios especializados
```

---

## 🎯 FUNCIONALIDADES IMPLEMENTADAS

### ✅ 1. FILTRO POR PID (Rígido vs Flexível)

**Problema resolvido:** Logs de outras APKs Overit aparecendo misturados

**Solução:**
```python
from core.adb_manager import ADBManager

adb = ADBManager()

# MODO RÍGIDO: Apenas PID específico da APK selecionada
adb.start_logcat_filtered("it.overit.amplawfm", strict_mode=True)

# MODO FLEXÍVEL: Qualquer processo Overit
adb.start_logcat_filtered("it.overit.amplawfm", strict_mode=False)
```

**Como funciona:**
1. Detecta automaticamente PID da APK: `pidof it.overit.amplawfm`
2. Filtra logcat apenas por aquele PID: `adb logcat --pid=12345`
3. Resultado: Apenas logs daquela APK específica!

---

### ✅ 2. PROXY AUTO-CONFIG (2 métodos)

#### Método A: ADB Reverse (Simples, sem root)
```python
adb = ADBManager()
adb.configure_proxy_reverse(port=8888)
# Pronto! Não precisa configurar nada no Android
```

#### Método B: iptables (Avançado, requer root)
```python
result = adb.configure_proxy_iptables(port=8888)
# Redireciona TODO tráfego HTTP/HTTPS automaticamente
# Transparente para a APK
```

**Vantagens iptables:**
- APK nem percebe que está sendo monitorada
- Captura TUDO, incluindo libs de terceiros
- Não precisa configurar proxy manualmente

---

### ✅ 3. ANÁLISE DE CAUSA RAIZ

**Antes:**
```
❌ Erro de sincronização
```

**Agora:**
```
❌ ERRO DE SINCRONIZAÇÃO

📍 CAUSA RAIZ:
├─ SocketTimeoutException
├─ Servidor não respondeu em 30s
└─ Endpoint: https://api.overit.com/sync

🔍 ANÁLISE TÉCNICA:
├─ Camada: NETWORK
├─ Request enviado: ✅ OK (14:30:15)
├─ Response: ❌ TIMEOUT após 30s
├─ WiFi: -67 dBm (Bom)
├─ Ping: 45ms (OK)
└─ Outras APIs: Funcionando

🎯 DIAGNÓSTICO:
┌──────────────────────────────────────┐
│ ORIGEM: SERVIDOR/BACKEND             │
│ RESPONSÁVEL: Time de Backend         │
│                                      │
│ Problema específico no endpoint/sync │
│ Possíveis causas:                    │
│ • Query lenta no banco               │
│ • Processamento pesado               │
│ • Lock no servidor                   │
└──────────────────────────────────────┘

🔧 AÇÃO:
Reportar à BACKEND para investigar:
- Logs do servidor
- Queries do banco
- Performance do endpoint
```

**Uso:**
```python
from analyzers.error_diagnostics import ErrorDiagnostics

diagnostics = ErrorDiagnostics()
diagnosis = diagnostics.diagnose_error(
    log_entry,
    network_context=network_traffic,
    timeline_events=timeline
)

print(diagnosis['responsible_team'])  # "BACKEND"
print(diagnosis['root_cause'])  # "Servidor não respondeu a tempo"
print(diagnosis['recommended_action'])  # Ações específicas
```

---

### ✅ 4. TIMELINE DE EVENTOS

Mostra exatamente o que aconteceu antes do erro:

```
📅 TIMELINE (30s antes do erro)

00:00:00 | ▶️  Usuário clicou "Sincronizar"
00:00:01 | 🔄 SyncManager.startSync() chamado
00:00:02 | 💾 SELECT * FROM pending_orders (50 resultados)
00:00:03 | 📦 JSON payload montado (2.3 MB)
00:00:04 | 🌐 POST /sync enviado
00:00:15 | ⏱️  Aguardando... (15s)
00:00:25 | ⏱️  Aguardando... (25s)
00:00:30 | ❌ SocketTimeoutException

🎯 PONTO DE FALHA: Servidor não respondeu em 30s
```

---

### ✅ 5. HOOKING COM FRIDA

Intercepta chamadas de métodos em TEMPO REAL:

#### Setup:
```bash
# 1. Instalar frida-tools
pip install frida frida-tools

# 2. Baixar frida-server
# https://github.com/frida/frida/releases

# 3. Instalar no dispositivo
adb push frida-server /data/local/tmp/
adb shell "su -c chmod 755 /data/local/tmp/frida-server"
adb shell "su -c /data/local/tmp/frida-server &"
```

#### Uso:
```python
from integrations.frida_hook import FridaHooker

hooker = FridaHooker("it.overit.amplawfm")

# Hook métodos de sincronização
def on_sync_call(message):
    print(f"SYNC CHAMADO: {message}")

hooker.hook_sync_methods(on_sync_call)

# Hook queries SQLite
def on_sql_query(message):
    query = message['payload']['query']
    print(f"SQL: {query}")

hooker.hook_sqlite_queries(on_sql_query)

# Hook HTTP requests
hooker.hook_http_requests(lambda msg: print(f"HTTP: {msg}"))
```

**O que você vê:**
```
SYNC CHAMADO: {
  "class": "com.overit.sync.SyncManager",
  "method": "performSync",
  "arguments": ["force=true"],
  "timestamp": "2026-03-31T14:30:15"
}

SQL: INSERT INTO sync_queue VALUES (...)
SQL: UPDATE orders SET synced=1 WHERE id=123

HTTP: {
  "method": "POST",
  "url": "https://api.overit.com/sync",
  "timestamp": "2026-03-31T14:30:16"
}
```

---

### ✅ 6. CAPTURA TCPDUMP + WIRESHARK

Captura TODOS os pacotes de rede:

```python
from integrations.tcpdump_capture import TCPDumpCapture

tcpdump = TCPDumpCapture()

# Captura tráfego da APK por 60 segundos
pcap_file = tcpdump.start_capture_for_app(
    package_name="it.overit.amplawfm",
    duration=60
)

# Arquivo salvo localmente: capture_20260331_143015.pcap
# Abra com Wireshark para análise detalhada!
```

**No Wireshark:**
- Ver request/response completos
- Timing exato de cada pacote
- Retransmissões (problemas de rede)
- SSL handshake (problemas de certificado)
- Follow TCP Stream para ver conversa completa

---

### ✅ 7. RELATÓRIOS ESPECIALIZADOS

#### Relatório para DESENVOLVIMENTO:
```python
from utils.report_generator import ReportGenerator

gen = ReportGenerator()

html = gen.generate_dev_report(
    errors=errors,
    logs=logs,
    sqlite_queries=queries
)

# Foco em:
# - Stack traces
# - Código com erro
# - Queries SQL
# - Performance
```

#### Relatório para INFRAESTRUTURA:
```python
html = gen.generate_infra_report(
    errors=errors,
    network_traffic=traffic,
    network_info=net_info
)

# Foco em:
# - Conectividade
# - Latência
# - Timeouts
# - Endpoints
# - Qualidade de rede
```

#### Sumário Executivo:
```python
html = gen.generate_executive_summary(
    errors=errors,
    stats=stats
)

# Foco em:
# - KPIs
# - Prioridades
# - Responsáveis
# - Impacto
```

---

## 🎯 WORKFLOW COMPLETO

### 1. SETUP INICIAL
```bash
cd apk_monitor_pro
pip install -r requirements.txt

# Opcional: Setup Frida
pip install frida frida-tools
# (ver guia completo em integrations/frida_hook.py)
```

### 2. USO BÁSICO
```python
from core.adb_manager import ADBManager
from analyzers.error_diagnostics import ErrorDiagnostics

# Conecta ADB
adb = ADBManager()
adb.configure_proxy_reverse(8888)

# Inicia logcat RÍGIDO (apenas PID específico)
process = adb.start_logcat_filtered(
    "it.overit.amplawfm",
    strict_mode=True  # Apenas essa APK!
)

# Analisa erros
diagnostics = ErrorDiagnostics()

for line in process.stdout:
    log = parse_log(line)
    
    if log['level'] in ['E', 'F']:
        # Diagnóstico automático
        diagnosis = diagnostics.diagnose_error(log)
        
        print(f"CAMADA: {diagnosis['layer']}")
        print(f"RESPONSÁVEL: {diagnosis['responsible_team']}")
        print(f"CAUSA: {diagnosis['root_cause']}")
        print(f"AÇÃO: {diagnosis['recommended_action']}")
```

### 3. INVESTIGAÇÃO AVANÇADA
```python
# Se erro complexo, ativa Frida
from integrations.frida_hook import FridaHooker

hooker = FridaHooker("it.overit.amplawfm")
hooker.hook_sync_methods(on_sync)
hooker.hook_sqlite_queries(on_sql)

# Ou captura pacotes
from integrations.tcpdump_capture import TCPDumpCapture

tcpdump = TCPDumpCapture()
pcap = tcpdump.start_capture_for_app("it.overit.amplawfm", 60)

# Analisa no Wireshark
```

### 4. GERA RELATÓRIO
```python
from utils.report_generator import ReportGenerator

gen = ReportGenerator()

# Para DEVs
dev_report = gen.generate_dev_report(errors, logs, queries)
with open("relatorio_dev.html", "w") as f:
    f.write(dev_report)

# Para INFRA
infra_report = gen.generate_infra_report(errors, traffic, net_info)
with open("relatorio_infra.html", "w") as f:
    f.write(infra_report)
```

---

## 📊 COMPARATIVO

| Funcionalidade | Versão Anterior | Versão Atual |
|----------------|----------------|--------------|
| Filtro de logs | Nome pacote (impreciso) | **PID específico (exato)** |
| Proxy | Manual no Android | **Auto-config iptables** |
| Análise de erro | Genérica | **Causa raiz técnica** |
| Timeline | Não tinha | **30s antes do erro** |
| Hooking | Não tinha | **Frida integrado** |
| Captura pacotes | Não tinha | **tcpdump + Wireshark** |
| Relatórios | 1 genérico | **3 especializados** |
| Responsável | Não identifica | **Identifica time** |

---

## 🚧 PRÓXIMOS PASSOS

Agora preciso criar a INTERFACE GRÁFICA que integra todos esses módulos!

Quer que eu:
1. ✅ Crie a UI completa integrando tudo?
2. ✅ Adicione botões para cada funcionalidade?
3. ✅ Mantenha compatibilidade com a interface antiga?

**Confirme e eu crio a UI profissional final!** 🚀
