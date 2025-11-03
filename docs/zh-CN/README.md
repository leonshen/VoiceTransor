# VoiceTransor

**基于 AI 的语音转文字工具，完全本地处理**

VoiceTransor 是一款桌面应用程序，使用 OpenAI 的 Whisper 模型将音频转换为文字，并可选择使用 Ollama 进行 AI 文本处理。所有处理都在本地完成 - 您的数据不会离开您的电脑。

[English README](./README.md)

## 功能特性

- **准确的语音识别** - 基于 OpenAI Whisper
- **GPU 加速** - 自动检测 CUDA/MPS 以加快处理速度
- **AI 文本处理** - 使用 Ollama 进行摘要、翻译或其他文本处理
- **多种导出格式** - 保存为 TXT 或 PDF
- **隐私优先** - 所有处理都在本地进行
- **跨平台** - 支持 Windows、macOS 和 Linux
- **多语言支持** - 支持 100 种语言

## 快速开始

### 1. 系统要求

**最低配置：**
- Windows 10 / macOS 10.15 / Linux
- 8GB 内存
- 5GB 可用磁盘空间

**推荐配置（GPU 加速）：**
- NVIDIA 显卡（GTX 900 系列或更新）
- 驱动版本 >= 525.60（支持 CUDA）

**注意：** GPU 是可选的 - 应用程序会自动检测您的硬件，如果没有 GPU 会自动降级使用 CPU。

### 2. 安装

**Windows：**
1. 解压 `VoiceTransor-Windows.zip`
2. 运行 `VoiceTransor.exe`

**重要：** 您还需要安装 FFmpeg（见下文）。

### 3. 安装 FFmpeg（必需）

VoiceTransor 需要 FFmpeg 来处理音频文件。

**Windows：**
- 下载：https://www.gyan.dev/ffmpeg/builds/
- 选择 "ffmpeg-release-essentials.zip"
- 解压并添加到 PATH（[如何操作？](https://www.architectryan.com/2018/03/17/add-to-the-path-on-windows-10/)）

**macOS：**
```bash
brew install ffmpeg
```

**Linux：**
```bash
sudo apt install ffmpeg  # Ubuntu/Debian
```

### 4. 首次使用

1. 启动 VoiceTransor
2. 点击"导入音频"（支持 WAV、MP3、M4A、FLAC 等）
3. 点击"转录为文本"
4. 选择设置：
   - **模型**：`base`（推荐大多数用户）
   - **设备**：`auto`（有 GPU 自动使用）
   - **语言**：自动检测或选择特定语言
5. 等待转录完成（首次使用会下载模型 ~140MB）
6. 导出为 TXT 或使用 AI 处理

## 可选：安装 Ollama

Ollama 支持 AI 文本处理（摘要、翻译等）- 完全离线运行。

**安装步骤：**
1. 下载：https://ollama.com/download
2. 安装并运行 `ollama serve`
3. 拉取模型：
   ```bash
   ollama pull llama3.1:8b  # 英文
   ollama pull qwen2.5:7b   # 中英文
   ```

**注意：** Ollama 同时支持 CPU 和 GPU - 无需特殊设置。

## 性能表现

**转录速度（1 小时音频）：**

| 硬件配置 | 时间 |
|----------|------|
| CPU（8核） | ~30-60 分钟 |
| NVIDIA RTX 3060 | ~2-5 分钟 |
| Apple M1 Pro | ~3-6 分钟 |

**GPU 兼容性：**
- ✅ **单一通用版本** - 同时支持 GPU 和 CPU 系统
- ✅ 自动检测 - 无需手动配置
- ✅ NVIDIA 显卡（GTX 900+、RTX 系列）- 使用 CUDA 加速
- ✅ Apple Silicon（M1/M2/M3）- 使用 Metal Performance Shaders
- ✅ 无 GPU 时自动降级使用 CPU
- ℹ️ **无需选择 CPU/GPU 版本** - 一个安装包适用所有用户

## 文档

- [用户指南](./USER_GUIDE.md) - 详细使用说明
- [安装指南](./INSTALLATION.md) - 分步安装说明
- [构建说明](./BUILD_INSTRUCTIONS.md) - 面向开发者

## 常见问题

**"ffprobe not found"**
- 安装 FFmpeg 并确保已添加到 PATH

**转录速度很慢**
- 使用更小的模型（`tiny` 或 `base`）
- 检查设备设置为 `auto` 或 `cuda`
- 确保 GPU 驱动程序是最新的

**"Ollama is not running"**
- 打开终端并运行 `ollama serve`

更多帮助请参见 [USER_GUIDE.md](./USER_GUIDE.md#troubleshooting)

## 许可证

MIT License - 详见 [LICENSE](../../LICENSE) 文件

## 支持

- GitHub Issues：https://github.com/leonshen/VoiceTransor/issues
- 邮箱：voicetransor@gmail.com

---

使用 ❤️ 制作，基于 [OpenAI Whisper](https://github.com/openai/whisper) 和 [Ollama](https://ollama.com)
