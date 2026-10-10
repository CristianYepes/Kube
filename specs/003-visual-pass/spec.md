# Spec 003 — The visual pass: a clean live view of an episode, for a screen recording

> v0.2, 2026-10-10. Status: **approved by the owner on 2026-10-10** ("me parece bien"), text on screen in English. Research: `specs/research-2026-10-10.md` (it wins if
> this file disagrees). How: `plan.md`. Steps: `tasks.md`.

## Problem

Spec 002 measured Jev playing the zombie mode of cub3D. The owner wants a short video of it for the LinkedIn post. What
exists today is a game window and log files. Shown as they are, logs are rows of milliseconds and JSON: they say
nothing to someone scrolling a feed, and the owner finds that look ugly. Demos of AI tools often go the other way, with
glowing panels, gradients, "thinking" animations and emoji, which reads as marketing. This account's voice is dry and
exact (`~/jev/post-linkedin/ESTILO_POSTS_LINKEDIN.md`).

The owner decided (2026-10-10): **the owner records it live, on the owner's Linux, in 16:9.**

## Who it is for and how we know it worked

- **For:** the owner, who records a take and posts it; then the people who watch it, mostly on a phone.
- **It worked when:** the owner records a take, on the first or a few tries, that shows at one glance (1) the game being
  played, (2) which of four tactics Jev chose and how sure it was, (3) what the four hand-written rules would have chosen
  from the same state, and (4) at the end, the conclusion of spec 002. The owner would post it as it is, and every number
  in it is the measured one.

## Scenarios

1. The owner opens the view in a browser on the Linux desktop, starts a Jev episode, and records the screen. While the
   game plays, the view beside it shows each decision as it arrives. When the game ends, the view shows the result and
   then the conclusion. The owner stops the recording and trims it.
2. The owner (or Claude) replays a recorded episode in the view on the Mac, with no game and no paid call, to see how the
   view looks at any moment before recording.

## Functional requirements

- **FR1 — Live.** WHILE an episode is played, THE VIEW SHALL show each decision once the agent has written it, with no
  change to how the agent plays.
- **FR2 — What it shows during the game.** For the decision in force, THE VIEW SHALL show:
  - the tactic, as its name and a few words saying what the code does with it;
  - the four options with the probability Jev gave each (for a Jev episode);
  - what Jev read, as at most three short facts taken from the state it was sent;
  - the tactic the four rules would have chosen from that same state, and how many of the decisions so far were the same.
- **FR3 — Over time.** THE VIEW SHALL show the tactic chosen over the episode so far, and the rules' choice, on one time
  axis, so that agreement and disagreement can be seen.
- **FR4 — The end.** WHEN the episode ends, THE VIEW SHALL show its result (won or lost, time, damage), and then a card
  with the conclusion of spec 002, every number of it as measured in R17, and where those numbers come from.
- **FR5 — Replay.** THE VIEW SHALL replay a finished run folder at its real speed, and SHALL be able to stop at a given
  moment, so that the view can be seen and checked without playing.
- **FR6 — Placing.** On the owner's Linux, THE SYSTEM SHALL put the game window in the place the layout expects, without
  a hand on the mouse while the game plays.
- **FR7 — Restraint.** The view SHALL follow the design rules below.

### Design rules (FR7)

1. **Nothing decorative.** No gradients, shadows, glows, blur, glass, particles, logos, icons or emoji. Flat colour, thin
   rules, type.
2. **No fake intelligence.** No "thinking…" dots, no typing effect, no animated brain or spark. A decision appears when it
   was made; while Jev is being asked, nothing pretends to happen.
3. **Few words, the code's own names.** The tactics keep their names (`ENGAGE`, `KITE`, `RETREAT`, `SEARCH`). No
   exclamation marks, no superlatives, no marketing words.
4. **One type family, two weights at most.** One background, one text colour, one muted colour, and one colour per tactic,
   always together with the tactic's name (never colour alone).
5. **Movement only when a value changes**, short (at most 200 ms), and no other animation.
6. **Readable on a phone.** On a 16:9 video about 390 px wide on a phone, the tactic's name and the conclusion stay
   readable: few elements, large type.
7. **Numbers are measured ones**, with their unit, and the final card says what they were measured on. No per-decision
   milliseconds on screen.

## Acceptance criteria

- **AC1 (FR1)** — With the view following a run folder that a test writes row by row, each row is on the page at most
  150 ms after it is written.
- **AC2 (FR1)** — An episode played while the view runs has no more stalls than the same policy and seed without it
  (stalls as in spec 002, AC8), on the owner's Linux.
- **AC3 (FR2, FR3)** — A replay of a T9 Jev run, stopped at three moments (a choice the rules share, one they do not, and
  the last decision), gives screenshots in which the tactic, the four probabilities, the facts, the rules' choice and the
  count match that run's `decisions.jsonl` (checked by a test on the data the page receives, and by eye on the screenshot).
- **AC4 (FR2)** — Every fact shown comes from a fixed mapping of `state` fields, unit-tested on every field value that
  occurs in the T9 runs. No text on screen is generated by a model.
- **AC5 (FR4)** — Every number on the final card equals the one recomputed by a test from
  `agent/runs/eval-20261010T122708Z-darwin` and the spend ledger, and the card names its source.
- **AC6 (FR5)** — A replay at real speed shows the last decision within 0.2 s of its `answered_at` from the start.
- **AC7 (FR6)** — In the rehearsal on the owner's Linux, the game's drawing area lands where the layout expects it, in
  3 of 3 episodes.
- **AC8 (FR7)** — A test over the page's source fails on any emoji, gradient, shadow, blur, `@keyframes`, transition over
  200 ms, font family outside the bundled one, colour defined outside the list of tokens, external URL or exclamation mark
  in the text; it is seen failing on a copy of the page with each of them put in.
- **AC9 (FR7)** — At 1920×1080, the tactic's name is at least 96 px tall, the lines of the final card at least 48 px, and
  no text is under 28 px (on a phone 390 px wide: about 20, 10 and 6 px [calc]).
- **AC10 (security)** — The server listens on 127.0.0.1 only, serves only its own fixed files and the events of the run
  folder (a request for any other path, `..` included, gets a 404), makes no request to the network, and never reads the
  key file or the environment's credentials.
- **AC11 (the take)** — 🔑 The owner records a take and says it can be posted.

## Decided by the owner (2026-10-10)

- Live, on the owner's Linux, recorded by the owner; 16:9.
- **The text on screen is in English** (the post is published in English, by the account's style guide).
- After the build, the owner tests it on Linux together with L5 of spec 002, and the post is written from the
  conclusion in `~/jev/NOTAS_POST_JEV_CUB3D.md` with the videos.

## Out of scope

- Composing or editing the video (cutting, music, subtitles, voice): the owner records and trims.
- Any change to the game or to its C bridge.
- New measurements. The view shows a demo game; the claims are those of R17.
- A view on the Mac for the live game (the game there runs in a virtual display in the container).
- The browser, the window manager and the recorder themselves: they are the owner's, configured as `tasks.md` says.
