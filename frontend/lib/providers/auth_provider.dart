import 'package:flutter/material.dart';
import '../models/auth.dart';
import '../services/auth_service.dart';

class AuthProvider with ChangeNotifier {
  final AuthService _authService = AuthService();

  CurrentUser? _currentUser;
  String? _token;
  bool _isLoading = false;
  String? _error;

  // Getters
  CurrentUser? get currentUser => _currentUser;
  String? get token => _token;
  bool get isLoading => _isLoading;
  String? get error => _error;
  bool get isAuthenticated => _token != null && _token!.isNotEmpty;

  AuthProvider() {
    _init();
  }

  /// Initialize auth state from saved data
  Future<void> _init() async {
    _token = await _authService.getToken();
    _currentUser = await _authService.getCurrentUser();
    notifyListeners();
  }

  /// Login with email and password
  Future<bool> login({
    required String email,
    required String password,
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final authResponse = await _authService.login(
        email: email,
        password: password,
      );
      _token = authResponse.accessToken;
      _currentUser = authResponse.user;
      _isLoading = false;
      _error = null;
      notifyListeners();
      return true;
    } catch (e) {
      _isLoading = false;
      _error = e.toString().replaceAll('Exception: ', '');
      notifyListeners();
      return false;
    }
  }

  /// Demo login
  Future<bool> loginDemo() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final authResponse = await _authService.loginDemo();
      _token = authResponse.accessToken;
      _currentUser = authResponse.user;
      _isLoading = false;
      _error = null;
      notifyListeners();
      return true;
    } catch (e) {
      _isLoading = false;
      _error = e.toString().replaceAll('Exception: ', '');
      notifyListeners();
      return false;
    }
  }

  /// Logout
  Future<void> logout() async {
    await _authService.logout();
    _token = null;
    _currentUser = null;
    _error = null;
    notifyListeners();
  }

  /// Check authentication status (for splash screen)
  Future<bool> checkAuth() async {
    _token = await _authService.getToken();
    _currentUser = await _authService.getCurrentUser();
    notifyListeners();
    return isAuthenticated;
  }

  /// Clear error message
  void clearError() {
    _error = null;
    notifyListeners();
  }

  /// Update user profile (email and full_name)
  Future<bool> updateProfile({
    String? email,
    String? fullName,
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final updatedUser = await _authService.updateProfile(
        email: email,
        fullName: fullName,
        token: _token!,
      );
      _currentUser = updatedUser;
      _isLoading = false;
      _error = null;
      notifyListeners();
      return true;
    } catch (e) {
      _isLoading = false;
      _error = e.toString().replaceAll('Exception: ', '');
      notifyListeners();
      return false;
    }
  }

  /// Change user password
  Future<bool> changePassword({
    required String currentPassword,
    required String newPassword,
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      await _authService.changePassword(
        currentPassword: currentPassword,
        newPassword: newPassword,
        token: _token!,
      );
      _isLoading = false;
      _error = null;
      notifyListeners();
      return true;
    } catch (e) {
      _isLoading = false;
      _error = e.toString().replaceAll('Exception: ', '');
      notifyListeners();
      return false;
    }
  }
}
