import 'dart:convert';
import 'dart:typed_data';
import 'package:http/http.dart' as http;
import 'package:flutter/foundation.dart'; // For kIsWeb

class ApiService {
  // Use 10.0.2.2 for Android emulator, localhost for iOS/Web
  static const String _baseUrlAndroid = 'http://10.0.2.2:8080';
  static const String _baseUrlLocal = 'http://127.0.0.1:8080';

  String get baseUrl {
    if (kIsWeb) return _baseUrlLocal;
    // Simple check, can be improved for real device vs emulator
    return _baseUrlLocal; 
    // In production, use env variables or config
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
      } else {
        throw Exception('Failed to get response: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error connecting to backend: $e');
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
