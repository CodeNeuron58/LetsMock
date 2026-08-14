// Verifies the client parses the exact JSON shape the server emits
// (server: viva/scoring/schema.py -> GET /scorecard/{room}).

import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:viva/scorecard.dart';

// Captured from the server's own scorecard output.
const _serverJson = '''
{
  "mode": "hr",
  "assessment": {
    "overall_score": 4.0,
    "summary": "Relevant experience but vague on specifics.",
    "strengths": ["Some relevant experience in AI engineering"],
    "weaknesses": ["Lack of clarity", "Insufficient technical depth"],
    "red_flags": ["Unclear motivation for the role"],
    "structure_note": "No clear STAR structure.",
    "per_answer": [
      {
        "question": "Tell me about yourself",
        "what_you_said": "Trying to get an AI engineering job",
        "strong_answer": "Lead with a concrete achievement",
        "score": 2.0,
        "flags": ["Lack of clarity", "No specific examples"]
      }
    ]
  },
  "metrics": {
    "candidate_word_count": 174,
    "speaking_seconds": 101.0,
    "words_per_minute": 103.4,
    "filler_word_count": 8,
    "filler_breakdown": {"kind of": 3, "like": 2}
  },
  "transcript": "INTERVIEWER: Hi\\nCANDIDATE: Hello"
}
''';

void main() {
  test('parses a server scorecard', () {
    final card = Scorecard.fromJson(
      jsonDecode(_serverJson) as Map<String, dynamic>,
    );

    expect(card.mode, 'hr');
    expect(card.assessment.overallScore, 4.0);
    expect(card.assessment.weaknesses, hasLength(2));
    expect(card.assessment.redFlags.first, contains('Unclear motivation'));

    final answer = card.assessment.perAnswer.single;
    expect(answer.question, 'Tell me about yourself');
    expect(answer.strongAnswer, 'Lead with a concrete achievement');
    expect(answer.flags, hasLength(2));

    expect(card.metrics.wordsPerMinute, 103.4);
    expect(card.metrics.fillerWordCount, 8);
    expect(card.metrics.fillerBreakdown['kind of'], 3);
    expect(card.transcript, contains('CANDIDATE'));
  });

  test('tolerates missing optional fields', () {
    final card = Scorecard.fromJson({
      'mode': 'sde',
      'assessment': {'overall_score': 7.5, 'summary': 'Solid.'},
      'metrics': {},
    });

    expect(card.assessment.overallScore, 7.5);
    expect(card.assessment.perAnswer, isEmpty);
    expect(card.metrics.fillerWordCount, 0);
    expect(card.transcript, '');
  });
}
