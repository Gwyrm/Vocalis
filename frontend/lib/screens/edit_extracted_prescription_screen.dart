import 'package:flutter/material.dart';
import '../api_service.dart';
import '../models/patient.dart';
import '../models/prescription.dart';
import 'validation_results_screen.dart';

class EditExtractedPrescriptionScreen extends StatefulWidget {
  final PrescriptionValidationResponse validationResult;
  final Patient patient;
  final ApiService apiService;
  final String? userRole; // 'doctor' or 'nurse'

  const EditExtractedPrescriptionScreen({
    Key? key,
    required this.validationResult,
    required this.patient,
    required this.apiService,
    this.userRole,
  }) : super(key: key);

  @override
  State<EditExtractedPrescriptionScreen> createState() =>
      _EditExtractedPrescriptionScreenState();
}

class _EditExtractedPrescriptionScreenState
    extends State<EditExtractedPrescriptionScreen> {
  late TextEditingController _medicationController;
  late TextEditingController _dosageController;
  late TextEditingController _durationController;
  late TextEditingController _diagnosisController;
  late TextEditingController _specialInstructionsController;

  @override
  void initState() {
    super.initState();
    final prescription = widget.validationResult.prescription;
    _medicationController =
        TextEditingController(text: prescription?.medication ?? '');
    _dosageController = TextEditingController(text: prescription?.dosage ?? '');
    _durationController =
        TextEditingController(text: prescription?.duration ?? '');
    _diagnosisController =
        TextEditingController(text: prescription?.diagnosis ?? '');
    _specialInstructionsController =
        TextEditingController(text: prescription?.specialInstructions ?? '');
  }

  @override
  void dispose() {
    _medicationController.dispose();
    _dosageController.dispose();
    _durationController.dispose();
    _diagnosisController.dispose();
    _specialInstructionsController.dispose();
    super.dispose();
  }

  void _proceedToValidation() {
    if (_medicationController.text.isEmpty ||
        _dosageController.text.isEmpty ||
        _durationController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Veuillez remplir les champs requis')),
      );
      return;
    }

    // Create updated prescription with edited data
    final updatedPrescription = Prescription(
      id: widget.validationResult.prescription?.id ?? '',
      patientName: widget.validationResult.prescription?.patientName ?? '',
      patientAge: widget.validationResult.prescription?.patientAge ?? '',
      diagnosis: _diagnosisController.text,
      medication: _medicationController.text,
      dosage: _dosageController.text,
      duration: _durationController.text,
      specialInstructions: _specialInstructionsController.text.isEmpty
          ? null
          : _specialInstructionsController.text,
      status: widget.validationResult.prescription?.status ?? 'draft',
      createdBy: widget.validationResult.prescription?.createdBy ?? '',
      createdAt: widget.validationResult.prescription?.createdAt ?? DateTime.now(),
      isSigned: widget.validationResult.prescription?.isSigned ?? false,
      doctorSignedAt: widget.validationResult.prescription?.doctorSignedAt,
    );

    // Create updated validation response with edited prescription
    final updatedResult = PrescriptionValidationResponse(
      prescription: updatedPrescription,
      validation: widget.validationResult.validation,
      patientSummary: widget.validationResult.patientSummary,
      structuredData: widget.validationResult.structuredData,
    );

    // Navigate to validation results with updated data
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (context) => ValidationResultsScreen(
          result: updatedResult,
          patient: widget.patient,
          apiService: widget.apiService,
          userRole: widget.userRole,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Éditer les données extraites'),
        centerTitle: true,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Patient info
            Card(
              color: Colors.blue.shade50,
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      widget.patient.fullName,
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                      ),
                    ),
                    Text('${widget.patient.ageInYears} ans'),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),

            // Info banner
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.blue.shade50,
                border: Border.all(color: Colors.blue.shade200),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                children: [
                  Icon(Icons.info_outline, color: Colors.blue.shade700),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      'Vérifiez et modifiez les données extraites par l\'IA',
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.blue.shade700,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),

            // Diagnosis
            Text(
              'Diagnostic (optionnel)',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _diagnosisController,
              maxLines: 2,
              decoration: InputDecoration(
                hintText: 'Ex: Bronchite légère',
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
            ),
            const SizedBox(height: 24),

            // Medication
            Text(
              'Médicament *',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _medicationController,
              decoration: InputDecoration(
                hintText: 'Ex: Amoxicilline',
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
            ),
            const SizedBox(height: 24),

            // Dosage
            Text(
              'Posologie *',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _dosageController,
              decoration: InputDecoration(
                hintText: 'Ex: 500mg, 3 fois par jour',
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
            ),
            const SizedBox(height: 24),

            // Duration
            Text(
              'Durée du traitement *',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _durationController,
              decoration: InputDecoration(
                hintText: 'Ex: 10 jours',
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
            ),
            const SizedBox(height: 24),

            // Special instructions
            Text(
              'Instructions spéciales (optionnel)',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _specialInstructionsController,
              maxLines: 2,
              decoration: InputDecoration(
                hintText: 'Ex: À prendre pendant les repas',
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
            ),
            const SizedBox(height: 32),

            // Buttons
            Row(
              children: [
                Expanded(
                  child: TextButton(
                    onPressed: () => Navigator.pop(context),
                    child: const Text('Annuler'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: _proceedToValidation,
                    icon: const Icon(Icons.check_circle),
                    label: const Text('Continuer'),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
