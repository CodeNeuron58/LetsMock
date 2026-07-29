/// App-wide configuration.
///
/// [backendBaseUrl] must point at the Viva token server (FastAPI, `api.py`).
/// For local testing:
///   - Android emulator: http://10.0.2.2:8000  (10.0.2.2 = the host machine)
///   - Physical phone:   `http://<your-PC-LAN-IP>:8000`  (same Wi-Fi network)
class AppConfig {
  static const String backendBaseUrl = 'http://10.0.2.2:8000';

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
