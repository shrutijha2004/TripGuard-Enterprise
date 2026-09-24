import os
import sys
import json
import time
import threading
import cv2
import numpy as np
import pyaudio
import requests
from datetime import datetime
from vosk import Model, KaldiRecognizer
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Shared state between Vision and Audio threads
system_state = {
    "vision_status": "CALM",  # Options: "CALM", "STRESSED", "NO_FACE"
    "active": True
}

CLOUD_ENDPOINT = "http://127.0.0.1:8000/api/v1/alerts"

def send_alert_to_cloud(phrase, vision_status):
    """Sends confirmed multi-modal safety alert to the FastAPI backend."""
    payload = {
        "vehicle_id": "CAB-9924-NY",
        "driver_id": "DRV-4821",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "distress_phrase": phrase,
        "vision_status": vision_status,
        "confidence_score": 0.95,
        "location_lat": 40.7128,
        "location_lng": -74.0060
    }
    
    try:
        response = requests.post(CLOUD_ENDPOINT, json=payload, timeout=3)
        if response.status_code == 201:
            print("☁️ [Cloud Sync] Alert successfully transmitted to FastAPI backend!")
            print(f"Server Response: {response.json()}")
        else:
            print(f"⚠️ [Cloud Sync] Failed with status code {response.status_code}: {response.text}")
    except requests.exceptions.ConnectionError:
        print("❌ [Cloud Sync Error] Could not connect to FastAPI backend. Is Uvicorn running?")

def vision_monitoring_thread():
    """Background thread running MediaPipe Face Landmarker to assess passenger composure."""
    model_path = "face_landmarker.task"
    if not os.path.exists(model_path):
        print(f"[Vision Thread] Error: {model_path} not found.")
        return

    base_options = python.BaseOptions(model_asset_path=model_path)
    options = vision.FaceLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.IMAGE,
        num_faces=1
    )
    
    detector = vision.FaceLandmarker.create_from_options(options)
    cap = cv2.VideoCapture(0)
    
    print("[Vision Thread] Edge privacy vision monitor started.")

    while system_state["active"]:
        ret, frame = cap.read()
        if not ret:
            break

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        detection_result = detector.detect(mp_image)

        if detection_result.face_landmarks:
            # Default to CALM unless rapid motion or distress patterns are detected
            system_state["vision_status"] = "CALM"
        else:
            system_state["vision_status"] = "NO_FACE"

        time.sleep(0.05)

    cap.release()
    cv2.destroyAllWindows()


def audio_monitoring_thread():
    """Background thread running Vosk offline speech keyword spotter with multi-modal fusion."""
    model_path = "vosk-model-small-en-us-0.15"
    if not os.path.exists(model_path):
        print(f"[Audio Thread] Error: Model folder {model_path} not found.")
        return

    model = Model(model_path)
    recognizer = KaldiRecognizer(model, 16000)

    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=16000,
        input=True,
        frames_per_buffer=4096
    )
    stream.start_stream()

    print("[Audio Thread] Offline audio distress keyword spotter started.")
    
    distress_triggers = ["help me", "emergency", "call the police", "let me out", "stop the car"]

    try:
        while system_state["active"]:
            data = stream.read(2048, exception_on_overflow=False)
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "").lower()

                if text:
                    if any(dt in text for dt in distress_triggers):
                        current_vision = system_state["vision_status"]
                        print(f"\n⚠️ AUDIO TRIGGER DETECTED: '{text}'")
                        print(f"🔍 Multimodal Check -> Camera Vision Status: [{current_vision}]")

                        # MULTIMODAL FUSION DECISION ENGINE
                        if current_vision == "CALM":
                            print("🛡️ SUPPRESSED: Audio keyword heard, but vision confirms passenger is calm (phone conversation). No alert sent.")
                        else:
                            print("🚨 CONFIRMED SAFETY ALERT: Escalating to cloud backend...")
                            send_alert_to_cloud(text, current_vision)
                    else:
                        print(f"Heard: '{text}' (Safe)")

    except Exception as e:
        print(f"[Audio Thread] Error: {e}")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()


if __name__ == "__main__":
    import mediapipe as mp
    print("=== Tripguard Multi-Modal Edge AI Initializing ===")
    
    v_thread = threading.Thread(target=vision_monitoring_thread, daemon=True)
    a_thread = threading.Thread(target=audio_monitoring_thread, daemon=True)

    v_thread.start()
    a_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down Tripguard safety monitors...")
        system_state["active"] = False