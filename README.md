# WiFi Monitoring Connector

Python connector service that collects data from Ruckus SmartZone controller and stores it in InfluxDB for the WiFi monitoring dashboard.

## Architecture

```
Ruckus Controller → Python Connector → InfluxDB → FastAPI Backend → Frontend
```

## Features

- Fetches data from Ruckus SmartZone API
- Transforms data to match frontend API requirements
- Stores data efficiently in InfluxDB with proper time-series structure
- Supports continuous data collection at configurable intervals
- Handles pagination for large datasets
- Comprehensive error handling and logging

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

Edit `config.py` or modify the configuration in `connector.py`:

```python
# Ruckus Controller
base_url = "https://3.12.57.221:8443"
username = "apireadonly"
password = "your-password"
api_version = "v9_1"

# InfluxDB
url = "http://20.64.233.185:8086"
org = "wifi-org"
bucket = "wifi-streaming"
token = "your-token"
```

## Usage

### Run Once (for testing)
```bash
python connector.py
```

### Run Continuously
Uncomment the `connector.run_continuous()` line in `connector.py` or modify the code to run continuously.

## Data Structure

The connector collects and stores the following data types in InfluxDB:

### Measurements

1. **venue** - Overall venue metrics
   - Fields: totalZones, totalAPs, totalClients, avgExperienceScore, slaCompliance

2. **zone** - Zone-level metrics
   - Tags: zoneId, zoneName
   - Fields: totalAPs, connectedAPs, disconnectedAPs, clients, apAvailability, clientsPerAP, experienceScore, utilization, rxDesense, netflixScore

3. **access_point** - Access point metrics
   - Tags: apMac, apName, zoneId, zoneName, model, status
   - Fields: clientCount, clientCount24G, clientCount5G, airtime24G, airtime5G, noise24G, noise5G, channel24G, channel5G, eirp24G, eirp5G

4. **client** - Client/device metrics
   - Tags: clientMac, zoneId, apMac, apName, ssid, osType
   - Fields: txBytes, rxBytes, txRxBytes, rssi, snr, uplinkRate, downlinkRate

5. **os_distribution** - OS distribution statistics
   - Tags: os
   - Fields: percentage

6. **host_usage** - Top host data usage
   - Tags: hostname
   - Fields: dataUsage

## API Endpoints Mapped

The connector transforms Ruckus data to support these frontend endpoints:

1. `/api/venue` - From zones and system inventory
2. `/api/zones/:zoneId/aps` - From AP data filtered by zone
3. `/api/clients` - From client data
4. `/api/hosts` - Calculated from client data usage
5. `/api/os-distribution` - Calculated from client OS types
6. `/api/load` - Can be calculated from time-series AP utilization data
7. `/api/time-series` - Stored as time-series points in InfluxDB

## Data Collection Interval

Default collection interval is 60 seconds. Modify `collection_interval` in `connector.py` to change.

## Error Handling

- Connection errors are logged and the service continues
- API errors are logged with details
- InfluxDB write errors are logged but don't stop collection

## Logging

Logs are output to console with timestamps. Log level can be adjusted in `connector.py`:

```python
logging.basicConfig(level=logging.INFO)  # Change to DEBUG for more details
```

## Notes

- The connector handles pagination automatically for large datasets
- SSL verification is disabled by default (set `verify_ssl=True` if using valid certificates)
- All timestamps are stored in UTC
- Data is transformed to match frontend API format requirements

