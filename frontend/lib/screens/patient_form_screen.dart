import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../api_service.dart';
import '../models/patient.dart';

class PatientFormScreen extends StatefulWidget {
  final ApiService apiService;
  final Patient? patient;

  const PatientFormScreen({
    Key? key,
    required this.apiService,
    this.patient,
  }) : super(key: key);

  @override
  State<PatientFormScreen> createState() => _PatientFormScreenState();
}

class _PatientFormScreenState extends State<PatientFormScreen> {
  late TextEditingController _firstNameController;
  late TextEditingController _lastNameController;
  late TextEditingController _phoneController;
  late TextEditingController _emailController;
  late TextEditingController _addressController;
  late TextEditingController _notesController;

  DateTime? _dateOfBirth;
  String? _gender;
  List<String> _allergies = [];
  List<String> _chronicConditions = [];
  List<String> _currentMedications = [];

  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _firstNameController = TextEditingController(text: widget.patient?.firstName ?? '');
    _lastNameController = TextEditingController(text: widget.patient?.lastName ?? '');
    _phoneController = TextEditingController(text: widget.patient?.phone ?? '');
    _emailController = TextEditingController(text: widget.patient?.email ?? '');
    _addressController = TextEditingController(text: widget.patient?.address ?? '');
    _notesController = TextEditingController(text: widget.patient?.medicalNotes ?? '');
    _dateOfBirth = widget.patient?.dateOfBirth;
    _gender = widget.patient?.gender;
    _allergies = List.from(widget.patient?.allergies ?? []);
    _chronicConditions = List.from(widget.patient?.chronicConditions ?? []);
    _currentMedications = List.from(widget.patient?.currentMedications ?? []);
  }

  @override
  void dispose() {
    _firstNameController.dispose();
    _lastNameController.dispose();
    _phoneController.dispose();
    _emailController.dispose();
    _addressController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  Future<void> _selectDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _dateOfBirth ?? DateTime.now(),
      firstDate: DateTime(1900),
      lastDate: DateTime.now(),
    );
    if (picked != null && picked != _dateOfBirth) {
      setState(() => _dateOfBirth = picked);
    }
  }

  Future<void> _submitForm() async {
    if (_firstNameController.text.isEmpty ||
        _lastNameController.text.isEmpty ||
        _dateOfBirth == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Veuillez remplir tous les champs obligatoires')),
      );
      return;
    }

    setState(() => _isLoading = true);

    try {
      if (widget.patient != null) {
        // Update existing patient
        await widget.apiService.updatePatient(
          widget.patient!.id,
          firstName: _firstNameController.text,
          lastName: _lastNameController.text,
          phone: _phoneController.text,
          email: _emailController.text,
          address: _addressController.text.isNotEmpty ? _addressController.text : null,
          gender: _gender,
          allergies: _allergies,
          chronicConditions: _chronicConditions,
          currentMedications: _currentMedications,
          medicalNotes: _notesController.text,
        );
      } else {
        // Create new patient
        await widget.apiService.createPatient(
          firstName: _firstNameController.text,
          lastName: _lastNameController.text,
          dateOfBirth: _dateOfBirth!,
          phone: _phoneController.text,
          email: _emailController.text,
          address: _addressController.text.isNotEmpty ? _addressController.text : null,
          gender: _gender,
          allergies: _allergies,
          chronicConditions: _chronicConditions,
          currentMedications: _currentMedications,
          medicalNotes: _notesController.text,
        );
      }

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(widget.patient != null
                ? 'Patient mis à jour'
                : 'Patient créé'),
          ),
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

  void _addAllergy() {
    _showAddDialog(
      title: 'Ajouter une allergie',
      onAdd: (value) {
        setState(() => _allergies.add(value));
      },
    );
  }

  void _addCondition() {
    _showAddDialog(
      title: 'Ajouter une condition chronique',
      onAdd: (value) {
        setState(() => _chronicConditions.add(value));
      },
    );
  }

  void _addMedication() {
    _showAddDialog(
      title: 'Ajouter un médicament',
      onAdd: (value) {
        setState(() => _currentMedications.add(value));
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.patient != null ? 'Éditer patient' : 'Nouveau patient'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Required Fields Section
            const Text(
              'Informations personnelles *',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _firstNameController,
              decoration: const InputDecoration(labelText: 'Prénom'),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _lastNameController,
              decoration: const InputDecoration(labelText: 'Nom'),
            ),
            const SizedBox(height: 12),
            GestureDetector(
              onTap: _selectDate,
              child: Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  border: Border.all(color: Colors.grey),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(_dateOfBirth != null
                        ? DateFormat('dd/MM/yyyy').format(_dateOfBirth!)
                        : 'Date de naissance'),
                    const Icon(Icons.calendar_today),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              value: _gender,
              decoration: const InputDecoration(labelText: 'Genre'),
              items: ['M', 'F', 'Autre']
                  .map((e) => DropdownMenuItem(value: e, child: Text(e)))
                  .toList(),
              onChanged: (value) => setState(() => _gender = value),
            ),
            const SizedBox(height: 24),

            // Contact Information
            const Text(
              'Contact',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _phoneController,
              decoration: const InputDecoration(labelText: 'Téléphone'),
              keyboardType: TextInputType.phone,
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _emailController,
              decoration: const InputDecoration(labelText: 'Email'),
              keyboardType: TextInputType.emailAddress,
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _addressController,
              decoration: const InputDecoration(labelText: 'Adresse'),
            ),
            const SizedBox(height: 24),

            // Medical Information
            const Text(
              'Informations médicales',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            _buildListSection(
              title: 'Allergies',
              items: _allergies,
              onAdd: _addAllergy,
              onRemove: (i) => setState(() => _allergies.removeAt(i)),
            ),
            const SizedBox(height: 12),
            _buildListSection(
              title: 'Conditions chroniques',
              items: _chronicConditions,
              onAdd: _addCondition,
              onRemove: (i) => setState(() => _chronicConditions.removeAt(i)),
            ),
            const SizedBox(height: 12),
            _buildListSection(
              title: 'Médicaments actuels',
              items: _currentMedications,
              onAdd: _addMedication,
              onRemove: (i) => setState(() => _currentMedications.removeAt(i)),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _notesController,
              decoration: const InputDecoration(labelText: 'Notes médicales'),
              maxLines: 3,
            ),
            const SizedBox(height: 24),

            // Submit Button
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _isLoading ? null : _submitForm,
                child: _isLoading
                    ? const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : Text(widget.patient != null ? 'Mettre à jour' : 'Créer'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildListSection({
    required String title,
    required List<String> items,
    required VoidCallback onAdd,
    required Function(int) onRemove,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(title),
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
                onDeleted: () => onRemove(entry.key),
              );
            }).toList(),
          )
        else
          const Text('Aucun élément', style: TextStyle(color: Colors.grey)),
      ],
    );
  }
}
