import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter/foundation.dart';
import '../models/auth.dart';

class AuthService {
  static const String _tokenKey = 'vocalis_auth_token';
  static const String _userKey = 'vocalis_current_user';
  static const String _envBaseUrl = String.fromEnvironment('API_URL');
  static const String _baseUrlLocal = 'http://127.0.0.1:8080';

  String get baseUrl {
    if (_envBaseUrl.isNotEmpty) return _envBaseUrl;
    if (kIsWeb) {
      final origin = Uri.base.origin;
      if (origin.contains('localhost') || origin.contains('127.0.0.1')) {
        return _baseUrlLocal;
      }
      return origin;
    }
    return _baseUrlLocal;
  }

  /// Login with email and password
  Future<AuthResponse> login({
    required String email,
    required String password,
  }) async {
    final url = Uri.parse('$baseUrl/api/auth/login');
    try {
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'email': email,
          'password': password,
        }),
      );

      if (response.statusCode == 200) {
        final authResponse = AuthResponse.fromJson(jsonDecode(response.body));
        // Save token and user info
        await _saveAuthData(authResponse);
        return authResponse;
      } else if (response.statusCode == 401) {
        throw Exception('Email ou mot de passe incorrect');
      } else {
        throw Exception('Erreur de connexion: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Erreur de connexion: $e');
    }
  }

  /// Get current user from localStorage (no API call)
  Future<CurrentUser?> getCurrentUser() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final userJson = prefs.getString(_userKey);
      if (userJson == null) return null;
      return CurrentUser.fromJson(jsonDecode(userJson));
    } catch (_) {
      return null;
    }
  }

  /// Get stored auth token
  Future<String?> getToken() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      return prefs.getString(_tokenKey);
    } catch (_) {
      return null;
    }
  }

  /// Check if user is authenticated (has valid token)
  Future<bool> isAuthenticated() async {
    final token = await getToken();
    return token != null && token.isNotEmpty;
  }

  /// Save auth data to local storage
  Future<void> _saveAuthData(AuthResponse authResponse) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_tokenKey, authResponse.accessToken);
    await prefs.setString(_userKey, jsonEncode({
      'id': authResponse.user.id,
      'email': authResponse.user.email,
      'role': authResponse.user.role,
      'org_id': authResponse.user.organizationId,
      'full_name': authResponse.user.fullName,
    }));
  }

  /// Update user profile (email and full_name)
  Future<CurrentUser> updateProfile({
    String? email,
    String? fullName,
    required String token,
  }) async {
    final url = Uri.parse('$baseUrl/api/users/profile');
    try {
      final response = await http.put(
        url,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: jsonEncode({
          if (email != null) 'email': email,
          if (fullName != null) 'full_name': fullName,
        }),
      );

      if (response.statusCode == 200) {
        final userJson = jsonDecode(response.body);
        final updatedUser = CurrentUser.fromJson(userJson);

        // Update stored user info
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString(_userKey, jsonEncode({
          'id': updatedUser.id,
          'email': updatedUser.email,
          'role': updatedUser.role,
          'org_id': updatedUser.organizationId,
          'full_name': updatedUser.fullName,
        }));

        return updatedUser;
      } else if (response.statusCode == 409) {
        throw Exception('Email already in use');
      } else if (response.statusCode == 422) {
        throw Exception('Invalid input');
      } else {
        throw Exception('Failed to update profile: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error updating profile: $e');
    }
  }

  /// Change user password
  Future<void> changePassword({
    required String currentPassword,
    required String newPassword,
    required String token,
  }) async {
    final url = Uri.parse('$baseUrl/api/users/change-password');
    try {
      final response = await http.post(
        url,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: jsonEncode({
          'current_password': currentPassword,
          'new_password': newPassword,
        }),
      );

      if (response.statusCode == 200) {
        return;
      } else if (response.statusCode == 401) {
        throw Exception('Current password is incorrect');
      } else if (response.statusCode == 422) {
        throw Exception('Password must be at least 8 characters and different from current password');
      } else {
        throw Exception('Failed to change password: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error changing password: $e');
    }
  }

  /// Clear auth data (logout)
  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_tokenKey);
    await prefs.remove(_userKey);
  }
}
