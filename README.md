# 🎵 Whispers of the Wires

**AI-Based Music Composer** — Transform your emotions into personalized musical compositions.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-red.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MusicGen](https://img.shields.io/badge/AI-MusicGen%20(Meta)-purple.svg)](https://huggingface.co/facebook/musicgen-small)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎼 **AI Music Generation** | Meta's MusicGen model (free, no API key) |
| 🎯 **Mood Analysis** | Multi-dimensional emotion recognition (VAD model) |
| 🎹 **MIDI Export** | Download compositions for DAW editing |
| 📊 **Visualizations** | Real-time waveform and spectrogram |
| 💾 **Generation History** | Save and revisit your creations |
| ❤️ **Favorites** | Bookmark your best compositions |
| 🎛️ **Advanced Controls** | Tempo, key, genre, duration, VAD sliders |
| 🌙 **Dark Theme** | Premium startup-grade UI |
| 🔓 **100% Free** | No API keys, no subscriptions, no limits |

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** (3.10+ recommended)
- **pip** package manager
- **ffmpeg** (optional, for audio processing)

### Installation

```bash
# 1. Extract or clone the project
cd whispers_of_the_wires

# 2. Create virtual environment (recommended)
python -m venv venv

# 3. Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt
```

> **Note:** First run will download Meta's MusicGen model (~1.2GB) from Hugging Face automatically. No API key needed!

### Running the App

```bash
# Method 1: Using the runner script
python run.py

# Method 2: Direct Streamlit
streamlit run app/main.py

# Method 3: Direct Python
python app.py
```

The app opens at **http://localhost:8501**

---

## 🎨 Usage Guide

### 1. Describe Your Mood
Type something like:
- "peaceful rainy morning with coffee"
- "energetic workout session"
- "melancholic piano piece"

### 2. Or Select a Preset
Choose from 8 curated mood presets:
- ☀️ Peaceful Morning
- 🌙 Late Night Work
- 💪 Workout Energy
- 🌧️ Rainy Day
- 🎉 Celebration
- 🧘 Deep Focus
- 🎨 Creative Flow
- 💕 Romantic Evening

### 3. Fine-tune Parameters
- **Valence** — Positivity (-1 to +1)
- **Arousal** — Energy level (-1 to +1)
- **Dominance** — Intensity (-1 to +1)
- **Genre** — 20 genres available
- **Tempo** — 40 to 200 BPM
- **Duration** — 5 to 60 seconds

### 4. Generate & Enjoy
Click **"✨ Generate Music"** and watch the AI compose!

### 5. Export Your Music
- 🎹 **MIDI** — For DAW editing (FL Studio, Ableton, Logic)
- 💾 **WAV** — High-quality audio
- 📊 **Visualizations** — Waveform & spectrogram

---

## 🏗️ Architecture

```
whispers_of_the_wires/
├── app/
│   ├── main.py              # Main Streamlit application
│   ├── utils/
│   │   ├── emotion_analyzer.py   # NLP + VAD emotion analysis
│   │   ├── music_generator.py      # MusicGen AI + Procedural synthesis
│   │   ├── visualizer.py          # Audio visualizations
│   │   └── session_manager.py     # Session state management
│   └── assets/
│       └── css/
│           └── style.css    # Premium dark theme (11KB)
├── config/
│   └── __init__.py         # Configuration & constants
├── tests/
│   └── test_app.py         # Test suite
├── requirements.txt         # Python dependencies
├── run.py                   # Entry point script
├── setup.py                 # Package setup
├── Dockerfile               # Container image
├── docker-compose.yml       # Docker orchestration
├── Makefile                 # Build commands
├── README.md               # This file
├── LICENSE                 # MIT License
└── CHANGELOG.md            # Version history
```

---

## 🛠️ Technology Stack

| Layer | Technology | License |
|-------|-----------|---------|
| **Frontend** | Streamlit + Custom CSS | Apache 2.0 |
| **AI Model** | MusicGen (Meta) | MIT (code) / CC-BY-NC 4.0 (weights) |
| **Audio Processing** | numpy, scipy, soundfile | BSD/MIT |
| **MIDI** | pretty_midi | MIT |
| **Visualization** | matplotlib, SVG | PSF |
| **Emotion Analysis** | Custom NLP + VAD | MIT |

### AI Model Details

**MusicGen** by Meta AI:
- **Paper:** [Simple and Controllable Music Generation](https://arxiv.org/abs/2306.05284) (Copet et al., 2023)
- **Model:** `facebook/musicgen-small` (300M parameters, ~1.2GB)
- **Source:** [Hugging Face](https://huggingface.co/facebook/musicgen-small)
- **License:** MIT (code), CC-BY-NC 4.0 (model weights)
- **No API key required** — downloads automatically on first use

---

## 🐳 Docker Deployment

```bash
# Build image
docker build -t whispers-of-the-wires .

# Run container
docker run -p 8501:8501 whispers-of-the-wires

# Or use docker-compose
docker-compose up -d
```

---

## 🧪 Testing

```bash
# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=app
```

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📄 License

**MIT License** — Free for personal and commercial use.

See [LICENSE](LICENSE) for full text.

---

## 🙏 Acknowledgments

- **Meta AI** — MusicGen model ([Paper](https://arxiv.org/abs/2306.05284))
- **Hugging Face** — Model hosting & Transformers library
- **Streamlit** — Amazing web framework
- **Open-source community** — All the libraries that make this possible

---

<div align="center">

Built with 💜 using entirely **free and open-source** tools.

**No API keys. No subscriptions. No limits.**

</div>
