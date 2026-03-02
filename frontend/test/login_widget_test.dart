import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:frontend/screens/auth/login_screen.dart';
import 'package:frontend/providers/auth_provider.dart';

// Simple mock for testing
class MockAuthProvider extends ChangeNotifier implements AuthProvider {
  @override
  bool isLoading = false;
  @override
  String? error;
  @override
  bool isAuthenticated = false;
  @override
  var currentUser;
  @override
  String? token;

  @override
  Future<bool> login({required String email, required String password}) async =>
      true;
  @override
  Future<void> logout() async {}
  @override
  Future<bool> checkAuth() async => false;
  @override
  void clearError() {}
  @override
  Future<bool> changePassword({
    required String currentPassword,
    required String newPassword,
  }) async => true;
  @override
  Future<bool> updateProfile({String? email, String? fullName}) async => true;
}

void main() {
  testWidgets('Login screen shows essential elements', (
    WidgetTester tester,
  ) async {
    final mockAuth = MockAuthProvider();

    await tester.pumpWidget(
      MaterialApp(
        home: ChangeNotifierProvider<AuthProvider>.value(
          value: mockAuth,
          child: const LoginScreen(),
        ),
      ),
    );

    // Check for the title
    expect(find.text('Assistant Médical IA'), findsOneWidget);

    // Check for email and password fields
    expect(find.byType(TextField), findsNWidgets(2));
    expect(find.text('Email'), findsOneWidget);
    expect(find.text('Mot de passe'), findsOneWidget);

    // Check for login button
    expect(find.text('Se connecter'), findsOneWidget);
    expect(find.byType(ElevatedButton), findsOneWidget);
  });
}
