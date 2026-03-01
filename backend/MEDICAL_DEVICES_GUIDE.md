# Medical Device Prescriptions Guide

**Important:** Vocalis prescriptions support **both medications AND medical devices**. This guide covers device management.

## Overview

Vocalis allows doctors to prescribe medical equipment and devices to patients, just like medications. A single prescription can include:
- Medications/treatments
- Medical devices/equipment
- Or both together

## Supported Device Types

### Mobility & Assistive Devices
- Walkers (2-wheel, 4-wheel, rolling)
- Canes and crutches
- Wheelchairs (manual, power)
- Scooters and power chairs
- Transfer boards and lifts
- Gait belts
- Braces and orthotics

### Monitoring & Diagnostic Devices
- Blood pressure monitors (home use)
- Glucose meters (diabetes)
- Pulse oximeters
- Thermometers (digital, non-contact)
- Weight scales
- Heart rate monitors

### Respiratory Devices
- CPAP machines
- Oxygen concentrators
- Nebulizers
- Inhalers
- Oxygen delivery systems

### Bath & Safety Equipment
- Shower chairs
- Grab bars and rails
- Raised toilet seats
- Bath benches
- Anti-slip mats

### Wound Care & Supplies
- Compression stockings
- Bandages and dressings
- Wound care kits
- First aid supplies

### Specialized Medical Equipment
- Feeding tubes
- Catheters
- Colostomy supplies
- TENS units
- Heating/ice packs
- Pill organizers
- Bed rails

## Device Inventory Management

### Create Device in Catalog

```bash
curl -X POST http://localhost:8080/api/devices \
  -H "Authorization: Bearer $DOCTOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mobility Walker - 4 Wheel",
    "model": "MW-2024-Elite",
    "serial_number": "MW-2024-00001",
    "description": "Lightweight aluminum 4-wheel walker with seat"
  }'

# Response:
# {
#   "id": "device-uuid",
#   "org_id": "org-uuid",
#   "name": "Mobility Walker - 4 Wheel",
#   "model": "MW-2024-Elite",
#   "serial_number": "MW-2024-00001",
#   "status": "available",
#   "created_at": "2026-03-01T..."
# }
```

### List All Devices in Inventory

```bash
curl -X GET http://localhost:8080/api/devices \
  -H "Authorization: Bearer $TOKEN"

# Response: Array of devices with current status
```

### Check Device Status

Devices have life-cycle statuses:
- `available` - In inventory, not assigned to anyone
- `assigned` - Linked to a prescription
- `in_use` - Delivered to patient, actively being used
- `maintenance` - Under repair or service
- `returned` - Patient returned it

### Update Device Status

```bash
curl -X PATCH http://localhost:8080/api/devices/{device_id} \
  -H "Authorization: Bearer $DOCTOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "in_use"
  }'
```

## Prescription-Device Assignment

### Add Device to Prescription

After creating a prescription, add devices to it:

```bash
# Prescription already created with ID: $PRESCRIPTION_ID
# Device already in inventory with ID: $DEVICE_ID

curl -X POST http://localhost:8080/api/prescriptions/{prescription_id}/devices \
  -H "Authorization: Bearer $DOCTOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "'$DEVICE_ID'",
    "quantity": 1,
    "instructions": "Use for mobility assistance. Check seat and brakes before each use.",
    "priority": "high"
  }'

# Response:
# {
#   "id": "assignment-uuid",
#   "device_id": "device-uuid",
#   "quantity": 1,
#   "instructions": "Use for mobility assistance...",
#   "priority": "high"
# }
```

### Multiple Devices on One Prescription

Add as many devices as needed:

```bash
# Add first device (walker)
curl -X POST http://localhost:8080/api/prescriptions/$PRESCRIPTION_ID/devices \
  -H "Authorization: Bearer $DOCTOR_TOKEN" \
  -d '{"device_id":"'$WALKER_ID'","quantity":1,"priority":"high","instructions":"..."}'

# Add second device (blood pressure monitor)
curl -X POST http://localhost:8080/api/prescriptions/$PRESCRIPTION_ID/devices \
  -H "Authorization: Bearer $DOCTOR_TOKEN" \
  -d '{"device_id":"'$MONITOR_ID'","quantity":1,"priority":"normal","instructions":"..."}'

# Add third device (compression stockings - quantity 2 pairs)
curl -X POST http://localhost:8080/api/prescriptions/$PRESCRIPTION_ID/devices \
  -H "Authorization: Bearer $DOCTOR_TOKEN" \
  -d '{"device_id":"'$STOCKING_ID'","quantity":2,"priority":"normal","instructions":"..."}'
```

### View Devices on Prescription

```bash
curl -X GET http://localhost:8080/api/prescriptions/{prescription_id}/devices \
  -H "Authorization: Bearer $TOKEN"

# Response: Array of devices assigned to this prescription
# [
#   {
#     "id": "...",
#     "device_id": "walker-id",
#     "quantity": 1,
#     "instructions": "Use for mobility assistance...",
#     "priority": "high"
#   },
#   {
#     "id": "...",
#     "device_id": "monitor-id",
#     "quantity": 1,
#     "instructions": "Check BP daily...",
#     "priority": "normal"
#   }
# ]
```

### Remove Device from Prescription

```bash
curl -X DELETE http://localhost:8080/api/prescriptions/{prescription_id}/devices/{device_id} \
  -H "Authorization: Bearer $DOCTOR_TOKEN"
```

## Complete Example: Multi-Device Prescription

**Scenario:** Elderly patient with hypertension and limited mobility

### Step 1: Create Devices in Inventory

```bash
# Create mobility walker
WALKER=$(curl -X POST http://localhost:8080/api/devices \
  -H "Authorization: Bearer $DOCTOR_TOKEN" \
  -d '{"name":"Walker 4-Wheel","model":"MW-2024","serial_number":"MW-001"}' | jq -r .id)

# Create blood pressure monitor
MONITOR=$(curl -X POST http://localhost:8080/api/devices \
  -H "Authorization: Bearer $DOCTOR_TOKEN" \
  -d '{"name":"BP Monitor","model":"BPM-2024","serial_number":"BPM-001"}' | jq -r .id)

# Create compression stockings
STOCKINGS=$(curl -X POST http://localhost:8080/api/devices \
  -H "Authorization: Bearer $DOCTOR_TOKEN" \
  -d '{"name":"Compression Stockings","model":"CS-L","serial_number":"CS-001"}' | jq -r .id)
```

### Step 2: Create Prescription

```bash
RX=$(curl -X POST http://localhost:8080/api/prescriptions \
  -H "Authorization: Bearer $DOCTOR_TOKEN" \
  -d '{
    "patient_id":"'$PATIENT_ID'",
    "patient_name":"Jane Doe",
    "patient_age":"78",
    "diagnosis":"Hypertension with Mobility Limitation",
    "medication":"Lisinopril",
    "dosage":"10mg daily",
    "duration":"30 days"
  }' | jq -r .id)
```

### Step 3: Assign Devices to Prescription

```bash
# Walker - high priority for safety
curl -X POST http://localhost:8080/api/prescriptions/$RX/devices \
  -H "Authorization: Bearer $DOCTOR_TOKEN" \
  -d '{
    "device_id":"'$WALKER'",
    "quantity":1,
    "priority":"high",
    "instructions":"Use for all ambulation. Check brakes before each use."
  }'

# Blood pressure monitor - regular monitoring
curl -X POST http://localhost:8080/api/prescriptions/$RX/devices \
  -H "Authorization: Bearer $DOCTOR_TOKEN" \
  -d '{
    "device_id":"'$MONITOR'",
    "quantity":1,
    "priority":"normal",
    "instructions":"Check BP daily at same time. Log readings."
  }'

# Compression stockings - circulation support
curl -X POST http://localhost:8080/api/prescriptions/$RX/devices \
  -H "Authorization: Bearer $DOCTOR_TOKEN" \
  -d '{
    "device_id":"'$STOCKINGS'",
    "quantity":2,
    "priority":"normal",
    "instructions":"Wear one pair daily. Wash alternating pairs."
  }'
```

### Step 4: Sign Prescription

```bash
curl -X PUT http://localhost:8080/api/prescriptions/$RX/sign \
  -H "Authorization: Bearer $DOCTOR_TOKEN" \
  -d '{"signature_base64":"..."}'

# Prescription now includes:
# ✓ Medication: Lisinopril 10mg daily
# ✓ Device 1: Walker 4-Wheel (high priority)
# ✓ Device 2: Blood Pressure Monitor (normal priority)
# ✓ Device 3: Compression Stockings x2 (normal priority)
```

### Step 5: Create Interventions

```bash
# Intervention 1: Device delivery and training
curl -X POST http://localhost:8080/api/interventions \
  -H "Authorization: Bearer $DOCTOR_TOKEN" \
  -d '{
    "prescription_id":"'$RX'",
    "intervention_type":"Medical equipment delivery",
    "description":"Deliver walker, BP monitor, compression stockings. Train patient on use.",
    "scheduled_date":"2026-03-05T10:00:00",
    "priority":"high"
  }'

# Intervention 2: Follow-up check
curl -X POST http://localhost:8080/api/interventions \
  -H "Authorization: Bearer $DOCTOR_TOKEN" \
  -d '{
    "prescription_id":"'$RX'",
    "intervention_type":"Follow-up visit",
    "description":"Check BP readings, review walker usage, comfort assessment.",
    "scheduled_date":"2026-03-15T14:00:00",
    "priority":"normal"
  }'
```

### Step 6: Nurse Logs Delivery

```bash
curl -X POST http://localhost:8080/api/interventions/{intervention_id}/log \
  -H "Authorization: Bearer $NURSE_TOKEN" \
  -d '{
    "status_change":"scheduled→completed",
    "notes":"All three items delivered and patient trained. Walker adjusted to proper height. Patient demonstrated safe use of BP monitor."
  }'
```

## Device Analytics

Track device utilization and availability:

```bash
curl -X GET http://localhost:8080/api/devices/{device_id}/analytics \
  -H "Authorization: Bearer $DOCTOR_TOKEN"

# Response includes:
# - Times device has been assigned
# - Current status
# - Days in use
# - Last activity
```

## Best Practices

### Device Naming
- Use clear, descriptive names: "Walker - 4 Wheel Rollator" (not just "Walker")
- Include type/model information: "Blood Pressure Monitor - Automatic"
- Be specific about size/fit: "Compression Stockings - Large"

### Device Instructions
- Be specific for the patient: "Use for daily walks, especially stairs"
- Include safety notes: "Check brakes before each use"
- Include care instructions: "Wash hands before using monitor"
- Include frequency: "Check BP daily at 8 AM"

### Device Priorities
- `high` - Safety-critical (walkers, fall prevention equipment)
- `normal` - Regular monitoring/support (BP monitors, compression wear)
- `low` - Optional/comfort items

### Inventory Management
- Keep serial numbers accurate for tracking
- Update status as devices move through patient care
- Mark maintenance status clearly
- Document device returns and refurbishment

## Access Control

| Operation | Doctor | Nurse |
|-----------|--------|-------|
| Create device | ✅ | ❌ |
| List devices | ✅ | ✅ |
| Update status | ✅ | ❌ |
| View analytics | ✅ | ✅ |
| Add to Rx | ✅ | ❌ |
| Remove from Rx | ✅ | ❌ |

## Integration with Workflow

```
Create Device → Create Prescription → Add Devices → Sign Rx →
Schedule Intervention → Nurse Logs Delivery → Track Usage
```

Each step links medications and devices in a unified prescription workflow.

## FAQ

**Q: Can I prescribe the same device multiple times?**
A: Yes! Quantity field allows prescribing multiple units (e.g., 2 pairs of compression stockings).

**Q: Can I change the device list after signing?**
A: Prescriptions are locked once signed. Create a new prescription if changes needed.

**Q: How do I track device returns?**
A: Use device status field - mark as "returned" when patient returns it.

**Q: Can multiple patients use the same device?**
A: Yes, update device status from patient 1 to patient 2 via new prescription.

**Q: What if a device needs repair?**
A: Mark status as "maintenance". Update back to "available" when ready.

## Related Documentation

- **V0_FEATURES.md** - Complete feature reference
- **README.md** - Quick start guide
- **SECURITY_CONFIG.md** - Production security setup

---

**Last Updated:** March 1, 2026
**Version:** V0
**Status:** ✅ Production Ready
