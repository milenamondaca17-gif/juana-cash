# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_submodules

datas = [('backend', 'backend'), ('desktop', 'desktop'), ('juana_cash.db', '.')]
binaries = []
hiddenimports = [
    'uvicorn.lifespan.on', 'uvicorn.loops.auto',
    'uvicorn.protocols.http.auto', 'uvicorn.protocols.websockets.auto',
    'passlib.handlers.bcrypt', 'sqlalchemy.dialects.sqlite',
    'requests', 'urllib3', 'charset_normalizer', 'certifi', 'idna',
    'email', 'email.mime', 'email.mime.text', 'email.mime.multipart',
    'email.mime.base', 'email.mime.application', 'email.encoders', 'smtplib',
    'PyQt6', 'PyQt6.QtWidgets', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtPrintSupport',
]

for pkg in ['uvicorn', 'fastapi', 'sqlalchemy', 'passlib', 'jose',
            'starlette', 'pydantic', 'anyio', 'h11', 'requests']:
    tmp = collect_all(pkg)
    datas += tmp[0]; binaries += tmp[1]; hiddenimports += tmp[2]

# Incluir todos los submodulos del UI de desktop
hiddenimports += collect_submodules('ui')
hiddenimports += collect_submodules('PyQt6')


a = Analysis(
    ['JuanaCash_main.py'],
    pathex=['desktop', 'backend'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    [],
    exclude_binaries=True,
    name='JuanaCash',
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
    icon=['juana_cash.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='JuanaCash',
)
