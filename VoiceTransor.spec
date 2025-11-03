# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for VoiceTransor
Usage: pyinstaller VoiceTransor.spec
"""

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all translation files
datas = [
    ('app/i18n/locales/*.qm', 'app/i18n/locales'),
    ('app/i18n/locales/*.ts', 'app/i18n/locales'),
]

# Collect Whisper model data if needed
# Note: Models are downloaded at runtime, but we include the module data
whisper_datas = collect_data_files('whisper')

# Collect PyTorch data files (includes CUDA DLLs and libraries)
# These will be filtered to remove .lib, .h, .c files
torch_datas = collect_data_files('torch', include_py_files=False)
torch_datas += collect_data_files('torchaudio', include_py_files=False)
torch_datas += collect_data_files('tiktoken_ext', include_py_files=False)

# Add whisper datas WITHOUT filtering (whisper needs all its data files)
datas += whisper_datas

# Add torch datas (will be filtered later)
datas += torch_datas

# Hidden imports for dynamic loading
hiddenimports = []
hiddenimports += collect_submodules('whisper')
hiddenimports += collect_submodules('pydub')

# Collect ALL torch submodules to ensure nothing is missing
# The size increase from extra modules is acceptable (~100MB) vs broken functionality
hiddenimports += collect_submodules('torch')
hiddenimports += collect_submodules('torchaudio')

# Other essential imports
hiddenimports += [
    'PySide6.QtCore',
    'PySide6.QtWidgets',
    'PySide6.QtGui',
    'openai',
    'requests',
    'markdown_it',
    'tiktoken',
    'tiktoken_ext',
    'tiktoken_ext.openai_public',
]

a = Analysis(
    ['run.py'],  # Entry point
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Data science libraries (not used)
        'matplotlib',
        'scipy',
        'pandas',
        'sklearn',
        # Computer vision (not used)
        'torchvision',
        # NOTE: PIL/Pillow is needed by reportlab for PDF generation
        # 'PIL',  # DO NOT exclude - needed by dependencies
        'cv2',
        # JIT compilation - NOTE: numba is needed by whisper.timing!
        # 'numba',  # DO NOT exclude - needed by whisper.timing
        # 'llvmlite',  # DO NOT exclude - needed by numba
        # Testing frameworks
        'pytest',
        # NOTE: unittest is needed by torch.testing (required by torch.autograd)
        # 'unittest',  # DO NOT exclude - needed by torch.testing
        'test',
        # Documentation
        'sphinx',
        'docutils',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Filter out unnecessary files to reduce package size
# Only filter torch-related files, keep whisper and other packages intact
original_count = len(a.datas)
filtered_datas = []
torch_filtered = 0

for item in a.datas:
    dest_name = item[0]
    # Only apply filter to torch/torchaudio/tiktoken files
    if any(x in dest_name for x in ['torch/', 'torch\\', 'torchaudio/', 'torchaudio\\', 'tiktoken/', 'tiktoken\\']):
        # Apply filtering
        should_keep = True
        dest_lower = dest_name.lower()

        # Check excluded extensions
        excluded_extensions = {'.lib', '.a', '.h', '.hpp', '.c', '.cpp', '.cu', '.cuh', '.cmake'}
        if any(dest_lower.endswith(ext) for ext in excluded_extensions):
            should_keep = False
            torch_filtered += 1

        # Check excluded directories (but keep torch/testing as it's required)
        excluded_dirs = {'include', 'Include', 'cmake', 'pkgconfig', 'test', 'tests', '_testing'}
        if should_keep and any(f'/{excl_dir}/' in dest_name or f'\\{excl_dir}\\' in dest_name for excl_dir in excluded_dirs):
            if not any(dest_lower.endswith(keep_ext) for keep_ext in {'.dll', '.so', '.pyd', '.dylib'}):
                should_keep = False
                torch_filtered += 1

        if should_keep:
            filtered_datas.append(item)
    else:
        # Keep all non-torch files (including whisper)
        filtered_datas.append(item)

a.datas = filtered_datas
filtered_count = len(a.datas)
print(f"[FILTER] Data files: {original_count} → {filtered_count} (removed {torch_filtered} torch-related files, kept whisper intact)")

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='VoiceTransor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window (GUI app)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' if sys.platform == 'win32' else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='VoiceTransor',
)

# macOS: Create .app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='VoiceTransor.app',
        icon=None,  # Optional: Add macOS icon file path if available
        bundle_identifier='com.voicetransor.app',
        info_plist={
            'CFBundleName': 'VoiceTransor',
            'CFBundleDisplayName': 'VoiceTransor',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'NSHighResolutionCapable': 'True',
            'NSRequiresAquaSystemAppearance': 'False',
        },
    )
