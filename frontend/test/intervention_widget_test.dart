import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:frontend/screens/intervention_list_screen.dart';
import 'package:frontend/screens/intervention_form_screen.dart';
import 'package:frontend/screens/intervention_completion_screen.dart';
import 'package:frontend/providers/auth_provider.dart';
import 'mocks.dart';

void main() {
  testWidgets('InterventionListScreen shows list of interventions', (
    WidgetTester tester,
  ) async {
    final mockAuth = MockAuthProvider();
    final mockApi = MockApiService();

    await tester.pumpWidget(
      MaterialApp(
        home: ChangeNotifierProvider<AuthProvider>.value(
          value: mockAuth,
          child: InterventionListScreen(
            prescriptionId: 'pre1',
            patientName: 'Jean Dupont',
            userRole: 'doctor',
            apiService: mockApi,
          ),
        ),
      ),
    );

    await tester.pump(); // Start building
    await tester.pump(); // Finish loadInterventions

    expect(find.text('Test sanguin'), findsOneWidget);
    expect(find.text('Suivi tension'), findsOneWidget);
    expect(find.text('Planifiées'), findsAtLeastNWidgets(1));
  });

  testWidgets('InterventionFormScreen validates required fields', (
    WidgetTester tester,
  ) async {
    final mockApi = MockApiService();

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: InterventionFormScreen(
            prescriptionId: 'pre1',
            onCreated: () {},
            apiService: mockApi,
          ),
        ),
      ),
    );

    await tester.tap(find.text("Créer l'intervention"));
    await tester.pump();

    expect(find.text("Le type d'intervention est requis"), findsOneWidget);
  });

  testWidgets(
    'InterventionCompletionScreen shows notes field and submit button',
    (WidgetTester tester) async {
      final mockApi = MockApiService();

      await tester.pumpWidget(
        MaterialApp(
          home: InterventionCompletionScreen(
            interventionId: 'i1',
            onCompleted: () {},
            apiService: mockApi,
          ),
        ),
      );

      expect(find.text("Notes d'intervention"), findsOneWidget);
      expect(find.byType(TextFormField), findsOneWidget);
      expect(find.text('Marquer comme complétée'), findsOneWidget);
    },
  );
}
