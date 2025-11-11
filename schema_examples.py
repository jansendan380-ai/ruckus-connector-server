"""
Example Python code for querying the InfluxDB schema
Useful for FastAPI backend development
"""
from influxdb_client import InfluxDBClient
from typing import List, Dict, Any, Optional


class InfluxDBQueries:
    """Example queries for the WiFi monitoring database schema"""

    def __init__(
        self,
        url: str,
        token: str,
        org: str,
        bucket: str
    ):
        self.client = InfluxDBClient(url=url, token=token, org=org)
        self.query_api = self.client.query_api()
        self.bucket = bucket

    def get_venue_data(self) -> Optional[Dict[str, Any]]:
        """Get latest venue data"""
        query = f'''
        from(bucket: "{self.bucket}")
          |> range(start: -1h)
          |> filter(fn: (r) => r["_measurement"] == "venue")
          |> last()
        '''
        result = self.query_api.query(query=query)

        if not result:
            return None

        venue_data = {}
        for table in result:
            for record in table.records:
                venue_data[record.get_field()] = record.get_value()

        return venue_data

    def get_zones(self) -> List[Dict[str, Any]]:
        """Get all zones"""
        query = f'''
        from(bucket: "{self.bucket}")
          |> range(start: -1h)
          |> filter(fn: (r) => r["_measurement"] == "zone")
          |> last()
        '''
        result = self.query_api.query(query=query)

        zones = {}
        for table in result:
            for record in table.records:
                zone_id = record.values.get("zoneId")
                if zone_id not in zones:
                    zones[zone_id] = {
                        "id": zone_id,
                        "name": record.values.get("zoneName", ""),
                    }
                zones[zone_id][record.get_field()] = record.get_value()

        return list(zones.values())

    def get_zone(self, zone_id: str) -> Optional[Dict[str, Any]]:
        """Get specific zone by ID"""
        query = f'''
        from(bucket: "{self.bucket}")
          |> range(start: -1h)
          |> filter(fn: (r) => r["_measurement"] == "zone")
          |> filter(fn: (r) => r["zoneId"] == "{zone_id}")
          |> last()
        '''
        result = self.query_api.query(query=query)

        zone = {}
        for table in result:
            for record in table.records:
                if not zone:
                    zone = {
                        "id": record.values.get("zoneId"),
                        "name": record.values.get("zoneName", ""),
                    }
                zone[record.get_field()] = record.get_value()
        
        return zone if zone else None

    def get_aps_by_zone(self, zone_id: str) -> List[Dict[str, Any]]:
        """Get all APs for a specific zone"""
        query = f'''
        from(bucket: "{self.bucket}")
          |> range(start: -1h)
          |> filter(fn: (r) => r["_measurement"] == "access_point")
          |> filter(fn: (r) => r["zoneId"] == "{zone_id}")
          |> last()
        '''
        result = self.query_api.query(query=query)

        aps = {}
        for table in result:
            for record in table.records:
                ap_mac = record.values.get("apMac")
                if ap_mac not in aps:
                    aps[ap_mac] = {
                        "mac": ap_mac,
                        "name": record.values.get("apName", ""),
                        "model": record.values.get("model", ""),
                        "status": record.values.get("status", ""),
                        "zoneId": record.values.get("zoneId", ""),
                        "zoneName": record.values.get("zoneName", ""),
                    }
                aps[ap_mac][record.get_field()] = record.get_value()

        return list(aps.values())

    def get_clients(
        self,
        zone_id: Optional[str] = None,
        ap_mac: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get clients, optionally filtered by zone or AP"""
        filters = ['r["_measurement"] == "client"']

        if zone_id:
            filters.append(f'r["zoneId"] == "{zone_id}"')
        if ap_mac:
            filters.append(f'r["apMac"] == "{ap_mac}"')

        filter_str = " and ".join(filters)

        query = f'''
        from(bucket: "{self.bucket}")
          |> range(start: -1h)
          |> filter(fn: (r) => {filter_str})
          |> last()
        '''
        result = self.query_api.query(query=query)

        clients = {}
        for table in result:
            for record in table.records:
                client_mac = record.values.get("clientMac")
                if client_mac not in clients:
                    clients[client_mac] = {
                        "macAddress": client_mac,
                        "zoneId": record.values.get("zoneId", ""),
                        "apMac": record.values.get("apMac", ""),
                        "apName": record.values.get("apName", ""),
                        "ssid": record.values.get("ssid", ""),
                        "osType": record.values.get("osType", ""),
                    }
                clients[client_mac][record.get_field()] = record.get_value()

        return list(clients.values())

    def get_os_distribution(self) -> List[Dict[str, Any]]:
        """Get OS distribution"""
        query = f'''
        from(bucket: "{self.bucket}")
          |> range(start: -1h)
          |> filter(fn: (r) => r["_measurement"] == "os_distribution")
          |> last()
        '''
        result = self.query_api.query(query=query)

        distribution = []
        for table in result:
            for record in table.records:
                distribution.append({
                    "os": record.values.get("os", ""),
                    "percentage": record.get_value()
                })

        return sorted(
            distribution, key=lambda x: x["percentage"], reverse=True
        )

    def get_host_usage(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top host usage"""
        query = f'''
        from(bucket: "{self.bucket}")
          |> range(start: -1h)
          |> filter(fn: (r) => r["_measurement"] == "host_usage")
          |> filter(fn: (r) => r["_field"] == "dataUsage")
          |> last()
          |> sort(columns: ["_value"], desc: true)
          |> limit(n: {limit})
        '''
        result = self.query_api.query(query=query)

        hosts = []
        for table in result:
            for record in table.records:
                hosts.append({
                    "hostname": record.values.get("hostname", ""),
                    "dataUsage": record.get_value()
                })
        
        return hosts

    def get_time_series(
        self,
        measurement: str,
        field: str,
        zone_id: Optional[str] = None,
        hours: int = 24,
        interval_minutes: int = 60
    ) -> List[Dict[str, Any]]:
        """Get time-series data"""
        filters = [f'r["_measurement"] == "{measurement}"']
        filters.append(f'r["_field"] == "{field}"')

        if zone_id:
            filters.append(f'r["zoneId"] == "{zone_id}"')

        filter_str = " and ".join(filters)
        interval = f"{interval_minutes}m"

        query = f'''
        from(bucket: "{self.bucket}")
          |> range(start: -{hours}h)
          |> filter(fn: (r) => {filter_str})
          |> aggregateWindow(every: {interval}, fn: mean, createEmpty: false)
        '''
        result = self.query_api.query(query=query)

        time_series = []
        for table in result:
            for record in table.records:
                time_series.append({
                    "timestamp": record.get_time().isoformat(),
                    "value": record.get_value(),
                    "zone": record.values.get("zoneName", "")
                })
        
        return sorted(time_series, key=lambda x: x["timestamp"])

    def close(self):
        """Close the InfluxDB client"""
        self.client.close()


# Example usage
if __name__ == "__main__":
    # Initialize
    token = (
        "vmEv3xPIBXM0iiW6rBQ8KKPZB7hdbjqbPJVtN0mrO0Cn96RhTGWP647J9K-"
        "lo-6mmB0_sQRvHLDdFgHrGb8GRQ=="
    )
    queries = InfluxDBQueries(
        url="http://20.64.233.185:8086",
        token=token,
        org="wifi-org",
        bucket="wifi-streaming"
    )

    # Example queries
    print("Venue Data:")
    print(queries.get_venue_data())

    print("\nZones:")
    print(queries.get_zones())

    print("\nOS Distribution:")
    print(queries.get_os_distribution())

    print("\nTop Host Usage:")
    print(queries.get_host_usage(limit=10))

    queries.close()
