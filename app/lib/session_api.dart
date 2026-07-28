import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import 'config.dart';
import 'scorecard.dart';

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

/// Thrown when the interview finished but the server could not score it.
class ScoringFailedException implements Exception {
  const ScoringFailedException();
  @override
  String toString() => 'The interview could not be scored.';
}

/// Poll for the scorecard of [room].
///
/// Scoring only starts once the call ends, so the server answers 202 while it
/// is still working and 200 when the result (or a failure) is final.
Future<Scorecard> pollScorecard(
  String room, {
  Duration interval = const Duration(seconds: 2),
  Duration timeout = const Duration(seconds: 120),
}) async {
  final deadline = DateTime.now().add(timeout);

  while (DateTime.now().isBefore(deadline)) {
    final res = await http.get(
      Uri.parse('${AppConfig.backendBaseUrl}/scorecard/$room'),
    );

    if (res.statusCode == 200) {
      final body = jsonDecode(res.body) as Map<String, dynamic>;
      final card = body['scorecard'];
      if (body['status'] == 'scored' && card != null) {
        return Scorecard.fromJson(card as Map<String, dynamic>);
      }
      throw const ScoringFailedException(); // status == failed
    }
    if (res.statusCode != 202) {
      throw Exception('Scorecard request failed (${res.statusCode}): ${res.body}');
    }
    await Future<void>.delayed(interval); // 202: still scoring
  }
  throw TimeoutException('Timed out waiting for the scorecard.');
}
