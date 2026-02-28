import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'api_service.dart';
import 'providers/auth_provider.dart';
import 'screens/patient_list_screen.dart';
import 'screens/auth/login_screen.dart';
import 'screens/nurse/nurse_deliveries_screen.dart';

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
          update: (context, authProvider, apiService) {
            apiService ??= ApiService();
            // Set token on ApiService whenever auth state changes
            if (authProvider.token != null) {
              apiService.setToken(authProvider.token!);
            }
            // Set auth error callback to logout when token is invalid/expired
            apiService.setOnAuthError(() {
              authProvider.logout();
            });
            return apiService;
          },
        ),
      ],
      child: MaterialApp(
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
        // If authenticated, show role-based screen
        if (authProvider.isAuthenticated) {
          final apiService = context.read<ApiService>();
          final userRole = authProvider.currentUser?.role;

          // Role-based navigation
          if (userRole == 'nurse') {
            return NurseDeliveriesScreen(apiService: apiService);
          } else if (userRole == 'admin') {
            // TODO: Add admin dashboard
            return PatientListScreen(apiService: apiService);
          } else {
            // Default to doctor/patient list screen
            return PatientListScreen(apiService: apiService);
          }
        }

        // If not authenticated, show login
        return const LoginScreen();
      },
    );
  }
}
