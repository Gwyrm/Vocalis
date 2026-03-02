import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:frontend/screens/patient_detail_screen.dart';
import 'package:frontend/providers/auth_provider.dart';
import 'package:frontend/models/patient.dart';
import 'mocks.dart';

void main() {
  final testPatient = Patient(
    id: 'p1',
    firstName: 'Jean',
    lastName: 'Dupont',
    dateOfBirth: DateTime(1980, 5, 10),
    gender: 'M',
    phone: '0612345678',
    email: 'jean@test.com',
    allergies: ['Pénicilline'],
    chronicConditions: ['Asthme', 'Diabète'],
    currentMedications: ['Ventoline'],
    createdAt: DateTime.now(),
  );

  testWidgets('PatientDetailScreen shows correct patient details', (
    WidgetTester tester,
  ) async {
    final mockAuth = MockAuthProvider();
    final mockApi = MockApiService();

    await tester.pumpWidget(
      MaterialApp(
        home: ChangeNotifierProvider<AuthProvider>.value(
          value: mockAuth,
          child: PatientDetailScreen(patient: testPatient, apiService: mockApi),
        ),
      ),
    );

    // Check name and age
    expect(find.text('Jean Dupont'), findsNWidgets(2)); // AppBar and Header
    expect(
      find.textContaining('45 ans'),
      findsOneWidget,
    ); // Depends on current year (2025/2026)

    // Check contact info
    expect(find.text('0612345678'), findsOneWidget);
    expect(find.text('jean@test.com'), findsOneWidget);

    // Check medical info
    expect(find.text('Allergies'), findsOneWidget);
    expect(find.text('Pénicilline'), findsOneWidget);
    expect(find.text('Asthme'), findsOneWidget);
    expect(find.text('Diabète'), findsOneWidget);
  });

  testWidgets('PatientDetailScreen shows prescription action buttons', (
    WidgetTester tester,
  ) async {
    final mockAuth = MockAuthProvider();
    final mockApi = MockApiService();

    await tester.pumpWidget(
      MaterialApp(
        home: ChangeNotifierProvider<AuthProvider>.value(
          value: mockAuth,
          child: PatientDetailScreen(patient: testPatient, apiService: mockApi),
        ),
      ),
    );

    expect(find.text('Créer une ordonnance'), findsOneWidget);
    expect(find.text('Voix'), findsOneWidget);
    expect(find.text('Texte'), findsOneWidget);
  });
}
