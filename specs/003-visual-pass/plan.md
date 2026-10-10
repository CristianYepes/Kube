# Plan 003 — The visual pass

> v0.2, 2026-10-10, approved with the spec. What and why: `spec.md`. Facts: `specs/research-2026-10-10.md` (F1-F7). Steps: `tasks.md`.

## The idea in one paragraph

`kube-agent run` stays as it is. A second command, `kube-agent view`, runs beside it: it reads the run folder while the
agent writes it (the agent already flushes every row, F1), turns the rows into events, and serves them with one page to a
browser on the same machine. The browser shows the page full screen; the game window sits on top of it, at the top-left
of the recorded area; the page draws the panel to its right and the time bands below. When the episode ends, the page
shows the result and then the conclusion card. The same page can replay a finished folder, which is how it is designed
and tested on the Mac.

```
kube-agent run --runner local ...       (unchanged)
   └─ writes agent/runs/<run>/episode.jsonl, decisions.jsonl, result.json   (row by row, flushed)
kube-agent view                          (new, a separate process)
   ├─ reads the newest run folder every 50 ms, adds `rules` and `read` to each decision
   ├─ (Linux, X11) moves the window `cub3D` into place and reads where it landed
   └─ serves 127.0.0.1:8765   /  (the page)   /fonts/<file>   /events?after=N
browser, full screen, asks /events every 50 ms and draws
```

## Constraints check

| Hard constraint (source) | How this plan meets it |
|---|---|
| Ask before changing the game; the repo is shared with Rodrigo (project memory) | No C file changes. The window is moved from outside with `xdotool` |
| Files, code and comments in English; chat in Spanish | Yes; the text on screen is in English too (owner, 2026-10-10) |
| Aggressive YAGNI | One new module, one page, one data file; no framework, no build step, no new Python dependency (F7) |
| No paid Jev call without the owner's OK | The view makes no call. The takes with `--policy jev` are the owner's, after the OK (about $0.001 each, R17) |
| The key never leaves `~/jev/libros/.env` | `view` never reads it and is started without it; it reads only the run folder; the run folders have none of it (AC12 of spec 002) |
| Colima off by default | Not needed: the live view runs on Linux, and the Mac only replays recorded folders |
| No commit or push without asking | The spec waits for the OK; each task is a commit only when the owner says so |
| Each dependency and library is a cost; licenses checked | Only the IBM Plex fonts, OFL-1.1, bundled with `OFL.txt` (F6) |
| Unattended code owns its environment (global rule 12) | Paths from the module's own file and from `REPO_ROOT`; every external tool (`xdotool`, `xwininfo`) with a timeout and a clear message if it is missing |

## Files

| Path | What it is |
|---|---|
| `agent/src/kube_agent/view.py` | Events from a run folder (follow and replay), `describe_state`, the HTTP server, the window placement |
| `agent/src/kube_agent/view_page/index.html` | The page: HTML, CSS and JS in one file, no external request |
| `agent/src/kube_agent/view_page/fonts/` | `IBMPlexSans-Regular.woff2`, `IBMPlexSans-SemiBold.woff2`, `IBMPlexMono-Regular.woff2`, `IBMPlexMono-SemiBold.woff2`, `OFL.txt`; their SHA-256 are written in `tasks.md` |
| `agent/src/kube_agent/view_conclusion.json` | The final card: its lines and the numbers in them, with their source |
| `agent/src/kube_agent/cli.py` | One new subcommand, `view` |
| `agent/tests/test_view.py`, `test_view_page.py`, `test_view_conclusion.py` | The tests of AC1, AC3-AC6, AC8-AC10 |

## The command

```
kube-agent view [--port 8765] [--place-game X,Y]      follow: the newest run folder created after it started
kube-agent view --replay FOLDER [--until T]           replay a finished folder at real speed, stopping at T seconds
```

- **Follow.** It looks in `agent/runs/` every 200 ms for a folder whose name (it starts with the UTC time) is later than
  the moment `view` started. It then reads new complete lines of `episode.jsonl` and `decisions.jsonl` every 50 ms, and
  `result.json` when it appears. A half-written last line is left for the next read. When the episode ends it goes back
  to waiting, so one `view` serves many takes.
- **Replay.** It loads the folder and releases each row at its own time: an episode row at `t`, a decision at its
  `answered_at` (or at `t` for `scripted`), the end at `survival_seconds`. With `--until T` it stops releasing at `T`,
  which freezes the page for a screenshot. The page has one code path: in both modes it only receives events.
- **`--place-game X,Y`** (Linux with an X11 session only). When a new run starts: `xdotool search --sync --name
  '^cub3D$'` (5 s timeout), `xdotool windowmove <id> X Y`, then `xwininfo -id <id>` for the absolute position and size of
  the drawing area, sent to the page as a `layout` event. Without it, or in replay, the page puts the game at (0, 0).
  If a tool is missing or the session is Wayland, `view` says so once and goes on without placing.

## Events

Every event has `n` (its index) and `kind`:

| `kind` | Fields | From |
|---|---|---|
| `run` | `run_id`, `policy`, `seed` | the folder's name |
| `row` | `t`, `tactic` | `episode.jsonl` |
| `decision` | `t`, `answered_at`, `tactic`, `applied`, `reason`, `probabilities` (Jev) or `null`, `confidence` (Jev) or `null`, `rules`, `read` | `decisions.jsonl`, plus two fields added by `view` |
| `end` | `outcome`, `survival_seconds`, `damage_taken` | `result.json` |
| `layout` | `x`, `y`, `width`, `height` of the game's drawing area, in screen pixels | `--place-game` |

- `rules` = `policies.scripted_tactic(state)`: the real rules, not a copy of them.
- `read` = `describe_state(state)`: at most three short facts, from a fixed table, in this order of priority:
  the nearest threat (`runner, close, left`; or `nothing in view, 3 left`), `cornered` when true, `health low` or
  `health medium` when not high, `boss here` when the boss is present. Tested on every value that occurs in the T9 runs.
- The page counts "same as the rules" over the decisions that were applied.
- Milliseconds are not sent to the page: it does not show them (design rule 7).

## Layout

The recorded area is 1920×1080 with its origin at the top-left of the game's drawing area. All sizes are in that area's
pixels; the page offsets them by the `layout` event.

```
x 0                        1280                    1920
y 0 ┌──────────────────────┬────────────────────────┐
    │                      │ 6.5 s                  │ 28 px, muted
    │                      │ KITE                   │ Mono SemiBold 112 px
    │   game 1280×720      │ back away, keep firing │ Sans 32 px
    │   (its own hp bar    │ ENGAGE ─         3 %   │ four rows, Mono 28 px,
    │   and wave dots)     │ KITE   ━━━━━━━  97 %   │ bars 4 px high
    │                      │ RETREAT          0 %   │
    │                      │ SEARCH           0 %   │
    │                      │ rules  KITE            │ Mono 32 px
    │                      │ runner, close, left    │ Sans 28 px, at most 3
y720├──────────────────────┴────────────────────────┤
    │ Jev    ▇▇▇ENGAGE▇▇▇▇KITE▇▇▇ENGAGE▇▇▇           │ two bands, 44 px high,
    │ rules  ▇▇▇ENGAGE▇▇▇▇KITE▇▇▇▇▇▇ENGAGE▇▇         │ 0-30 s axis, 28 px ticks
    │ same choice as the rules: 27 of 29             │ Sans 32 px
    │ Jev picks one of four tactics every half       │ Sans 32 px, muted
    │ second. The code aims, fires and walks.        │
y1080└──────────────────────────────────────────────┘
```

- **Words under the tactic** (what the code does, read in `controller.py`): `ENGAGE` "stand still and fire",
  `KITE` "back away, keep firing", `RETREAT` "get to open space", `SEARCH` "walk to the nearest zombie". The code fires
  whenever a target is lined up, whatever the tactic.
- **Time axis:** 0-30 s; past 30 s it scrolls with the last 30 s. The cursor moves between rows by the page's clock and
  snaps to each row (rows come every 0.5 s).
- **When the rules differ,** both names are shown as they are; nothing turns red. The difference is the content.
- **Before a run** (waiting), the page shows only the thesis line and four 1-px corner marks of the recorded area, to
  align the recorder's selection; they go away when the run starts.
- **The end:** when `end` arrives, the right column shows `won in 13.6 s · no damage` for 3 s; the game window is gone by
  then (the agent quits the game), and the page fades (200 ms) to the conclusion card over the whole area.

## Look (design rules of `spec.md`)

- **Type:** IBM Plex, Mono for the tactic names and numbers (tabular figures), Sans for words; weights 400 and 600 only.
  Sizes at 1920×1080: tactic 112 px; card headline 72 px, card lines 48 px; everything else 28-32 px; nothing under 28.
- **Colour tokens** (the only colour literals in the page, on `:root`): `--bg #121212`, `--fg #ECECEC`, `--muted #8C8C8C`,
  `--rule #2B2B2B`, and one per tactic, chosen in task V3 with the palette and the validator of the `dataviz` skill: four
  hues apart for colour-blind viewers, each at least 3:1 against `--bg`. Bands always carry the tactic's name inside or
  beside them.
- **Motion:** `transition` on `opacity` and `width` only, 150-200 ms. No `@keyframes`.
- **The lint** (AC8, `test_view_page.py`) reads `index.html` and fails on: any character in Unicode's Extended_Pictographic
  set; `gradient(`, `box-shadow`, `text-shadow`, `blur(`, `backdrop-filter`, `@keyframes`; a `transition` longer than
  200 ms; a `font-family` other than the bundled ones; a `#` colour or `rgb(` outside `:root`; `http://` or `https://`;
  and, in the strings shown on screen (one `TEXT` table in the page, and `view_conclusion.json`), a `!` or a marketing word (`magic`, `revolutionary`, `game-changing`, `AI-powered`, `unleash`,
  `supercharge`, `seamless`, `cutting-edge`, `thinking`). It is seen failing once per item on a copy of the page.

## The final card (`view_conclusion.json`), draft for the owner's OK

```
What I found

Jev won 40 of 40 games. Four hand-written rules won 40 of 40 too.
It chose what the rules would choose in 91-98 % of its decisions.
Neither won faster.
About $0.001 a game, and an answer in about 0.3 s.
What changed its play was how I wrote the four options.

120 games: three players, 20 held-out seeds, two maps, on a Mac, 2026-10-10. typesafe/jev-1.13. Details: R17, R15.
```

Each number has its source in the file, and `test_view_conclusion.py` recomputes it from
`agent/runs/eval-20261010T122708Z-darwin` (wins of `jev` and `scripted`; agreement with `scripted_tactic` per map; the
sign test's p over 0.8 on both maps for "neither won faster"; spend per Jev episode; latency p50). The last line rests on
the tuning, where the wording was the only thing changed (R15: damage in 6 of 20 games before the rewording, 1 of 40
after); it carries no number on the card.
**The text is the owner's to approve (task V4).**

## Testing

- **On the Mac, free, with no Colima:** unit tests; a test that writes a run folder line by line with pauses, with `view`
  following it, and measures when each event is served (AC1); replay timing (AC6); the server's routes and the bind
  address (AC10); the lint with its deliberate breaks (AC8); the card's numbers (AC5).
- **Screenshots:** `view --replay <a T9 Jev folder> --until T` and Chrome headless at 1920×1080 (`--headless
  --screenshot --window-size=1920,1080`), for three moments (AC3). Claude looks at them; the owner gets them before
  the rehearsal.
- **On the owner's Linux (🔑):** the session check, the rehearsal with `scripted` (free) and then the takes with `jev`
  (paid, after the OK). See `tasks.md`.

## Rejected alternatives (the reasons are in the research)

- A terminal panel, text inside the game window, a Tk window, a video composed by a program (research, "Options").
- Pushing events from inside `play()` (a callback or a queue in the agent): it would put new code in the loop whose
  stalls spec 002 measured. Reading the flushed files gives the same events from outside it.
- Server-sent events: a long-lived connection is more code in `http.server` than a 50 ms poll on localhost.
- Showing latency per decision: the owner found it noise; the card gives the measured median once.
- Drawing hp and the wave: the game already draws them (F2).
