# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['apk_monitor_pro.py'],
    pathex=[],
    binaries=[],
    datas=[('apk_monitor_pro', 'apk_monitor_pro')],
    hiddenimports=['apk_monitor_pro.core.adb_manager', 'apk_monitor_pro.analyzers.error_diagnostics', 'apk_monitor_pro.integrations.frida_hook', 'apk_monitor_pro.integrations.tcpdump_capture', 'apk_monitor_pro.utils.report_generator'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='APKMonitorPro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
app = BUNDLE(
    exe,
    name='APKMonitorPro.app',
    icon=None,
    bundle_identifier=None,
)
