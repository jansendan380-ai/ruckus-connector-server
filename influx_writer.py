"""
InfluxDB Writer
Writes data to InfluxDB using the InfluxDB Python client
"""
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class InfluxWriter:
    """Writer for sending data to InfluxDB"""
    
    def __init__(
        self,
        url: str,
        org: str,
        bucket: str,
        token: str
    ):
        self.url = url
        self.org = org
        self.bucket = bucket
        self.token = token
        self.client = InfluxDBClient(url=url, token=token, org=org)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        
    def write_points(self, points: List[Point]) -> bool:
        """Write multiple points to InfluxDB"""
        try:
            self.write_api.write(bucket=self.bucket, org=self.org, record=points)
            logger.info(f"Successfully wrote {len(points)} points to InfluxDB")
            return True
        except Exception as e:
            logger.error(f"Error writing points to InfluxDB: {e}")
            return False
    
    def write_point(
        self,
        measurement: str,
        tags: Dict[str, str],
        fields: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ) -> bool:
        """Write a single point to InfluxDB"""
        point = Point(measurement)
        
        # Add tags
        for key, value in tags.items():
            if value is not None:
                point = point.tag(key, str(value))
        
        # Add fields
        for key, value in fields.items():
            if value is not None:
                if isinstance(value, (int, float)):
                    point = point.field(key, value)
                elif isinstance(value, bool):
                    point = point.field(key, value)
                elif isinstance(value, str):
                    # Try to convert string numbers
                    try:
                        if '.' in value:
                            point = point.field(key, float(value))
                        else:
                            point = point.field(key, int(value))
                    except ValueError:
                        point = point.field(key, value)
        
        # Set timestamp
        if timestamp:
            point = point.time(timestamp)
        
        return self.write_points([point])
    
    def close(self):
        """Close the InfluxDB client"""
        self.client.close()

