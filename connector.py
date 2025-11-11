"""
Main Connector Service
Orchestrates data collection from Ruckus and writing to InfluxDB
"""
import logging
import time
from datetime import datetime
from typing import Dict, List, Any
from ruckus_client import RuckusClient
from influx_writer import InfluxWriter
from transformers import DataTransformer
from cause_code_generator import CauseCodeGenerator
from influxdb_client import Point

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WiFiConnector:
    """Main connector service"""
    
    def __init__(
        self,
        ruckus_client: RuckusClient,
        influx_writer: InfluxWriter,
        collection_interval: int = 60  # seconds
    ):
        self.ruckus = ruckus_client
        self.influx = influx_writer
        self.transformer = DataTransformer()
        self.cause_code_generator = CauseCodeGenerator()
        self.collection_interval = collection_interval
        self.running = False
    
    def collect_and_store(self):
        """Collect data from Ruckus and store in InfluxDB"""
        logger.info("Starting data collection cycle")
        timestamp = datetime.utcnow()
        
        try:
            # 1. Get zones
            logger.info("Fetching zones...")
            ruckus_zones = self.ruckus.get_zones()
            logger.info(f"Retrieved {len(ruckus_zones)} zones")
            
            # Transform zones
            frontend_zones = [self.transformer.transform_zone_to_frontend(z) for z in ruckus_zones]
            
            # 2. Get system inventory for additional metrics
            logger.info("Fetching system inventory...")
            system_inventory = self.ruckus.get_system_inventory()
            
            # 3. Get all APs
            logger.info("Fetching access points...")
            all_aps = self.ruckus.get_aps()
            logger.info(f"Retrieved {len(all_aps)} access points")
            
            # Group APs by zone
            aps_by_zone = {}
            for ap in all_aps:
                zone_id = ap.get("zoneId", "")
                if zone_id not in aps_by_zone:
                    aps_by_zone[zone_id] = []
                aps_by_zone[zone_id].append(ap)
            
            # 4. Get all clients
            logger.info("Fetching clients...")
            all_clients = self.ruckus.get_clients()
            logger.info(f"Retrieved {len(all_clients)} clients")
            
            # Transform clients
            frontend_clients = [self.transformer.transform_client_to_frontend(c) for c in all_clients]
            
            # 5. Calculate aggregated metrics
            self._calculate_zone_metrics(frontend_zones, aps_by_zone, all_clients)
            
            # 6. Create venue data
            venue_data = self.transformer.transform_venue_data(frontend_zones, system_inventory)
            
            # 7. Calculate OS distribution
            os_distribution = self.transformer.calculate_os_distribution(frontend_clients)
            
            # 8. Calculate host usage
            host_usage = self.transformer.calculate_host_usage(frontend_clients)
            
            # 9. Generate cause codes for disconnected APs
            disconnected_aps = []
            for ap in all_aps:
                # Check multiple possible status fields
                status = ap.get("status", "").lower()
                ap_connection_state = ap.get("apConnectionState", "").lower()
                connection_state = ap.get("connectionState", "").lower()
                
                # Consider AP offline if any of these indicate offline
                is_offline = (
                    status == "offline" or
                    ap_connection_state == "offline" or
                    connection_state == "offline" or
                    (status not in ["online", "connected"] and
                     ap_connection_state not in ["online", "connected"] and
                     connection_state not in ["online", "connected"])
                )
                if is_offline:
                    disconnected_aps.append(ap)
            
            ap_cause_codes = self.cause_code_generator.generate_cause_codes_for_aps(disconnected_aps)
            if ap_cause_codes:
                logger.info(f"Generated cause codes for {len(ap_cause_codes)} disconnected APs")
            
            # 10. Write to InfluxDB
            points = []
            
            # Write venue data
            points.extend(self._create_venue_points(venue_data, timestamp))
            
            # Write zone data
            points.extend(self._create_zone_points(frontend_zones, timestamp))
            
            # Write AP data
            points.extend(self._create_ap_points(all_aps, timestamp))
            
            # Write client data
            points.extend(self._create_client_points(all_clients, timestamp))
            
            # Write OS distribution
            points.extend(self._create_os_distribution_points(os_distribution, timestamp))
            
            # Write host usage
            points.extend(self._create_host_usage_points(host_usage, timestamp))
            
            # Write AP cause codes
            points.extend(self._create_ap_cause_code_points(ap_cause_codes, timestamp))
            
            # Write all points
            if points:
                self.influx.write_points(points)
                logger.info(f"Successfully wrote {len(points)} data points to InfluxDB")
            
            logger.info("Data collection cycle completed")
            
        except Exception as e:
            logger.error(f"Error in data collection cycle: {e}", exc_info=True)
    
    def _calculate_zone_metrics(
        self,
        zones: List[Dict[str, Any]],
        aps_by_zone: Dict[str, List[Dict[str, Any]]],
        clients: List[Dict[str, Any]]
    ):
        """Calculate zone-level metrics from AP and client data"""
        # Group clients by zone
        clients_by_zone = {}
        for client in clients:
            zone_id = client.get("zoneId", "")
            if zone_id not in clients_by_zone:
                clients_by_zone[zone_id] = []
            clients_by_zone[zone_id].append(client)
        
        for zone in zones:
            zone_id = zone.get("id", "")
            zone_aps = aps_by_zone.get(zone_id, [])
            zone_clients = clients_by_zone.get(zone_id, [])
            
            # Calculate average utilization from APs
            utilizations = []
            rx_desenses = []
            
            for ap in zone_aps:
                airtime_24g = ap.get("airtime24G", 0) or 0
                airtime_5g = ap.get("airtime5G", 0) or 0
                if airtime_24g or airtime_5g:
                    utilizations.append((airtime_24g + airtime_5g) / 2)
                
                rx_desense_24g = ap.get("rxDesense24G", 0) or 0
                rx_desense_5g = ap.get("rxDesense5G", 0) or 0
                if rx_desense_24g:
                    rx_desenses.append(rx_desense_24g)
                if rx_desense_5g:
                    rx_desenses.append(rx_desense_5g)
            
            zone["utilization"] = round(sum(utilizations) / len(utilizations), 1) if utilizations else 0
            zone["rxDesense"] = round(sum(rx_desenses) / len(rx_desenses), 1) if rx_desenses else 0
            
            # Calculate experience score (simplified - based on RSSI and SNR)
            if zone_clients:
                rssi_values = []
                for client in zone_clients:
                    rssi = client.get("rssi")
                    if rssi:
                        rssi_values.append(rssi)
                
                if rssi_values:
                    avg_rssi = sum(rssi_values) / len(rssi_values)
                    # Convert RSSI to experience score (0-100 scale)
                    # -50 to -70 is good, -70 to -85 is fair, below -85 is poor
                    if avg_rssi >= -50:
                        experience_score = 100
                    elif avg_rssi >= -70:
                        experience_score = 80 + ((avg_rssi + 70) / 20) * 20
                    elif avg_rssi >= -85:
                        experience_score = 60 + ((avg_rssi + 85) / 15) * 20
                    else:
                        experience_score = max(0, 60 + ((avg_rssi + 85) / 15) * 60)
                    
                    zone["experienceScore"] = round(experience_score, 1)
                    zone["netflixScore"] = round(experience_score * 0.95, 1)  # Slightly lower
    
    def _create_venue_points(self, venue_data: Dict[str, Any], timestamp: datetime) -> List[Point]:
        """Create InfluxDB points for venue data"""
        points = []
        
        point = Point("venue")
        point = point.time(timestamp)
        point = point.field("totalZones", venue_data.get("totalZones", 0))
        point = point.field("totalAPs", venue_data.get("totalAPs", 0))
        point = point.field("totalClients", venue_data.get("totalClients", 0))
        # Ensure float types for decimal fields
        point = point.field("avgExperienceScore", float(venue_data.get("avgExperienceScore", 0.0)))
        point = point.field("slaCompliance", float(venue_data.get("slaCompliance", 0.0)))
        points.append(point)
        
        return points
    
    def _create_zone_points(self, zones: List[Dict[str, Any]], timestamp: datetime) -> List[Point]:
        """Create InfluxDB points for zone data"""
        points = []
        
        for zone in zones:
            point = Point("zone")
            point = point.time(timestamp)
            point = point.tag("zoneId", zone.get("id", ""))
            point = point.tag("zoneName", zone.get("name", ""))
            point = point.field("totalAPs", zone.get("totalAPs", 0))
            point = point.field("connectedAPs", zone.get("connectedAPs", 0))
            point = point.field("disconnectedAPs", zone.get("disconnectedAPs", 0))
            point = point.field("clients", zone.get("clients", 0))
            # Ensure float types for decimal fields
            point = point.field("apAvailability", float(zone.get("apAvailability", 0.0)))
            point = point.field("clientsPerAP", float(zone.get("clientsPerAP", 0.0)))
            point = point.field("experienceScore", float(zone.get("experienceScore", 0.0)))
            point = point.field("utilization", float(zone.get("utilization", 0.0)))
            point = point.field("rxDesense", float(zone.get("rxDesense", 0.0)))
            point = point.field("netflixScore", float(zone.get("netflixScore", 0.0)))
            points.append(point)
        
        return points
    
    def _create_ap_points(self, aps: List[Dict[str, Any]], timestamp: datetime) -> List[Point]:
        """Create InfluxDB points for AP data"""
        points = []
        
        for ap in aps:
            point = Point("access_point")
            point = point.time(timestamp)
            point = point.tag("apMac", ap.get("apMac", ""))
            point = point.tag("apName", ap.get("deviceName", ""))
            point = point.tag("zoneId", ap.get("zoneId", ""))
            point = point.tag("zoneName", ap.get("zoneName", ""))
            point = point.tag("model", ap.get("model", ""))
            point = point.tag("status", ap.get("status", ""))
            
            point = point.field("clientCount", ap.get("numClients", 0) or 0)
            point = point.field("clientCount24G", ap.get("numClients24G", 0) or 0)
            point = point.field("clientCount5G", ap.get("numClients5G", 0) or 0)
            # Ensure float types for decimal fields
            point = point.field("airtime24G", float(ap.get("airtime24G", 0) or 0))
            point = point.field("airtime5G", float(ap.get("airtime5G", 0) or 0))
            point = point.field("noise24G", float(ap.get("noise24G", 0) or 0))
            point = point.field("noise5G", float(ap.get("noise5G", 0) or 0))
            point = point.field("channel24G", ap.get("channel24gValue", 0) or 0)
            point = point.field("channel5G", ap.get("channel50gValue", 0) or 0)
            point = point.field("eirp24G", ap.get("eirp24G", 0) or 0)
            point = point.field("eirp5G", ap.get("eirp50G", 0) or 0)
            
            points.append(point)
        
        return points
    
    def _create_client_points(self, clients: List[Dict[str, Any]], timestamp: datetime) -> List[Point]:
        """Create InfluxDB points for client data"""
        points = []
        
        for client in clients:
            point = Point("client")
            point = point.time(timestamp)
            point = point.tag("clientMac", client.get("clientMac", ""))
            point = point.tag("zoneId", client.get("zoneId", ""))
            point = point.tag("apMac", client.get("apMac", ""))
            point = point.tag("apName", client.get("apName", ""))
            point = point.tag("ssid", client.get("ssid", ""))
            point = point.tag("osType", client.get("osType", ""))
            
            point = point.field("txBytes", client.get("txBytes", 0) or 0)
            point = point.field("rxBytes", client.get("rxBytes", 0) or 0)
            point = point.field("txRxBytes", client.get("txRxBytes", 0) or 0)
            # Ensure float types for decimal fields (rssi/snr can be negative decimals)
            point = point.field("rssi", float(client.get("rssi", 0) or 0))
            point = point.field("snr", float(client.get("snr", 0) or 0))
            point = point.field("uplinkRate", float(client.get("uplinkRate", 0) or 0))
            point = point.field("downlinkRate", float(client.get("downlinkRate", 0) or 0))
            
            points.append(point)
        
        return points
    
    def _create_os_distribution_points(
        self,
        os_distribution: List[Dict[str, Any]],
        timestamp: datetime
    ) -> List[Point]:
        """Create InfluxDB points for OS distribution"""
        points = []
        
        for dist in os_distribution:
            point = Point("os_distribution")
            point = point.time(timestamp)
            point = point.tag("os", dist.get("os", ""))
            # Ensure float type for percentage
            point = point.field("percentage", float(dist.get("percentage", 0.0)))
            points.append(point)
        
        return points
    
    def _create_host_usage_points(
        self,
        host_usage: List[Dict[str, Any]],
        timestamp: datetime
    ) -> List[Point]:
        """Create InfluxDB points for host usage"""
        points = []
        
        for host in host_usage:
            point = Point("host_usage")
            point = point.time(timestamp)
            point = point.tag("hostname", host.get("hostname", ""))
            # Ensure float type for dataUsage
            point = point.field("dataUsage", float(host.get("dataUsage", 0.0)))
            points.append(point)
        
        return points
    
    def _create_ap_cause_code_points(
        self,
        cause_codes: List[Dict[str, Any]],
        timestamp: datetime
    ) -> List[Point]:
        """Create InfluxDB points for AP disconnect cause codes"""
        points = []
        
        for cause_data in cause_codes:
            point = Point("ap_disconnect_cause")
            point = point.time(timestamp)
            point = point.tag("apMac", cause_data.get("apMac", ""))
            point = point.tag("apName", cause_data.get("apName", ""))
            point = point.tag("zoneId", cause_data.get("zoneId", ""))
            point = point.tag("zoneName", cause_data.get("zoneName", ""))
            point = point.tag("model", cause_data.get("model", ""))
            point = point.tag("causeCode", str(cause_data.get("causeCode", 0)))
            
            point = point.field("causeCode", cause_data.get("causeCode", 0))
            point = point.field("causeDescription", cause_data.get("causeDescription", ""))
            # Ensure float type for impactScore
            point = point.field("impactScore", float(cause_data.get("impactScore", 0.0)))
            
            points.append(point)
        
        return points
    
    def run_continuous(self):
        """Run connector continuously"""
        self.running = True
        logger.info(f"Starting connector service (interval: {self.collection_interval}s)")
        
        while self.running:
            try:
                self.collect_and_store()
            except Exception as e:
                logger.error(f"Error in continuous run: {e}", exc_info=True)
            
            if self.running:
                logger.info(f"Waiting {self.collection_interval} seconds until next collection...")
                time.sleep(self.collection_interval)
    
    def stop(self):
        """Stop the connector service"""
        logger.info("Stopping connector service...")
        self.running = False
        self.influx.close()


def main():
    """Main entry point"""
    # Configuration
    ruckus_client = RuckusClient(
        base_url="https://3.12.57.221:8443",
        username="apireadonly",
        password="SBAedge2112#",
        api_version="v9_1",
        timeout=30,
        verify_ssl=False
    )
    
    influx_writer = InfluxWriter(
        url="http://20.64.233.185:8086",
        org="wifi-org",
        bucket="wifi-streaming",
        token="vmEv3xPIBXM0iiW6rBQ8KKPZB7hdbjqbPJVtN0mrO0Cn96RhTGWP647J9K-lo-6mmB0_sQRvHLDdFgHrGb8GRQ=="
    )
    
    # Test connections
    logger.info("Testing Ruckus connection...")
    if not ruckus_client.test_connection():
        logger.error("Failed to connect to Ruckus controller")
        return
    
    logger.info("Ruckus connection successful")
    
    # Create connector
    connector = WiFiConnector(
        ruckus_client=ruckus_client,
        influx_writer=influx_writer,
        collection_interval=60  # Collect every 60 seconds
    )
    
    # Run once or continuously
    try:
        # Run once for testing
        connector.collect_and_store()
        
        # Uncomment to run continuously:
        # connector.run_continuous()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        connector.stop()


if __name__ == "__main__":
    main()

