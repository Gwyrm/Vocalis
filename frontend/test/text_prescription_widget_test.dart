import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:frontend/screens/text_prescription_screen.dart';
import 'package:frontend/providers/auth_provider.dart';
import 'package:frontend/models/patient.dart';
import 'mocks.dart';

void main() {
  final testPatient = Patient(
    id: 'p1',
    firstName: 'Jean',
    lastName: 'Dupont',
    dateOfBirth: DateTime(1980, 5, 10),
    allergies: [],
    chronicConditions: [],
    currentMedications: [],
    createdAt: DateTime.now(),
  );

  testWidgets('TextPrescriptionScreen shows error if text is empty', (
    WidgetTester tester,
  ) async {
    final mockAuth = MockAuthProvider();
    final mockApi = MockApiService();

    await tester.pumpWidget(
      MaterialApp(
        home: ChangeNotifierProvider<AuthProvider>.value(
          value: mockAuth,
          child: TextPrescriptionScreen(
            patient: testPatient,
            apiService: mockApi,
          ),
        ),
      ),
    );

    // Click validate without entering text
    await tester.tap(find.text('Valider'));
    await tester.pump();

    expect(find.text('Veuillez entrer une ordonnance'), findsOneWidget);
  });

  testWidgets(
    'TextPrescriptionScreen contains recommended format instructions',
    (WidgetTester tester) async {
      final mockAuth = MockAuthProvider();
      final mockApi = MockApiService();

      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthProvider>.value(
            value: mockAuth,
            child: TextPrescriptionScreen(
              patient: testPatient,
              apiService: mockApi,
            ),
          ),
        ),
      );

      expect(find.text('Format recommandé:'), findsOneWidget);
      expect(find.text('Patient: Nom complet'), findsOneWidget);
    },
  );
}
