import asyncio
from winrt.windows.devices.geolocation import Geolocator, GeolocationAccessStatus

def get_winrt_location():
    """Queries Windows Native Geolocation directly using C++ WinRT bindings."""
    async def _async_get():
        access = await Geolocator.request_access_async()
        if access != GeolocationAccessStatus.ALLOWED:
            print("⚠️ Windows Location Permission denied in Settings.")
            return None
        
        geolocator = Geolocator()
        geolocator.desired_accuracy_in_meters = 10
        pos = await geolocator.get_geoposition_async()
        coord = pos.coordinate.point.position
        
        return {
            "latitude": coord.latitude,
            "longitude": coord.longitude,
            "accuracy": pos.coordinate.accuracy,
            "source": "Windows Hardware/Wi-Fi Geolocation",
            "maps_url": f"https://www.google.com/maps?q={coord.latitude},{coord.longitude}"
        }

    try:
        return asyncio.run(_async_get())
    except Exception as e:
        print(f"⚠️ WinRT Native Location error: {e}")
        return None

def get_current_location():
    """Fetches device location via native Windows service."""
    native_loc = get_winrt_location()
    if native_loc:
        return native_loc
    
    return {
        "latitude": 0.0,
        "longitude": 0.0,
        "source": "Location Disabled in Windows Settings",
        "maps_url": "N/A"
    }