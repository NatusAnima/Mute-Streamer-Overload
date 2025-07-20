# -*- mode: python ; coding: utf-8 -*-

import importlib.util
import os

pyexpat_spec = importlib.util.find_spec("pyexpat")
pyexpat_pyd = os.path.join(os.path.dirname(pyexpat_spec.origin), "pyexpat.pyd")


a = Analysis(
    ['main.py'],
    pathex=[],
    datas=[('mute_streamer_overload\\web\\templates', 'mute_streamer_overload/web/templates'),
           ('mute_streamer_overload\\web\\static', 'mute_streamer_overload/web/static')],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MuteStreamerOverload',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets\\icon_256x256.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MuteStreamerOverload',
)
