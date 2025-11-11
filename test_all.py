#!/usr/bin/env python3
"""
Comprehensive test script for both Ruckus and InfluxDB connections
"""
import sys
import subprocess


def main():
    """Run all connection tests"""
    print("=" * 60)
    print("WiFi Connector - Comprehensive Connection Tests")
    print("=" * 60)
    print()

    # Test Ruckus connection
    print("Testing Ruckus Controller Connection...")
    print("-" * 60)
    try:
        subprocess.run([sys.executable, "test_connection.py"], check=False)
    except Exception as e:
        print(f"Error running Ruckus test: {e}")
    print()

    # Test InfluxDB connection
    print("\nTesting InfluxDB Connection...")
    print("-" * 60)
    try:
        subprocess.run([sys.executable, "test_influx.py"], check=False)
    except Exception as e:
        print(f"Error running InfluxDB test: {e}")
    print()

    print("=" * 60)
    print("All tests completed")
    print("=" * 60)


if __name__ == "__main__":
    main()

