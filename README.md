# CircuitMind AI ⚡

> **AI-powered electrical network analysis tool** — solve Mesh Analysis, Nodal Analysis, Thevenin/Norton Equivalents, Superposition, Delta-Wye, and more. Upload a circuit image or describe your network in text.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

---

## Features

- 🧠 **Powered by Google Gemini** — multimodal AI understands both text and circuit diagram images
- 📷 **Image Input** — upload hand-drawn or printed schematic photos
- ✏️ **Text Input** — describe your circuit in plain English
- ⚡ **Exact Math** — SymPy solver executes generated code for 100% accurate numerical answers
- 🔄 **Model Fallback** — automatically switches between Gemini models if quota is hit
- 🌐 **Web Interface** — beautiful dark-mode UI with MathJax equation rendering

## Supported Analysis Methods

| Method | Description |
|--------|-------------|
| Mesh Analysis | KVL-based loop current analysis |
| Nodal Analysis | KCL-based node voltage analysis |
| Thevenin's Theorem | Find Vth and Rth across terminals |
| Norton's Theorem | Find In and Rn across terminals |
| Superposition | Multi-source independent analysis |
| Delta-Wye Transform | Network topology conversion |
| Source Transformation | Voltage ↔ Current source equivalence |
| Max Power Transfer | Find RL for maximum power |

## Quick Start (Local)

```bash
git clone https://github.com/YOUR_USERNAME/circuit-mind-ai.git
cd circuit-mind-ai

pip install -r requirements.txt

# Create .env file with your API key
echo "GEMINI_API_KEY=your_key_here" > .env

python app.py        # local only
# OR
python launch.py     # local + public tunnel via localhost.run
```

Get a free Gemini API key at [aistudio.google.com](https://aistudio.google.com/apikey).

## Deploy to Render (Free)

1. Fork this repository
2. Go to [render.com](https://render.com) → New → Web Service
3. Connect your GitHub repo
4. Add environment variable: `GEMINI_API_KEY = your_key`
5. Deploy — get a free `*.onrender.com` URL!

## Tech Stack

- **Backend**: Python / Flask
- **AI**: Google Gemini API (`google-genai`)
- **Solver**: SymPy (symbolic math)
- **Frontend**: Vanilla HTML/CSS/JS + MathJax

## License

MIT
