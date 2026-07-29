/// App-wide configuration.
///
/// [backendBaseUrl] must point at the LetsMock token server (FastAPI, `api.py`).
/// Override it per run rather than editing this file:
///
///   emulator (default) : flutter run
///   USB phone          : adb reverse tcp:8000 tcp:8000
///                        flutter run --dart-define=BACKEND_URL=http://localhost:8000
///   deployed           : flutter run --dart-define=BACKEND_URL=https://api.letsmock.app
///
/// 10.0.2.2 is the emulator's alias for the host machine.
class AppConfig {
  static const String backendBaseUrl = String.fromEnvironment(
    'BACKEND_URL',
    defaultValue: 'http://10.0.2.2:8000',
  );

  /// RevenueCat SDK key. These are *public by design* — they ship inside the
  /// app binary, unlike RevenueCat's secret server keys. This is the Test Store
  /// key: it must be swapped for the production key before release, because a
  /// release build configured with a test key deliberately crashes.
  static const String revenueCatApiKey = 'test_wXdhlVuGsKBBcbXaNfTRKzBjHmr';

  /// Entitlement identifier that grants Pro. Must match the identifier in the
  /// RevenueCat dashboard (Product catalog -> Entitlements) exactly.
  static const String proEntitlement = 'LetsMock Pro';
}

/// The interview rounds the backend understands. `apiKey` must match the
/// server-side mode keys (see server `interview/modes.py`).
enum InterviewMode {
  hr('hr', 'HR / Behavioural'),
  resume('resume', 'Resume Grill'),
  sde('sde', 'Tech Concepts (SDE)');

  const InterviewMode(this.apiKey, this.label);

  final String apiKey;
  final String label;
}
