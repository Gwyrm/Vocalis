# Phase 3.5: Offline-First Mobile Synchronization

Complete guide for implementing offline-first mobile app with conflict resolution and sync queuing.

## Overview

Phase 3.5 enables nurses to work without internet connectivity and seamlessly sync when connection returns.

**Key Features:**
- 📵 Work without internet
- 📦 Automatic data sync
- 🔄 Conflict resolution
- ⚡ Optimized bandwidth
- 🔋 Battery efficient
- 📊 Sync monitoring

## Architecture

```
Mobile App (Offline-First)
├─ SQLite Local Cache
│  ├─ Prescriptions
│  ├─ Visits
│  ├─ Devices
│  ├─ Locations
│  └─ Photos
│
├─ Offline Queue
│  ├─ Create actions
│  ├─ Update actions
│  ├─ Delete actions
│  └─ Sync status
│
└─ Sync Engine
   ├─ Connection detection
   ├─ Batch queue processing
   ├─ Conflict resolution
   ├─ Retry logic
   └─ Progress tracking

↕️ (Sync)

Backend API
├─ /api/offline-sync/prepare (download package)
├─ /api/offline-sync/push (upload queued changes)
├─ /api/offline-sync/status (check pending)
└─ /api/offline-sync/queue (manage queue)
```

## API Endpoints

### 1. Prepare Offline Data

**POST** `/api/offline-sync/prepare?date_from=...&date_to=...`

Download data for offline use.

```bash
curl -X POST http://localhost:8080/api/offline-sync/prepare \
  -H "Authorization: Bearer <nurse_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "date_from": "2026-02-26T00:00:00",
    "date_to": "2026-02-26T23:59:59"
  }'
```

Response:
```json
{
  "user": {
    "id": "nurse-123",
    "email": "nurse@clinic.com",
    "full_name": "Marie Soignante",
    "role": "nurse"
  },
  "organization": {
    "id": "org-456",
    "name": "Clinic Paris",
    "address": "123 Rue de Paris, 75001",
    "phone": "01-23-45-67-89"
  },
  "prescriptions": [
    {
      "id": "rx-001",
      "patient_name": "Jean Martin",
      "diagnosis": "Hypertension",
      "medication": "Amlodipine",
      "dosage": "5mg daily",
      "duration": "30 days",
      "created_at": "2026-02-25T10:00:00"
    }
  ],
  "patient_visits": [
    {
      "id": "visit-001",
      "prescription_id": "rx-001",
      "patient_address": "456 Rue de Lion, 75002",
      "scheduled_date": "2026-02-26T14:00:00",
      "status": "pending"
    }
  ],
  "devices": [
    {
      "id": "device-001",
      "name": "Oxygen Concentrator",
      "serial_number": "OC-2024-001234",
      "status": "available"
    }
  ],
  "photos": [],
  "last_sync": "2026-02-26T08:00:00",
  "package_version": "1.0"
}
```

### 2. Queue Offline Action

**POST** `/api/offline-sync/queue`

Queue an action while offline.

```bash
curl -X POST http://localhost:8080/api/offline-sync/queue \
  -H "Authorization: Bearer <nurse_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "update",
    "resource_type": "patient_visit",
    "resource_id": "visit-001",
    "payload": {
      "status": "in_progress"
    }
  }'
```

Response:
```json
{
  "id": "queue-001",
  "status": "pending"
}
```

**Supported Actions:**
```
POST /api/offline-sync/queue
{
  "action": "create|update|delete",
  "resource_type": "patient_visit|nurse_location|device",
  "resource_id": "...",
  "payload": { ... }
}
```

### 3. Get Sync Queue

**GET** `/api/offline-sync/queue?status=pending`

View pending offline actions.

```bash
curl -H "Authorization: Bearer <nurse_token>" \
  "http://localhost:8080/api/offline-sync/queue?status=pending"
```

Response:
```json
[
  {
    "id": "queue-001",
    "action": "update",
    "resource_type": "patient_visit",
    "resource_id": "visit-001",
    "payload": {"status": "in_progress"},
    "status": "pending",
    "created_at": "2026-02-26T14:30:00"
  },
  {
    "id": "queue-002",
    "action": "create",
    "resource_type": "nurse_location",
    "resource_id": null,
    "payload": {"latitude": 48.8566, "longitude": 2.3522},
    "status": "pending",
    "created_at": "2026-02-26T14:32:00"
  }
]
```

### 4. Push Offline Changes

**POST** `/api/offline-sync/push`

Send queued offline actions to server.

```bash
curl -X POST http://localhost:8080/api/offline-sync/push \
  -H "Authorization: Bearer <nurse_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "queue_items": [
      {
        "action": "update",
        "resource_type": "patient_visit",
        "resource_id": "visit-001",
        "payload": {"status": "in_progress"}
      },
      {
        "action": "create",
        "resource_type": "nurse_location",
        "payload": {"latitude": 48.8566, "longitude": 2.3522, "visit_id": "visit-001"}
      }
    ]
  }'
```

Response:
```json
{
  "synced_count": 2,
  "failed_count": 0,
  "total_processed": 2,
  "conflicts": []
}
```

### 5. Get Sync Status

**GET** `/api/offline-sync/status`

Check current sync status.

```bash
curl -H "Authorization: Bearer <nurse_token>" \
  "http://localhost:8080/api/offline-sync/status"
```

Response:
```json
{
  "pending_count": 5,
  "synced_count": 12,
  "failed_count": 1,
  "last_sync_time": "2026-02-26T14:45:00",
  "next_retry_time": "2026-02-26T14:47:00"
}
```

### 6. Clear Queue Item

**DELETE** `/api/offline-sync/queue/{queue_id}`

Remove specific queue item.

```bash
curl -X DELETE "http://localhost:8080/api/offline-sync/queue/queue-001" \
  -H "Authorization: Bearer <nurse_token>"
```

Response:
```json
{
  "status": "deleted"
}
```

## Mobile App Implementation

### Flutter Example

```dart
import 'package:sqflite/sqflite.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:dio/dio.dart';

class OfflineSyncManager {
  final Database _db;
  final Dio _dio;
  final Connectivity _connectivity = Connectivity();

  OfflineSyncManager(this._db, this._dio);

  /// Download data for offline use
  Future<void> prepareOfflineData(String token) async {
    try {
      final response = await _dio.post(
        '/api/offline-sync/prepare',
        options: Options(
          headers: {'Authorization': 'Bearer $token'},
        ),
      );

      // Save to local SQLite
      await _saveToLocalDb(response.data);
    } catch (e) {
      print('Error preparing offline data: $e');
    }
  }

  /// Queue action while offline
  Future<void> queueAction({
    required String action,
    required String resourceType,
    required Map<String, dynamic> payload,
    String? resourceId,
  }) async {
    final queueItem = {
      'id': _generateId(),
      'action': action,
      'resource_type': resourceType,
      'resource_id': resourceId,
      'payload': json.encode(payload),
      'status': 'pending',
      'created_at': DateTime.now().toIso8601String(),
    };

    // Save to local queue table
    await _db.insert('offline_queue', queueItem);
  }

  /// Auto-sync when connection returns
  void initAutoSync(String token) {
    _connectivity.onConnectivityChanged.listen((result) async {
      if (result != ConnectivityResult.none) {
        print('Connection restored, syncing...');
        await syncPendingActions(token);
      }
    });
  }

  /// Sync pending actions
  Future<void> syncPendingActions(String token) async {
    try {
      // Get pending items from local queue
      final pendingItems = await _db.query(
        'offline_queue',
        where: 'status = ?',
        whereArgs: ['pending'],
      );

      if (pendingItems.isEmpty) {
        print('No pending actions to sync');
        return;
      }

      // Send to server
      final response = await _dio.post(
        '/api/offline-sync/push',
        data: {
          'queue_items': pendingItems.map((item) => {
            'action': item['action'],
            'resource_type': item['resource_type'],
            'resource_id': item['resource_id'],
            'payload': json.decode(item['payload'] as String),
          }).toList(),
        },
        options: Options(
          headers: {'Authorization': 'Bearer $token'},
        ),
      );

      // Mark as synced
      for (final item in pendingItems) {
        await _db.update(
          'offline_queue',
          {'status': 'synced', 'synced_at': DateTime.now().toIso8601String()},
          where: 'id = ?',
          whereArgs: [item['id']],
        );
      }

      print('Synced ${pendingItems.length} actions');

      // Refresh local data
      await prepareOfflineData(token);

    } catch (e) {
      print('Sync error: $e');
      // Mark as failed with retry logic
    }
  }

  /// Get local data for offline use
  Future<List<Map>> getLocalVisits() async {
    return await _db.query('patient_visits');
  }

  Future<List<Map>> getLocalPrescriptions() async {
    return await _db.query('prescriptions');
  }

  /// Update local data
  Future<void> updateLocalVisit(String visitId, String status) async {
    await _db.update(
      'patient_visits',
      {'status': status, 'updated_at': DateTime.now().toIso8601String()},
      where: 'id = ?',
      whereArgs: [visitId],
    );

    // Queue for sync
    await queueAction(
      action: 'update',
      resourceType: 'patient_visit',
      resourceId: visitId,
      payload: {'status': status},
    );
  }

  String _generateId() => 'id_${DateTime.now().millisecondsSinceEpoch}';

  Future<void> _saveToLocalDb(Map<String, dynamic> data) async {
    // Save user info
    await _db.insert('user', data['user']);

    // Save prescriptions
    for (final rx in data['prescriptions']) {
      await _db.insert('prescriptions', rx);
    }

    // Save visits
    for (final visit in data['patient_visits']) {
      await _db.insert('patient_visits', visit);
    }

    // Save devices
    for (final device in data['devices']) {
      await _db.insert('devices', device);
    }

    // Update sync timestamp
    await _db.execute(
      "INSERT OR REPLACE INTO sync_meta (key, value) VALUES ('last_sync', ?)",
      [DateTime.now().toIso8601String()],
    );
  }
}
```

### React Native Example

```javascript
import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-community/netinfo';
import SQLite from 'react-native-sqlite-storage';

class OfflineSyncManager {
  constructor(apiClient) {
    this.api = apiClient;
    this.db = null;
    this.initDatabase();
    this.listenForConnection();
  }

  async initDatabase() {
    this.db = await SQLite.openDatabase({
      name: 'vocalis.db',
      location: 'default',
    });
    await this.createTables();
  }

  async createTables() {
    const queries = [
      `CREATE TABLE IF NOT EXISTS offline_queue (
        id TEXT PRIMARY KEY,
        action TEXT,
        resource_type TEXT,
        resource_id TEXT,
        payload TEXT,
        status TEXT DEFAULT 'pending',
        created_at TEXT
      )`,
      `CREATE TABLE IF NOT EXISTS patient_visits (
        id TEXT PRIMARY KEY,
        prescription_id TEXT,
        patient_address TEXT,
        scheduled_date TEXT,
        status TEXT,
        created_at TEXT
      )`,
      `CREATE TABLE IF NOT EXISTS prescriptions (
        id TEXT PRIMARY KEY,
        patient_name TEXT,
        diagnosis TEXT,
        medication TEXT,
        dosage TEXT,
        duration TEXT,
        created_at TEXT
      )`,
    ];

    for (const query of queries) {
      await this.db.executeSql(query);
    }
  }

  async prepareOfflineData(token) {
    try {
      const response = await this.api.post(
        '/api/offline-sync/prepare',
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );

      // Save to local database
      await this.saveLocalData(response.data);
      console.log('Offline data prepared');
    } catch (error) {
      console.error('Error preparing offline data:', error);
    }
  }

  async queueAction(action, resourceType, payload, resourceId) {
    const queueItem = {
      id: `id_${Date.now()}`,
      action,
      resource_type: resourceType,
      resource_id: resourceId || null,
      payload: JSON.stringify(payload),
      status: 'pending',
      created_at: new Date().toISOString(),
    };

    await this.db.executeSql(
      `INSERT INTO offline_queue (id, action, resource_type, resource_id, payload, status, created_at)
       VALUES (?, ?, ?, ?, ?, ?, ?)`,
      [
        queueItem.id,
        queueItem.action,
        queueItem.resource_type,
        queueItem.resource_id,
        queueItem.payload,
        queueItem.status,
        queueItem.created_at,
      ]
    );
  }

  async syncPendingActions(token) {
    try {
      const [result] = await this.db.executeSql(
        'SELECT * FROM offline_queue WHERE status = ?',
        ['pending']
      );

      if (result.rows.length === 0) {
        console.log('No pending actions');
        return;
      }

      const queueItems = result.rows.raw().map(row => ({
        action: row.action,
        resource_type: row.resource_type,
        resource_id: row.resource_id,
        payload: JSON.parse(row.payload),
      }));

      const response = await this.api.post(
        '/api/offline-sync/push',
        { queue_items: queueItems },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      // Mark as synced
      for (const item of result.rows.raw()) {
        await this.db.executeSql(
          'UPDATE offline_queue SET status = ? WHERE id = ?',
          ['synced', item.id]
        );
      }

      console.log(`Synced ${response.synced_count} actions`);

      // Refresh offline data
      await this.prepareOfflineData(token);

    } catch (error) {
      console.error('Sync error:', error);
    }
  }

  listenForConnection() {
    NetInfo.addEventListener(state => {
      if (state.isConnected) {
        console.log('Connection restored, syncing...');
        // Get token from storage and sync
        AsyncStorage.getItem('auth_token').then(token => {
          if (token) this.syncPendingActions(token);
        });
      }
    });
  }

  async getLocalVisits() {
    const [result] = await this.db.executeSql(
      'SELECT * FROM patient_visits'
    );
    return result.rows.raw();
  }

  async updateLocalVisit(visitId, status) {
    // Update local database
    await this.db.executeSql(
      'UPDATE patient_visits SET status = ? WHERE id = ?',
      [status, visitId]
    );

    // Queue for sync
    await this.queueAction('update', 'patient_visit', { status }, visitId);
  }

  async saveLocalData(data) {
    // Save prescriptions
    for (const rx of data.prescriptions) {
      await this.db.executeSql(
        `INSERT OR REPLACE INTO prescriptions
         (id, patient_name, diagnosis, medication, dosage, duration, created_at)
         VALUES (?, ?, ?, ?, ?, ?, ?)`,
        [rx.id, rx.patient_name, rx.diagnosis, rx.medication, rx.dosage, rx.duration, rx.created_at]
      );
    }

    // Save visits
    for (const visit of data.patient_visits) {
      await this.db.executeSql(
        `INSERT OR REPLACE INTO patient_visits
         (id, prescription_id, patient_address, scheduled_date, status, created_at)
         VALUES (?, ?, ?, ?, ?, ?)`,
        [visit.id, visit.prescription_id, visit.patient_address, visit.scheduled_date, visit.status, visit.created_at]
      );
    }
  }
}
```

## Workflow: Offline Nurse App

```
1. Start of Day (Online)
   ├─ Download daily data: GET /api/offline-sync/prepare
   └─ Store in local SQLite

2. Work Throughout Day (May go offline)
   ├─ View local visits
   ├─ Start visit
   ├─ Record GPS: Queue action
   ├─ Upload photos: Queue action (photo saved locally)
   ├─ Complete visit: Queue action
   └─ No internet needed!

3. Back to Service Area (Connection Returns)
   ├─ App detects connection
   ├─ Auto-trigger sync: POST /api/offline-sync/push
   ├─ All queued actions sent to server
   ├─ Refresh local data
   └─ Continue work

4. End of Day
   ├─ Final sync if needed
   ├─ Validate all actions synced
   └─ Ready for tomorrow
```

## Conflict Resolution

**Strategy: Last-Write-Wins**

If same visit updated both offline and on server:

```
Server Update: 2026-02-26 14:30:00 → status="completed"
Offline Update: 2026-02-26 14:35:00 → status="in_progress"

Result: Offline wins (later timestamp)
Response includes: SyncConflict notification
```

**Handling Conflicts:**

```bash
# Server detects conflict
Response includes:
{
  "conflicts": [{
    "resource_type": "patient_visit",
    "resource_id": "visit-001",
    "local_version": {...},
    "server_version": {...},
    "local_updated_at": "2026-02-26T14:35:00",
    "server_updated_at": "2026-02-26T14:30:00",
    "resolution": "server_wins"  # or "local_wins"
  }]
}
```

**Mobile App Response:**

```dart
if (response.conflicts.isNotEmpty) {
  // Show conflict resolution UI
  for (var conflict in response.conflicts) {
    if (conflict.resolution == 'server_wins') {
      // Update local with server version
      await updateLocalData(conflict.resourceId, conflict.serverVersion);
    }
    // Show notification to user
    showNotification('Data conflict resolved automatically');
  }
}
```

## Sync Retry Logic

**Exponential Backoff:**

```
Failed Sync Attempt 1: Retry after 2 minutes
Failed Sync Attempt 2: Retry after 4 minutes
Failed Sync Attempt 3: Retry after 8 minutes
Failed Sync Attempt 4: Retry after 16 minutes
Max: 64 minutes between retries
```

**Manual Sync:**

```dart
// User can manually trigger sync
onPressed: () async {
  await syncManager.syncPendingActions(token);
  showSnackBar('Sync complete');
}
```

## Data Package Structure

**Downloaded Package (50-500 KB typical):**

```json
{
  "user": { ... },
  "organization": { ... },
  "prescriptions": [...],     // Only user's org
  "patient_visits": [...],    // Only nurse's visits
  "devices": [...],           // All org devices
  "photos": [...],            // Only nurse's visit photos
  "last_sync": "2026-02-26T08:00:00",
  "package_version": "1.0"
}
```

**Compression:**
- GZIP compress data before sending
- Typical size: 50 KB → 10 KB
- Saves bandwidth for field workers

## Battery & Data Optimization

**Battery:**
- Sync only when connected
- Batch queue every 30 seconds
- Disable GPS when not in visit

**Data:**
- Compress JSON payloads
- Only sync changed data (delta sync)
- Batch operations
- Remove deleted data after 30 days

## Testing Offline Sync

### Simulate Offline Mode

**iOS Simulator:**
```
Xcode → Hardware → Network Link Conditioner
Select "Very Bad Network" or "No Network"
```

**Android Emulator:**
```
Emulator Controls (⋮) → Extended Controls → Network
Set to "Disconnected"
```

**Postman:**
```
1. Download data: POST /api/offline-sync/prepare
2. Manually queue actions:
   POST /api/offline-sync/queue
3. Send to server:
   POST /api/offline-sync/push
```

## Monitoring

**Track Sync Health:**

```bash
# Check sync status
curl -H "Authorization: Bearer <nurse_token>" \
  "http://localhost:8080/api/offline-sync/status"

# View queue
curl -H "Authorization: Bearer <nurse_token>" \
  "http://localhost:8080/api/offline-sync/queue"

# Logs show sync events
[2026-02-26 14:30] Queue: 5 pending actions
[2026-02-26 14:35] Sync: 5 synced, 0 failed
[2026-02-26 14:36] Refresh: Downloaded new data
```

## Production Deployment

### Pre-launch Checklist

- ✅ Test offline mode thoroughly
- ✅ Test conflict resolution
- ✅ Test retry logic
- ✅ Monitor sync queue
- ✅ Plan data storage limits
- ✅ Implement sync monitoring
- ✅ Set up alerts for failed syncs
- ✅ Document user procedures

### Migration Strategy

**Phase 1:** Beta with select nurses
**Phase 2:** Gradual rollout
**Phase 3:** Full deployment

## Next Steps (Phase 4+)

After Phase 3.5 stabilizes:

- **Analytics:** Real-time sync metrics
- **Compression:** Better bandwidth optimization
- **Delta Sync:** Only sync changes
- **P2P Sync:** Nurse-to-nurse data sharing
- **Multi-site:** Sync across multiple clinics

---

## Summary

Phase 3.5 enables **true field operations** with:

✅ Work without internet
✅ Automatic sync on reconnect
✅ Conflict resolution
✅ Battery optimized
✅ Data efficient
✅ Easy mobile integration

All while maintaining **100% backend compatibility** with existing Phase 1-3 APIs.
