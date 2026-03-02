import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:frontend/screens/nurse/nurse_deliveries_screen.dart';
import 'package:frontend/screens/nurse/delivery_detail_screen.dart';
import 'package:frontend/providers/auth_provider.dart';
import 'mocks.dart';

void main() {
  testWidgets('NurseDeliveriesScreen shows list of deliveries', (
    WidgetTester tester,
  ) async {
    final mockAuth = MockAuthProvider();
    final mockApi = MockApiService();

    await tester.pumpWidget(
      MaterialApp(
        home: ChangeNotifierProvider<AuthProvider>.value(
          value: mockAuth,
          child: NurseDeliveriesScreen(apiService: mockApi),
        ),
      ),
    );

    await tester.pump(); // Start building
    await tester.pump(); // Finish FutureBuilder

    expect(find.text('Jean Dupont'), findsOneWidget);
    expect(find.text('Marie Curie'), findsOneWidget);
    expect(find.text('🔴 En attente'), findsOneWidget);
    expect(find.text('🟠 En cours'), findsOneWidget);
  });

  testWidgets('DeliveryDetailScreen shows delivery details and patient info', (
    WidgetTester tester,
  ) async {
    final mockAuth = MockAuthProvider();
    final mockApi = MockApiService();

    await tester.pumpWidget(
      MaterialApp(
        home: ChangeNotifierProvider<AuthProvider>.value(
          value: mockAuth,
          child: DeliveryDetailScreen(deliveryId: 'v1', apiService: mockApi),
        ),
      ),
    );

    await tester.pump(); // Start building
    await tester.pump(); // Finish FutureBuilders

    expect(find.text('Jean Dupont'), findsAtLeastNWidgets(1));
    expect(find.text('123 Rue de Paris'), findsOneWidget);
    expect(find.text('Oxygène'), findsOneWidget);
    expect(find.text('Démarrer la Livraison'), findsOneWidget);
  });
}
