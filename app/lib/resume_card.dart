import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';

import 'session_api.dart';

/// Shows what resume is on file and lets the candidate attach or replace one.
/// Resume Grill works without it, but is far sharper with it.
class ResumeCard extends StatefulWidget {
  const ResumeCard({super.key});

  @override
  State<ResumeCard> createState() => _ResumeCardState();
}

class _ResumeCardState extends State<ResumeCard> {
  ResumeInfo? _resume;
  bool _busy = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final resume = await fetchResume();
      if (mounted) setState(() => _resume = resume);
    } catch (_) {
      // Offline or backend down — the card just shows the empty state.
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _pickAndUpload() async {
    final picked = await FilePicker.pickFiles(
      type: FileType.custom,
      allowedExtensions: const ['pdf'],
      withData: false,
    );
    final file = picked?.files.single;
    if (file?.path == null) return; // cancelled

    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final resume = await uploadResume(file!.path!, file.name);
      if (mounted) setState(() => _resume = resume);
    } catch (e) {
      if (mounted) {
        setState(() => _error = '$e'.replaceFirst('Exception: ', ''));
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final attached = _resume != null;
    return Card(
      margin: EdgeInsets.zero,
      child: ListTile(
        leading: Icon(
          attached ? Icons.description : Icons.upload_file,
          color: attached ? Colors.green.shade600 : Colors.black45,
        ),
        title: Text(attached ? _resume!.filename : 'Attach your resume'),
        subtitle: Text(
          _error ??
              (attached
                  ? 'Resume Grill will interview you on this'
                  : 'Optional — makes Resume Grill ask about your real projects'),
          style: TextStyle(color: _error != null ? Colors.red.shade700 : null),
        ),
        trailing: _busy
            ? const SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(strokeWidth: 2),
              )
            : TextButton(
                onPressed: _pickAndUpload,
                child: Text(attached ? 'Replace' : 'Upload'),
              ),
        onTap: _busy ? null : _pickAndUpload,
      ),
    );
  }
}
