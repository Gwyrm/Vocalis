import 'package:flutter/material.dart';
import '../api_service.dart';
import '../models/intervention.dart';
import 'intervention_detail_screen.dart';
import 'intervention_form_screen.dart';

class InterventionListScreen extends StatefulWidget {
  final String prescriptionId;
  final String patientName;
  final String userRole;
  final ApiService apiService;

  const InterventionListScreen({
    Key? key,
    required this.prescriptionId,
    required this.patientName,
    required this.userRole,
    required this.apiService,
  }) : super(key: key);

  @override
  State<InterventionListScreen> createState() => _InterventionListScreenState();
}

class _InterventionListScreenState extends State<InterventionListScreen> {
  late ApiService apiService;
  List<Intervention> interventions = [];
  List<Intervention> filteredInterventions = [];
  bool isLoading = false;
  String selectedStatus = 'all';

  @override
  void initState() {
    super.initState();
    apiService = widget.apiService;
    loadInterventions();
  }

  Future<void> loadInterventions() async {
    setState(() => isLoading = true);
    try {
      final data = await apiService.getInterventions(
        prescriptionId: widget.prescriptionId,
      );
      final list = data.map((item) => Intervention.fromJson(item)).toList();
      list.sort((a, b) => a.scheduledDate.compareTo(b.scheduledDate));

      setState(() {
        interventions = list;
        filterByStatus();
      });
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Erreur : ${e.toString()}')));
      }
    } finally {
      setState(() => isLoading = false);
    }
  }

  void filterByStatus() {
    if (selectedStatus == 'all') {
      filteredInterventions = interventions;
    } else {
      filteredInterventions = interventions
          .where((i) => i.status == selectedStatus)
          .toList();
    }
  }

  void _onStatusFilterChanged(String? value) {
    if (value != null) {
      setState(() {
        selectedStatus = value;
        filterByStatus();
      });
    }
  }

  void _onInterventionCreated() {
    loadInterventions();
  }

  void _showCreateDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Créer une intervention'),
        content: InterventionFormScreen(
          prescriptionId: widget.prescriptionId,
          onCreated: () {
            Navigator.pop(context);
            _onInterventionCreated();
          },
          apiService: apiService,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Fermer'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Interventions - ${widget.patientName}'),
        elevation: 0,
        backgroundColor: Colors.blue.shade700,
      ),
      floatingActionButton: widget.userRole == 'doctor'
          ? FloatingActionButton(
              onPressed: _showCreateDialog,
              tooltip: 'Créer une intervention',
              child: const Icon(Icons.add),
            )
          : null,
      body: isLoading
          ? const Center(child: CircularProgressIndicator())
          : Column(
              children: [
                // Status Filter
                Padding(
                  padding: const EdgeInsets.all(8.0),
                  child: SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                    child: Row(
                      children: [
                        const Padding(
                          padding: EdgeInsets.symmetric(horizontal: 8.0),
                          child: Text(
                            'Filtre:',
                            style: TextStyle(fontWeight: FontWeight.bold),
                          ),
                        ),
                        _buildStatusChip('all', 'Tous'),
                        _buildStatusChip('scheduled', 'Planifiées'),
                        _buildStatusChip('in_progress', 'En cours'),
                        _buildStatusChip('completed', 'Complétées'),
                        _buildStatusChip('cancelled', 'Annulées'),
                      ],
                    ),
                  ),
                ),
                // Interventions List
                Expanded(
                  child: filteredInterventions.isEmpty
                      ? Center(
                          child: Text(
                            selectedStatus != 'all'
                                ? 'Aucune intervention $selectedStatus'
                                : 'Aucune intervention',
                            style: const TextStyle(color: Colors.grey),
                          ),
                        )
                      : ListView.builder(
                          itemCount: filteredInterventions.length,
                          itemBuilder: (context, index) {
                            final intervention = filteredInterventions[index];
                            return _buildInterventionCard(intervention);
                          },
                        ),
                ),
              ],
            ),
    );
  }

  Widget _buildStatusChip(String value, String label) {
    final isSelected = selectedStatus == value;
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 4.0),
      child: FilterChip(
        label: Text(label),
        selected: isSelected,
        onSelected: (_) => _onStatusFilterChanged(value),
      ),
    );
  }

  Widget _buildInterventionCard(Intervention intervention) {
    Color statusColor = Colors.grey;
    if (intervention.status == 'scheduled') statusColor = Colors.blue;
    if (intervention.status == 'in_progress') statusColor = Colors.orange;
    if (intervention.status == 'completed') statusColor = Colors.green;
    if (intervention.status == 'cancelled') statusColor = Colors.red;

    Color priorityColor = Colors.grey;
    if (intervention.priority == 'high') priorityColor = Colors.red;
    if (intervention.priority == 'normal') priorityColor = Colors.blue;
    if (intervention.priority == 'low') priorityColor = Colors.green;

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 4.0),
      child: ListTile(
        isThreeLine: true,
        title: Text(
          intervention.interventionType,
          style: const TextStyle(fontWeight: FontWeight.bold),
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 4),
            Text('Planifiée: ${intervention.formattedScheduledDate}'),
          ],
        ),
        trailing: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
              decoration: BoxDecoration(
                color: statusColor,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                intervention.statusDisplayName,
                style: const TextStyle(color: Colors.white, fontSize: 12),
              ),
            ),
            SizedBox(height: 4),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
              decoration: BoxDecoration(
                color: priorityColor.withAlpha(51), // ~20% opacity
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                intervention.priorityDisplayName,
                style: TextStyle(color: priorityColor, fontSize: 11),
              ),
            ),
          ],
        ),
        onTap: () async {
          final result = await Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => InterventionDetailScreen(
                interventionId: intervention.id,
                userRole: widget.userRole,
                apiService: apiService,
              ),
            ),
          );
          if (result == true) {
            loadInterventions();
          }
        },
      ),
    );
  }
}
