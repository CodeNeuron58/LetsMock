// Smoke test: the home screen renders the three interview modes.

import 'package:flutter_test/flutter_test.dart';

import 'package:viva/main.dart';

void main() {
  testWidgets('home screen shows the interview modes', (tester) async {
    await tester.pumpWidget(const VivaApp());

    expect(find.text('HR / Behavioural'), findsOneWidget);
    expect(find.text('Resume Grill'), findsOneWidget);
    expect(find.text('Tech Concepts (SDE)'), findsOneWidget);
  });
}
