import 'package:flutter/material.dart';
import 'package:record/record.dart';
import 'package:path_provider/path_provider.dart';
import 'package:flutter/foundation.dart';
import 'dart:async';
import 'dart:io';
import '../api_service.dart';
import '../models/patient.dart';
import 'validation_results_screen.dart';

class VoicePrescriptionScreen extends StatefulWidget {
  final Patient patient;
  final ApiService apiService;

  const VoicePrescriptionScreen({
    Key? key,
    required this.patient,
    required this.apiService,
  }) : super(key: key);

  @override
  State<VoicePrescriptionScreen> createState() =>
      _VoicePrescriptionScreenState();
}

class _VoicePrescriptionScreenState extends State<VoicePrescriptionScreen> {
  late final AudioRecorder _recorder;
  bool _isRecording = false;
  bool _isProcessing = false;
  Duration _recordingDuration = Duration.zero;
  Timer? _timer;
  String? _filePath;

  @override
  void initState() {
    super.initState();
    _recorder = AudioRecorder();
  }

  @override
  void dispose() {
    _timer?.cancel();
    _recorder.dispose();
    super.dispose();
  }

  Future<void> _startRecording() async {
    try {
      // Check for permission
      if (!(await _recorder.hasPermission())) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Permission de microphone refusée')),
        );
        return;
      }

      // Generate file path for recording
      final dir = await getApplicationDocumentsDirectory();
      final fileName = 'prescription_${DateTime.now().millisecondsSinceEpoch}.wav';
      _filePath = '${dir.path}/$fileName';

      // Simulate recording by setting a flag
      // TODO: Implement actual recording with record package
      setState(() {
        _isRecording = true;
        _recordingDuration = Duration.zero;
      });

      _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
        setState(() {
          _recordingDuration += const Duration(seconds: 1);
        });
      });
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Erreur: $e')),
      );
    }
  }

  Future<void> _stopRecording() async {
    try {
      _timer?.cancel();
      _filePath = await _recorder.stop();
      setState(() => _isRecording = false);

      if (_filePath != null) {
        _processRecording();
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Erreur: $e')),
      );
    }
  }

  Future<void> _processRecording() async {
    setState(() => _isProcessing = true);

    try {
      // Read the audio file
      final audioBytes = await _readAudioFile(_filePath!);

      // Create prescription with voice
      final result = await widget.apiService.createVoicePrescription(
        patientId: widget.patient.id,
        audioBytes: audioBytes,
      );

      if (mounted) {
        Navigator.of(context).push(
          MaterialPageRoute(
            builder: (context) => ValidationResultsScreen(
              result: result,
              patient: widget.patient,
              apiService: widget.apiService,
            ),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Erreur: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _isProcessing = false);
    }
  }

  Future<List<int>> _readAudioFile(String filePath) async {
    try {
      final file = File(filePath);
      if (await file.exists()) {
        return await file.readAsBytes();
      }
      return [];
    } catch (e) {
      return [];
    }
  }

  String _formatDuration(Duration duration) {
    final minutes = duration.inMinutes;
    final seconds = duration.inSeconds.remainder(60);
    return '$minutes:${seconds.toString().padLeft(2, '0')}';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Ordonnance vocale'),
            Text(widget.patient.fullName, style: const TextStyle(fontSize: 12)),
          ],
        ),
      ),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(
                'Patient: ${widget.patient.fullName}',
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 16),
              Text(
                _isRecording
                    ? 'Enregistrement en cours...'
                    : (_filePath != null ? 'Enregistrement prêt' : 'Appuyez pour enregistrer'),
                style: TextStyle(
                  fontSize: 16,
                  color: Colors.grey.shade600,
                ),
              ),
              const SizedBox(height: 32),

              // Recording Duration
              if (_isRecording)
                Text(
                  _formatDuration(_recordingDuration),
                  style: const TextStyle(
                    fontSize: 48,
                    fontWeight: FontWeight.bold,
                    color: Colors.red,
                  ),
                ),
              const SizedBox(height: 32),

              // Record Button
              if (!_isProcessing)
                FloatingActionButton.large(
                  onPressed: _isRecording ? _stopRecording : _startRecording,
                  backgroundColor: _isRecording ? Colors.red : Colors.blue,
                  child: Icon(
                    _isRecording ? Icons.stop : Icons.mic,
                    size: 32,
                  ),
                )
              else
                const SizedBox(
                  width: 80,
                  height: 80,
                  child: CircularProgressIndicator(strokeWidth: 4),
                ),

              const SizedBox(height: 32),

              // Transcribe Button
              if (_filePath != null && !_isRecording && !_isProcessing)
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton.icon(
                    onPressed: _processRecording,
                    icon: const Icon(Icons.check),
                    label: const Text('Transcrire et valider'),
                  ),
                ),

              const SizedBox(height: 16),

              // Retry Button
              if (_filePath != null && !_isProcessing)
                SizedBox(
                  width: double.infinity,
                  child: OutlinedButton.icon(
                    onPressed: () {
                      setState(() => _filePath = null);
                    },
                    icon: const Icon(Icons.refresh),
                    label: const Text('Nouvel enregistrement'),
                  ),
                ),

              const SizedBox(height: 24),

              // Instructions
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.blue.shade50,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: const [
                    Text(
                      'Instructions:',
                      style: TextStyle(fontWeight: FontWeight.bold),
                    ),
                    SizedBox(height: 8),
                    Text('1. Appuyez sur le micro pour commencer'),
                    Text('2. Dictez l\'ordonnance clairement'),
                    Text('3. Appuyez à nouveau pour arrêter'),
                    Text('4. Appuyez sur "Transcrire et valider"'),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
