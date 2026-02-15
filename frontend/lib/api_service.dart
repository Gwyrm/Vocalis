import 'dart:convert';
import 'dart:typed_data';
import 'package:http/http.dart' as http;
import 'package:flutter/foundation.dart'; // For kIsWeb

class ApiService {
  // Check for environment variable set via --dart-define (e.g. --dart-define=API_URL=https://api.example.com)
  static const String _envBaseUrl = String.fromEnvironment('API_URL');
  static const String _baseUrlLocal = 'http://127.0.0.1:8080';

  String get baseUrl {
    // 1. Check if provided via --dart-define
    if (_envBaseUrl.isNotEmpty) return _envBaseUrl;

    // 2. For Web, attempt to use the current origin if not provided
    if (kIsWeb) {
      final origin = Uri.base.origin;
      if (origin.contains('localhost') || origin.contains('127.0.0.1')) {
        return _baseUrlLocal;
      }
      // If deployed, assume the API is on the same host or port 8080
      // You can adjust this logic: e.g., origin + ":8080" if API is on 8080
      return origin; 
    }

    return _baseUrlLocal; 
  }

  Future<String> chat(String message) async {
    final url = Uri.parse('$baseUrl/api/chat');
    try {
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'message': message, 'model': 'mistral'}),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return data['response'];
      } else if (response.statusCode == 503) {
        throw Exception('Le service AI (Ollama) n\'est pas disponible. Vérifiez qu\'il est bien lancé.');
      } else if (response.statusCode == 504) {
        throw Exception('L\'IA met trop de temps à répondre. Le modèle est peut-être trop lourd pour votre serveur.');
      } else {
        final detail = jsonDecode(response.body)['detail'] ?? 'Erreur inconnue';
        throw Exception('Erreur $detail (${response.statusCode})');
      }
    } catch (e) {
      if (e is Exception) rethrow;
      throw Exception('Erreur de connexion : $e');
    }
  }

  Future<Uint8List> generatePdf(String content, String signatureBase64) async {
    final url = Uri.parse('$baseUrl/api/generate-pdf');
    try {
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'content': content,
          'signature_base64': signatureBase64,
        }),
      );

      if (response.statusCode == 200) {
        return response.bodyBytes;
      } else {
        throw Exception('Failed to generate PDF: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error generating PDF: $e');
    }
  }
}
