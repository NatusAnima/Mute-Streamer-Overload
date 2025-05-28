# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('mute_streamer_overload/web/templates', 'mute_streamer_overload/web/templates')],
    hiddenimports=['flask', 'flask_socketio', 'engineio.async_drivers.threading', 'eventlet.hubs.epolls', 'eventlet.hubs.kqueue', 'eventlet.hubs.selects', 'dns', 'requests', 'urllib3', 'idna', 'chardet', 'certifi', 'jinja2', 'jinja2.ext', 'jinja2.loaders', 'jinja2.environment', 'jinja2.utils', 'jinja2.filters', 'jinja2.runtime', 'jinja2.async_utils', 'jinja2.bccache', 'jinja2.debug', 'jinja2.exceptions', 'jinja2.nodes', 'jinja2.optimizer', 'jinja2.parser', 'jinja2.sandbox', 'jinja2.visitor', 'werkzeug', 'werkzeug.serving', 'werkzeug.middleware', 'werkzeug.debug', 'werkzeug.security', 'werkzeug.wsgi', 'werkzeug.http', 'werkzeug.datastructures', 'werkzeug.formparser', 'werkzeug.local', 'werkzeug.routing', 'werkzeug.test', 'werkzeug.urls', 'werkzeug.utils', 'werkzeug.wrappers', 'werkzeug.wrappers.json', 'werkzeug.wrappers.response', 'werkzeug.wrappers.request', 'werkzeug.wrappers.base_response', 'werkzeug.wrappers.base_request', 'werkzeug.wrappers.accept', 'werkzeug.wrappers.etag', 'werkzeug.wrappers.cors'],
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
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    uac_admin=True,
    icon=['assets\\icon.ico'],
)
