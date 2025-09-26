# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['speech_recognition', 'pydub', 'moviepy'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tensorflow', 'torch', 'torchvision', 'torchaudio', 'transformers', 'sklearn', 'scipy', 'matplotlib', 'numpy', 'opencv-python', 'pillow', 'pandas', 'h5py', 'grpc', 'google', 'cv2', 'PyQt5', 'zmq', 'sqlite3', 'imageio', 'fsspec'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SubSync',
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
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SubSync',
)
