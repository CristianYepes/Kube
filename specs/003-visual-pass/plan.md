# Plan 003 — The strip

> v1.0, 2026-10-15. Replaces v0.2, the plan of the web view (in the git history of this folder).

## Pieces

| File | Role |
|---|---|
| `agent/strip.py` | The strip: a GTK 3 popup window, run with the system Python (`/usr/bin/python3`). It reads the run folder while the agent writes it. |
| `agent/src/kube_agent/cli.py` | `run --strip`: starts `strip.py` once the run folder exists (`strip_starter`), with `bridge.child_environment()` (no credentials) and stdin closed. |
| `agent/src/kube_agent/episode.py` | With a live view, writes `keys.jsonl` (a row `{"t", "keys"}` each time the `C` line sent to the game changes) and calls the view before the game starts. |
| `agent/tests/test_strip.py` | The strip's logic; the live-view tests are in `test_episode.py` and `test_cli.py`. |

## How it works

- **Data.** `decisions.jsonl` (only applied decisions set the tactic), `keys.jsonl` and `result.json` (written last, read only
  when whole). Polled every 30 ms, complete lines only.
- **Display.** `GDK_BACKEND=x11`: only X11 lets a popup that no window manager handles sit at a given place above the other
  windows, and GNOME on Wayland runs X11 programs, the game too, through Xwayland. The strip sits 24 px in from the bottom
  left of the monitor's work area; the game's health bar is at the bottom right.
- **GTK and the system Python.** The Tk of uv's Python drew X11 bitmap fonts on the owner's screen (seen 2026-10-11). The
  system Python has GTK 3 (`sudo apt install python3-gi gir1.2-gtk-3.0`).
- **End.** After `result.json` the strip shows `WON in 12.3 s`, `LOST at …`, `TIME UP at …` or `STOPPED` for 3 s. If the
  agent's process goes away first, the strip closes.
- **Security.** The strip never holds the OpenRouter key (filtered environment, tested) and opens no socket.

## Rejected

- **The 1920x1080 web page** (v0.2): see `spec.md`.
- **Tk with uv's Python:** bitmap fonts.
- **Drawing inside the game (C):** it would change the game shared with the other author; an overlay does it from outside.
