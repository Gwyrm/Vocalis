import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:frontend/screens/patient_list_screen.dart';
import 'package:frontend/providers/auth_provider.dart';
import 'mocks.dart';

void main() {
  testWidgets('PatientListScreen shows loading indicator initially', (
    WidgetTester tester,
  ) async {
    final mockAuth = MockAuthProvider();
    final mockApi = MockApiService();

    await tester.pumpWidget(
      MaterialApp(
        home: ChangeNotifierProvider<AuthProvider>.value(
          value: mockAuth,
          child: PatientListScreen(apiService: mockApi),
        ),
      ),
    );

    expect(find.byType(CircularProgressIndicator), findsOneWidget);
  });

  testWidgets('PatientListScreen shows list of patients when data is loaded', (
    WidgetTester tester,
  ) async {
    final mockAuth = MockAuthProvider();
    final mockApi = MockApiService();

    await tester.pumpWidget(
      MaterialApp(
        home: ChangeNotifierProvider<AuthProvider>.value(
          value: mockAuth,
          child: PatientListScreen(apiService: mockApi),
        ),
      ),
    );

    // Wait for the FutureBuilder to complete
    await tester.pumpAndSettle();

    expect(find.text('Patients'), findsOneWidget);
    expect(find.text('Jean Dupont'), findsOneWidget);
    expect(find.text('Marie Curie'), findsOneWidget);
    expect(find.byType(ListTile), findsNWidgets(2));
  });

  testWidgets('PatientListScreen shows "Ajouter" floating button', (
    WidgetTester tester,
  ) async {
    final mockAuth = MockAuthProvider();
    final mockApi = MockApiService();

    await tester.pumpWidget(
      MaterialApp(
        home: ChangeNotifierProvider<AuthProvider>.value(
          value: mockAuth,
          child: PatientListScreen(apiService: mockApi),
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Ajouter'), findsOneWidget);
    expect(find.byType(FloatingActionButton), findsOneWidget);
  });
}
