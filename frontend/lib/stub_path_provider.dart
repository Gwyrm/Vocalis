/// Stub implementation of path_provider for web platforms
/// On web, we don't need to save files to documents directory
/// This stub is used when running on Flutter Web to avoid plugin errors

import 'dart:async';

/// Stub class for getApplicationDocumentsDirectory
/// Returns a dummy directory object
Future<Directory> getApplicationDocumentsDirectory() async {
  return Directory('documents');
}

/// Dummy Directory class for web
class Directory {
  final String path;

  Directory(this.path);

  String get absolutePath => path;
}
