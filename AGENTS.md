@/Users/jayse/Code/blackrim/CLAUDE.md

# GridWars.run — Agent Guide

This file is read by Claude Code, Codex, OpenCode, and other AI agents at session start.
It extends the Blackrim crew framework (imported above) with project-specific lessons.

---

## Beads workflow

```bash
bd prime                    # Load full workflow context + commands
bd ready                    # Find available work
bd show <id>                # View issue details
bd update <id> --claim      # Claim work atomically
bd close <id>               # Complete work
```

Rules:
- Use `bd` for ALL task tracking — never TodoWrite, TaskCreate, or markdown TODO lists.
- Use `bd remember` for persistent knowledge — never MEMORY.md files.
- Run `bd prime` at session start to load context and essential commands.

---

## Session completion (mandatory)

Work is NOT done until `git push` succeeds.

1. File issues for remaining work.
2. Run quality gates if code changed: `make test`.
3. Update issue status — close finished, update in-progress.
4. Push:

```bash
git pull --rebase
bd dolt remote list 2>&1 | grep -q "No remotes" || bd dolt push
git push
git status   # MUST show "up to date with origin"
```

Critical rules:
- NEVER stop before pushing — that leaves work stranded locally.
- NEVER say "ready to push when you are" — the agent must push.
- If push fails, resolve and retry until it succeeds.

---

## GridWars.run project guidance

### Project layout

- `gridwars/` — Evennia game directory; **all game code lives here**. Subfolders: `commands/`, `typeclasses/`, `world/`, `web/`, `server/`.
- `vendor/evennia/` — Evennia v6.0.0 as a git submodule. **Read-only. Never modify.**
- `docs/` — operational docs: `SETUP.md` (run procedure), `CONVENTIONS.md` (SPDX header rule).
- `.github/workflows/test.yml` — CI; runs `make test` on push + PR.

### Run a dev server (contributors only)

> Players don't need this — connect to gridwars.run instead. The make targets below are for **contributors** running a local copy to test changes before opening a PR.

```bash
make install            # one-time venv + Evennia install
make migrate            # one-time DB init (non-interactive)
make createsuperuser    # interactive — creates your in-game #1 character
make run                # boot server (telnet localhost 4000, web localhost 4001)
make stop
make test               # Evennia test harness
```

`make migrate` is **non-interactive** — it runs `python -m django migrate`. The interactive
`evennia migrate` path prompts for superuser creation and will deadlock in CI. Never use it
in automation.

### Evennia v6 idioms (lessons paid for in debugging time)

**1. AttributeProperty — direct access is canonical; `.attributes.get()` returns `None`.**

`AttributeProperty`-backed fields are accessed directly on the object:

```python
c.integrity = 50     # correct
c.attributes.get("integrity")  # returns None — don't use this
```

We swept the codebase once; do not reintroduce the `.attributes.get()` pattern for
`AttributeProperty` fields.

**2. Settings paths are relative to the gamedir, not the repo root.**

```python
# Correct
BASE_CHARACTER_TYPECLASS = "typeclasses.characters.Character"

# Wrong — Evennia adds gridwars/ to sys.path
BASE_CHARACTER_TYPECLASS = "gridwars.typeclasses.characters.Character"
```

**3. `evennia batchcode` is an in-game command, not a shell CLI command.**

Run build scripts via Django shell instead:

```bash
cd gridwars && ../.venv/bin/python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.conf.settings')
django.setup()
from world import build_grid
build_grid.run()
"
```

**4. `START_LOCATION` is a stale dbref — override via `Account.create_character()`.**

We override character spawn in `gridwars/typeclasses/accounts.py` using
`search_tag("users_sector", "world_build")` so spawn is robust across world rebuilds.
Never hard-code a dbref for start location.

**5. `evennia --init <name>` creates `./<name>/` relative to cwd.**

Our `gridwars/` directory was generated from the repo root:

```bash
cd /path/to/gridwars.run
evennia --init gridwars
```

If you need to re-scaffold anything, run from repo root.

**6. Python 3.12+ required.**

Evennia v6.0.0 dropped Python 3.11. The default `python3` on macOS may be 3.11; the
venv uses `python3.12` explicitly. CI pins to 3.12. Always activate the venv before
running any game commands:

```bash
source .venv/bin/activate
```

### Character-deletion invariant

**Characters are never deleted.** Defeat sends a Character back to Users' Sector with
restored integrity via `reset_for_respawn()`. Any mechanic that "removes" a Character
must respawn / demote / debuff / exile — never call `.delete()` on a Character object.

Reference implementation: `gridwars/commands/combat.py`.

### Worktree discipline (Blackrim crew agents)

Agents spawn in `.claude/worktrees/agent-<id>/` and may only edit within their declared
`owned_paths`. The worktree guard at `~/.claude/hooks/worktree-guard.sh` enforces this.

- Use only repo-relative paths in Write/Edit calls (e.g. `docs/SETUP.md`, not `/Users/...`).
- Absolute paths bypass the worktree and silently land on the main working tree.
- After any non-trivial Write, read back or `ls -la` to confirm placement.

Trapped-Gestalt sessions (resuming inside a worktree) are identified via the SessionStart
hook (`record-gestalt-session.sh`) so the guard correctly allows Gestalt to escape.

### `/handoff` convention

When dispatching background agents, compose handoff docs in `/tmp/*handoff*.md`. These
paths are exempt from the Edit/Write delegation counter, so Gestalt can author them freely.
The handoff doc is the live-session global memory for the agent transition.
