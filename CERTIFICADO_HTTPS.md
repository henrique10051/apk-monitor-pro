# 🔐 Guia de Instalação do Certificado HTTPS

Para interceptar tráfego HTTPS (criptografado), você precisa instalar o certificado do mitmproxy no dispositivo Android.

---

## 📱 Instalação no Android

### Método 1: Via Navegador (Mais Fácil)

#### Passo 1: Configure o proxy
```
Configurações → Wi-Fi → Sua rede → Proxy Manual
Servidor: [IP do seu PC]
Porta: 8888
```

#### Passo 2: Inicie o proxy
1. Abra APK Monitor Pro
2. Clique em "Iniciar Monitoramento"
3. Aguarde status "Proxy iniciado na porta 8888"

#### Passo 3: Baixe o certificado
1. No navegador do Android, acesse: **http://mitm.it**
2. Clique no ícone do Android
3. Baixe o certificado

#### Passo 4: Instale o certificado
```
Configurações → Segurança → Criptografia e credenciais
→ Instalar certificado de CA
→ Escolha o arquivo baixado
→ Nomeie: "mitmproxy"
```

⚠️ **Android 7+**: Você pode precisar instalar como "certificado de usuário"

---

### Método 2: Via ADB (Requer Root)

Para Android com root:

```bash
# 1. Gere o certificado
cd ~/.mitmproxy
adb push mitmproxy-ca-cert.pem /sdcard/

# 2. Converta para formato Android
openssl x509 -inform PEM -outform DER \
  -in mitmproxy-ca-cert.pem \
  -out mitmproxy-ca-cert.crt

# 3. Envie para o dispositivo
adb push mitmproxy-ca-cert.crt /sdcard/

# 4. Instale
# Vá em Configurações → Segurança → Instalar de armazenamento
```

---

## ✅ Verificação

### Como saber se funcionou?

1. **Acesse um site HTTPS** no navegador
   - Ex: https://www.google.com

2. **Veja o tráfego no APK Monitor Pro**
   - Tab "Tráfego de Rede"
   - Deve aparecer requests HTTPS decodificados

3. **Teste com a APK**
   - Use a aplicação normalmente
   - Veja os requests/responses na ferramenta

---

## 🐛 Problemas Comuns

### ❌ "Certificado não confiável"

**Solução:**
```
Configurações → Segurança → Credenciais de usuário
→ Verifique se "mitmproxy" está listado
```

### ❌ "Não vejo conteúdo HTTPS"

**Possíveis causas:**

1. **Certificado não instalado**
   - Reinstale seguindo o método 1

2. **App usa Certificate Pinning**
   - Alguns apps (bancos, etc) não aceitam certificados personalizados
   - Solução: Requer técnicas avançadas (Frida, Xposed)

3. **Proxy não configurado**
   - Verifique IP e porta no Wi-Fi do Android

### ❌ "mitm.it não abre"

**Soluções:**

1. **Verifique se proxy está rodando**
   ```
   Status bar do APK Monitor Pro deve mostrar:
   "Proxy iniciado na porta 8888"
   ```

2. **Verifique configuração do proxy**
   ```bash
   # Teste de conectividade
   ping [IP_DO_PC]
   ```

3. **Use ADB reverse**
   ```bash
   adb reverse tcp:8888 tcp:8888
   ```

---

## 📋 Localização do Certificado

O certificado é gerado automaticamente pelo mitmproxy em:

- **Windows**: `C:\Users\[SEU_USUARIO]\.mitmproxy\`
- **Linux**: `~/.mitmproxy/`
- **Mac**: `~/.mitmproxy/`

Arquivos criados:
- `mitmproxy-ca-cert.pem` - Certificado PEM
- `mitmproxy-ca-cert.p12` - Para iOS
- `mitmproxy-ca-cert.cer` - Para Windows

---

## 🔒 Segurança

### ⚠️ IMPORTANTE:

1. **Remova o certificado após uso**
   ```
   Configurações → Segurança → Credenciais de usuário
   → Toque em "mitmproxy" → Remover
   ```

2. **Não compartilhe o certificado**
   - Qualquer pessoa com o certificado pode interceptar seu tráfego

3. **Use apenas em ambiente de teste**
   - Não use em dispositivos de produção
   - Ideal para PDAs de desenvolvimento/homologação

---

## 🎯 Android 7+ (Nougat)

A partir do Android 7, apps podem bloquear certificados de usuário.

### Solução 1: App em Debug Mode

Se você tem o APK em modo debug:

```xml
<!-- AndroidManifest.xml -->
<application
    android:networkSecurityConfig="@xml/network_security_config">
```

```xml
<!-- res/xml/network_security_config.xml -->
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <base-config>
        <trust-anchors>
            <certificates src="system" />
            <certificates src="user" />
        </trust-anchors>
    </base-config>
</network-security-config>
```

### Solução 2: Root + Magisk

Para instalar como certificado de sistema (requer root):

```bash
# 1. Calcule hash do certificado
openssl x509 -inform PEM -subject_hash_old \
  -in mitmproxy-ca-cert.pem | head -1

# 2. Renomeie (ex: se hash = c8750f0d)
mv mitmproxy-ca-cert.pem c8750f0d.0

# 3. Instale como certificado de sistema
adb root
adb remount
adb push c8750f0d.0 /system/etc/security/cacerts/
adb shell chmod 644 /system/etc/security/cacerts/c8750f0d.0
adb reboot
```

---

## ✨ Verificação Final

Execute este teste após instalar o certificado:

```bash
# No APK Monitor Pro:
1. Inicie monitoramento
2. Configure proxy no Android
3. No Android, acesse: https://www.google.com
4. Veja se aparece o request HTTPS completo na tab "Tráfego de Rede"

✅ Se viu o request/response = FUNCIONOU!
❌ Se aparece erro de certificado = Reinstale
⚠️ Se não aparece nada = Verifique proxy
```

---

## 🎓 Resumo

| Etapa | Comando/Local | Status |
|-------|---------------|--------|
| Configurar proxy | Wi-Fi → Proxy Manual | ✅ |
| Acessar mitm.it | http://mitm.it | ✅ |
| Baixar certificado | Clique no Android | ✅ |
| Instalar | Segurança → Instalar CA | ✅ |
| Testar | https://google.com | ✅ |

---

**Tempo estimado:** 5-10 minutos

**Dificuldade:** ⭐⭐☆☆☆ (Fácil)

---

Dúvidas sobre certificados? Consulte:
- Documentação mitmproxy: https://docs.mitmproxy.org/stable/
- README.md completo deste projeto
