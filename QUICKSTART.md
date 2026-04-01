# 🚀 INÍCIO RÁPIDO - APK Monitor Pro

## ⏱️ 5 Minutos para começar

### 1️⃣ Prepare o ambiente (2 min)

```bash
# Instale as dependências
python install_dependencies.py

# OU use pip diretamente
pip install -r requirements.txt
```

### 2️⃣ Conecte o dispositivo (1 min)

```bash
# Conecte via USB e verifique
adb devices

# Deve mostrar algo como:
# ABC123456789    device
```

**Se aparecer "unauthorized":**
- Aceite a mensagem no Android
- Execute `adb devices` novamente

### 3️⃣ Teste o sistema (1 min)

```bash
# Execute o teste
python test_system.py

# Deve mostrar ✅ em todos os itens
```

### 4️⃣ Execute a ferramenta (1 min)

```bash
# Inicie o APK Monitor Pro
python apk_monitor_pro.py
```

---

## 🎯 Uso Básico

### Passo 1: Configure
1. **APK**: Selecione no dropdown:
   - 🇧🇷 Rio (Ampla)
   - 🇧🇷 São Paulo (Enel)
   - 🇧🇷 Ceará (Coelce)
   - 📦 Personalizado (digite manualmente)

2. **Nível de Log**: Escolha "I (Info)" para começar

3. **Porta Proxy**: Deixe 8888 (padrão)

### Passo 1.1: Use Filtros Rápidos (Opcional)
Para focar em problemas específicos, ative filtros:
- **Sync** → Ver apenas sincronizações
- **Apenas Erros** → Só erros e warnings
- **Network** → Problemas de rede
- **Exceptions** → Exceções lançadas
- **Crashes** → Erros fatais

Combine filtros! Ex: "Sync" + "Apenas Erros" = erros de sync

### Passo 2: Inicie
1. Clique em **"▶️ Iniciar Monitoramento"**
2. Use a APK no dispositivo
3. Veja os logs aparecendo em tempo real

### Passo 3: Configure proxy no Android (Para tráfego HTTPS)

**Opção Rápida (via ADB):**
```bash
adb reverse tcp:8888 tcp:8888
```

**Opção Manual (Wi-Fi):**
1. Configurações → Wi-Fi → Sua rede
2. Configurar Proxy → Manual
3. Servidor: [SEU_IP] (mostrado no test_system.py)
4. Porta: 8888

### Passo 4: Analise
1. Tab **"Logs ADB"**: Veja erros e exceções
2. Tab **"Tráfego de Rede"**: Veja requests/responses
3. Tab **"Análise"**: Clique em "Analisar"
4. Tab **"Relatórios"**: Gere HTML ou JSON

---

## 💡 Dicas Rápidas

### ✅ Para monitorar APK específica
- Basta selecionar no dropdown: Rio, São Paulo ou Ceará

### ✅ Para ver apenas erros de sincronização
- Ative: "Sync" + "Apenas Erros"

### ✅ Para ver apenas crashes
- Ative: "Crashes" + "Apenas Erros"

### ✅ Para ver apenas erros
- Mude nível para "E (Error)" OU ative filtro "Apenas Erros"

### ✅ Para descobrir nome de outro pacote
```bash
adb shell pm list packages | grep palavra_chave
```

### ✅ Para limpar logs antigos
- Clique em "🗑️ Limpar Logs"

### ✅ Para ver HTTPS
1. Inicie o proxy
2. No Android, acesse: http://mitm.it
3. Baixe e instale o certificado

---

## 🐛 Problemas Comuns

| Problema | Solução |
|----------|---------|
| "ADB não encontrado" | Instale Android Platform Tools |
| "Device unauthorized" | Aceite mensagem no Android |
| "Nenhum log aparece" | Verifique se selecionou a APK correta |
| "Muitos logs não relevantes" | Use filtros rápidos (Sync, Errors, etc) |
| "Proxy não funciona" | Configure proxy no Wi-Fi |
| "Não vê HTTPS" | Instale certificado mitmproxy |

---

## 📊 O que você pode descobrir

### 🔍 Logs ADB
- ✅ Crashes e exceções
- ✅ Erros de sincronização
- ✅ Problemas de classes
- ✅ Stack traces completos

### 🌐 Tráfego de Rede
- ✅ O que o PDA envia para o servidor
- ✅ O que o servidor retorna
- ✅ Headers completos (tokens, auth, etc)
- ✅ Body dos requests e responses
- ✅ Status codes (200, 404, 500, etc)

---

## 🎓 Próximos Passos

1. **Gere relatórios** para a fábrica
2. **Personalize filtros** em config.json
3. **Use utilitários** em utils.py para análise avançada
4. **Crie executável** com build_exe.py

---

## 🚀 Workflow Recomendado

```
1. Conectar dispositivo
   ↓
2. Iniciar APK Monitor Pro
   ↓
3. Configurar nome do pacote
   ↓
4. Iniciar monitoramento
   ↓
5. Reproduzir o problema na APK
   ↓
6. Parar monitoramento
   ↓
7. Analisar dados
   ↓
8. Gerar relatório HTML
   ↓
9. Enviar para a fábrica
```

---

**Tempo total de setup: ~5 minutos**
**Tempo para capturar logs: Variável (conforme uso)**
**Tempo para gerar relatório: ~30 segundos**

---

Dúvidas? Consulte o README.md completo!
