# Phase 3: Advanced Features

Complete guide for GPS tracking, photo attachments, device inventory, analytics, and real-time updates.

## Overview

Phase 3 adds enterprise features for healthcare device delivery:
- 📍 GPS tracking for field nurses
- 📸 Photo documentation of device setup
- 📦 Device inventory management
- 📊 Real-time analytics dashboards
- 🔄 Real-time WebSocket updates

## New Endpoints

### GPS Tracking

#### Record Nurse Location
**POST** `/api/nurse-locations`

Nurse app periodically sends GPS coordinates.

```bash
curl -X POST http://localhost:8080/api/nurse-locations \
  -H "Authorization: Bearer <nurse_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 48.8566,
    "longitude": 2.3522,
    "accuracy": 10.5,
    "visit_id": "visit-123"
  }'
```

Response:
```json
{
  "id": "loc-456",
  "recorded_at": "2026-02-26T14:30:00"
}
```

#### Get Current Nurse Locations
**GET** `/api/nurse-locations?nurse_id=nurse-id`

Doctor sees where nurses are in real-time (optionally filtered by nurse).

```bash
curl -H "Authorization: Bearer <doctor_token>" \
  "http://localhost:8080/api/nurse-locations"
```

Response:
```json
[
  {
    "id": "loc-456",
    "nurse_id": "nurse-123",
    "latitude": 48.8566,
    "longitude": 2.3522,
    "accuracy": 10.5,
    "recorded_at": "2026-02-26T14:30:00"
  }
]
```

---

### Photo Attachments

#### Upload Visit Photo
**POST** `/api/patient-visits/{visit_id}/photos`

Nurse uploads before/after photos from device installation.

```bash
curl -X POST "http://localhost:8080/api/patient-visits/visit-123/photos" \
  -H "Authorization: Bearer <nurse_token>" \
  -F "file=@device_setup.jpg" \
  -F "caption=Device installed at bedside"
```

Response:
```json
{
  "id": "photo-789",
  "file_path": "/tmp/photo_visit-123_abc123.jpg",
  "caption": "Device installed at bedside",
  "uploaded_at": "2026-02-26T14:45:00"
}
```

#### Get Visit Photos
**GET** `/api/patient-visits/{visit_id}/photos`

View all photos for a visit.

```bash
curl -H "Authorization: Bearer <nurse_token>" \
  "http://localhost:8080/api/patient-visits/visit-123/photos"
```

Response:
```json
[
  {
    "id": "photo-789",
    "file_path": "/tmp/photo_...",
    "caption": "Before setup",
    "uploaded_at": "2026-02-26T14:30:00"
  },
  {
    "id": "photo-790",
    "file_path": "/tmp/photo_...",
    "caption": "After setup",
    "uploaded_at": "2026-02-26T14:45:00"
  }
]
```

---

### Device Inventory

#### Create Device
**POST** `/api/devices`

Add new device to inventory.

```bash
curl -X POST http://localhost:8080/api/devices \
  -H "Authorization: Bearer <doctor_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Oxygen Concentrator",
    "model": "DeVilbiss 5L",
    "serial_number": "OC-2024-001234"
  }'
```

Response:
```json
{
  "id": "device-001",
  "status": "available"
}
```

#### List Inventory
**GET** `/api/devices?status=available`

View organization's device inventory (filtered by status).

```bash
curl -H "Authorization: Bearer <doctor_token>" \
  "http://localhost:8080/api/devices?status=available"
```

Response:
```json
[
  {
    "id": "device-001",
    "name": "Oxygen Concentrator",
    "model": "DeVilbiss 5L",
    "serial_number": "OC-2024-001234",
    "status": "available",
    "created_at": "2026-02-25T10:00:00"
  }
]
```

#### Update Device Status
**PATCH** `/api/devices/{device_id}`

Change device status (e.g., after installation).

```bash
curl -X PATCH "http://localhost:8080/api/devices/device-001" \
  -H "Authorization: Bearer <doctor_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "in_use",
    "visit_id": "visit-123",
    "reason": "Installed at patient Jean Martin's home"
  }'
```

Response:
```json
{
  "id": "device-001",
  "status": "in_use"
}
```

**Device Statuses:**
- `available` - Ready to assign
- `assigned` - Assigned to a visit
- `in_use` - Currently with patient
- `maintenance` - Requires service
- `returned` - Returned and cleaned

---

### Analytics

#### Visit Analytics
**GET** `/api/analytics/visits?date_from=2026-02-01T00:00:00&date_to=2026-02-28T23:59:59`

Get visit completion metrics for date range.

```bash
curl -H "Authorization: Bearer <doctor_token>" \
  "http://localhost:8080/api/analytics/visits"
```

Response:
```json
{
  "total_visits": 45,
  "completed_visits": 38,
  "pending_visits": 5,
  "in_progress_visits": 2,
  "completion_rate": 84.44,
  "average_visit_duration_minutes": 45.5
}
```

#### Device Analytics
**GET** `/api/analytics/devices`

Get device inventory metrics.

```bash
curl -H "Authorization: Bearer <doctor_token>" \
  "http://localhost:8080/api/analytics/devices"
```

Response:
```json
{
  "total_devices": 25,
  "available_devices": 8,
  "in_use_devices": 15,
  "maintenance_devices": 2,
  "device_utilization_rate": 68.0
}
```

#### Nurse Performance
**GET** `/api/analytics/nurses`

Compare nurse performance metrics.

```bash
curl -H "Authorization: Bearer <doctor_token>" \
  "http://localhost:8080/api/analytics/nurses"
```

Response:
```json
[
  {
    "nurse_id": "nurse-123",
    "nurse_name": "Marie Soignante",
    "total_visits": 15,
    "completed_visits": 14,
    "average_visit_duration_minutes": 42.3,
    "completion_rate": 93.33
  },
  {
    "nurse_id": "nurse-124",
    "nurse_name": "Jean Caregivier",
    "total_visits": 12,
    "completed_visits": 10,
    "average_visit_duration_minutes": 48.5,
    "completion_rate": 83.33
  }
]
```

---

### Real-time Updates (WebSocket)

#### Connect to Real-time Updates
**WS** `/ws/doctor/{user_id}`

Doctor connects to receive live updates about nurse activities.

```javascript
// Frontend JavaScript
const ws = new WebSocket(
  `ws://localhost:8080/ws/doctor/${doctorUserId}`
);

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);

  if (update.type === "visit_update") {
    console.log(`Visit ${update.visit_id} status: ${update.status}`);
    // Update UI with real-time status
    updateVisitStatus(update.visit_id, update.status);
  }
};

ws.send(JSON.stringify({ type: "ping" }));
```

**Real-time Events:**
- `visit_update` - Visit status changed (pending → in_progress → completed)
- `nurse_location_update` - Nurse location updated
- `device_status_change` - Device status changed
- `visit_completed` - Visit marked as completed with details

Example events:
```json
{
  "type": "visit_update",
  "visit_id": "visit-123",
  "status": "in_progress",
  "details": {
    "nurse_id": "nurse-123",
    "patient_name": "Jean Martin"
  },
  "timestamp": "2026-02-26T14:30:00"
}
```

---

## Complete Advanced Workflow

```bash
# 1. DOCTOR: Create device in inventory
curl -X POST http://localhost:8080/api/devices \
  -H "Authorization: Bearer <doctor_token>" \
  -d '{"name": "Oxygen Concentrator", "serial_number": "OC-2024-001234"}'
# → {"id": "device-001", "status": "available"}

# 2. DOCTOR: Assign nurse to visit
curl -X POST http://localhost:8080/api/patient-visits \
  -H "Authorization: Bearer <doctor_token>" \
  -d '{"prescription_id": "rx-123", "assigned_nurse": "nurse-id", ...}'
# → {"id": "visit-123", "status": "pending"}

# 3. NURSE: Start daily routine - check schedule
curl -H "Authorization: Bearer <nurse_token>" \
  "http://localhost:8080/api/patient-visits?date_from=2026-02-26T00:00:00"
# → [{"id": "visit-123", "patient_name": "Jean Martin", ...}]

# 4. NURSE: Begin driving to patient - send GPS
curl -X POST http://localhost:8080/api/nurse-locations \
  -H "Authorization: Bearer <nurse_token>" \
  -d '{"latitude": 48.8566, "longitude": 2.3522, "accuracy": 25}'
# → {"id": "loc-456", ...}

# 5. DOCTOR: Monitor nurse in real-time
# WebSocket receives: {"type": "visit_update", "visit_id": "visit-123", "status": "in_progress"}

# 6. NURSE: Arrive and mark in progress
curl -X PUT "http://localhost:8080/api/patient-visits/visit-123/status" \
  -H "Authorization: Bearer <nurse_token>" \
  -d '{"status": "in_progress"}'

# 7. NURSE: Take before photo
curl -X POST "http://localhost:8080/api/patient-visits/visit-123/photos" \
  -H "Authorization: Bearer <nurse_token>" \
  -F "file=@before.jpg" \
  -F "caption=Patient home before setup"
# → {"id": "photo-789", ...}

# 8. NURSE: Install device, take after photo
curl -X POST "http://localhost:8080/api/patient-visits/visit-123/photos" \
  -H "Authorization: Bearer <nurse_token>" \
  -F "file=@after.jpg" \
  -F "caption=Device installed and patient trained"

# 9. DOCTOR: Update device status to in_use
curl -X PATCH "http://localhost:8080/api/devices/device-001" \
  -H "Authorization: Bearer <doctor_token>" \
  -d '{"status": "in_use", "visit_id": "visit-123"}'
# → {"id": "device-001", "status": "in_use"}

# 10. NURSE: Complete visit with signature and notes
curl -X POST "http://localhost:8080/api/patient-visits/visit-123/complete" \
  -H "Authorization: Bearer <nurse_token>" \
  -d '{
    "nurse_notes": "Device installed. Patient trained on usage.",
    "device_serial_installed": "OC-2024-001234",
    "patient_signature": "data:image/png;base64,..."
  }'

# 11. DOCTOR: View real-time analytics
curl -H "Authorization: Bearer <doctor_token>" \
  "http://localhost:8080/api/analytics/visits"
# → {"total_visits": 45, "completed_visits": 39, "completion_rate": 86.67, ...}

# 12. DOCTOR: Check nurse performance
curl -H "Authorization: Bearer <doctor_token>" \
  "http://localhost:8080/api/analytics/nurses"
# → [{"nurse_name": "Marie", "completion_rate": 93.33, ...}]
```

---

## Database Extensions

### NurseLocation
```
id, org_id, nurse_id, latitude, longitude, accuracy
visit_id, recorded_at
```

### PhotoAttachment
```
id, visit_id, file_path, caption, file_size, mime_type, uploaded_at
```

### DeviceStatus
```
id, device_id, visit_id, old_status, new_status, changed_by
reason, changed_at
```

### OfflineQueue
```
id, user_id, action, resource_type, resource_id, payload
status, attempted_at, synced_at, error_message, created_at
```

---

## Frontend Implementation

### Nurse Mobile App

**Daily Schedule Screen:**
- Fetch `/api/patient-visits?date_from=...&date_to=...`
- Display as list/map
- Tap to see details

**Visit Detail Screen:**
- Show prescription info
- "Start Visit" → calls `/api/patient-visits/:id/status` with `in_progress`

**During Visit:**
- Start GPS tracking every 30 seconds: `POST /api/nurse-locations`
- Upload photos: `POST /api/patient-visits/:id/photos`
- Take patient signature

**Completion Screen:**
- Add notes
- Scan device serial or manual entry
- Get patient signature
- Submit: `POST /api/patient-visits/:id/complete`

### Doctor Dashboard

**Real-time View:**
- Connect WebSocket: `ws://localhost:8080/ws/doctor/{user_id}`
- Show live nurse locations on map
- Live visit status updates
- Real-time analytics graphs

**Analytics Dashboard:**
- Charts for completion rate
- Device utilization graphs
- Nurse performance comparison
- Device status distribution

---

## Production Considerations

### GPS & Privacy
- Get user consent before tracking
- Option to disable location sharing
- Clear privacy policy

### Photo Storage
- Current: Local filesystem (development)
- Production: Use AWS S3 or similar
- Encrypt sensitive data at rest

### WebSocket Scalability
- Current: In-memory connection storage
- Production: Use Redis or database for connection management
- Implement connection pooling

### Analytics Caching
- Cache computed analytics
- Refresh every 5-10 minutes
- Use Redis for performance

### Offline Sync
- Phase 3.5: Implement `OfflineQueue` table
- Mobile app queues actions when offline
- Syncs when connection available
- Conflict resolution for simultaneous edits

---

## Phase 3.5 Preview: Offline-First Mobile

After Phase 3 stabilizes:

**Offline Capabilities:**
- Download daily schedule as SQLite
- Queue location updates
- Queue photo uploads
- Queue visit completions
- Sync when online

**Offline Queue Table:**
```sql
INSERT INTO offline_queue (user_id, action, resource_type, payload)
VALUES ('nurse-123', 'update', 'patient_visit', '{"id": "...", "status": "completed"}');
```

**Sync Logic:**
1. Mobile detects connection
2. Processes queue in order
3. Retries failed actions
4. Resolves conflicts
5. Clears synced items

---

## Testing Phase 3

### GPS Testing
```bash
# Simulate nurse movement
for i in {1..10}; do
  curl -X POST http://localhost:8080/api/nurse-locations \
    -H "Authorization: Bearer <nurse_token>" \
    -d "{\"latitude\": $((48 + i/1000)), \"longitude\": 2.3522}"
  sleep 5
done
```

### WebSocket Testing
```bash
# Use websocat or wscat
wscat -c ws://localhost:8080/ws/doctor/doctor-123
# Paste: {"type": "ping"}
```

### Analytics Testing
```bash
# Create multiple visits with various statuses
# Then check analytics endpoints
curl -H "Authorization: Bearer <doctor_token>" \
  "http://localhost:8080/api/analytics/visits"
```

---

## Summary

Phase 3 transforms Vocalis into an enterprise healthcare logistics platform with:

✅ Real-time nurse tracking
✅ Photo documentation
✅ Device inventory management
✅ Live analytics dashboards
✅ Real-time status updates
✅ Foundation for offline-first mobile

All endpoints support role-based access control and organization data isolation.
