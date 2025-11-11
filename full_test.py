#!/usr/bin/env python3
"""
End-to-end test:
- Authenticate to Ruckus (session)
- Fetch minimal datasets (controller, zones [POST], a few APs/clients)
- Connect to InfluxDB (health + ensure bucket)
- Write a small test point and verify a query roundtrip
"""
import sys
import logging
from datetime import datetime

from ruckus_client import RuckusClient
from influx_writer import InfluxWriter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("full_test")


def test_ruckus(base_url: str, username: str, password: str, api_version: str = "v9_1") -> bool:
    logger.info("Testing Ruckus login and endpoints...")
    rc = RuckusClient(
        base_url=base_url,
        username=username,
        password=password,
        api_version=api_version,
        timeout=30,
        verify_ssl=False,
    )

    controllers = rc.get_controllers()
    if not controllers:
        logger.error("Failed to fetch controllers")
        return False
    logger.info(f"Controllers OK (count={len(controllers)})")

    zones = rc.get_zones()
    logger.info(f"Zones OK (count={len(zones)})")

    # Fetch a small page of APs/clients to validate POST pagination path
    aps = rc.get_aps(limit=50)
    logger.info(f"APs OK (count={len(aps)})")

    clients = rc.get_clients(limit=50)
    logger.info(f"Clients OK (count={len(clients)})")

    return True


def test_influx(url: str, org: str, bucket: str, token: str) -> bool:
    logger.info("Testing InfluxDB connectivity and write/query...")
    iw = InfluxWriter(url=url, org=org, bucket=bucket, token=token)

    # Write a simple test point
    ok_write = iw.write_point(
        measurement="connector_e2e_test",
        tags={"component": "full_test"},
        fields={"value": 1},
        timestamp=datetime.utcnow(),
    )
    if not ok_write:
        logger.error("Failed to write test point")
        iw.close()
        return False

    # Query back using client query_api directly
    try:
        query_api = iw.client.query_api()
        query = f'''
        from(bucket: "{bucket}")
          |> range(start: -5m)
          |> filter(fn: (r) => r["_measurement"] == "connector_e2e_test")
          |> sort(columns: ["_time"], desc: true)
          |> limit(n: 1)
        '''
        result = query_api.query(query=query)
        found = False
        for table in result:
            for record in table.records:
                logger.info(f"Influx query OK: value={record.get_value()} time={record.get_time()}")
                found = True
        if not found:
            logger.warning("No test records found in query window")
            iw.close()
            return False
    except Exception as e:
        logger.error(f"Influx query failed: {e}")
        iw.close()
        return False

    iw.close()
    return True


def main():
    # Static config from project
    ruckus_cfg = {
        "base_url": "https://3.12.57.221:8443",
        "username": "apireadonly",
        "password": "SBAedge2112#",
        "api_version": "v9_1",
    }
    influx_cfg = {
        "url": "http://20.64.233.185:8086",
        "org": "wifi-org",
        "bucket": "wifi-streaming",
        "token": (
            "vmEv3xPIBXM0iiW6rBQ8KKPZB7hdbjqbPJVtN0mrO0Cn96RhTGWP647J9K-"
            "lo-6mmB0_sQRvHLDdFgHrGb8GRQ=="
        ),
    }

    ok_ruckus = test_ruckus(**ruckus_cfg)
    ok_influx = test_influx(**influx_cfg)

    if ok_ruckus and ok_influx:
        logger.info("Full end-to-end test PASSED")
        sys.exit(0)
    else:
        logger.error("Full end-to-end test FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
*** End Patch" }>>

