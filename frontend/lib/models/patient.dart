class Patient {
  final String id;
  final String firstName;
  final String lastName;
  final DateTime dateOfBirth;
  final String? gender;
  final String? phone;
  final String? email;
  final List<String> allergies;
  final List<String> chronicConditions;
  final List<String> currentMedications;
  final String? medicalNotes;
  final DateTime createdAt;

  Patient({
    required this.id,
    required this.firstName,
    required this.lastName,
    required this.dateOfBirth,
    this.gender,
    this.phone,
    this.email,
    required this.allergies,
    required this.chronicConditions,
    required this.currentMedications,
    this.medicalNotes,
    required this.createdAt,
  });

  String get fullName => '$firstName $lastName';

  int get ageInYears {
    final now = DateTime.now();
    int age = now.year - dateOfBirth.year;
    if (now.month < dateOfBirth.month ||
        (now.month == dateOfBirth.month && now.day < dateOfBirth.day)) {
      age--;
    }
    return age;
  }

  factory Patient.fromJson(Map<String, dynamic> json) {
    return Patient(
      id: json['id'] as String,
      firstName: json['first_name'] as String,
      lastName: json['last_name'] as String,
      dateOfBirth: DateTime.parse(json['date_of_birth'] as String),
      gender: json['gender'] as String?,
      phone: json['phone'] as String?,
      email: json['email'] as String?,
      allergies: List<String>.from(json['allergies'] as List? ?? []),
      chronicConditions: List<String>.from(json['chronic_conditions'] as List? ?? []),
      currentMedications: List<String>.from(json['current_medications'] as List? ?? []),
      medicalNotes: json['medical_notes'] as String?,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }

  Map<String, dynamic> toJson() => {
    'first_name': firstName,
    'last_name': lastName,
    'date_of_birth': dateOfBirth.toIso8601String().split('T')[0],
    'gender': gender,
    'phone': phone,
    'email': email,
    'allergies': allergies,
    'chronic_conditions': chronicConditions,
    'current_medications': currentMedications,
    'medical_notes': medicalNotes,
  };
}
