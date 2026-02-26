import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'api_service.dart';
import 'providers/auth_provider.dart';
import 'screens/patient_list_screen.dart';
import 'screens/auth/login_screen.dart';
import 'screens/splash_screen.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthProvider()),
        ProxyProvider<AuthProvider, ApiService>(
          update: (_, authProvider, apiService) {
            apiService ??= ApiService();
            // Set token on ApiService whenever auth state changes
            if (authProvider.token != null) {
              apiService.setToken(authProvider.token!);
            }
            return apiService;
          },
        ),
      ],
      child: Builder(
        builder: (context) {
          // Set up auth error callback on ApiService
          WidgetsBinding.instance.addPostFrameCallback((_) {
            final apiService = context.read<ApiService>();
            final authProvider = context.read<AuthProvider>();
            apiService.setOnAuthError(() async {
              // Logout and show error when auth fails
              await authProvider.logout();
              if (context.mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('Votre session a expiré. Veuillez vous reconnecter.'),
                  ),
                );
              }
            });
          });

          return MaterialApp(
            title: 'Vocalis AI',
            debugShowCheckedModeBanner: false,
            theme: ThemeData(
              colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
              useMaterial3: true,
              inputDecorationTheme: InputDecorationTheme(
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                filled: true,
                contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              ),
            ),
            home: const _AppRouter(),
          );
        },
      ),
    );
  }
}

/// Routes to appropriate screen based on auth state
class _AppRouter extends StatefulWidget {
  const _AppRouter();

  @override
  State<_AppRouter> createState() => _AppRouterState();
}

class _AppRouterState extends State<_AppRouter> {
  @override
  void initState() {
    super.initState();
    // Check auth on startup
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AuthProvider>().checkAuth();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<AuthProvider>(
      builder: (context, authProvider, _) {
        // If authenticated, show main app
        if (authProvider.isAuthenticated) {
          return PatientListScreen(
            apiService: context.read<ApiService>(),
          );
        }

        // If not authenticated, show login (default)
        return const LoginScreen();
      },
    );
  }
}
