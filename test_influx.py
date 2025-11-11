#!/usr/bin/env python3
"""
Test script to verify InfluxDB connection
"""
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime


def test_influx_connection():
    """Test InfluxDB connection and write a test point"""
    url = "http://20.64.233.185:8086"
    org = "wifi-org"
    bucket = "wifi-streaming"
    token = (
        "vmEv3xPIBXM0iiW6rBQ8KKPZB7hdbjqbPJVtN0mrO0Cn96RhTGWP647J9K-"
        "lo-6mmB0_sQRvHLDdFgHrGb8GRQ=="
    )

    print("=" * 60)
    print("InfluxDB Connection Test")
    print("=" * 60)
    print(f"URL: {url}")
    print(f"Organization: {org}")
    print(f"Bucket: {bucket}")
    print(f"Token: {token[:20]}...")
    print()

    try:
        # Test 1: Create client
        print("Test 1: Creating InfluxDB client...")
        client = InfluxDBClient(url=url, token=token, org=org)
        print("  ✓ Client created successfully")
        print()

        # Test 2: Check health
        print("Test 2: Checking InfluxDB health...")
        try:
            health = client.health()
            print(f"  ✓ Health check passed")
            print(f"    Status: {health.status}")
            print(f"    Message: {health.message}")
        except Exception as e:
            print(f"  ⚠ Health check failed: {e}")
        print()

        # Test 3: List buckets
        print("Test 3: Listing buckets...")
        try:
            buckets_api = client.buckets_api()
            buckets = buckets_api.find_buckets()
            print(f"  ✓ Found {len(buckets.buckets)} bucket(s):")
            for bucket_item in buckets.buckets:
                print(f"    - {bucket_item.name} (ID: {bucket_item.id})")
                if bucket_item.name == bucket:
                    print(f"      ✓ Target bucket found!")
        except Exception as e:
            print(f"  ✗ Error listing buckets: {e}")
        print()

        # Test 4: Write test point
        print("Test 4: Writing test point...")
        try:
            write_api = client.write_api(write_options=SYNCHRONOUS)
            from influxdb_client import Point

            point = Point("connection_test")
            point = point.tag("test", "true")
            point = point.field("value", 1)
            point = point.time(datetime.utcnow())

            write_api.write(bucket=bucket, org=org, record=point)
            print("  ✓ Test point written successfully")
        except Exception as e:
            print(f"  ✗ Error writing point: {e}")
        print()

        # Test 5: Query test point
        print("Test 5: Querying test point...")
        try:
            query_api = client.query_api()
            query = f'''
            from(bucket: "{bucket}")
              |> range(start: -1h)
              |> filter(fn: (r) => r["_measurement"] == "connection_test")
              |> last()
            '''
            result = query_api.query(query=query)
            if result:
                print("  ✓ Test point retrieved successfully")
                for table in result:
                    for record in table.records:
                        print(f"    Value: {record.get_value()}")
                        print(f"    Time: {record.get_time()}")
            else:
                print("  ⚠ No test point found (may need to wait)")
        except Exception as e:
            print(f"  ✗ Error querying: {e}")
        print()

        # Test 6: Check permissions
        print("Test 6: Checking permissions...")
        try:
            query_api = client.query_api()
            query = f'''
            from(bucket: "{bucket}")
              |> range(start: -1h)
              |> limit(n: 1)
            '''
            result = query_api.query(query=query)
            print("  ✓ Query permission verified")
        except Exception as e:
            print(f"  ✗ Permission error: {e}")
        print()

        client.close()
        print("=" * 60)
        print("InfluxDB test completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_influx_connection()

