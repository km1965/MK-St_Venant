# -*- mode: python ; coding: utf-8 -*-
"""
Spec PyInstaller pour MK-St_Venant (Allievi / Strickler-Bernoulli).
Build Windows (one-folder) avec icône et assets embarqués.
"""

from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None
project_dir = Path(SPECPATH).resolve()

# Données CustomTkinter (thèmes, assets UI) et ressources de l'application
datas = []
datas += collect_data_files("customtkinter")
datas += [(str(project_dir / "assets"), "assets")]
# Catalogue source MCP joint au livrable pour traçabilité des débits utilisés.
datas += [(str(project_dir / "Tableau_Recapitulatif_Debits_Ventouses_MCP.xlsx"), ".")]

hiddenimports = []
hiddenimports += collect_submodules("customtkinter")
hiddenimports += collect_submodules("core")
hiddenimports += collect_submodules("ui")
hiddenimports += [
    "matplotlib.backends.backend_tkagg",
    "openpyxl",
    "docx",
    "PIL",
    "numpy",
]

a = Analysis(
    [str(project_dir / "main.py")],
    pathex=[str(project_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "pytest",
        "IPython",
        "notebook",
        "jupyter",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Mk_Stvenant_Allievi_Strickler-Bernoulli",
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
    icon=str(project_dir / "assets" / "mk-st-venant-icon.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Mk_Stvenant_Allievi_Strickler-Bernoulli",
)
