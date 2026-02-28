import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../api_service.dart';
import '../models/patient.dart';
import '../providers/auth_provider.dart';
import 'edit_extracted_prescription_screen.dart';
import 'validation_results_screen.dart';

class TextPrescriptionScreen extends StatefulWidget {
  final Patient patient;
  final ApiService apiService;

  const TextPrescriptionScreen({
    Key? key,
    required this.patient,
    required this.apiService,
  }) : super(key: key);

  @override
  State<TextPrescriptionScreen> createState() => _TextPrescriptionScreenState();
}

class _TextPrescriptionScreenState extends State<TextPrescriptionScreen> {
  late TextEditingController _textController;
  bool _isProcessing = false;

  @override
  void initState() {
    super.initState();
    _textController = TextEditingController();
  }

  @override
  void dispose() {
    _textController.dispose();
    super.dispose();
  }

  Future<void> _submitPrescription() async {
    if (_textController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Veuillez entrer une ordonnance')),
      );
      return;
    }

    setState(() => _isProcessing = true);

    try {
      final result = await widget.apiService.createTextPrescription(
        patientId: widget.patient.id,
        prescriptionText: _textController.text,
      );

      if (mounted) {
        final userRole = Provider.of<AuthProvider>(context, listen: false).currentUser?.role;
        Navigator.of(context).push(
          MaterialPageRoute(
            builder: (context) => EditExtractedPrescriptionScreen(
              validationResult: result,
              patient: widget.patient,
              apiService: widget.apiService,
              userRole: userRole,
            ),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Erreur: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _isProcessing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Ordonnance texte'),
            Text(widget.patient.fullName, style: const TextStyle(fontSize: 12)),
          ],
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Patient: ${widget.patient.fullName}',
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 24),
            const Text(
              'Entrez l\'ordonnance:',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _textController,
              maxLines: 10,
              decoration: InputDecoration(
                hintText:
                    'Patient: ...\nMédication: ...\nPosologie: ...\nDurée: ...\nInstructions: ...',
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
            ),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: _isProcessing ? null : _submitPrescription,
                icon: _isProcessing
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.check),
                label: const Text('Valider'),
              ),
            ),
            const SizedBox(height: 24),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.blue.shade50,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Format recommandé:',
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 8),
                  const Text('Patient: Nom complet'),
                  const Text('Médication: Nom du médicament'),
                  const Text('Posologie: Dose et fréquence'),
                  const Text('Durée: Durée du traitement'),
                  const Text('Instructions: Instructions spéciales'),
                  const SizedBox(height: 16),
                  const Text(
                    'Exemple:',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
                  ),
                  const SizedBox(height: 4),
                  Container(
                    padding: const EdgeInsets.all(8),
                    color: Colors.white,
                    child: const Text(
                      'Patient: Jean Dupont\n'
                      'Médication: Amoxicilline\n'
                      'Posologie: 500mg trois fois par jour\n'
                      'Durée: 7 jours\n'
                      'Instructions: Prendre avec de la nourriture',
                      style: TextStyle(fontSize: 12, fontFamily: 'monospace'),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
