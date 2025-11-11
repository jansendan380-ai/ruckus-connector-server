# Quick Start Guide

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

The connector is pre-configured with your credentials. If you need to change them, edit `connector.py` or `run_connector.py`.

## Running the Connector

### Option 1: Run Once (for testing)
```bash
python run_connector.py --once
```

### Option 2: Run Continuously
```bash
python run_connector.py
```

The connector will collect data every 60 seconds by default.

### Option 3: Use connector.py directly
```bash
python connector.py
```

## What Gets Collected

The connector collects the following data from Ruckus and stores it in InfluxDB:

1. **Venue Data** - Overall network metrics
2. **Zone Data** - Per-zone statistics (APs, clients, metrics)
3. **Access Point Data** - Detailed AP information (status, utilization, clients)
4. **Client Data** - Connected device information
5. **OS Distribution** - Operating system statistics
6. **Host Usage** - Top data usage by hostname

## InfluxDB Structure

Data is stored in the following measurements:

- `venue` - Overall venue metrics
- `zone` - Zone-level metrics (tagged by zoneId)
- `access_point` - AP metrics (tagged by apMac, zoneId)
- `client` - Client metrics (tagged by clientMac, zoneId, apMac)
- `os_distribution` - OS statistics (tagged by os)
- `host_usage` - Host usage stats (tagged by hostname)

## Querying Data

Example InfluxDB queries:

```flux
// Get latest venue data
from(bucket: "wifi-streaming")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "venue")
  |> last()

// Get all zones
from(bucket: "wifi-streaming")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "zone")
  |> last()

// Get APs for a specific zone
from(bucket: "wifi-streaming")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "access_point")
  |> filter(fn: (r) => r["zoneId"] == "your-zone-id")
  |> last()
```

## Troubleshooting

### Connection Issues

1. **Ruckus connection fails**: Check network connectivity and credentials
2. **InfluxDB write fails**: Verify InfluxDB is running and token is valid

### Data Issues

- Check logs for error messages
- Verify API endpoints are accessible with your credentials
- Ensure InfluxDB bucket exists

## Next Steps

1. Verify data is being written to InfluxDB
2. Set up your FastAPI backend to query InfluxDB
3. Configure the connector to run as a service (systemd, Windows Service, etc.)


