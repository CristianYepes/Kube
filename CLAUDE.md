# Kube (cub3D) — instructions for Claude

**Talk to the owner (Cristian) in Spanish. Everything written to disk is in English:** code,
comments, docs and commit messages.

This branch, `feature/jev-agentv1`, implements **spec 002: Jev (TypeSafe AI's decision model)
plays the zombie mode of `cub3D_bonus`**, like TypeSafe's Doom demo. The handoff is imported
below. Follow it, then work through `specs/002-jev-agent/tasks.md` in order, ticking each task.
The project overview is `specs/CONTEXT.md`.

## The owner's working rules (from earlier sessions; they apply here)

- **Verify, don't recall.** APIs, versions, paths and prices are checked with a command, the
  repo or official docs. A number you computed is a claim, not a measurement. A result that
  cannot be true means a broken instrument. A zero proves nothing until the check has been
  seen to find something.
- **Aggressive YAGNI:**
  - no placeholder typedefs or headers;
  - no constants before their first use;
  - no directories before their first file;
  - fixtures live in the commit of the test that uses them.
- **The simplest thing that works.** Size the answer to the question.
- **Ask before anything irreversible:** deleting, overwriting, force-pushing, pushing.
  **Never push unless the owner asks.** One commit per task.
- **Secrets:** the OpenRouter key lives in `~/jev/libros/.env` on the owner's machines. It is
  never printed, logged, committed, or passed to Docker.
- **Report what actually happened,** with numbers. "It should work" and "it works" are two
  different claims. If a result is bad, say so plainly.

@specs/002-jev-agent/START_HERE.md
