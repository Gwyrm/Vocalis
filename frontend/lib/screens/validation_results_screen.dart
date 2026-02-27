import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/patient.dart';
import '../models/prescription.dart';
import '../api_service.dart';

class ValidationResultsScreen extends StatefulWidget {
  final PrescriptionValidationResponse result;
  final Patient patient;
  final ApiService apiService;

  const ValidationResultsScreen({
    Key? key,
    required this.result,
    required this.patient,
    required this.apiService,
  }) : super(key: key);

  @override
  State<ValidationResultsScreen> createState() => _ValidationResultsScreenState();
}

class _ValidationResultsScreenState extends State<ValidationResultsScreen> {
  late List<String> _allergies;
  late List<String> _chronicConditions;
  late List<String> _currentMedications;
  bool _isEditingPatient = false;
  bool _isSavingChanges = false;
  bool _hasChanges = false;

  @override
  void initState() {
    super.initState();
    _allergies = List.from(widget.patient.allergies);
    _chronicConditions = List.from(widget.patient.chronicConditions);
    _currentMedications = List.from(widget.patient.currentMedications);
  }

  Color _getSeverityColor(String severity) {
    switch (severity) {
      case 'high':
        return Colors.red;
      case 'medium':
        return Colors.orange;
      case 'low':
        return Colors.amber;
      default:
        return Colors.grey;
    }
  }

  void _checkChanges() {
    _hasChanges = (_allergies != widget.patient.allergies) ||
        (_chronicConditions != widget.patient.chronicConditions) ||
        (_currentMedications != widget.patient.currentMedications);
    setState(() {});
  }

  Future<void> _savePatientChanges() async {
    setState(() => _isSavingChanges = true);
    try {
      await widget.apiService.updatePatient(
        widget.patient.id,
        firstName: widget.patient.firstName,
        lastName: widget.patient.lastName,
        allergies: _allergies,
        chronicConditions: _chronicConditions,
        currentMedications: _currentMedications,
      );
      if (mounted) {
        setState(() {
          _isEditingPatient = false;
          _hasChanges = false;
        });
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Informations patient mises à jour')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Erreur: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _isSavingChanges = false);
    }
  }

  void _addAllergy() {
    _showAddDialog(
      title: 'Ajouter une allergie',
      onAdd: (value) {
        setState(() {
          if (!_allergies.contains(value)) {
            _allergies.add(value);
            _checkChanges();
          }
        });
      },
    );
  }

  void _addCondition() {
    _showAddDialog(
      title: 'Ajouter une condition chronique',
      onAdd: (value) {
        setState(() {
          if (!_chronicConditions.contains(value)) {
            _chronicConditions.add(value);
            _checkChanges();
          }
        });
      },
    );
  }

  void _addMedication() {
    _showAddDialog(
      title: 'Ajouter un médicament',
      onAdd: (value) {
        setState(() {
          if (!_currentMedications.contains(value)) {
            _currentMedications.add(value);
            _checkChanges();
          }
        });
      },
    );
  }

  void _showAddDialog({
    required String title,
    required Function(String) onAdd,
  }) {
    final controller = TextEditingController();
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(title),
        content: TextField(
          controller: controller,
          decoration: const InputDecoration(hintText: 'Entrez une valeur'),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Annuler'),
          ),
          TextButton(
            onPressed: () {
              if (controller.text.isNotEmpty) {
                onAdd(controller.text);
                Navigator.pop(context);
              }
            },
            child: const Text('Ajouter'),
          ),
        ],
      ),
    );
  }

  Widget _buildListSection({
    required String title,
    required List<String> items,
    required VoidCallback onAdd,
    required Function(int) onRemove,
    required bool isEditing,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(title),
            if (isEditing)
              IconButton(
                icon: const Icon(Icons.add),
                onPressed: onAdd,
                constraints: const BoxConstraints.tightFor(width: 40, height: 40),
                padding: EdgeInsets.zero,
              ),
          ],
        ),
        if (items.isNotEmpty)
          Wrap(
            spacing: 8,
            children: items.asMap().entries.map((entry) {
              return Chip(
                label: Text(entry.value),
                onDeleted: isEditing ? () => setState(() {
                  items.removeAt(entry.key);
                  _checkChanges();
                }) : null,
              );
            }).toList(),
          )
        else
          const Text('Aucun élément', style: TextStyle(color: Colors.grey)),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Résultats de validation'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Status Card
            Card(
              color: widget.result.validation.valid ? Colors.green.shade50 : Colors.red.shade50,
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(
                          widget.result.validation.valid ? Icons.check_circle : Icons.error,
                          color: widget.result.validation.valid ? Colors.green : Colors.red,
                          size: 32,
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                widget.result.validation.valid
                                    ? 'Ordonnance valide'
                                    : 'Ordonnance invalide',
                                style: const TextStyle(
                                  fontSize: 18,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              Text(
                                'Confiance: ${(widget.result.validation.confidence * 100).toStringAsFixed(0)}%',
                                style: const TextStyle(fontSize: 14),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),

            // Patient Information with Edit Capability
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Patient',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                ),
                if (!_isEditingPatient)
                  TextButton.icon(
                    onPressed: () => setState(() => _isEditingPatient = true),
                    icon: const Icon(Icons.edit),
                    label: const Text('Modifier'),
                  ),
              ],
            ),
            const SizedBox(height: 8),
            Card(
              color: _isEditingPatient ? Colors.blue.shade50 : null,
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      widget.patient.fullName,
                      style: const TextStyle(fontWeight: FontWeight.bold),
                    ),
                    Text('${widget.patient.ageInYears} ans'),
                    const SizedBox(height: 12),
                    _buildListSection(
                      title: 'Allergies',
                      items: _allergies,
                      onAdd: _addAllergy,
                      onRemove: (i) => setState(() {
                        _allergies.removeAt(i);
                        _checkChanges();
                      }),
                      isEditing: _isEditingPatient,
                    ),
                    const SizedBox(height: 12),
                    _buildListSection(
                      title: 'Conditions chroniques',
                      items: _chronicConditions,
                      onAdd: _addCondition,
                      onRemove: (i) => setState(() {
                        _chronicConditions.removeAt(i);
                        _checkChanges();
                      }),
                      isEditing: _isEditingPatient,
                    ),
                    const SizedBox(height: 12),
                    _buildListSection(
                      title: 'Médicaments actuels',
                      items: _currentMedications,
                      onAdd: _addMedication,
                      onRemove: (i) => setState(() {
                        _currentMedications.removeAt(i);
                        _checkChanges();
                      }),
                      isEditing: _isEditingPatient,
                    ),
                    if (_isEditingPatient) ...[
                      const SizedBox(height: 16),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.end,
                        children: [
                          TextButton(
                            onPressed: _isSavingChanges
                                ? null
                                : () {
                                    setState(() {
                                      _isEditingPatient = false;
                                      _allergies = List.from(widget.patient.allergies);
                                      _chronicConditions =
                                          List.from(widget.patient.chronicConditions);
                                      _currentMedications =
                                          List.from(widget.patient.currentMedications);
                                      _hasChanges = false;
                                    });
                                  },
                            child: const Text('Annuler'),
                          ),
                          const SizedBox(width: 8),
                          ElevatedButton.icon(
                            onPressed: _isSavingChanges || !_hasChanges
                                ? null
                                : _savePatientChanges,
                            icon: _isSavingChanges
                                ? const SizedBox(
                                    width: 16,
                                    height: 16,
                                    child: CircularProgressIndicator(strokeWidth: 2),
                                  )
                                : const Icon(Icons.save),
                            label: const Text('Enregistrer'),
                          ),
                        ],
                      ),
                    ],
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),

            // Prescription Data
            if (widget.result.prescription != null) ...[
              const Text(
                'Ordonnance',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _buildRow('Médication:', widget.result.prescription!.medication),
                      const SizedBox(height: 8),
                      _buildRow('Posologie:', widget.result.prescription!.dosage),
                      const SizedBox(height: 8),
                      _buildRow('Durée:', widget.result.prescription!.duration),
                      if (widget.result.prescription!.specialInstructions != null)
                        Padding(
                          padding: const EdgeInsets.only(top: 8),
                          child: _buildRow(
                            'Instructions:',
                            widget.result.prescription!.specialInstructions!,
                          ),
                        ),
                      const SizedBox(height: 8),
                      _buildRow(
                        'Créée:',
                        DateFormat('dd/MM/yyyy HH:mm')
                            .format(widget.result.prescription!.createdAt),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),
            ],

            // Errors
            if (widget.result.validation.errors.isNotEmpty) ...[
              const Text(
                'Erreurs',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.red),
              ),
              const SizedBox(height: 8),
              ...widget.result.validation.errors.map((error) {
                return Card(
                  color: Colors.red.shade50,
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Icon(Icons.error, color: Colors.red, size: 20),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                error.type,
                                style: const TextStyle(
                                  fontWeight: FontWeight.bold,
                                  color: Colors.red,
                                ),
                              ),
                              Text(error.message),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              }).toList(),
              const SizedBox(height: 24),
            ],

            // Warnings
            if (widget.result.validation.warnings.isNotEmpty) ...[
              const Text(
                'Avertissements',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.orange),
              ),
              const SizedBox(height: 8),
              ...widget.result.validation.warnings.map((warning) {
                final color = _getSeverityColor(warning.severity);
                return Card(
                  color: color.withOpacity(0.1),
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Icon(Icons.warning, color: color, size: 20),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                warning.type,
                                style: TextStyle(
                                  fontWeight: FontWeight.bold,
                                  color: color,
                                ),
                              ),
                              Text(warning.message),
                              Text(
                                'Sévérité: ${warning.severity}',
                                style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              }).toList(),
              const SizedBox(height: 24),
            ],

            // Success Message
            if (widget.result.validation.valid && widget.result.validation.errors.isEmpty)
              Card(
                color: Colors.green.shade50,
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Row(
                    children: [
                      const Icon(Icons.check_circle, color: Colors.green, size: 32),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: const [
                            Text(
                              'Ordonnance valide',
                              style: TextStyle(
                                fontWeight: FontWeight.bold,
                                fontSize: 16,
                                color: Colors.green,
                              ),
                            ),
                            Text('L\'ordonnance a été créée avec succès.'),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),

            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () {
                  // Pop twice: validation screen, then text/voice prescription screen
                  Navigator.of(context).pop();
                  Navigator.of(context).pop();
                },
                child: const Text('Retour au patient'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRow(String label, String value) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: 100,
          child: Text(
            label,
            style: const TextStyle(fontWeight: FontWeight.bold),
          ),
        ),
        Expanded(child: Text(value)),
      ],
    );
  }
}
