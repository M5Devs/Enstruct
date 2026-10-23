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

**Enstruct** is a professional, production-ready, open-source audio toolkit that wraps OpenAI's Whisper model (powered by the high-performance `faster-whisper` engine). Designed to run fully locally, via Docker with GPU acceleration, or on cloud instances, Enstruct offers a free, private alternative to expensive paid services like Otter.ai, Transkriptor, and AssemblyAI.

### Key Features
* ⚡ **Ultra-Fast Transcription**: Powered by `faster-whisper` utilizing CTranslate2 for up to 4x speedups over standard Whisper.
* 🚀 **`large-v3-turbo` Support**: Modern default model size providing high accuracy with significantly lower latency.
* 🌐 **Any-to-English Translation**: Translate speech from dozens of languages directly to fluent English transcripts.
* 📝 **Multi-Format Export**: Generates professional `SRT` and `VTT` subtitle files, alongside raw `TXT` transcripts.
* 📂 **Batch & Watch Folder Auto-Processing**: Transcribe whole folders or continuously monitor inbox directories for automated output.
* 🔌 **OpenAI-Compatible REST API**: Drop-in API replacement (`/v1/audio/transcriptions`) for seamless integrations with existing Whisper applications.
* 🐳 **Docker & GPU Support**: Full Docker Container Toolkit support with NVIDIA GPU passthrough (`docker-compose.yml`).
* 🎬 **YouTube Integration**: Transcribe and translate YouTube video content directly via URL input.
* ☁️ **Google Drive Storage & History**: Persistent session tracking and seamless drive mounting inside Google Colab.
* 🎙️ **Flexible Interfaces**: Supports CLI, REST API, and interactive **Gradio Web UI**.

---

## 📊 Comparison: Enstruct vs Paid Services

| Feature | Enstruct (Ours) | Otter.ai | Transkriptor | AssemblyAI |
| :--- | :---: | :---: | :---: | :---: |
| **Cost** | 🆓 **100% Free** | Paid Subscription | Paid / Minute | Paid / Minute |
| **Hosting** | 💻 Fully Local / Docker | Cloud-only | Cloud-only | API-only |
| **Privacy** | 🔒 Zero data shared, fully private | Processed on third-party | Processed on third-party | Processed on third-party |
| **API / Watch Folder** | ✅ Built-in OpenAI REST API & Watch Folder | Limited | Limited | Paid API-only |
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

Enstruct is designed to work seamlessly as a command-line tool, REST API server, Docker container, or Python library.

### 1. Command Line Interface (CLI)

```bash
# Transcribe an audio file using default large-v3-turbo model into SRT format
enstruct transcribe voice_note.mp3

# Transcribe with target language and VTT format
enstruct transcribe audio.wav --language es --format vtt --output subtitle.vtt

# Watch folder auto-processing (monitors /inbox and saves subtitles to /outbox)
enstruct watch --input-dir /inbox --output-dir /outbox --format srt

# Launch OpenAI-compatible REST API server
enstruct api --host 0.0.0.0 --port 8000

# Batch process an entire directory of mixed audio/video files
enstruct batch /path/to/audios --output /path/to/subtitles --format srt
```

### 2. OpenAI-Compatible REST API

Start the REST API server:
```bash
enstruct api
```

Send a transcription request using standard OpenAI Whisper parameters:
```bash
curl http://localhost:8000/v1/audio/transcriptions \
  -F file="@speech.mp3" \
  -F model="large-v3-turbo" \
  -F response_format="json"
```

### 3. Docker Deployment (Self-Hosted)

Run Enstruct with GPU support using Docker Compose:

```bash
docker-compose up -d
```

This exposes:
- **Gradio Web UI**: `http://localhost:7860`
- **OpenAI-Compatible REST API**: `http://localhost:8000`

### 4. Python Library API

```python
from enstruct.core.transcriber import EnstructTranscriber
from enstruct.tools.subtitle import SubtitleGenerator

# Initialize the transcriber (defaults to large-v3-turbo and auto device selection)
transcriber = EnstructTranscriber(model_size="large-v3-turbo", device="auto")

# Transcribe audio file
result = transcriber.transcribe("interview.m4a")

print(f"Detected Language: {result['language']}")
print(f"Transcript: {result['text']}")

# Generate SRT subtitle format
generator = SubtitleGenerator()
generator.generate(result["segments"], "interview.srt", format="srt")
```

#### Google Drive Manager
```python
from enstruct.tools.drive import DriveManager

drive_manager = DriveManager()
# Mount Google Drive (Colab) or store locally
drive_manager.save_file("transcript.srt", "Subtitles content...")
# View persistent session history
history = drive_manager.get_history()
```

---

## 🌐 Gradio Web Interface

Enstruct includes an interactive browser-based Web UI.

To start the Web UI locally:
```bash
python -m interfaces.web.app
```
Open `http://localhost:7860` in your browser. You can:
1. **Audio Sources**: Upload files, select Google Drive paths, or paste YouTube URLs.
2. **Model Selection**: Choose models (`tiny`, `base`, `small`, `medium`, `large-v3`, `large-v3-turbo`).
3. **Session Logs**: View, refresh, or clear transcription history logs.

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
