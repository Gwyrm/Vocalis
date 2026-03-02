import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:frontend/screens/profile_screen.dart';
import 'package:frontend/providers/auth_provider.dart';
import 'mocks.dart';

void main() {
  testWidgets('ProfileScreen shows user information', (
    WidgetTester tester,
  ) async {
    final mockAuth = MockAuthProvider();

    await tester.pumpWidget(
      MaterialApp(
        home: ChangeNotifierProvider<AuthProvider>.value(
          value: mockAuth,
          child: const ProfileScreen(),
        ),
      ),
    );

    expect(find.text('test@vocalis.com'), findsOneWidget);
    expect(find.text('Test Doctor'), findsOneWidget);
    expect(find.text('doctor'), findsAtLeastNWidgets(1));
    expect(find.text('Mettre à jour le profil'), findsOneWidget);
  });
}
