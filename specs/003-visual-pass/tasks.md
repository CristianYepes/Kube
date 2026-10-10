# Tasks 003 — The visual pass

> v0.1, 2026-10-10, draft. `spec.md` says what, `plan.md` how, `specs/research-2026-10-10.md` what was checked.
> Rules carried over from spec 002: tests first and seen failing; each check broken on purpose once and restored
> (`cmp` against a copy); `PYTHONDONTWRITEBYTECODE=1`; one local commit per task (approved with the spec, V0); push only
> when the owner asks; files in English. 🔑 = the owner does it. Commands for the owner's terminal are short lines, one
> step at a time, and the owner pastes the output.

- [x] 🔑 **V0** — The owner reads `spec.md`, `plan.md` and this file, says OK or what to change, and answers the open
  question: the text on screen in English or in Spanish.
  - **Done when:** the OK is given and the language is written into `spec.md` (the open question removed).
  - **Done 2026-10-10:** the owner approved the spec ("me parece bien") and chose English. With the spec approved, each
    task below is a local commit; nothing is pushed until the owner asks.

- [ ] 🔑 **V1** — What the owner's Linux has. Do L5 of spec 002 in the same sitting first (its first step is
  `git pull --ff-only`), then, in a terminal on the Linux desktop:

  ```bash
  echo $XDG_SESSION_TYPE
  xrandr | grep '\*'
  command -v xdotool xwininfo xprop firefox
  ```

  - `x11` is what `--place-game` needs. If it says `wayland`: log out and pick "Ubuntu on Xorg" on the gear of the
    login screen. If there is no gear, setting `WaylandEnable=false` in `/etc/gdm3/custom.conf` changes every login on
    that machine: **the owner decides**, and it is undone by putting the line back.
  - The screen should be at least 1920×1200, so that the area under the game's title bar and GNOME's top bar still
    fits 1080 rows (research, gotchas). If it is 1920×1080, the bottom band gets shorter and the video is about
    1920×1011, which LinkedIn accepts (research F5).
  - A missing `xwininfo` or `xprop` comes with `sudo apt install x11-utils`.
  - **Done when:** the four facts are written into the research (F3) with the date.

- [x] **V2** — `view.py`: the events of a run folder, in follow and in replay. **Done 2026-10-10.**
  - Tests first: `describe_state` on every value of the T9 runs (AC4); `rules` equal to `scripted_tactic`; a run folder
    written line by line by the test, with `view` following it, each event served at most 150 ms after its line (AC1);
    a half-written line is not served until it is complete; replay of a T9 Jev folder releases the last decision within
    0.2 s of its `answered_at` (AC6); `--until T` releases nothing after `T`.
  - **Commit:** `agent: the events of the view, from a run folder` (the command itself comes with V3, so the first message
    would have promised too much).
  - **Done when:** the new tests pass, each was seen failing, and the suite is green.
  - **Done 2026-10-10:** 32 tests in `agent/tests/test_view.py`, seen failing first (no module) and then against **32 deliberate
    breaks of `view.py`, all caught**, the file restored and identical (`cmp`). The suite: 579 passed. AC1 measured on 120 rows:
    median 45 ms, p95 70 ms, max 80 ms between writing a row and the page's poll seeing it (limit 150 ms). Two tests of mine
    would have passed for the wrong reason (the one on folders that are not runs, and the one on the end coming after the
    rows) and were rewritten before the breaks. What changed from the plan: the polls are 25 ms, the `run` event carries
    `mode`, no `confidence` (the page does not use it), and the facts are `being hit` and not `boss here`.

- [x] **V3** — The page, its fonts and the server. **Done 2026-10-10.**
  - Fonts: the four `woff2` files and `OFL.txt` of IBM Plex from its official release (research F6), their SHA-256
    written here.
  - The colour of each tactic chosen with the `dataviz` skill's palette and validator (`plan.md`, "Look").
  - Tests: the lint of the design rules with one deliberate break per item (AC8); the sizes of AC9 read from the page's
    CSS; the server answers only `/`, `/fonts/<one of its files>` and `/events`, gives 404 to anything else (`..` and an
    encoded `%2e%2e` included), listens on 127.0.0.1 only, and opens no outgoing connection (AC10).
  - **Commit:** `agent: the view page, with IBM Plex`.
  - **Done when:** the tests pass, each seen failing, and the page loads in Chrome on the Mac from a replay.
  - **Done 2026-10-10.** The page, `kube-agent view` (`--port`, `--replay`, `--until`), the server and the draft of the card
    (`view_conclusion.json`, whose numbers V4 checks). **Tests:** `test_view_server.py` 45, `test_view_page.py` 43 (of them 31
    deliberate breaks of the page, each caught by the check), 8 new in `test_cli.py`; all seen failing first (no `PAGE_DIR`),
    then **31 deliberate breaks of `view.py` and `cli.py`, all caught**, files restored and identical (`cmp`). The suite:
    681 passed. Two things that came from reading my own tests: the `serve` threads of two tests were not daemons (a failing test
    would have hung pytest), and the worker-failure test could hang; both fixed before the breaks.
  - **Fonts** (IBM Plex, OFL-1.1, from the releases `@ibm/plex-sans@1.1.0` and `@ibm/plex-mono@2.5.0` of github.com/IBM/plex,
    2026-10-10; the license file is the one of the release, `OFL.txt` next to them; the test pins every hash):
    `IBMPlexSans-Regular.woff2` ba711a3085ff9f27440b6b9c4550cfc47c97bf36591d5da958b975bb3add8c1a;
    `IBMPlexSans-SemiBold.woff2` f78048030eab62e860efa39a0df79e2e5581bf122eb95b9bc42c0b8a4988d205;
    `IBMPlexMono-Regular.woff2` ba204497f16b6d334cee9d1e963a831b73e3a56e1d6300a8489d18df7214b350;
    `IBMPlexMono-SemiBold.woff2` 6a825b4824c01cbb401e829e5a066a1818411bcb3538b5a5792c5ca9b82343c3;
    `OFL.txt` 7e6b2818edbd8f6a01ae80641cc8f16a51080d08fb4e532be3a0b6f74adb07da.
  - **Colours:** `node <dataviz skill>/scripts/validate_palette.js "#3987e5,#c98500,#d55181,#008300" --mode dark --surface "#121212"
    --pairs all` -> all checks pass, with one WARN on colour-blind separation (6.9) that the names in the bands and the legend
    make legal (`plan.md`, "Look"). The skill's first four slots fail on all pairs; of the 70 choices of four hues only two pass.
  - **Seen:** Chrome headless at 1920x1080 on a replay of a T9 Jev game (`eval-20261010T122708Z-darwin`, seed 101, `subject_map`),
    mid-game, at the end and the card. The page loads, draws the decision, the four probabilities, what Jev read, the rules'
    choice, the bands and the count, and the card fits on one screen. What the first look changed: the last tick wrapped, the
    window was 30 s and left two thirds of the band empty (now 25 s), the big word did not say whose it was (now `Jev chose`),
    `rules ENGAGE` became `rules would choose ENGAGE`, the bars went from 4 to 8 px, and the card lines were shortened until each
    fits one row (no widow). The page's package files travel in the wheel (`uv build --wheel` lists them).
  - **Not checked yet:** that the numbers on the page are the ones of the run, moment by moment (V5), and the game window on
    top of the page (V6, V7).

- [ ] **V4** — The final card (the file exists since V3, with the draft text; V4 adds the facts and the check). `view_conclusion.json` with the text of `plan.md` and the source of each number;
  `test_view_conclusion.py` recomputes them from `agent/runs/eval-20261010T122708Z-darwin` (AC5) and is seen failing
  on a copy with one number changed.
  - 🔑 The owner approves the text, or changes it; the test then checks the new text.
  - **Commit:** `agent: the conclusion card of the view`.
  - **Done when:** the owner approved the text and the test passes.

- [ ] **V5** — Stills on the Mac, free. A T9 Jev folder replayed and stopped at three moments (a choice the rules share,
  one where they differ, the last decision), plus the result line and the card; Chrome headless at 1920×1080.
  - Claude checks each still against that folder's `decisions.jsonl` (AC3) and looks at them; the owner gets the five
    images.
  - **Done when:** 🔑 the owner says the look is right, or what to change (and V3-V4 are redone for it).

- [ ] **V6** — `--place-game X,Y` for the Linux take.
  - Tests with fake `xdotool` and `xwininfo` (no X needed): the window is looked for by its name with a 5 s timeout, moved,
    and its drawing area read into a `layout` event; a missing tool, a timeout or a Wayland session give one clear
    message and the view goes on unplaced.
  - **Commit:** `agent: the view places the game window on X11`.
  - **Done when:** the tests pass, each seen failing.

- [ ] 🔑 **V7** — Rehearsal on the owner's Linux, free (`scripted`). After `git pull --ff-only`:
  - Terminal 1: `cd ~/Desktop/Kube/agent`, then `uv run kube-agent view --place-game 0,0`.
  - Firefox: open `http://127.0.0.1:8765`, then F11 (full screen).
  - Terminal 2, then click Firefox within the 5 s:

    ```bash
    cd ~/Desktop/Kube/agent
    sleep 5; uv run kube-agent run --runner local \
      --policy scripted --seed 3
    ```

  - Three takes like that, and one more of the same seed with `view` stopped, to compare the stalls.
  - **Done when:** AC7 (the game's drawing area where the layout expects it in 3 of 3) and AC2 (no more stalls than
    without the view) hold, from the owner's pasted output and one screenshot. If the window could not be placed, stop
    here and decide with the owner (research F4, the fallback).

- [ ] 🔑 **V8** — Takes with Jev. **Paid: ask the owner for the OK first.** About $0.0009 a game on `subject_map` and
  $0.0013 on `pillars` (R17); ten takes are about $0.013 [calc], with the cap of $0.05 a run of spec 002. Development
  seeds (1-20) only: the test seeds stay the evaluation's.

  ```bash
  cd ~/Desktop/Kube/agent
  ( set -a; . ~/jev/libros/.env; set +a; sleep 5; \
    uv run kube-agent run --runner local \
    --policy jev --seed 3 )
  ```

  - The owner records with Shift-Command-5 on the Mac, a selected portion that starts at the top-left corner of the
    game's drawing area (the corner marks of the page show it before the run), and stops after the card.
  - **Done when:** at least one take the owner likes is on disk, and its run folder is in `agent/runs/` on the Linux.

- [ ] 🔑 **V9** — The video. The owner trims the start (the window moves into place there) and the end in QuickTime, and
  says it can be posted (AC11). The run folders of the takes are committed from the Linux and pushed only when the owner
  asks (as in the L checkpoints of spec 002).
  - **Done when:** the owner says it can be posted.

- [ ] **V10** — Docs. `specs/CONTEXT.md` ("Status"), the post notes (`~/jev/NOTAS_POST_JEV_CUB3D.md`: which take, its run
  folder, its cost), the project memory.
  - **Commit:** `specs: spec 003 done`.
  - **Done when:** the docs say what happened, and nothing in them is left saying "draft".
