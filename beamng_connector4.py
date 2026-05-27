from beamngpy import BeamNGpy, Scenario, Vehicle
from beamngpy.sensors import Electrics, Damage, Camera
from groq import Groq
import google.generativeai as genai
import PIL.Image
import pyttsx3
import numpy as np
import threading
import time
import os
import json
from datetime import datetime

from dotenv import load_dotenv
import os

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ── Config ───────────────────────────────────────────────────
BEAMNG_PATH = r"C:\Users\T490\Downloads\BeamNG\BeamNG.tech.v0.38.3.0"
SPEED_LIMIT = 50

groq_client = Groq(api_key=GROQ_API_KEY)
genai.configure(api_key=GEMINI_API_KEY)
vision_model = genai.GenerativeModel('gemini-1.5-flash')

DVSA_CURRICULUM = """
UK DVSA 2024 OFFICIAL TEST FAILURE CATEGORIES:
1. Junctions - look right left right, judge speed, give way
2. Mirrors - Mirror-Signal-Manoeuvre every time, check every 8-10 seconds
3. Vulnerable road users - cyclists 1.5m gap, children near schools, pedestrians
4. Speed management - 30mph residential, 2 second rule dry, 4 seconds wet
5. Vehicle controls - indicate before turning, progressive braking, smooth steering
6. Road signs and markings - stop signs, give way, double white lines, box junctions
7. Positioning - keep left, correct lane, safe clearance from parked cars
8. Manoeuvres - check mirrors and blind spots, reverse slowly, full observations
"""

GAGNE_EVENTS = [
    "gain attention",
    "stimulate recall",
    "present content",
    "elicit performance",
    "enhance retention",
]

def get_gagne_event(elapsed_seconds):
    if elapsed_seconds < 60:    return GAGNE_EVENTS[0]
    elif elapsed_seconds < 120: return GAGNE_EVENTS[1]
    elif elapsed_seconds < 180: return GAGNE_EVENTS[2]
    elif elapsed_seconds < 240: return GAGNE_EVENTS[3]
    else:                        return GAGNE_EVENTS[4]

# ── Combined mean calculator ──────────────────────────────────
def calculate_combined_mean(name, route, total_runs=10):
    """
    Reads ALL session JSON files for a given profile name and route.
    Calculates the combined mean across all runs.
    Called automatically after each session.
    """
    criteria = [
        "personal_relevance",
        "training_embedding",
        "environment_consistency",
        "character_authenticity",
        "emotional_stakes",
        "total"
    ]

    all_scores = {c: [] for c in criteria}
    runs_found = []

    log_dir = "session_logs"
    if not os.path.exists(log_dir):
        return

    for fname in sorted(os.listdir(log_dir)):
        # Match files for this profile and route
        prefix = f"{name.replace(' ', '_')}_Route{route}_"
        if not fname.startswith(prefix) or not fname.endswith(".json"):
            continue

        try:
            with open(os.path.join(log_dir, fname)) as f:
                data = json.load(f)

            run_num = data.get("run_number", "?")
            runs_found.append(run_num)

            # Collect all scored responses from this run
            for r in data.get("responses", []):
                if r.get("scores"):
                    for c in criteria:
                        val = r["scores"].get(c)
                        if val is not None:
                            all_scores[c].append(val)

        except Exception as e:
            print(f"  Could not read {fname}: {e}")

    if not runs_found:
        return

    # Calculate combined means across all runs
    combined = {}
    for c in criteria:
        vals = all_scores[c]
        combined[c] = round(sum(vals) / len(vals), 2) if vals else 0

    print(f"\n{'='*55}")
    print(f"COMBINED MEAN — {name} | Route {route} | Runs: {sorted(runs_found, key=str)}")
    print(f"{'='*55}")
    print(f"  Responses across all runs:   {len(all_scores['total'])}")
    print(f"  Personal relevance:          {combined['personal_relevance']}/5")
    print(f"  Training embedding:          {combined['training_embedding']}/5")
    print(f"  Environment consistency:     {combined['environment_consistency']}/5")
    print(f"  Character authenticity:      {combined['character_authenticity']}/5")
    print(f"  Emotional stakes:            {combined['emotional_stakes']}/5")
    print(f"  COMBINED MEAN TOTAL:         {combined['total']}/25")
    print(f"{'='*55}\n")

    # Save combined mean to a summary file
    summary_file = f"session_logs/{name.replace(' ','_')}_Route{route}_COMBINED_MEAN.json"
    summary = {
        "profile_name": name,
        "route": route,
        "runs_included": sorted(runs_found, key=str),
        "total_responses_scored": len(all_scores['total']),
        "combined_means": combined
    }
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"Combined mean saved to: {summary_file}")

# ── Session logger ────────────────────────────────────────────
class SessionLogger:
    def __init__(self, profile, route, run_number):
        self.profile    = profile
        self.route      = route
        self.run_number = run_number
        self.responses  = []
        self.start_time = datetime.now()

        os.makedirs('session_logs', exist_ok=True)

        self.filename = (
            f"session_logs/"
            f"{profile['name'].replace(' ','_')}_"
            f"Route{route}_"
            f"Run{str(run_number).zfill(2)}_"
            f"{self.start_time.strftime('%Y-%m-%d_%H-%M')}.json"
        )
        print(f"Logging session to: {self.filename}")

    def log_response(self, elapsed, events, scene, gagne_event, text):
        self.responses.append({
            "elapsed_seconds": round(elapsed),
            "gagne_event":     gagne_event,
            "events_detected": events,
            "scene_described": scene,
            "maya_response":   text,
            "scores":          None
        })

    def save(self):
        data = {
            "profile":         self.profile,
            "route":           self.route,
            "run_number":      self.run_number,
            "date":            self.start_time.strftime('%Y-%m-%d %H:%M'),
            "total_responses": len(self.responses),
            "responses":       self.responses
        }
        with open(self.filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\nSession saved: {self.filename}")
        return self.filename

    def score_and_save(self):
        """
        Scores every Maya response against Smeda's 5 criteria.
        Then calculates combined mean across ALL runs for this
        profile and route — not just this session.
        """
        print("\nScoring responses against Smeda criteria...")
        for i, r in enumerate(self.responses):
            print(f"  Scoring response {i+1} of {len(self.responses)}...", end='\r')
            try:
                scoring_prompt = f"""
Score this driving training response on 5 criteria from 1 to 5.

LEARNER NAME: {self.profile['name']}
LEARNER MOTIVATION: {self.profile['important_person']}
RESPONSE: {r['maya_response']}

CRITERIA:
1. Personal relevance - uses learner name, feels personally meaningful
2. Training embedding - driving rule embedded naturally, not stated directly
3. Environment consistency - fits UK Somerset countryside road context
4. Character authenticity - sounds like a real friend, not an instructor
5. Emotional stakes - references something personally meaningful to learner

Return ONLY 5 numbers separated by commas. Example: 4,5,3,5,4
No other text.
"""
                resp = groq_client.chat.completions.create(
                    messages=[{"role": "user", "content": scoring_prompt}],
                    model="llama-3.3-70b-versatile",
                    max_tokens=20
                )
                scores_text = resp.choices[0].message.content.strip()
                scores = [int(s.strip()) for s in scores_text.split(',')]
                if len(scores) == 5:
                    r['scores'] = {
                        "personal_relevance":      scores[0],
                        "training_embedding":      scores[1],
                        "environment_consistency": scores[2],
                        "character_authenticity":  scores[3],
                        "emotional_stakes":        scores[4],
                        "total":                   sum(scores)
                    }
            except Exception as e:
                print(f"\n  Scoring note: {e}")
                r['scores'] = None

        # Save this run's file
        self.save()

        # Per-session summary
        scored = [r for r in self.responses if r['scores']]
        if scored:
            run_mean = round(
                sum(r['scores']['total'] for r in scored) / len(scored), 2)
            print(f"\n  Run {self.run_number} mean total: {run_mean}/25")

        # Combined mean across ALL runs for this profile + route
        print("\nCalculating combined mean across all runs so far...")
        calculate_combined_mean(
            self.profile['name'],
            self.route
        )

# ── Text to speech ────────────────────────────────────────────
def maya_speak(text):
    def speak():
        try:
            tts = pyttsx3.init()
            tts.setProperty('rate', 150)
            tts.setProperty('volume', 0.9)
            voices = tts.getProperty('voices')
            for voice in voices:
                if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                    tts.setProperty('voice', voice.id)
                    break
            tts.say(text)
            tts.runAndWait()
            tts.stop()
        except Exception as e:
            print(f"Speech note: {e}")
    threading.Thread(target=speak, daemon=True).start()

# ── Learner profile ───────────────────────────────────────────
def get_learner_profile():
    print("\n" + "=" * 50)
    print("   NARRATIVE DRIVING SIMULATOR")
    print("   Powered by BeamNG.tech + AI")
    print("=" * 50)
    print("\nTell Maya a little about yourself.\n")
    name = input("1. What is your name? ").strip()
    print("\n2. How confident do you feel about driving?")
    print("   a) Very nervous")
    print("   b) A little nervous")
    print("   c) Okay")
    print("   d) Confident")
    confidence = input("   Enter a, b, c or d: ").strip().lower()
    important_person = input(
        "\n3. Who are you driving for today? "
        "(e.g. to pick up my child, to support my mum, for myself): "
    ).strip()
    print("\n4. Which route?")
    print("   1) Route 1 — Junction near SLOW marking (1229, 2800)")
    print("   2) Route 2 — Near building with asphalt road (902, 2240)")
    route = input("   Enter 1 or 2: ").strip()
    print("\n5. Run number? (1-10)")
    run_number = input("   Enter run number: ").strip()
    try:
        run_number = int(run_number)
    except Exception:
        run_number = 1

    confidence_map = {
        "a": "very nervous", "b": "a little nervous",
        "c": "fairly okay",  "d": "confident"
    }

    spawn_points = {
        "1": {
            "pos":   (1229.0, 2800.0, 175.0),
            "rot":   (0.0, 0.0, 0.9609, 0.2768),
            "label": "Route 1 — Junction near SLOW marking"
        },
        "2": {
            "pos":   (902.996521, 2240.44312, 112.616074),
            "rot":   (0.0, 0.0, -0.7327, 0.6806),
            "label": "Route 2 — Near building with asphalt road"
        }
    }
    chosen = spawn_points.get(route, spawn_points["1"])

    return {
        "name":             name,
        "confidence":       confidence_map.get(confidence, "a little nervous"),
        "important_person": important_person,
        "route":            route,
        "run_number":       run_number,
        "spawn_pos":        chosen["pos"],
        "spawn_rot":        chosen["rot"],
        "route_label":      chosen["label"]
    }

# ── BeamNG screen display ─────────────────────────────────────
def show_on_screen(bng, message):
    safe_msg = message.replace("'", "").replace('"', '')
    bng.control.queue_lua_command(
        f"guihooks.trigger('Message', "
        f"{{msg='{safe_msg}', ttl=6, icon='information'}})"
    )

def maya_say(bng, message):
    print(f"\nMAYA: {message}\n")
    show_on_screen(bng, f"Maya: {message}")
    # maya_speak(message)  # ← uncomment to enable speech

# ── Gemini vision — non-blocking ─────────────────────────────
def poll_camera_async(dashcam, on_scene_callback):
    def poll():
        try:
            dashcam.poll()
            colour_frame = dashcam.data.get('colour')
            if colour_frame is not None:
                pil_image = PIL.Image.fromarray(
                    colour_frame.astype(np.uint8))
                response = vision_model.generate_content([
                    "You are a dashcam on a UK road. "
                    "Describe in ONE sentence what you see. "
                    "Focus on: pedestrians, cyclists, children, "
                    "road signs, junctions, bends, hazards, vehicles, "
                    "road markings. If clear say 'clear road ahead'.",
                    pil_image
                ])
                scene = response.text.strip()
                if scene:
                    on_scene_callback(scene)
        except Exception as e:
            print(f"\nCamera note: {e}")
    threading.Thread(target=poll, daemon=True).start()

# ── Groq response — non-blocking ─────────────────────────────
def get_maya_response_async(events, scene_description,
                             profile, elapsed_seconds,
                             bng, logger, on_done_callback):
    def generate():
        try:
            gagne_event = get_gagne_event(elapsed_seconds)
            events_text = " and ".join(events) if events else "normal driving"
            scene_context = ""
            if scene_description:
                scene_context = (f"\nWHAT THE DASHCAM SEES:\n"
                                 f"{scene_description}\n")
            prompt = f"""
You are Maya, a close friend in the passenger seat with
{profile['name']} learning to drive in Somerset, UK.
{profile['name']} is {profile['confidence']} about driving.
They are driving {profile['important_person']}.

WHAT JUST HAPPENED: {events_text}
{scene_context}
UK DVSA CURRICULUM — embed one topic naturally:
{DVSA_CURRICULUM}

Gagné event to fulfil: {gagne_event}

RULES:
1. 1-2 sentences ONLY
2. Sound like a real friend, not an instructor
3. NEVER state a rule directly
4. Address {profile['name']} by name
5. React specifically to cyclists, pedestrians, children if seen
6. Mention road signs or junctions naturally if visible
7. Tone: {'reassure and encourage' if 'nervous' in profile['confidence']
          else 'gently challenge and stretch'}
"""
            response = groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                max_tokens=80
            )
            text = response.choices[0].message.content.strip().strip('"')

            if logger:
                logger.log_response(
                    elapsed_seconds, events,
                    scene_description, gagne_event, text)

            on_done_callback(text)
        except Exception as e:
            print(f"\nGroq note: {e}")
    threading.Thread(target=generate, daemon=True).start()

# ── Detect driving events ─────────────────────────────────────
def detect_events(current, previous):
    events = []
    speed      = current['speed']
    prev_speed = previous['speed']
    brake      = current['brake']
    throttle   = current['throttle']
    steering   = current['steering']
    damage     = current['damage']
    wheel_slip = current['wheel_slip']

    if speed > SPEED_LIMIT:
        events.append(f"speeding at {speed:.0f} km/h in {SPEED_LIMIT} zone")
    if speed < 5 and prev_speed > 30:
        events.append(f"very sudden stop from {prev_speed:.0f} km/h")
    if brake > 0.8 and prev_speed > 20:
        events.append("harsh emergency braking")
    elif brake > 0.5 and prev_speed > 15:
        events.append("heavy braking")
    if (abs(speed - prev_speed) < 2 and speed > 15
            and brake < 0.1 and abs(steering) < 0.15):
        events.append("driving very smoothly and steadily")
    if abs(steering) > 200:
        events.append("very sharp steering — tight bend or hazard")
    elif abs(steering) > 80:
        events.append("significant steering — bend or junction")
    if wheel_slip > 0.3:
        events.append("wheel slip — loss of traction")
    if damage > previous['damage'] + 0.5:
        events.append("vehicle took damage — collision or kerb strike")
    if throttle > 0.9 and speed > 40:
        events.append("aggressive acceleration at speed")
    if 0 < speed < 8 and throttle > 0.3:
        events.append("very slow — possible junction hesitation")
    return events

# ── Main simulation ───────────────────────────────────────────
def run_simulation(profile):
    print(f"\n=== LOADING BEAMNG SIMULATION ===")
    print(f"Profile: {profile['name']} | {profile['route_label']} | Run {profile['run_number']}")
    print("Please wait while Somerset UK loads...\n")

    logger = SessionLogger(
        profile, profile['route'], profile['run_number'])

    bng = BeamNGpy('localhost', 64256, home=BEAMNG_PATH)
    bng.open(launch=True)

    scenario = Scenario('somerset', 'narrative_drive')
    vehicle  = Vehicle('ego', model='etk800',
                       license=profile['name'][:3].upper())

    electrics     = Electrics()
    damage_sensor = Damage()
    vehicle.attach_sensor('electrics', electrics)
    vehicle.attach_sensor('damage',    damage_sensor)

    scenario.add_vehicle(vehicle,
        pos=profile['spawn_pos'],
        rot_quat=profile['spawn_rot'])

    scenario.make(bng)
    bng.load_scenario(scenario)
    bng.start_scenario()

    try:
        bng.traffic.spawn(max_amount=4, extra_amount=0)
        print("AI traffic spawned.")
    except Exception as e:
        print(f"Traffic note: {e}")

    print("Waiting for scenario to fully load...")
    time.sleep(5)

    # Camera disabled for performance — uncomment to enable
    dashcam = None
    # try:
    #     dashcam = Camera(
    #         'dashcam', bng, vehicle,
    #         requested_update_time=10.0,
    #         pos=(0, 2, 1), dir=(0, 1, 0),
    #         field_of_view_y=70,
    #         resolution=(320, 240),
    #         is_render_colours=True,
    #         is_render_annotations=False,
    #         is_render_depth=False
    #     )
    #     print("Dashcam attached.")
    #     time.sleep(2)
    # except Exception as e:
    #     print(f"Camera note: {e}")

    state = {
        'last_scene':     None,
        'maya_busy':      False,
        'camera_polling': False,
    }
    state_lock = threading.Lock()

    def on_scene(scene):
        print(f"\n[DASHCAM: {scene}]")
        with state_lock:
            state['last_scene']     = scene
            state['camera_polling'] = False

    def on_maya_done(text):
        maya_say(bng, text)
        with state_lock:
            state['maya_busy'] = False

    def on_opening_done(text):
        maya_say(bng, text)

    get_maya_response_async(
        ["starting the journey"], None,
        profile, 0, bng, logger, on_opening_done)

    print(f"\nMaya is watching everything — drive naturally.")
    print("Drive for at least 2 minutes then press Ctrl+C to end.\n")

    previous = {
        'speed': 0, 'brake': 0, 'throttle': 0,
        'steering': 0, 'damage': 0, 'wheel_slip': 0
    }

    last_response_time   = time.time()
    last_camera_poll     = time.time()
    response_cooldown    = 12
    camera_poll_interval = 10
    start_time           = time.time()

    while True:
        try:
            vehicle.poll_sensors()

            speed      = electrics.data.get('wheelspeed', 0) * 3.6
            brake      = electrics.data.get('brake', 0)
            throttle   = electrics.data.get('throttle', 0)
            steering   = electrics.data.get('steering', 0)
            wheel_slip = electrics.data.get('wheelslip', 0)
            damage_data = damage_sensor.data
            damage_val  = (damage_data.get('damage', 0)
                           if isinstance(damage_data, dict) else 0)

            current = {
                'speed':      round(speed, 1),
                'brake':      brake,
                'throttle':   throttle,
                'steering':   steering,
                'damage':     damage_val,
                'wheel_slip': (wheel_slip
                               if isinstance(wheel_slip, (int, float))
                               else 0)
            }

            elapsed = time.time() - start_time
            mins    = int(elapsed // 60)
            secs    = int(elapsed % 60)

            print(
                f"Time: {mins:02d}:{secs:02d} | "
                f"Speed: {current['speed']:.1f} km/h | "
                f"Brake: {brake:.2f} | "
                f"Dmg: {damage_val:.2f}",
                end='\r'
            )

            current_time    = time.time()
            time_since_last = current_time - last_response_time

            with state_lock:
                cam_polling = state['camera_polling']

            if (dashcam and not cam_polling and
                    current_time - last_camera_poll > camera_poll_interval):
                with state_lock:
                    state['camera_polling'] = True
                poll_camera_async(dashcam, on_scene)
                last_camera_poll = current_time

            with state_lock:
                maya_busy  = state['maya_busy']
                last_scene = state['last_scene']

            if not maya_busy and time_since_last > response_cooldown:
                events = detect_events(current, previous)
                if events or last_scene:
                    with state_lock:
                        state['maya_busy']  = True
                        state['last_scene'] = None
                    get_maya_response_async(
                        events, last_scene,
                        profile, elapsed,
                        bng, logger, on_maya_done)
                    last_response_time = current_time

            previous = current
            time.sleep(0.5)

        except KeyboardInterrupt:
            print(f"\n\nSession ended after {mins:02d}:{secs:02d}.")
            break
        except Exception as e:
            print(f"\nError: {e}")
            time.sleep(1)

    # Score this run and calculate combined mean across all runs
    logger.score_and_save()
    print(f"\nReady for Run {profile['run_number'] + 1}. Restart the script.")

def main():
    profile = get_learner_profile()
    run_simulation(profile)

if __name__ == "__main__":
    main()