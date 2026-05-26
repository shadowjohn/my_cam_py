# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['my_cam_py.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['_ssl', '_bz2', '_lzma', 'pyconfig', 'pytorch', 'torch', 'sqlite3', 'pandas', 'IPython', 'scipy', 'matplotlib', 'contourpy', 'cycler', 'fontTools', 'kiwisolver', 'tornado', 'pygments', 'pyinstaller', 'tensorflow', 'unittest', 'doctest', 'pillow', 'av', 'requests', 'urllib3', 'certifi', 'charset_normalizer', 'idna', 'setuptools', 'PIL'],
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
    name='my_cam_py',
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
    version='metadata.txt',
    icon=['pic\\icon.ico'],
)
