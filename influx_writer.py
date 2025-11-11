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
        # Ensure connectivity and bucket
        self._check_health()
        self._ensure_bucket_exists()

    def _check_health(self) -> None:
        """Check InfluxDB health and log status"""
        try:
            health = self.client.health()
            logger.info(f"InfluxDB health: {health.status} - {health.message}")
        except Exception as e:
            logger.warning(f"InfluxDB health check failed: {e}")

    def _ensure_bucket_exists(self) -> None:
        """Ensure target bucket exists; create if missing"""
        try:
            buckets_api = self.client.buckets_api()
            orgs_api = self.client.organizations_api()
            # Resolve org id
            orgs = orgs_api.find_organizations()
            org_list = orgs if isinstance(orgs, list) else getattr(orgs, "orgs", [])
            org_id = None
            for o in org_list:
                if getattr(o, "name", None) == self.org:
                    org_id = getattr(o, "id", None)
                    break
            if not org_id:
                logger.warning(f"Organization '{self.org}' not found; bucket creation skipped")
                return
            # Check buckets
            found = False
            buckets = buckets_api.find_buckets()
            bucket_list = buckets if isinstance(buckets, list) else getattr(buckets, "buckets", [])
            for b in bucket_list:
                if getattr(b, "name", None) == self.bucket:
                    found = True
                    break
            if not found:
                from influxdb_client.domain.bucket import Bucket
                from influxdb_client.domain.bucket_retention_rules import BucketRetentionRules
                retention_rules = BucketRetentionRules(every_seconds=0)
                bucket_obj = Bucket(name=self.bucket, retention_rules=[retention_rules], org_id=org_id)
                buckets_api.create_bucket(bucket=bucket_obj)
                logger.info(f"Created InfluxDB bucket: {self.bucket}")
        except Exception as e:
            logger.warning(f"Bucket ensure failed: {e}")
        
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

