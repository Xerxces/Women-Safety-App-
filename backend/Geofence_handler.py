import math
import time

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculates the great-circle distance between two points on Earth in meters.
    """
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c  # Distance in meters

class RouteMonitor:
    def __init__(self, destination_lat, destination_lon, max_allowed_deviation_meters=300):
        self.dest_lat = float(destination_lat)
        self.dest_lon = float(destination_lon)
        self.max_deviation = max_allowed_deviation_meters  # Geofence boundary radius
        self.start_time = time.time()
        self.is_active = True

    def check_position(self, current_lat, current_lon, route_waypoints=None):
        """
        Verifies if current position is within allowed distance of target destination or waypoints.
        """
        if not self.is_active:
            return {"status": "inactive", "message": "Monitoring is off."}

        current_lat, current_lon = float(current_lat), float(current_lon)

        # Distance to destination
        dist_to_destination = haversine_distance(
            current_lat, current_lon, self.dest_lat, self.dest_lon
        )

        # Destination reached (within 50 meters)
        if dist_to_destination <= 50:
            self.is_active = False
            return {
                "status": "arrived",
                "message": "User safely reached destination!",
                "distance_to_dest_m": round(dist_to_destination, 2)
            }

        # Check deviation against route waypoints (if provided)
        if route_waypoints and len(route_waypoints) > 0:
            min_dist_to_route = min(
                haversine_distance(current_lat, current_lon, wp[0], wp[1])
                for wp in route_waypoints
            )
            if min_dist_to_route > self.max_deviation:
                return {
                    "status": "route_deviation_alert",
                    "message": f"🚨 Off-route deviation detected! ({round(min_dist_to_route)}m away from safe path)",
                    "distance_m": round(min_dist_to_route, 2)
                }

        return {
            "status": "safe",
            "message": "User is on safe route.",
            "distance_to_dest_m": round(dist_to_destination, 2)
        }

if __name__ == "__main__":
    # Quick Test: Destination is 500m away
    monitor = RouteMonitor(destination_lat=21.2380, destination_lon=81.6380, max_allowed_deviation_meters=200)
    
    # Test current location (within route)
    result = monitor.check_position(current_lat=21.2350, current_lon=81.6350)
    print("Check 1:", result)