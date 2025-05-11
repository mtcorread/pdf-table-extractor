# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

a = Analysis(
    ['main.py'],
    pathex=[
        '/Users/marthacorrea/Desktop/ClaudeMCPProjects/PDFTable-Extractor-Helper-main',  # Add the project root path
    ],
    binaries=[],
    datas=[
        ('gui', 'gui'),  # Include the gui directory
        ('core', 'core'),  # Include the core directory
        ('image', 'image'),  # Include the image directory
        ('utils', 'utils'),  # Include the utils directory if you have one
    ],
    hiddenimports=[
        'gui', 'gui.app', 'gui.menu', 'gui.toolbar', 'gui.main_area', 'gui.status_bar', 'gui.dialogs',
        'core', 'core.pdf_handler', 'core.table_extractor', 'core.marker_manager',
        'core.config_manager', 'core.manual_input', 'core.text_orientation_corrector',
        'image', 'image.area_processor', 'image.line_detector',
        'utils', 'utils.exporters',
        'fitz', 'PIL', 'numpy', 'pandas', 'openpyxl',
        'tkinter', 'tkinter.filedialog', 'tkinter.messagebox', 'tkinter.ttk'
    ],
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
    name='PDF Table Extractor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
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
    name='PDF Table Extractor',
)

app = BUNDLE(
    coll,
    name='PDF Table Extractor.app',
    icon='icon/app.icns',
    bundle_identifier='com.your.pdftableextractor',
    info_plist={
        'NSHighResolutionCapable': True,
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0'
    }
)