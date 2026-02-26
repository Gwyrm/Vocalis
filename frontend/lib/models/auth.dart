/// Authentication models for login/register
class LoginRequest {
  final String email;
  final String password;

  LoginRequest({
    required this.email,
    required this.password,
  });

  Map<String, dynamic> toJson() => {
    'email': email,
    'password': password,
  };
}

class AuthResponse {
  final String accessToken;
  final String tokenType;
  final CurrentUser user;

  AuthResponse({
    required this.accessToken,
    required this.tokenType,
    required this.user,
  });

  factory AuthResponse.fromJson(Map<String, dynamic> json) {
    return AuthResponse(
      accessToken: json['access_token'] ?? '',
      tokenType: json['token_type'] ?? 'bearer',
      user: CurrentUser.fromJson(json['user'] ?? {}),
    );
  }
}

class CurrentUser {
  final String id;
  final String email;
  final String role;
  final String organizationId;
  final String? fullName;

  CurrentUser({
    required this.id,
    required this.email,
    required this.role,
    required this.organizationId,
    this.fullName,
  });

  factory CurrentUser.fromJson(Map<String, dynamic> json) {
    return CurrentUser(
      id: json['id'] ?? '',
      email: json['email'] ?? '',
      role: json['role'] ?? 'nurse',
      organizationId: json['org_id'] ?? json['organization_id'] ?? '',
      fullName: json['full_name'] ?? json['fullName'],
    );
  }

  bool isDoctor() => role.toLowerCase() == 'doctor';
  bool isNurse() => role.toLowerCase() == 'nurse';
}
