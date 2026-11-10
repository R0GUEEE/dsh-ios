---
name: dsh-ios-platform
description: How to work with this iOS instance of DeepSeek Harness — the loopback host bridge that reaches iOS capabilities, what asks the user first, and which guest limitations are permanent. Use when a task needs the device itself (calendar, reminders, health, location, contacts, notifications, files, photos, sharing, Shortcuts) or when a shell command fails in a way that looks environmental.
---

# DSH on iOS

You are running inside an iOS app: iSH-ARM64 emulates AArch64 Linux, and the
harness runs on Alpine inside that emulator. Two consequences shape everything
here — the guest is slow, and the guest is not the device.

## Reaching iOS

The app exposes capabilities as tools through a loopback HTTP bridge. Use them
instead of trying to call `osascript`, `open`, or any iOS API from the shell;
none of those exist here.

| Need | Tool |
|---|---|
| Device facts, battery, thermal state | `device_info`, `device_power` |
| Calendar read / create | `calendar_query`, `calendar_create_event` |
| Reminders read / create | `reminders_query`, `reminders_create` |
| Steps, heart rate, sleep, workouts | `health_query` |
| One location fix | `location_query` |
| Find a person | `contacts_search` |
| Finish-a-long-task notification | `notify` |
| Bring in a file / a photo | `file_import`, `photo_import` |
| Save something out | `file_export` |
| Send text onward | `share` |
| Run the user's Shortcut | `shortcut_run` |

**Reads** depend on the user's per-capability switch and iOS's own permission
prompt; if either is closed you get `permission_denied`, which tells you what the
user must change. That is an answer, not a failure to retry.

**Writes** ask the user every single time. Expect a confirmation, and do not
retry a declined one.

Things that do not exist, and should not be improvised: clipboard access (no tool,
deliberately), listing the photo library (a person picks each photo), and
enumerating contacts (search by name only).

An empty Health answer is ambiguous by design — iOS never reveals whether *read*
access was declined. Relay the note the tool returns instead of concluding that
the user took no steps.

## The guest

- **Node runs jitless.** No WebAssembly, so anything requiring it fails; a
  `fetch()` polyfill covers LLM streaming.
- **No network sandbox.** Landlock and bubblewrap are absent, so the sandbox mode
  is `danger-full-access`; the approval prompt is the only gate. That is why
  risky commands should be explained rather than assumed.
- **It is slow.** A cold `npm install` can take minutes. Prefer `apk` packages to
  building from source, and avoid compiling inside the guest when a prebuilt
  exists.
- **Paths**: the workspace is `/root/workspace`; harness state is `/root/.dsh`
  (sessions, credentials, skills, `mcp.json`); the image's own files live under
  `/usr/local`.

## Plugins and MCP

- `~/.dsh/mcp.json` lists MCP servers; each key is a server name and its tools
  appear as `mcp__<name>__<tool>`. Edit the file, then restart the harness.
- `~/.dsh/skills/` is yours for skills; a skill here shadows a bundled one of the
  same name.
- Packages ship with the image. Adding a plugin that changes the Host is a
  restart-level change, not something to do mid-task.
