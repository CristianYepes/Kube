# Tasks 003 — The strip (record)

> v1.0, 2026-10-15. The tasks of v0.2 (V0-V9, the web view) are in the git history of this folder: the view was built on the
> Mac (V2-V6), measured against the owner's Linux (V1, 2026-10-11), rejected there and removed in S4. 🔑 = the owner did it.

- [x] **S1** — Probe on the owner's Linux (2026-10-11). A Tk window drew bitmap fonts; a GTK one (`agent/strip_demo.py`,
  commit `3e8a4f5`) stayed above the game with smooth text. The owner: "está bien".
- [x] **S2** — `kube-agent run --strip` (commit `acf6940`, 2026-10-12). Before the change its tests gave 22 failures and 26
  errors; after it, the whole agent suite passed (773 tests). 26 deliberate breaks were caught, each file restored identical
  (`cmp`). The probe of S1 was removed. The GTK window cannot run on the Mac (no GTK there), so its first real run was the
  owner's (S3).
- [x] 🔑 **S3** — The takes, on the owner's Linux (2026-10-12/13): the rule bot and Jev on seed 3 with `--strip`, recorded
  from the screen. The owner approved the look ("me gusta"). The Jev takes were paid (about $0.001 each [calc]). Their run
  folders, with their cost, stay on the owner's Linux and are not in `agent/runs/`, so `kube-agent spend` here does not
  count them.
- [x] **S4** — Remove the web view (2026-10-15): `kube-agent view`, its page, fonts, closing card and tests (13 files).
  `test_help_lists_exactly_the_subcommands` now fails on a leftover or a missing subcommand (seen failing both ways, the
  file restored identical). Agent suite: 582 passed.
