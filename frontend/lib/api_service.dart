import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter/foundation.dart'; // For kIsWeb
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
        return data
            .map((p) => Patient.fromJson(p as Map<String, dynamic>))
            .toList();
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
      if (chronicConditions != null)
        body['chronic_conditions'] = chronicConditions;
      if (currentMedications != null)
        body['current_medications'] = currentMedications;
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
  // PATIENT PRESCRIPTION HISTORY
  // ============================================================================

  Future<List<Prescription>> getPatientPrescriptions(String patientId) async {
    final url = Uri.parse('$baseUrl/api/patients/$patientId/prescriptions');
    try {
      final response = await http.get(url, headers: _authHeaders);

      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);
        return data
            .map((p) => Prescription.fromJson(p as Map<String, dynamic>))
            .toList();
      } else {
        throw Exception(_getErrorMessage(response));
      }
    } catch (e) {
      throw Exception('Erreur récupération ordonnances: $e');
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
        return PrescriptionValidationResponse.fromJson(
          jsonDecode(responseData),
        );
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
        return PrescriptionValidationResponse.fromJson(
          jsonDecode(response.body),
        );
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
        throw Exception(
          'Le modèle IA n\'est pas encore chargé. Veuillez patienter quelques secondes.',
        );
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
        body: jsonEncode({'signature_base64': signatureBase64}),
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
  // DEVICE MANAGEMENT ENDPOINTS
  // ============================================================================

  Future<List<dynamic>> getDevices() async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/devices'),
      headers: _authHeaders,
    );

    if (response.statusCode == 200) {
      final List<dynamic> data = jsonDecode(response.body);
      return data;
    } else {
      throw Exception(_getErrorMessage(response));
    }
  }

  Future<void> assignDeviceToPrescription(
    String prescriptionId,
    String deviceId,
    int quantity,
    String? instructions,
    String priority,
  ) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/prescriptions/$prescriptionId/devices'),
      headers: _authHeaders,
      body: jsonEncode({
        'device_id': deviceId,
        'quantity': quantity,
        'instructions': instructions,
        'priority': priority,
      }),
    );

    if (response.statusCode != 200) {
      throw Exception(_getErrorMessage(response));
    }
  }

  Future<List<dynamic>> getPrescriptionDevices(String prescriptionId) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/prescriptions/$prescriptionId/devices'),
      headers: _authHeaders,
    );

    if (response.statusCode == 200) {
      final List<dynamic> data = jsonDecode(response.body);
      return data;
    } else {
      throw Exception(_getErrorMessage(response));
    }
  }

  Future<void> removeDeviceFromPrescription(
    String prescriptionId,
    String deviceId,
  ) async {
    final response = await http.delete(
      Uri.parse('$baseUrl/api/prescriptions/$prescriptionId/devices/$deviceId'),
      headers: _authHeaders,
    );

    if (response.statusCode != 200) {
      throw Exception(_getErrorMessage(response));
    }
  }

  Future<void> completeDeviceDelivery(
    String visitId,
    String deviceSerialInstalled,
    String nurseNotes,
    String? patientSignature,
  ) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/patient-visits/$visitId/complete'),
      headers: _authHeaders,
      body: jsonEncode({
        'device_serial_installed': deviceSerialInstalled,
        'nurse_notes': nurseNotes,
        'patient_signature': patientSignature,
      }),
    );

    if (response.statusCode != 200) {
      throw Exception(_getErrorMessage(response));
    }
  }

  Future<Prescription> signPrescription(
    String prescriptionId,
    String signatureBase64,
  ) async {
    final response = await http.put(
      Uri.parse('$baseUrl/api/prescriptions/$prescriptionId/sign'),
      headers: _authHeaders,
      body: jsonEncode({
        'doctor_signature': signatureBase64,
      }),
    );

    if (response.statusCode == 200) {
      return Prescription.fromJson(jsonDecode(response.body));
    } else {
      throw Exception(_getErrorMessage(response));
    }
  }

  Future<Prescription> updatePrescription(
    String prescriptionId, {
    String? medication,
    String? dosage,
    String? duration,
    String? diagnosis,
    String? specialInstructions,
  }) async {
    final response = await http.put(
      Uri.parse('$baseUrl/api/prescriptions/$prescriptionId'),
      headers: _authHeaders,
      body: jsonEncode({
        if (medication != null) 'medication': medication,
        if (dosage != null) 'dosage': dosage,
        if (duration != null) 'duration': duration,
        if (diagnosis != null) 'diagnosis': diagnosis,
        if (specialInstructions != null) 'special_instructions': specialInstructions,
      }),
    );

    if (response.statusCode == 200) {
      return Prescription.fromJson(jsonDecode(response.body));
    } else {
      throw Exception(_getErrorMessage(response));
    }
  }

  // ============================================================================
  // PATIENT VISITS / DELIVERIES ENDPOINTS
  // ============================================================================

  Future<List<dynamic>> getPatientVisits() async {
    final url = Uri.parse('$baseUrl/api/patient-visits');
    try {
      final response = await http.get(url, headers: _authHeaders);

      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);
        return data;
      } else {
        throw Exception(_getErrorMessage(response));
      }
    } catch (e) {
      throw Exception('Erreur récupération visites: $e');
    }
  }

  Future<Map<String, dynamic>> getVisitDetails(String visitId) async {
    final url = Uri.parse('$baseUrl/api/patient-visits/$visitId');
    try {
      final response = await http.get(url, headers: _authHeaders);

      if (response.statusCode == 200) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      } else {
        throw Exception(_getErrorMessage(response));
      }
    } catch (e) {
      throw Exception('Erreur récupération détails visite: $e');
    }
  }

  Future<void> updateVisitStatus(String visitId, String status) async {
    final url = Uri.parse('$baseUrl/api/patient-visits/$visitId/status');
    try {
      final response = await http.put(
        url,
        headers: _authHeaders,
        body: jsonEncode({'status': status}),
      );

      if (response.statusCode != 200) {
        throw Exception(_getErrorMessage(response));
      }
    } catch (e) {
      throw Exception('Erreur mise à jour statut: $e');
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

  // ============================================================================
  // INTERVENTIONS
  // ============================================================================

  /// Create a new intervention (doctor only)
  Future<Map<String, dynamic>> createIntervention({
    required String prescriptionId,
    required String interventionType,
    String? description,
    required DateTime scheduledDate,
    String priority = 'normal',
  }) async {
    final body = {
      'prescription_id': prescriptionId,
      'intervention_type': interventionType,
      if (description != null) 'description': description,
      'scheduled_date': scheduledDate.toIso8601String(),
      'priority': priority,
    };

    final response = await http.post(
      Uri.parse('$baseUrl/api/interventions'),
      headers: _getHeaders(),
      body: jsonEncode(body),
    ).timeout(Duration(seconds: 30));

    if (response.statusCode == 200 || response.statusCode == 201) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    } else {
      throw _parseError(response);
    }
  }

  /// Get list of interventions (optionally filtered by prescription_id and status)
  Future<List<Map<String, dynamic>>> getInterventions({
    String? prescriptionId,
    String? status,
  }) async {
    final queryParams = <String, String>{};
    if (prescriptionId != null) queryParams['prescription_id'] = prescriptionId;
    if (status != null) queryParams['status'] = status;

    final uri = Uri.parse('$baseUrl/api/interventions').replace(queryParameters: queryParams);
    final response = await http.get(uri, headers: _getHeaders()).timeout(Duration(seconds: 30));

    if (response.statusCode == 200) {
      final List<dynamic> data = jsonDecode(response.body);
      return data.cast<Map<String, dynamic>>();
    } else {
      throw _parseError(response);
    }
  }

  /// Get intervention details with logs
  Future<Map<String, dynamic>> getIntervention(String interventionId) async {
    final response = await http
        .get(
          Uri.parse('$baseUrl/api/interventions/$interventionId'),
          headers: _getHeaders(),
        )
        .timeout(Duration(seconds: 30));

    if (response.statusCode == 200) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    } else {
      throw _parseError(response);
    }
  }

  /// Update intervention (doctor only, only if scheduled)
  Future<Map<String, dynamic>> updateIntervention(
    String interventionId, {
    String? interventionType,
    String? description,
    DateTime? scheduledDate,
    String? priority,
    String? status,
  }) async {
    final body = <String, dynamic>{};
    if (interventionType != null) body['intervention_type'] = interventionType;
    if (description != null) body['description'] = description;
    if (scheduledDate != null) body['scheduled_date'] = scheduledDate.toIso8601String();
    if (priority != null) body['priority'] = priority;
    if (status != null) body['status'] = status;

    final response = await http.put(
      Uri.parse('$baseUrl/api/interventions/$interventionId'),
      headers: _getHeaders(),
      body: jsonEncode(body),
    ).timeout(Duration(seconds: 30));

    if (response.statusCode == 200) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    } else {
      throw _parseError(response);
    }
  }

  /// Delete intervention (doctor only, only if scheduled)
  Future<void> deleteIntervention(String interventionId) async {
    final response = await http.delete(
      Uri.parse('$baseUrl/api/interventions/$interventionId'),
      headers: _getHeaders(),
    ).timeout(Duration(seconds: 30));

    if (response.statusCode != 200) {
      throw _parseError(response);
    }
  }

  /// Log intervention status change
  Future<Map<String, dynamic>> logIntervention(
    String interventionId, {
    required String statusChange,
    String? notes,
  }) async {
    final body = {
      'status_change': statusChange,
      if (notes != null) 'notes': notes,
    };

    final response = await http.post(
      Uri.parse('$baseUrl/api/interventions/$interventionId/log'),
      headers: _getHeaders(),
      body: jsonEncode(body),
    ).timeout(Duration(seconds: 30));

    if (response.statusCode == 200 || response.statusCode == 201) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    } else {
      throw _parseError(response);
    }
  }

  /// Get all logs for an intervention
  Future<List<Map<String, dynamic>>> getInterventionLogs(String interventionId) async {
    final response = await http
        .get(
          Uri.parse('$baseUrl/api/interventions/$interventionId/logs'),
          headers: _getHeaders(),
        )
        .timeout(Duration(seconds: 30));

    if (response.statusCode == 200) {
      final List<dynamic> data = jsonDecode(response.body);
      return data.cast<Map<String, dynamic>>();
    } else {
      throw _parseError(response);
    }
  }

  /// Upload document to intervention log
  Future<Map<String, dynamic>> uploadInterventionDocument(
    String interventionId, {
    required File file,
    String documentType = 'note',
    String? caption,
    String? logId,
  }) async {
    final request = http.MultipartRequest(
      'POST',
      Uri.parse('$baseUrl/api/interventions/$interventionId/documents'),
    );

    // Add headers
    request.headers.addAll(_getHeaders());

    // Add fields
    request.fields['document_type'] = documentType;
    if (caption != null) request.fields['caption'] = caption;
    if (logId != null) request.fields['log_id'] = logId;

    // Add file
    request.files.add(
      await http.MultipartFile.fromPath('file', file.path),
    );

    final response = await request.send().timeout(Duration(seconds: 60));
    final responseBody = await response.stream.bytesToString();

    if (response.statusCode == 200 || response.statusCode == 201) {
      return jsonDecode(responseBody) as Map<String, dynamic>;
    } else {
      throw _parseError(http.Response(responseBody, response.statusCode));
    }
  }

  /// Get all documents for an intervention
  Future<List<Map<String, dynamic>>> getInterventionDocuments(String interventionId) async {
    final response = await http
        .get(
          Uri.parse('$baseUrl/api/interventions/$interventionId/documents'),
          headers: _getHeaders(),
        )
        .timeout(Duration(seconds: 30));

    if (response.statusCode == 200) {
      final List<dynamic> data = jsonDecode(response.body);
      return data.cast<Map<String, dynamic>>();
    } else {
      throw _parseError(response);
    }
  }
}
