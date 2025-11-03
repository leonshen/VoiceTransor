# Changelog

All notable changes to VoiceTransor will be documented in this file.

## [0.9.0] - 2025-11-02

### Added
- Complete distribution packaging system
- Automated build scripts (`scripts/build/build_app.bat`, `package_distribution.bat`)
- Inno Setup installer script (`installer/installer.iss`)
- **Single universal build strategy** - one installer works for all users
  - Includes CUDA 12.1 support
  - Automatic GPU detection and fallback to CPU
  - No separate CPU/GPU versions needed
- Comprehensive documentation (English and Chinese)
  - README.md / README_zh_CN.md
  - INSTALLATION.md / INSTALLATION_zh_CN.md
  - USER_GUIDE.md
  - DISTRIBUTION_GUIDE.md
- ffprobe path caching for better performance

### Changed
- Version updated from 0.3.0 to 0.9.0 (Beta release)
- Language support count corrected to 100 languages (from 90+)

### Fixed
- **Critical performance fix**: Audio file loading time reduced from 5+ seconds to <100ms
  - Issue: subprocess.run() was extremely slow in PyInstaller frozen environment
  - Solution: Use shell=True in frozen environment to bypass Windows security overhead
  - Performance improvement: 98.4% faster (60x speedup)
- Improved ffprobe executable path resolution with caching

### Technical Details
- Implemented intelligent subprocess execution strategy:
  - Development environment: Direct process execution
  - Frozen environment: Shell-based execution with proper escaping
- Added comprehensive performance profiling during development
- Optimized for Windows security scanning behavior

### Documentation
- Added PERFORMANCE_FIX_REPORT.md with technical analysis
- Added DISTRIBUTION_REPORT.md for release workflow
- Updated BUILD_INSTRUCTIONS.md
- Created bilingual user documentation

## [0.3.0] - Previous Release

### Features
- Speech-to-text with Whisper
- Ollama integration for text processing
- GPU/CPU auto-detection
- Export to TXT/PDF
- Multi-language support
- Dynamic language switching

---

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
