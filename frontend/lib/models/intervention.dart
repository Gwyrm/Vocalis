/// Models for intervention scheduling and tracking

import 'package:intl/intl.dart';

class Intervention {
  final String id;
  final String prescriptionId;
  final String interventionType;
  final String? description;
  final DateTime scheduledDate;
  final String priority;
  final String status;
  final String createdBy;
  final DateTime createdAt;
  final DateTime updatedAt;

  Intervention({
    required this.id,
    required this.prescriptionId,
    required this.interventionType,
    this.description,
    required this.scheduledDate,
    required this.priority,
    required this.status,
    required this.createdBy,
    required this.createdAt,
    required this.updatedAt,
  });

  factory Intervention.fromJson(Map<String, dynamic> json) {
    return Intervention(
      id: json['id'] as String? ?? '',
      prescriptionId: json['prescription_id'] as String? ?? '',
      interventionType: json['intervention_type'] as String? ?? '',
      description: json['description'] as String?,
      scheduledDate: json['scheduled_date'] != null ? DateTime.parse(json['scheduled_date'] as String) : DateTime.now(),
      priority: json['priority'] as String? ?? 'normal',
      status: json['status'] as String? ?? 'scheduled',
      createdBy: json['created_by'] as String? ?? 'unknown',
      createdAt: json['created_at'] != null ? DateTime.parse(json['created_at'] as String) : DateTime.now(),
      updatedAt: json['updated_at'] != null ? DateTime.parse(json['updated_at'] as String) : DateTime.now(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'prescription_id': prescriptionId,
      'intervention_type': interventionType,
      'description': description,
      'scheduled_date': scheduledDate.toIso8601String(),
      'priority': priority,
      'status': status,
      'created_by': createdBy,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
    };
  }

  String get statusDisplayName {
    switch (status) {
      case 'scheduled':
        return 'Planifiée';
      case 'in_progress':
        return 'En cours';
      case 'completed':
        return 'Complétée';
      case 'cancelled':
        return 'Annulée';
      default:
        return status;
    }
  }

  String get priorityDisplayName {
    switch (priority) {
      case 'low':
        return 'Basse';
      case 'normal':
        return 'Normale';
      case 'high':
        return 'Haute';
      default:
        return priority;
    }
  }

  String get formattedScheduledDate {
    return DateFormat('dd/MM/yyyy HH:mm').format(scheduledDate);
  }
}

class InterventionLog {
  final String id;
  final String interventionId;
  final String loggedBy;
  final String statusChange;
  final String? notes;
  final DateTime loggedAt;

  InterventionLog({
    required this.id,
    required this.interventionId,
    required this.loggedBy,
    required this.statusChange,
    this.notes,
    required this.loggedAt,
  });

  factory InterventionLog.fromJson(Map<String, dynamic> json) {
    return InterventionLog(
      id: json['id'] as String? ?? '',
      interventionId: json['intervention_id'] as String? ?? '',
      loggedBy: json['logged_by'] as String? ?? 'unknown',
      statusChange: json['status_change'] as String? ?? '',
      notes: json['notes'] as String?,
      loggedAt: json['logged_at'] != null ? DateTime.parse(json['logged_at'] as String) : DateTime.now(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'intervention_id': interventionId,
      'logged_by': loggedBy,
      'status_change': statusChange,
      'notes': notes,
      'logged_at': loggedAt.toIso8601String(),
    };
  }

  String get formattedLoggedAt {
    return DateFormat('dd/MM/yyyy HH:mm').format(loggedAt);
  }
}

class InterventionDocument {
  final String id;
  final String logId;
  final String documentType;
  final String fileName;
  final String filePath;
  final String? mimeType;
  final int? fileSize;
  final String? caption;
  final DateTime uploadedAt;

  InterventionDocument({
    required this.id,
    required this.logId,
    required this.documentType,
    required this.fileName,
    required this.filePath,
    this.mimeType,
    this.fileSize,
    this.caption,
    required this.uploadedAt,
  });

  factory InterventionDocument.fromJson(Map<String, dynamic> json) {
    return InterventionDocument(
      id: json['id'] as String? ?? '',
      logId: json['log_id'] as String? ?? '',
      documentType: json['document_type'] as String? ?? 'other',
      fileName: json['file_name'] as String? ?? 'document',
      filePath: json['file_path'] as String? ?? '',
      mimeType: json['mime_type'] as String?,
      fileSize: json['file_size'] as int?,
      caption: json['caption'] as String?,
      uploadedAt: json['uploaded_at'] != null ? DateTime.parse(json['uploaded_at'] as String) : DateTime.now(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'log_id': logId,
      'document_type': documentType,
      'file_name': fileName,
      'file_path': filePath,
      'mime_type': mimeType,
      'file_size': fileSize,
      'caption': caption,
      'uploaded_at': uploadedAt.toIso8601String(),
    };
  }

  String get documentTypeDisplayName {
    switch (documentType) {
      case 'note':
        return 'Note';
      case 'photo':
        return 'Photo';
      case 'result':
        return 'Résultat';
      case 'other':
        return 'Autre';
      default:
        return documentType;
    }
  }

  String get formattedFileSize {
    if (fileSize == null) return '';
    if (fileSize! < 1024) return '$fileSize B';
    if (fileSize! < 1024 * 1024) return '${(fileSize! / 1024).toStringAsFixed(1)} KB';
    return '${(fileSize! / (1024 * 1024)).toStringAsFixed(1)} MB';
  }

  String get formattedUploadedAt {
    return DateFormat('dd/MM/yyyy HH:mm').format(uploadedAt);
  }
}

class InterventionDetail {
  final String id;
  final String prescriptionId;
  final String interventionType;
  final String? description;
  final DateTime scheduledDate;
  final String priority;
  final String status;
  final String createdBy;
  final DateTime createdAt;
  final DateTime updatedAt;
  final List<InterventionLog> logs;

  InterventionDetail({
    required this.id,
    required this.prescriptionId,
    required this.interventionType,
    this.description,
    required this.scheduledDate,
    required this.priority,
    required this.status,
    required this.createdBy,
    required this.createdAt,
    required this.updatedAt,
    required this.logs,
  });

  factory InterventionDetail.fromJson(Map<String, dynamic> json) {
    var logsJson = json['logs'] as List? ?? [];
    return InterventionDetail(
      id: json['id'] as String? ?? '',
      prescriptionId: json['prescription_id'] as String? ?? '',
      interventionType: json['intervention_type'] as String? ?? '',
      description: json['description'] as String?,
      scheduledDate: json['scheduled_date'] != null ? DateTime.parse(json['scheduled_date'] as String) : DateTime.now(),
      priority: json['priority'] as String? ?? 'normal',
      status: json['status'] as String? ?? 'scheduled',
      createdBy: json['created_by'] as String? ?? 'unknown',
      createdAt: json['created_at'] != null ? DateTime.parse(json['created_at'] as String) : DateTime.now(),
      updatedAt: json['updated_at'] != null ? DateTime.parse(json['updated_at'] as String) : DateTime.now(),
      logs: logsJson.map((log) => InterventionLog.fromJson(log as Map<String, dynamic>)).toList(),
    );
  }

  String get statusDisplayName {
    switch (status) {
      case 'scheduled':
        return 'Planifiée';
      case 'in_progress':
        return 'En cours';
      case 'completed':
        return 'Complétée';
      case 'cancelled':
        return 'Annulée';
      default:
        return status;
    }
  }

  String get priorityDisplayName {
    switch (priority) {
      case 'low':
        return 'Basse';
      case 'normal':
        return 'Normale';
      case 'high':
        return 'Haute';
      default:
        return priority;
    }
  }

  String get formattedScheduledDate {
    return DateFormat('dd/MM/yyyy HH:mm').format(scheduledDate);
  }
}
