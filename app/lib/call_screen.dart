import 'package:flutter/material.dart';
import 'package:livekit_client/livekit_client.dart';
import 'package:permission_handler/permission_handler.dart';

import 'config.dart';
import 'scorecard_screen.dart';
import 'session_api.dart';
import 'subscriptions.dart';

/// The live interview call. On open it: asks for the mic, gets a token from the
/// backend, joins the LiveKit room, and publishes the microphone. The agent
/// worker is dispatched into the same room and does the interviewing; its audio
/// plays automatically once its track is subscribed.
class CallScreen extends StatefulWidget {
  const CallScreen({super.key, required this.mode});

  final InterviewMode mode;

  @override
  State<CallScreen> createState() => _CallScreenState();
}

class _CallScreenState extends State<CallScreen> {
  final Room _lkRoom = Room();
  EventsListener<RoomEvent>? _listener;

  String _status = 'Getting ready…';
  bool _connected = false;
  bool _failed = false;
  String? _roomName; // set once the session exists; needed to fetch the scorecard

  @override
  void initState() {
    super.initState();
    _lkRoom.addListener(_onRoomChanged); // rebuild on connection-state changes
    _start();
  }

  Future<void> _start() async {
    try {
      // 1. Microphone permission.
      final mic = await Permission.microphone.request();
      if (!mic.isGranted) {
        return _fail('Microphone permission is required for the interview.');
      }

      // 2. Token from the backend. The server enforces the free tier, so this
      //    is also where an exhausted quota surfaces.
      _setStatus('Setting up your interview…');
      late final SessionInfo session;
      try {
        session = await createSession(widget.mode);
      } on QuotaExceededException catch (e) {
        return _offerUpgrade(e.reason);
      }
      _roomName = session.room;

      // 3. Wire up room events, then connect.
      _listener = _lkRoom.createListener()
        ..on<RoomConnectedEvent>((_) => _setStatus('Connected', connected: true))
        ..on<RoomDisconnectedEvent>((_) => _setStatus('Interview ended'))
        ..on<TrackSubscribedEvent>((_) => _refresh());

      _setStatus('Connecting to your interviewer…');
      await _lkRoom.connect(session.url, session.token);

      // 4. Publish the microphone so the interviewer can hear you.
      await _lkRoom.localParticipant?.setMicrophoneEnabled(true);
    } catch (e) {
      _fail('Could not start the interview.\n$e');
    }
  }

  void _onRoomChanged() => _refresh();
  void _refresh() {
    if (mounted) setState(() {});
  }

  void _setStatus(String status, {bool connected = false}) {
    if (!mounted) return;
    setState(() {
      _status = status;
      _connected = connected;
    });
  }

  /// Free tier is used up: show the paywall, and start the interview straight
  /// away if they upgrade.
  Future<void> _offerUpgrade(String reason) async {
    _setStatus(reason);
    final purchased = await Subscriptions.showPaywall();
    if (!mounted) return;
    if (purchased) {
      _setStatus('Setting up your interview…');
      await _start();
    } else {
      _fail(reason);
    }
  }

  void _fail(String message) {
    if (!mounted) return;
    setState(() {
      _failed = true;
      _connected = false;
      _status = message;
    });
  }

  Future<void> _hangUp() async {
    // Capture the navigator before awaiting — `context` is not safe across the gap.
    final navigator = Navigator.of(context);
    final room = _roomName;

    await _lkRoom.disconnect();
    if (!mounted) return;

    // Scoring only starts once the agent leaves the room, so hand the room name
    // to the scorecard screen and let it poll. Nothing to score if we never
    // got as far as connecting.
    if (room != null && _connected) {
      navigator.pushReplacement(
        MaterialPageRoute(builder: (_) => ScorecardScreen(room: room)),
      );
    } else {
      navigator.pop();
    }
  }

  @override
  void dispose() {
    _lkRoom.removeListener(_onRoomChanged);
    _listener?.dispose();
    _lkRoom.dispose(); // also disconnects
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final interviewerPresent = _lkRoom.remoteParticipants.isNotEmpty;
    return Scaffold(
      backgroundColor: const Color(0xFF0E1116),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            children: [
              const Spacer(),
              Icon(
                _failed
                    ? Icons.error_outline
                    : (_connected ? Icons.graphic_eq : Icons.hourglass_top),
                size: 72,
                color: _failed ? Colors.redAccent : Colors.white70,
              ),
              const SizedBox(height: 24),
              Text(
                widget.mode.label,
                style: const TextStyle(
                    color: Colors.white, fontSize: 22, fontWeight: FontWeight.w600),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 10),
              Text(
                _status,
                style: const TextStyle(color: Colors.white54, fontSize: 15),
                textAlign: TextAlign.center,
              ),
              if (_connected)
                Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: Text(
                    interviewerPresent
                        ? 'Interviewer is on the line'
                        : 'Waiting for the interviewer…',
                    style: const TextStyle(color: Colors.white38, fontSize: 13),
                  ),
                ),
              const Spacer(),
              Padding(
                padding: const EdgeInsets.only(bottom: 32),
                child: FloatingActionButton(
                  backgroundColor: Colors.redAccent,
                  onPressed: _hangUp,
                  child: const Icon(Icons.call_end),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
