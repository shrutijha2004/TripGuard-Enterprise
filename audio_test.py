import os
import sys
import json
import time
import pyaudio
import requests
from vosk import Model, KaldiRecognizer

MODEL_PATH = "vosk-model-small-en-us-0.15"

if not os.path.exists(MODEL_PATH):
    print(f"ERROR: Model directory '{MODEL_PATH}' not found. Download it from https://alphacephei.com/vosk/models")
    sys.exit(1)

print("Initializing offline speech recognition model...")
model = Model(MODEL_PATH)
recognizer = KaldiRecognizer(model, 16000)

p = pyaudio.PyAudio()
stream = p.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=16000,
    input=True,
    frames_per_buffer=8192
)
stream.start_stream()

print("\nTripguard Audio AI: Active monitoring with expanded phrase dictionaries...")
print("Press Ctrl+C to stop.\n")

# State variables for voice verification
verification_mode = False
timer_start = 0.0
VERIFICATION_DURATION = 5.0  # seconds
last_detected_phrase = "help me"

# FastAPI Cloud Backend Ingestion Endpoint
CLOUD_API_URL = "http://127.0.0.1:8000/api/v1/alerts"

def dispatch_audio_alert(phrase_text):
    """Dispatches confirmed audio distress telemetry to the FastAPI cloud backend."""
    payload = {
        "vehicle_id": "CAB-8821",
        "driver_id": "DRV-901",
        "distress_phrase": f"Acoustic distress keyword matched: '{phrase_text}'",
        "vision_status": "CABIN_DISTRESS_DETECTED",
        "confidence_score": 0.98,
        "location_lat": 28.6139,
        "location_lng": 77.2090
    }
    
    try:
        response = requests.post(CLOUD_API_URL, json=payload, timeout=2.0)
        if response.status_code == 201:
            print(f"🚨 Audio distress successfully dispatched to Cloud Gateway & Dashboard!")
        else:
            print(f"⚠️ Backend returned status code {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Failed to connect to FastAPI backend. Ensure uvicorn main:app is running on port 8000.")
    except Exception as e:
        print(f"Error sending audio alert: {e}")

# Expanded dictionary of contextual distress phrases (reduces single-word false alarms)
DISTRESS_TRIGGERS = [
    "help me",
    "emergency",
    "call the police",
    "let me out",
    "stop the car",
    "driver stop",
    "danger",
    "save me",
    "get me out"
]

# Expanded dictionary of voice-cancellation phrases
CANCELLATION_PHRASES = [
    "false alarm",
    "i am fine",
    "im fine",
    "i'm fine",
    "i'm okay",
    "im okay",
    "i am okay",
    "just joking",
    "all good",
    "everything is fine",
    "talking on the phone"
]

try:
    while True:
        data = stream.read(4096, exception_on_overflow=False)
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            text = result.get("text", "").lower()
            
            if text:
                current_time = time.time()
                
                # If we are currently in the 5-second verification window
                if verification_mode:
                    if current_time - timer_start < VERIFICATION_DURATION:
                        if any(cp in text for cp in CANCELLATION_PHRASES):
                            print(f"\n✅ CANCELLATION DETECTED ('{text}'). False alarm cleared safely.")
                            verification_mode = False
                            continue
                    else:
                        # Timer expired without cancellation -> Confirm Alert!
                        print("\n🚨 CONFIRMED ALERT: No cancellation received. Escalating safety event!")
                        dispatch_audio_alert(last_detected_phrase)
                        verification_mode = False

                # Normal monitoring state for initial distress cues
                if any(dt in text for dt in DISTRESS_TRIGGERS) and not verification_mode:
                    last_detected_phrase = text
                    print(f"\n⚠️ WARNING: Distress pattern detected ('{text}').")
                    print(f"⏳ Listening for cancellation phrase for {VERIFICATION_DURATION}s...")
                    verification_mode = True
                    timer_start = time.time()
                elif not verification_mode:
                    print(f"Heard: '{text}'")

        else:
            # Handle real-time partial feedback and check if verification timer expired mid-stream
            if verification_mode and (time.time() - timer_start >= VERIFICATION_DURATION):
                print("\n🚨 CONFIRMED ALERT: Verification window expired. Escalating safety event!")
                dispatch_audio_alert(last_detected_phrase)
                verification_mode = False

            partial = json.loads(recognizer.PartialResult())
            partial_text = partial.get("partial", "")
            if partial_text:
                if verification_mode:
                    sys.stdout.write(f"\r[VERIFYING...] Heard: {partial_text}   ")
                else:
                    sys.stdout.write(f"\rListening: {partial_text}   ")
                sys.stdout.flush()

except KeyboardInterrupt:
    print("\nStopping audio monitor...")
    stream.stop_stream()
    stream.close()
    p.terminate()