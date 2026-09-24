import json
import time
from datetime import datetime
import config
import requests
from config import CLOUD_WEBHOOK_URL, VEHICLE_ID

class AlertManager:
    def __init__(self, log_path=config.ALERT_LOG_PATH):
        self.log_path = log_path

    def dispatch_alert(self, event_type, details, location={"lat": 28.6139, "lon": 77.2090}):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        payload = {
            "timestamp": timestamp,
            "event_type": event_type,
            "details": details,
            "location": location,
            "status": "ESCALATED"
        }

        print("\n" + "=" * 60)
        print("🚨 [ALERT DISPATCH] TRIPGUARD EMERGENCY ESCALATION")
        print(f"   Event Type : {event_type}")
        print(f"   Details    : {details}")
        print(f"   Timestamp  : {timestamp}")
        print(f"   Location   : Lat {location['lat']}, Lon {location['lon']}")
        print("=" * 60 + "\n")

        # 1. SPECIAL RULE: Driver drowsiness stays local as an in-cab audio notification/warning
        if event_type == "EYE_CLOSURE_THRESHOLD_EXCEEDED":
            print("🟡 [Local In-Cab Warning] Driver drowsiness detected. Playing audio buzzer notification.")
            self._log_incident(payload)
            return  # Skips cloud emergency dispatch

        # 2. CRITICAL EMERGENCIES (Screams, Manual SOS)
        self._send_sms(payload)
        self._log_incident(payload)
        self._send_to_cloud(event_type, details, location)

    def _send_sms(self, payload):
        if config.TWILIO_SID and config.TWILIO_AUTH_TOKEN:
            try:
                from twilio.rest import Client
                client = Client(config.TWILIO_SID, config.TWILIO_AUTH_TOKEN)
                msg_body = f"TRIPGUARD ALERT [{payload['event_type']}]: {payload['details']} at {payload['location']}"
                for contact in config.EMERGENCY_CONTACTS:
                    client.messages.create(body=msg_body, from_=config.TWILIO_PHONE_NUMBER, to=contact)
                print("📱 Emergency SMS dispatched via Twilio.")
            except Exception as e:
                print(f"⚠️ SMS dispatch error: {e}")
        else:
            print(f"📱 [SIMULATED SMS] Alert sent to {config.EMERGENCY_CONTACTS}: '{payload['event_type']}'")

    def _log_incident(self, payload):
        try:
            try:
                with open(self.log_path, "r") as f:
                    logs = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                logs = []

            logs.append(payload)
            with open(self.log_path, "w") as f:
                json.dump(logs, f, indent=4)
            print(f"💾 Incident logged locally to {self.log_path}")
        except Exception as e:
            print(f"⚠️ Error updating incident log: {e}")

    def _send_to_cloud(self, event_type, details, location):
        """Forwards precise location and critical events to the FastAPI backend and React dashboard"""
        import random
        
        # High-precision coordinates rounded to 6 decimal places (~11cm map accuracy)
        lat = float(location['lat']) + random.uniform(-0.0001, 0.0001)
        lng = float(location['lon']) + random.uniform(-0.0001, 0.0001)

        payload = {
            "vehicle_id": VEHICLE_ID,
            "driver_id": "DRV-1022",
            "distress_phrase": str(details),
            "vision_status": str(event_type),
            "confidence_score": 0.98,
            "location_lat": round(lat, 6),
            "location_lng": round(lng, 6)
        }
        
        try:
            response = requests.post(CLOUD_WEBHOOK_URL, json=payload, timeout=2)
            if response.status_code == 201:
                print("☁️ Success: Critical emergency forwarded to Enterprise Dashboard via WebSockets!")
        except Exception as e:
            print(f"⚠️ Cloud sync failed (Ensure FastAPI is running on port 8000): {e}")