"""
Cause Code Generator
Generates realistic 802.11 disconnect cause codes for disconnected APs
"""
import random
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class CauseCodeGenerator:
    """Generates realistic disconnect cause codes for APs"""
    
    # Common 802.11 disconnect cause codes with realistic weights
    # Higher weight = more likely to occur
    CAUSE_CODES = [
        {
            "code": 1,
            "description": "Unspecified reason",
            "weight": 15,
            "impactScore": 14.3
        },
        {
            "code": 3,
            "description": "Deauthenticated - leaving or left BSS",
            "weight": 20,
            "impactScore": 17.4
        },
        {
            "code": 4,
            "description": "Disassociated due to inactivity",
            "weight": 18,
            "impactScore": 13.0
        },
        {
            "code": 5,
            "description": "Disassociated - AP unable to handle all STAs",
            "weight": 25,
            "impactScore": 21.5
        },
        {
            "code": 6,
            "description": "Class 2 frame received from nonauthenticated STA",
            "weight": 5,
            "impactScore": 8.5
        },
        {
            "code": 7,
            "description": "Class 3 frame received from nonassociated STA",
            "weight": 5,
            "impactScore": 8.5
        },
        {
            "code": 8,
            "description": "Disassociated - STA has left BSS",
            "weight": 22,
            "impactScore": 17.8
        },
        {
            "code": 15,
            "description": "4-way handshake timeout",
            "weight": 12,
            "impactScore": 15.2
        },
        {
            "code": 25,
            "description": "Disassociated due to insufficient QoS",
            "weight": 30,
            "impactScore": 94.6
        },
        {
            "code": 31,
            "description": "Disassociated - AP unable to handle all associated STAs",
            "weight": 20,
            "impactScore": 19.5
        },
        {
            "code": 33,
            "description": "Disassociated - STA requesting association is not authenticated",
            "weight": 8,
            "impactScore": 10.2
        },
        {
            "code": 45,
            "description": "Peer unreachable",
            "weight": 28,
            "impactScore": 28.3
        },
        {
            "code": 47,
            "description": "Requested from peer",
            "weight": 25,
            "impactScore": 23.2
        },
        {
            "code": 200,
            "description": "AP lost heartbeat with controller",
            "weight": 35,
            "impactScore": 45.0
        },
        {
            "code": 201,
            "description": "AP firmware update in progress",
            "weight": 10,
            "impactScore": 12.0
        },
        {
            "code": 202,
            "description": "AP power failure or reboot",
            "weight": 15,
            "impactScore": 25.0
        },
        {
            "code": 203,
            "description": "Network connectivity issue",
            "weight": 25,
            "impactScore": 30.0
        },
        {
            "code": 204,
            "description": "AP configuration error",
            "weight": 8,
            "impactScore": 15.0
        }
    ]
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize the cause code generator"""
        if seed is not None:
            random.seed(seed)
        self._build_weighted_list()
    
    def _build_weighted_list(self):
        """Build a weighted list for random selection"""
        self.weighted_codes = []
        for cause in self.CAUSE_CODES:
            # Add each code multiple times based on its weight
            for _ in range(cause["weight"]):
                self.weighted_codes.append(cause)
    
    def generate_cause_code(self, ap_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate a realistic cause code for a disconnected AP
        
        Args:
            ap_data: Optional AP data to influence cause code selection
            
        Returns:
            Dictionary with code, description, and impactScore
        """
        # Select a random cause code based on weights
        selected = random.choice(self.weighted_codes)
        
        # Create a copy to avoid modifying the original
        cause_code = {
            "code": selected["code"],
            "description": selected["description"],
            "impactScore": selected["impactScore"]
        }
        
        # Optionally adjust based on AP characteristics
        if ap_data:
            # If AP has been offline for a long time, more likely to be network/power issue
            # This is a simplified heuristic
            model = ap_data.get("model") or ""
            model = str(model).upper() if model else ""
            if model and ("T" in model or "H" in model):  # Outdoor/Industrial models
                # More likely to have power/network issues
                if random.random() < 0.3:
                    power_codes = [c for c in self.CAUSE_CODES if "power" in c["description"].lower() or 
                                 "network" in c["description"].lower() or 
                                 "heartbeat" in c["description"].lower()]
                    if power_codes:
                        selected = random.choice(power_codes)
                        cause_code = {
                            "code": selected["code"],
                            "description": selected["description"],
                            "impactScore": selected["impactScore"]
                        }
        
        return cause_code
    
    def generate_cause_codes_for_aps(
        self, 
        disconnected_aps: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate cause codes for a list of disconnected APs
        
        Args:
            disconnected_aps: List of disconnected AP dictionaries
            
        Returns:
            List of cause code dictionaries with AP information
        """
        cause_codes = []
        
        for ap in disconnected_aps:
            # Handle different field name variations, ensuring None values become empty strings
            ap_mac = (ap.get("apMac") or 
                     ap.get("mac") or 
                     ap.get("apMacAddress") or
                     ap.get("macAddress") or "")
            ap_mac = str(ap_mac) if ap_mac else ""
            
            ap_name = (ap.get("deviceName") or 
                      ap.get("name") or
                      ap.get("apName") or "")
            ap_name = str(ap_name) if ap_name else ""
            
            zone_id = ap.get("zoneId") or ""
            zone_id = str(zone_id) if zone_id else ""
            
            zone_name = ap.get("zoneName") or ""
            zone_name = str(zone_name) if zone_name else ""
            
            model = ap.get("model") or ""
            model = str(model) if model else ""
            
            # Generate cause code
            cause_code = self.generate_cause_code(ap)
            
            # Combine AP info with cause code
            cause_codes.append({
                "apMac": ap_mac,
                "apName": ap_name,
                "zoneId": zone_id,
                "zoneName": zone_name,
                "model": model,
                "causeCode": cause_code["code"],
                "causeDescription": cause_code["description"],
                "impactScore": cause_code["impactScore"]
            })
        
        return cause_codes
    
    def get_all_cause_codes(self) -> List[Dict[str, Any]]:
        """Get all available cause codes"""
        return [
            {
                "code": c["code"],
                "description": c["description"],
                "impactScore": c["impactScore"]
            }
            for c in self.CAUSE_CODES
        ]

