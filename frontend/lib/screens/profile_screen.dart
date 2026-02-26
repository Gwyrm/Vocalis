import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  late TextEditingController _emailController;
  late TextEditingController _fullNameController;
  late TextEditingController _currentPasswordController;
  late TextEditingController _newPasswordController;
  late TextEditingController _confirmPasswordController;

  bool _obscureCurrentPassword = true;
  bool _obscureNewPassword = true;
  bool _obscureConfirmPassword = true;

  @override
  void initState() {
    super.initState();
    final authProvider = context.read<AuthProvider>();
    _emailController = TextEditingController(text: authProvider.currentUser?.email ?? '');
    _fullNameController = TextEditingController(text: authProvider.currentUser?.fullName ?? '');
    _currentPasswordController = TextEditingController();
    _newPasswordController = TextEditingController();
    _confirmPasswordController = TextEditingController();
  }

  @override
  void dispose() {
    _emailController.dispose();
    _fullNameController.dispose();
    _currentPasswordController.dispose();
    _newPasswordController.dispose();
    _confirmPasswordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Mon Profil'),
        centerTitle: true,
      ),
      body: Consumer<AuthProvider>(
        builder: (context, authProvider, _) {
          return SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // ===== Profile Section =====
                const Text(
                  'Informations Personnelles',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 16),

                // Email field
                TextField(
                  controller: _emailController,
                  enabled: !authProvider.isLoading,
                  keyboardType: TextInputType.emailAddress,
                  decoration: InputDecoration(
                    labelText: 'Email',
                    prefixIcon: const Icon(Icons.email),
                    hintText: 'votre.email@exemple.fr',
                  ),
                ),
                const SizedBox(height: 16),

                // Full Name field
                TextField(
                  controller: _fullNameController,
                  enabled: !authProvider.isLoading,
                  decoration: InputDecoration(
                    labelText: 'Nom Complet',
                    prefixIcon: const Icon(Icons.person),
                    hintText: 'Dr. Jean Dupont',
                  ),
                ),
                const SizedBox(height: 16),

                // Role (read-only)
                TextField(
                  enabled: false,
                  decoration: InputDecoration(
                    labelText: 'Rôle',
                    prefixIcon: const Icon(Icons.badge),
                    hintText: authProvider.currentUser?.role ?? 'Unknown',
                  ),
                ),
                const SizedBox(height: 16),

                // Organization (read-only)
                TextField(
                  enabled: false,
                  decoration: InputDecoration(
                    labelText: 'Organisation',
                    prefixIcon: const Icon(Icons.business),
                    hintText: 'Organisation ID: ${authProvider.currentUser?.organizationId ?? 'Unknown'}',
                  ),
                ),
                const SizedBox(height: 24),

                // Error message (profile)
                if (authProvider.error != null && !_isPasswordChangeMode())
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.red.shade50,
                      border: Border.all(color: Colors.red.shade300),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Row(
                      children: [
                        Icon(Icons.error_outline, color: Colors.red.shade700),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            authProvider.error ?? '',
                            style: TextStyle(color: Colors.red.shade700),
                          ),
                        ),
                      ],
                    ),
                  ),
                if (authProvider.error != null && !_isPasswordChangeMode())
                  const SizedBox(height: 16),

                // Update profile button
                SizedBox(
                  width: double.infinity,
                  height: 52,
                  child: ElevatedButton(
                    onPressed: authProvider.isLoading ? null : _handleUpdateProfile,
                    child: authProvider.isLoading && _isPasswordChangeMode() == false
                        ? const SizedBox(
                            height: 20,
                            width: 20,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Text('Mettre à jour le profil'),
                  ),
                ),
                const SizedBox(height: 40),

                // ===== Password Section =====
                const Text(
                  'Changer le Mot de Passe',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 16),

                // Current password field
                TextField(
                  controller: _currentPasswordController,
                  enabled: !authProvider.isLoading,
                  obscureText: _obscureCurrentPassword,
                  decoration: InputDecoration(
                    labelText: 'Mot de passe actuel',
                    prefixIcon: const Icon(Icons.lock),
                    suffixIcon: IconButton(
                      icon: Icon(
                        _obscureCurrentPassword
                            ? Icons.visibility_off
                            : Icons.visibility,
                      ),
                      onPressed: () {
                        setState(() {
                          _obscureCurrentPassword = !_obscureCurrentPassword;
                        });
                      },
                    ),
                  ),
                ),
                const SizedBox(height: 16),

                // New password field
                TextField(
                  controller: _newPasswordController,
                  enabled: !authProvider.isLoading,
                  obscureText: _obscureNewPassword,
                  decoration: InputDecoration(
                    labelText: 'Nouveau mot de passe',
                    prefixIcon: const Icon(Icons.lock_outline),
                    suffixIcon: IconButton(
                      icon: Icon(
                        _obscureNewPassword
                            ? Icons.visibility_off
                            : Icons.visibility,
                      ),
                      onPressed: () {
                        setState(() {
                          _obscureNewPassword = !_obscureNewPassword;
                        });
                      },
                    ),
                  ),
                ),
                const SizedBox(height: 16),

                // Confirm password field
                TextField(
                  controller: _confirmPasswordController,
                  enabled: !authProvider.isLoading,
                  obscureText: _obscureConfirmPassword,
                  decoration: InputDecoration(
                    labelText: 'Confirmer le nouveau mot de passe',
                    prefixIcon: const Icon(Icons.lock_outline),
                    suffixIcon: IconButton(
                      icon: Icon(
                        _obscureConfirmPassword
                            ? Icons.visibility_off
                            : Icons.visibility,
                      ),
                      onPressed: () {
                        setState(() {
                          _obscureConfirmPassword = !_obscureConfirmPassword;
                        });
                      },
                    ),
                  ),
                ),
                const SizedBox(height: 24),

                // Error message (password)
                if (authProvider.error != null && _isPasswordChangeMode())
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.red.shade50,
                      border: Border.all(color: Colors.red.shade300),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Row(
                      children: [
                        Icon(Icons.error_outline, color: Colors.red.shade700),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            authProvider.error ?? '',
                            style: TextStyle(color: Colors.red.shade700),
                          ),
                        ),
                      ],
                    ),
                  ),
                if (authProvider.error != null && _isPasswordChangeMode())
                  const SizedBox(height: 16),

                // Change password button
                SizedBox(
                  width: double.infinity,
                  height: 52,
                  child: ElevatedButton(
                    onPressed: authProvider.isLoading ? null : _handleChangePassword,
                    child: authProvider.isLoading && _isPasswordChangeMode()
                        ? const SizedBox(
                            height: 20,
                            width: 20,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Text('Changer le mot de passe'),
                  ),
                ),
                const SizedBox(height: 40),
              ],
            ),
          );
        },
      ),
    );
  }

  bool _isPasswordChangeMode() {
    return _currentPasswordController.text.isNotEmpty ||
        _newPasswordController.text.isNotEmpty ||
        _confirmPasswordController.text.isNotEmpty;
  }

  Future<void> _handleUpdateProfile() async {
    final authProvider = context.read<AuthProvider>();

    // Validate email format if changed
    final currentEmail = authProvider.currentUser?.email ?? '';
    if (_emailController.text.isNotEmpty &&
        _emailController.text != currentEmail &&
        !_isValidEmail(_emailController.text)) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Format email invalide')),
      );
      return;
    }

    // Prepare update data
    String? newEmail =
        _emailController.text != currentEmail ? _emailController.text : null;
    String? newFullName =
        _fullNameController.text != (authProvider.currentUser?.fullName ?? '')
            ? _fullNameController.text
            : null;

    if (newEmail == null && newFullName == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Aucune modification détectée')),
      );
      return;
    }

    final success = await authProvider.updateProfile(
      email: newEmail,
      fullName: newFullName,
    );

    if (mounted) {
      if (success) {
        authProvider.clearError();
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Profil mis à jour avec succès')),
        );
        // Update controllers to reflect new values
        _emailController.text = authProvider.currentUser?.email ?? '';
        _fullNameController.text = authProvider.currentUser?.fullName ?? '';
      }
    }
  }

  Future<void> _handleChangePassword() async {
    final authProvider = context.read<AuthProvider>();

    // Validate inputs
    if (_currentPasswordController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Veuillez entrer votre mot de passe actuel')),
      );
      return;
    }

    if (_newPasswordController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Veuillez entrer un nouveau mot de passe')),
      );
      return;
    }

    if (_newPasswordController.text.length < 8) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Le mot de passe doit contenir au moins 8 caractères')),
      );
      return;
    }

    if (_newPasswordController.text != _confirmPasswordController.text) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Les nouveaux mots de passe ne correspondent pas')),
      );
      return;
    }

    final success = await authProvider.changePassword(
      currentPassword: _currentPasswordController.text,
      newPassword: _newPasswordController.text,
    );

    if (mounted) {
      if (success) {
        authProvider.clearError();
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Mot de passe changé avec succès')),
        );
        // Clear password fields
        _currentPasswordController.clear();
        _newPasswordController.clear();
        _confirmPasswordController.clear();
      }
    }
  }

  bool _isValidEmail(String email) {
    final regex = RegExp(r'^[^@]+@[^@]+\.[^@]+$');
    return regex.hasMatch(email);
  }
}
