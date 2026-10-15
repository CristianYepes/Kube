# Spec 003 — The strip for the video

> v1.0, 2026-10-15. Replaces v0.2 (2026-10-10), a web view that the owner rejected on 2026-10-11; v0.2 is in the git
> history of this folder. `plan.md` says how, `tasks.md` what was done.

## Why

The owner records the agent playing for a LinkedIn post. The video has to make clear that no person is playing: who plays
(the rule bot or Jev), the tactic in force and the keys being pressed.

## Constraints (measured on the owner's Linux, 2026-10-11)

- Everything runs on the owner's Linux: a UTM virtual machine with Ubuntu 22.04 and GNOME on Wayland (X11 programs run
  through Xwayland). Its largest screen mode is 1280x800.
- The game window is a fixed 1280x720 (`includes/cub3d.h`), so nothing fits beside it: the strip sits on top of it.
- Minimal: the fewest elements that say who plays, which tactic and which keys.

## What was rejected, and why

v0.2 was a 1920x1080 web page (`kube-agent view`) with the game beside it. It was designed for a screen the owner does not
have, and the owner rejected its look. Its code was removed (`tasks.md`, S4).

## Acceptance criteria (all met, see `tasks.md`)

- **AC1.** WHEN `kube-agent run` is given `--strip`, THE SYSTEM SHALL show a strip at the bottom left of the screen that
  stays above the game window.
- **AC2.** The strip SHALL say who plays (`THE RULE BOT IS PLAYING`, `JEV IS PLAYING` or `NO ONE IS PLAYING`), the tactic in
  force with a few words on what it does, and light the keys the agent holds (W A S D, ← →, ↑ to fire) as it sends them.
- **AC3.** WHEN the episode ends, the strip SHALL show the result for 3 s and close. WHEN the agent stops without a result,
  the strip SHALL close.
- **AC4.** The strip SHALL run without the credentials of the agent's environment and make no network call.
- **AC5.** Without `--strip` nothing changes: no `keys.jsonl`, no strip. A strip that cannot start SHALL be reported, and the
  game SHALL go on.

## Out of scope

- The closing message of the video: the owner adds it in the video editor and the post.
- Recording: the owner records the screen with the desktop's own tools.
