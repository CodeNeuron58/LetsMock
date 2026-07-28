import 'package:flutter/material.dart';

import 'scorecard.dart';
import 'session_api.dart';

/// Shown after hanging up: polls for the scorecard, then renders the report.
class ScorecardScreen extends StatefulWidget {
  const ScorecardScreen({super.key, required this.room});

  final String room;

  @override
  State<ScorecardScreen> createState() => _ScorecardScreenState();
}

class _ScorecardScreenState extends State<ScorecardScreen> {
  late Future<Scorecard> _future;

  @override
  void initState() {
    super.initState();
    _future = pollScorecard(widget.room);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Your scorecard')),
      body: FutureBuilder<Scorecard>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) {
            return const _Analysing();
          }
          if (snap.hasError) {
            return _Failed(message: '${snap.error}');
          }
          return _Report(scorecard: snap.data!);
        },
      ),
    );
  }
}

class _Analysing extends StatelessWidget {
  const _Analysing();

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          CircularProgressIndicator(),
          SizedBox(height: 20),
          Text('Analysing your interview…'),
          SizedBox(height: 6),
          Text(
            'Scoring your answers and delivery.',
            style: TextStyle(color: Colors.black54, fontSize: 13),
          ),
        ],
      ),
    );
  }
}

class _Failed extends StatelessWidget {
  const _Failed({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error_outline, size: 48, color: Colors.redAccent),
            const SizedBox(height: 16),
            Text(message, textAlign: TextAlign.center),
          ],
        ),
      ),
    );
  }
}

class _Report extends StatelessWidget {
  const _Report({required this.scorecard});

  final Scorecard scorecard;

  @override
  Widget build(BuildContext context) {
    final a = scorecard.assessment;
    final m = scorecard.metrics;

    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 8, 20, 40),
      children: [
        _ScoreHero(score: a.overallScore),
        const SizedBox(height: 20),
        Text(a.summary, style: const TextStyle(fontSize: 15, height: 1.45)),
        const SizedBox(height: 24),

        // Delivery — these numbers are measured, not judged by the model.
        Row(
          children: [
            _Metric(label: 'Pace', value: '${m.wordsPerMinute.round()}', unit: 'wpm'),
            _Metric(label: 'Fillers', value: '${m.fillerWordCount}', unit: 'words'),
            _Metric(label: 'Spoken', value: '${(m.speakingSeconds / 60).round()}', unit: 'min'),
          ],
        ),
        if (m.fillerBreakdown.isNotEmpty) ...[
          const SizedBox(height: 10),
          Wrap(
            spacing: 6,
            runSpacing: 6,
            children: [
              for (final e in m.fillerBreakdown.entries)
                Chip(
                  label: Text('"${e.key}" ×${e.value}'),
                  visualDensity: VisualDensity.compact,
                ),
            ],
          ),
        ],

        const SizedBox(height: 24),
        if (a.strengths.isNotEmpty)
          _Bullets(title: 'What worked', items: a.strengths, color: Colors.green.shade700),
        if (a.weaknesses.isNotEmpty)
          _Bullets(title: 'What to fix', items: a.weaknesses, color: Colors.orange.shade800),
        if (a.redFlags.isNotEmpty)
          _Bullets(title: 'Red flags', items: a.redFlags, color: Colors.red.shade700),

        if (a.structureNote.isNotEmpty) ...[
          const SizedBox(height: 8),
          _Card(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Structure', style: TextStyle(fontWeight: FontWeight.w600)),
                const SizedBox(height: 6),
                Text(a.structureNote, style: const TextStyle(height: 1.4)),
              ],
            ),
          ),
        ],

        if (a.perAnswer.isNotEmpty) ...[
          const SizedBox(height: 28),
          const Text('Answer by answer',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
          const SizedBox(height: 12),
          for (final ans in a.perAnswer) _AnswerCard(answer: ans),
        ],

        if (scorecard.transcript.isNotEmpty) ...[
          const SizedBox(height: 16),
          _Card(
            padded: false,
            child: ExpansionTile(
              title: const Text('Full transcript'),
              childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
              children: [
                Text(scorecard.transcript,
                    style: const TextStyle(fontSize: 13, height: 1.5)),
              ],
            ),
          ),
        ],
      ],
    );
  }
}

class _ScoreHero extends StatelessWidget {
  const _ScoreHero({required this.score});

  final double score;

  @override
  Widget build(BuildContext context) {
    final color = scoreColor(score);
    return Center(
      child: Column(
        children: [
          Container(
            width: 132,
            height: 132,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: color.withValues(alpha: 0.12),
              border: Border.all(color: color, width: 3),
            ),
            child: Center(
              child: Text(
                score.toStringAsFixed(1),
                style: TextStyle(
                    fontSize: 42, fontWeight: FontWeight.w700, color: color),
              ),
            ),
          ),
          const SizedBox(height: 8),
          const Text('out of 10', style: TextStyle(color: Colors.black54)),
        ],
      ),
    );
  }
}

/// Shared score colouring so the hero and per-answer scores agree.
Color scoreColor(double score) {
  if (score >= 7) return Colors.green.shade600;
  if (score >= 5) return Colors.orange.shade700;
  return Colors.red.shade600;
}

class _Metric extends StatelessWidget {
  const _Metric({required this.label, required this.value, required this.unit});

  final String label;
  final String value;
  final String unit;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: _Card(
        margin: const EdgeInsets.only(right: 8),
        child: Column(
          children: [
            Text(value,
                style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w700)),
            Text(unit, style: const TextStyle(fontSize: 11, color: Colors.black45)),
            const SizedBox(height: 4),
            Text(label, style: const TextStyle(fontSize: 12, color: Colors.black54)),
          ],
        ),
      ),
    );
  }
}

class _Bullets extends StatelessWidget {
  const _Bullets({required this.title, required this.items, required this.color});

  final String title;
  final List<String> items;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title,
              style: TextStyle(fontWeight: FontWeight.w700, color: color, fontSize: 15)),
          const SizedBox(height: 6),
          for (final item in items)
            Padding(
              padding: const EdgeInsets.only(bottom: 4),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('•  ', style: TextStyle(color: color)),
                  Expanded(child: Text(item, style: const TextStyle(height: 1.4))),
                ],
              ),
            ),
        ],
      ),
    );
  }
}

class _AnswerCard extends StatelessWidget {
  const _AnswerCard({required this.answer});

  final AnswerEvaluation answer;

  @override
  Widget build(BuildContext context) {
    return _Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Text(answer.question,
                    style: const TextStyle(fontWeight: FontWeight.w600, height: 1.35)),
              ),
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: scoreColor(answer.score).withValues(alpha: 0.14),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Text(
                  answer.score.toStringAsFixed(1),
                  style: TextStyle(
                      color: scoreColor(answer.score), fontWeight: FontWeight.w700),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          _Contrast(label: 'You said', text: answer.whatYouSaid, color: Colors.black54),
          const SizedBox(height: 8),
          _Contrast(
            label: 'A strong answer',
            text: answer.strongAnswer,
            color: Colors.green.shade700,
          ),
          if (answer.flags.isNotEmpty) ...[
            const SizedBox(height: 10),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: [
                for (final f in answer.flags)
                  Chip(
                    label: Text(f, style: const TextStyle(fontSize: 12)),
                    backgroundColor: Colors.orange.shade50,
                    visualDensity: VisualDensity.compact,
                  ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}

class _Contrast extends StatelessWidget {
  const _Contrast({required this.label, required this.text, required this.color});

  final String label;
  final String text;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label.toUpperCase(),
            style: TextStyle(
                fontSize: 10.5, fontWeight: FontWeight.w700, color: color, letterSpacing: 0.6)),
        const SizedBox(height: 2),
        Text(text, style: const TextStyle(height: 1.4)),
      ],
    );
  }
}

class _Card extends StatelessWidget {
  const _Card({required this.child, this.margin = EdgeInsets.zero, this.padded = true});

  final Widget child;
  final EdgeInsets margin;
  final bool padded;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: margin,
      padding: padded ? const EdgeInsets.all(14) : EdgeInsets.zero,
      decoration: BoxDecoration(
        color: Colors.grey.shade50,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey.shade200),
      ),
      child: child,
    );
  }
}
