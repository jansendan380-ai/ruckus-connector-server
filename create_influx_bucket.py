#!/usr/bin/env python3
"""
Script to create InfluxDB bucket if it doesn't exist
"""
from influxdb_client import InfluxDBClient
from influxdb_client.domain.bucket import Bucket
from influxdb_client.domain.bucket_retention_rules import BucketRetentionRules


def create_bucket():
    """Create InfluxDB bucket if it doesn't exist"""
    url = "http://20.64.233.185:8086"
    org = "wifi-org"
    bucket_name = "wifi-streaming"
    token = (
        "vmEv3xPIBXM0iiW6rBQ8KKPZB7hdbjqbPJVtN0mrO0Cn96RhTGWP647J9K-"
        "lo-6mmB0_sQRvHLDdFgHrGb8GRQ=="
    )

    print("=" * 60)
    print("InfluxDB Bucket Creation")
    print("=" * 60)
    print(f"URL: {url}")
    print(f"Organization: {org}")
    print(f"Bucket: {bucket_name}")
    print()

    try:
        client = InfluxDBClient(url=url, token=token, org=org)
        buckets_api = client.buckets_api()

        # Check if bucket exists
        print("Checking if bucket exists...")
        buckets = buckets_api.find_buckets()
        existing_bucket = None

        for bucket in buckets.buckets:
            if bucket.name == bucket_name:
                existing_bucket = bucket
                break

        if existing_bucket:
            print(f"✓ Bucket '{bucket_name}' already exists")
            print(f"  ID: {existing_bucket.id}")
            print(f"  Retention: {existing_bucket.retention_rules}")
        else:
            print(f"Bucket '{bucket_name}' not found. Creating...")

            # Create bucket
            retention_rules = BucketRetentionRules(
                every_seconds=0  # 0 = infinite retention
            )

            bucket = Bucket(
                name=bucket_name,
                retention_rules=[retention_rules],
                org_id=None  # Will use org from client
            )

            created_bucket = buckets_api.create_bucket(bucket=bucket)
            print(f"✓ Bucket '{bucket_name}' created successfully!")
            print(f"  ID: {created_bucket.id}")

        client.close()
        print()
        print("=" * 60)
        print("Done!")
        print("=" * 60)

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    create_bucket()

