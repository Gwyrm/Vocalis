import 'package:flutter/material.dart';
import 'dart:convert';
import '../../api_service.dart';
import 'package:signature/signature.dart';

class DeliveryDetailScreen extends StatefulWidget {
  final String deliveryId;
  final ApiService apiService;
  final VoidCallback? onComplete;

  const DeliveryDetailScreen({
    super.key,
    required this.deliveryId,
    required this.apiService,
    this.onComplete,
  });

  @override
  State<DeliveryDetailScreen> createState() => _DeliveryDetailScreenState();
}

class _DeliveryDetailScreenState extends State<DeliveryDetailScreen> {
  late Future<Map<String, dynamic>> _visitDetailsFuture;
  late Future<List<dynamic>> _devicesFuture;

  final SignatureController _signatureController = SignatureController(
    penStrokeWidth: 5,
    penColor: Colors.black,
    exportBackgroundColor: Colors.white,
  );

  final Map<String, TextEditingController> _deviceSerialControllers = {};
  final Map<String, bool> _devicePresentChecklist = {};
  final Map<String, bool> _deviceInstalledChecklist = {};
  final Map<String, TextEditingController> _deviceNotesControllers = {};

  final TextEditingController _generalNotesController = TextEditingController();

  bool _isLoading = false;
  String? _currentStatus;
  bool _patientSigned = false;

  @override
  void initState() {
    super.initState();
    _loadVisitDetails();
  }

  void _loadVisitDetails() {
    _visitDetailsFuture = widget.apiService.getVisitDetails(widget.deliveryId);
    _devicesFuture = _loadDevices();
  }

  Future<List<dynamic>> _loadDevices() async {
    try {
      final visitDetails = await widget.apiService.getVisitDetails(widget.deliveryId);
      final prescriptionId = visitDetails['prescription_id'] as String;
      final devices = await widget.apiService.getPrescriptionDevices(prescriptionId);

      // Initialize controllers for each device
      for (final device in devices) {
        final deviceId = device['id'] as String;
        _deviceSerialControllers[deviceId] = TextEditingController();
        _devicePresentChecklist[deviceId] = false;
        _deviceInstalledChecklist[deviceId] = false;
        _deviceNotesControllers[deviceId] = TextEditingController();
      }

      return devices;
    } catch (e) {
      rethrow;
    }
  }

  Future<void> _handleStartDelivery() async {
    if (_currentStatus == 'pending') {
      try {
        setState(() => _isLoading = true);
        await widget.apiService.updateVisitStatus(widget.deliveryId, 'in_progress');
        if (mounted) {
          setState(() => _currentStatus = 'in_progress');
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Livraison démarrée')),
          );
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
  }

  Future<void> _handleCompleteDelivery() async {
    // Validate all devices are confirmed
    final devices = await _devicesFuture;
    bool allConfirmed = true;
    for (final device in devices) {
      final deviceId = device['id'] as String;
      if (!(_devicePresentChecklist[deviceId] ?? false) ||
          !(_deviceInstalledChecklist[deviceId] ?? false) ||
          (_deviceSerialControllers[deviceId]?.text.isEmpty ?? true)) {
        allConfirmed = false;
        break;
      }
    }

    if (!allConfirmed) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Veuillez confirmer tous les appareils')),
        );
      }
      return;
    }

    // Check if signature is present
    if (_signatureController.isEmpty) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Signature du patient requise')),
        );
      }
      return;
    }

    // Check if patient confirmed signature
    if (!_patientSigned) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Veuillez confirmer la signature')),
        );
      }
      return;
    }

    try {
      setState(() => _isLoading = true);

      // Get first device serial for now (can be extended for multiple devices)
      final devices = await _devicesFuture;
      final firstDeviceId = devices.isNotEmpty ? devices[0]['id'] as String : '';
      final deviceSerial = _deviceSerialControllers[firstDeviceId]?.text ?? '';

      // For now, send empty signature - can be enhanced to export image later
      await widget.apiService.completeDeviceDelivery(
        widget.deliveryId,
        deviceSerial,
        _generalNotesController.text,
        null, // signature - can be enhanced later
      );

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Livraison complétée avec succès')),
        );
        widget.onComplete?.call();
        Navigator.pop(context);
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
        title: const Text('Détails de Livraison'),
        elevation: 0,
      ),
      body: FutureBuilder<Map<String, dynamic>>(
        future: _visitDetailsFuture,
        builder: (context, visitSnapshot) {
          if (visitSnapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }

          if (visitSnapshot.hasError) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.error_outline, size: 48, color: Colors.red),
                  const SizedBox(height: 16),
                  Text('Erreur: ${visitSnapshot.error}'),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () {
                      setState(() => _loadVisitDetails());
                    },
                    child: const Text('Réessayer'),
                  ),
                ],
              ),
            );
          }

          final visitData = visitSnapshot.data ?? {};
          _currentStatus = visitData['status'] as String?;
          final patientName = visitData['patient_name'] as String? ?? 'Patient inconnu';
          final patientAddress = visitData['patient_address'] as String? ?? '';
          final scheduledDate = visitData['scheduled_date'] as String? ?? '';

          return FutureBuilder<List<dynamic>>(
            future: _devicesFuture,
            builder: (context, devicesSnapshot) {
              if (devicesSnapshot.connectionState == ConnectionState.waiting) {
                return const Center(child: CircularProgressIndicator());
              }

              if (devicesSnapshot.hasError) {
                return Center(
                  child: Text('Erreur: ${devicesSnapshot.error}'),
                );
              }

              final devices = devicesSnapshot.data ?? [];

              return SingleChildScrollView(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Patient Information
                    Card(
                      margin: const EdgeInsets.only(bottom: 16),
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Informations Patient',
                              style: Theme.of(context).textTheme.titleLarge,
                            ),
                            const Divider(height: 16),
                            Row(
                              children: [
                                const Icon(Icons.person, size: 20, color: Colors.grey),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      const Text('Patient', style: TextStyle(fontSize: 12, color: Colors.grey)),
                                      Text(patientName, style: const TextStyle(fontWeight: FontWeight.bold)),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 12),
                            Row(
                              children: [
                                const Icon(Icons.location_on, size: 20, color: Colors.grey),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      const Text('Adresse', style: TextStyle(fontSize: 12, color: Colors.grey)),
                                      Text(patientAddress, style: const TextStyle(fontWeight: FontWeight.bold)),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 12),
                            Row(
                              children: [
                                const Icon(Icons.calendar_today, size: 20, color: Colors.grey),
                                const SizedBox(width: 12),
                                Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    const Text('Date programmée', style: TextStyle(fontSize: 12, color: Colors.grey)),
                                    Text(_formatDate(scheduledDate), style: const TextStyle(fontWeight: FontWeight.bold)),
                                  ],
                                ),
                              ],
                            ),
                            const SizedBox(height: 12),
                            Row(
                              children: [
                                const Icon(Icons.info, size: 20, color: Colors.grey),
                                const SizedBox(width: 12),
                                Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    const Text('Statut', style: TextStyle(fontSize: 12, color: Colors.grey)),
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                                      decoration: BoxDecoration(
                                        color: _getStatusColor(_currentStatus ?? ''),
                                        borderRadius: BorderRadius.circular(8),
                                      ),
                                      child: Text(
                                        _getStatusLabel(_currentStatus ?? ''),
                                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
                                      ),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    ),

                    // Devices Section
                    if (devices.isNotEmpty) ...[
                      Text(
                        'Appareils à Livrer',
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                      const SizedBox(height: 12),
                      ...devices.map((device) => _buildDeviceCard(device)),
                    ],

                    const SizedBox(height: 16),

                    // General Notes
                    Text(
                      'Notes Générales',
                      style: Theme.of(context).textTheme.titleLarge,
                    ),
                    const SizedBox(height: 8),
                    TextField(
                      controller: _generalNotesController,
                      maxLines: 3,
                      decoration: InputDecoration(
                        hintText: 'Notes de la livraison...',
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(8),
                        ),
                      ),
                    ),

                    const SizedBox(height: 16),

                    // Signature Section
                    Text(
                      'Signature du Patient',
                      style: Theme.of(context).textTheme.titleLarge,
                    ),
                    const SizedBox(height: 8),
                    Container(
                      decoration: BoxDecoration(
                        border: Border.all(color: Colors.grey[300]!),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Signature(
                        controller: _signatureController,
                        height: 200,
                        backgroundColor: Colors.grey[50]!,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        Expanded(
                          child: ElevatedButton.icon(
                            onPressed: () {
                              _signatureController.clear();
                            },
                            icon: const Icon(Icons.clear),
                            label: const Text('Effacer'),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.grey[300],
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    CheckboxListTile(
                      contentPadding: EdgeInsets.zero,
                      title: const Text('Patient a signé'),
                      subtitle: const Text('Je confirme que le patient a signé ci-dessus'),
                      value: _patientSigned,
                      onChanged: (value) {
                        setState(() {
                          _patientSigned = value ?? false;
                        });
                      },
                    ),

                    const SizedBox(height: 24),

                    // Action Buttons
                    if (_currentStatus == 'pending')
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton.icon(
                          onPressed: _isLoading ? null : _handleStartDelivery,
                          icon: const Icon(Icons.play_arrow),
                          label: const Text('Démarrer la Livraison'),
                        ),
                      ),
                    if (_currentStatus == 'in_progress') ...[
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton.icon(
                          onPressed: _isLoading ? null : _handleCompleteDelivery,
                          icon: const Icon(Icons.check_circle),
                          label: const Text('Compléter la Livraison'),
                        ),
                      ),
                      const SizedBox(height: 8),
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton.icon(
                          onPressed: _isLoading ? null : () => Navigator.pop(context),
                          icon: const Icon(Icons.cancel),
                          label: const Text('Annuler'),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.grey[400],
                          ),
                        ),
                      ),
                    ],
                  ],
                ),
              );
            },
          );
        },
      ),
    );
  }

  Widget _buildDeviceCard(dynamic device) {
    final deviceId = device['id'] as String;
    final deviceName = device['device_name'] as String? ?? 'Appareil inconnu';
    final quantity = device['quantity'] as int? ?? 1;
    final instructions = device['instructions'] as String?;
    final priority = device['priority'] as String? ?? 'normal';

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Device Name and Priority
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        deviceName,
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      Text(
                        'Quantité: $quantity',
                        style: TextStyle(color: Colors.grey[600], fontSize: 12),
                      ),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: _getPriorityColor(priority),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    priority.toUpperCase(),
                    style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold),
                  ),
                ),
              ],
            ),
            if (instructions != null && instructions.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(
                'Instructions: $instructions',
                style: TextStyle(color: Colors.grey[600], fontSize: 12, fontStyle: FontStyle.italic),
              ),
            ],
            const Divider(height: 16),
            // Device Present Checkbox
            CheckboxListTile(
              contentPadding: EdgeInsets.zero,
              title: const Text('Appareil présent'),
              value: _devicePresentChecklist[deviceId] ?? false,
              onChanged: (value) {
                setState(() {
                  _devicePresentChecklist[deviceId] = value ?? false;
                });
              },
            ),
            // Serial Number Input
            if (_devicePresentChecklist[deviceId] ?? false)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 8),
                child: TextField(
                  controller: _deviceSerialControllers[deviceId],
                  decoration: InputDecoration(
                    labelText: 'Numéro de série',
                    hintText: 'Entrez le numéro de série',
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(6),
                    ),
                  ),
                ),
              ),
            // Installation Checkbox
            if (_devicePresentChecklist[deviceId] ?? false)
              CheckboxListTile(
                contentPadding: EdgeInsets.zero,
                title: const Text('Installation confirmée'),
                value: _deviceInstalledChecklist[deviceId] ?? false,
                onChanged: (value) {
                  setState(() {
                    _deviceInstalledChecklist[deviceId] = value ?? false;
                  });
                },
              ),
            // Installation Notes
            if (_deviceInstalledChecklist[deviceId] ?? false)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 8),
                child: TextField(
                  controller: _deviceNotesControllers[deviceId],
                  maxLines: 2,
                  decoration: InputDecoration(
                    labelText: 'Notes d\'installation',
                    hintText: 'Ex: Testé, calibré, patient instruit...',
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(6),
                    ),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
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

  String _getStatusLabel(String status) {
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

  Color _getPriorityColor(String priority) {
    switch (priority.toLowerCase()) {
      case 'high':
        return Colors.red[200]!;
      case 'normal':
        return Colors.blue[200]!;
      case 'low':
        return Colors.green[200]!;
      default:
        return Colors.grey[200]!;
    }
  }

  @override
  void dispose() {
    _signatureController.dispose();
    _generalNotesController.dispose();
    for (final controller in _deviceSerialControllers.values) {
      controller.dispose();
    }
    for (final controller in _deviceNotesControllers.values) {
      controller.dispose();
    }
    super.dispose();
  }
}
