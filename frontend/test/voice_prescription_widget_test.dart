import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:frontend/screens/voice_prescription_screen.dart';
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

  testWidgets('VoicePrescriptionScreen shows patient name and instructions', (
    WidgetTester tester,
  ) async {
    final mockAuth = MockAuthProvider();
    final mockApi = MockApiService();

    await tester.pumpWidget(
      MaterialApp(
        home: ChangeNotifierProvider<AuthProvider>.value(
          value: mockAuth,
          child: VoicePrescriptionScreen(
            patient: testPatient,
            apiService: mockApi,
          ),
        ),
      ),
    );

    expect(
      find.textContaining('Jean Dupont'),
      findsNWidgets(2),
    ); // AppBar and Title
    expect(find.text('Instructions:'), findsOneWidget);
    expect(find.text('1. Appuyez sur le micro pour commencer'), findsOneWidget);
  });

  testWidgets('VoicePrescriptionScreen shows mic icon initially', (
    WidgetTester tester,
  ) async {
    final mockAuth = MockAuthProvider();
    final mockApi = MockApiService();

    await tester.pumpWidget(
      MaterialApp(
        home: ChangeNotifierProvider<AuthProvider>.value(
          value: mockAuth,
          child: VoicePrescriptionScreen(
            patient: testPatient,
            apiService: mockApi,
          ),
        ),
      ),
    );

    expect(find.byIcon(Icons.mic), findsOneWidget);
    expect(find.text('Appuyez pour enregistrer'), findsOneWidget);
  });
}
