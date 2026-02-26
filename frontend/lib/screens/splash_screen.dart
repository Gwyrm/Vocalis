import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  @override
  void initState() {
    super.initState();
    _checkAuth();
  }

  Future<void> _checkAuth() async {
    try {
      // Small delay for splash screen visibility
      await Future.delayed(const Duration(milliseconds: 1000));

      if (!mounted) return;

      final authProvider = context.read<AuthProvider>();
      await authProvider.checkAuth();

      if (!mounted) return;

      // Wait a bit more to ensure state is updated
      await Future.delayed(const Duration(milliseconds: 500));

      // Navigation is handled by main.dart based on auth state
      // Force a rebuild by checking the auth state again
      if (mounted) {
        setState(() {});
      }
    } catch (e) {
      print('Error during auth check: $e');
      if (mounted) {
        setState(() {});
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 120,
              height: 120,
              decoration: BoxDecoration(
                color: Colors.deepPurple.shade100,
                borderRadius: BorderRadius.circular(30),
              ),
              child: Icon(
                Icons.medical_services,
                size: 80,
                color: Colors.deepPurple.shade700,
              ),
            ),
            const SizedBox(height: 40),
            const Text(
              'Vocalis',
              style: TextStyle(
                fontSize: 32,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 20),
            const CircularProgressIndicator(),
            const SizedBox(height: 40),
            const Text(
              'Vérification de votre session...',
              style: TextStyle(
                fontSize: 14,
                color: Colors.grey,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
