import os
import sys
import requests
from datetime import datetime
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# Ensure project backend paths are loaded
PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_DIR))

# Directories
EVIDENCE_DIR = PROJECT_DIR / "evidence"
EVIDENCE_DIR.mkdir(exist_ok=True)

from backend.location_handler import get_current_location
from backend.Evidence_handler import record_audio_evidence, send_telegram_audio
from backend.Geofence_handler import RouteMonitor, haversine_distance
from backend.threat_detector import analyze_location_threat
from backend.wireless_handler import get_wireless_evidence_summary
import psutil
from typing import Optional
from backend.voice_listener import ContinuousVoiceListener
from fastapi import FastAPI, BackgroundTasks

# 1. Initialize FastAPI app
app = FastAPI(title="Women Safety MVP")

# 2. Define callback function (single instance)
def on_voice_emergency_detected(detected_phrase: str, pre_audio_bytes: bytes = None):
    print(f"🚨 Hands-Free Voice Trigger Activated: '{detected_phrase}'")
    execute_emergency_pipeline(
        user_id="Dhananjay",
        trigger_source=f"Voice Activated ('{detected_phrase}')"
    )

# 3. Instantiate voice listener
voice_listener = ContinuousVoiceListener(callback_function=on_voice_emergency_detected)

# 4. Modern lifespan startup handler
@app.on_event("startup")
def start_background_voice_service():
    print("🚀 Initializing 24/7 Background Mic Listener...")
    voice_listener.start_listening()
load_dotenv(PROJECT_DIR / ".env")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_IDS")

# Initialize FastAPI App
app = FastAPI(title="Women Safety API", version="1.0")

# Store latest location in memory
latest_location = {
    "latitude": None,
    "longitude": None,
    "accuracy": None
}

# Global route monitoring object
active_route = None


# Models
class EmergencyData(BaseModel):
    user_id: str = "Dhananjay"
    trigger_source: str = "API"
    confidence_score: Optional[float] = 0.0
    detected_phrase: Optional[str] = "Manual Trigger"
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class LocationData(BaseModel):
    latitude: float
    longitude: float
    accuracy: Optional[float] = None

class StartRouteRequest(BaseModel):
    destination_lat: float
    destination_lon: float
    max_deviation_meters: float = 300.0

class LocationPingRequest(BaseModel):
    current_lat: float
    current_lon: float


# Pipeline Execution
def execute_emergency_pipeline(
    user_id: str = "Dhananjay",
    trigger_source: str = "API",
    override_lat: float = None,
    override_lon: float = None
):
    """Executes full emergency sequence in background using live Windows GPS."""
    print(f"🚨 Executing pipeline triggered by: {trigger_source}")

    # Use manually passed coordinates if provided, otherwise fetch live Windows GPS
    if override_lat and override_lon:
        maps_link = f"https://www.google.com/maps?q={override_lat},{override_lon}"
        loc_source = "Manual Override"
    else:
        loc_info = get_current_location()
        maps_link = loc_info.get("maps_url", "N/A")
        loc_source = loc_info.get("source", "Windows Location Service")

    battery = psutil.sensors_battery()
    battery_percent = f"{battery.percent}%" if battery else "Unknown"
    is_plugged = "Plugged In" if (battery and battery.power_plugged) else "On Battery"

    wireless_evidence = get_wireless_evidence_summary()

    alert_text = (
        f"🚨 **EMERGENCY DISTRESS ALERT** 🚨\n\n"
        f"**User:** {user_id}\n"
        f"**Source:** {trigger_source}\n"
        f"**Battery:** {battery_percent} ({is_plugged})\n"
        f"**Location Source:** {loc_source}\n"
        f"**Google Maps:** {maps_link}\n\n"
        f"{wireless_evidence}\n\n"
        f"🎙️ *Recording 10 seconds of live audio evidence...*"
    )

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": alert_text, "parse_mode": "Markdown"}

    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print("❌ Error sending alert text:", e)

    audio_file = record_audio_evidence(duration=10)
    if audio_file:
        send_telegram_audio(
            bot_token=BOT_TOKEN,
            chat_id=CHAT_ID,
            audio_file_path=audio_file,
            caption="📁 **Live Audio Evidence Recorded**",
        )
# API Endpoints
@app.get("/")
def root():
    return {"status": "online", "system": "Women Safety API"}

@app.post("/api/emergency")
def emergency_alert(data: EmergencyData, background_tasks: BackgroundTasks):
    background_tasks.add_task(
        execute_emergency_pipeline,
        user_id="Dhananjay",
        trigger_source=f"Voice Detected ({data.detected_phrase})"
    )
    return {"status": "emergency_triggered"}

@app.post("/api/update_location")
def update_location(data: LocationData):
    global latest_location
    latest_location = {
        "latitude": data.latitude,
        "longitude": data.longitude,
        "accuracy": data.accuracy
    }
    return {"status": "location_updated", "location": latest_location}
# =========================================================
# INTERACTIVE MAP & AUTOMATIC GEOFENCE MONITORING
# =========================================================

@app.get("/map", response_class=HTMLResponse)
def get_map_page():
     """Serves an interactive map to pick a destination and start monitoring."""
     html_content = """
     <!DOCTYPE html>
     <html>
     <head>
        <title>Safe Route Monitoring</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 0; }
            #map { height: 70vh; width: 100%; }
            .container { padding: 15px; text-align: center; }
            button { background: #d9534f; color: white; border: none; padding: 12px 20px; font-size: 16px; border-radius: 5px; cursor: pointer; }
            button:disabled { background: #cccccc; }
            #status { margin-top: 10px; font-weight: bold; color: #333; }
        </style>
    </head>
    <body>
        <div id="map"></div>
        <div class="container">
            <p><strong>Click anywhere on the map to set your Destination!</strong></p>
            <button id="startBtn" onclick="startRoute()" disabled>Start Safe Route Monitoring</button>
            <div id="status">Select destination on map...</div>
        </div>

        <script>
            let map, userMarker, destMarker, currentLat, currentLon, destLat, destLon;
            let watchId = null;

            // Initialize Map
            map = L.map('map').setView([21.2514, 81.6296], 13);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }).addTo(map);

            // Fetch live location on start
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(position => {
                    currentLat = position.coords.latitude;
                    currentLon = position.coords.longitude;
                    map.setView([currentLat, currentLon], 15);
                    userMarker = L.marker([currentLat, currentLon]).addTo(map).bindPopup("Your Location").openPopup();
                });
            }

            // Map click handler to set destination
            map.on('click', function(e) {
                destLat = e.latlng.lat;
                destLon = e.latlng.lng;

                if (destMarker) map.removeLayer(destMarker);
                destMarker = L.marker([destLat, destLon], {color: 'red'}).addTo(map).bindPopup("Destination Selected").openPopup();

                document.getElementById('startBtn').disabled = false;
                document.getElementById('status').innerText = `Destination set: ${destLat.toFixed(4)}, ${destLon.toFixed(4)}`;
            });

            function startRoute() {
                // Initialize Route in Backend
                fetch('/api/route/start', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        destination_lat: destLat,
                        destination_lon: destLon,
                        max_deviation_meters: 300.0
                    })
                })
                .then(res => res.json())
                .then(data => {
                    document.getElementById('status').innerText = "🟢 Active Monitoring: Tracking movement...";
                    document.getElementById('startBtn').disabled = true;

                    // Start Continuous Live Location Tracking
                    watchId = navigator.geolocation.watchPosition(sendPing, err => console.error(err), {
                        enableHighAccuracy: true,
                        maximumAge: 5000,
                        timeout: 10000
                    });
                });
            }

            function sendPing(position) {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;

                if (userMarker) userMarker.setLatLng([lat, lon]);

                fetch('/api/route/ping', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ current_lat: lat, current_lon: lon })
                })
                .then(res => res.json())
                .then(res => {
                    if (res.status === 'route_deviation_alert') {
                        document.getElementById('status').innerHTML = "<span style='color:red;'>🚨 OFF ROUTE! Telegram Emergency Triggered!</span>";
                    } else if (res.status === 'arrived') {
                        document.getElementById('status').innerHTML = "<span style='color:green;'>🎉 Destination Reached Safely!</span>";
                        navigator.geolocation.clearWatch(watchId);
                    }
                });
            }
        </script>
    </body>
    </html>
"""
     return HTMLResponse(content=html_content)


@app.post("/api/update_location")
def update_location(data: LocationData):
    global latest_location
    latest_location = {
        "latitude": data.latitude,
        "longitude": data.longitude,
        "accuracy": data.accuracy
    }
    return {"status": "location_updated", "location": latest_location}

@app.get("/api/get_latest_location")
def get_latest_location():
    return latest_location

@app.get("/api/get_latest_location")
def get_latest_location():
    return latest_location


# Safe Route / Geofencing Endpoints
@app.post("/api/route/start")
def start_route(req: StartRouteRequest):
    global active_route
    active_route = RouteMonitor(
        destination_lat=req.destination_lat,
        destination_lon=req.destination_lon,
        max_allowed_deviation_meters=req.max_deviation_meters
    )
    return {"status": "success", "message": "Safe route monitoring initiated."}

@app.post("/api/route/ping")
def ping_location(req: LocationPingRequest, background_tasks: BackgroundTasks):
    global active_route
    if not active_route or not active_route.is_active:
        return {"status": "error", "message": "No active route session found."}

    check_result = active_route.check_position(req.current_lat, req.current_lon)

    if check_result.get("status") == "route_deviation_alert":
        background_tasks.add_task(
            execute_emergency_pipeline,
            user_id="Dhananjay",
            trigger_source="Geofence Route Deviation Alert"
        )

    return check_result
# =========================================================
# INTERACTIVE MAP & AUTOMATIC GEOFENCE MONITORING
# =========================================================

@app.get("/map", response_class=HTMLResponse)
def get_map_page():
    """Serves an interactive map to pick a destination and start monitoring."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Safe Route Monitoring</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 0; }
            #map { height: 75vh; width: 100%; }
            .container { padding: 15px; text-align: center; }
            button { background: #d9534f; color: white; border: none; padding: 12px 20px; font-size: 16px; border-radius: 5px; cursor: pointer; }
            button:disabled { background: #cccccc; }
            #status { margin-top: 10px; font-weight: bold; color: #333; }
        </style>
    </head>
    <body>
        <div id="map"></div>
        <div class="container">
            <p><strong>Click anywhere on the map to set your Destination!</strong></p>
            <button id="startBtn" onclick="startRoute()" disabled>Start Safe Route Monitoring</button>
            <div id="status">Select destination on map...</div>
        </div>

        <script>
            let map, userMarker, destMarker, currentLat, currentLon, destLat, destLon;
            let watchId = null;

            // Initialize Map
            map = L.map('map').setView([21.2514, 81.6296], 13);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }).addTo(map);

            // Fetch live location on start
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(position => {
                    currentLat = position.coords.latitude;
                    currentLon = position.coords.longitude;
                    map.setView([currentLat, currentLon], 15);
                    userMarker = L.marker([currentLat, currentLon]).addTo(map).bindPopup("Your Location").openPopup();
                });
            }

            // Map click handler to set destination
            map.on('click', function(e) {
                destLat = e.latlng.lat;
                destLon = e.latlng.lng;

                if (destMarker) map.removeLayer(destMarker);
                destMarker = L.marker([destLat, destLon]).addTo(map).bindPopup("Destination Selected").openPopup();

                document.getElementById('startBtn').disabled = false;
                document.getElementById('status').innerText = `Destination set: ${destLat.toFixed(4)}, ${destLon.toFixed(4)}`;
            });

            function startRoute() {
                fetch('/api/route/start', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        destination_lat: destLat,
                        destination_lon: destLon,
                        max_deviation_meters: 300.0
                    })
                })
                .then(res => res.json())
                .then(data => {
                    document.getElementById('status').innerText = "🟢 Active Monitoring: Tracking movement...";
                    document.getElementById('startBtn').disabled = true;

                    watchId = navigator.geolocation.watchPosition(sendPing, err => console.error(err), {
                        enableHighAccuracy: true,
                        maximumAge: 5000,
                        timeout: 10000
                    });
                });
            }

            function sendPing(position) {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;

                if (userMarker) userMarker.setLatLng([lat, lon]);

                fetch('/api/route/ping', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ current_lat: lat, current_lon: lon })
                })
                .then(res => res.json())
                .then(res => {
                    if (res.status === 'route_deviation_alert') {
                        document.getElementById('status').innerHTML = "<span style='color:red;'>🚨 OFF ROUTE! Telegram Emergency Triggered!</span>";
                    } else if (res.status === 'arrived') {
                        document.getElementById('status').innerHTML = "<span style='color:green;'>🎉 Destination Reached Safely!</span>";
                        navigator.geolocation.clearWatch(watchId);
                    }
                });
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# =========================================================
# THREAT DETECTOR ENDPOINT
# =========================================================

class ThreatCheckRequest(BaseModel):
    latitude: float
    longitude: float

@app.post("/api/threat/check")
def check_threat_level(req: ThreatCheckRequest):
    return analyze_location_threat(req.latitude, req.longitude)
# ==========================================
# 24/7 HANDS-FREE VOICE LISTENER INTEGRATION
# ==========================================
from backend.voice_listener import ContinuousVoiceListener

def on_voice_emergency_detected(detected_phrase: str, pre_audio_bytes: bytes = None):
    print(f"🚨 Hands-Free Voice Trigger Activated: '{detected_phrase}'")
    execute_emergency_pipeline(
        user_id="Dhananjay",
        trigger_source=f"Voice Activated ('{detected_phrase}')"
    )

voice_listener = ContinuousVoiceListener(callback_function=on_voice_emergency_detected)

@app.on_event("startup")
def start_background_voice_service():
    print("🚀 Initializing 24/7 Background Mic Listener...")
    voice_listener.start_listening()