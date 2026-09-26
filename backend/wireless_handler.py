import subprocess
import re

def scan_nearby_wifi():
    """Scans nearby Wi-Fi networks using Windows netsh command."""
    try:
        # Run netsh wlan show networks mode=bssid
        result = subprocess.run(
            ["netsh", "wlan", "show", "networks", "mode=bssid"],
            capture_output=True,
            text=True,
            timeout=5
        )
        output = result.stdout

        networks = []
        current_ssid = "Unknown"
        
        for line in output.split('\n'):
            line = line.strip()
            if line.startswith("SSID"):
                parts = line.split(":", 1)
                if len(parts) > 1:
                    current_ssid = parts[1].strip() or "Hidden Network"
            elif line.startswith("BSSID"):
                parts = line.split(":", 1)
                if len(parts) > 1:
                    bssid = parts[1].strip()
                    networks.append(f"• SSID: {current_ssid} | BSSID: {bssid}")

        return networks[:10]  # Return top 10 detected
    except Exception as e:
        return [f"Wi-Fi scan error: {str(e)}"]


def scan_nearby_bluetooth():
    """Scans nearby Bluetooth devices via Windows PowerShell script."""
    try:
        ps_script = """
        Get-PnpDevice -Class Bluetooth | Where-Object {$_.Status -eq "OK"} | Select-Object -Property FriendlyName, InstanceId | Format-Table -HideTableHeaders
        """
        result = subprocess.run(
            ["powershell", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=5
        )
        devices = [line.strip() for line in result.stdout.split('\n') if line.strip()]
        return devices[:5] if devices else ["No active Bluetooth devices detected"]
    except Exception as e:
        return [f"Bluetooth scan error: {str(e)}"]


def get_wireless_evidence_summary():
    """Compiles a complete report of nearby Wi-Fi and Bluetooth signals."""
    wifi_list = scan_nearby_wifi()
    bt_list = scan_nearby_bluetooth()

    report = "📶 **NEARBY WI-FI NETWORKS (DIGITAL EVIDENCE):**\n"
    if wifi_list:
        report += "\n".join(wifi_list) + "\n\n"
    else:
        report += "No Wi-Fi signals detected.\n\n"

    report += "📡 **NEARBY BLUETOOTH DEVICES:**\n"
    if bt_list:
        report += "\n".join([f"• {dev}" for dev in bt_list])
    else:
        report += "No Bluetooth signals detected."

    return report