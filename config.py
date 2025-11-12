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
    bucket: str = "demo"
    token: str = "NVmRj218iGEZbkWEVUokEO2AP3JTasaVhbfEhGk_6okfepun8HzWBxfyb1nEk0ENNnXuU8qoJsFy7m2ykcyrsA=="


@dataclass
class ConnectorConfig:
    """Connector service configuration"""
    collection_interval: int = 1800  # seconds (30 minutes)
    run_continuous: bool = True


