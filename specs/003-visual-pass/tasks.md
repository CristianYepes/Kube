# Tasks 003 — The visual pass

> v0.1, 2026-10-10, draft. `spec.md` says what, `plan.md` how, `specs/research-2026-10-10.md` what was checked.
> Rules carried over from spec 002: tests first and seen failing; each check broken on purpose once and restored
> (`cmp` against a copy); `PYTHONDONTWRITEBYTECODE=1`; one local commit per task (approved with the spec, V0); push only
> when the owner asks; files in English. 🔑 = the owner does it. Commands for the owner's terminal are short lines, one
> step at a time, and the owner pastes the output.

> **2026-10-11: the plan below is replaced.** V1 measured the owner's Linux: a Wayland session whose largest screen mode
> is 1280x800, while the game window is a fixed 1280x720 (`includes/cub3d.h`). The 1920x1080 page of V2-V6 cannot sit
> next to the game there, and the owner rejected its look ("AI slop"). The new direction, from the owner: everything on the
> Linux, the game window and a minimal strip on top of it that says what is happening; nothing on the Mac. The Tk of uv's
> Python draws bitmap fonts there, so the strip uses GTK with the system Python. First probe: `agent/strip_demo.py`, a
> sample strip for 90 s that the owner runs while the bot plays. The tasks below stay as the record of what was built;
> they are rewritten once the owner approves the strip.

- [x] 🔑 **V0** — The owner reads `spec.md`, `plan.md` and this file, says OK or what to change, and answers the open
  question: the text on screen in English or in Spanish.
  - **Done when:** the OK is given and the language is written into `spec.md` (the open question removed).
  - **Done 2026-10-10:** the owner approved the spec ("me parece bien") and chose English. With the spec approved, each
    task below is a local commit; nothing is pushed until the owner asks.

- [ ] 🔑 **V1** — What the owner's Linux has. (L5 of spec 002 was done first, in the same sitting, on 2026-10-11, and the branch is pulled.)
  In a terminal on the Linux desktop. **Not in the terminal of L5**: there `DISPLAY` is `:99`, the virtual screen, so `xrandr` would measure
  that one; the command below says `DISPLAY=:0`, the real one (Xwayland, if the session is Wayland):

  ```bash
  echo $XDG_SESSION_TYPE
  DISPLAY=:0 xrandr | grep '\*'
  for t in xdotool xwininfo xprop firefox; do
    printf '%-9s %s\n' $t "$(command -v $t || echo MISSING)"
  done
  ```

  - `x11` is what `--place-game` needs. If it says `wayland`: log out and pick "Ubuntu on Xorg" on the gear of the
    login screen. If there is no gear, setting `WaylandEnable=false` in `/etc/gdm3/custom.conf` changes every login on
    that machine: **the owner decides**, and it is undone by putting the line back.
  - The screen should be at least 1920×1200, so that the whole 1920×1080 of the page fits under the game's title bar (about 37 px,
    to be measured). On a 1920×1080 screen it still works: the content of the page ends at row 1019 of its 1080, so the
    recorded region can end about 1040 rows down (1920×1040 is inside what LinkedIn accepts, research F5).
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

- [ ] **V4** — The final card, with its numbers checked. **Built 2026-10-10; the one point left is the owner's OK of its words.**
  - `view_conclusion.json` has the lines, the source and a `facts` object; `test_view_conclusion.py` recomputes every fact from the raw
    runs of the evaluation (R17) and of the tuning (R15), and checks that each line says what its facts say, and that every number
    in the lines is one of the facts.
  - 🔑 **The owner approves the text, or changes it** (the test then checks the new words). What changed from the draft of `plan.md`,
    and why: (1) the last line was "What changed its play was how I wrote the four options": a cause, and the only claim not measured
    on the held-out seeds. It is now "Rewording the four options changed its play: games with damage went from 6 of 20 to 1 of 40",
    which is a before-and-after with its numbers (R15), and the card's source says that this one is from development seeds, so that
    the 120 held-out games are not credited with it. (2) "Jev chose what the rules choose" became "Jev matched the rules". (3) "Neither
    won faster" became "No difference in how fast they won" (the sign test gives p of 0.82 on both maps; it is an observation, not
    a proof of equality). The honest weak point is line 6: it is one change, before and after, on the same seeds, not a randomised test.
  - **Commit:** `agent: the conclusion card of the view`.
  - **Done 2026-10-10 (all but the OK):** 18 tests, 14 of them deliberately wrong cards, each caught; seen failing first (a card
    with no `facts`). The recomputation agrees with numbers I had computed by other scripts (R17: 40 of 40 and 40 of 40; 91.0% and 97.7%;
    p of 0.815 and 0.824; $0.00108 and 292 ms; and R15: 6 of 20 and 1 of 40). The card was rendered in Chrome until every line fit one
    row at 64 px, the options sentence sits apart from the first five lines, and the source is two rows.
- [ ] **V5** — Stills on the Mac, free. **Built and checked 2026-10-10; the one point left is the owner's OK of the look.**
  - A T9 Jev folder replayed and stopped at three moments, plus the result line and the card; Chrome headless at 1920x1080.
  - **Checked against the data (AC3):** `kube-agent view --replay <game> --until T`, Chrome dumps the DOM, and what the page paints
    is compared with what `episode.jsonl` and `decisions.jsonl` give at T, computed apart: the word and whose it is, the clock, the
    four percentages, the rules' choice, what Jev read, the count, and **the tactic of every segment of both bands, in order**. Two
    games, three moments each (a choice Jev shares with the rules, one where it differs, the last decision): `subject_map` seed 101
    (stopped at 6.24 s, 2.85 s and 13.85 s) and `pillars` seed 103 (5.68 s, 17.76 s and 21.17 s). **0 differences in the 2 x 3 moments.** Broken on purpose
    five ways (the rules' name, the rules band, the count, the percentages, the facts), the check showed each one; a sixth break,
    `floor` instead of `round` on the percentages, was not shown because it changes nothing: all 5,208 probabilities of the 40 games
    are whole percents.
  - **Done when:** 🔑 the owner says the look is right, or what to change (and V3-V4 are redone for it).
- [x] **V6** — `--place-game X,Y` for the Linux take. **Done 2026-10-11, on X11 in the container; on the owner's Linux it is V1 and V7.**
  - Tests with fake `xdotool` and `xwininfo` (no X needed): the window is looked for by its name with a timeout, moved,
    and its drawing area read into a `layout` event; a missing tool, a timeout or a window that did not go where it was asked give one
    clear message and the view goes on unplaced.
  - **Commit:** `agent: the view places the game window on X11`.
  - **Done when:** the tests pass, each seen failing.
  - **Done 2026-10-11.** `view.place_game_window` and the `--place-game X,Y` option. `test_view_place.py` 27 tests and 12 new ones
    in `test_cli.py`; 24 of the first 25 failed before the code existed; then **27 deliberate breaks of `view.py` and `cli.py`, all caught**,
    files restored and identical (`cmp`); the suite: 738 passed. Two holes of my own tests found while preparing the breaks, and closed:
    nothing checked the moment given to the window manager between moving the window and measuring it, and nothing checked that a
    placement that waits for the window does not stop the rows of the game from reaching the page.
  - **Run for real against the real tools.** The container `kube-dev` (Xvfb `:99`, no window manager, `xdotool` of the image,
    `xwininfo` of `x11-utils`, which I installed in the container for this, because the image does not have it): my code, through
    `docker exec`, while a real game played (`scripted`, seed 3, won in 11.13 s; `agent/runs/20261010T221030Z-scripted-s3-darwin`):
    it found the window by `^cub3D$`, moved it to 100,50 and measured **100,50, 1280x720, in 0.93 s**, with no warning. What that
    showed: the labels of the real `xwininfo` are the ones the code reads, and its answer is now the fixture of the tests;
    `xdotool search --name` takes a regular expression (`cub3` matches, `^cub$` does not); with no match it exits with 1 (with `--sync`
    it waits instead, which is why every call has a 10 s timeout). A second game (`scripted`, seed 101, won in 10.69 s) gave real
    frames of the game for the mock-ups of V5.
  - **Mock-ups for the owner's look** (`~/jev/vista-previa-spec003/`, outside git): the page of a real Jev game with a real frame of
    the game in the corner, made by overlaying a frame from the container on the screenshot. The frame is not from the same game as
    the data: the mock-up shows the composition, not a synchronised recording.
  - **The page also warns** when the browser zoom or the display scale is not 100% (`window.devicePixelRatio`), because the game
    window is placed in screen pixels and the page must be at 1 to 1.
  - **Not checked** (V1, V7, on the owner's Linux): that its window manager lets the window be moved in an X11 session, how much its
    title bar offsets the drawing area (the page follows where the window lands, so only the margin matters), and Wayland, where
    `xdotool windowmove` is not promised to work (research F4): there the code warns if the window ended far from the corner.

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
