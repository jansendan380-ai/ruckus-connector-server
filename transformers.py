"""
Data Transformers
Transform Ruckus API data to frontend API format
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DataTransformer:
    """Transform Ruckus data to frontend format"""
    
    @staticmethod
    def transform_zone_to_frontend(ruckus_zone: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Ruckus zone data to frontend format"""
        total_aps = ruckus_zone.get("apCountOnline", 0) + ruckus_zone.get("apCountOffline", 0)
        connected_aps = ruckus_zone.get("apCountOnline", 0)
        disconnected_aps = ruckus_zone.get("apCountOffline", 0)
        clients = ruckus_zone.get("clientCount", 0)
        
        # Calculate availability percentage
        ap_availability = (connected_aps / total_aps * 100) if total_aps > 0 else 0
        
        # Calculate clients per AP
        clients_per_ap = (clients / connected_aps) if connected_aps > 0 else 0
        
        return {
            "id": ruckus_zone.get("id", ""),
            "name": ruckus_zone.get("zoneName", ""),
            "totalAPs": total_aps,
            "connectedAPs": connected_aps,
            "disconnectedAPs": disconnected_aps,
            "clients": clients,
            "apAvailability": round(ap_availability, 1),
            "clientsPerAP": round(clients_per_ap, 2),
            "experienceScore": 0,  # Will be calculated from time-series data
            "utilization": 0,  # Will be calculated from AP data
            "rxDesense": 0,  # Will be calculated from AP data
            "netflixScore": 0  # Will be calculated from time-series data
        }
    
    @staticmethod
    def transform_venue_data(
        zones: List[Dict[str, Any]],
        system_inventory: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Transform to venue data format"""
        # Aggregate zone data
        total_zones = len(zones)
        total_aps = sum(z.get("totalAPs", 0) for z in zones)
        total_clients = sum(z.get("clients", 0) for z in zones)
        
        # Calculate average experience score
        experience_scores = [z.get("experienceScore", 0) for z in zones if z.get("experienceScore", 0) > 0]
        avg_experience_score = sum(experience_scores) / len(experience_scores) if experience_scores else 0
        
        # Calculate SLA compliance (percentage of zones with >95% AP availability)
        compliant_zones = sum(1 for z in zones if z.get("apAvailability", 0) >= 95)
        sla_compliance = (compliant_zones / total_zones * 100) if total_zones > 0 else 0
        
        return {
            "name": "Main Venue",
            "totalZones": total_zones,
            "totalAPs": total_aps,
            "totalClients": total_clients,
            "avgExperienceScore": round(avg_experience_score, 1),
            "slaCompliance": round(sla_compliance, 1),
            "zones": zones
        }
    
    @staticmethod
    def transform_ap_to_frontend(ruckus_ap: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Ruckus AP data to frontend format"""
        status = ruckus_ap.get("status", "offline").lower()
        if status == "online":
            status = "online"
        else:
            status = "offline"
        
        # Extract channel information
        channel_24g = ruckus_ap.get("channel24G", "")
        channel_5g = ruckus_ap.get("channel5G", "")
        
        # Parse channel values
        channel_24g_value = ruckus_ap.get("channel24gValue", 0)
        channel_5g_value = ruckus_ap.get("channel50gValue", 0)
        
        # Calculate utilization (average of airtime utilization)
        airtime_24g = ruckus_ap.get("airtime24G", 0) or 0
        airtime_5g = ruckus_ap.get("airtime5G", 0) or 0
        channel_utilization = (airtime_24g + airtime_5g) / 2 if (airtime_24g or airtime_5g) else 0
        
        # Build radios array
        radios = []
        
        if channel_24g_value:
            radios.append({
                "band": "2.4GHz",
                "channel": channel_24g_value,
                "txPower": ruckus_ap.get("eirp24G", 0) or 0,
                "noiseFloor": ruckus_ap.get("noise24G", 0) or 0,
                "clientCount": ruckus_ap.get("numClients24G", 0) or 0
            })
        
        if channel_5g_value:
            radios.append({
                "band": "5GHz",
                "channel": channel_5g_value,
                "txPower": ruckus_ap.get("eirp50G", 0) or 0,
                "noiseFloor": ruckus_ap.get("noise5G", 0) or 0,
                "clientCount": ruckus_ap.get("numClients5G", 0) or 0
            })
        
        return {
            "mac": ruckus_ap.get("apMac", ""),
            "name": ruckus_ap.get("deviceName", ""),
            "model": ruckus_ap.get("model", ""),
            "status": status,
            "ip": ruckus_ap.get("ip", ""),
            "zoneId": ruckus_ap.get("zoneId", ""),
            "zoneName": ruckus_ap.get("zoneName", ""),
            "firmwareVersion": ruckus_ap.get("firmwareVersion", ""),
            "serialNumber": ruckus_ap.get("serial", ""),
            "clientCount": ruckus_ap.get("numClients", 0) or 0,
            "channelUtilization": round(channel_utilization, 1),
            "airtimeUtilization": round(max(airtime_24g, airtime_5g), 1),
            "cpuUtilization": 0,  # Not available in Ruckus API
            "memoryUtilization": 0,  # Not available in Ruckus API
            "radios": radios
        }
    
    @staticmethod
    def transform_client_to_frontend(ruckus_client: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Ruckus client data to frontend format"""
        # Calculate data usage in MB
        tx_bytes = ruckus_client.get("txBytes", 0) or 0
        rx_bytes = ruckus_client.get("rxBytes", 0) or 0
        total_bytes = tx_bytes + rx_bytes
        data_usage_mb = total_bytes / (1024 * 1024)  # Convert to MB
        
        # Map OS type
        os_type = ruckus_client.get("osType", "Unknown")
        os_vendor = ruckus_client.get("osVendorType", "")
        
        # Normalize OS
        if "iOS" in os_type or os_vendor == "iOS":
            os = "iOS"
        elif "Android" in os_type or os_vendor == "Android":
            os = "Android"
        elif "Windows" in os_type:
            os = "Windows"
        elif "Mac" in os_type or "macOS" in os_type:
            os = "macOS"
        elif "Chrome" in os_type:
            os = "Chrome OS/Chromebook"
        else:
            os = "Unknown"
        
        # Map device type
        device_type_raw = ruckus_client.get("deviceType", "").lower()
        if "phone" in device_type_raw or "smartphone" in device_type_raw:
            device_type = "phone"
        elif "laptop" in device_type_raw or "notebook" in device_type_raw:
            device_type = "laptop"
        elif "tablet" in device_type_raw:
            device_type = "tablet"
        else:
            device_type = "other"
        
        return {
            "hostname": ruckus_client.get("hostname", ruckus_client.get("clientMac", "")),
            "modelName": ruckus_client.get("modelName", "Unknown"),
            "ipAddress": f"{ruckus_client.get('ipAddress', '')} /{ruckus_client.get('ipv6Address', '::')}",
            "macAddress": ruckus_client.get("clientMac", ""),
            "wlan": ruckus_client.get("ssid", ""),
            "apName": ruckus_client.get("apName", ""),
            "apMac": ruckus_client.get("apMac", ""),
            "dataUsage": round(data_usage_mb, 1),
            "os": os,
            "deviceType": device_type
        }
    
    @staticmethod
    def calculate_os_distribution(clients: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate OS distribution from clients"""
        os_counts = {}
        total = len(clients)
        
        for client in clients:
            os = client.get("os", "Unknown")
            os_counts[os] = os_counts.get(os, 0) + 1
        
        # Color mapping
        colors = {
            "iOS": "#8B5CF6",
            "Android": "#3B82F6",
            "Unknown": "#1E3A5F",
            "Chrome OS/Chromebook": "#10B981",
            "macOS": "#D1D5DB",
            "Windows": "#6B7280"
        }
        
        distribution = []
        for os, count in sorted(os_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total * 100) if total > 0 else 0
            distribution.append({
                "os": os,
                "percentage": round(percentage, 2),
                "color": colors.get(os, "#6B7280")
            })
        
        return distribution
    
    @staticmethod
    def calculate_host_usage(clients: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
        """Calculate top host usage from clients"""
        # Group by hostname and sum data usage
        host_usage = {}
        
        for client in clients:
            hostname = client.get("hostname", "")
            data_usage = client.get("dataUsage", 0)
            
            if hostname in host_usage:
                host_usage[hostname] += data_usage
            else:
                host_usage[hostname] = data_usage
        
        # Sort and limit
        sorted_hosts = sorted(host_usage.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        return [
            {
                "hostname": hostname,
                "dataUsage": round(usage, 1)
            }
            for hostname, usage in sorted_hosts
        ]

