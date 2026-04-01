# 📱 APK Monitor Pro - Sistema de Logging Personalizado

Sistema completo para monitoramento de APKs Android com captura de logs via ADB e interceptação de tráfego de rede via Proxy MITM.

## 🎯 Funcionalidades

### ✅ Captura via ADB LogCat
- ✔️ Logs de erro, crash e exceções
- ✔️ Filtro por nome do pacote
- ✔️ Níveis de log configuráveis (Verbose, Debug, Info, Warning, Error, Fatal)
- ✔️ Visualização em tempo real com código de cores
- ✔️ Estatísticas de erros e warnings

### ✅ Interceptação de Tráfego de Rede
- ✔️ Captura requests HTTP/HTTPS
- ✔️ Visualização completa de headers e body
- ✔️ Análise de endpoints mais acessados
- ✔️ Status codes e tamanhos de resposta
- ✔️ **Descobre o que o servidor envia para o PDA e vice-versa**

### ✅ Análise e Relatórios
- ✔️ Análise automática de padrões
- ✔️ Identificação de erros recorrentes
- ✔️ Relatórios em HTML profissional
- ✔️ Exportação em JSON para análise externa
- ✔️ Estatísticas detalhadas de uso

---

## 📋 Pré-requisitos

### 1. **ADB (Android Debug Bridge)**

#### Windows:
```bash
# Baixe Android Platform Tools
# https://developer.android.com/studio/releases/platform-tools

# Adicione ao PATH:
# 1. Extraia o ZIP em C:\platform-tools
# 2. Adicione C:\platform-tools ao PATH do Windows
# 3. Teste no CMD:
adb version
```

#### Linux/Mac:
```bash
# Ubuntu/Debian
sudo apt install android-tools-adb

# Mac (Homebrew)
brew install android-platform-tools

# Teste
adb version
```

### 2. **Python 3.8+**
- Download: https://www.python.org/downloads/
- ⚠️ Marque "Add Python to PATH" na instalação

---

## 🚀 Instalação

### Passo 1: Clone ou baixe os arquivos
```bash
# Coloque todos os arquivos .py na mesma pasta
- apk_monitor_pro.py
- install_dependencies.py
- build_exe.py
```

### Passo 2: Instale as dependências
```bash
python install_dependencies.py
```

**Dependências instaladas:**
- `PyQt5` - Interface gráfica
- `mitmproxy` - Proxy MITM para interceptação HTTPS
- `pyinstaller` - Gerador de executável

---

## 🔧 Configuração do Dispositivo Android

### 1. **Habilitar Depuração USB**
```
1. Vá em Configurações > Sobre o telefone
2. Toque 7 vezes em "Número da versão"
3. Volte e entre em "Opções do desenvolvedor"
4. Ative "Depuração USB"
```

### 2. **Conectar via ADB**
```bash
# Conecte o cabo USB
adb devices

# Deve aparecer:
# List of devices attached
# ABC123456789    device
```

### 3. **Configurar Proxy no Android** (Para capturar tráfego HTTPS)

#### Opção A: Wi-Fi Manual
```
1. Conecte Android e PC na MESMA rede Wi-Fi
2. No Android: Configurações > Wi-Fi > Toque na rede conectada
3. Avançado > Proxy > Manual
   - Hostname: [IP do seu PC] (ex: 192.168.1.100)
   - Porta: 8888
   - Salve
```

#### Opção B: ADB Reverse (mais fácil)
```bash
# No terminal/CMD:
adb reverse tcp:8888 tcp:8888
```

### 4. **Instalar Certificado SSL** (Para interceptar HTTPS)

```bash
# 1. Inicie o proxy no APK Monitor Pro
# 2. No navegador do Android, acesse: http://mitm.it
# 3. Baixe o certificado para Android
# 4. Instale: Configurações > Segurança > Instalar de armazenamento
# 5. Escolha o certificado mitmproxy
```

---

## 🎮 Como Usar

### 1. **Executar a Aplicação**
```bash
python apk_monitor_pro.py
```

### 2. **Configurar Monitoramento**
1. **APK**: Selecione no dropdown qual APK você quer monitorar:
   - 🇧🇷 **Rio** - `it.overit.amplawfm`
   - 🇧🇷 **São Paulo** - `it.overit.enelsaopaulowfm`
   - 🇧🇷 **Ceará** - `it.overit.coelcewfm`
   - 📦 **Personalizado** - Digite manualmente outro pacote

2. **Nível de Log**: Escolha o nível de detalhamento
   - **Verbose**: Tudo (muito verboso)
   - **Debug**: Informações de debug
   - **Info**: Informações gerais ✅ (Recomendado)
   - **Warning**: Apenas avisos
   - **Error**: Apenas erros
   - **Fatal**: Apenas crashes

3. **Porta do Proxy**: Padrão 8888 (não precisa alterar)

### 3. **Iniciar Monitoramento**
1. Clique em **"▶️ Iniciar Monitoramento"**
2. Use a APK normalmente no dispositivo
3. Veja os logs em tempo real na aba "Logs ADB"
4. Veja o tráfego de rede na aba "Tráfego de Rede"

### 3.1. **Usar Filtros Rápidos**
Para facilitar a identificação de problemas, use os filtros rápidos:

- ✅ **Sync** - Filtra apenas logs de sincronização
- ✅ **Apenas Erros** - Mostra apenas erros e warnings
- ✅ **Network** - Filtra logs relacionados a rede
- ✅ **Exceptions** - Mostra apenas exceções
- ✅ **Crashes** - Filtra crashes e erros fatais

**Você pode combinar múltiplos filtros!** Por exemplo:
- Ative "Sync" + "Apenas Erros" = Ver apenas erros de sincronização
- Ative "Network" + "Exceptions" = Ver exceções de rede

### 4. **Analisar Resultados**
1. Vá para aba **"📊 Análise"**
2. Clique em **"🔍 Analisar Dados Capturados"**
3. Veja:
   - Top erros encontrados
   - Endpoints mais acessados
   - Distribuição de logs por nível
   - Status codes HTTP

### 5. **Gerar Relatório**
1. Vá para aba **"📄 Relatórios"**
2. Escolha as opções:
   - ✅ Incluir Logs ADB
   - ✅ Incluir Tráfego de Rede
   - ✅ Incluir Análise
3. Clique em:
   - **📄 Gerar Relatório HTML**: Relatório visual profissional
   - **📋 Exportar JSON**: Dados estruturados para análise

---

## 🔍 Entendendo o Tráfego de Rede

### O que você pode ver:

#### 📤 **Requests (PDA → Servidor)**
```json
{
  "method": "POST",
  "url": "https://api.empresa.com/sync",
  "headers": {
    "Content-Type": "application/json",
    "Authorization": "Bearer xxx"
  },
  "content": "{\"data\": \"informações enviadas\"}"
}
```

#### 📥 **Responses (Servidor → PDA)**
```json
{
  "status_code": 200,
  "headers": {
    "Content-Type": "application/json"
  },
  "content": "{\"result\": \"dados recebidos\"}"
}
```

### Casos de Uso:
- ✅ Ver exatamente quais dados o PDA envia
- ✅ Ver quais dados o servidor retorna
- ✅ Identificar erros de API (404, 500, etc)
- ✅ Verificar sincronizações
- ✅ Debugar problemas de rede

---

## 🏗️ Gerar Executável .exe

Para distribuir sem precisar instalar Python:

```bash
python build_exe.py
```

**Resultado:**
- 📁 Pasta `dist/` será criada
- 📦 Arquivo `APKMonitorPro.exe` (~50-80 MB)
- ✅ Pode ser executado sem instalar Python
- ⚠️ ADB ainda precisa estar no PATH

---

## 🐛 Solução de Problemas

### ❌ "ADB não encontrado"
```bash
# Certifique-se que ADB está no PATH
adb version

# Se não funcionar, adicione manualmente ao PATH:
# Windows: C:\platform-tools
# Linux/Mac: /usr/local/bin
```

### ❌ "Device não autorizado"
```bash
# Desconecte e reconecte o cabo USB
# Aceite a mensagem "Permitir depuração USB" no Android
adb devices
```

### ❌ "Proxy não captura HTTPS"
```
1. Certifique-se que instalou o certificado mitmproxy
2. Acesse http://mitm.it no navegador do Android
3. Baixe e instale o certificado
4. Reinicie o proxy
```

### ❌ "Nenhum log aparece"
```
1. Verifique se o nome do pacote está correto
2. Use filtro "V (Verbose)" para ver todos os logs
3. Execute a APK e faça ações que geram logs
4. Verifique se o dispositivo está conectado: adb devices
```

### ❌ "Tráfego de rede não aparece"
```
1. Configure o proxy manualmente no Wi-Fi do Android
2. Use o IP correto do seu PC (ipconfig/ifconfig)
3. Porta: 8888
4. Teste acessando http://mitm.it
```

---

## 📊 Exemplos de Análise

### Caso 1: Identificar Crashes
```
📱 ANÁLISE DE LOGS ADB
----------------------------------------
⚠️ ERROS ENCONTRADOS (15):

[1] 2024-03-31 14:23:15.123 - AndroidRuntime
    FATAL EXCEPTION: main
    java.lang.NullPointerException: Attempt to invoke virtual method...
    
[2] 2024-03-31 14:25:32.456 - MyApp
    ERROR: Failed to sync data with server
    java.net.SocketTimeoutException
```

### Caso 2: Análise de Sincronização
```
🌐 ANÁLISE DE TRÁFEGO DE REDE
----------------------------------------
Endpoints mais acessados:
  api.empresa.com/sync: 47 requests
  api.empresa.com/auth: 12 requests
  
Métodos HTTP:
  POST: 45
  GET: 14
  
Status codes:
  200: 52 (sucesso)
  401: 5 (não autorizado)
  500: 2 (erro no servidor)
```

---

## 🎓 Dicas Avançadas

### 1. **Filtrar logs específicos**
```python
# Modifique o método filter_log() em apk_monitor_pro.py
def filter_log(self, log_entry):
    # Exemplo: apenas erros de sincronização
    return 'sync' in log_entry['message'].lower() and \
           log_entry['level'] in ['E', 'F']
```

### 2. **Salvar logs automaticamente**
```python
# Adicione no método on_log_received()
with open('logs_autosave.txt', 'a') as f:
    f.write(f"{log_entry['timestamp']} - {log_entry['message']}\n")
```

### 3. **Alertas em tempo real**
```python
# Adicione no método on_log_received()
if log_entry['level'] == 'F':  # Fatal error
    QMessageBox.critical(self, "CRASH DETECTADO!", log_entry['message'])
```

---

## 📝 Estrutura de Arquivos

```
apk_monitor_pro/
│
├── apk_monitor_pro.py          # Aplicação principal
├── install_dependencies.py     # Instalador de dependências
├── build_exe.py               # Gerador de executável
├── README.md                  # Este arquivo
│
└── dist/                      # Gerado após build_exe.py
    └── APKMonitorPro.exe      # Executável Windows
```

---

## 🤝 Reportando Erros para a Fábrica

Com o APK Monitor Pro, você pode:

1. **Gerar relatório HTML** com todos os logs
2. **Destacar erros específicos** com timestamps
3. **Mostrar tráfego de rede** que falhou
4. **Provar problemas** com evidências técnicas

**Exemplo de relatório:**
```
ERRO CRÍTICO DETECTADO

Timestamp: 2024-03-31 14:23:15.123
Tipo: NullPointerException
Classe: com.empresa.app.SyncManager
Método: syncData()

Tráfego de rede relacionado:
- POST https://api.empresa.com/sync
- Status: 500 Internal Server Error
- Response: {"error": "Database connection failed"}

Conclusão: Servidor retornou erro 500, causando crash na APK
```

---

## 📞 Suporte

Problemas? Dúvidas? 

- Verifique a seção "Solução de Problemas"
- Confira se ADB está funcionando: `adb devices`
- Teste o proxy: acesse `http://mitm.it` no Android

---

## 📜 Licença

Livre para uso pessoal e comercial.

---

**Desenvolvido para análise profissional de APKs Android** 🚀
