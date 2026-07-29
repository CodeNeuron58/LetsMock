import 'package:flutter/material.dart';

import 'call_screen.dart';
import 'config.dart';
import 'resume_card.dart';
import 'subscriptions.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Subscriptions.init();
  runApp(const VivaApp());
}

class VivaApp extends StatelessWidget {
  const VivaApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'LetsMock',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorSchemeSeed: const Color(0xFF4C6FFF),
        useMaterial3: true,
      ),
      home: const HomeScreen(),
    );
  }
}

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('LetsMock')),
      body: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const SizedBox(height: 8),
            Text(
              'Pick a round to practise',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 4),
            Text(
              'The interviewer will call you, ask questions, and follow up. '
              'Answer out loud — you can interrupt it.',
              style: Theme.of(context)
                  .textTheme
                  .bodyMedium
                  ?.copyWith(color: Colors.black54),
            ),
            const SizedBox(height: 16),
            const ResumeCard(),
            const SizedBox(height: 20),
            for (final mode in InterviewMode.values)
              Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: FilledButton.tonal(
                  onPressed: () => Navigator.of(context).push(
                    MaterialPageRoute(builder: (_) => CallScreen(mode: mode)),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    child: Text(mode.label, style: const TextStyle(fontSize: 16)),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
