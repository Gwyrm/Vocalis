import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/screens/edit_prescription_screen.dart';
import 'package:frontend/models/patient.dart';
import 'package:frontend/models/prescription.dart';
import 'mocks.dart';

void main() {
  testWidgets('EditPrescriptionScreen shows pre-filled fields', (
    WidgetTester tester,
  ) async {
    final mockApi = MockApiService();
    final patient = Patient(
      id: 'p1',
      firstName: 'Jean',
      lastName: 'Dupont',
      dateOfBirth: DateTime(1980, 1, 1),
      gender: 'M',
      allergies: [],
      chronicConditions: [],
      currentMedications: [],
      createdAt: DateTime.now(),
    );
    final prescription = Prescription(
      id: 'pre1',
      patientName: 'Jean Dupont',
      patientAge: '44',
      diagnosis: 'Asthme',
      medication: 'Ventoline',
      dosage: '1 bouffée',
      duration: 'Selon besoin',
      createdAt: DateTime.now(),
      createdBy: 'd1',
      status: 'active',
    );

    await tester.pumpWidget(
      MaterialApp(
        home: EditPrescriptionScreen(
          prescription: prescription,
          patient: patient,
          apiService: mockApi,
        ),
      ),
    );

    expect(find.text('Ventoline'), findsOneWidget);
    expect(find.text('1 bouffée'), findsOneWidget);
    expect(find.text('Asthme'), findsOneWidget);
  });
}
