/// App-wide configuration.
///
/// [backendBaseUrl] must point at the Viva token server (FastAPI, `api.py`).
/// For local testing:
///   - Android emulator: http://10.0.2.2:8000  (10.0.2.2 = the host machine)
///   - Physical phone:   `http://<your-PC-LAN-IP>:8000`  (same Wi-Fi network)
class AppConfig {
  static const String backendBaseUrl = 'http://10.0.2.2:8000';
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
