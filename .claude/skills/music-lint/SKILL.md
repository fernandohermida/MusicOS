---
name: music-lint
description: Use when doing a periodic health check of the MusicOS library, or after a big organize pass, to surface misplaced files, duplicates, incomplete albums, unimported files, or albums that never matched MusicBrainz. Read-only by default; only the guarded --fix path touches anything.
---

# music-lint

## Overview

Runs the full set of library-hygiene checks beets already ships with, reports the results, and updates `beetsdir/logs/last-health-report.md` (overwritten each run) plus one line in the shared operational log. Every check here is a stock beets command or a zero-extra-dependency plugin — nothing that writes to files or tags.

## When to use

- Periodic health check ("how healthy is my library", "check for problems").
- Before/after a big `music-organize` pass, to confirm nothing's left in a bad state.
- The user changed the folder scheme or path template and wants to confirm nothing's now misplaced.

Not for: fixing what it finds — report only, unless `--fix` is explicitly requested, and even then only mechanical fixes apply automatically.

## Quick reference

| Check | Command | Catches |
|---|---|---|
| Placement drift | `beet move --pretend` | Files whose path no longer matches the configured `paths:` template |
| Duplicates | `beet duplicates` | Duplicate tracks/albums |
| Incomplete albums | `beet missing` | Albums missing tracks |
| Unimported files | `beet unimported` | Files under `directory:` not in the DB at all |
| Singletons | `beet ls singleton:true` | Tracks with no associated album |
| Unmatched imports | `beet ls -- '^mb_albumid::.'` | Albums that never got a confident MusicBrainz match |

## Procedure

1. Run every check in the table above. None of them modify anything.
2. Summarize findings by category, with counts and a few concrete examples per category (not just totals).
3. Write the full report to `beetsdir/logs/last-health-report.md`, overwriting the previous run.
4. Append one line to `beetsdir/logs/musicos-activity.log`: `<timestamp> lint <n> issues across <n> categories`.
5. **`--fix` (only if explicitly requested):** apply only the mechanical, unambiguous fix — running `beet move` for the placement-drift findings from step 1 (i.e., delegate to `music-organize`'s move step). Duplicates, incomplete albums, and unmatched imports always require the user's judgment; never auto-resolve them.

## Common mistakes

- Treating `beet duplicates`/`beet missing`/unmatched-import findings as something to silently resolve — they're for the user to decide on.
- Running `--fix` without having shown the `beet move --pretend` output first.
- Letting `last-health-report.md` accumulate as history instead of overwriting it — it's a current-state snapshot, not a log (the operational log already covers history).
