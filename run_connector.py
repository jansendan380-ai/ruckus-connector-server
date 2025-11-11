#!/usr/bin/env python3
"""
Simple script to run the WiFi connector
Can be used as a service or scheduled task
"""
import sys
import logging
from connector import WiFiConnector
from ruckus_client import RuckusClient
from influx_writer import InfluxWriter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point"""
    # Configuration
    ruckus_client = RuckusClient(
        base_url="https://3.12.57.221:8443",
        username="apireadonly",
        password="SBAedge2112#",
        query_api_version="v9_1",
        login_api_version="v10_0",
        timeout=30,
        verify_ssl=False
    )

    influx_writer = InfluxWriter(
        url="http://20.64.233.185:8086",
        org="wifi-org",
        bucket="wifi-streaming",
        token=(
            "vmEv3xPIBXM0iiW6rBQ8KKPZB7hdbjqbPJVtN0mrO0Cn96RhTGWP647J9K-"
            "lo-6mmB0_sQRvHLDdFgHrGb8GRQ=="
        )
    )

    # Test connections
    logger.info("Testing Ruckus connection...")
    if not ruckus_client.test_connection():
        logger.error("Failed to connect to Ruckus controller")
        sys.exit(1)

    logger.info("Ruckus connection successful")

    # Create connector
    connector = WiFiConnector(
        ruckus_client=ruckus_client,
        influx_writer=influx_writer,
        collection_interval=60  # Collect every 60 seconds
    )

    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        # Run once
        logger.info("Running connector once...")
        connector.collect_and_store()
    else:
        # Run continuously
        try:
            connector.run_continuous()
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            connector.stop()


if __name__ == "__main__":
    main()

