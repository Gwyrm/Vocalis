import 'package:flutter/material.dart';
import '../api_service.dart';

class InterventionFormScreen extends StatefulWidget {
  final String prescriptionId;
  final VoidCallback onCreated;

  const InterventionFormScreen({
    Key? key,
    required this.prescriptionId,
    required this.onCreated,
  }) : super(key: key);

  @override
  State<InterventionFormScreen> createState() => _InterventionFormScreenState();
}

class _InterventionFormScreenState extends State<InterventionFormScreen> {
  late ApiService apiService;
  final _formKey = GlobalKey<FormState>();

  final _interventionTypeController = TextEditingController();
  final _descriptionController = TextEditingController();
  DateTime _scheduledDate = DateTime.now().add(Duration(days: 1));
  String _priority = 'normal';
  bool isSubmitting = false;

  @override
  void initState() {
    super.initState();
    apiService = ApiService();
  }

  @override
  void dispose() {
    _interventionTypeController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  Future<void> _selectDate(BuildContext context) async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _scheduledDate,
      firstDate: DateTime.now(),
      lastDate: DateTime.now().add(Duration(days: 365)),
    );
    if (picked != null && picked != _scheduledDate) {
      // If date picked, use time picker
      if (mounted) {
        final timeOfDay = await showTimePicker(
          context: context,
          initialTime: TimeOfDay.fromDateTime(_scheduledDate),
        );
        if (timeOfDay != null) {
          setState(() {
            _scheduledDate = picked.replaceHour(timeOfDay.hour).replaceMinute(timeOfDay.minute);
          });
        }
      }
    }
  }

  Future<void> _submitForm() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => isSubmitting = true);
    try {
      await apiService.createIntervention(
        prescriptionId: widget.prescriptionId,
        interventionType: _interventionTypeController.text.trim(),
        description: _descriptionController.text.isEmpty ? null : _descriptionController.text.trim(),
        scheduledDate: _scheduledDate,
        priority: _priority,
      );

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Intervention créée')),
        );
        widget.onCreated();
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
    return Form(
      key: _formKey,
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Intervention Type
            TextFormField(
              controller: _interventionTypeController,
              decoration: const InputDecoration(
                labelText: 'Type d\'intervention',
                hintText: 'Ex: Test sanguin, Suivi téléphonique',
                border: OutlineInputBorder(),
              ),
              validator: (value) {
                if (value == null || value.trim().isEmpty) {
                  return 'Le type d\'intervention est requis';
                }
                return null;
              },
            ),
            const SizedBox(height: 16),

            // Description
            TextFormField(
              controller: _descriptionController,
              decoration: const InputDecoration(
                labelText: 'Description (optionnel)',
                border: OutlineInputBorder(),
              ),
              maxLines: 3,
            ),
            const SizedBox(height: 16),

            // Scheduled Date
            InkWell(
              onTap: () => _selectDate(context),
              child: InputDecorator(
                decoration: const InputDecoration(
                  labelText: 'Date et heure prévues',
                  border: OutlineInputBorder(),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      '${_scheduledDate.day}/${_scheduledDate.month}/${_scheduledDate.year} '
                      '${_scheduledDate.hour.toString().padLeft(2, '0')}:'
                      '${_scheduledDate.minute.toString().padLeft(2, '0')}',
                    ),
                    const Icon(Icons.calendar_today),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Priority
            InputDecorator(
              decoration: const InputDecoration(
                labelText: 'Priorité',
                border: OutlineInputBorder(),
              ),
              child: DropdownButton<String>(
                value: _priority,
                isExpanded: true,
                underline: SizedBox(),
                items: const [
                  DropdownMenuItem(value: 'low', child: Text('Basse')),
                  DropdownMenuItem(value: 'normal', child: Text('Normale')),
                  DropdownMenuItem(value: 'high', child: Text('Haute')),
                ]
                    .map((item) => DropdownMenuItem(
                          value: item.value,
                          child: item.child,
                        ))
                    .toList(),
                onChanged: (value) {
                  if (value != null) {
                    setState(() => _priority = value);
                  }
                },
              ),
            ),
            const SizedBox(height: 24),

            // Submit Button
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: isSubmitting ? null : _submitForm,
                child: isSubmitting
                    ? const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Text('Créer l\'intervention'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

extension DateTimeExtension on DateTime {
  DateTime replaceHour(int hour) {
    return DateTime(year, month, day, hour, minute, second, millisecond, microsecond);
  }

  DateTime replaceMinute(int minute) {
    return DateTime(year, month, day, hour, minute, second, millisecond, microsecond);
  }
}
