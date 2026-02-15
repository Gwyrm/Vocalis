import 'dart:convert';
import 'dart:typed_data';
import 'package:http/http.dart' as http;
import 'package:flutter/foundation.dart'; // For kIsWeb
import 'models/prescription_data.dart';

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
        final detail = jsonDecode(response.body)['detail'] ?? 'Erreur inconnue';
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
        final detail = jsonDecode(response.body)['detail'] ?? 'Données incomplètes';
        throw Exception(detail);
      } else {
        final detail = jsonDecode(response.body)['detail'] ?? 'Erreur inconnue';
        throw Exception('Erreur PDF: $detail (${response.statusCode})');
      }
    } catch (e) {
      if (e is Exception) rethrow;
      throw Exception('Erreur génération PDF: $e');
    }
  }

  Future<Map<String, dynamic>> collectPrescriptionInfo(
    PrescriptionData currentData,
    String userInput,
  ) async {
    final url = Uri.parse('$baseUrl/api/collect-prescription-info');
    try {
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'currentData': currentData.toJson(),
          'userInput': userInput,
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return data;
      } else if (response.statusCode == 503) {
        throw Exception('Le modèle IA n\'est pas encore chargé. Veuillez patienter quelques secondes.');
      } else {
        final detail = jsonDecode(response.body)['detail'] ?? 'Erreur inconnue';
        throw Exception('Erreur: $detail (${response.statusCode})');
      }
    } catch (e) {
      if (e is Exception) rethrow;
      throw Exception('Erreur de connexion : $e');
    }
  }

  Future<String> generatePrescription(PrescriptionData data) async {
    final url = Uri.parse('$baseUrl/api/generate-prescription');
    try {
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'data': data.toJson(),
        }),
      );

      if (response.statusCode == 200) {
        final responseData = jsonDecode(response.body);
        return responseData['prescription'] ?? '';
      } else if (response.statusCode == 503) {
        throw Exception('Le modèle IA n\'est pas encore chargé. Veuillez patienter quelques secondes.');
      } else if (response.statusCode == 400) {
        final detail = jsonDecode(response.body)['detail'] ?? 'Données incomplètes';
        throw Exception(detail);
      } else {
        final detail = jsonDecode(response.body)['detail'] ?? 'Erreur inconnue';
        throw Exception('Erreur: $detail (${response.statusCode})');
      }
    } catch (e) {
      if (e is Exception) rethrow;
      throw Exception('Erreur de génération : $e');
    }
  }
}
