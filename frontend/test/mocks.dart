import 'package:flutter/material.dart';
import 'package:frontend/providers/auth_provider.dart';
import 'package:frontend/api_service.dart';
import 'package:frontend/models/auth.dart';
import 'package:frontend/models/patient.dart';
import 'package:frontend/models/prescription.dart';
import 'dart:typed_data';

class MockAuthProvider extends ChangeNotifier implements AuthProvider {
  @override
  bool isLoading = false;
  @override
  String? error;
  @override
  bool isAuthenticated = true;
  @override
  CurrentUser? currentUser = CurrentUser(
    id: 'user-1',
    email: 'test@vocalis.com',
    fullName: 'Test Doctor',
    role: 'doctor',
    organizationId: 'org-1',
  );
  @override
  String? token = 'mock-token';

  @override
  Future<bool> login({required String email, required String password}) async =>
      true;
  @override
  Future<void> logout() async {
    isAuthenticated = false;
    currentUser = null;
    token = null;
    notifyListeners();
  }

  @override
  Future<bool> checkAuth() async => true;
  @override
  void clearError() {
    error = null;
    notifyListeners();
  }

  @override
  Future<bool> changePassword({
    required String currentPassword,
    required String newPassword,
  }) async => true;
  @override
  Future<bool> updateProfile({String? email, String? fullName}) async => true;
}

class MockApiService implements ApiService {
  @override
  String get baseUrl => 'http://mock';

  @override
  void setToken(String token) {}
  @override
  void setOnAuthError(Function callback) {}

  @override
  Future<List<Patient>> getPatients() async {
    return [
      Patient(
        id: 'p1',
        firstName: 'Jean',
        lastName: 'Dupont',
        dateOfBirth: DateTime(1980, 5, 10),
        allergies: ['Pénicilline'],
        chronicConditions: ['Asthme'],
        currentMedications: [],
        createdAt: DateTime.now(),
      ),
      Patient(
        id: 'p2',
        firstName: 'Marie',
        lastName: 'Curie',
        dateOfBirth: DateTime(1990, 11, 7),
        allergies: [],
        chronicConditions: [],
        currentMedications: [],
        createdAt: DateTime.now(),
      ),
    ];
  }

  @override
  Future<Patient> getPatient(String id) async {
    return Patient(
      id: id,
      firstName: 'Test',
      lastName: 'Patient',
      dateOfBirth: DateTime(1985, 1, 1),
      allergies: [],
      chronicConditions: [],
      currentMedications: [],
      createdAt: DateTime.now(),
    );
  }

  @override
  Future<Patient> createPatient({
    required String firstName,
    required String lastName,
    required DateTime dateOfBirth,
    String? gender,
    String? phone,
    String? email,
    String? address,
    List<String>? allergies,
    List<String>? chronicConditions,
    List<String>? currentMedications,
    String? medicalNotes,
  }) async {
    return Patient(
      id: 'new-id',
      firstName: firstName,
      lastName: lastName,
      dateOfBirth: dateOfBirth,
      allergies: allergies ?? [],
      chronicConditions: chronicConditions ?? [],
      currentMedications: currentMedications ?? [],
      createdAt: DateTime.now(),
    );
  }

  @override
  Future<Patient> updatePatient(
    String id, {
    String? firstName,
    String? lastName,
    String? gender,
    String? phone,
    String? email,
    String? address,
    List<String>? allergies,
    List<String>? chronicConditions,
    List<String>? currentMedications,
    String? medicalNotes,
  }) async {
    return Patient(
      id: id,
      firstName: firstName ?? 'Edited',
      lastName: lastName ?? 'Patient',
      dateOfBirth: DateTime(1980, 1, 1),
      allergies: [],
      chronicConditions: [],
      currentMedications: [],
      createdAt: DateTime.now(),
    );
  }

  @override
  Future<List<Prescription>> getPatientPrescriptions(String patientId) async =>
      [];

  @override
  Future<TranscriptionResult> transcribeAudio(List<int> bytes) async =>
      PrescriptionStub.transcriptionResult();

  @override
  Future<PrescriptionValidationResponse> createVoicePrescription({
    required String patientId,
    required List<int> audioBytes,
  }) async {
    return PrescriptionStub.validationResponse();
  }

  @override
  Future<PrescriptionValidationResponse> createTextPrescription({
    required String patientId,
    required String prescriptionText,
  }) async {
    return PrescriptionStub.validationResponse();
  }

  @override
  Future<Map<String, dynamic>> chat(String message) async => {
    'response': 'Mock AI response',
  };

  @override
  Future<Uint8List> generatePdf(String signature) async => Uint8List(0);

  @override
  Future<List<dynamic>> getDevices() async => [];
  @override
  Future<void> assignDeviceToPrescription(
    String pId,
    String dId,
    int q,
    String? i,
    String pr,
  ) async {}
  @override
  Future<void> removeDeviceFromPrescription(String pId, String dId) async {}
  @override
  Future<List<dynamic>> getPatientVisits() async {
    return [
      {
        'id': 'v1',
        'patient_name': 'Jean Dupont',
        'patient_address': '123 Rue de Paris',
        'status': 'pending',
        'scheduled_date': DateTime.now().toIso8601String(),
        'diagnosis': 'Asthme',
      },
      {
        'id': 'v2',
        'patient_name': 'Marie Curie',
        'patient_address': '456 Ave des Sciences',
        'status': 'in_progress',
        'scheduled_date': DateTime.now().toIso8601String(),
        'diagnosis': 'Infection',
      },
    ];
  }

  @override
  Future<Map<String, dynamic>> getVisitDetails(String id) async {
    return {
      'id': id,
      'patient_name': 'Jean Dupont',
      'patient_address': '123 Rue de Paris',
      'status': 'pending',
      'scheduled_date': DateTime.now().toIso8601String(),
      'prescription_id': 'pre1',
    };
  }

  @override
  Future<void> updateVisitStatus(String id, String s) async {}

  @override
  Future<List<dynamic>> getPrescriptionDevices(String pId) async {
    return [
      {
        'id': 'd1',
        'device_name': 'Oxygène',
        'quantity': 1,
        'instructions': '2L/min',
        'priority': 'high',
      },
    ];
  }

  @override
  Future<void> completeDeviceDelivery(
    String vId,
    String s,
    String n,
    String? p,
  ) async {}
  @override
  Future<Prescription> signPrescription(String id, String sig) async =>
      PrescriptionStub.prescription(id);
  @override
  Future<Prescription> updatePrescription(
    String id, {
    String? medication,
    String? dosage,
    String? duration,
    String? diagnosis,
    String? specialInstructions,
  }) async => PrescriptionStub.prescription(id);
  @override
  Future<List<Map<String, dynamic>>> getInterventions({
    String? prescriptionId,
    String? status,
  }) async {
    return [
      {
        'id': 'i1',
        'prescription_id': 'pre1',
        'intervention_type': 'Test sanguin',
        'description': 'Vérifier la glycémie',
        'scheduled_date': DateTime.now()
            .add(const Duration(days: 1))
            .toIso8601String(),
        'priority': 'normal',
        'status': 'scheduled',
        'created_at': DateTime.now().toIso8601String(),
      },
      {
        'id': 'i2',
        'prescription_id': 'pre1',
        'intervention_type': 'Suivi tension',
        'description': 'Prise de tension trijournalière',
        'scheduled_date': DateTime.now().toIso8601String(),
        'priority': 'high',
        'status': 'in_progress',
        'created_at': DateTime.now().toIso8601String(),
      },
    ];
  }

  @override
  Future<Map<String, dynamic>> createIntervention({
    required String prescriptionId,
    required String interventionType,
    String? description,
    required DateTime scheduledDate,
    String priority = 'normal',
  }) async {
    return {
      'id': 'new-i',
      'prescription_id': prescriptionId,
      'intervention_type': interventionType,
      'status': 'scheduled',
    };
  }

  @override
  Future<Map<String, dynamic>> getIntervention(String id) async => {};
  @override
  Future<Map<String, dynamic>> updateIntervention(
    String id, {
    String? interventionType,
    String? description,
    DateTime? scheduledDate,
    String? priority,
    String? status,
  }) async => {};
  @override
  Future<void> deleteIntervention(String id) async {}
  @override
  Future<Map<String, dynamic>> logIntervention(
    String id, {
    required String statusChange,
    String? notes,
  }) async {
    return {'status': 'success'};
  }

  @override
  Future<List<Map<String, dynamic>>> getInterventionLogs(String id) async => [];
  @override
  Future<Map<String, dynamic>> uploadInterventionDocument(
    String id, {
    required dynamic file,
    String documentType = 'note',
    String? caption,
    String? logId,
  }) async => {};
  @override
  Future<List<Map<String, dynamic>>> getInterventionDocuments(
    String id,
  ) async => [];
}

class PrescriptionStub {
  static Prescription prescription(String id) => Prescription(
    id: id,
    patientName: 'Jean Dupont',
    patientAge: '45',
    diagnosis: 'Asthme',
    medication: 'Ventoline',
    dosage: '1 bouffée',
    duration: '7 jours',
    status: 'active',
    createdBy: 'doctor',
    createdAt: DateTime.now(),
  );

  static PrescriptionValidation validation() => PrescriptionValidation(
    valid: true,
    confidence: 0.9,
    warnings: [],
    errors: [],
  );

  static PrescriptionValidationResponse validationResponse() =>
      PrescriptionValidationResponse(
        prescription: prescription('p1'),
        validation: validation(),
        patientSummary: {},
      );

  static TranscriptionResult transcriptionResult() => TranscriptionResult(
    text: 'Mock transcription',
    confidence: 0.95,
    language: 'fr',
  );
}
