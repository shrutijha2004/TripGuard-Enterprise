import cv2
import time
import numpy as np
import mediapipe as mp
import requests
import config

class VisionMonitor:
    def __init__(self, camera_idx=config.CAMERA_INDEX):
        self.camera_idx = camera_idx
        self.mp_face_mesh = mp.solutions.face_mesh
        
        # Tracks the driver plus up to 5 passengers in a standard cab/SUV
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=6, 
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.is_running = False
        
        self.driver_x_threshold = 0.5 
        self.driver_is_left_in_frame = True 
        
        # FastAPI Cloud Backend Ingestion Endpoint & Cooldown Tracking
        self.cloud_api_url = "http://127.0.0.1:8000/api/v1/alerts"
        self.last_dispatched_time = 0
        self.cooldown_seconds = 30.0

    def _calculate_ear(self, landmarks, eye_indices, w, h):
        pts = [np.array([landmarks[i].x * w, landmarks[i].y * h]) for i in eye_indices]
        v1 = np.linalg.norm(pts[1] - pts[5])
        v2 = np.linalg.norm(pts[2] - pts[4])
        horiz = np.linalg.norm(pts[0] - pts[3])
        return (v1 + v2) / (2.0 * horiz) if horiz > 0 else 0.0

    def _send_cloud_alert(self, vision_status, details, confidence_score):
        """Dispatches automated safety telemetry payload to the FastAPI backend gateway."""
        current_time = time.time()
        if current_time - self.last_dispatched_time < self.cooldown_seconds:
            return # Respect cooldown window to prevent flooding
            
        payload = {
            "vehicle_id": "CAB-9924-NY",
            "driver_id": "DRV-4821",
            "distress_phrase": f"None ({details})",
            "vision_status": vision_status,
            "confidence_score": confidence_score,
            "location_lat": 28.6139,
            "location_lng": 77.2090
        }
        
        try:
            response = requests.post(self.cloud_api_url, json=payload, timeout=2.0)
            if response.status_code == 201:
                print(f"🚨 Autonomous Telemetry dispatched to Cloud Gateway: {vision_status}")
                self.last_dispatched_time = current_time
            else:
                print(f"⚠️ Cloud gateway responded with status code {response.status_code}")
        except requests.exceptions.ConnectionError:
            print("❌ Failed to connect to FastAPI backend. Ensure main_2.py is running on port 8000.")
        except Exception as e:
            print(f"Error dispatching safety alert: {e}")

    def start_monitoring(self, callback_on_event=None):
        cap = cv2.VideoCapture(self.camera_idx)
        if not cap.isOpened():
            print("❌ Vision Engine: Unable to open camera stream.")
            return

        self.is_running = True
        eyes_closed_start = None
        no_face_start = None

        LEFT_EYE = [362, 385, 387, 263, 373, 380]
        RIGHT_EYE = [33, 160, 158, 133, 153, 144]

        print("📹 Vision AI active (Multi-passenger depth filtering + Automated Cloud Dispatch enabled)...")

        while self.is_running and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            h, w, _ = frame.shape
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(rgb_frame)
            current_time = time.time()
            
            driver_found = False
            driver_landmarks = None
            max_face_width = 0

            if results.multi_face_landmarks:
                # PASS 1: Identify the driver using spatial X-coordinates AND depth (face size)[cite: 26]
                for face_landmarks in results.multi_face_landmarks:
                    nose_x = face_landmarks.landmark[1].x
                    
                    # Check if face is on the driver's side of the cabin[cite: 26]
                    is_driver_side = (nose_x < self.driver_x_threshold) if self.driver_is_left_in_frame else (nose_x >= self.driver_x_threshold)
                    
                    if is_driver_side:
                        # Measure face width using cheekbone landmarks (indices 234 and 454)[cite: 26]
                        left_cheek = face_landmarks.landmark[234].x
                        right_cheek = face_landmarks.landmark[454].x
                        face_width = abs(right_cheek - left_cheek)
                        
                        # The largest face on the driver's side belongs to the front row (the driver)[cite: 26]
                        if face_width > max_face_width:
                            max_face_width = face_width
                            driver_landmarks = face_landmarks

                # PASS 2: Process driver telemetry and render labels for everyone[cite: 26]
                for face_landmarks in results.multi_face_landmarks:
                    nose_x = face_landmarks.landmark[1].x
                    nose_y = face_landmarks.landmark[1].y
                    pixel_x = int(nose_x * w)
                    pixel_y = int(nose_y * h)

                    if face_landmarks == driver_landmarks:
                        driver_found = True
                        left_ear = self._calculate_ear(face_landmarks.landmark, LEFT_EYE, w, h)
                        right_ear = self._calculate_ear(face_landmarks.landmark, RIGHT_EYE, w, h)
                        avg_ear = (left_ear + right_ear) / 2.0

                        if avg_ear < config.EAR_THRESHOLD:
                            if eyes_closed_start is None:
                                eyes_closed_start = current_time
                            elif current_time - eyes_closed_start >= config.EYE_CLOSED_DURATION:
                                cv2.putText(frame, "DRIVER DROWSINESS ALERT!", (30, 50),
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                                if callback_on_event:
                                    callback_on_event("VISION_DROWSINESS", "Driver eyes closed beyond threshold.")
                                
                                # Automatically push alert to Cloud Backend & Frontend Dashboard
                                self._send_cloud_alert(
                                    vision_status="EYE_CLOSURE_THRESHOLD_EXCEEDED",
                                    details="Driver micro-sleep / eyes closed",
                                    confidence_score=0.95
                                )
                        else:
                            eyes_closed_start = None

                        cv2.putText(frame, f"Driver EAR: {avg_ear:.2f}", (30, h - 30),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                        
                        cv2.putText(frame, "DRIVER", (pixel_x - 20, pixel_y - 50),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                    else:
                        cv2.putText(frame, "PASSENGER", (pixel_x - 40, pixel_y - 50),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 165, 0), 2)

            if not driver_found:
                eyes_closed_start = None
                if no_face_start is None:
                    no_face_start = current_time
                elif current_time - no_face_start >= config.FACE_LOST_DURATION:
                    cv2.putText(frame, "WARNING: DRIVER FACE LOST", (30, 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    if callback_on_event:
                        callback_on_event("VISION_FACE_LOST", "Driver not detected in Region of Interest.")
                    
                    # Automatically push face loss alert to Cloud Backend
                    self._send_cloud_alert(
                        vision_status="CABIN_OCCUPANT_MISSING",
                        details="Driver face lost from Region of Interest",
                        confidence_score=0.91
                    )
            else:
                no_face_start = None

            cv2.imshow("Tripguard Multi-Passenger Vision Monitor", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()
        self.is_running = False

    def stop(self):
        self.is_running = False

if __name__ == "__main__":
    monitor = VisionMonitor()
    monitor.start_monitoring()