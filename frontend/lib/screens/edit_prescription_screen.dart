import 'package:flutter/material.dart';
import '../api_service.dart';
import '../models/patient.dart';
import '../models/prescription.dart';
import 'validation_results_screen.dart';

class EditPrescriptionScreen extends StatefulWidget {
  final Prescription prescription;
  final Patient patient;
  final ApiService apiService;

  const EditPrescriptionScreen({
    Key? key,
    required this.prescription,
    required this.patient,
    required this.apiService,
  }) : super(key: key);

  @override
  State<EditPrescriptionScreen> createState() => _EditPrescriptionScreenState();
}

class _EditPrescriptionScreenState extends State<EditPrescriptionScreen> {
  late TextEditingController _medicationController;
  late TextEditingController _dosageController;
  late TextEditingController _durationController;
  late TextEditingController _diagnosisController;
  late TextEditingController _specialInstructionsController;

  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _medicationController = TextEditingController(text: widget.prescription.medication);
    _dosageController = TextEditingController(text: widget.prescription.dosage);
    _durationController = TextEditingController(text: widget.prescription.duration);
    _diagnosisController = TextEditingController(text: widget.prescription.diagnosis);
    _specialInstructionsController =
        TextEditingController(text: widget.prescription.specialInstructions ?? '');
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

  Future<void> _savePrescription() async {
    if (_medicationController.text.isEmpty ||
        _dosageController.text.isEmpty ||
        _durationController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Veuillez remplir les champs requis')),
      );
      return;
    }

    setState(() => _isLoading = true);
    try {
      final updatedPrescription = await widget.apiService.updatePrescription(
        widget.prescription.id,
        medication: _medicationController.text,
        dosage: _dosageController.text,
        duration: _durationController.text,
        diagnosis: _diagnosisController.text,
        specialInstructions: _specialInstructionsController.text.isEmpty
            ? null
            : _specialInstructionsController.text,
      );

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Ordonnance mise à jour')),
        );
        Navigator.of(context).pop(true);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Erreur: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Éditer ordonnance'),
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
                    onPressed: _isLoading ? null : () => Navigator.pop(context),
                    child: const Text('Annuler'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: _isLoading ? null : _savePrescription,
                    icon: _isLoading
                        ? const SizedBox(
                            width: 16,
                            height: 16,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Icon(Icons.save),
                    label: const Text('Enregistrer'),
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
