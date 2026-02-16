import 'dart:convert';
import 'dart:typed_data';
import 'package:http/http.dart' as http;
import 'package:flutter/foundation.dart'; // For kIsWeb
import 'models/prescription_data.dart';

class ApiService {
  // Check for environment variable set via --dart-define (e.g. --dart-define=API_URL=https://api.example.com)
  static const String _envBaseUrl = String.fromEnvironment('API_URL');
  static const String _baseUrlLocal = 'http://127.0.0.1:8081';

  String get baseUrl {
    // 1. Check if provided via --dart-define
    if (_envBaseUrl.isNotEmpty) return _envBaseUrl;

    // 2. For Web, attempt to use the current origin if not provided
    if (kIsWeb) {
      final origin = Uri.base.origin;
      if (origin.contains('localhost') || origin.contains('127.0.0.1')) {
        return _baseUrlLocal;
      }
      
      // If accessed from a device/production (e.g. i-noovate.ddns.net),
      // assume Nginx is proxying /api to the backend.
      // So we just use the origin.
      return origin;
    }

    return _baseUrlLocal; 
  }

  Future<Map<String, dynamic>> chat(String message) async {
    final url = Uri.parse('$baseUrl/api/chat');
    try {
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'message': message}),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return data;
      } else if (response.statusCode == 503) {
        throw Exception('Le modèle IA n\'est pas encore chargé. Veuillez patienter quelques secondes.');
      } else if (response.statusCode == 504) {
        throw Exception('L\'IA met trop de temps à répondre.');
      } else {
        final detail = _tryDecodeDetail(response.body);
        throw Exception('Erreur $detail (${response.statusCode})');
      }
    } catch (e) {
      if (e is Exception) rethrow;
      throw Exception('Erreur de connexion : $e');
    }
  }

  Future<Uint8List> generatePdf(String signatureBase64) async {
    final url = Uri.parse('$baseUrl/api/generate-pdf');
    try {
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'signature_base64': signatureBase64,
        }),
      );

      if (response.statusCode == 200) {
        return response.bodyBytes;
      } else if (response.statusCode == 400) {
        final detail = _tryDecodeDetail(response.body);
        throw Exception(detail);
      } else {
        final detail = _tryDecodeDetail(response.body);
        throw Exception('Erreur PDF: $detail (${response.statusCode})');
      }
    } catch (e) {
      if (e is Exception) rethrow;
      throw Exception('Erreur génération PDF: $e');
    }
  }

  String _tryDecodeDetail(String body) {
    try {
      return jsonDecode(body)['detail'] ?? 'Erreur inconnue';
    } catch (_) {
      // If body is HTML or not JSON, return a snippet
      return body.substring(0, 50).replaceAll('\n', ' ') + '...';
    }
  }
}
