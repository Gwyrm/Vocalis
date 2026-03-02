import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/models/patient.dart';
import 'package:frontend/models/prescription.dart';
import 'package:frontend/models/auth.dart';

void main() {
  group('Patient Model Tests', () {
    final patientJson = {
      'id': 'p1',
      'first_name': 'Jean',
      'last_name': 'Dupont',
      'date_of_birth': '1980-05-10',
      'gender': 'M',
      'phone': '0612345678',
      'email': 'jean@test.com',
      'address': '123 Rue de Paris',
      'allergies': ['Pénicilline'],
      'chronic_conditions': ['Asthme'],
      'current_medications': ['Ventoline'],
      'medical_notes': 'Stable',
      'created_at': '2023-01-01T10:00:00Z',
    };

    test('Patient.fromJson parses correctly', () {
      final patient = Patient.fromJson(patientJson);
      expect(patient.id, 'p1');
      expect(patient.firstName, 'Jean');
      expect(patient.fullName, 'Jean Dupont');
      expect(patient.allergies, contains('Pénicilline'));
    });

    test('Patient.ageInYears calculates correctly', () {
      // Assuming today is 2025 or 2026 for the test environment
      final patient = Patient.fromJson(patientJson);
      final age = patient.ageInYears;
      // 2025-1980 = 45 or 2026-1980 = 46
      expect(age, anyOf(44, 45, 46));
    });

    test('Patient.toJson generates correct map', () {
      final patient = Patient.fromJson(patientJson);
      final json = patient.toJson();
      expect(json['first_name'], 'Jean');
      expect(json['date_of_birth'], '1980-05-10');
    });
  });

  group('Prescription Model Tests', () {
    final prescriptionJson = {
      'id': 'pre1',
      'patient_name': 'Jean Dupont',
      'patient_age': '45',
      'diagnosis': 'Infection',
      'medication': 'Amoxicilline',
      'dosage': '1g x 3/jour',
      'duration': '7 jours',
      'status': 'active',
      'created_by': 'doctor@test.fr',
      'created_at': '2023-01-01T10:00:00Z',
      'is_signed': true,
      'doctor_signed_at': '2023-01-01T10:05:00Z',
    };

    test('Prescription.fromJson parses correctly', () {
      final prescription = Prescription.fromJson(prescriptionJson);
      expect(prescription.id, 'pre1');
      expect(prescription.medication, 'Amoxicilline');
      expect(prescription.isSigned, isTrue);
    });
  });

  group('Auth Model Tests', () {
    test('CurrentUser.isDoctor identifies roles correctly', () {
      final user = CurrentUser(
        id: 'u1',
        email: 'doc@test.fr',
        role: 'doctor',
        organizationId: 'org1',
      );
      expect(user.isDoctor(), isTrue);
      expect(user.isNurse(), isFalse);
    });

    test('AuthResponse.fromJson parses correctly', () {
      final responseJson = {
        'access_token': 'secret-token',
        'token_type': 'bearer',
        'user': {
          'id': 'u1',
          'email': 'nurse@test.fr',
          'role': 'nurse',
          'org_id': 'org1',
        },
      };
      final response = AuthResponse.fromJson(responseJson);
      expect(response.accessToken, 'secret-token');
      expect(response.user.isNurse(), isTrue);
    });
  });
}
