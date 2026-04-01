# 📱 Guia Simples - APK Monitor Pro
## Para Equipe Não-Técnica

Este guia explica como usar a ferramenta **sem conhecimento técnico**.

---

## 🎯 Para que serve?

O APK Monitor Pro ajuda você a:
- ✅ **Ver erros** que acontecem na APK
- ✅ **Entender** por que os erros acontecem (em português!)
- ✅ **Gerar relatórios** para enviar à fábrica
- ✅ **Descobrir** problemas de sincronização e internet

---

## 🚀 Como Usar (Passo a Passo)

### Passo 1: Preparar o Computador e Celular

#### No Computador:
1. Instale o programa:
   ```
   python install_dependencies.py
   ```

2. Conecte o celular/PDA no computador com **cabo USB**

3. No celular, quando aparecer mensagem perguntando sobre "Depuração USB", clique em **"Permitir"**

#### Verificar se está tudo OK:
```
python test_system.py
```

Se aparecer ✅ em tudo, pode continuar!

---

### Passo 2: Abrir o Programa

```
python apk_monitor_pro.py
```

Vai abrir uma janela assim:

```
┌─────────────────────────────────────────────┐
│ APK Monitor Pro                              │
├─────────────────────────────────────────────┤
│ APK: [🇧🇷 São Paulo - Enel ▼]               │
│ Nível: [I (Info) ▼]  Porta: [8888]          │
│ [▶️ Iniciar]  [⏹️ Parar]                     │
├─────────────────────────────────────────────┤
│ Abas: Logs | Rede | Erros | SQLite | Rel.  │
└─────────────────────────────────────────────┘
```

---

### Passo 3: Escolher a APK

Clique no menu **"APK:"** e escolha qual você quer monitorar:
- 🇧🇷 Rio - Ampla
- 🇧🇷 São Paulo - Enel  ← **Exemplo**
- 🇧🇷 Ceará - Coelce

---

### Passo 4: Iniciar o Monitoramento

1. Clique no botão verde **"▶️ Iniciar"**

2. Você vai ver uma mensagem:
   ```
   ✅ Monitorando São Paulo - Enel...
   ```

3. **Agora use a APK normalmente no celular!**
   - Faça o que você normalmente faz
   - Tente reproduzir o problema/erro
   - Use as funções que dão erro

---

### Passo 5: Ver os Erros com Explicação

Enquanto usa a APK, o programa está capturando tudo!

#### Para ver erros:

1. Clique na aba **"❌ Análise de Erros"**

2. Vai aparecer uma lista de erros encontrados:
   ```
   [14:23:15] 🌐 Erro de Conexão - Servidor não encontrado
   [14:25:30] ⏱️ Timeout - Servidor demorou muito
   [14:27:10] 🔄 Erro de Sincronização
   ```

3. **Clique em um erro** para ver explicação completa:

```
┌────────────────────────────────────────┐
│ 🌐 Erro de Conexão                     │
├────────────────────────────────────────┤
│ 📝 O que aconteceu?                    │
│ O dispositivo não conseguiu encontrar  │
│ o servidor na internet.                │
│                                        │
│ 🔍 Possíveis Causas:                   │
│ • Dispositivo sem internet             │
│ • Servidor fora do ar                  │
│ • WiFi desligado                       │
│                                        │
│ ✅ Como Resolver:                      │
│ 1. Verificar se WiFi está ligado      │
│ 2. Tentar outro site para testar      │
│ 3. Aguardar e tentar novamente         │
└────────────────────────────────────────┘
```

**Agora você entende o erro em português!** 🎉

---

### Passo 6: Gerar Relatório para a Fábrica

Quando encontrar um erro, você precisa reportar:

1. Clique na aba **"📄 Relatórios"**

2. Marque o que quer incluir:
   - ✅ Incluir Logs ADB
   - ✅ Incluir Tráfego de Rede
   - ✅ Incluir Análise de Erros

3. Clique em **"📄 Gerar Relatório HTML Completo"**

4. Escolha onde salvar (ex: Desktop/relatorio_erro.html)

5. **Abra o arquivo HTML** para ver:
   - Todos os erros encontrados
   - Explicação de cada erro
   - Horário exato que ocorreu
   - O que fazer para resolver

6. **Envie este arquivo HTML para a fábrica!**

---

## 🔍 Como Usar os Filtros (Simplificado)

Na aba **"📱 Logs ADB"**, você tem filtros rápidos:

### Para ver apenas erros:
✅ Marque: **"Apenas Erros"**

### Para ver problemas de sincronização:
✅ Marque: **"Sync"** + **"Apenas Erros"**

### Para ver problemas de internet:
✅ Marque: **"Network"** + **"Apenas Erros"**

### Combinação Útil:
Para investigar erro de sincronização:
- ✅ Sync
- ✅ Apenas Erros
- ✅ Exceptions

Agora você vê APENAS erros de sincronização!

---

## 🌐 Como Capturar Tráfego de Internet

Se você quer ver **o que a APK envia e recebe** do servidor:

### Passo 1: Configurar Proxy no Celular

1. No celular, vá em: **Configurações → WiFi**

2. **Toque e segure** na rede WiFi conectada

3. Escolha **"Modificar rede"** ou **"Configurações avançadas"**

4. Proxy → **Manual**

5. Preencha:
   - **Servidor:** [IP do seu computador]
   - **Porta:** 8888

   *Para saber o IP do PC, execute:*
   ```
   python test_system.py
   ```
   *Vai mostrar algo como: "IP local: 192.168.1.100"*

6. **Salve**

### Passo 2: Ver o Tráfego

1. No APK Monitor Pro, clique na aba **"🌐 Tráfego de Rede"**

2. Use a APK normalmente

3. Você vai ver:
   ```
   ┌────────────────────────────────────────────┐
   │ 14:30:15 | REQUEST | POST | api.empresa... │
   │ 14:30:16 | RESPONSE | 200 | api.empresa... │
   └────────────────────────────────────────────┘
   ```

4. **Clique em uma linha** para ver detalhes:
   - O que a APK enviou
   - O que o servidor respondeu
   - Headers (informações técnicas)
   - Dados enviados e recebidos

---

## 📊 Exemplo Real de Uso

### Situação: Erro de Sincronização

1. Você abre a APK no celular
2. Tenta sincronizar
3. Aparece: **"Erro de sincronização"** 😠

**O que fazer?**

1. **No APK Monitor Pro:**
   - Ative filtros: **Sync + Apenas Erros**
   
2. **Olhe os logs:**
   ```
   [14:25:30] E/SyncManager: SocketTimeoutException: timeout
   ```

3. **Vá na aba "Análise de Erros":**
   ```
   ⏱️ Timeout - Servidor demorou muito para responder
   
   Causas possíveis:
   • Internet muito lenta
   • Servidor sobrecarregado
   
   Soluções:
   1. Verificar qualidade da internet
   2. Tentar novamente em alguns minutos
   ```

4. **Gere relatório HTML**

5. **Envie para a fábrica** dizendo:
   ```
   "Ocorreu erro de timeout durante sincronização.
   Veja relatório anexo com detalhes técnicos.
   Ocorreu em 31/03/2026 às 14:25:30."
   ```

**Pronto!** Você reportou o erro de forma profissional! 🎉

---

## 🆘 Problemas Comuns

### "Nenhum log aparece"
✅ Verifique se selecionou a APK correta no dropdown  
✅ Verifique se o celular está conectado via USB  
✅ Execute: `adb devices` para confirmar conexão

### "Erro no proxy"
✅ Não se preocupe! Você pode usar só os logs ADB  
✅ Desmarque "Habilitar Proxy" e clique em Iniciar

### "Muitos logs, não acho o erro"
✅ Use os filtros! Marque "Apenas Erros"  
✅ Ou vá direto na aba "Análise de Erros"

---

## 💡 Dicas Importantes

### ✅ Sempre faça isso:
1. **Conecte o celular** antes de abrir o programa
2. **Aceite "Depuração USB"** quando aparecer no celular
3. **Reproduza o erro** enquanto monitora
4. **Gere relatório** logo depois do erro

### ❌ Evite fazer isso:
1. Desconectar o celular enquanto monitora
2. Fechar o programa antes de gerar relatório
3. Esquecer de anotar horário do erro

---

## 📝 Template de Reporte para Fábrica

Quando reportar erro, use este modelo:

```
Assunto: Erro na APK [Nome da APK] - [Tipo do Erro]

Olá,

Encontrei um erro na APK durante uso em campo:

📱 APK: [Rio/São Paulo/Ceará]
⏰ Data/Hora: [31/03/2026 14:25:30]
❌ Erro: [Erro de Sincronização]
📝 Descrição: [Ao tentar sincronizar, apareceu mensagem 
              "Erro de sincronização" e não completou]

🔍 Análise:
[Cole aqui o que apareceu na aba "Análise de Erros"]

📎 Anexo: relatorio_completo.html

Aguardo retorno sobre correção.

Atenciosamente,
[Seu Nome]
```

---

## 🎓 Resumo Final

| O que fazer | Como fazer |
|-------------|------------|
| Ver erros com explicação | Aba "Análise de Erros" |
| Ver só erros importantes | Filtro "Apenas Erros" |
| Ver problemas de sync | Filtros "Sync + Apenas Erros" |
| Ver internet | Aba "Tráfego de Rede" |
| Gerar relatório | Aba "Relatórios" → HTML |

---

**Dúvidas?** Consulte o README.md completo ou peça ajuda!

**Tempo para aprender:** 15 minutos  
**Tempo para gerar relatório:** 2 minutos  
**Valor:** Reportes profissionais à fábrica! 🚀
