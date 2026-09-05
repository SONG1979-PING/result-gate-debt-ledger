# Result Gate + Debt Ledger

A pattern (and a small parser) for self-improving agents: **turn "self-improvement" from an internal loop into an auditable, user-visible ledger.**

> If your agent fixes itself but never reports back to a human, you don't have autonomy — you have a very tidy island.

## The problem this solves

An agent that self-heals will hit four failure modes, in order. Each one was
found in production, each one looks different, but they are the same disease:
**the completion criteria live entirely inside the agent's own call stack.**

| # | Failure mode | What it looked like | What it really was |
|---|---|---|---|
| 1 | No mechanism | Nobody reads the debt list at session start | Missing structure |
| 2 | Command rot | The ritual pinned one exact command; the command broke; the agent silently skipped reading | Success criteria pinned to a command, not a result |
| 3 | Stale read | Agent read a 40-min-old cache and reported it as current truth | Reads never verified freshness |
| 4 | Reported invisibly | Agent "reported" the debt — inside tool outputs the user can never see | "Report" was never defined as *user-visible* |

Fixes 1–3 are about **reading**. Fix 4 is about **delivery**. Most agent
systems die at 4: internally consistent, externally silent.

## The pattern

Three components:

1. **Debt ledger** (`debt-registry.md`) — a single markdown file, the agent's
   working checklist. P0/P1/P2 sections by severity; each debt is an entry
   with status. It is *not* an archive: the agent must read it before every
   session.
2. **Result gate** — the first action of every session must produce the active
   debt IDs (or "0 active debts"), **in the user-visible reply**. No pinned
   command: any working path counts (read cache, run parser, read source).
   A command error means *switch paths*, never skip.
3. **Freshness anchor** — every parsed snapshot carries the source file's
   mtime. Reading a snapshot means checking the anchor; if the source is
   newer than the snapshot, rebuild. A gate that passes on stale data is a
   failed gate.

## What you get here

- `debt_registry.py` — dependency-free parser. Markdown ledger in,
  `{p0_active, p1_active, p2_active, done_recent, source_mtime_epoch}` out.
  Plus `render_gate_report()` which renders the plain-text line an agent must
  put in front of a human.
- `example/debt-registry.md` — a sample ledger in the exact format contract.
- `test_debt_registry.py` — 12 tests, including the two bugs that ate us
  (MULTILINE regex flag; `open (...)` vs `open → done` status semantics).

## Quick start

```bash
python -c "from debt_registry import parse_debt_registry, render_gate_report; \
print(render_gate_report(parse_debt_registry('example/debt-registry.md')))"
```

Expected output:

```
p0_active: ['D-2026-09-05-014'] | p1_active: ['D-2026-09-05-003', ...] | p2_active: ...
```

```bash
python -m pytest test_debt_registry.py -q   # 12 passed
```

## Format contract

```markdown
## P0 — section title            ← grade comes from the section header
### D-YYYY-MM-DD-NNN — title     ← debt entry
- **状态**: open                 ← active iff 'open' or 'open (...)'
- **问题**: ...                  ← also recognized: 文件
```

Everything else is freeform. The parser is forgiving on prose and strict on
the two anchors above.

## Two rules that matter more than the code

Extracted from the ledger that produced this repo:

> **Bookkeeping is not exempt.** Deciding "this doesn't need a debt entry"
> requires an explicit written reason — and the reason may not be "it's in the
> logs" or "I'll notice next time".

> **Internal tests passing ≠ done.** Only externally observable results
> (a user's reply, a stranger's star, a decision actually used) may be marked
> done. Pure internal fixes stay "in-progress" until the outside world
> confirms.

## Provenance

Extracted from Hermes OPC, a production self-improving agent. Every design
decision in `debt_registry.py` is scar tissue from one of the four failures
above. License: MIT.
