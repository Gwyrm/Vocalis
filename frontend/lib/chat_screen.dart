import 'dart:convert';
import 'package:universal_io/io.dart';
import 'dart:typed_data';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:open_file/open_file.dart';
import 'package:path_provider/path_provider.dart';
import 'package:signature/signature.dart';
import 'package:universal_html/html.dart' as html;
import 'api_service.dart';
import 'models/prescription_data.dart';

enum PrescriptionStage {
  informationCollection,
  review,
  signing,
}

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final TextEditingController _messageController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final ApiService _apiService = ApiService();

  // Stage management
  PrescriptionStage _currentStage = PrescriptionStage.informationCollection;
  PrescriptionData _prescriptionData = PrescriptionData();
  String _generatedPrescription = '';

  // Chat messages: {'role': 'user'|'assistant'|'system', 'content': 'text'}
  final List<Map<String, String>> _messages = [];
  bool _isLoading = false;

  // Signature controller
  final SignatureController _signatureController = SignatureController(
    penStrokeWidth: 3,
    penColor: Colors.black,
    exportBackgroundColor: Colors.transparent,
  );

  // Text controller for prescription review
  late TextEditingController _prescriptionController;

  @override
  void initState() {
    super.initState();
    _prescriptionController = TextEditingController();
    _addWelcomeMessage();
  }

  @override
  void dispose() {
    _messageController.dispose();
    _scrollController.dispose();
    _signatureController.dispose();
    _prescriptionController.dispose();
    super.dispose();
  }

  void _addWelcomeMessage() {
    final welcomeMessage =
        "Bonjour! Pour rédiger une ordonnance, j'ai besoin des informations suivantes:\n"
        "• Nom du patient\n"
        "• Âge/Date de naissance\n"
        "• Diagnostic\n"
        "• Médicament\n"
        "• Posologie\n"
        "• Durée du traitement\n"
        "• Instructions spéciales\n\n"
        "Veuillez commencer par fournir les informations du patient.";

    setState(() {
      _messages.add({
        'role': 'system',
        'content': welcomeMessage,
      });
    });
  }

  Future<void> _sendMessage() async {
    final message = _messageController.text;
    if (message.isEmpty) return;

    setState(() {
      _messages.add({'role': 'user', 'content': message});
      _isLoading = true;
    });
    _messageController.clear();
    _scrollToBottom();

    try {
      // Call simplified chat endpoint
      final response = await _apiService.chat(message);

      // Update prescription data from response
      if (response['prescription_data'] != null) {
        _prescriptionData = PrescriptionData.fromJson(response['prescription_data']);
      }

      // Add AI response to messages
      setState(() {
        _messages.add({
          'role': 'assistant',
          'content': response['response'] ?? 'Pas de réponse',
        });

        // Check if collection is complete
        if (response['is_complete'] == true) {
          _messages.add({
            'role': 'system',
            'content': '✓ Toutes les informations requises ont été collectées! '
                'Cliquez sur le bouton "Générer ordonnance" pour passer à la suite.',
          });
        } else if (response['missing_fields'] != null &&
                   (response['missing_fields'] as List).isNotEmpty) {
          // Show missing fields summary
          final missing = (response['missing_fields'] as List).join(', ');
          _messages.add({
            'role': 'system',
            'content': 'Informations manquantes: $missing',
          });
        }
      });
    } catch (e) {
      setState(() {
        _messages.add({
          'role': 'assistant',
          'content': 'Erreur: $e',
        });
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
      _scrollToBottom();
    }
  }

  Future<void> _generatePrescription() async {
    if (!_prescriptionData.isComplete()) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'Informations manquantes: ${_prescriptionData.getMissingRequiredFields().join(", ")}',
          ),
        ),
      );
      return;
    }

    setState(() {
      _isLoading = true;
    });

    try {
      // Generate prescription text locally from collected data
      final prescription = _formatPrescriptionText(_prescriptionData);
      setState(() {
        _generatedPrescription = prescription;
        _prescriptionController.text = prescription;
        _currentStage = PrescriptionStage.review;
      });
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Erreur: $e')),
        );
      }
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  String _formatPrescriptionText(PrescriptionData data) {
    return '''ORDONNANCE MEDICALE

Patient: ${data.patientName ?? 'N/A'}
Âge: ${data.patientAge ?? 'N/A'}

DIAGNOSTIC:
${data.diagnosis ?? 'N/A'}

MEDICAMENT:
${data.medication ?? 'N/A'}

POSOLOGIE:
${data.dosage ?? 'N/A'}

DUREE:
${data.duration ?? 'N/A'}

INSTRUCTIONS SPECIALES:
${data.specialInstructions ?? 'N/A'}

Date: ${DateTime.now().toLocal().toString().split(' ')[0]}''';
  }

  void _proceedToSigning() {
    setState(() {
      _generatedPrescription = _prescriptionController.text;
      _currentStage = PrescriptionStage.signing;
    });
  }

  void _backToReview() {
    setState(() {
      _currentStage = PrescriptionStage.review;
    });
  }

  void _backToCollection() {
    setState(() {
      _currentStage = PrescriptionStage.informationCollection;
    });
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Future<void> _generateAndDownloadPdf() async {
    try {
      // Verify data is complete
      if (!_prescriptionData.isComplete()) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(
                'Données incomplètes: ${_prescriptionData.getMissingRequiredFields().join(", ")}',
              ),
            ),
          );
        }
        return;
      }

      // Get signature as png bytes
      final signatureBytes = await _signatureController.toPngBytes();
      if (signatureBytes == null) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Veuillez d\'abord signer!')),
          );
        }
        return;
      }

      final signatureBase64 = base64Encode(signatureBytes);

      // Call API - now backend generates prescription from session data
      setState(() {
        _isLoading = true;
      });

      final pdfBytes = await _apiService.generatePdf(signatureBase64);

      // Handle download/save
      if (kIsWeb) {
        // Web: Create blob and download link
        final blob = html.Blob([pdfBytes], 'application/pdf');
        final url = html.Url.createObjectUrlFromBlob(blob);
        final anchor = html.AnchorElement(href: url)
          ..setAttribute("download", "prescription.pdf")
          ..click();
        html.Url.revokeObjectUrl(url);
      } else {
        // Mobile: Save to documents and open
        final dir = await getApplicationDocumentsDirectory();
        final file = File('${dir.path}/prescription_signed.pdf');
        await file.writeAsBytes(pdfBytes);
        await OpenFile.open(file.path);
      }

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Ordonnance générée avec succès!')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Erreur: $e')),
        );
      }
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Vocalis AI Care'),
        actions: [
          if (_currentStage == PrescriptionStage.informationCollection &&
              _prescriptionData.isComplete())
            IconButton(
              icon: const Icon(Icons.check_circle),
              tooltip: 'Generate Prescription',
              onPressed: _isLoading ? null : _generatePrescription,
            ),
          if (_currentStage != PrescriptionStage.informationCollection)
            IconButton(
              icon: const Icon(Icons.arrow_back),
              tooltip: 'Back to Collection',
              onPressed: _backToCollection,
            ),
        ],
      ),
      body: _buildCurrentStage(),
    );
  }

  Widget _buildCurrentStage() {
    switch (_currentStage) {
      case PrescriptionStage.informationCollection:
        return _buildInformationCollectionStage();
      case PrescriptionStage.review:
        return _buildReviewStage();
      case PrescriptionStage.signing:
        return _buildSigningStage();
    }
  }

  Widget _buildInformationCollectionStage() {
    return Column(
      children: [
        Expanded(
          child: _messages.isEmpty
              ? const Center(
                  child: Text(
                    'Start a conversation to collect prescription information.',
                    style: TextStyle(color: Colors.grey),
                  ),
                )
              : ListView.builder(
                  controller: _scrollController,
                  padding: const EdgeInsets.all(16),
                  itemCount: _messages.length,
                  itemBuilder: (context, index) {
                    final msg = _messages[index];
                    final role = msg['role'];
                    final isUser = role == 'user';
                    final isSystem = role == 'system';

                    return Align(
                      alignment:
                          isUser ? Alignment.centerRight : Alignment.centerLeft,
                      child: Container(
                        margin: const EdgeInsets.symmetric(vertical: 4),
                        padding: const EdgeInsets.all(12),
                        constraints: BoxConstraints(
                          maxWidth: MediaQuery.of(context).size.width * 0.75,
                        ),
                        decoration: BoxDecoration(
                          color: isSystem
                              ? Colors.blue[100]
                              : isUser
                                  ? Theme.of(context).colorScheme.primaryContainer
                                  : Theme.of(context)
                                      .colorScheme
                                      .secondaryContainer,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: MarkdownBody(data: msg['content'] ?? ''),
                      ),
                    );
                  },
                ),
        ),
        if (_isLoading) const LinearProgressIndicator(),
        Padding(
          padding: const EdgeInsets.all(16.0),
          child: Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _messageController,
                  decoration: const InputDecoration(
                    hintText: 'Type your message...',
                  ),
                  onSubmitted: (_) => _isLoading ? null : _sendMessage(),
                  enabled: !_isLoading,
                ),
              ),
              const SizedBox(width: 8),
              FloatingActionButton(
                onPressed: _isLoading ? null : _sendMessage,
                child: const Icon(Icons.send),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildReviewStage() {
    return Column(
      children: [
        Expanded(
          child: SingleChildScrollView(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Review Prescription',
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 16),
                  const Text(
                    'Prescription Content:',
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 8),
                  TextField(
                    controller: _prescriptionController,
                    maxLines: 12,
                    decoration: const InputDecoration(
                      border: OutlineInputBorder(),
                      hintText: 'Edit prescription text here...',
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
        Padding(
          padding: const EdgeInsets.all(16.0),
          child: Row(
            children: [
              TextButton(
                onPressed: _backToCollection,
                child: const Text('Back'),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: ElevatedButton.icon(
                  onPressed: _proceedToSigning,
                  icon: const Icon(Icons.edit),
                  label: const Text('Proceed to Signature'),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildSigningStage() {
    return Column(
      children: [
        Expanded(
          child: SingleChildScrollView(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Sign and Generate PDF',
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 16),
                  const Text(
                    'Signature:',
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 8),
                  Container(
                    decoration: BoxDecoration(
                      border: Border.all(color: Colors.grey),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Signature(
                      controller: _signatureController,
                      height: 200,
                      backgroundColor: Colors.grey[200]!,
                    ),
                  ),
                  const SizedBox(height: 8),
                  TextButton(
                    onPressed: () => _signatureController.clear(),
                    child: const Text('Clear Signature'),
                  ),
                  const SizedBox(height: 16),
                  const Text(
                    'Preview:',
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 8),
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      border: Border.all(color: Colors.grey),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: MarkdownBody(data: _generatedPrescription),
                  ),
                ],
              ),
            ),
          ),
        ),
        if (_isLoading) const LinearProgressIndicator(),
        Padding(
          padding: const EdgeInsets.all(16.0),
          child: Row(
            children: [
              TextButton(
                onPressed: _isLoading ? null : _backToReview,
                child: const Text('Back'),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: ElevatedButton.icon(
                  onPressed: _isLoading ? null : _generateAndDownloadPdf,
                  icon: const Icon(Icons.download),
                  label: const Text('Generate & Download PDF'),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
