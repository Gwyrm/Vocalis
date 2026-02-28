import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/models/intervention.dart';
import 'package:intl/intl.dart';

void main() {
  group('Intervention Model Tests', () {
    test('Create intervention from JSON', () {
      final json = {
        'id': 'int-1',
        'prescription_id': 'presc-1',
        'intervention_type': 'Blood Test',
        'description': 'Annual checkup',
        'scheduled_date': '2026-03-15T10:00:00',
        'priority': 'high',
        'status': 'scheduled',
        'created_by': 'doctor-1',
        'created_at': '2026-02-28T10:00:00',
        'updated_at': '2026-02-28T10:00:00',
      };

      final intervention = Intervention.fromJson(json);

      expect(intervention.id, equals('int-1'));
      expect(intervention.prescriptionId, equals('presc-1'));
      expect(intervention.interventionType, equals('Blood Test'));
      expect(intervention.description, equals('Annual checkup'));
      expect(intervention.priority, equals('high'));
      expect(intervention.status, equals('scheduled'));
    });

    test('Convert intervention to JSON', () {
      final now = DateTime.now();
      final intervention = Intervention(
        id: 'int-1',
        prescriptionId: 'presc-1',
        interventionType: 'Blood Test',
        description: 'Test description',
        scheduledDate: now,
        priority: 'normal',
        status: 'scheduled',
        createdBy: 'doctor-1',
        createdAt: now,
        updatedAt: now,
      );

      final json = intervention.toJson();

      expect(json['id'], equals('int-1'));
      expect(json['intervention_type'], equals('Blood Test'));
      expect(json['priority'], equals('normal'));
      expect(json['status'], equals('scheduled'));
    });

    test('Status display name translations', () {
      final interventions = {
        'scheduled': 'Planifiée',
        'in_progress': 'En cours',
        'completed': 'Complétée',
        'cancelled': 'Annulée',
      };

      interventions.forEach((status, expected) {
        final intervention = Intervention(
          id: 'int-1',
          prescriptionId: 'presc-1',
          interventionType: 'Test',
          description: null,
          scheduledDate: DateTime.now(),
          priority: 'normal',
          status: status,
          createdBy: 'doctor-1',
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
        );

        expect(intervention.statusDisplayName, equals(expected));
      });
    });

    test('Priority display name translations', () {
      final priorities = {
        'low': 'Basse',
        'normal': 'Normale',
        'high': 'Haute',
      };

      priorities.forEach((priority, expected) {
        final intervention = Intervention(
          id: 'int-1',
          prescriptionId: 'presc-1',
          interventionType: 'Test',
          description: null,
          scheduledDate: DateTime.now(),
          priority: priority,
          status: 'scheduled',
          createdBy: 'doctor-1',
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
        );

        expect(intervention.priorityDisplayName, equals(expected));
      });
    });

    test('Formatted scheduled date', () {
      final date = DateTime(2026, 3, 15, 10, 30);
      final intervention = Intervention(
        id: 'int-1',
        prescriptionId: 'presc-1',
        interventionType: 'Test',
        description: null,
        scheduledDate: date,
        priority: 'normal',
        status: 'scheduled',
        createdBy: 'doctor-1',
        createdAt: DateTime.now(),
        updatedAt: DateTime.now(),
      );

      final formatted = intervention.formattedScheduledDate;
      expect(formatted, contains('15'));
      expect(formatted, contains('03'));
      expect(formatted, contains('2026'));
    });
  });

  group('InterventionLog Model Tests', () {
    test('Create log from JSON', () {
      final json = {
        'id': 'log-1',
        'intervention_id': 'int-1',
        'logged_by': 'nurse-1',
        'status_change': 'scheduled→in_progress',
        'notes': 'Patient arrived',
        'logged_at': '2026-02-28T14:00:00',
      };

      final log = InterventionLog.fromJson(json);

      expect(log.id, equals('log-1'));
      expect(log.interventionId, equals('int-1'));
      expect(log.loggedBy, equals('nurse-1'));
      expect(log.statusChange, equals('scheduled→in_progress'));
      expect(log.notes, equals('Patient arrived'));
    });

    test('Convert log to JSON', () {
      final now = DateTime.now();
      final log = InterventionLog(
        id: 'log-1',
        interventionId: 'int-1',
        loggedBy: 'nurse-1',
        statusChange: 'scheduled→in_progress',
        notes: 'Started',
        loggedAt: now,
      );

      final json = log.toJson();

      expect(json['id'], equals('log-1'));
      expect(json['status_change'], equals('scheduled→in_progress'));
      expect(json['notes'], equals('Started'));
    });
  });

  group('InterventionDocument Model Tests', () {
    test('Create document from JSON', () {
      final json = {
        'id': 'doc-1',
        'log_id': 'log-1',
        'document_type': 'photo',
        'file_name': 'test.jpg',
        'file_path': '/path/to/test.jpg',
        'mime_type': 'image/jpeg',
        'file_size': 102400,
        'caption': 'Test caption',
        'uploaded_at': '2026-02-28T14:00:00',
      };

      final doc = InterventionDocument.fromJson(json);

      expect(doc.id, equals('doc-1'));
      expect(doc.logId, equals('log-1'));
      expect(doc.documentType, equals('photo'));
      expect(doc.fileName, equals('test.jpg'));
      expect(doc.mimeType, equals('image/jpeg'));
    });

    test('Document type display names', () {
      final types = {
        'note': 'Note',
        'photo': 'Photo',
        'result': 'Résultat',
        'other': 'Autre',
      };

      types.forEach((type, expected) {
        final doc = InterventionDocument(
          id: 'doc-1',
          logId: 'log-1',
          documentType: type,
          fileName: 'test.jpg',
          filePath: '/path/to/test.jpg',
          mimeType: 'image/jpeg',
          fileSize: 1024,
          caption: 'Test',
          uploadedAt: DateTime.now(),
        );

        expect(doc.documentTypeDisplayName, equals(expected));
      });
    });

    test('Formatted file size', () {
      final cases = {
        512: '512 B',
        1024: '1.0 KB',
        1048576: '1.0 MB',
      };

      cases.forEach((size, expected) {
        final doc = InterventionDocument(
          id: 'doc-1',
          logId: 'log-1',
          documentType: 'photo',
          fileName: 'test.jpg',
          filePath: '/path/to/test.jpg',
          mimeType: 'image/jpeg',
          fileSize: size,
          caption: null,
          uploadedAt: DateTime.now(),
        );

        expect(doc.formattedFileSize, equals(expected));
      });
    });
  });

  group('InterventionDetail Model Tests', () {
    test('Create detail from JSON with logs', () {
      final json = {
        'id': 'int-1',
        'prescription_id': 'presc-1',
        'intervention_type': 'Blood Test',
        'description': 'Test',
        'scheduled_date': '2026-03-15T10:00:00',
        'priority': 'high',
        'status': 'completed',
        'created_by': 'doctor-1',
        'created_at': '2026-02-28T10:00:00',
        'updated_at': '2026-02-28T10:00:00',
        'logs': [
          {
            'id': 'log-1',
            'intervention_id': 'int-1',
            'logged_by': 'nurse-1',
            'status_change': 'scheduled→in_progress',
            'notes': 'Started',
            'logged_at': '2026-02-28T14:00:00',
          },
          {
            'id': 'log-2',
            'intervention_id': 'int-1',
            'logged_by': 'nurse-1',
            'status_change': 'in_progress→completed',
            'notes': 'Completed',
            'logged_at': '2026-02-28T15:00:00',
          },
        ],
      };

      final detail = InterventionDetail.fromJson(json);

      expect(detail.id, equals('int-1'));
      expect(detail.status, equals('completed'));
      expect(detail.logs.length, equals(2));
      expect(detail.logs[0].statusChange, equals('scheduled→in_progress'));
      expect(detail.logs[1].statusChange, equals('in_progress→completed'));
    });

    test('Detail with empty logs', () {
      final json = {
        'id': 'int-1',
        'prescription_id': 'presc-1',
        'intervention_type': 'Test',
        'description': null,
        'scheduled_date': '2026-03-15T10:00:00',
        'priority': 'normal',
        'status': 'scheduled',
        'created_by': 'doctor-1',
        'created_at': '2026-02-28T10:00:00',
        'updated_at': '2026-02-28T10:00:00',
        'logs': [],
      };

      final detail = InterventionDetail.fromJson(json);

      expect(detail.logs.length, equals(0));
    });
  });
}
