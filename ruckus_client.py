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
        query_api_version: str = "v9_1",
        login_api_version: str = "v10_0",
        timeout: int = 30,
        verify_ssl: bool = False
    ):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.query_api_version = query_api_version
        self.login_api_version = login_api_version
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        login_api_path = f"/wsg/api/public/{self.login_api_version}"
        query_api_path = f"/wsg/api/public/{self.query_api_version}"
        self.base_api_url_login = f"{self.base_url}{login_api_path}"
        self.base_api_url_query = f"{self.base_url}{query_api_path}"
        self.session = requests.Session()
        self.session.verify = verify_ssl
        self._authenticated = False
        self._login()

    def _login(self) -> bool:
        """Login to Ruckus API and establish session"""
        login_url = f"{self.base_api_url_login}/session"
        
        try:
            # Try POST with credentials
            response = self.session.post(
                login_url,
                json={
                    "username": self.username,
                    "password": self.password
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                self._authenticated = True
                logger.info("Successfully authenticated with Ruckus API")
                return True
            
            # Try Basic Auth approach
            response = self.session.post(
                login_url,
                auth=HTTPBasicAuth(self.username, self.password),
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                self._authenticated = True
                logger.info("Successfully authenticated with Ruckus API (Basic Auth)")
                return True
            
            logger.error(
                f"Login failed with status {response.status_code}: "
                f"{response.text[:200]}"
            )
            return False
            
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False

    def _make_request(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> Optional[Dict[str, Any]]:
        """Make HTTP request to Ruckus API"""
        url = f"{self.base_api_url_query}{endpoint}"

        try:
            # Ensure authenticated session
            if not self._authenticated:
                self._login()

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
                # Attempt re-authentication once and retry
                logger.warning("401 received; attempting re-authentication and retry...")
                self._authenticated = False
                if self._login():
                    if method == "GET":
                        response = self.session.get(
                            url, params=params, timeout=self.timeout
                        )
                    else:
                        response = self.session.post(
                            url, json=data, params=params, timeout=self.timeout
                        )
                else:
                    logger.error(
                        f"Re-authentication failed. Response: {response.text[:200]}"
                    )
                    response.raise_for_status()

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

    def get_zones(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get all zones using page/limit pagination (POST only)."""
        endpoint = "/query/zone"
        zones: List[Dict[str, Any]] = []
        page = 1
        while True:
            payload = {"limit": limit, "page": page}
            response = self._make_request(endpoint, method="POST", data=payload)
            if not response or "list" not in response:
                break
            batch = response.get("list", []) or []
            zones.extend(batch)
            if not response.get("hasMore", False):
                break
            page += 1
        return zones

    def get_aps(
        self,
        zone_id: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get access points, optionally filtered by zone (POST only, page/limit)."""
        endpoint = "/query/ap"
        aps: List[Dict[str, Any]] = []
        page = 1
        while True:
            payload: Dict[str, Any] = {"limit": limit, "page": page}
            if zone_id:
                # Preferred filter style; if schema rejects, we'll retry alternative
                payload["filters"] = [{"type": "ZONE", "value": zone_id}]
            response = self._make_request(endpoint, method="POST", data=payload)
            if (not response) and zone_id:
                # Retry without filters using direct zoneId field (seen in some deployments)
                alt_payload = {"limit": limit, "page": page, "zoneId": zone_id}
                response = self._make_request(endpoint, method="POST", data=alt_payload)
            if not response or "list" not in response:
                break
            batch = response.get("list", []) or []
            aps.extend(batch)
            if not response.get("hasMore", False):
                break
            page += 1
        return aps

    def get_clients(
        self,
        zone_id: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get clients, optionally filtered by zone (POST only, page/limit)."""
        endpoint = "/query/client"
        clients: List[Dict[str, Any]] = []
        page = 1
        while True:
            payload: Dict[str, Any] = {"limit": limit, "page": page}
            if zone_id:
                payload["filters"] = [{"type": "ZONE", "value": zone_id}]
            response = self._make_request(endpoint, method="POST", data=payload)
            if (not response) and zone_id:
                alt_payload = {"limit": limit, "page": page, "zoneId": zone_id}
                response = self._make_request(endpoint, method="POST", data=alt_payload)
            if not response or "list" not in response:
                break
            batch = response.get("list", []) or []
            clients.extend(batch)
            if not response.get("hasMore", False):
                break
            page += 1
        return clients

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

