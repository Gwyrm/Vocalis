import 'dart:convert';
import 'dart:typed_data';
import 'package:http/http.dart' as http;
import 'package:flutter/foundation.dart'; // For kIsWeb
import 'models/prescription_data.dart';
import 'models/patient.dart';
import 'models/prescription.dart';

class ApiService {
  // Check for environment variable set via --dart-define (e.g. --dart-define=API_URL=https://api.example.com)
  static const String _envBaseUrl = String.fromEnvironment('API_URL');
  static const String _baseUrlLocal = 'http://127.0.0.1:8080';

  String? _token;
  Function? _onAuthError;

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

  void setToken(String token) {
    _token = token;
  }

  void setOnAuthError(Function callback) {
    _onAuthError = callback;
  }

  void _handleAuthError() {
    _onAuthError?.call();
  }

  Map<String, String> get _authHeaders {
    final headers = <String, String>{'Content-Type': 'application/json'};
    if (_token != null) {
      headers['Authorization'] = 'Bearer $_token';
    }
    return headers;
  }

  // ============================================================================
  // PATIENT MANAGEMENT ENDPOINTS
  // ============================================================================

  Future<Patient> createPatient({
    required String firstName,
    required String lastName,
    required DateTime dateOfBirth,
    String? gender,
    String? phone,
    String? email,
    String? address,
    List<String>? allergies,
    List<String>? chronicConditions,
    List<String>? currentMedications,
    String? medicalNotes,
  }) async {
    final url = Uri.parse('$baseUrl/api/patients');
    try {
      final response = await http.post(
        url,
        headers: _authHeaders,
        body: jsonEncode({
          'first_name': firstName,
          'last_name': lastName,
          'date_of_birth': dateOfBirth.toIso8601String().split('T')[0],
          'gender': gender,
          'phone': phone,
          'email': email,
          'address': address,
          'allergies': allergies ?? [],
          'chronic_conditions': chronicConditions ?? [],
          'current_medications': currentMedications ?? [],
          'medical_notes': medicalNotes,
        }),
      );

      if (response.statusCode == 200) {
        return Patient.fromJson(jsonDecode(response.body));
      } else {
        throw Exception(_getErrorMessage(response));
      }
    } catch (e) {
      throw Exception('Erreur création patient: $e');
    }
  }

  Future<List<Patient>> getPatients() async {
    final url = Uri.parse('$baseUrl/api/patients');
    try {
      final response = await http.get(url, headers: _authHeaders);

      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);
        return data.map((p) => Patient.fromJson(p as Map<String, dynamic>)).toList();
      } else {
        throw Exception(_getErrorMessage(response));
      }
    } catch (e) {
      throw Exception('Erreur récupération patients: $e');
    }
  }

  Future<Patient> getPatient(String patientId) async {
    final url = Uri.parse('$baseUrl/api/patients/$patientId');
    try {
      final response = await http.get(url, headers: _authHeaders);

      if (response.statusCode == 200) {
        return Patient.fromJson(jsonDecode(response.body));
      } else {
        throw Exception(_getErrorMessage(response));
      }
    } catch (e) {
      throw Exception('Erreur récupération patient: $e');
    }
  }

  Future<Patient> updatePatient(
    String patientId, {
    String? firstName,
    String? lastName,
    String? gender,
    String? phone,
    String? email,
    String? address,
    List<String>? allergies,
    List<String>? chronicConditions,
    List<String>? currentMedications,
    String? medicalNotes,
  }) async {
    final url = Uri.parse('$baseUrl/api/patients/$patientId');
    try {
      final body = <String, dynamic>{};
      if (firstName != null) body['first_name'] = firstName;
      if (lastName != null) body['last_name'] = lastName;
      if (gender != null) body['gender'] = gender;
      if (phone != null) body['phone'] = phone;
      if (email != null) body['email'] = email;
      if (address != null) body['address'] = address;
      if (allergies != null) body['allergies'] = allergies;
      if (chronicConditions != null) body['chronic_conditions'] = chronicConditions;
      if (currentMedications != null) body['current_medications'] = currentMedications;
      if (medicalNotes != null) body['medical_notes'] = medicalNotes;

      final response = await http.put(
        url,
        headers: _authHeaders,
        body: jsonEncode(body),
      );

      if (response.statusCode == 200) {
        return Patient.fromJson(jsonDecode(response.body));
      } else {
        throw Exception(_getErrorMessage(response));
      }
    } catch (e) {
      throw Exception('Erreur mise à jour patient: $e');
    }
  }

  // ============================================================================
  // VOICE/TEXT PRESCRIPTION ENDPOINTS
  // ============================================================================

  Future<TranscriptionResult> transcribeAudio(List<int> audioBytes) async {
    final url = Uri.parse('$baseUrl/api/voice/transcribe');
    try {
      final request = http.MultipartRequest('POST', url)
        ..headers.addAll({'Authorization': 'Bearer $_token'})
        ..files.add(
          http.MultipartFile.fromBytes(
            'file',
            audioBytes,
            filename: 'prescription.wav',
          ),
        )
        ..fields['language'] = 'fr';

      final response = await request.send();

      if (response.statusCode == 200) {
        final responseData = await response.stream.bytesToString();
        return TranscriptionResult.fromJson(jsonDecode(responseData));
      } else {
        throw Exception(_getErrorMessageFromStream(response));
      }
    } catch (e) {
      throw Exception('Erreur transcription: $e');
    }
  }

  Future<PrescriptionValidationResponse> createVoicePrescription({
    required String patientId,
    required List<int> audioBytes,
  }) async {
    final url = Uri.parse('$baseUrl/api/prescriptions/voice');
    try {
      final request = http.MultipartRequest('POST', url)
        ..headers.addAll({'Authorization': 'Bearer $_token'})
        ..files.add(
          http.MultipartFile.fromBytes(
            'file',
            audioBytes,
            filename: 'prescription.wav',
          ),
        )
        ..fields['patient_id'] = patientId;

      final response = await request.send();

      if (response.statusCode == 200) {
        final responseData = await response.stream.bytesToString();
        return PrescriptionValidationResponse.fromJson(jsonDecode(responseData));
      } else {
        throw Exception(_getErrorMessageFromStream(response));
      }
    } catch (e) {
      throw Exception('Erreur création ordonnance vocale: $e');
    }
  }

  Future<PrescriptionValidationResponse> createTextPrescription({
    required String patientId,
    required String prescriptionText,
  }) async {
    final url = Uri.parse('$baseUrl/api/prescriptions/text');
    try {
      final response = await http.post(
        url,
        headers: _authHeaders,
        body: jsonEncode({
          'patient_id': patientId,
          'prescription_text': prescriptionText,
        }),
      );

      if (response.statusCode == 200) {
        return PrescriptionValidationResponse.fromJson(jsonDecode(response.body));
      } else {
        throw Exception(_getErrorMessage(response));
      }
    } catch (e) {
      throw Exception('Erreur création ordonnance texte: $e');
    }
  }

  // ============================================================================
  // LEGACY CHAT/PDF ENDPOINTS
  // ============================================================================

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

  // ============================================================================
  // HELPER METHODS
  // ============================================================================

  String _getErrorMessage(http.Response response) {
    // Check for auth errors
    if (response.statusCode == 401 || response.statusCode == 403) {
      _handleAuthError();
    }

    try {
      final json = jsonDecode(response.body);
      return json['detail'] ?? 'Erreur ${response.statusCode}';
    } catch (_) {
      return 'Erreur ${response.statusCode}';
    }
  }

  String _getErrorMessageFromStream(http.StreamedResponse response) {
    // Check for auth errors
    if (response.statusCode == 401 || response.statusCode == 403) {
      _handleAuthError();
    }

    try {
      return 'Erreur ${response.statusCode}';
    } catch (_) {
      return 'Erreur réseau';
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
