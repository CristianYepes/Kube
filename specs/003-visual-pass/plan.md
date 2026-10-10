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
   ├─ reads the newest run folder every 25 ms, adds `rules` and `read` to each decision
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

- **Follow.** Every 25 ms it looks in `agent/runs/` for a folder of `kube-agent run` (UTC time, policy, seed, machine; not
  `eval-` or probe folders) created at or after the moment `view` started, and reads the new complete lines of
  `episode.jsonl` and `decisions.jsonl`, and `result.json` when it appears. The page asks for events every 50 ms, so a row
  is on the page 80 ms after it is written at most (measured, V2). A half-written last line is left for the next read. When the episode ends it goes back
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
| `run` | `run_id`, `policy`, `seed`, `mode` (`live` or `replay`) | the folder's name |
| `row` | `t`, `tactic` | `episode.jsonl` |
| `decision` | `t`, `answered_at`, `source`, `tactic`, `applied`, `reason`, `probabilities` (Jev) or `null`, `rules`, `read` | `decisions.jsonl`, plus two fields added by `view` |
| `end` | `outcome`, `survival_seconds`, `damage_taken` | `result.json` |
| `layout` | `x`, `y`, `width`, `height` of the game's drawing area, in screen pixels | `--place-game` |

- `rules` = `policies.scripted_tactic(state)`: the real rules, not a copy of them.
- `read` = `describe_state(state)`: at most three short facts, in this order: the nearest threat (`runner, close, left`; or
  `no zombie left`), `being hit`, `cornered`, `health low` or `health medium` (when not high), and `1 in view, 3 left`. Every
  word is a value of the state or one of these phrases; tested on every state of the T9 runs.
- A decision that was not applied (`stale`, `below_threshold`, `episode_ended`, an error) is sent with `applied: false`; the
  page does not show it. An answer that came after the end has `answered_at: null`.
- The page counts "same as the rules" over the decisions that were applied.
- Milliseconds are not sent to the page: it does not show them (design rule 7).

## The server (as built, V3)

`view.make_server` gives a `ThreadingHTTPServer` on `127.0.0.1` only. It answers GET and nothing else (405 with `Allow: GET`):
`/` the page, `/fonts/<one of the four names>`, `/conclusion`, and `/events?after=N`. Anything else is a 404, whatever
the path (`..`, `%2e%2e`, a trailing slash, a file that is next to the fonts, such as `OFL.txt`): the name of a font is looked
up in a fixed list, a file name is never made from the request. A request whose `Host` is not `127.0.0.1:<port>` or
`localhost:<port>` is a 404, which stops a page on another site, whose name points to this machine, from reading the run
(DNS rebinding). Every answer carries `Content-Security-Policy: default-src 'none'; ...; frame-ancestors 'none'`,
`X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer` and `Cache-Control: no-store`. The module imports nothing that
opens a connection and never reads the environment (a test reads its source for both). A worker that dies stops the server and
says why; Ctrl-C stops it cleanly.

## Layout

The recorded area is 1920×1080 with its origin at the top-left of the game's drawing area. All sizes are in that area's
pixels; the page offsets them by the `layout` event.

```
x 0                        1280                    1920
y 0 ┌──────────────────────┬────────────────────────┐
    │                      │ Jev chose        6.5 s │ Sans 32 px, muted
    │                      │ KITE                   │ Mono SemiBold 112 px
    │   game 1280×720      │ back away, keep firing │ Sans 36 px
    │   (its own hp bar    │ ENGAGE ─          3%   │ four rows, Mono 32 px,
    │   and wave dots)     │ KITE   ━━━━━━━   97%   │ bars 8 px high
    │                      │ RETREAT ─         0%   │
    │                      │ SEARCH  ─         0%   │
    │                      │ rules would choose KITE│ Sans 36 px, name in Mono
    │                      │ runner, close, left    │ Sans 32 px, at most 3
y720├──────────────────────┴────────────────────────┤
    │ Jev    ▇▇▇ENGAGE▇▇▇▇KITE▇▇▇ENGAGE▇▇▇           │ two bands, 44 px high,
    │ rules  ▇▇▇ENGAGE▇▇▇▇KITE▇▇▇▇▇▇ENGAGE▇▇         │ 0-25 s axis, 28 px ticks
    │ same choice as the rules: 27 of 29     legend  │ Sans 36 px; legend Mono 28 px
    │ Jev picks one of four tactics every half       │ Sans 32 px, muted
    │ second. The code aims, fires and walks.        │
y1080└──────────────────────────────────────────────┘
```

- **Words under the tactic** (what the code does, read in `controller.py`): `ENGAGE` "stand still and fire",
  `KITE` "back away, keep firing", `RETREAT` "get to open space", `SEARCH` "walk to the nearest zombie". The code fires
  whenever a target is lined up, whatever the tactic.
- **Time axis:** 0-25 s, so that the episodes of both maps (11 to 24 s in T9) fit without moving; past 25 s it scrolls with
  the last 25 s. The bands are drawn by decision (each decision from its state's time to the next one's), the clock steps
  with the rows (every 0.5 s), and nothing is interpolated.
- **Whose word it is:** the top line of the panel says `Jev chose` (or `rules chose`), and the time on the right; at the end the
  result takes its place.
- **When the rules differ,** both names are shown as they are; nothing turns red. The difference is the content.
- **Before a run** (waiting), the page shows only the thesis line and four 1-px corner marks of the recorded area, to
  align the recorder's selection; they go away when the run starts.
- **The end:** when `end` arrives, the right column shows `won in 13.6 s · no damage` for 3 s; the game window is gone by
  then (the agent quits the game), and the page fades (200 ms) to the conclusion card over the whole area.

## Look (design rules of `spec.md`)

- **Type:** IBM Plex, Mono for the tactic names and numbers (tabular figures), Sans for words; weights 400 and 600 only.
  Sizes at 1920×1080: tactic 112 px; card headline 96 px, card lines 64 px (13 px on a phone 390 px wide, which is what makes
  the card readable there); everything else 28-36 px; nothing under 28.
- **Colour tokens** (the only colour literals in the page, on `:root`): `--bg #121212`, `--fg #ECECEC`, `--muted #8C8C8C`,
  `--rule #2B2B2B`, and one per tactic: `ENGAGE #3987E5` (blue), `KITE #C98500` (amber), `RETREAT #D55181` (magenta),
  `SEARCH #008300` (green). **How they were chosen (2026-10-10):** with the validator of the `dataviz` skill
  (`validate_palette.js`), dark mode, surface `#121212`, **all pairs**, because any two tactics can sit side by side in a band.
  The skill's own first four slots fail that (amber beside orange: colour-blind distance 4.8, normal vision 10.6, floor 15);
  of the 70 ways to take four of its eight dark hues, only two pass, and this is one. Result: lightness band PASS, chroma PASS,
  normal-vision floor PASS (worst 19.3), contrast against the background PASS (3.79 to 6.10), colour-blind separation WARN
  (worst 6.9, green and amber under protanopia; floor 6, target 8), which the skill allows only with a second channel: each band
  segment carries the tactic's name when it is wide enough, there is a legend, and the big word names it too. The test
  `test_the_four_tactic_colours_are_the_validated_ones` pins the values; the command is in `tasks.md`, V3.
- **What of the dataviz skill is not built, on purpose:** the table view, the texture fill and the hover tooltips. They serve a
  chart that people use; this page is the backdrop of a recording, with the pointer hidden. The identity channel is the name.
- **Motion:** `transition` on `opacity` and `width` only, 150-200 ms. No `@keyframes`.
- **The lint** (AC8, `test_view_page.py`) reads `index.html` and fails on: any character in Unicode's Extended_Pictographic
  set; `gradient(`, `box-shadow`, `text-shadow`, `blur(`, `backdrop-filter`, `@keyframes`; a `transition` longer than
  200 ms; a `font-family` other than the bundled ones; a `#` colour or `rgb(` outside `:root`; `http://` or `https://`;
  and, in the strings shown on screen (one `TEXT` table in the page, and `view_conclusion.json`), a `!` or a marketing word (`magic`, `revolutionary`, `game-changing`, `AI-powered`, `unleash`,
  `supercharge`, `seamless`, `cutting-edge`, `thinking`). It is seen failing once per item on a copy of the page.

## The final card (`view_conclusion.json`), draft for the owner's OK

```
What I found

Jev won 40 of 40 games.
Four hand-written rules won 40 of 40 too.
Jev matched the rules in 91 to 98% of its decisions.
No difference in how fast they won.
About $0.001 a game, and an answer in 0.3 s.
What changed its play was how I wrote the four options.

120 games, 20 held-out seeds, two maps, a Mac, 2026-10-10. typesafe/jev-1.13. R17, R15.
```

Each number has its source in the file (`facts`, V4), and `test_view_conclusion.py` recomputes it from
`agent/runs/eval-20261010T122708Z-darwin` (wins of `jev` and `scripted`; agreement with `scripted_tactic` per map; the
sign test's p above 0.8 on both maps for "no difference in how fast"; spend per Jev episode; latency p50). The last line
rests on the tuning, where the wording was the only thing changed (R15: damage in 6 of 20 games before the rewording, 1 of 40
after); it carries no number on the card. It was shortened in V3 until each line fits one row at 64 px (the page was
rendered in Chrome to check it).
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
