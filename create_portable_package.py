"""
Cria Pacote Portátil Completo do APK Monitor Pro
Incluindo ADB, não requer permissões de admin
"""

import shutil
import zipfile
from pathlib import Path
import urllib.request

print("=" * 70)
print("CRIANDO PACOTE PORTÁTIL - APK MONITOR PRO")
print("=" * 70)
print()

# 1. Verifica se executável existe
exe_path = Path("dist/APKMonitorPro.exe")
if not exe_path.exists():
    print("❌ APKMonitorPro.exe não encontrado em dist/")
    print("   Execute o build primeiro: python build_windows.py")
    exit(1)

print("✅ Executável encontrado")

# 2. Cria estrutura portátil
portable_dir = Path("dist/APK_Monitor_Portable")
if portable_dir.exists():
    shutil.rmtree(portable_dir)

portable_dir.mkdir(parents=True)
print(f"✅ Pasta criada: {portable_dir}")

# 3. Copia executável
print("📦 Copiando executável...")
shutil.copy(exe_path, portable_dir / "APKMonitorPro.exe")

# 4. Baixa/copia ADB
adb_dir = portable_dir / "adb"
adb_dir.mkdir()

platform_tools = Path("platform-tools")

if not platform_tools.exists():
    print("📥 Baixando Platform Tools (ADB)...")
    url = "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"
    zip_file = "platform-tools.zip"
    
    urllib.request.urlretrieve(url, zip_file)
    print("   Extraindo...")
    
    import zipfile
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        zip_ref.extractall(".")
    
    Path(zip_file).unlink()
    print("   ✅ Platform Tools baixado")

# Copia arquivos ADB necessários
print("📦 Copiando ADB...")
files_to_copy = [
    "adb.exe",
    "AdbWinApi.dll",
    "AdbWinUsbApi.dll"
]

for file in files_to_copy:
    src = platform_tools / file
    if src.exists():
        shutil.copy(src, adb_dir / file)
        print(f"   ✅ {file}")
    else:
        print(f"   ⚠️  {file} não encontrado")

# 5. Cria script .bat
print("📝 Criando script inicializador...")

batch_content = """@echo off
REM ============================================
REM APK Monitor Pro - Inicializador Portátil
REM ============================================

title APK Monitor Pro

set CURRENT_DIR=%~dp0

cls
echo.
echo ================================================
echo    APK MONITOR PRO - VERSAO PORTATIL
echo ================================================
echo.

if not exist "%CURRENT_DIR%APKMonitorPro.exe" (
    echo [ERRO] APKMonitorPro.exe nao encontrado!
    pause
    exit /b 1
)

if exist "%CURRENT_DIR%adb\\adb.exe" (
    echo [OK] ADB encontrado
    set PATH=%PATH%;%CURRENT_DIR%adb
)

echo [OK] Iniciando APK Monitor Pro...
echo.

start "" "%CURRENT_DIR%APKMonitorPro.exe"

timeout /t 2 /nobreak >nul
echo.
echo [OK] Programa iniciado!
echo Pode fechar esta janela.
echo.
timeout /t 3 /nobreak >nul
"""

(portable_dir / "Start_APK_Monitor.bat").write_text(batch_content, encoding='utf-8')

# 6. Cria README
print("📝 Criando README...")

readme_content = """APK MONITOR PRO - VERSAO PORTATIL
===================================

VERSAO: 2.0 Portable
PLATAFORMA: Windows 10/11

COMO USAR:
----------

1. Conecte seu dispositivo Android via USB
2. Clique duas vezes em "Start_APK_Monitor.bat"
3. Pronto!

REQUISITOS:
-----------

✅ Windows 10 ou superior
✅ Dispositivo Android com USB Debug ativo
✅ Cabo USB

NAO PRECISA:
------------

❌ Permissões de administrador
❌ Instalar ADB separadamente
❌ Configurar variáveis de ambiente
❌ Instalar Python ou dependências

CONTEUDO DO PACOTE:
-------------------

📁 APK_Monitor_Portable/
  ├── Start_APK_Monitor.bat    ← EXECUTE ESTE ARQUIVO
  ├── APKMonitorPro.exe        ← Programa principal
  ├── README.txt               ← Este arquivo
  └── adb/
      ├── adb.exe              ← Android Debug Bridge
      ├── AdbWinApi.dll
      └── AdbWinUsbApi.dll

TROUBLESHOOTING:
----------------

❓ "Nenhum dispositivo encontrado"
→ Verifique se USB Debug está ativo no Android
→ Aceite a mensagem de autorização no Android
→ Tente outro cabo ou porta USB

❓ "Windows protegeu seu PC"
→ Clique em "Mais informações"
→ Clique em "Executar assim mesmo"

❓ Antivírus bloqueou
→ Adicione exceção para APKMonitorPro.exe
→ É falso positivo, o programa é seguro

SUPORTE:
--------

GitHub: https://github.com/seu-usuario/apk-monitor-pro
Email: suporte@example.com

LICENÇA:
--------

[Adicione sua licença aqui]

Copyright © 2024
"""

(portable_dir / "README.txt").write_text(readme_content, encoding='utf-8')

# 7. Verifica integridade
print()
print("🔍 Verificando integridade...")

required_files = [
    "APKMonitorPro.exe",
    "Start_APK_Monitor.bat",
    "README.txt",
    "adb/adb.exe",
    "adb/AdbWinApi.dll",
    "adb/AdbWinUsbApi.dll"
]

all_ok = True
for file in required_files:
    file_path = portable_dir / file
    if file_path.exists():
        size = file_path.stat().st_size / 1024
        print(f"   ✅ {file:<30} ({size:.1f} KB)")
    else:
        print(f"   ❌ {file:<30} FALTANDO!")
        all_ok = False

if not all_ok:
    print()
    print("⚠️  Alguns arquivos estão faltando!")
    exit(1)

# 8. Cria ZIP
print()
print("📦 Criando arquivo ZIP...")

zip_path = Path("dist/APK_Monitor_Pro_Portable.zip")
if zip_path.exists():
    zip_path.unlink()

with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for file in portable_dir.rglob('*'):
        if file.is_file():
            arcname = file.relative_to(portable_dir.parent)
            zipf.write(file, arcname)
            print(f"   ✅ {arcname}")

# Calcula tamanho
zip_size = zip_path.stat().st_size / (1024 * 1024)

print()
print("=" * 70)
print("✅ PACOTE PORTÁTIL CRIADO COM SUCESSO!")
print("=" * 70)
print()
print(f"📁 Pasta: {portable_dir.absolute()}")
print(f"📦 ZIP:   {zip_path.absolute()}")
print(f"💾 Tamanho: {zip_size:.1f} MB")
print()
print("🚀 DISTRIBUIR:")
print("   1. Envie o arquivo ZIP para os usuários")
print("   2. Eles extraem o ZIP")
print("   3. Executam Start_APK_Monitor.bat")
print("   4. PRONTO!")
print()
print("✅ NÃO REQUER:")
print("   ❌ Permissões de administrador")
print("   ❌ Instalação de ADB")
print("   ❌ Configuração de PATH")
print()
print("=" * 70)
