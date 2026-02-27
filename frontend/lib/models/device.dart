class Device {
  final String id;
  final String name;
  final String? model;
  final String? serialNumber;
  final String? description;
  final String status;

  Device({
    required this.id,
    required this.name,
    this.model,
    this.serialNumber,
    this.description,
    required this.status,
  });

  factory Device.fromJson(Map<String, dynamic> json) {
    return Device(
      id: json['id'] as String,
      name: json['name'] as String,
      model: json['model'] as String?,
      serialNumber: json['serial_number'] as String?,
      description: json['description'] as String?,
      status: json['status'] as String,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'model': model,
      'serial_number': serialNumber,
      'description': description,
      'status': status,
    };
  }
}

class PrescriptionDevice {
  final String id;
  final String deviceId;
  final String deviceName;
  final String? model;
  final int quantity;
  final String? instructions;
  final String priority;
  final Device? device;

  PrescriptionDevice({
    required this.id,
    required this.deviceId,
    required this.deviceName,
    this.model,
    required this.quantity,
    this.instructions,
    required this.priority,
    this.device,
  });

  factory PrescriptionDevice.fromJson(Map<String, dynamic> json) {
    return PrescriptionDevice(
      id: json['id'] as String,
      deviceId: json['device_id'] as String,
      deviceName: json['device_name'] as String? ?? '',
      model: json['model'] as String?,
      quantity: json['quantity'] as int? ?? 1,
      instructions: json['instructions'] as String?,
      priority: json['priority'] as String? ?? 'normal',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'device_id': deviceId,
      'quantity': quantity,
      'instructions': instructions,
      'priority': priority,
    };
  }
}
