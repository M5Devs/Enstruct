# 🎙️ Enstruct

<p align="center">
  <img src="https://raw.githubusercontent.com/m5devs/enstruct/main/assets/logo.png" alt="Enstruct Logo" width="150" style="border-radius: 50%"/>
</p>

<p align="center">
  <strong>Transcribe. Structure. Free.</strong>
</p>

<p align="center">
  <a href="https://github.com/m5devs/enstruct/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/enstruct/enstruct?style=flat-square" alt="MIT License" />
  </a>
  <a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/python-3.8+-blue.svg?style=flat-square" alt="Python 3.8+" />
  </a>
  <a href="https://github.com/m5devs/enstruct">
    <img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square" alt="PRs Welcome" />
  </a>
  <a href="https://colab.research.google.com/github/m5devs/enstruct/blob/main/notebooks/Enstruct_Colab.ipynb">
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
* 🎙️ **Flexible Interfaces**: Supports a robust **Command Line Interface (CLI)** and a sleek, interactive **Gradio Web UI**.
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
| **Open Source** | 🔓 Yes (MIT License) | No | No | No |

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

Enstruct is designed to work seamlessly both as a command-line tool and as a Python library.

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

---

## 🌐 Gradio Web Interface

Enstruct comes with an interactive, beautiful browser-based Web UI.

To start the Web UI locally:
```bash
python -m interfaces.web.app
```
Then, open `http://localhost:7860` in your browser to record speech, upload files, customize model sizes, and download SRT/VTT/TXT transcripts instantly.

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

Distributed under the **MIT License**. See `LICENSE` for more information.
