# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('mute_streamer_overload\\web\\templates', 'mute_streamer_overload\\web\\templates'), ('mute_streamer_overload\\web\\static', 'mute_streamer_overload\\web\\static'), ('C:\\Users\\iyave\\Desktop\\Mute Streamer Overload\\.venv\\Lib\\site-packages\\PyQt6\\Qt6\\plugins', 'PyQt6/Qt6/plugins'), ('assets', 'assets')],
    hiddenimports=['PyQt6', 'PyQt6.sip', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets', 'PyQt6.QtSvg', 'flask', 'flask_socketio', 'engineio.async_drivers.threading', 'werkzeug', 'jinja2', 'requests', 'keyboard'],
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
    name='MuteStreamerOverload',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    uac_admin=True,
    icon=['assets\\icon_256x256.ico'],
)
