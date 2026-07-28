import 'dart:convert';

import 'package:http/http.dart' as http;

import 'config.dart';

/// The join details the backend returns from `POST /session`.
class SessionInfo {
  const SessionInfo({
    required this.url,
    required this.token,
    required this.room,
    required this.mode,
  });

  final String url;
  final String token;
  final String room;
  final String mode;

  factory SessionInfo.fromJson(Map<String, dynamic> json) => SessionInfo(
        url: json['url'] as String,
        token: json['token'] as String,
        room: json['room'] as String,
        mode: json['mode'] as String,
      );
}

/// Ask the backend to mint a LiveKit token for a fresh interview room in the
/// requested [mode]. Throws if the server is unreachable or returns an error.
Future<SessionInfo> createSession(InterviewMode mode) async {
  final res = await http.post(
    Uri.parse('${AppConfig.backendBaseUrl}/session'),
    headers: const {'Content-Type': 'application/json'},
    body: jsonEncode({'mode': mode.apiKey}),
  );
  if (res.statusCode != 200) {
    throw Exception('Session request failed (${res.statusCode}): ${res.body}');
  }
  return SessionInfo.fromJson(jsonDecode(res.body) as Map<String, dynamic>);
}
