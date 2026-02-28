import 'package:flutter/material.dart';
import '../api_service.dart';
import '../models/intervention.dart';

class InterventionDetailScreen extends StatefulWidget {
  final String interventionId;
  final String userRole;

  const InterventionDetailScreen({
    Key? key,
    required this.interventionId,
    required this.userRole,
  }) : super(key: key);

  @override
  State<InterventionDetailScreen> createState() => _InterventionDetailScreenState();
}

class _InterventionDetailScreenState extends State<InterventionDetailScreen> {
  late ApiService apiService;
  InterventionDetail? intervention;
  List<InterventionDocument> documents = [];
  bool isLoading = false;
  bool isUpdatingStatus = false;

  @override
  void initState() {
    super.initState();
    apiService = ApiService();
    loadDetails();
  }

  Future<void> loadDetails() async {
    setState(() => isLoading = true);
    try {
      final interventionData = await apiService.getIntervention(widget.interventionId);
      final documentsData = await apiService.getInterventionDocuments(widget.interventionId);

      setState(() {
        intervention = InterventionDetail.fromJson(interventionData);
        documents = documentsData.map((item) => InterventionDocument.fromJson(item)).toList();
        documents.sort((a, b) => b.uploadedAt.compareTo(a.uploadedAt));
      });
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Erreur: ${e.toString()}')),
        );
      }
    } finally {
      setState(() => isLoading = false);
    }
  }

  Future<void> _updateStatus(String newStatus) async {
    if (intervention == null) return;

    setState(() => isUpdatingStatus = true);
    try {
      final oldStatus = intervention!.status;
      final statusChange = '$oldStatus→$newStatus';

      await apiService.logIntervention(
        widget.interventionId,
        statusChange: statusChange,
      );

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Statut mis à jour')),
      );

      await loadDetails();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Erreur: ${e.toString()}')),
        );
      }
    } finally {
      setState(() => isUpdatingStatus = false);
    }
  }

  void _showStatusTransitionDialog() {
    if (intervention == null) return;

    List<String> availableTransitions = [];
    if (intervention!.status == 'scheduled') {
      availableTransitions = ['in_progress', 'cancelled'];
    } else if (intervention!.status == 'in_progress') {
      availableTransitions = ['completed', 'cancelled'];
    }

    if (availableTransitions.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Aucune transition disponible')),
      );
      return;
    }

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Mettre à jour le statut'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: availableTransitions.map((status) {
            String label = status == 'in_progress'
                ? 'Commencer'
                : status == 'completed'
                    ? 'Marquer comme complétée'
                    : 'Annuler';
            return ListTile(
              title: Text(label),
              onTap: () {
                Navigator.pop(context);
                _updateStatus(status);
              },
            );
          }).toList(),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (isLoading) {
      return Scaffold(
        appBar: AppBar(title: const Text('Détails de l\'intervention')),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    if (intervention == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Détails de l\'intervention')),
        body: const Center(child: Text('Intervention non trouvée')),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Détails de l\'intervention'),
        elevation: 0,
        backgroundColor: Colors.blue.shade700,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header with type and status
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      intervention!.interventionType,
                      style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                          decoration: BoxDecoration(
                            color: _getStatusColor(intervention!.status),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Text(
                            intervention!.statusDisplayName,
                            style: const TextStyle(color: Colors.white),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                          decoration: BoxDecoration(
                            color: _getPriorityColor(intervention!.priority),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Text(
                            intervention!.priorityDisplayName,
                            style: const TextStyle(color: Colors.white),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Details section
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Détails', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 12),
                    _buildDetailRow('Planifiée:', intervention!.formattedScheduledDate),
                    _buildDetailRow('Priorité:', intervention!.priorityDisplayName),
                    if (intervention!.description != null)
                      _buildDetailRow('Description:', intervention!.description!),
                    _buildDetailRow('Créée le:', intervention!.formattedScheduledDate),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Status transition button
            if ((widget.userRole == 'nurse' || widget.userRole == 'doctor') &&
                intervention!.status != 'completed' &&
                intervention!.status != 'cancelled')
              ElevatedButton.icon(
                onPressed: isUpdatingStatus ? null : _showStatusTransitionDialog,
                icon: const Icon(Icons.edit),
                label: const Text('Mettre à jour le statut'),
              ),
            const SizedBox(height: 16),

            // Logs section
            const Text('Historique', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            if (intervention!.logs.isEmpty)
              const Text('Aucun historique', style: TextStyle(color: Colors.grey))
            else
              Column(
                children: intervention!.logs.map((log) {
                  return Card(
                    margin: const EdgeInsets.symmetric(vertical: 4.0),
                    child: Padding(
                      padding: const EdgeInsets.all(12.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            log.statusChange,
                            style: const TextStyle(fontWeight: FontWeight.bold),
                          ),
                          const SizedBox(height: 4),
                          Text(log.formattedLoggedAt, style: const TextStyle(fontSize: 12, color: Colors.grey)),
                          if (log.notes != null) ...[
                            const SizedBox(height: 8),
                            Text(log.notes!),
                          ],
                        ],
                      ),
                    ),
                  );
                }).toList(),
              ),
            const SizedBox(height: 16),

            // Documents section
            const Text('Documents', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            if (documents.isEmpty)
              const Text('Aucun document', style: TextStyle(color: Colors.grey))
            else
              Column(
                children: documents.map((doc) {
                  return Card(
                    margin: const EdgeInsets.symmetric(vertical: 4.0),
                    child: ListTile(
                      leading: Icon(_getDocumentIcon(doc.documentType)),
                      title: Text(doc.fileName),
                      subtitle: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('${doc.documentTypeDisplayName} - ${doc.formattedFileSize}'),
                          Text(doc.formattedUploadedAt, style: const TextStyle(fontSize: 11)),
                          if (doc.caption != null)
                            Text(doc.caption!, style: const TextStyle(fontStyle: FontStyle.italic)),
                        ],
                      ),
                    ),
                  );
                }).toList(),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4.0),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(label, style: const TextStyle(fontWeight: FontWeight.bold)),
          ),
          Expanded(child: Text(value)),
        ],
      ),
    );
  }

  Color _getStatusColor(String status) {
    switch (status) {
      case 'scheduled':
        return Colors.blue;
      case 'in_progress':
        return Colors.orange;
      case 'completed':
        return Colors.green;
      case 'cancelled':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  Color _getPriorityColor(String priority) {
    switch (priority) {
      case 'high':
        return Colors.red;
      case 'normal':
        return Colors.blue;
      case 'low':
        return Colors.green;
      default:
        return Colors.grey;
    }
  }

  IconData _getDocumentIcon(String type) {
    switch (type) {
      case 'photo':
        return Icons.image;
      case 'result':
        return Icons.description;
      case 'note':
        return Icons.note;
      default:
        return Icons.file_present;
    }
  }
}
