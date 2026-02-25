class ValidationWarning {
  final String type;
  final String message;
  final String severity; // low, medium, high

  ValidationWarning({
    required this.type,
    required this.message,
    required this.severity,
  });

  factory ValidationWarning.fromJson(Map<String, dynamic> json) {
    return ValidationWarning(
      type: json['type'] as String,
      message: json['message'] as String,
      severity: json['severity'] as String,
    );
  }
}

class ValidationError {
  final String type;
  final String message;
  final String? field;

  ValidationError({
    required this.type,
    required this.message,
    this.field,
  });

  factory ValidationError.fromJson(Map<String, dynamic> json) {
    return ValidationError(
      type: json['type'] as String,
      message: json['message'] as String,
      field: json['field'] as String?,
    );
  }
}

class PrescriptionValidation {
  final bool valid;
  final double confidence;
  final List<ValidationWarning> warnings;
  final List<ValidationError> errors;

  PrescriptionValidation({
    required this.valid,
    required this.confidence,
    required this.warnings,
    required this.errors,
  });

  factory PrescriptionValidation.fromJson(Map<String, dynamic> json) {
    return PrescriptionValidation(
      valid: json['valid'] as bool,
      confidence: (json['confidence'] as num).toDouble(),
      warnings: (json['warnings'] as List?)
          ?.map((w) => ValidationWarning.fromJson(w as Map<String, dynamic>))
          .toList() ??
          [],
      errors: (json['errors'] as List?)
          ?.map((e) => ValidationError.fromJson(e as Map<String, dynamic>))
          .toList() ??
          [],
    );
  }
}

class Prescription {
  final String id;
  final String patientName;
  final String patientAge;
  final String diagnosis;
  final String medication;
  final String dosage;
  final String duration;
  final String? specialInstructions;
  final String status;
  final String createdBy;
  final DateTime createdAt;

  Prescription({
    required this.id,
    required this.patientName,
    required this.patientAge,
    required this.diagnosis,
    required this.medication,
    required this.dosage,
    required this.duration,
    this.specialInstructions,
    required this.status,
    required this.createdBy,
    required this.createdAt,
  });

  factory Prescription.fromJson(Map<String, dynamic> json) {
    return Prescription(
      id: json['id'] as String,
      patientName: json['patient_name'] as String,
      patientAge: json['patient_age'] as String,
      diagnosis: json['diagnosis'] as String,
      medication: json['medication'] as String,
      dosage: json['dosage'] as String,
      duration: json['duration'] as String,
      specialInstructions: json['special_instructions'] as String?,
      status: json['status'] as String,
      createdBy: json['created_by'] as String,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }
}

class TranscriptionResult {
  final String text;
  final double confidence;
  final String language;

  TranscriptionResult({
    required this.text,
    required this.confidence,
    required this.language,
  });

  factory TranscriptionResult.fromJson(Map<String, dynamic> json) {
    return TranscriptionResult(
      text: json['text'] as String,
      confidence: (json['confidence'] as num).toDouble(),
      language: json['language'] as String,
    );
  }
}

class PrescriptionValidationResponse {
  final Prescription? prescription;
  final PrescriptionValidation validation;
  final Map<String, dynamic> patientSummary;
  final Map<String, dynamic>? structuredData;

  PrescriptionValidationResponse({
    required this.prescription,
    required this.validation,
    required this.patientSummary,
    this.structuredData,
  });

  factory PrescriptionValidationResponse.fromJson(Map<String, dynamic> json) {
    return PrescriptionValidationResponse(
      prescription: json['prescription'] != null
          ? Prescription.fromJson(json['prescription'] as Map<String, dynamic>)
          : null,
      validation: PrescriptionValidation.fromJson(
          json['validation'] as Map<String, dynamic>),
      patientSummary: json['patient_summary'] as Map<String, dynamic>,
      structuredData: json['structured_data'] as Map<String, dynamic>?,
    );
  }
}
