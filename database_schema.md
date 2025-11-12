# InfluxDB Database Schema

This document describes the database schema for the WiFi monitoring system stored in InfluxDB.

## Database Information

- **Database/Bucket**: `demo`
- **Organization**: `wifi-org`
- **Retention Policy**: Default (can be configured)

## Schema Overview

InfluxDB uses a time-series data model with:
- **Measurements**: Equivalent to tables (e.g., `venue`, `zone`, `access_point`)
- **Tags**: Indexed fields for filtering (e.g., `zoneId`, `apMac`)
- **Fields**: Actual data values (e.g., `totalAPs`, `clientCount`)
- **Timestamp**: Automatically added for each point

---

## Measurements

### 1. `venue`

Overall venue/network metrics aggregated across all zones.

**Tags:**
- None (single venue record)

**Fields:**
- `totalZones` (integer) - Total number of zones
- `totalAPs` (integer) - Total number of access points
- `totalClients` (integer) - Total number of connected clients
- `avgExperienceScore` (float) - Average experience score across all zones
- `slaCompliance` (float) - SLA compliance percentage

**Example Point:**
```
measurement: venue
time: 2024-01-15T09:24:00Z
fields: {
  totalZones: 24,
  totalAPs: 3255,
  totalClients: 11473,
  avgExperienceScore: 81.0,
  slaCompliance: 100.0
}
```

**Query Example:**
```flux
from(bucket: "demo")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "venue")
  |> last()
```

---

### 2. `zone`

Zone-level metrics and statistics.

**Tags:**
- `zoneId` (string) - Unique zone identifier
- `zoneName` (string) - Zone name
- `domainId` (string) - Domain identifier
- `domainName` (string) - Domain name

**Fields:**
- `totalAPs` (integer) - Total APs in zone
- `connectedAPs` (integer) - Number of online APs
- `disconnectedAPs` (integer) - Number of offline APs
- `clients` (integer) - Number of connected clients
- `apAvailability` (float) - AP availability percentage
- `clientsPerAP` (float) - Average clients per AP
- `experienceScore` (float) - Zone experience score (0-100)
- `utilization` (float) - Average channel utilization percentage
- `rxDesense` (float) - Average RX desense value
- `netflixScore` (float) - Netflix score (0-100)

**Example Point:**
```
measurement: zone
time: 2024-01-15T09:24:00Z
tags: {
  zoneId: "8533f41b-f651-42f3-828a-d4898c82294c",
  zoneName: "IL23640-P - Lutheran Hillside"
}
fields: {
  totalAPs: 383,
  connectedAPs: 379,
  disconnectedAPs: 4,
  clients: 369,
  apAvailability: 98.9,
  clientsPerAP: 0.97,
  experienceScore: 85.5,
  utilization: 65.2,
  rxDesense: 8.5,
  netflixScore: 82.3
}
```

**Query Examples:**
```flux
// Get all zones
from(bucket: "demo")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "zone")
  |> last()

// Get specific zone
from(bucket: "demo")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "zone")
  |> filter(fn: (r) => r["zoneId"] == "8533f41b-f651-42f3-828a-d4898c82294c")
  |> last()

// Get zone time-series data
from(bucket: "demo")
  |> range(start: -24h)
  |> filter(fn: (r) => r["_measurement"] == "zone")
  |> filter(fn: (r) => r["zoneId"] == "8533f41b-f651-42f3-828a-d4898c82294c")
  |> aggregateWindow(every: 1h, fn: mean)
```

---

### 3. `access_point`

Access point metrics and status information.

**Tags:**
- `apMac` (string) - AP MAC address (unique identifier)
- `apName` (string) - AP device name
- `zoneId` (string) - Zone identifier
- `zoneName` (string) - Zone name
- `model` (string) - AP model (e.g., "R750", "H550")
- `status` (string) - AP status ("online" or "offline")

**Fields:**
- `clientCount` (integer) - Total connected clients
- `clientCount24G` (integer) - Clients on 2.4GHz band
- `clientCount5G` (integer) - Clients on 5GHz band
- `airtime24G` (float) - 2.4GHz airtime utilization percentage
- `airtime5G` (float) - 5GHz airtime utilization percentage
- `noise24G` (float) - 2.4GHz noise floor (dBm)
- `noise5G` (float) - 5GHz noise floor (dBm)
- `channel24G` (integer) - 2.4GHz channel number
- `channel5G` (integer) - 5GHz channel number
- `eirp24G` (integer) - 2.4GHz EIRP (dBm)
- `eirp5G` (integer) - 5GHz EIRP (dBm)

**Example Point:**
```
measurement: access_point
time: 2024-01-15T09:24:00Z
tags: {
  apMac: "70:47:77:2F:E0:90",
  apName: "ap0031-POOL",
  zoneId: "cfb621aa-341f-4e5c-bb04-f2d1c21e801e",
  zoneName: "GA29532-P - Signal House",
  model: "R750",
  status: "online"
}
fields: {
  clientCount: 28,
  clientCount24G: 3,
  clientCount5G: 25,
  airtime24G: 45.2,
  airtime5G: 72.8,
  noise24G: -90,
  noise5G: -95,
  channel24G: 6,
  channel5G: 36,
  eirp24G: 18,
  eirp5G: 22
}
```

**Query Examples:**
```flux
// Get all APs for a zone
from(bucket: "demo")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "access_point")
  |> filter(fn: (r) => r["zoneId"] == "cfb621aa-341f-4e5c-bb04-f2d1c21e801e")
  |> last()

// Get specific AP
from(bucket: "demo")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "access_point")
  |> filter(fn: (r) => r["apMac"] == "70:47:77:2F:E0:90")
  |> last()

// Get offline APs
from(bucket: "demo")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "access_point")
  |> filter(fn: (r) => r["status"] == "offline")
  |> last()

// Get AP utilization over time
from(bucket: "demo")
  |> range(start: -24h)
  |> filter(fn: (r) => r["_measurement"] == "access_point")
  |> filter(fn: (r) => r["apMac"] == "70:47:77:2F:E0:90")
  |> aggregateWindow(every: 1h, fn: mean)
```

---

### 4. `client`

Client/device connection information and metrics.

**Tags:**
- `clientMac` (string) - Client MAC address (unique identifier)
- `zoneId` (string) - Zone identifier
- `apMac` (string) - Associated AP MAC address
- `apName` (string) - Associated AP name
- `ssid` (string) - SSID/WLAN name
- `osType` (string) - Operating system type

**Fields:**
- `txBytes` (integer) - Transmitted bytes
- `rxBytes` (integer) - Received bytes
- `txRxBytes` (integer) - Total bytes (tx + rx)
- `rssi` (integer) - Received signal strength indicator (dBm)
- `snr` (integer) - Signal-to-noise ratio (dB)
- `uplinkRate` (integer) - Uplink data rate (Mbps)
- `downlinkRate` (integer) - Downlink data rate (Mbps)

**Example Point:**
```
measurement: client
time: 2024-01-15T09:24:00Z
tags: {
  clientMac: "F2:66:34:40:49:B6",
  zoneId: "cfb621aa-341f-4e5c-bb04-f2d1c21e801e",
  apMac: "70:47:77:2F:E0:90",
  apName: "ap0031-POOL",
  ssid: "Passpoint-Secure",
  osType: "iOS Phone"
}
fields: {
  txBytes: 4507,
  rxBytes: 3167,
  txRxBytes: 7674,
  rssi: -79,
  snr: 17,
  uplinkRate: 7,
  downlinkRate: 10
}
```

**Query Examples:**
```flux
// Get all clients
from(bucket: "demo")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "client")
  |> last()

// Get clients for a zone
from(bucket: "demo")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "client")
  |> filter(fn: (r) => r["zoneId"] == "cfb621aa-341f-4e5c-bb04-f2d1c21e801e")
  |> last()

// Get clients for an AP
from(bucket: "demo")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "client")
  |> filter(fn: (r) => r["apMac"] == "70:47:77:2F:E0:90")
  |> last()

// Get clients by OS type
from(bucket: "demo")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "client")
  |> filter(fn: (r) => r["osType"] == "iOS Phone")
  |> last()
```

---

### 5. `os_distribution`

Operating system distribution statistics.

**Tags:**
- `os` (string) - Operating system name (e.g., "iOS", "Android", "Windows")

**Fields:**
- `percentage` (float) - Percentage of clients using this OS

**Example Point:**
```
measurement: os_distribution
time: 2024-01-15T09:24:00Z
tags: {
  os: "iOS"
}
fields: {
  percentage: 26.48
}
```

**Query Example:**
```flux
// Get OS distribution
from(bucket: "demo")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "os_distribution")
  |> last()
  |> group(columns: ["os"])
```

---

### 6. `host_usage`

Top host data usage statistics.

**Tags:**
- `hostname` (string) - Hostname or MAC address

**Fields:**
- `dataUsage` (float) - Data usage in MB

**Example Point:**
```
measurement: host_usage
time: 2024-01-15T09:24:00Z
tags: {
  hostname: "iPhone1"
}
fields: {
  dataUsage: 1300.5
}
```

**Query Example:**
```flux
// Get top host usage
from(bucket: "demo")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "host_usage")
  |> last()
  |> sort(columns: ["_value"], desc: true)
  |> limit(n: 10)
```

---

### 7. `ap_disconnect_cause`

AP disconnect cause codes for offline access points.

**Tags:**
- `apMac` (string) - AP MAC address (unique identifier)
- `apName` (string) - AP device name
- `zoneId` (string) - Zone identifier
- `zoneName` (string) - Zone name
- `model` (string) - AP model (e.g., "R750", "H550")
- `causeCode` (string) - Disconnect cause code identifier

**Fields:**
- `causeCode` (integer) - 802.11 disconnect cause code
- `causeDescription` (string) - Human-readable description
- `impactScore` (float) - Impact score (0-100)

**Example Point:**
```
measurement: ap_disconnect_cause
time: 2024-01-15T09:24:00Z
tags: {
  apMac: "70:47:77:2F:E0:90",
  apName: "ap0031-POOL",
  zoneId: "cfb621aa-341f-4e5c-bb04-f2d1c21e801e",
  zoneName: "GA29532-P - Signal House",
  model: "R750",
  causeCode: "200"
}
fields: {
  causeCode: 200,
  causeDescription: "AP lost heartbeat with controller",
  impactScore: 45.0
}
```

**Query Examples:**
```flux
// Get all disconnect causes
from(bucket: "demo")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "ap_disconnect_cause")
  |> last()

// Get disconnect causes for a specific zone
from(bucket: "demo")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "ap_disconnect_cause")
  |> filter(fn: (r) => r["zoneId"] == "cfb621aa-341f-4e5c-bb04-f2d1c21e801e")
  |> last()

// Get disconnect causes by code
from(bucket: "demo")
  |> range(start: -24h)
  |> filter(fn: (r) => r["_measurement"] == "ap_disconnect_cause")
  |> filter(fn: (r) => r["causeCode"] == "200")
  |> last()

// Count disconnect causes by code
from(bucket: "demo")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "ap_disconnect_cause")
  |> group(columns: ["causeCode"])
  |> count()
```

---

## Common Query Patterns

### Get Latest Data for All Measurements

```flux
// Venue
from(bucket: "demo")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "venue")
  |> last()

// All Zones
from(bucket: "demo")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "zone")
  |> last()

// All APs
from(bucket: "demo")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "access_point")
  |> last()

// All Clients
from(bucket: "demo")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "client")
  |> last()

// All AP Disconnect Causes
from(bucket: "demo")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "ap_disconnect_cause")
  |> last()
```

### Time-Series Queries

```flux
// Zone experience score over 24 hours
from(bucket: "demo")
  |> range(start: -24h)
  |> filter(fn: (r) => r["_measurement"] == "zone")
  |> filter(fn: (r) => r["zoneId"] == "8533f41b-f651-42f3-828a-d4898c82294c")
  |> filter(fn: (r) => r["_field"] == "experienceScore")
  |> aggregateWindow(every: 1h, fn: mean)

// AP utilization over time
from(bucket: "demo")
  |> range(start: -24h)
  |> filter(fn: (r) => r["_measurement"] == "access_point")
  |> filter(fn: (r) => r["apMac"] == "70:47:77:2F:E0:90")
  |> filter(fn: (r) => r["_field"] == "airtime5G")
  |> aggregateWindow(every: 15m, fn: mean)
```

### Aggregation Queries

```flux
// Average experience score across all zones
from(bucket: "demo")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "zone")
  |> filter(fn: (r) => r["_field"] == "experienceScore")
  |> mean()

// Total clients across all zones
from(bucket: "demo")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "zone")
  |> filter(fn: (r) => r["_field"] == "clients")
  |> sum()

// Count of online APs
from(bucket: "demo")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "access_point")
  |> filter(fn: (r) => r["status"] == "online")
  |> count()
```

---

## Data Collection Frequency

- **Collection Interval**: 60 seconds (configurable)
- **Timestamp**: UTC
- **Retention**: Configurable in InfluxDB

## Notes

1. All timestamps are in UTC
2. Tags are indexed for fast filtering
3. Fields contain the actual metric values
4. Each measurement point represents a snapshot at a specific time
5. Historical data is preserved for time-series analysis
6. Use `last()` to get the most recent data point
7. Use `aggregateWindow()` for time-series aggregation

## FastAPI Integration

When building your FastAPI backend, you can use the InfluxDB Python client to query this schema:

```python
from influxdb_client import InfluxDBClient

client = InfluxDBClient(url="...", token="...", org="wifi-org")
query_api = client.query_api()

# Query example
query = '''
from(bucket: "demo")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "venue")
  |> last()
'''

result = query_api.query(query=query)
```


