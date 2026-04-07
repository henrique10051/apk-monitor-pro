@echo off
REM ============================================
REM APK Monitor Pro - Inicializador Portátil
REM Não requer permissões de administrador
REM ============================================

title APK Monitor Pro

REM Define o diretório atual
set CURRENT_DIR=%~dp0

REM Limpa a tela
cls

echo.
echo ================================================
echo    APK MONITOR PRO - INICIANDO
echo ================================================
echo.

REM Verifica se o executável existe
if not exist "%CURRENT_DIR%APKMonitorPro.exe" (
    color 0C
    echo [ERRO] APKMonitorPro.exe nao encontrado!
    echo.
    echo Certifique-se de que este script esta na mesma pasta
    echo que o APKMonitorPro.exe
    echo.
    pause
    exit /b 1
)

REM Verifica se a pasta ADB existe
if not exist "%CURRENT_DIR%adb" (
    color 0E
    echo [AVISO] Pasta 'adb' nao encontrada
    echo.
    echo O APK Monitor Pro pode usar ADB embutido,
    echo mas se der erro, crie a pasta 'adb' e coloque:
    echo   - adb.exe
    echo   - AdbWinApi.dll
    echo   - AdbWinUsbApi.dll
    echo.
    echo Baixe de: https://developer.android.com/tools/releases/platform-tools
    echo.
    timeout /t 3 /nobreak >nul
) else (
    REM Verifica se adb.exe existe
    if exist "%CURRENT_DIR%adb\adb.exe" (
        echo [OK] ADB encontrado!
        set PATH=%PATH%;%CURRENT_DIR%adb
        echo [OK] PATH configurado (temporariamente)
    ) else (
        color 0E
        echo [AVISO] adb.exe nao encontrado em 'adb\'
    )
)

echo.
echo ================================================
echo    VERIFICANDO DISPOSITIVOS
echo ================================================
echo.

REM Tenta listar dispositivos se ADB existir
if exist "%CURRENT_DIR%adb\adb.exe" (
    "%CURRENT_DIR%adb\adb.exe" devices
    echo.
) else (
    echo Verificacao de dispositivos sera feita pelo programa
    echo.
)

echo ================================================
echo    INICIANDO APK MONITOR PRO
echo ================================================
echo.

REM Inicia o executável
start "" "%CURRENT_DIR%APKMonitorPro.exe"

REM Aguarda 2 segundos
timeout /t 2 /nobreak >nul

echo [OK] APK Monitor Pro iniciado!
echo.
echo Voce pode fechar esta janela agora.
echo.
echo ================================================

REM Aguarda 3 segundos antes de fechar
timeout /t 3 /nobreak >nul

exit /b 0
