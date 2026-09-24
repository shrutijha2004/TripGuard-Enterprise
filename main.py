import sys
import os
import time
import json
import threading
import pyaudio
from vosk import Model, KaldiRecognizer

import config
from alert_manager import AlertManager
from vision_monitor import VisionMonitor

class AudioMonitorThread(threading.Thread):
    def __init__(self, alert_callback):
        super().__init__()
        self.alert_callback = alert_callback
        self.running = True
        self.daemon = True

    def run(self):
        if not os.path.exists(config.VOSK_MODEL_PATH):
            print(f"❌ Audio Engine Error: Vosk model missing at {config.VOSK_MODEL_PATH}")
            return

        model = Model(config.VOSK_MODEL_PATH)
        recognizer = KaldiRecognizer(model, config.AUDIO_SAMPLE_RATE)

        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=config.AUDIO_SAMPLE_RATE,
            input=True,
            frames_per_buffer=8192
        )
        stream.start_stream()

        print("🎙️ Audio AI Engine active: Listening for vocal distress patterns...")
        verification_mode = False
        timer_start = 0.0

        try:
            while self.running:
                data = stream.read(config.AUDIO_CHUNK_SIZE, exception_on_overflow=False)
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    text = result.get("text", "").lower()

                    if text:
                        current_time = time.time()
                        if verification_mode:
                            if current_time - timer_start < config.VERIFICATION_DURATION:
                                if any(cp in text for cp in config.CANCELLATION_PHRASES):
                                    print(f"\n✅ Voice cancellation phrase detected: '{text}'. Alarm cleared.")
                                    verification_mode = False
                                    continue
                            else:
                                self.alert_callback("AUDIO_DISTRESS_UNCONFIRMED", "Distress trigger without vocal cancellation.")
                                verification_mode = False

                        if any(dt in text for dt in config.DISTRESS_TRIGGERS) and not verification_mode:
                            print(f"\n⚠️ DISTRESS PATTERN DETECTED: '{text}'")
                            print(f"⏳ Verification timer started ({config.VERIFICATION_DURATION}s to cancel)...")
                            verification_mode = True
                            timer_start = time.time()
                else:
                    if verification_mode and (time.time() - timer_start >= config.VERIFICATION_DURATION):
                        self.alert_callback("AUDIO_DISTRESS_TIMEOUT", "Distress phrase confirmed (cancellation window elapsed).")
                        verification_mode = False
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()

    def stop(self):
        self.running = False

def main():
    print("=" * 60)
    print("       TRIPGUARD MULTIMODAL IN-CAB SAFETY SYSTEM       ")
    print("=" * 60)

    alert_mgr = AlertManager()

    def safety_event_handler(event_type, details):
        alert_mgr.dispatch_alert(event_type=event_type, details=details)

    # Launch Audio Processing in Background Thread
    audio_thread = AudioMonitorThread(alert_callback=safety_event_handler)
    audio_thread.start()

    # Launch Vision Processing on Main Thread
    vision_mon = VisionMonitor(camera_idx=config.CAMERA_INDEX)
    try:
        vision_mon.start_monitoring(callback_on_event=safety_event_handler)
    except KeyboardInterrupt:
        print("\nShutting down Tripguard system...")
    finally:
        audio_thread.stop()
        print("Tripguard safely terminated.")

if __name__ == "__main__":
    main()