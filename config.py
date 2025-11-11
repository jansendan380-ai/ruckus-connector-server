"""
Configuration file for WiFi Connector
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class RuckusConfig:
    """Ruckus SmartZone controller configuration"""
    base_url: str = "https://3.12.57.221:8443"
    username: str = "apireadonly"
    password: str = "SBAedge2112#"
    api_version: str = "v9_1"
    timeout: int = 30
    verify_ssl: bool = False


@dataclass
class InfluxConfig:
    """InfluxDB configuration"""
    url: str = "http://20.64.233.185:8086"
    org: str = "wifi-org"
    bucket: str = "wifi-streaming"
    token: str = "vmEv3xPIBXM0iiW6rBQ8KKPZB7hdbjqbPJVtN0mrO0Cn96RhTGWP647J9K-lo-6mmB0_sQRvHLDdFgHrGb8GRQ=="


@dataclass
class ConnectorConfig:
    """Connector service configuration"""
    collection_interval: int = 60  # seconds
    run_continuous: bool = True


