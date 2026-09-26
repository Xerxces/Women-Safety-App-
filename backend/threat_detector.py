import json
from pathlib import Path
from backend.Geofence_handler import haversine_distance

PROJECT_DIR = Path(__file__).resolve().parent.parent
CRIME_DATA_FILE = PROJECT_DIR / "backend" / "crime_data.json"


def load_crime_data():
    """Loads crime data records from JSON file."""
    if not CRIME_DATA_FILE.exists():
        return []
    with open(CRIME_DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def analyze_location_threat(current_lat: float, current_lon: float):
    """
    Evaluates nearby crime incidents within user's proximity.
    Returns overall safety score and nearby threat zones.
    """
    crime_records = load_crime_data()
    nearby_threats = []
    max_severity_weight = 0

    severity_weights = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}

    for zone in crime_records:
        distance = haversine_distance(
            current_lat, current_lon, zone["latitude"], zone["longitude"]
        )

        # Check if user is within threat impact radius
        if distance <= zone["radius_meters"]:
            threat_info = {
                "area_name": zone["area_name"],
                "crime_type": zone["crime_type"],
                "severity": zone["severity"],
                "distance_meters": round(distance, 2),
            }
            nearby_threats.append(threat_info)
            max_severity_weight = max(
                max_severity_weight, severity_weights.get(zone["severity"], 1)
            )

    # Calculate status and safety score (100 = Completely Safe, 0 = High Danger)
    if not nearby_threats:
        status = "SAFE"
        safety_score = 100
        message = "🟢 Area is clear. No active threat zones detected nearby."
    elif max_severity_weight <= 2:
        status = "MODERATE_WARNING"
        safety_score = 65
        message = f"⚠️ Moderate Risk Area: {len(nearby_threats)} crime incident(s) reported nearby."
    else:
        status = "HIGH_THREAT"
        safety_score = 30
        message = f"🚨 HIGH RISK AREA DETECTED! Near {nearby_threats[0]['area_name']}."

    return {
        "status": status,
        "safety_score": safety_score,
        "message": message,
        "nearby_threats": nearby_threats,
    }


if __name__ == "__main__":
    # Test near Railway Station Alleyway
    res = analyze_location_threat(21.2515, 81.6297)
    print("Threat Analysis:", res)