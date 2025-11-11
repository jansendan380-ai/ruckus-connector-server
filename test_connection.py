#!/usr/bin/env python3
"""
Test script to diagnose Ruckus controller connection issues
"""
import requests
from requests.auth import HTTPBasicAuth
import urllib3
from urllib3.exceptions import InsecureRequestWarning

# Suppress SSL warnings
urllib3.disable_warnings(InsecureRequestWarning)


def test_connection():
    """Test Ruckus controller connection with detailed diagnostics"""
    base_url = "https://3.12.57.221:8443"
    username = "apireadonly"
    password = "SBAedge2112#"
    api_version = "v9_1"

    print("=" * 60)
    print("Ruckus Controller Connection Test")
    print("=" * 60)
    print(f"Base URL: {base_url}")
    print(f"Username: {username}")
    print(f"Password: {'*' * len(password)}")
    print(f"API Version: {api_version}")
    print()

    # Test 1: Basic connectivity
    print("Test 1: Basic connectivity check...")
    try:
        response = requests.get(
            base_url,
            verify=False,
            timeout=10
        )
        print(f"  ✓ Server is reachable (Status: {response.status_code})")
    except requests.exceptions.SSLError as e:
        print(f"  ⚠ SSL Error (expected with self-signed cert): {e}")
    except requests.exceptions.ConnectionError as e:
        print(f"  ✗ Connection failed: {e}")
        return
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return
    print()

    # Test 2: API endpoint accessibility
    api_url = f"{base_url}/wsg/api/public/{api_version}/controller"
    print(f"Test 2: API endpoint accessibility...")
    print(f"  URL: {api_url}")
    try:
        response = requests.get(
            api_url,
            verify=False,
            timeout=10
        )
        print(f"  Status Code: {response.status_code}")
        print(f"  Response Headers: {dict(response.headers)}")
        if response.status_code == 401:
            print("  ✗ Authentication required (401)")
            print(f"  Response: {response.text[:200]}")
        elif response.status_code == 200:
            print("  ✓ Endpoint is accessible")
            print(f"  Response: {response.text[:200]}")
        else:
            print(f"  ⚠ Unexpected status: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    print()

    # Test 3: Basic Auth with requests
    print("Test 3: Basic Authentication with requests library...")
    try:
        response = requests.get(
            api_url,
            auth=HTTPBasicAuth(username, password),
            verify=False,
            timeout=10
        )
        print(f"  Status Code: {response.status_code}")
        if response.status_code == 200:
            print("  ✓ Authentication successful!")
            try:
                data = response.json()
                print(f"  Response keys: {list(data.keys())}")
                if "list" in data:
                    print(f"  Found {len(data.get('list', []))} items")
            except Exception as e:
                print(f"  Response parsing error: {e}")
        elif response.status_code == 401:
            print("  ✗ Authentication failed (401)")
            print(f"  Response: {response.text[:500]}")
            print("\n  Possible issues:")
            print("    - Incorrect username or password")
            print("    - Account is locked or disabled")
            print("    - Account doesn't have API access")
        else:
            print(f"  ⚠ Unexpected status: {response.status_code}")
            print(f"  Response: {response.text[:500]}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    print()

    # Test 4: Session-based authentication
    print("Test 4: Session-based authentication...")
    try:
        session = requests.Session()
        session.auth = HTTPBasicAuth(username, password)
        session.verify = False

        response = session.get(api_url, timeout=10)
        print(f"  Status Code: {response.status_code}")
        if response.status_code == 200:
            print("  ✓ Session authentication successful!")
        else:
            print(f"  ✗ Session authentication failed")
            print(f"  Response: {response.text[:500]}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    print()

    # Test 5: Try login endpoint (if exists)
    print("Test 5: Checking for login endpoint...")
    login_urls = [
        f"{base_url}/wsg/api/public/v9_1/login",
        f"{base_url}/wsg/api/public/v9_1/session",
        f"{base_url}/wsg/api/public/v9_1/auth",
    ]
    for login_url in login_urls:
        try:
            response = requests.post(
                login_url,
                json={"username": username, "password": password},
                verify=False,
                timeout=10
            )
            print(f"  {login_url}: {response.status_code}")
            if response.status_code != 404:
                print(f"    Response: {response.text[:200]}")
        except Exception as e:
            print(f"  {login_url}: Error - {e}")
    print()

    # Test 6: Test other endpoints
    print("Test 6: Testing other endpoints...")
    test_endpoints = [
        "/query/zone",
        "/system/inventory",
        "/domains",
    ]
    session = requests.Session()
    session.auth = HTTPBasicAuth(username, password)
    session.verify = False

    for endpoint in test_endpoints:
        url = f"{base_url}/wsg/api/public/{api_version}{endpoint}"
        try:
            response = session.get(url, timeout=10)
            print(f"  {endpoint}: {response.status_code}")
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "list" in data:
                        print(f"    ✓ Found {len(data.get('list', []))} items")
                except Exception:
                    pass
        except Exception as e:
            print(f"  {endpoint}: Error - {e}")
    print()

    # Test 7: Check credentials format
    print("Test 7: Credential format check...")
    print(f"  Username length: {len(username)}")
    print(f"  Username contains spaces: {' ' in username}")
    print(f"  Password length: {len(password)}")
    print(f"  Password contains special chars: {any(c in password for c in '@#$%^&*')}")
    print()

    print("=" * 60)
    print("Test completed")
    print("=" * 60)


if __name__ == "__main__":
    test_connection()

