# AICTE Obligation Engine (SIH PS 26262)

## Non-negotiables
- Real, running code only. No stubs, no TODO-as-implementation, no "would implement". If it's mocked, it's labelled MOCK in code and README.
- Every task is done only when its tests pass AND I ran it and saw it work. Paste the command output as evidence.
- Rules (routes, SLAs, escalation ladders) live in DB config rows, never in code.
- All scheduler logic reads `clock.now()`, never `datetime.now()`. Grep-enforced in CI.
- Audit log is written in the same DB transaction as the state change. Hash-chained.
- Decision stages are *suggested* actions needing an authorised click. Only mechanical stages auto-advance.
- Region scoping enforced server-side in the query layer, not the UI.
- Numbers in docs/UI are prototype results on synthetic data, with n stated. No inflated claims.

## Loop (every task)
1. Read TASKS.md, pick the top unchecked task.
2. Write the failing test first.
3. Implement minimal code.
4. Run: `make check` (lint + typecheck + tests). Fix until green.
5. Run the feature for real (curl/UI/script). Capture output.
6. Update TASKS.md (check box + one-line evidence) and docs if behavior changed.
7. Commit: `type(scope): msg`. One task = one commit.
8. If blocked >2 attempts on the same error, write it in BLOCKERS.md with what you tried, then move on.

## Code standards
- Python 3.12, FastAPI, SQLAlchemy 2 + Alembic, Pydantic v2, ruff + mypy strict on `app/`.
- Functions small, typed, no dead code, no commented-out code, no god files (>300 lines = split).
- No broad `except:`. Errors typed, logged with context, surfaced with correct HTTP codes.
- Config via env (pydantic-settings). No secrets in repo.

## UI standards
- Minimal: one neutral palette + one accent, 4/8px spacing scale, system font stack or Inter, max 2 weights.
- No gradients, glassmorphism, emoji icons, giant shadows, centered-everything hero layouts, or card-in-card-in-card.
- Tables dense and scannable. Status = small text badge, not a rainbow.
- Every screen has loading, empty, and error states.