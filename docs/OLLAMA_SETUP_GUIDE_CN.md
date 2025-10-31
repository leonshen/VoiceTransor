# Ollama 安装和使用指南

VoiceTransor 使用 Ollama 提供本地 AI 文本处理功能，无需将您的数据上传到云端，完全保护隐私。

---

## 📋 系统要求

### 推荐配置（GPU模式）
- **GPU：** NVIDIA 显卡，8GB+ 显存
- **内存：** 16GB+ RAM
- **磁盘：** 每个模型约 4-8GB 空间
- **操作系统：** Windows 10/11, macOS, Linux

### 最低配置（CPU模式）
- **CPU：** 现代多核处理器
- **内存：** 16GB+ RAM（推荐 32GB）
- **磁盘：** 每个模型约 4-8GB 空间
- **注意：** CPU模式运行速度会较慢（约3-10倍慢于GPU）

### 模型大小参考
| 模型 | 大小 | 显存需求 | 推荐用途 |
|------|------|---------|---------|
| llama3.1:8b | ~4.7GB | 6-8GB | 英文文本处理（默认） |
| qwen2.5:7b | ~4.4GB | 6-8GB | 中英文平衡 |
| gemma2:9b | ~5.4GB | 8-10GB | 高质量文本处理 |
| llama3.1:70b | ~40GB | 48GB+ | 顶级质量（需要高端硬件） |

---

## 🚀 快速安装（Windows）

### 方法1：使用自动安装脚本（推荐）

1. 双击运行项目根目录下的 `install_ollama.bat`
2. 脚本会自动：
   - 下载 Ollama 安装程序
   - 安装 Ollama
   - 启动 Ollama 服务
   - 可选下载默认模型（llama3.1:8b）
3. 等待安装完成

### 方法2：手动安装

1. **下载 Ollama**
   - 访问：https://ollama.com/download
   - 下载 Windows 版本（约 300MB）

2. **安装 Ollama**
   - 运行下载的安装程序
   - 按照提示完成安装
   - Ollama 会自动添加到系统路径

3. **启动 Ollama 服务**
   - 打开命令提示符（CMD）或 PowerShell
   - 运行：`ollama serve`
   - 保持这个窗口打开（或让其在后台运行）

4. **下载模型**
   - 打开另一个命令提示符
   - 运行：`ollama pull llama3.1:8b`
   - 等待下载完成（约4.7GB，需要几分钟）

---

## 🍎 macOS 安装

### 使用 Homebrew（推荐）
```bash
brew install ollama
```

### 手动安装
1. 访问 https://ollama.com/download
2. 下载 macOS 版本
3. 安装并运行

### 下载模型
```bash
ollama pull llama3.1:8b
```

---

## 🐧 Linux 安装

### 一键安装脚本
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### 启动服务
```bash
ollama serve &
```

### 下载模型
```bash
ollama pull llama3.1:8b
```

---

## ✅ 验证安装

### 检查 Ollama 是否安装成功
```bash
ollama --version
```

### 检查服务是否运行
```bash
# Windows
tasklist | findstr ollama

# macOS/Linux
ps aux | grep ollama
```

### 列出已安装的模型
```bash
ollama list
```

### 测试模型
```bash
ollama run llama3.1:8b "Hello, how are you?"
```

---

## 🎯 在 VoiceTransor 中使用

### 1. 确保 Ollama 服务运行中
VoiceTransor 会自动检测 Ollama 是否运行。如果未运行：
- Windows：运行 `ollama serve`
- macOS/Linux：运行 `ollama serve &`

### 2. 选择模型
在"Run Text Operations"对话框中：
- 从下拉菜单选择模型，或
- 手动输入自定义模型名称

### 3. 输入处理指令
输入您想要AI执行的操作，例如：
- "总结这段文字的要点"
- "将内容翻译成英文"
- "提取关键信息并列成清单"
- "纠正语法错误"

### 4. 等待处理
- GPU模式：通常几秒到几十秒
- CPU模式：可能需要1-5分钟

---

## 🛠️ 常用命令

### 模型管理
```bash
# 下载模型
ollama pull llama3.1:8b
ollama pull qwen2.5:7b
ollama pull gemma2:9b

# 列出已安装模型
ollama list

# 删除模型（释放空间）
ollama rm llama3.1:8b

# 查看模型信息
ollama show llama3.1:8b
```

### 服务管理
```bash
# 启动服务
ollama serve

# 停止服务（Windows）
taskkill /IM ollama.exe /F

# 停止服务（macOS/Linux）
killall ollama
```

---

## 💡 推荐模型选择

### 🚀 快速推荐
| 使用场景 | 推荐模型 | 理由 |
|---------|---------|------|
| 英文为主 | llama3.1:8b | 速度快，质量好，默认选择 |
| 中英混合 | qwen2.5:7b | 中文支持优秀 |
| 高质量 | gemma2:9b | Google出品，质量高 |
| 硬件受限 | llama3.1:8b | 资源需求最低 |

### 🎨 详细对比

#### llama3.1:8b（默认）
- ✅ 英文处理优秀
- ✅ 速度快
- ✅ 资源占用适中（6-8GB显存）
- ⚠️ 中文支持一般
- **适合：** 英文文本处理，日常使用

#### qwen2.5:7b
- ✅ 中英文平衡
- ✅ 中文理解能力强
- ✅ 文化适配好
- **适合：** 中文或中英混合文本

#### gemma2:9b
- ✅ 质量高
- ✅ Google官方支持
- ⚠️ 显存需求稍高（8-10GB）
- **适合：** 追求高质量输出

---

## 🐛 常见问题

### Q1: Ollama 服务无法启动
**A:**
- 检查是否已有Ollama进程在运行
- 尝试重启电脑
- 检查防火墙设置
- 确保端口 11434 未被占用

### Q2: 模型下载失败或很慢
**A:**
- 检查网络连接
- 尝试使用VPN或代理
- 等待一段时间后重试
- 确保有足够的磁盘空间

### Q3: VoiceTransor 提示"Ollama不可用"
**A:**
1. 确认Ollama服务正在运行
2. 在浏览器访问 http://localhost:11434 检查
3. 运行 `ollama list` 确认有已下载的模型
4. 重启VoiceTransor

### Q4: 处理速度很慢
**A:**
- **检查GPU：** 确保CUDA正常工作
- **尝试小模型：** 换用 llama3.1:8b
- **关闭其他程序：** 释放GPU/内存
- **CPU模式很慢是正常的**

### Q5: 显存不足 (Out of Memory)
**A:**
- 换用更小的模型
- 关闭其他GPU程序
- 使用CPU模式（设置环境变量）
- 升级显卡

### Q6: 如何使用CPU而非GPU？
**A:**
设置环境变量：
```bash
# Windows CMD
set OLLAMA_HOST=0.0.0.0:11434
set OLLAMA_SKIP_CPU_CHECK=1

# 重启 ollama serve
```

---

## 📚 更多资源

### 官方文档
- Ollama 官网：https://ollama.com
- 模型库：https://ollama.com/library
- GitHub：https://github.com/ollama/ollama

### 社区资源
- Discord：https://discord.gg/ollama
- Reddit：r/ollama
- 中文社区：各大AI论坛

---

## 🔧 高级配置

### 修改 Ollama 监听地址
```bash
# 允许远程访问（谨慎使用）
set OLLAMA_HOST=0.0.0.0:11434
ollama serve
```

### 指定GPU设备
```bash
# CUDA设备选择
set CUDA_VISIBLE_DEVICES=0
ollama serve
```

### 调整模型参数
在代码中可以修改：
- `temperature`: 控制随机性（0.0-1.0）
- `top_p`: 核采样参数
- `max_tokens`: 最大输出长度

---

## 📞 获取帮助

如果遇到问题：
1. 查看本文档的"常见问题"部分
2. 检查 Ollama 官方文档
3. 在 VoiceTransor GitHub Issues 提问
4. 访问 Ollama 社区寻求帮助

---

**祝您使用愉快！🎉**
