from fastapi import FastAPI, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime
import logging
from typing import List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TripguardCloud")

app = FastAPI(
    title="Tripguard Enterprise Fleet Ingestion API",
    description="Centralized REST and WebSocket gateway for Uber and Rapido safety telemetry.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

class SafetyAlert(BaseModel):
    vehicle_id: str = Field(..., example="CAB-9924-NY")
    driver_id: str = Field(..., example="DRV-4821")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
    distress_phrase: str = Field(..., example="help me")
    vision_status: str = Field(..., example="DROWSINESS_DETECTED")
    confidence_score: float = Field(..., ge=0.0, le=1.0, example=0.94)
    location_lat: float = Field(..., example=28.6139)
    location_lng: float = Field(..., example=77.2090)

@app.get("/")
def health_check():
    return {"status": "online", "service": "Tripguard Fleet Gateway", "timestamp": datetime.utcnow().isoformat()}

@app.post("/api/v1/alerts", status_code=status.HTTP_201_CREATED)
async def receive_safety_alert(alert: SafetyAlert):
    logger.info(f"🚨 INCOMING SAFETY ALERT FROM VEHICLE: {alert.vehicle_id}")

    dispatch_status = "CRITICAL" if alert.confidence_score > 0.85 else "WARNING"
    
    dashboard_payload = {
        "id": f"TG-{int(datetime.utcnow().timestamp())}",
        "timestamp": alert.timestamp,
        "event_type": f"AI_{alert.vision_status}",
        "details": f"Vocal: '{alert.distress_phrase}' | Vision Confidence: {int(alert.confidence_score * 100)}%",
        "vehicle_id": alert.vehicle_id,
        "driver_id": alert.driver_id,
        "location": {"lat": alert.location_lat, "lon": alert.location_lng},
        "status": dispatch_status
    }

    await manager.broadcast(dashboard_payload)

    return {
        "status": "success",
        "message": "Alert processed and broadcasted to Fleet Command.",
        "alert_id": dashboard_payload["id"],
        "action_taken": dispatch_status
    }

@app.websocket("/ws/dashboard")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)