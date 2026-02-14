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

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final TextEditingController _messageController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final ApiService _apiService = ApiService();
  
  // List of messages: {'role': 'user'|'assistant', 'content': 'text'}
  final List<Map<String, String>> _messages = [];
  bool _isLoading = false;

  // Signature controller
  final SignatureController _signatureController = SignatureController(
    penStrokeWidth: 3,
    penColor: Colors.black,
    exportBackgroundColor: Colors.transparent,
  );

  @override
  void dispose() {
    _messageController.dispose();
    _scrollController.dispose();
    _signatureController.dispose();
    super.dispose();
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
      final response = await _apiService.chat(message);
      setState(() {
        _messages.add({'role': 'assistant', 'content': response});
      });
    } catch (e) {
      setState(() {
        _messages.add({'role': 'assistant', 'content': 'Error: $e'});
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
      _scrollToBottom();
    }
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

  Future<void> _showPrescriptionDialog() async {
    // Determine initial content from last AI message, or empty
    String initialContent = "";
    if (_messages.isNotEmpty && _messages.last['role'] == 'assistant') {
      initialContent = _messages.last['content']!;
    }

    final prescriptionController = TextEditingController(text: initialContent);

    await showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        title: const Text('Review & Sign Prescription'),
        content: SizedBox(
          width: MediaQuery.of(context).size.width * 0.8,
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Prescription Content:', style: TextStyle(fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                TextField(
                  controller: prescriptionController,
                  maxLines: 8,
                  decoration: const InputDecoration(
                    border: OutlineInputBorder(),
                    hintText: 'Edit prescription text here...',
                  ),
                ),
                const SizedBox(height: 16),
                const Text('Signature:', style: TextStyle(fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                Container(
                  decoration: BoxDecoration(
                    border: Border.all(color: Colors.grey),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Signature(
                    controller: _signatureController,
                    height: 150,
                    backgroundColor: Colors.grey[200]!,
                  ),
                ),
                TextButton(
                  onPressed: () => _signatureController.clear(),
                  child: const Text('Clear Signature'),
                ),
              ],
            ),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              _signatureController.clear();
            },
            child: const Text('Cancel'),
          ),
          ElevatedButton.icon(
            onPressed: () async {
              if (_signatureController.isEmpty) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Please sign first!')),
                );
                return;
              }
              Navigator.pop(context);
              await _generateAndDownloadPdf(prescriptionController.text);
            },
            icon: const Icon(Icons.download),
            label: const Text('Generate PDF & Sign'),
          ),
        ],
      ),
    );
  }

  Future<void> _generateAndDownloadPdf(String content) async {
    try {
      // Get signature as png bytes
      final signatureBytes = await _signatureController.toPngBytes();
      if (signatureBytes == null) return;
      
      final signatureBase64 = base64Encode(signatureBytes);

      // Call API
      final pdfBytes = await _apiService.generatePdf(content, signatureBase64);

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
          const SnackBar(content: Text('Prescription generated successfully!')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error generating PDF: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Vocalis AI Care'),
        actions: [
          IconButton(
            icon: const Icon(Icons.description),
            onPressed: _showPrescriptionDialog,
            tooltip: 'Create Prescription',
          ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: _messages.isEmpty
                ? const Center(
                    child: Text(
                      'Start a conversation with AI to generate a prescription.',
                      style: TextStyle(color: Colors.grey),
                    ),
                  )
                : ListView.builder(
                    controller: _scrollController,
                    padding: const EdgeInsets.all(16),
                    itemCount: _messages.length,
                    itemBuilder: (context, index) {
                      final msg = _messages[index];
                      final isUser = msg['role'] == 'user';
                      return Align(
                        alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
                        child: Container(
                          margin: const EdgeInsets.symmetric(vertical: 4),
                          padding: const EdgeInsets.all(12),
                          constraints: BoxConstraints(
                            maxWidth: MediaQuery.of(context).size.width * 0.75,
                          ),
                          decoration: BoxDecoration(
                            color: isUser
                                ? Theme.of(context).colorScheme.primaryContainer
                                : Theme.of(context).colorScheme.secondaryContainer,
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
                    onSubmitted: (_) => _sendMessage(),
                  ),
                ),
                const SizedBox(width: 8),
                FloatingActionButton(
                  onPressed: _sendMessage,
                  child: const Icon(Icons.send),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
