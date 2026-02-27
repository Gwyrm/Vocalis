import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../api_service.dart';
import '../../providers/auth_provider.dart';
import 'delivery_detail_screen.dart';

class NurseDeliveriesScreen extends StatefulWidget {
  final ApiService apiService;

  const NurseDeliveriesScreen({
    super.key,
    required this.apiService,
  });

  @override
  State<NurseDeliveriesScreen> createState() => _NurseDeliveriesScreenState();
}

class _NurseDeliveriesScreenState extends State<NurseDeliveriesScreen> {
  late Future<List<dynamic>> _deliveriesFuture;
  String _filterStatus = 'all'; // all, pending, in_progress, completed

  @override
  void initState() {
    super.initState();
    _loadDeliveries();
  }

  void _loadDeliveries() {
    _deliveriesFuture = widget.apiService.getPatientVisits();
  }

  List<dynamic> _filterDeliveries(List<dynamic> deliveries) {
    if (_filterStatus == 'all') {
      return deliveries;
    }
    return deliveries.where((d) => d['status'] == _filterStatus).toList();
  }

  String _getStatusBadgeColor(String status) {
    switch (status) {
      case 'pending':
        return '🔴 En attente';
      case 'in_progress':
        return '🟠 En cours';
      case 'completed':
        return '🟢 Complétée';
      default:
        return status;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Mes Livraisons'),
        elevation: 0,
        actions: [
          // Menu
          Consumer<AuthProvider>(
            builder: (context, authProvider, _) {
              return PopupMenuButton(
                itemBuilder: (context) => [
                  PopupMenuItem(
                    child: const Text('Mon Profil'),
                    onTap: () {
                      // Navigate to profile
                    },
                  ),
                  PopupMenuItem(
                    child: const Text('Déconnexion'),
                    onTap: () async {
                      await authProvider.logout();
                      if (context.mounted) {
                        Navigator.of(context).pushReplacementNamed('/login');
                      }
                    },
                  ),
                ],
              );
            },
          ),
        ],
      ),
      body: Column(
        children: [
          // Filter tabs
          Container(
            color: Colors.grey[100],
            padding: const EdgeInsets.all(12),
            child: Row(
              children: [
                _buildFilterChip('all', 'Tous'),
                _buildFilterChip('pending', 'En attente'),
                _buildFilterChip('in_progress', 'En cours'),
                _buildFilterChip('completed', 'Complétées'),
              ],
            ),
          ),
          // Deliveries list
          Expanded(
            child: FutureBuilder<List<dynamic>>(
              future: _deliveriesFuture,
              builder: (context, snapshot) {
                if (snapshot.connectionState == ConnectionState.waiting) {
                  return const Center(child: CircularProgressIndicator());
                }

                if (snapshot.hasError) {
                  return Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.error_outline, size: 48, color: Colors.red),
                        const SizedBox(height: 16),
                        Text('Erreur: ${snapshot.error}'),
                        const SizedBox(height: 16),
                        ElevatedButton(
                          onPressed: () {
                            setState(() {
                              _loadDeliveries();
                            });
                          },
                          child: const Text('Réessayer'),
                        ),
                      ],
                    ),
                  );
                }

                final deliveries = _filterDeliveries(snapshot.data ?? []);

                if (deliveries.isEmpty) {
                  return Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(
                          Icons.local_shipping_outlined,
                          size: 64,
                          color: Colors.grey[300],
                        ),
                        const SizedBox(height: 16),
                        Text(
                          _filterStatus == 'all'
                              ? 'Aucune livraison assignée'
                              : 'Aucune livraison ${_filterStatus == 'pending' ? 'en attente' : _filterStatus == 'in_progress' ? 'en cours' : 'complétée'}',
                          style: TextStyle(color: Colors.grey[600], fontSize: 16),
                        ),
                      ],
                    ),
                  );
                }

                return ListView.builder(
                  padding: const EdgeInsets.all(12),
                  itemCount: deliveries.length,
                  itemBuilder: (context, index) {
                    final delivery = deliveries[index];
                    return _buildDeliveryCard(context, delivery);
                  },
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFilterChip(String value, String label) {
    final isSelected = _filterStatus == value;
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 4),
      child: FilterChip(
        label: Text(label),
        selected: isSelected,
        onSelected: (selected) {
          setState(() {
            _filterStatus = value;
          });
        },
        backgroundColor: Colors.white,
        selectedColor: Colors.deepPurple[100],
      ),
    );
  }

  Widget _buildDeliveryCard(BuildContext context, dynamic delivery) {
    final patientName = delivery['patient_name'] ?? 'Patient inconnu';
    final diagnosis = delivery['diagnosis'] ?? '';
    final address = delivery['patient_address'] ?? '';
    final status = delivery['status'] ?? '';
    final scheduledDate = delivery['scheduled_date'] ?? '';
    final deliveryId = delivery['id'] ?? '';

    return Card(
      margin: const EdgeInsets.symmetric(vertical: 8),
      elevation: 2,
      child: InkWell(
        onTap: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => DeliveryDetailScreen(
                deliveryId: deliveryId,
                apiService: widget.apiService,
                onComplete: () {
                  // Refresh list after delivery
                  setState(() {
                    _loadDeliveries();
                  });
                },
              ),
            ),
          );
        },
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Patient name and status
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          patientName,
                          style: const TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        if (diagnosis.isNotEmpty) ...[
                          const SizedBox(height: 4),
                          Text(
                            diagnosis,
                            style: TextStyle(
                              fontSize: 13,
                              color: Colors.grey[600],
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ],
                      ],
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(
                      color: _getStatusColor(status),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      _getStatusBadgeColor(status),
                      style: const TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ],
              ),
              const Divider(height: 16),
              // Address
              Row(
                children: [
                  const Icon(Icons.location_on, size: 16, color: Colors.grey),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      address,
                      style: TextStyle(color: Colors.grey[600], fontSize: 13),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              // Scheduled date
              Row(
                children: [
                  const Icon(Icons.calendar_today, size: 16, color: Colors.grey),
                  const SizedBox(width: 8),
                  Text(
                    _formatDate(scheduledDate),
                    style: TextStyle(color: Colors.grey[600], fontSize: 13),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              // Action button
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => DeliveryDetailScreen(
                          deliveryId: deliveryId,
                          apiService: widget.apiService,
                          onComplete: () {
                            setState(() {
                              _loadDeliveries();
                            });
                          },
                        ),
                      ),
                    );
                  },
                  icon: status == 'pending'
                      ? const Icon(Icons.play_arrow)
                      : const Icon(Icons.edit),
                  label: Text(
                    status == 'pending' ? 'Démarrer' : 'Continuer',
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Color _getStatusColor(String status) {
    switch (status) {
      case 'pending':
        return Colors.red[100]!;
      case 'in_progress':
        return Colors.orange[100]!;
      case 'completed':
        return Colors.green[100]!;
      default:
        return Colors.grey[100]!;
    }
  }

  String _formatDate(String dateString) {
    if (dateString.isEmpty) return 'Date non définie';
    try {
      final date = DateTime.parse(dateString);
      final now = DateTime.now();
      if (date.year == now.year && date.month == now.month && date.day == now.day) {
        return 'Aujourd\'hui';
      }
      return '${date.day}/${date.month}/${date.year}';
    } catch (e) {
      return dateString;
    }
  }

}
