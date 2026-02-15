import 'package:flutter/foundation.dart';

class PrescriptionData {
  String? patientName;
  String? patientAge;
  String? diagnosis;
  String? medication;
  String? dosage;
  String? duration;
  String? specialInstructions;

  PrescriptionData({
    this.patientName,
    this.patientAge,
    this.diagnosis,
    this.medication,
    this.dosage,
    this.duration,
    this.specialInstructions,
  });

  /// Get list of missing required fields in French
  List<String> getMissingRequiredFields() {
    final required = [
      ('patientName', 'Nom du patient'),
      ('patientAge', 'Âge/Date de naissance'),
      ('diagnosis', 'Diagnostic'),
      ('medication', 'Médicament'),
      ('dosage', 'Posologie'),
      ('duration', 'Durée du traitement'),
      ('specialInstructions', 'Instructions spéciales'),
    ];

    final missing = <String>[];
    for (final (field, label) in required) {
      final value = _getFieldValue(field);
      if (value == null || value.isEmpty) {
        missing.add(label);
      }
    }
    return missing;
  }

  /// Check if all required fields are present
  bool isComplete() {
    return getMissingRequiredFields().isEmpty;
  }

  /// Get a field value by name
  String? _getFieldValue(String fieldName) {
    switch (fieldName) {
      case 'patientName':
        return patientName;
      case 'patientAge':
        return patientAge;
      case 'diagnosis':
        return diagnosis;
      case 'medication':
        return medication;
      case 'dosage':
        return dosage;
      case 'duration':
        return duration;
      case 'specialInstructions':
        return specialInstructions;
      default:
        return null;
    }
  }

  /// Convert to JSON
  Map<String, dynamic> toJson() {
    return {
      'patientName': patientName,
      'patientAge': patientAge,
      'diagnosis': diagnosis,
      'medication': medication,
      'dosage': dosage,
      'duration': duration,
      'specialInstructions': specialInstructions,
    };
  }

  /// Create from JSON
  static PrescriptionData fromJson(Map<String, dynamic> json) {
    return PrescriptionData(
      patientName: json['patientName'],
      patientAge: json['patientAge'],
      diagnosis: json['diagnosis'],
      medication: json['medication'],
      dosage: json['dosage'],
      duration: json['duration'],
      specialInstructions: json['specialInstructions'],
    );
  }

  /// Create a copy with updated fields
  PrescriptionData copyWith({
    String? patientName,
    String? patientAge,
    String? diagnosis,
    String? medication,
    String? dosage,
    String? duration,
    String? specialInstructions,
  }) {
    return PrescriptionData(
      patientName: patientName ?? this.patientName,
      patientAge: patientAge ?? this.patientAge,
      diagnosis: diagnosis ?? this.diagnosis,
      medication: medication ?? this.medication,
      dosage: dosage ?? this.dosage,
      duration: duration ?? this.duration,
      specialInstructions: specialInstructions ?? this.specialInstructions,
    );
  }
}
