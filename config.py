import os
from pathlib import Path

# Define base directory of the project dynamically
BASE_DIR = Path(__file__).resolve().parent

# Model Paths
FACE_DETECTOR_PATH = BASE_DIR / "face_detector.tflite"
FACE_LANDMARKS_PATH = BASE_DIR / "face_landmarks_detector.tflite"

# Audio & Vision Thresholds
EAR_THRESHOLD = 0.22
CONSEC_FRAMES_THRESHOLD = 15

# Camera Settings
CAMERA_INDEX = 0

# Audio Configuration
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHUNK_SIZE = 4096
VERIFICATION_DURATION = 5.0  # Verification window in seconds

# Vocal Trigger Phrases
DISTRESS_TRIGGERS = [
    "help me", "emergency", "call the police", "let me out",
    "stop the car", "driver stop", "danger", "save me", "get me out"
]
CANCELLATION_PHRASES = [
    "false alarm", "i am fine", "im fine", "i'm fine",
    "i'm okay", "im okay", "i am okay", "just joking", "all good"
]

# Vision Configuration
CAMERA_INDEX = 0
EAR_THRESHOLD = 0.21         # Eye Aspect Ratio threshold for drowsiness detection
EYE_CLOSED_DURATION = 2.0    # Seconds of closed eyes to trigger drowsiness alert
FACE_LOST_DURATION = 3.0     # Seconds of face absence before triggering obscuration alert

# Alert & Incident Telemetry Logging
EMERGENCY_CONTACTS = ["+1234567890"]
ALERT_LOG_PATH = os.path.join(BASE_DIR, "incidents_log.json")

# Twilio Cloud SMS Integration (Optional)
TWILIO_SID = os.getenv("TWILIO_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "")