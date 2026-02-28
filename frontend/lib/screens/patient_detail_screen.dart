import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../api_service.dart';
import '../models/patient.dart';
import '../models/prescription.dart';
import 'patient_form_screen.dart';
import 'voice_prescription_screen.dart';
import 'text_prescription_screen.dart';
import 'edit_prescription_screen.dart';

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
        builder: (context) =>
            PatientFormScreen(apiService: widget.apiService, patient: _patient),
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
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Erreur: $e')));
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

  void _editPrescription(Prescription prescription) async {
    final result = await Navigator.of(context).push<bool>(
      MaterialPageRoute(
        builder: (context) => EditPrescriptionScreen(
          prescription: prescription,
          patient: _patient,
          apiService: widget.apiService,
        ),
      ),
    );
    if (result == true) {
      _refreshPatient();
    }
  }

  void _showSignPrescriptionDialog(Prescription prescription) {
    bool isLoading = false;

    showDialog(
      context: context,
      builder: (dialogContext) => StatefulBuilder(
        builder: (context, setState) => AlertDialog(
          title: const Text('Confirmer l\'ordonnance'),
          content: SingleChildScrollView(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  'Médicament: ${prescription.medication}',
                  style: const TextStyle(fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 8),
                Text(
                  'Dosage: ${prescription.dosage}',
                  style: const TextStyle(fontSize: 12),
                ),
                Text(
                  'Durée: ${prescription.duration}',
                  style: const TextStyle(fontSize: 12),
                ),
                if (prescription.diagnosis.isNotEmpty) ...[
                  const SizedBox(height: 8),
                  Text(
                    'Diagnostic: ${prescription.diagnosis}',
                    style: const TextStyle(fontSize: 12),
                  ),
                ],
                const SizedBox(height: 16),
                const Text(
                  'Voulez-vous confirmer cette ordonnance?',
                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: isLoading ? null : () => Navigator.pop(dialogContext),
              child: const Text('Annuler'),
            ),
            ElevatedButton(
              onPressed: isLoading
                  ? null
                  : () async {
                      setState(() => isLoading = true);
                      try {
                        await widget.apiService.signPrescription(
                          prescription.id,
                          '', // No signature data needed
                        );

                        if (mounted) {
                          Navigator.pop(dialogContext);
                          if (mounted) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(
                                content: const Text('Ordonnance confirmée'),
                                backgroundColor: Colors.green.shade600,
                              ),
                            );
                          }
                          _refreshPatient();
                        }
                      } catch (e) {
                        if (mounted) {
                          setState(() => isLoading = false);
                          if (mounted) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(
                                content: Text('Erreur: $e'),
                                backgroundColor: Colors.red.shade600,
                              ),
                            );
                          }
                        }
                      }
                    },
              child: isLoading
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                      ),
                    )
                  : const Text('Confirmer'),
            ),
          ],
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
          IconButton(icon: const Icon(Icons.edit), onPressed: _editPatient),
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
                  if (_patient.phone != null) Text(_patient.phone!),
                  if (_patient.email != null) Text(_patient.email!),
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

            // Prescription History
            Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Historique des ordonnances',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 12),
                  FutureBuilder<List<Prescription>>(
                    future: widget.apiService.getPatientPrescriptions(
                      _patient.id,
                    ),
                    builder: (context, snapshot) {
                      if (snapshot.connectionState == ConnectionState.waiting) {
                        return const Center(
                          child: Padding(
                            padding: EdgeInsets.all(16),
                            child: CircularProgressIndicator(),
                          ),
                        );
                      }

                      if (snapshot.hasError) {
                        return Center(
                          child: Padding(
                            padding: const EdgeInsets.all(16),
                            child: Text(
                              'Erreur: ${snapshot.error}',
                              style: TextStyle(color: Colors.red.shade700),
                            ),
                          ),
                        );
                      }

                      final prescriptions = snapshot.data ?? [];

                      if (prescriptions.isEmpty) {
                        return Padding(
                          padding: const EdgeInsets.all(16),
                          child: Text(
                            'Aucune ordonnance',
                            style: TextStyle(color: Colors.grey.shade600),
                          ),
                        );
                      }

                      return ListView.builder(
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
                        itemCount: prescriptions.length,
                        itemBuilder: (context, index) {
                          final prescription = prescriptions[index];
                          return Card(
                            margin: const EdgeInsets.only(bottom: 12),
                            child: Padding(
                              padding: const EdgeInsets.all(12),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    mainAxisAlignment:
                                        MainAxisAlignment.spaceBetween,
                                    children: [
                                      Expanded(
                                        child: Column(
                                          crossAxisAlignment:
                                              CrossAxisAlignment.start,
                                          children: [
                                            Text(
                                              prescription.medication,
                                              style: const TextStyle(
                                                fontWeight: FontWeight.bold,
                                                fontSize: 16,
                                              ),
                                            ),
                                            const SizedBox(height: 4),
                                            Text(
                                              'Dosage: ${prescription.dosage}',
                                              style: TextStyle(
                                                fontSize: 12,
                                                color: Colors.grey.shade600,
                                              ),
                                            ),
                                            Text(
                                              'Durée: ${prescription.duration}',
                                              style: TextStyle(
                                                fontSize: 12,
                                                color: Colors.grey.shade600,
                                              ),
                                            ),
                                          ],
                                        ),
                                      ),
                                      Column(
                                        crossAxisAlignment: CrossAxisAlignment.end,
                                        children: [
                                          Container(
                                            padding: const EdgeInsets.symmetric(
                                              horizontal: 8,
                                              vertical: 4,
                                            ),
                                            decoration: BoxDecoration(
                                              color: prescription.status == 'active'
                                                  ? Colors.green.shade100
                                                  : Colors.orange.shade100,
                                              borderRadius: BorderRadius.circular(
                                                4,
                                              ),
                                            ),
                                            child: Text(
                                              prescription.status,
                                              style: TextStyle(
                                                fontSize: 12,
                                                fontWeight: FontWeight.bold,
                                                color:
                                                    prescription.status == 'active'
                                                    ? Colors.green.shade700
                                                    : Colors.orange.shade700,
                                              ),
                                            ),
                                          ),
                                          const SizedBox(height: 4),
                                          Container(
                                            padding: const EdgeInsets.symmetric(
                                              horizontal: 6,
                                              vertical: 2,
                                            ),
                                            decoration: BoxDecoration(
                                              color: prescription.isSigned
                                                  ? Colors.green.shade100
                                                  : Colors.orange.shade100,
                                              borderRadius: BorderRadius.circular(3),
                                            ),
                                            child: Text(
                                              prescription.isSigned
                                                  ? '✓ Signée'
                                                  : '⏳ À signer',
                                              style: TextStyle(
                                                fontSize: 10,
                                                fontWeight: FontWeight.bold,
                                                color: prescription.isSigned
                                                    ? Colors.green.shade700
                                                    : Colors.orange.shade700,
                                              ),
                                            ),
                                          ),
                                        ],
                                      ),
                                    ],
                                  ),
                                  const SizedBox(height: 8),
                                  if (prescription.diagnosis != null &&
                                      prescription.diagnosis!.isNotEmpty) ...[
                                    Text(
                                      'Diagnostic: ${prescription.diagnosis}',
                                      style: TextStyle(
                                        fontSize: 12,
                                        color: Colors.grey.shade700,
                                      ),
                                    ),
                                    const SizedBox(height: 4),
                                  ],
                                  if (prescription.specialInstructions !=
                                          null &&
                                      prescription
                                          .specialInstructions!
                                          .isNotEmpty) ...[
                                    Text(
                                      'Instructions: ${prescription.specialInstructions}',
                                      style: TextStyle(
                                        fontSize: 12,
                                        color: Colors.grey.shade700,
                                      ),
                                    ),
                                    const SizedBox(height: 4),
                                  ],
                                  Text(
                                    'Créée le ${DateFormat('dd/MM/yyyy à HH:mm').format(prescription.createdAt)} par ${prescription.createdBy}',
                                    style: TextStyle(
                                      fontSize: 10,
                                      color: Colors.grey.shade500,
                                    ),
                                  ),
                                  if (prescription.isSigned &&
                                      prescription.doctorSignedAt != null) ...[
                                    const SizedBox(height: 4),
                                    Text(
                                      'Signée le ${DateFormat('dd/MM/yyyy à HH:mm').format(prescription.doctorSignedAt!)}',
                                      style: TextStyle(
                                        fontSize: 10,
                                        color: Colors.green.shade600,
                                      ),
                                    ),
                                  ],
                                  const SizedBox(height: 12),
                                  if (prescription.status == 'draft') ...[
                                    Row(
                                      children: [
                                        Expanded(
                                          child: TextButton.icon(
                                            onPressed: () => _editPrescription(prescription),
                                            icon: const Icon(Icons.edit),
                                            label: const Text('Éditer'),
                                          ),
                                        ),
                                        const SizedBox(width: 8),
                                        Expanded(
                                          child: ElevatedButton.icon(
                                            onPressed: () =>
                                                _showSignPrescriptionDialog(
                                                  prescription,
                                                ),
                                            icon: const Icon(Icons.check_circle),
                                            label: const Text('Signer'),
                                            style: ElevatedButton.styleFrom(
                                              backgroundColor: Colors.green.shade600,
                                            ),
                                          ),
                                        ),
                                      ],
                                    ),
                                  ] else if (!prescription.isSigned) ...[
                                    SizedBox(
                                      width: double.infinity,
                                      child: ElevatedButton.icon(
                                        onPressed: () =>
                                            _showSignPrescriptionDialog(
                                              prescription,
                                            ),
                                        icon: const Icon(Icons.edit_document),
                                        label: const Text('Signer'),
                                        style: ElevatedButton.styleFrom(
                                          backgroundColor: Colors.blue.shade600,
                                        ),
                                      ),
                                    ),
                                  ],
                                ],
                              ),
                            ),
                          );
                        },
                      );
                    },
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
                    'Conditions chroniques',
                    _patient.chronicConditions,
                  ),
                  const SizedBox(height: 16),
                  _buildMedicalSection(
                    'Médicaments actuels',
                    _patient.currentMedications,
                  ),
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
                        style: const TextStyle(
                          fontSize: 12,
                          color: Colors.grey,
                        ),
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
        Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        if (items.isEmpty)
          Text('Aucun', style: TextStyle(color: Colors.grey.shade600))
        else
          Wrap(
            spacing: 8,
            children: items
                .map(
                  (item) => Chip(
                    label: Text(item),
                    backgroundColor: Colors.blue.shade100,
                  ),
                )
                .toList(),
          ),
      ],
    );
  }
}
