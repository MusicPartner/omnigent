# Windows native attachment delivery plan

## Supported contract

The Windows work must preserve the existing shared attachment contract rather
than add a separate Windows format:

- Resolved image/file data is materialized under the per-session
  `~/.omnigent/attachments/<session-key>/` cache (or `OMNIGENT_DATA_DIR`),
  outside the agent's working tree. Turns reuse the launch cache; resume
  rebuilds materialize attachments into the current launch's cache.
- The original basename is retained when safe. Path components and marker
  delimiters are sanitized; collisions must not overwrite different bytes.
- Images are delivered as paths for Claude Code and as Codex `localImage`
  inputs. Binary files such as ZIP/Office/database attachments are filesystem
  attachments only for `claude-native` and `codex-native`; the session upload
  capability/allowlist must continue to advertise that boundary.
- A resume reconstructs the same attachment from stored file metadata and
  bytes. A missing or malformed file remains visible as an attachment error;
  it is never silently dropped.
- When an image was downscaled, preserve its original dimensions for the
  existing model-facing resize notice/path metadata.

The implementation is explicitly scoped to Claude and Codex for ZIP and other
filesystem attachments (`FILESYSTEM_ATTACHMENT_HARNESSES`). Cursor, Kimi, and
Antigravity already materialize image data to a path and inject an
`[Attached: …]` reference. Their text-injection workflow is not a claim that
they can open ZIPs or Office documents. No Copilot native attachment consumer
or filesystem capability is currently registered, so Copilot must remain
unsupported for this feature unless a separately verified consumer is added.

## Windows implementation boundary

This is a filesystem-leaf and small-dispatch change. Keep attachment decoding,
safe filename handling, cache placement, and resume re-resolution in the
existing Python helpers. Anchor Windows leaf creation to a trusted storage
directory handle with `NtCreateFile` and a relative leaf name; refuse reparse
points instead of resolving an untrusted path and opening it in a separate
operation. Do not grant or use attribute-only mutation as a substitute for the
anchored create/open protection. Dispatch the resulting path through the
existing executor path; no new process or transport mechanism is needed.

The cache must be on a fixed local drive with Windows ACL support and trusted
ancestors. UNC/removable locations, reparse points, hard-linked leaves, and
directories granting unrelated identities mutation access are refused. New
files receive a protected current-user/SYSTEM ACL without execute access; safe
pre-existing cache owners (current user, SYSTEM, or Administrators) are retained
while their ACLs are tightened. A custom `OMNIGENT_DATA_DIR` must satisfy the
same rules. This protects attachment storage and does not add a process sandbox.

Preserve spaces and Unicode filenames. Do not extract ZIP contents, mark
uploaded files executable, or place them in the agent workspace. Keep
attachment payloads and access tokens out of diagnostic logs. On expected
storage failures, log a concise safe error without `exc_info=True`, which could
emit sensitive paths or other exception context.

## User entry points and test limits

The feature map is `feature-map/composer.md`, under `attachments`. It lists the
in-session composer (attach button, paste, drop onto transcript, removable
chips) and the new-session composer (attach before first send). Its current E2E
UI cases are:

- `tests/e2e_ui/chat/test_composer_attachments.py::test_attach_then_remove_file`
- `tests/e2e_ui/chat/test_composer_attachments.py::test_attach_zip_as_file_card`
- `tests/e2e_ui/chat/test_composer_attachments.py::test_file_dropped_on_the_transcript_attaches`
- `tests/e2e_ui/chat/test_composer_attachments.py::test_landing_rejects_unsupported_type_and_keeps_message`
- `tests/e2e_ui/start_session/test_image_only_first_message_send.py::test_landing_image_only_draft_starts_the_session` (landing/new-session image-only first send)

These cover browser composer admission, preview/chips, upload and first-send
behavior. They do not exercise a live Windows native harness. The
`feature-map/skills/verify-omnigent` isolated runtime uses POSIX process-group
cleanup (`start_new_session` / `os.killpg`), so it cannot currently provide a
Windows live-runtime check. Do not claim Windows live-UI or native-harness E2E
coverage from these tests.

## Regression selection

Run these focused tests on Windows and the existing Linux CI platform:

- Shared cache and filename safety: `tests/inner/test_native_attachments.py`
  (`test_materialize_attachment_uses_block_filename`,
  `test_materialize_attachment_same_name_collision_is_bounded`,
  `test_materialize_cache_contains_path_traversal`,
  `test_materialize_cache_refuses_symlinked_destination`,
  `test_attachment_cache_isolates_sessions_and_leaves_git_workspace_clean`,
  `test_materialize_cache_creates_or_reuses_non_executable_files`).
- Claude image, file, resize, and history restoration:
  `tests/inner/test_claude_native_executor.py` (tests
  `test_run_turn_materializes_image_to_bridge_dir`,
  `test_run_turn_materializes_zip_outside_workspace`,
  `test_resize_notice_uses_hidden_hook_context`,
  `test_run_turn_path_traversal_filename_sanitized`) and
  `tests/harnesses/claude_native/test_claude_native.py` (tests
  `test_resume_rebuild_delivers_a_zip_to_the_attachment_cache`,
  `test_resume_restores_attachments_using_the_launch_bridge`).
- Codex image, ZIP, resize, and resume:
  `tests/inner/test_codex_native_executor.py` (tests
  `test_image_block_is_sent_as_local_image_not_inline_base64`,
  `test_resize_notice_is_encoded_in_model_visible_image_path`,
  `test_input_file_zip_is_materialized_without_workspace`,
  `test_zip_submitted_as_an_image_block_still_uses_a_file_reference`) and
  `tests/harnesses/codex_native/test_codex_native.py::test_ensure_local_codex_resume_rollout_restores_a_zip_outside_the_workspace`.
- Capability contract: `tests/server/routes/test_filesystem_attachment_runtime.py`
  (`test_connected_builds_must_advertise_attachment_support`) and
  `tests/inner/test_native_attachments.py::test_client_server_filesystem_extension_parity`.
- Existing path-injection consumers: `tests/inner/test_cursor_native_executor.py::TestContentExtraction::test_real_image_attachment_materialized`,
  `tests/inner/test_kimi_native_executor.py::TestContentExtraction::test_real_image_attachment_materialized`, and
  `tests/inner/test_antigravity_native_executor.py::test_run_turn_image_attachment_materialized`.

Keep Windows CI focused on the listed attachment nodes, the shared cache
security cases, and capability checks. Do not make the full Claude/Codex
executor modules required Windows selections; unrelated baseline failures in
those large modules would obscure this regression signal. The smaller
consumer tests for Cursor/Kimi/Antigravity are regression coverage for
unchanged path delivery; Copilot has no attachment test selection until a
supported attachment path exists.

The related upstream commit `36c94573` adds bounded HTTP retries for transient
attachment resource reads and corresponding recovery tests. That addresses
network-read reliability; it does not change Windows filesystem storage or
directory handling. Review that upstream blob and issue history separately
before reusing it as evidence for this Windows fix.

## Codex sandbox acceptance limit

Codex 0.162.0 snapshots `localImage` files through a direct host-process read
([official source](https://github.com/openai/codex/blob/rust-v0.162.0/codex-rs/protocol/src/local_media.rs));
when app-server runs as the attachment owner, image ingestion does not require
sandbox-account access. A ZIP path sent as text is not a filesystem permission
grant. Elevated commands use dedicated sandbox accounts, and their readable
roots come from the permission policy
([official source](https://github.com/openai/codex/blob/rust-v0.162.0/codex-rs/windows-sandbox-rs/src/setup.rs)).
Reading the private cache through those accounts still needs live acceptance
testing; a successful image response does not establish ZIP shell access. Keep
the private DACL intact and do not silently switch to full access. If Codex
requests native approval to read an attachment, granting that access must be an
explicit user decision.

## Manual acceptance on Windows

Use a fresh local Claude native session and then a fresh Codex native session
with the same three files: an image named `diagram final.png`, an image with a
Unicode name such as `café.png`, and a ZIP named `sample archive.zip`.

1. Attach the image and ask the harness to describe it. Confirm the visible
   answer reflects the image. Confirm the attachment chip retains its filename
   and that its cached file is under Omnigent's attachment cache, outside the
   workspace.
2. Attach the ZIP and ask Claude or Codex to list its contents without extracting
   it. Confirm the harness can read the archive by path and the user-provided
   filename survives.
   Confirm no archive members are extracted automatically and the workspace
   remains unchanged.
3. Stop the native process/session, resume the same Omnigent conversation, and
   ask again about the image and ZIP. Confirm both original attachments resolve
   from history and the paths remain valid.
4. Send a high-resolution image that triggers server resizing. Confirm the
   image still arrives and the response can use the original dimensions in its
   guidance; this is a model-visible notice for Claude and Codex image-path
   metadata for Codex.
5. Repeat the image check with Cursor, Kimi, and Antigravity only if those
   harnesses are available in the environment. These harnesses support the
   existing image-path reference behavior; do not use a ZIP pass as an
   acceptance criterion for them.
6. Copilot is not an acceptance target for filesystem attachments. If testing
   Copilot image delivery, record it as exploratory until its support is
   represented by a registered capability and regression test.
