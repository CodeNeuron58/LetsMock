/// Client-side mirror of the server's `Scorecard` schema
/// (see server `viva/scoring/schema.py`).
library;

class AnswerEvaluation {
  const AnswerEvaluation({
    required this.question,
    required this.whatYouSaid,
    required this.strongAnswer,
    required this.score,
    required this.flags,
  });

  final String question;
  final String whatYouSaid;
  final String strongAnswer;
  final double score;
  final List<String> flags;

  factory AnswerEvaluation.fromJson(Map<String, dynamic> j) => AnswerEvaluation(
    question: j['question'] as String? ?? '',
    whatYouSaid: j['what_you_said'] as String? ?? '',
    strongAnswer: j['strong_answer'] as String? ?? '',
    score: (j['score'] as num?)?.toDouble() ?? 0,
    flags: _strings(j['flags']),
  );
}

class Assessment {
  const Assessment({
    required this.overallScore,
    required this.summary,
    required this.strengths,
    required this.weaknesses,
    required this.redFlags,
    required this.structureNote,
    required this.perAnswer,
  });

  final double overallScore;
  final String summary;
  final List<String> strengths;
  final List<String> weaknesses;
  final List<String> redFlags;
  final String structureNote;
  final List<AnswerEvaluation> perAnswer;

  factory Assessment.fromJson(Map<String, dynamic> j) => Assessment(
    overallScore: (j['overall_score'] as num?)?.toDouble() ?? 0,
    summary: j['summary'] as String? ?? '',
    strengths: _strings(j['strengths']),
    weaknesses: _strings(j['weaknesses']),
    redFlags: _strings(j['red_flags']),
    structureNote: j['structure_note'] as String? ?? '',
    perAnswer: ((j['per_answer'] as List?) ?? const [])
        .map((e) => AnswerEvaluation.fromJson(_map(e)))
        .toList(),
  );
}

class SpeechMetrics {
  const SpeechMetrics({
    required this.wordCount,
    required this.speakingSeconds,
    required this.wordsPerMinute,
    required this.fillerWordCount,
    required this.fillerBreakdown,
  });

  final int wordCount;
  final double speakingSeconds;
  final double wordsPerMinute;
  final int fillerWordCount;
  final Map<String, int> fillerBreakdown;

  factory SpeechMetrics.fromJson(Map<String, dynamic> j) => SpeechMetrics(
    wordCount: (j['candidate_word_count'] as num?)?.toInt() ?? 0,
    speakingSeconds: (j['speaking_seconds'] as num?)?.toDouble() ?? 0,
    wordsPerMinute: (j['words_per_minute'] as num?)?.toDouble() ?? 0,
    fillerWordCount: (j['filler_word_count'] as num?)?.toInt() ?? 0,
    fillerBreakdown: ((j['filler_breakdown'] as Map?) ?? const {}).map(
      (k, v) => MapEntry(k as String, (v as num).toInt()),
    ),
  );
}

class Scorecard {
  const Scorecard({
    required this.mode,
    required this.assessment,
    required this.metrics,
    required this.transcript,
  });

  final String mode;
  final Assessment assessment;
  final SpeechMetrics metrics;
  final String transcript;

  factory Scorecard.fromJson(Map<String, dynamic> j) => Scorecard(
    mode: j['mode'] as String? ?? '',
    assessment: Assessment.fromJson(_map(j['assessment'])),
    metrics: SpeechMetrics.fromJson(_map(j['metrics'])),
    transcript: j['transcript'] as String? ?? '',
  );
}

List<String> _strings(Object? raw) =>
    ((raw as List?) ?? const []).map((e) => e.toString()).toList();

/// Normalise a nested JSON object; tolerates `Map<dynamic, dynamic>`.
Map<String, dynamic> _map(Object? raw) => raw is Map
    ? raw.map((k, v) => MapEntry(k.toString(), v))
    : <String, dynamic>{};
