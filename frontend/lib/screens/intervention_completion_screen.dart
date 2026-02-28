import 'package:flutter/material.dart';
import '../api_service.dart';

class InterventionCompletionScreen extends StatefulWidget {
  final String interventionId;
  final VoidCallback onCompleted;
  final ApiService apiService;

  const InterventionCompletionScreen({
    Key? key,
    required this.interventionId,
    required this.onCompleted,
    required this.apiService,
  }) : super(key: key);

  @override
  State<InterventionCompletionScreen> createState() => _InterventionCompletionScreenState();
}

class _InterventionCompletionScreenState extends State<InterventionCompletionScreen> {
  late ApiService apiService;
  final _formKey = GlobalKey<FormState>();
  final _notesController = TextEditingController();

  bool isSubmitting = false;

  @override
  void initState() {
    super.initState();
    apiService = widget.apiService;
  }

  @override
  void dispose() {
    _notesController.dispose();
    super.dispose();
  }

  Future<void> _submitCompletion() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => isSubmitting = true);
    try {
      // Log the status change
      await apiService.logIntervention(
        widget.interventionId,
        statusChange: 'in_progress→completed',
        notes: _notesController.text.isEmpty ? null : _notesController.text.trim(),
      );

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Intervention complétée')),
        );
        widget.onCompleted();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Erreur: ${e.toString()}')),
        );
      }
    } finally {
      setState(() => isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Compléter l\'intervention'),
        elevation: 0,
        backgroundColor: Colors.blue.shade700,
      ),
      body: Form(
        key: _formKey,
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Notes section
              const Text(
                'Notes d\'intervention',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              TextFormField(
                controller: _notesController,
                decoration: const InputDecoration(
                  labelText: 'Notes',
                  hintText: 'Décrivez comment s\'est déroulée l\'intervention',
                  border: OutlineInputBorder(),
                ),
                maxLines: 5,
              ),
              const SizedBox(height: 32),

              // Submit button
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: isSubmitting ? null : _submitCompletion,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.green,
                  ),
                  child: isSubmitting
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Text('Marquer comme complétée'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
