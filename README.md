# Narrative Driving Simulator
### MSc Dissertation — De Montfort University, 2026

> **"Towards a Generative Narrative Layer for Driver Training Simulators"**  
> Author: Oluw B | Supervisor: Dr A ni

---

## Overview

A Python-based system that integrates a large language model (LLM) with BeamNG.tech, a physics-based driving simulator, to generate personalised, real-time narrative feedback through an AI companion character named **Maya**.

Maya acts as the learner's close friend in the passenger seat. She reads telemetry data from the simulation every 500 milliseconds, detects eleven categories of driving event, and responds with contextually relevant, curriculum-aligned conversation that embeds UK DVSA 2024 training topics naturally — without stating them as rules.

---

## System Architecture

```
Learner Profile (name, confidence, motivation)
        ↓
BeamNG.tech — physics simulation running
        ↓
BeamNGpy — polls sensors every 500ms via localhost
        ↓
Event Detection (11 event types from telemetry)
        ↓
Prompt Builder (profile + events + DVSA curriculum + Gagné event)
        ↓
Groq API — llama-3.3-70b-versatile
        ↓
Maya Response — displayed on BeamNG screen (< 2 seconds)
```

---

## Files

| File | Description |
|------|-------------|
| `beamng_connector4.py` | Main evaluation connector — real-time event detection, prompt construction, Groq API calls, Smeda auto-scoring |
| `driving_simulator_v2.py` | Real-time event-driven system (no pre-written story) |
| `narrative_generator_v3.py` | Original story generator — 3 variants scored and selected |
| `requirements.txt` | Python dependencies |

---

## Step-by-Step Installation

### Step 1 — Install Python 3.13

Download and install Python 3.13 from https://www.python.org/downloads/

During installation, make sure to tick **"Add Python to PATH"**.

Verify the installation:
```bash
python --version
# Should show: Python 3.13.x
```

---

### Step 2 — Get BeamNG.tech (Academic Licence)

BeamNG.tech is the research version of BeamNG.drive. It is free for academic use.

1. Go to https://beamng.tech
2. Click **Request Academic Licence**
3. Fill in your university details — use your DMU email address
4. You will receive a licence key and download link by email
5. Download and install BeamNG.tech v0.38.3.0

> **Important:** This project uses BeamNG.**tech** (the research/academic version), not BeamNG.**drive** (the commercial game). They look similar but BeamNG.tech supports the Python API (BeamNGpy) that this system requires.

---

### Step 3 — Locate Your BeamNG.tech Installation Path

BeamNGpy needs to know where BeamNG.tech is installed so it can launch it automatically. You do not need to open BeamNG.tech manually — the Python script launches it for you.

The default installation path is usually:
```
C:\Program Files\BeamNG.tech
```

Check inside `beamng_connector4.py` and make sure the `home` path matches your installation:
```python
bng = BeamNGpy('localhost', 64256, home='C:\Program Files\BeamNG.tech')
```

If BeamNG.tech is installed in a different location, update this path to match.

> BeamNGpy communicates with BeamNG.tech over a local network socket on port 64256. Python launches BeamNG.tech, waits for it to start, and then connects automatically. No internet connection is required for this communication — it is all local on your machine.

---

### Step 4 — Install the Somerset UK Map

Somerset UK (v4.30, el_ferrito) is a community-made map that provides authentic UK road layouts, left-hand driving, UK road signs, and AI traffic support. It is the only available BeamNG map that meets these requirements.

1. Open BeamNG.tech
2. Go to **Main Menu → Repository → Browse Maps**
3. Search for **Somerset UK** or **el_ferrito**
4. Click **Subscribe / Install**
5. Wait for the download to complete
6. The map will appear in your map list as **Somerset, UK**

Alternatively, download directly from the BeamNG forums and place the `.zip` file in:
```
C:\Users\[YourName]\AppData\Local\BeamNG.tech\0.38\mods\
```

---

### Step 5 — Clone the Repository

```bash
git clone https://github.com/shephy4/narrative-driving-simulator
cd narrative-driving-simulator
```

Or download the ZIP from GitHub and extract it.

---

### Step 6 — Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs:

| Package | Purpose |
|---------|---------|
| `beamngpy` | Python API for communicating with BeamNG.tech |
| `groq` | Groq API client for LLM calls |
| `google-generativeai` | Gemini 1.5 Flash (camera vision — currently disabled) |
| `pyttsx3` | Text-to-speech (currently disabled during evaluation) |
| `Pillow` | Image processing for camera frames |
| `numpy` | Numerical processing |
| `python-dotenv` | Loads API keys from .env file |

---

### Step 7 — Get Your API Keys

**Groq API key (required)**
1. Go to https://console.groq.com
2. Sign up for a free account
3. Go to **API Keys → Create API Key**
4. Copy the key — it starts with `gsk_`

**Gemini API key (optional — camera vision is currently disabled)**
1. Go to https://aistudio.google.com
2. Sign in with a Google account
3. Click **Get API Key**
4. Copy the key — it starts with `AIza`

Create a file called `.env` in the project root directory:
```
GROQ_API_KEY=gsk_your_key_here
GEMINI_API_KEY=AIza_your_key_here
```

> The `.env` file is listed in `.gitignore` and will never be uploaded to GitHub. Never share your API keys publicly.

---

### Step 8 — Understand How Python Connects to BeamNG.tech

This is the most important part to understand before running the system.

**How the connection works:**

```
BeamNG.tech (running on your machine)
    |
    | Opens a server socket on localhost:64256
    |
BeamNGpy (Python library)
    |
    | Connects to localhost:64256
    | Sends commands (spawn vehicle, attach sensors)
    | Reads sensor data every 500ms
    |
beamng_connector4.py
    |
    | Processes sensor data
    | Detects driving events
    | Sends prompt to Groq API
    | Receives Maya response
    | Sends Lua command to display text on screen
```

### Step 8 — Run the System

Simply run the script. BeamNG.tech will launch automatically.

```bash
python beamng_connector4.py
```

You will be prompted:
```
Enter your name: Kemi
Enter your confidence level (e.g. very nervous, fairly confident): very nervous
What is your personal motivation for this journey?: to pick up my daughter from school
Select route (1 or 2): 1
```

The system will:
1. Connect to BeamNG.tech
2. Load Somerset UK
3. Spawn the vehicle at the Route 1 coordinates (1229, 2800, 175)
4. Begin polling sensors every 500ms
5. Generate Maya responses in real time as you drive

Maya's responses appear in the **top-left corner** of the BeamNG.tech screen.

---

## Evaluation Routes

| Route | Spawn Position | Description |
|-------|---------------|-------------|
| Route 1 | (1229, 2800, 175) | Junction near SLOW road marking |
| Route 2 | (902, 2240, 112) | Near building with asphalt road |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ConnectionRefusedError` | Check the `home` path in `beamng_connector4.py` matches your BeamNG.tech installation folder. |
| `ModuleNotFoundError: beamngpy` | Run `pip install beamngpy` |
| `AuthenticationError: groq` | Check your `.env` file has the correct Groq API key |
| Vehicle spawns mid-air | You are on the wrong map. Load Somerset UK specifically. |
| No text appearing on screen | Check BeamNG.tech Lua hooks are enabled. Restart BeamNG.tech. |
| Maya responds too frequently | The 12-second cooldown is in `beamng_connector4.py` line ~85. Increase the value. |
| Somerset UK map not found | Install the map via the BeamNG repository (Step 4). |


## Licence

This project was developed for academic purposes as part of an MSc dissertation at De Montfort University. Not for commercial use.