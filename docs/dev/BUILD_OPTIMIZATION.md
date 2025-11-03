# Build Size Optimization Guide

This document explains the build size optimizations applied to VoiceTransor and how to maintain a lean distribution package.

## Table of Contents

1. [Overview](#overview)
2. [Problem Discovery](#problem-discovery)
3. [Root Causes](#root-causes)
4. [Optimizations Applied](#optimizations-applied)
5. [Results](#results)
6. [Best Practices](#best-practices)

## Overview

### Initial Problem

During development, the build size grew from an expected **~4.2GB** to **~5.1GB** - an unwanted increase of **~900MB**.

Investigation revealed **870MB of unnecessary files** were being included in the distribution:
- **750MB**: Static library files (.lib, .a)
- **102MB**: Unused llvmlite package (JIT compilation)
- **15MB**: Unused torchvision package (computer vision)
- **54MB**: Source files, headers, and test directories

### Target Size

- **Built application**: ~4.2GB (includes CUDA support)
- **ZIP package**: ~4GB compressed
- **Installer**: ~450MB (highly compressed)

## Problem Discovery

### Timeline

1. **User error**: Ran build without activating conda environment
2. **Initial diagnosis**: Missing PyTorch dependencies
3. **Incorrect fix**: Added `collect_submodules('torch')` and `collect_submodules('torchaudio')`
4. **Result**: Build grew by **500MB** due to collecting ALL torch submodules
5. **Investigation**: Found additional 370MB of unnecessary files

### Files Included Unnecessarily

#### Static Libraries (750MB) - Largest Bloat Source

Static libraries (.lib on Windows, .a on Unix) are only needed at **compile/link time**, NOT at runtime:

```
_internal\torch\lib\
├── dnnl.lib               607 MB  ❌ Static library
├── libprotoc.lib           38 MB  ❌ Static library
├── asmjit.lib              35 MB  ❌ Static library
├── c10.lib                 12 MB  ❌ Static library
├── fbgemm.lib              11 MB  ❌ Static library
├── torch_cpu.lib            9 MB  ❌ Static library
└── ... (many more)

✅ Only .dll files are needed at runtime
❌ .lib files are for linking during development
```

#### Unused Python Packages (117MB)

Packages pulled in as dependencies but never used:

```
_internal\
├── llvmlite\              102 MB  ❌ JIT compilation (not used)
├── torchvision\            15 MB  ❌ Computer vision (not used)
└── numba\                   ~0 MB  ❌ Excluded explicitly
```

#### Development Files (54MB)

Source and header files not needed for runtime:

```
Various locations:
├── *.py files             ~30 MB  ❌ Python source (already compiled to .pyc)
├── *.h, *.hpp files       ~10 MB  ❌ C/C++ headers
├── *.cu, *.cuh files       ~5 MB  ❌ CUDA source files
├── *.c, *.cpp files        ~5 MB  ❌ C/C++ source
└── test/ directories       ~4 MB  ❌ Test files
```

## Root Causes

### 1. Using `collect_submodules()` Indiscriminately

**Problem code in VoiceTransor.spec:**

```python
# ❌ BAD - Collects EVERYTHING including tests, unused features
hiddenimports += collect_submodules('torch')
hiddenimports += collect_submodules('torchaudio')
```

This collected:
- All torch submodules (500+ modules)
- Test modules (torch.testing.*, torch.*.test_*)
- Unused features (torch.jit.*, torch.onnx.*, etc.)

### 2. No File Filtering

PyInstaller's `collect_data_files()` includes everything by default:
- Static libraries (.lib, .a)
- Header files (.h, .hpp, .cu, .cuh)
- Source files (.py, .c, .cpp)
- Build files (CMakeLists.txt, *.cmake)
- Test directories

### 3. Transitive Dependencies

Some packages pull in large dependencies:
- PyTorch → llvmlite (102MB) for JIT compilation
- torchvision included even though not imported
- numba included as dependency

## Optimizations Applied

### 1. File Filtering Function

Added `filter_datas()` function to VoiceTransor.spec:lines 12-55:

```python
def filter_datas(datas):
    """
    Remove unnecessary files from datas to reduce package size.

    Filters out:
    - Python source files (.py, .pyx, .pxd)
    - C/C++ source/header files (.c, .cpp, .h, .hpp, .cu, .cuh)
    - Static libraries (.lib, .a) - HUGE space savings (~750MB)
    - Build files (.cmake, CMakeLists.txt)
    - Test/testing directories
    - Development directories (include/, cmake/, etc.)
    """
    filtered = []
    excluded_extensions = {
        # Source files
        '.py', '.pyx', '.pxd', '.c', '.cpp', '.h', '.hpp', '.cu', '.cuh',
        # Build files
        '.cmake',
        # Static libraries (NOT needed at runtime, only .dll/.so/.pyd needed)
        '.lib', '.a'
    }
    excluded_dirs = {'include', 'Include', 'cmake', 'pkgconfig', 'test', 'tests', 'testing', '_testing'}
    excluded_patterns = {'CMakeLists.txt', 'test_', 'testing_'}

    for dest_name, src_path, type_code in datas:
        # Skip if file has excluded extension
        if any(dest_name.lower().endswith(ext) for ext in excluded_extensions):
            continue

        # Skip if file is in excluded directory
        dest_lower = dest_name.lower()
        if any(f'/{excl_dir}/' in dest_name or f'\\{excl_dir}\\' in dest_name for excl_dir in excluded_dirs):
            # But keep runtime libraries even if in these dirs
            if not any(dest_lower.endswith(keep_ext) for keep_ext in {'.dll', '.so', '.pyd', '.dylib'}):
                continue

        # Skip if filename matches excluded patterns
        if any(pattern in dest_name for pattern in excluded_patterns):
            continue

        filtered.append((dest_name, src_path, type_code))

    return filtered

# Apply filter to collected data
a.datas = filter_datas(a.datas)
```

**Key Points:**
- Excludes .lib and .a files → **750MB savings**
- Excludes source files (.py, .h, .c, .cu) → **54MB savings**
- Excludes test directories → **~4MB savings**
- **Preserves runtime libraries** (.dll, .so, .pyd, .dylib)

### 2. Explicit PyTorch Imports

Replaced `collect_submodules()` with explicit essential imports only:

```python
# ❌ BEFORE (caused 500MB bloat):
hiddenimports += collect_submodules('torch')
hiddenimports += collect_submodules('torchaudio')

# ✅ AFTER (explicit imports only):
hiddenimports += [
    # PyTorch core (essential)
    'torch',
    'torch.cuda',
    'torch.nn',
    'torch.nn.functional',
    'torch.nn.modules',
    'torch.nn.modules.activation',
    'torch.nn.modules.conv',
    'torch.nn.modules.linear',
    'torch.optim',
    'torch.autograd',
    'torch.utils',
    'torch.utils.data',
    # CUDA support
    'torch.backends.cudnn',
    'torch.backends.cuda',
    'torch.cuda.amp',
    # TorchAudio (essential for Whisper)
    'torchaudio',
    'torchaudio.transforms',
    'torchaudio.functional',
    'torchaudio.backend',
    'torchaudio.backend.soundfile_backend',
    # Whisper dependencies
    'tiktoken',
    'tiktoken_ext',
    'tiktoken_ext.openai_public',
]
```

### 3. Package Exclusions

Added comprehensive exclusion list in VoiceTransor.spec:lines 124-144:

```python
excludes=[
    # Data science libraries (not used)
    'matplotlib',
    'scipy',
    'pandas',
    'sklearn',
    # Computer vision (not used)
    'torchvision',  # ← 15MB savings
    'PIL',
    'cv2',
    # JIT compilation (not used, saves ~102MB)
    'numba',         # ← 102MB savings
    'llvmlite',
    # Testing frameworks
    'pytest',
    'unittest',
    'test',
    # Documentation
    'sphinx',
    'docutils',
]
```

## Results

### Expected Size Reduction

| Item | Before | After | Savings |
|------|--------|-------|---------|
| Static libraries (.lib) | 750 MB | 0 MB | **750 MB** |
| llvmlite package | 102 MB | 0 MB | **102 MB** |
| torchvision package | 15 MB | 0 MB | **15 MB** |
| Source/header files | 54 MB | 0 MB | **54 MB** |
| **Total** | **921 MB** | **0 MB** | **921 MB** |

### Build Metrics

After optimization, you should see output like:

```
[FILTER] Data files: 45,234 → 42,891 (removed 2,343 unnecessary files)
```

### Final Sizes

- **Application folder**: ~4.2GB (down from ~5.1GB)
- **Distribution ZIP**: ~4.0GB compressed
- **Windows Installer**: ~450MB

## Best Practices

### 1. Always Use Explicit Imports

❌ **Don't do this:**
```python
hiddenimports += collect_submodules('torch')  # Collects everything!
```

✅ **Do this instead:**
```python
hiddenimports += [
    'torch',
    'torch.cuda',
    'torch.nn',
    # ... only what you actually need
]
```

### 2. Filter Data Files

Always filter collected data to remove development files:

```python
datas += collect_data_files('torch', include_py_files=False)
datas = filter_datas(datas)  # Remove .lib, .h, test dirs, etc.
```

### 3. Exclude Unused Packages

Explicitly exclude packages you don't use:

```python
excludes=[
    'matplotlib',  # Not used
    'scipy',       # Not used
    'torchvision', # Not used
    'numba',       # Not used
]
```

### 4. Test Build Size Regularly

```bash
# Clean build to test optimizations
scripts\clean_build.bat
scripts\build_all.bat

# Check size
dir /s dist\VoiceTransor\_internal
```

### 5. Monitor PyInstaller Warnings

Look for warnings during build:

```
WARNING: Hidden import "torch.testing" not found!
```

These often indicate unnecessary imports that can be removed.

## Verification Steps

### After Each Optimization

1. **Clean rebuild:**
   ```bash
   scripts\clean_build.bat
   scripts\build_all.bat
   ```

2. **Check build log:**
   ```
   [FILTER] Data files: X → Y (removed Z unnecessary files)
   ```

3. **Verify size:**
   ```bash
   # Check total size
   dir /s dist\VoiceTransor

   # Should be ~4.2GB, not ~5.1GB
   ```

4. **Test application:**
   ```bash
   dist\VoiceTransor\VoiceTransor.exe
   ```

   - ✅ Launches successfully
   - ✅ Imports audio file
   - ✅ Runs transcription
   - ✅ CUDA detected (if GPU available)
   - ✅ Ollama integration works

5. **Check for missing DLLs:**
   - If application crashes on launch
   - Check if filter removed essential .dll files
   - Review filter logic

## Troubleshooting

### Build Size Still Too Large

1. Check if filter is applied:
   ```python
   # In VoiceTransor.spec
   a.datas = filter_datas(a.datas)  # Make sure this line exists
   ```

2. List large files:
   ```bash
   # Windows PowerShell
   Get-ChildItem -Path dist\VoiceTransor\_internal -Recurse |
     Sort-Object Length -Descending |
     Select-Object -First 50 FullName,Length
   ```

3. Check for .lib files:
   ```bash
   # Should return nothing
   dir /s /b dist\VoiceTransor\_internal\*.lib
   ```

### Application Won't Start After Optimization

1. **Missing imports**: Add to hiddenimports
2. **Missing data files**: Reduce filter aggressiveness
3. **Missing DLLs**: Check filter preserves .dll files

### Build Log Shows Few Filtered Files

If you see:
```
[FILTER] Data files: 43,000 → 42,950 (removed 50 unnecessary files)
```

Problem: Filter not working correctly. Check:
1. Filter function is defined correctly
2. `a.datas = filter_datas(a.datas)` is called
3. Case sensitivity in file extensions

## Related Files

- `VoiceTransor.spec` - PyInstaller configuration with optimizations
- `scripts\clean_build.bat` - Clean build artifacts
- `scripts\build_all.bat` - Complete build pipeline
- `docs\dev\DISTRIBUTION_GUIDE.md` - Distribution process

## Support

For questions about build optimization:
- Email: voicetransor@gmail.com
- Check PyInstaller docs: https://pyinstaller.org/

---

Last updated: 2025-11-03
