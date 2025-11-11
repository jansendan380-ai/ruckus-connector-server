# Database Schema Diagram

## Entity Relationship Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        VENUE                                 │
│  (Single record - overall network metrics)                  │
│  - totalZones                                               │
│  - totalAPs                                                 │
│  - totalClients                                             │
│  - avgExperienceScore                                       │
│  - slaCompliance                                            │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ aggregates
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                         ZONE                                 │
│  Tags: zoneId, zoneName                                     │
│  Fields: totalAPs, connectedAPs, clients,                   │
│          experienceScore, utilization, etc.                 │
└─────────────────────────────────────────────────────────────┘
         │                              │
         │ contains                     │ contains
         ▼                              ▼
┌──────────────────────┐    ┌──────────────────────┐
│   ACCESS_POINT       │    │      CLIENT          │
│  Tags: apMac,        │    │  Tags: clientMac,    │
│        zoneId,       │◄───┤        zoneId,       │
│        model,        │    │        apMac,        │
│        status        │    │        ssid, osType  │
│  Fields: clientCount,│    │  Fields: txBytes,    │
│          airtime24G, │    │          rxBytes,    │
│          airtime5G,  │    │          rssi, snr   │
│          channel24G, │    │                      │
│          channel5G   │    │                      │
└──────────────────────┘    └──────────────────────┘
                                      │
                                      │ aggregates to
                                      ▼
                    ┌─────────────────────────────┐
                    │   OS_DISTRIBUTION           │
                    │  Tags: os                   │
                    │  Fields: percentage         │
                    └─────────────────────────────┘
                                      │
                                      │ aggregates to
                                      ▼
                    ┌─────────────────────────────┐
                    │     HOST_USAGE              │
                    │  Tags: hostname             │
                    │  Fields: dataUsage          │
                    └─────────────────────────────┘
```

## Measurement Hierarchy

```
VENUE (1 record)
  └── ZONE (N zones)
        ├── ACCESS_POINT (M APs per zone)
        │     └── CLIENT (K clients per AP)
        │
        └── CLIENT (L clients per zone)
              ├── OS_DISTRIBUTION (aggregated)
              └── HOST_USAGE (aggregated)
```

## Tag Relationships

| Measurement      | Primary Tag        | Related Tags                    |
|------------------|-------------------|----------------------------------|
| venue            | (none)            | -                                |
| zone             | zoneId            | zoneName                         |
| access_point     | apMac             | zoneId, zoneName, model, status  |
| client           | clientMac         | zoneId, apMac, apName, ssid, osType |
| os_distribution  | os                | -                                |
| host_usage       | hostname          | -                                |

## Field Categories

### Count Fields
- `totalZones`, `totalAPs`, `totalClients`
- `connectedAPs`, `disconnectedAPs`
- `clientCount`, `clientCount24G`, `clientCount5G`

### Percentage Fields
- `apAvailability`, `slaCompliance`
- `utilization`, `airtime24G`, `airtime5G`
- `clientsPerAP`, `percentage` (OS distribution)

### Score Fields
- `experienceScore`, `netflixScore`

### Network Fields
- `rssi`, `snr`, `noise24G`, `noise5G`
- `channel24G`, `channel5G`
- `eirp24G`, `eirp5G`

### Data Fields
- `txBytes`, `rxBytes`, `txRxBytes`
- `dataUsage`
- `uplinkRate`, `downlinkRate`

### Metric Fields
- `rxDesense`

## Query Patterns by Use Case

### Frontend Endpoint: `/api/venue`
```flux
from(bucket: "wifi-streaming")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "venue")
  |> last()
```

### Frontend Endpoint: `/api/zones/:zoneId/aps`
```flux
from(bucket: "wifi-streaming")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "access_point")
  |> filter(fn: (r) => r["zoneId"] == "{zoneId}")
  |> last()
```

### Frontend Endpoint: `/api/clients`
```flux
from(bucket: "wifi-streaming")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "client")
  |> last()
```

### Frontend Endpoint: `/api/os-distribution`
```flux
from(bucket: "wifi-streaming")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "os_distribution")
  |> last()
```

### Frontend Endpoint: `/api/hosts`
```flux
from(bucket: "wifi-streaming")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "host_usage")
  |> last()
  |> sort(columns: ["_value"], desc: true)
  |> limit(n: 10)
```

### Frontend Endpoint: `/api/time-series`
```flux
from(bucket: "wifi-streaming")
  |> range(start: -{hours}h)
  |> filter(fn: (r) => r["_measurement"] == "zone")
  |> filter(fn: (r) => r["_field"] == "experienceScore")
  |> filter(fn: (r) => r["zoneId"] == "{zoneId}")
  |> aggregateWindow(every: {interval}m, fn: mean)
```

### Frontend Endpoint: `/api/load`
```flux
from(bucket: "wifi-streaming")
  |> range(start: -{hours}h)
  |> filter(fn: (r) => r["_measurement"] == "access_point")
  |> filter(fn: (r) => r["_field"] == "airtime24G" or r["_field"] == "airtime5G")
  |> aggregateWindow(every: 1h, fn: mean)
  |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
```

## Data Flow

```
Ruckus Controller
    │
    ├─→ Zones → zone measurement
    ├─→ APs → access_point measurement
    ├─→ Clients → client measurement
    │
    └─→ Aggregations
          ├─→ OS Distribution → os_distribution measurement
          ├─→ Host Usage → host_usage measurement
          └─→ Venue Stats → venue measurement
```

## Time-Series Considerations

All measurements are time-series data:
- Each point has a timestamp
- Historical data is preserved
- Use `aggregateWindow()` for time-based aggregations
- Use `last()` to get the most recent snapshot
- Use `range()` to specify time windows

## Indexing Strategy

Tags are indexed for fast filtering:
- Filter by `zoneId` to get zone-specific data
- Filter by `apMac` to get AP-specific data
- Filter by `clientMac` to get client-specific data
- Filter by `status` to get online/offline APs
- Filter by `osType` to get OS-specific clients

Fields are not indexed but contain the actual metric values.

