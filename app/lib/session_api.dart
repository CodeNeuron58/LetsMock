import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';

import 'config.dart';
import 'scorecard.dart';
import 'subscriptions.dart';

/// The join details the backend returns from `POST /session`.
class SessionInfo {
  const SessionInfo({
    required this.url,
    required this.token,
    required this.room,
    required this.mode,
    required this.minutes,
  });

  final String url;
  final String token;
  final String room;
  final String mode;
  final int minutes; // length cap for this interview (free vs Pro)

  factory SessionInfo.fromJson(Map<String, dynamic> json) => SessionInfo(
    url: json['url'] as String,
    token: json['token'] as String,
    room: json['room'] as String,
    mode: json['mode'] as String,
    minutes: (json['minutes'] as num?)?.toInt() ?? 5,
  );
}

/// The server refused because the free tier is used up — show the paywall.
class QuotaExceededException implements Exception {
  const QuotaExceededException(this.reason);
  final String reason;
  @override
  String toString() => reason;
}

/// Ask the backend to mint a LiveKit token for a fresh interview room in the
/// requested [mode]. Throws if the server is unreachable or returns an error.
Future<SessionInfo> createSession(InterviewMode mode) async {
  // The server counts free-tier usage against the RevenueCat user id, so both
  // it and the current entitlement go with every request.
  final res = await http.post(
    Uri.parse('${AppConfig.backendBaseUrl}/session'),
    headers: const {'Content-Type': 'application/json'},
    body: jsonEncode({
      'mode': mode.apiKey,
      'user_id': await Subscriptions.userId(),
      'is_pro': await Subscriptions.isPro(),
    }),
  );

  if (res.statusCode == 402) {
    final detail = jsonDecode(res.body)['detail'];
    final reason = detail is Map ? detail['reason'] as String? : null;
    throw QuotaExceededException(reason ?? 'Your free interview is used up.');
  }
  if (res.statusCode != 200) {
    throw Exception('Session request failed (${res.statusCode}): ${res.body}');
  }
  return SessionInfo.fromJson(jsonDecode(res.body) as Map<String, dynamic>);
}

/// What resume, if any, the server has on file for this user.
class ResumeInfo {
  const ResumeInfo({required this.filename, required this.characters});

  final String filename;
  final int characters;

  factory ResumeInfo.fromJson(Map<String, dynamic> j) => ResumeInfo(
    filename: j['filename'] as String? ?? 'resume.pdf',
    characters: (j['characters'] as num?)?.toInt() ?? 0,
  );
}

/// The resume on file, or null if none has been uploaded.
Future<ResumeInfo?> fetchResume() async {
  final userId = await Subscriptions.userId();
  final res = await http.get(
    Uri.parse('${AppConfig.backendBaseUrl}/resume/$userId'),
  );
  if (res.statusCode != 200 || res.body.trim() == 'null') return null;
  return ResumeInfo.fromJson(jsonDecode(res.body) as Map<String, dynamic>);
}

/// Upload a resume PDF. Throws with the server's message if it is unusable
/// (wrong type, too big, or a scan with no text layer).
Future<ResumeInfo> uploadResume(String path, String filename) async {
  final req =
      http.MultipartRequest(
          'POST',
          Uri.parse('${AppConfig.backendBaseUrl}/resume'),
        )
        ..fields['user_id'] = await Subscriptions.userId()
        ..files.add(
          await http.MultipartFile.fromPath(
            'file',
            path,
            filename: filename,
            contentType: MediaType('application', 'pdf'),
          ),
        );

  final res = await http.Response.fromStream(await req.send());
  if (res.statusCode != 200) {
    final detail = jsonDecode(res.body)['detail'];
    throw Exception(
      detail is String ? detail : 'Upload failed (${res.statusCode}).',
    );
  }
  return ResumeInfo.fromJson(jsonDecode(res.body) as Map<String, dynamic>);
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
      throw Exception(
        'Scorecard request failed (${res.statusCode}): ${res.body}',
      );
    }
    await Future<void>.delayed(interval); // 202: still scoring
  }
  throw TimeoutException('Timed out waiting for the scorecard.');
}
