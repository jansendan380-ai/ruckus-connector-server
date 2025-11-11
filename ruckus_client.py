"""
Ruckus SmartZone API Client
Fetches data from Ruckus SmartZone controller
"""
import requests
from requests.auth import HTTPBasicAuth
from typing import Dict, List, Optional, Any
import logging
from urllib3.exceptions import InsecureRequestWarning

# Suppress SSL warnings for self-signed certificates
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

logger = logging.getLogger(__name__)


class RuckusClient:
    """Client for interacting with Ruckus SmartZone API"""

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        api_version: str = "v9_1",
        timeout: int = 30,
        verify_ssl: bool = False
    ):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.api_version = api_version
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        api_path = f"/wsg/api/public/{self.api_version}"
        self.base_api_url = f"{self.base_url}{api_path}"
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(username, password)
        self.session.verify = verify_ssl

    def _make_request(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> Optional[Dict[str, Any]]:
        """Make HTTP request to Ruckus API"""
        url = f"{self.base_api_url}{endpoint}"

        try:
            if method == "GET":
                response = self.session.get(
                    url, params=params, timeout=self.timeout
                )
            elif method == "POST":
                response = self.session.post(
                    url, json=data, params=params, timeout=self.timeout
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            # Log response details for debugging
            if response.status_code == 401:
                logger.error(
                    f"Authentication failed (401) for {url}. "
                    f"Response: {response.text[:200]}"
                )
            elif response.status_code >= 400:
                logger.warning(
                    f"Request returned {response.status_code} for {url}. "
                    f"Response: {response.text[:200]}"
                )

            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(
                f"HTTP error {e.response.status_code} for {url}: {e}"
            )
            if e.response.status_code == 401:
                logger.error(
                    "Authentication failed. Please check credentials. "
                    "Response: " + e.response.text[:500]
                )
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request to {url}: {e}")
            return None

    def get_zones(self) -> List[Dict[str, Any]]:
        """Get all zones"""
        endpoint = "/query/zone"
        response = self._make_request(endpoint)
        if response and "list" in response:
            return response["list"]
        return []

    def get_aps(
        self,
        zone_id: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get access points, optionally filtered by zone"""
        endpoint = "/query/ap"
        params = {"listSize": limit}
        if zone_id:
            params["zoneId"] = zone_id

        all_aps = []
        first_index = 0

        while True:
            params["firstIndex"] = first_index
            response = self._make_request(endpoint, params=params)

            if not response or "list" not in response:
                break

            aps = response.get("list", [])
            all_aps.extend(aps)

            if not response.get("hasMore", False):
                break

            first_index += len(aps)

        return all_aps

    def get_clients(
        self,
        zone_id: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get clients, optionally filtered by zone"""
        endpoint = "/query/client"
        params = {"listSize": limit}
        if zone_id:
            params["zoneId"] = zone_id

        all_clients = []
        first_index = 0

        while True:
            params["firstIndex"] = first_index
            response = self._make_request(endpoint, params=params)

            if not response or "list" not in response:
                break

            clients = response.get("list", [])
            all_clients.extend(clients)

            if not response.get("hasMore", False):
                break

            first_index += len(clients)

        return all_clients

    def get_system_inventory(self) -> List[Dict[str, Any]]:
        """Get system inventory with zone statistics"""
        endpoint = "/system/inventory"
        response = self._make_request(endpoint)
        if response and "list" in response:
            return response["list"]
        return []

    def get_controllers(self) -> List[Dict[str, Any]]:
        """Get controller information"""
        endpoint = "/controller"
        response = self._make_request(endpoint)
        if response and "list" in response:
            return response["list"]
        return []

    def test_connection(self) -> bool:
        """Test connection to Ruckus controller"""
        try:
            response = self.get_controllers()
            return len(response) > 0
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

