# Backend API Endpoints Reference

This document outlines all API endpoints your backend should implement to support the dashboard frontend.

## Base URL
```
http://your-backend-url:3001/api
```

## Authentication
All endpoints should require authentication. Use JWT tokens or session-based auth.

**Headers**:
```
Authorization: Bearer <token>
Content-Type: application/json
```

## Endpoints

### 1. Get Venue Data
**GET** `/api/venue`

Returns overall venue/network metrics and all zones.

**Response**: See `venue-data.json`

**Example**:
```bash
curl -X GET http://localhost:3001/api/venue \
  -H "Authorization: Bearer <token>"
```

---

### 2. Get Access Points for Zone
**GET** `/api/zones/:zoneId/aps`

Returns detailed access point information for a specific zone.

**Parameters**:
- `zoneId` (path): Zone identifier

**Response**: See `ap-data.json`

**Example**:
```bash
curl -X GET http://localhost:3001/api/zones/zone-001/aps \
  -H "Authorization: Bearer <token>"
```

---

### 3. Get Cause Code Data
**GET** `/api/cause-codes`

Returns 802.11 disconnect cause codes with counts and impact scores.

**Query Parameters** (optional):
- `limit`: Number of results to return (default: all)
- `sort`: Sort by "count" or "impactScore" (default: "count")

**Response**: See `cause-code-data.json`

**Example**:
```bash
curl -X GET http://localhost:3001/api/cause-codes?limit=10 \
  -H "Authorization: Bearer <token>"
```

---

### 4. Get Anomalies
**GET** `/api/anomalies`

Returns detected network anomalies.

**Query Parameters** (optional):
- `severity`: Filter by severity ("critical" | "major" | "warning" | "info")
- `zoneId`: Filter by zone ID
- `limit`: Number of results (default: 50)
- `sort`: Sort order "timestamp" | "severity" (default: "timestamp")

**Response**: See `anomalies-data.json`

**Example**:
```bash
curl -X GET http://localhost:3001/api/anomalies?severity=critical&limit=20 \
  -H "Authorization: Bearer <token>"
```

---

### 5. Get Clients
**GET** `/api/clients`

Returns list of connected clients/devices.

**Query Parameters** (optional):
- `zoneId`: Filter by zone ID
- `apId`: Filter by access point ID
- `limit`: Number of results (default: 100)
- `offset`: Pagination offset (default: 0)
- `sort`: Sort by "dataUsage" | "hostname" | "timestamp" (default: "dataUsage")

**Response**: See `clients-data.json`

**Example**:
```bash
curl -X GET http://localhost:3001/api/clients?zoneId=zone-001&limit=50 \
  -H "Authorization: Bearer <token>"
```

---

### 6. Get Host Usage Data
**GET** `/api/hosts`

Returns host data usage statistics.

**Query Parameters** (optional):
- `limit`: Number of top hosts to return (default: 10)
- `sort`: Sort order "desc" | "asc" (default: "desc")

**Response**: See `host-usage-data.json`

**Example**:
```bash
curl -X GET http://localhost:3001/api/hosts?limit=20 \
  -H "Authorization: Bearer <token>"
```

---

### 7. Get OS Distribution
**GET** `/api/os-distribution`

Returns operating system distribution percentages.

**Response**: See `os-distribution-data.json`

**Example**:
```bash
curl -X GET http://localhost:3001/api/os-distribution \
  -H "Authorization: Bearer <token>"
```

---

### 8. Get Load Data
**GET** `/api/load`

Returns frequency band load data over time.

**Query Parameters**:
- `hours`: Number of hours of data (default: 1, max: 24)
- `zoneId`: Filter by zone ID (optional)

**Response**: See `load-data.json`

**Example**:
```bash
curl -X GET http://localhost:3001/api/load?hours=1 \
  -H "Authorization: Bearer <token>"
```

---

### 9. Get Time Series Data
**GET** `/api/time-series`

Returns time-series data for metrics.

**Query Parameters**:
- `metric`: Metric type ("experienceScore" | "utilization" | "netflixScore")
- `zoneIds`: Comma-separated zone IDs (optional)
- `startTime`: Start timestamp (ISO 8601)
- `endTime`: End timestamp (ISO 8601)
- `interval`: Data point interval in minutes (default: 1)

**Response**: See `time-series-data.json`

**Example**:
```bash
curl -X GET "http://localhost:3001/api/time-series?metric=experienceScore&zoneIds=zone-001,zone-002&interval=5" \
  -H "Authorization: Bearer <token>"
```

---

## Error Responses

All endpoints should return standard HTTP status codes:

### Success
- `200 OK`: Request successful
- `201 Created`: Resource created successfully

### Client Errors
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error

### Server Errors
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service temporarily unavailable

**Error Response Format**:
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}
  }
}
```

---

## Response Format Standards

1. **Content-Type**: Always `application/json`
2. **Timestamps**: ISO 8601 format (e.g., "2024-01-15T09:24:00Z")
3. **Numbers**: Always numbers, not strings (e.g., `98.5` not `"98.5"`)
4. **Null Values**: Use `null` for missing optional fields
5. **Empty Arrays**: Return `[]` instead of `null` for empty lists

---

## Pagination

For endpoints that support pagination:

**Query Parameters**:
- `limit`: Items per page (default: 50, max: 1000)
- `offset`: Number of items to skip (default: 0)

**Response Headers**:
```
X-Total-Count: 150
X-Page-Size: 50
X-Page-Number: 1
X-Total-Pages: 3
```

**Response Body**:
```json
{
  "data": [...],
  "pagination": {
    "total": 150,
    "limit": 50,
    "offset": 0,
    "hasMore": true
  }
}
```

---

## Rate Limiting

Consider implementing rate limiting:
- `X-RateLimit-Limit`: Requests per window
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Reset time (Unix timestamp)

---

## Caching Headers

For frequently accessed, less volatile data:
```
Cache-Control: public, max-age=300
ETag: "unique-resource-hash"
```

---

## WebSocket Endpoints (Optional)

For real-time updates:

**WS** `/ws/updates`

Subscribe to real-time data updates:
- Client connections
- AP status changes
- Anomaly detections
- Load metrics updates

**Message Format**:
```json
{
  "type": "client_connected" | "ap_status_change" | "anomaly_detected" | "load_update",
  "data": {...},
  "timestamp": "2024-01-15T09:24:00Z"
}
```

---

## Testing

Use the sample JSON files in this directory to:
1. Test your backend response format
2. Mock API responses during frontend development
3. Validate data transformations from SmartZone API

---

## Implementation Notes

- All timestamps should be in UTC
- Consider timezone conversion if needed for display
- Implement proper error handling and logging
- Use connection pooling for database/API connections
- Consider implementing request validation middleware
- Add API versioning if needed: `/api/v1/...`


