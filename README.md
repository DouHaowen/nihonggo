# 🌸 日语学习助手 | Japanese Learning Assistant

一个基于 **Streamlit + LLM** 的多语言日语学习平台，支持音视频转写、智能断句、自动翻译、假名标注、单句分析等功能，助力日语学习者高效提升听读能力。

👉 **在线体验地址**：[https://nihonggo-saita.streamlit.app/](https://nihonggo-saita.streamlit.app/)

## ✨ 项目特色

- **多语言界面**：支持中文、英文、韩文三种界面，适合不同母语的用户。  
- **音视频转写**：支持上传 MP4、MOV、MP3、WAV 等格式的音视频文件，自动调用 Whisper 进行日语语音转写。  
- **智能断句**：结合大模型（GPT）对转写结果进行智能分句，保证每句自然流畅，避免语义断裂。  
- **自动翻译**：每句日语自动翻译为中文、英文或韩文，翻译流畅、准确。  
- **假名标注**：日语原文自动添加假名（Furigana），便于初学者阅读。  
- **单句朗读与分析**：支持单句循环播放、点击分析，输出词汇表、语法点、例句等详细内容。  
- **美观易用的界面**：现代化 UI，支持高亮当前句、全文对照、交互式操作。

## 🚀 快速开始

### 克隆项目

```bash
git clone https://github.com/DouHaowen/nihonggo.git
cd nihonggo
```

### 安装依赖（建议使用虚拟环境）

```bash
pip install -r requirements.txt
```

### 配置 OpenAI API Key

在项目根目录下新建 `.env` 文件，内容如下：

```ini
OPENAI_API_KEY=你的API密钥
```

### 启动应用

```bash
streamlit run app.py
```

## 🖥️ 功能演示

- 上传日语音频或视频文件，自动生成带假名和翻译的字幕
- 支持单句循环播放，便于跟读和听力训练
- 点击任意句子，自动分析词汇、语法点、例句等，输出表格和详细解释
- 多语言界面一键切换，适合不同用户群体

## 📦 技术栈

- 前端/界面：`Streamlit`
- 语音转写：`OpenAI Whisper`
- 智能分析与翻译：`OpenAI GPT-4o`
- 音视频处理：`moviepy`
- 多语言支持：内置语言映射配置

## 📂 项目结构

```bash
├── app.py                     # 主程序入口
├── .env                       # OpenAI 密钥文件（需手动创建）
├── requirements.txt           # 依赖列表
```

## 🙏 致谢

- 感谢 [OpenAI](https://openai.com/) 提供的强大 API 支持  
- 感谢 [Streamlit](https://streamlit.io/) 社区的优秀生态  
- 感谢所有日语学习者的反馈与建议，让我们一起打造更好用的学习工具！

💡 欢迎 Star / Fork 本项目，也欢迎提交 Issue 与 PR，共建开源日语学习工具！
