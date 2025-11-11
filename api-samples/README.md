# Backend API Sample JSON Files

This directory contains sample JSON files that represent the expected data structure for your backend API endpoints. Use these files as a reference when building your backend to ensure compatibility with the frontend dashboard.

## API Endpoints Structure

### 1. Venue Data
**Endpoint**: `GET /api/venue`  
**File**: `venue-data.json`

Returns overall venue/network data including all zones with their metrics.

**Key Fields**:
- `name`: Venue name
- `totalZones`: Total number of zones
- `totalAPs`: Total access points across all zones
- `totalClients`: Total connected clients
- `avgExperienceScore`: Average experience score across zones
- `slaCompliance`: SLA compliance percentage
- `zones`: Array of zone objects with detailed metrics

### 2. Access Point Data
**Endpoint**: `GET /api/zones/:zoneId/aps`  
**File**: `ap-data.json`

Returns detailed access point information for a specific zone.

**Key Fields**:
- `total`: Total number of APs
- `list`: Array of AP objects with:
  - MAC address, name, model, status
  - IP address, zone information
  - Firmware version, serial number
  - Client count and utilization metrics
  - Radio configurations (2.4GHz and 5GHz)

### 3. Cause Code Data
**Endpoint**: `GET /api/cause-codes`  
**File**: `cause-code-data.json`

Returns 802.11 disconnect cause codes with counts and impact scores.

**Key Fields**:
- `code`: Cause code number
- `description`: Human-readable description
- `count`: Number of occurrences
- `impactScore`: Calculated impact score

### 4. Anomalies Data
**Endpoint**: `GET /api/anomalies`  
**File**: `anomalies-data.json`

Returns detected network anomalies with severity levels.

**Key Fields**:
- `id`: Unique anomaly ID
- `timestamp`: ISO timestamp string
- `type`: Type of anomaly (e.g., "poor_experience", "interference")
- `severity`: "critical" | "major" | "warning" | "info"
- `description`: Human-readable description
- `affectedZone`: Zone name where anomaly occurred
- `metric`: Metric type that triggered the anomaly

### 5. Clients Data
**Endpoint**: `GET /api/clients`  
**File**: `clients-data.json`

Returns list of connected clients/devices.

**Key Fields**:
- `hostname`: Device hostname or identifier
- `modelName`: Device model name
- `ipAddress`: Client IP address
- `macAddress`: Client MAC address
- `wlan`: WLAN/SSID name
- `apName`: Associated access point name
- `apMac`: Associated access point MAC
- `dataUsage`: Data usage in MB
- `os`: Operating system (optional)
- `deviceType`: Device type category (optional)

### 6. Host Usage Data
**Endpoint**: `GET /api/hosts`  
**File**: `host-usage-data.json`

Returns host data usage statistics for the hosts list visualization.

**Key Fields**:
- `hostname`: Device hostname
- `dataUsage`: Data usage in MB

### 7. OS Distribution Data
**Endpoint**: `GET /api/os-distribution`  
**File**: `os-distribution-data.json`

Returns operating system distribution percentages.

**Key Fields**:
- `os`: Operating system name
- `percentage`: Percentage of devices using this OS
- `color`: Hex color code for visualization

### 8. Load Data
**Endpoint**: `GET /api/load?hours=1`  
**File**: `load-data.json`

Returns frequency band load data over time.

**Key Fields**:
- `bands`: Array of band objects
  - `band`: "2.4G" | "5G" | "6G/5G"
  - `color`: Hex color code
  - `data`: Array of time-series data points
    - `timestamp`: ISO timestamp
    - `band24G`: 2.4G load value (0 for non-2.4G bands)
    - `band5G`: 5G load value (0 for non-5G bands)
    - `band6G5G`: 6G/5G load value (0 for non-6G/5G bands)

## Data Format Guidelines

1. **Timestamps**: All timestamps should be in ISO 8601 format (e.g., "2024-01-15T09:24:00Z")

2. **Numbers**: 
   - Percentages should be numbers (e.g., 98.5 not "98.5%")
   - Scores/values should be numbers, not strings
   - Utilization values should be between 0-100

3. **Status Values**:
   - AP status: "online" | "offline"
   - Anomaly severity: "critical" | "major" | "warning" | "info"

4. **Arrays**: All list responses should be arrays, even if empty

5. **Optional Fields**: Fields marked with `?` in TypeScript interfaces are optional but recommended

## Integration Example

```javascript
// Express.js example
app.get('/api/venue', async (req, res) => {
  try {
    // Fetch data from Ruckus SmartZone API
    const zones = await fetchZonesFromSmartZone();
    
    // Transform to match venue-data.json structure
    const venueData = {
      name: "Main Venue",
      totalZones: zones.length,
      totalAPs: calculateTotalAPs(zones),
      totalClients: calculateTotalClients(zones),
      avgExperienceScore: calculateAvgExperience(zones),
      slaCompliance: 100,
      zones: zones.map(transformZone)
    };
    
    res.json(venueData);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});
```

## Testing

You can use these sample files to:
1. Test your frontend locally by serving these as static files
2. Mock your backend API during development
3. Validate your backend responses match the expected structure
4. Use as reference for data transformation from SmartZone API

## Notes

- All file paths and endpoint URLs are examples - adjust to match your backend structure
- The sample data is representative - real data will vary
- Ensure your backend handles error cases and returns appropriate HTTP status codes
- Consider implementing pagination for large datasets (clients, APs)
- Add rate limiting to prevent API abuse


