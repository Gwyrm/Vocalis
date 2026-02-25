import 'package:flutter/material.dart';
import '../api_service.dart';
import '../models/patient.dart';
import 'patient_form_screen.dart';
import 'patient_detail_screen.dart';

class PatientListScreen extends StatefulWidget {
  final ApiService apiService;

  const PatientListScreen({
    Key? key,
    required this.apiService,
  }) : super(key: key);

  @override
  State<PatientListScreen> createState() => _PatientListScreenState();
}

class _PatientListScreenState extends State<PatientListScreen> {
  late Future<List<Patient>> _patientsFuture;

  @override
  void initState() {
    super.initState();
    _loadPatients();
  }

  void _loadPatients() {
    _patientsFuture = widget.apiService.getPatients();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Patients'),
        elevation: 0,
      ),
      body: FutureBuilder<List<Patient>>(
        future: _patientsFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }

          if (snapshot.hasError) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text('Erreur: ${snapshot.error}'),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () => setState(() => _loadPatients()),
                    child: const Text('Réessayer'),
                  ),
                ],
              ),
            );
          }

          final patients = snapshot.data ?? [];

          if (patients.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.person_outline, size: 64, color: Colors.grey),
                  const SizedBox(height: 16),
                  const Text('Aucun patient'),
                  const SizedBox(height: 16),
                  ElevatedButton.icon(
                    onPressed: _navigateToNewPatient,
                    icon: const Icon(Icons.add),
                    label: const Text('Ajouter un patient'),
                  ),
                ],
              ),
            );
          }

          return ListView.builder(
            padding: const EdgeInsets.all(8),
            itemCount: patients.length,
            itemBuilder: (context, index) {
              final patient = patients[index];
              return Card(
                margin: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                child: ListTile(
                  title: Text(patient.fullName),
                  subtitle: Text(
                    '${patient.ageInYears} ans • ${patient.chronicConditions.isEmpty ? "Pas de conditions chroniques" : patient.chronicConditions.join(", ")}',
                  ),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => _navigateToPatientDetail(patient),
                ),
              );
            },
          );
        },
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _navigateToNewPatient,
        icon: const Icon(Icons.add),
        label: const Text('Ajouter'),
      ),
    );
  }

  void _navigateToNewPatient() async {
    final result = await Navigator.of(context).push<bool>(
      MaterialPageRoute(
        builder: (context) => PatientFormScreen(apiService: widget.apiService),
      ),
    );
    if (result == true) {
      _loadPatients();
    }
  }

  void _navigateToPatientDetail(Patient patient) async {
    final result = await Navigator.of(context).push<bool>(
      MaterialPageRoute(
        builder: (context) => PatientDetailScreen(
          patient: patient,
          apiService: widget.apiService,
        ),
      ),
    );
    if (result == true) {
      _loadPatients();
    }
  }
}
