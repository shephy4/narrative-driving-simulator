# Narrative Driving Simulator
### MSc Dissertation — De Montfort University, 2026

> **"Towards a Generative Narrative Layer for Driver Training Simulators"**  
> Author: Oluwasefunmi Bamidele | Supervisor: Dr Aboosar

---

## Overview

A Python-based system that integrates a large language model (LLM) with BeamNG.tech, a physics-based driving simulator, to generate personalised, real-time narrative feedback through an AI companion character named **Maya**.

Maya acts as the learner's close friend in the passenger seat. She reads telemetry data from the simulation every 500 milliseconds, detects driving events, and responds with contextually relevant, curriculum-aligned conversation that embeds UK DVSA 2024 training topics naturally — without stating them as rules.

---

## System Architecture

```
Learner Profile (name, confidence, motivation)
        ↓
BeamNGpy — polls sensors every 500ms
        ↓
Event Detection (11 event types)
        ↓
Prompt Builder (profile + events + DVSA curriculum + Gagné events)
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

---

## Requirements

### Software
- Python 3.13
- BeamNG.tech v0.38.3.0 (academic licence — https://beamng.tech)
- Somerset UK map mod (el_ferrito, v4.30) — install via BeamNG mod manager

### Python Dependencies
Install all dependencies with:
```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install beamngpy groq google-generativeai pyttsx3 Pillow numpy
```

### API Keys
You will need:
- **Groq API key** — free tier at https://console.groq.com
- **Gemini API key** — free tier at https://aistudio.google.com (for camera vision, currently disabled)

Create a `.env` file in the root directory:
```
GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

---

## How to Run

### 1. Start BeamNG.tech
- Open BeamNG.tech
- Load the **Somerset UK** map
- Enable BeamNG remote control (required for BeamNGpy connection)

### 2. Run the main connector
```bash
python beamng_connector4.py
```

You will be prompted for:
- Your name
- Confidence level (e.g. very nervous, a little nervous, fairly confident)
- Personal motivation (e.g. "to pick up my daughter from school")
- Route (1 or 2)

### 3. Drive
Maya will respond to your driving events in real time. Responses appear on the BeamNG screen and optionally spoken aloud.

---

## Evaluation Routes

| Route | Spawn Position | Description |
|-------|---------------|-------------|
| Route 1 | (1229, 2800, 175) | Junction near SLOW road marking |
| Route 2 | (902, 2240, 112) | Near building with asphalt road |

---

## DVSA Curriculum Categories (embedded in prompt)

1. Junctions and observations
2. Mirrors and observations (MSM routine)
3. Vulnerable road users
4. Speed management
5. Vehicle controls and signals
6. Road signs and markings
7. Positioning and lane discipline
8. Manoeuvres

---

## Evaluation Framework

Each Maya response is automatically scored against **Smeda, Dakich and Sharda's (2014)** five-criterion digital storytelling framework:

| Criterion | Description | Max Score |
|-----------|-------------|-----------|
| Personal relevance | Maya uses the learner's name and personal motivation | 5 |
| Training embedding | DVSA curriculum embedded naturally in dialogue | 5 |
| Environment consistency | References only elements present in the simulation | 5 |
| Character authenticity | Maya sounds like a real friend, not an instructor | 5 |
| Emotional stakes | Genuine emotional investment in the journey | 5 |
| **Total** | | **25** |

---

## Results Summary

| Route | Sessions | Responses | Mean Total |
|-------|----------|-----------|------------|
| Route 1 | 10 | 98 | 21.81/25 |
| Route 2 | 10 | 91 | 21.97/25 |

---

## Known Limitations

- **Camera vision disabled** — BeamNG camera sensor and Gemini 1.5 Flash vision integration is built into the architecture but disabled during evaluation due to hardware constraints on the development machine (Lenovo ThinkPad T490). The code is present and functional in isolation.
- **Single learner profile** — all 20 evaluation sessions used the Kemi profile. A second profile is identified as future work.
- **No user study** — system evaluated as a DSR proof-of-concept prototype. Human participant evaluation is the next step.

---

## References

- Baylor, I. (2021) *Road Rulez*. Graduate project, California State University, Northridge.
- Gagné, R.M., Briggs, L.J. and Wager, W.W. (1992) *Principles of Instructional Design*. 4th edn.
- Green, M.C. and Brock, T.C. (2000) 'The role of transportation in the persuasiveness of public narratives', *Journal of Personality and Social Psychology*, 79(5).
- Smeda, N., Dakich, E. and Sharda, N. (2014) 'The effectiveness of digital storytelling in the classrooms', *Smart Learning Environments*, 1(1).

---

## Licence

This project was developed for academic purposes as part of an MSc dissertation at De Montfort University. Not for commercial use.