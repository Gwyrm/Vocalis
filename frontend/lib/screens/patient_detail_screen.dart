import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../api_service.dart';
import '../models/patient.dart';
import 'patient_form_screen.dart';
import 'voice_prescription_screen.dart';
import 'text_prescription_screen.dart';

class PatientDetailScreen extends StatefulWidget {
  final Patient patient;
  final ApiService apiService;

  const PatientDetailScreen({
    Key? key,
    required this.patient,
    required this.apiService,
  }) : super(key: key);

  @override
  State<PatientDetailScreen> createState() => _PatientDetailScreenState();
}

class _PatientDetailScreenState extends State<PatientDetailScreen> {
  late Patient _patient;

  @override
  void initState() {
    super.initState();
    _patient = widget.patient;
  }

  void _editPatient() async {
    final result = await Navigator.of(context).push<bool>(
      MaterialPageRoute(
        builder: (context) => PatientFormScreen(
          apiService: widget.apiService,
          patient: _patient,
        ),
      ),
    );
    if (result == true) {
      _refreshPatient();
    }
  }

  void _refreshPatient() async {
    try {
      final updated = await widget.apiService.getPatient(_patient.id);
      setState(() => _patient = updated);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Erreur: $e')),
        );
      }
    }
  }

  void _navigateToVoicePrescription() {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (context) => VoicePrescriptionScreen(
          patient: _patient,
          apiService: widget.apiService,
        ),
      ),
    );
  }

  void _navigateToTextPrescription() {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (context) => TextPrescriptionScreen(
          patient: _patient,
          apiService: widget.apiService,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_patient.fullName),
        actions: [
          IconButton(
            icon: const Icon(Icons.edit),
            onPressed: _editPatient,
          ),
        ],
      ),
      body: SingleChildScrollView(
        child: Column(
          children: [
            // Patient Header Card
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              color: Colors.blue.shade50,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    _patient.fullName,
                    style: const TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text('${_patient.ageInYears} ans'),
                  if (_patient.phone != null)
                    Text(_patient.phone!),
                  if (_patient.email != null)
                    Text(_patient.email!),
                ],
              ),
            ),

            // Quick Actions
            Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Créer une ordonnance',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(
                        child: ElevatedButton.icon(
                          onPressed: _navigateToVoicePrescription,
                          icon: const Icon(Icons.mic),
                          label: const Text('Voix'),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: ElevatedButton.icon(
                          onPressed: _navigateToTextPrescription,
                          icon: const Icon(Icons.edit),
                          label: const Text('Texte'),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),

            // Medical Information
            Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Informations médicales',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 12),
                  _buildMedicalSection('Allergies', _patient.allergies),
                  const SizedBox(height: 16),
                  _buildMedicalSection(
                      'Conditions chroniques', _patient.chronicConditions),
                  const SizedBox(height: 16),
                  _buildMedicalSection(
                      'Médicaments actuels', _patient.currentMedications),
                  if (_patient.medicalNotes != null &&
                      _patient.medicalNotes!.isNotEmpty) ...[
                    const SizedBox(height: 16),
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(12),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              'Notes',
                              style: TextStyle(fontWeight: FontWeight.bold),
                            ),
                            const SizedBox(height: 8),
                            Text(_patient.medicalNotes!),
                          ],
                        ),
                      ),
                    ),
                  ],
                ],
              ),
            ),

            // Metadata
            Padding(
              padding: const EdgeInsets.all(16),
              child: Card(
                color: Colors.grey.shade100,
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Créé le: ${DateFormat('dd/MM/yyyy HH:mm').format(_patient.createdAt)}',
                        style: const TextStyle(fontSize: 12, color: Colors.grey),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMedicalSection(String title, List<String> items) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: const TextStyle(fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 8),
        if (items.isEmpty)
          Text(
            'Aucun',
            style: TextStyle(color: Colors.grey.shade600),
          )
        else
          Wrap(
            spacing: 8,
            children: items
                .map((item) => Chip(
                      label: Text(item),
                      backgroundColor: Colors.blue.shade100,
                    ))
                .toList(),
          ),
      ],
    );
  }
}
