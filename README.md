# 🎙️ Enstruct

<p align="center">
  <img src="https://raw.githubusercontent.com/M5Devs/Enstruct/main/assets/logo.png" alt="Enstruct Logo" width="150" style="border-radius: 50%"/>
</p>

<p align="center">
  <strong>Transcribe. Structure. Free.</strong>
</p>

<p align="center">
  <a href="https://github.com/M5Devs/Enstruct/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/M5Devs/Enstruct?style=flat-square" alt="AGPL v3 License" />
  </a>
  <a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/python-3.8+-blue.svg?style=flat-square" alt="Python 3.8+" />
  </a>
  <a href="https://github.com/M5Devs/Enstruct">
    <img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square" alt="PRs Welcome" />
  </a>
  <a href="https://colab.research.google.com/github/M5Devs/Enstruct/blob/main/notebooks/Enstruct_Colab.ipynb">
    <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab" />
  </a>
</p>

---

## 🚀 Overview

**Enstruct** is a professional, production-ready, open-source audio toolkit that wraps OpenAI's Whisper model (powered by the high-performance `faster-whisper` engine). Designed to run fully locally or on free cloud instances, Enstruct offers a free, private alternative to expensive paid services like Otter.ai, Transkriptor, and AssemblyAI.

### Key Features
* ⚡ **Ultra-Fast Transcription**: Powered by `faster-whisper` utilizing CTranslate2 for up to 4x speedups over standard Whisper.
* 🌐 **Any-to-English Translation**: Translate speech from dozens of languages directly to fluent English transcripts.
* 📝 **Multi-Format Export**: Generates professional `SRT` and `VTT` subtitle files, alongside raw `TXT` transcripts.
* 📂 **Batch Folder Processing**: Automatically transcribes entire folders of audio/video files with beautiful progress indicators.
* 🎬 **YouTube Integration**: Transcribe and translate YouTube video content directly via url input.
* ☁️ **Google Drive Storage**: Seamless automatic drive mounting and file saving inside Google Colab.
* 🎙️ **Flexible Interfaces**: Supports a robust **Command Line Interface (CLI)** and a sleek, interactive **Gradio Web UI** with activity history.
* 🧠 **Auto-Hardware Detection**: Dynamically utilizes CUDA if an NVIDIA GPU is available, falling back safely to highly-optimized CPU execution.

---

## 📊 Comparison: Enstruct vs Paid Services

| Feature | Enstruct (Ours) | Otter.ai | Transkriptor | AssemblyAI |
| :--- | :---: | :---: | :---: | :---: |
| **Cost** | 🆓 **100% Free** | Paid Subscription | Paid / Minute | Paid / Minute |
| **Hosting** | 💻 Fully Local / Self-Hosted | Cloud-only | Cloud-only | API-only |
| **Privacy** | 🔒 Zero data shared, fully private | Processed on third-party | Processed on third-party | Processed on third-party |
| **Batch Support** | ✅ Built-in CLI & API | Limited | Limited | Paid API-only |
| **Translation** | ✅ Any-to-English | Limited | Paid | Paid |
| **Open Source** | 🔓 Yes (AGPL v3 License) | No | No | No |

---

## 🛠️ Installation

```bash
pip install enstruct
```

> **Note**: Enstruct requires `ffmpeg` to process audio/video container formats.
> - **Ubuntu/Debian**: `sudo apt install ffmpeg`
> - **macOS**: `brew install ffmpeg`
> - **Windows**: `choco install ffmpeg`

---

## 💻 Usage

ENstruct is designed to work seamlessly both as a command-line tool and as a Python library.

### 1. Command Line Interface (CLI)

```bash
# Transcribe an audio file into default SRT format
enstruct transcribe voice_note.mp3

# Transcribe with target language and VTT format
enstruct transcribe audio.wav --language es --format vtt --output subtitle.vtt

# Translate a Spanish audio file directly to English
enstruct translate foreign_audio.mp4 --format txt --output english_transcript.txt

# Batch process an entire directory of mixed audio/video files
enstruct batch /path/to/audios --output /path/to/subtitles --format srt

# Detect spoken language of an audio file
enstruct detect-language conversation.wav
```

### 2. Python API

#### Standard Transcription
```python
from enstruct.core.transcriber import EnstructTranscriber

# Initialize the transcriber (automatically uses GPU if available)
transcriber = EnstructTranscriber(model_size="large-v3", device="auto")

# Transcribe audio file
result = transcriber.transcribe("interview.m4a")

print(f"Detected Language: {result['language']}")
print(f"Transcript: {result['text']}")

# Generate subtitle formats using SubtitleGenerator
from enstruct.tools.subtitle import SubtitleGenerator

generator = SubtitleGenerator()
generator.generate(result["segments"], "interview.srt", format="srt")
```

#### YouTube Downloader
```python
from enstruct.tools.youtube import YouTubeDownloader

downloader = YouTubeDownloader()
# Download best-quality audio from YouTube URL and save as MP3
audio_file = downloader.download_audio("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
print(f"Downloaded audio to: {audio_file}")
```

#### Google Drive Manager (Google Colab only)
```python
from enstruct.integrations.drive import DriveManager

drive_manager = DriveManager()
# Mount Google Drive
drive_manager.mount_drive()
# Save transcript directly to Drive: /content/drive/MyDrive/Enstruct/outputs
drive_manager.save_file("transcript.srt", "Subtitles content...")
```

---

## 🌐 Gradio Web Interface

Enstruct comes with an interactive, beautiful browser-based Web UI featuring dynamic source input switching and session logs history.

To start the Web UI locally:
```bash
python -m interfaces.web.app
```
Then, open `http://localhost:7860` in your browser. You can:
1. **Choose Audio Source**: Select between "Upload / Microphone", "Google Drive" (Colab path), or "YouTube URL".
2. **Configure options**: Choose model sizes (tiny to large-v3), output formats (SRT, VTT, TXT), and task (Transcribe or Translate).
3. **Activity Logs & History**: Track session logs inside the "History" tab, refresh listings, or clear all history logs.
4. **Execute & Download**: Run transcription, preview results, and download output files immediately.

---

## 💼 Commercial Use

Enstruct is free under **AGPL v3** for open-source and personal use.

If you want to use Enstruct in a **closed-source or commercial product**, a commercial license is required.
See [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md) for pricing and details.

---

## 🤝 Contributing

We welcome contributions from the open-source community! 
1. Fork the Repository.
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`).
3. Set up development environment and run tests:
   ```bash
   pip install pytest
   pytest
   ```
4. Commit your Changes (`git commit -m 'Add some AmazingFeature'`).
5. Push to the Branch (`git push origin feature/AmazingFeature`).
6. Open a Pull Request.

---

## 📄 License

Distributed under the **AGPL v3 License**. See `LICENSE` for more information.
Commercial licensing and bespoke features are also available.
