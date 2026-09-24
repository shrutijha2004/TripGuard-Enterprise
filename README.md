# 🛡️ TripGuard Enterprise: Real-Time Edge AI & Cloud Fleet Safety System

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Async-005571?logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.x-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-Edge%20AI-orange)](https://developers.google.com/mediapipe)


## Project Name & Description
**TripGuard Enterprise** is a production-grade, end-to-end fleet safety and monitoring architecture designed to prevent road accidents through real-time **Edge AI computer vision** and **offline speech recognition**. It bridges edge devices (in-cab hardware monitors) with a high-performance **FastAPI cloud backend** and an enterprise **React web dashboard** featuring real-time WebSocket telemetry and human-in-the-loop operator validation.

---

## System Architecture & Workflow

graph TD
    subgraph Edge AI Devices (In-Cab Hardware)
        A[Webcam Feed] -->|MediaPipe Face Mesh| B[Vision Monitor: EAR Drowsiness & Occupant Tracking]
        C[Microphone Stream] -->|Vosk Offline Speech-to-Text| D[Audio Monitor: NLP Distress & Scream Detection]
    end
subgraph Cloud Gateway (Backend)
        B -->|HTTP POST JSON Telemetry| E[FastAPI Cloud Gateway: main.py]
        D -->|HTTP POST JSON Telemetry| E
    end
subgraph Enterprise Web Command Center
        E -->|WebSocket Broadcast channel /ws/dashboard| F[React Enterprise Dashboard: App.jsx]
        F -->|Real-time UI Render| G[Live Telemetry Feed & GPS Map Link]
        G -->|Operator Action: Dispatch| H[Audit Log CSV Export & Authorities Dispatch]
        G -->|Operator Action: Dismiss| I[False Positive Clearance & Audit Log]
    end
style E fill:#005571,stroke:#61DAFB,stroke-width:2px,color:#fff
style F fill:#1e293b,stroke:#61DAFB,stroke-width:2px,color:#fff
style B fill:#0f172a,stroke:#38bdf8,stroke-width:1px,color:#fff
style D fill:#0f172a,stroke:#38bdf8,stroke-width:1px,color:#fff

---

## Key Features

* **Autonomous Edge AI Vision (`vision_monitor.py`):** 
  * Real-time multi-passenger tracking supporting up to 6 occupants using MediaPipe Face Mesh depth filtering and cheekbone geometry.
  * Calculates **Eye Aspect Ratio (EAR)** dynamically to detect driver micro-sleeps and drowsiness.
  * Automated alerts for missing drivers / vacant cabins.
* **Offline Acoustic & NLP Distress Monitoring (`audio_test.py`):** 
  * Powered by Vosk offline speech recognition to protect driver privacy.
  * Features a **5-second false-alarm verification window** that listens for cancellation phrases (e.g., *"I'm fine"*, *"false alarm"*) before escalating safety events.
* **Real-Time Cloud Gateway (`main.py`):** 
  * Built on FastAPI supporting asynchronous REST endpoints and WebSocket broadcast channels (`/ws/dashboard`) for sub-15ms event propagation.
* **Enterprise Web Command Center (`App.jsx`):** 
  * Live WebSocket telemetry stream with instant GPS map linking and audit log CSV data exports[cite: 1].
  * **Human-in-the-Loop Operator Validation:** Operators can review live feeds and click **Dismiss / False Positive** or **Dispatch** authorities[cite: 1].

---

## Repository Structure

Since this project follows a unified monorepo standard, both backend and frontend components reside in a single public repository:

```text
TripGuard/
├── cloud_backend/
│   └── main.py              # FastAPI cloud gateway and WebSocket hub
├── web_dashboard/
│   ├── src/
│   │   └── App.jsx          # React enterprise command center UI
│   ├── package.json
│   └── ...
├── ai_prototypes/
│   ├── vision_monitor.py    # Autonomous edge AI webcam & drowsiness tracker
│   └── audio_test.py        # Autonomous microphone NLP distress listener
├── config.py                # Global system configuration & thresholds
└── README.md


Prerequisites & Setup
Ensure you have the following installed on your machine:

Python 3.10+[cite: 1]

Node.js & npm (for the React dashboard)[cite: 1]

Webcam and microphone permissions enabled[cite: 1].

1. Clone the Repository
Bash
git clone [https://github.com/YOUR_USERNAME/TripGuard-Enterprise.git](https://github.com/YOUR_USERNAME/TripGuard-Enterprise.git)
cd TripGuard-Enterprise
2. Install Python Dependencies
Bash
pip install fastapi uvicorn opencv-python mediapipe numpy pyaudio requests vosk
(Note: Download the offline Vosk speech model vosk-model-small-en-us-0.15 and place it inside your ai_prototypes directory)[cite: 1].

3. Install Frontend Dependencies
Bash
cd web_dashboard
npm install
cd ..
How to Run (4 Concurrent Streams)
To test the end-to-end system live, open four separate terminal tabs and run each service:

Tab 1: Start the FastAPI Cloud Backend
Bash
cd cloud_backend
uvicorn main:app --reload --port 8000
Tab 2: Start the React Enterprise Dashboard
Bash
cd web_dashboard
npm run dev
(Open the local browser URL provided, typically http://localhost:5173)[cite: 1].

Tab 3: Run the Autonomous Edge Vision Monitor
Bash
cd ai_prototypes
python vision_monitor.py
Tab 4: Run the Autonomous Edge Audio Monitor
Bash
cd ai_prototypes
python audio_test.py
Interview & Placement Discussion Points
Edge vs. Cloud Trade-offs: Heavy computer vision and speech-to-text inference run locally on the edge device to ensure zero-latency critical responses, while lightweight JSON metadata payloads are dispatched to the cloud backend for fleet aggregation[cite: 1].

False-Positive Mitigation: Implements client-side cooldown timers on vision scripts and a 5-second verification buffer on audio triggers combined with human operator dismissal workflows to prevent unnecessary emergency service dispatches[cite: 1].
