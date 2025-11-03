# 安装指南

本指南将帮助您在系统上安装和设置 VoiceTransor。

[English Installation Guide](./INSTALLATION.md)

## 目录

1. [下载](#下载)
2. [系统要求](#系统要求)
3. [安装 VoiceTransor](#安装-voicetransor)
4. [安装 FFmpeg（必需）](#安装-ffmpeg必需)
5. [安装 Ollama（可选）](#安装-ollama可选)
6. [验证安装](#验证安装)
7. [故障排除](#故障排除)

## 下载

下载适合您平台的最新版本：

**Windows：**
- `VoiceTransor-v0.9.0-Windows-x64.zip`（约 4GB）- **通用版本，适用所有系统**
- **或者** `VoiceTransor-v0.9.0-Windows-x64-Setup.exe`（约 450MB）- 安装器版本

### 💡 重要：单一通用版本

VoiceTransor 使用**单一版本适用所有用户**：
- ✅ **有 NVIDIA 显卡？** 自动使用 CUDA 加速
- ✅ **没有显卡？** 自动使用 CPU（完全正常工作，只是慢一些）
- ✅ **无需选择** CPU/GPU 版本
- ✅ **同一个安装包** 适用所有 Windows 10+ 系统

这类似于 Ollama 的工作方式 - 一次下载，自动检测硬件。

## 系统要求

### 最低要求

- **操作系统：**
  - Windows 10 或更高版本（64 位）
  - macOS 10.15 (Catalina) 或更高版本
  - Linux（Ubuntu 20.04+、Debian 11+ 或同等版本）

- **硬件：**
  - 8GB 内存
  - 5GB 可用磁盘空间（用于应用程序和模型）
  - 双核处理器

### 推荐配置

- **硬件：**
  - 16GB 内存
  - 10GB 可用磁盘空间
  - 四核或更好的处理器

### GPU 加速（可选）

- **NVIDIA 显卡：**
  - GTX 900 系列或更新（GTX 1050、RTX 20/30/40 系列等）
  - 4GB+ 显存
  - 驱动版本 >= 525.60.13

- **Apple Silicon：**
  - M1、M2 或 M3 芯片
  - 自动检测和使用

**注意：** GPU 加速是可选的。应用程序在 CPU 上也能完美运行，只是速度较慢。

## 安装 VoiceTransor

### Windows

1. **解压文件：**
   - 右键点击 `VoiceTransor-Windows.zip`
   - 选择"全部提取..."
   - 选择目标文件夹（例如 `C:\Program Files\VoiceTransor`）

2. **启动应用程序：**
   - 进入解压后的文件夹
   - 双击 `VoiceTransor.exe`

3. **Windows 安全警告：**
   - 如果看到"Windows 已保护你的电脑"，点击"更多信息"
   - 然后点击"仍要运行"
   - 这对于未签名的应用程序是正常的

### macOS

1. **解压文件：**
   - 双击 `VoiceTransor-macOS.zip`
   - 将 `VoiceTransor.app` 移动到应用程序文件夹

2. **首次启动：**
   - 右键点击 `VoiceTransor.app` 并选择"打开"
   - 在安全对话框中点击"打开"

3. **授予权限：**
   - 在提示时允许访问文件

### Linux

1. **解压文件：**
   ```bash
   unzip VoiceTransor-Linux.zip -d ~/Applications/VoiceTransor
   cd ~/Applications/VoiceTransor
   ```

2. **设置可执行权限：**
   ```bash
   chmod +x VoiceTransor
   ```

3. **启动：**
   ```bash
   ./VoiceTransor
   ```

## 安装 FFmpeg（必需）

VoiceTransor 需要 FFmpeg 来处理音频文件。您必须单独安装它。

### Windows

**方法 1：自动安装（推荐）**

1. 从此处下载 FFmpeg：https://www.gyan.dev/ffmpeg/builds/
2. 下载 **"ffmpeg-release-essentials.zip"**
3. 解压到 `C:\ffmpeg`
4. 添加到 PATH：
   - 按 `Win + R`，输入 `sysdm.cpl`，按回车
   - 转到"高级"选项卡
   - 点击"环境变量"
   - 在"系统变量"下，找到"Path"并点击"编辑"
   - 点击"新建"
   - 添加：`C:\ffmpeg\bin`
   - 在所有窗口上点击"确定"
5. **重启计算机**（或至少注销并重新登录）

**方法 2：使用包管理器**

如果您安装了 Chocolatey：
```bash
choco install ffmpeg
```

如果您安装了 Scoop：
```bash
scoop install ffmpeg
```

**验证安装：**
```bash
ffmpeg -version
```

### macOS

**使用 Homebrew（推荐）：**
```bash
brew install ffmpeg
```

**验证安装：**
```bash
ffmpeg -version
```

### Linux

**Ubuntu/Debian：**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Fedora：**
```bash
sudo dnf install ffmpeg
```

**Arch Linux：**
```bash
sudo pacman -S ffmpeg
```

**验证安装：**
```bash
ffmpeg -version
```

## 安装 Ollama（可选）

Ollama 支持 AI 文本处理（摘要、翻译、提取要点等）。这是可选的，但建议安装。

### 什么是 Ollama？

- 本地 AI 模型（无云端，您的数据保持私密）
- 同时支持 CPU 和 GPU
- VoiceTransor 的文本处理功能需要它

### 安装

**Windows：**

1. 从此处下载安装程序：https://ollama.com/download
2. 运行安装程序
3. 打开命令提示符并验证：
   ```bash
   ollama --version
   ```

**macOS：**

1. 从此处下载：https://ollama.com/download
2. 安装 .dmg 文件
3. 在终端中验证：
   ```bash
   ollama --version
   ```

**Linux：**

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### 下载模型

安装 Ollama 后：

1. **启动 Ollama 服务**（如果未自动启动）：
   ```bash
   ollama serve
   ```

2. **拉取模型**（在新终端中）：
   ```bash
   # 英文模型
   ollama pull llama3.1:8b

   # 中英文模型
   ollama pull qwen2.5:7b
   ```

3. **模型大小：**
   - `llama3.1:8b` - 约 4.7GB
   - `qwen2.5:7b` - 约 4.4GB

**注意：** 模型下载到：
- Windows：`%USERPROFILE%\.ollama\models`
- macOS/Linux：`~/.ollama/models`

## 验证安装

### 测试 VoiceTransor

1. 启动 VoiceTransor
2. 尝试导入一个小音频文件
3. 如果 FFmpeg 正常工作，您应该能看到音频信息

### 测试 GPU 检测（如果您有 NVIDIA 显卡）

1. 进入转录设置
2. 选择设备："auto" 或 "cuda"
3. 开始转录
4. 检查日志 - 应该提到使用 CUDA

如果未检测到 GPU，应用程序将自动使用 CPU。

### 测试 Ollama（如果已安装）

1. 在 VoiceTransor 中，尝试"运行文本操作"
2. 选择一个预设（例如"摘要"）
3. 如果 Ollama 正在运行并有模型，它应该可以工作

## 故障排除

### "ffprobe not found" 错误

**原因：** FFmpeg 未安装或不在 PATH 中。

**解决方案：**
1. 验证 FFmpeg 已安装：`ffmpeg -version`
2. 如果未找到，重新安装 FFmpeg
3. 确保 FFmpeg 在您的 PATH 中
4. 重启 VoiceTransor（或您的计算机）

### "Ollama is not running" 错误

**原因：** Ollama 服务未启动。

**解决方案：**
1. 打开终端
2. 运行：`ollama serve`
3. 保持此终端打开
4. 在 VoiceTransor 中重试

**自动启动 Ollama（可选）：**
- Windows：创建计划任务
- macOS：添加到登录项
- Linux：启用 systemd 服务

### 应用程序无法启动

**Windows：**
- 尝试以管理员身份运行
- 检查 Windows Defender 是否阻止了它

**macOS：**
- 转到系统偏好设置 → 安全性与隐私
- 点击"仍要打开"

**Linux：**
- 检查文件权限：`chmod +x VoiceTransor`
- 安装所需库：`sudo apt install libxcb-cursor0`

### GPU 未检测到

**检查您的 GPU：**
```bash
# NVIDIA
nvidia-smi
```

**更新驱动程序：**
- NVIDIA：从 https://www.nvidia.com/drivers 下载
- 最低版本：525.60.13（用于 CUDA 12.1）

**如果 GPU 不工作也不用担心：**
- 应用程序将自动使用 CPU
- 一切仍然可以工作，只是速度较慢

## 下一步

安装完成后：

1. 阅读[用户指南](./USER_GUIDE.md)了解详细使用说明
2. 尝试您的第一次转录
3. 使用 Ollama 探索 AI 文本处理

## 获取帮助

如果遇到此处未涵盖的问题：

1. 查看 [USER_GUIDE.md - 故障排除](./USER_GUIDE.md#troubleshooting)
2. 电子邮件：voicetransor@gmail.com

---

祝您转录愉快！🎉
