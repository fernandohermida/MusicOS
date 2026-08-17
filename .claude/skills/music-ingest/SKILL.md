---
name: music-ingest
description: Use when the user wants to bring new music files into the MusicOS library — importing a folder, a downloaded album, or a batch of ripped/purchased tracks. Not for reorganizing or fixing tags on music already in the library.
---

# music-ingest

## Overview

Wraps `beet import` — and only `beet import` — to bring new music into the library. Ingest never creates or edits any notes, pages, or synthesis output; its only write beyond the beets library itself is one line in the shared operational log recording the batch. Placing the new music into its correct on-disk letter/artist folder and checking for tag gaps is `music-organize`'s job, run as a follow-up.

## When to use

- User has new audio files (a downloaded album, a ripped CD, a purchased digital release) to add to the library.
- User asks to "import", "add", or "bring in" music.

Not for: `-L` retagging of music already in the library (that's enrichment — see `music-organize` / `docs/ROADMAP.md`'s `music-curate`), or anything involving external text/reviews/notes about the music (out of scope entirely for this project).

## Quick reference

| Step | Command |
|---|---|
| Preflight | confirm `BEETSDIR` set, `directory:` writable, source path has audio files |
| Dry run | `beet import --pretend <path>` |
| Batch stamp | `--set musicos_batch=<YYYYMMDD-HHMM>-<slug>` |
| Log capture | `-l beetsdir/logs/import-<batch>.log` |
| Unattended mode | `beet import -q --quiet-fallback skip <path>` |
| Post-import summary | `beet export -a -i id,album,albumartist,year,mb_albumid,albumtypes musicos_batch:<batch>` |

## Procedure

1. **Preflight.** Confirm `BEETSDIR` is set and `beetsdir/config.yaml` exists (if not, hand off to `music-setup` first). Confirm the source path exists and contains audio. Confirm `directory:` is writable.
2. **Dry run first, always.** Run `beet import --pretend <path>` and summarize what would be tagged/grouped for the user before anything real happens.
3. **Generate a batch id** — `<YYYYMMDD-HHMM>-<slug>` — and use it in both `--set musicos_batch=<batch>` (applied to the album and every item) and the log path `-l beetsdir/logs/import-<batch>.log`.
4. **Choose interactivity mode with the user:**
   - **Assisted (default):** compose the exact `beet import ...` command and have the user run it themselves in their own terminal — beets' match-selection prompt is an interactive TUI loop that doesn't reliably drive through a piped/non-TTY session. Resume once they report it's done.
   - **Unattended (opt-in, for bulk/low-stakes imports):** `beet import -q --quiet-fallback skip <path>` — strong matches apply automatically; anything ambiguous is skipped and recorded in the logfile for a later assisted pass. **Never** use `-q` with `quiet_fallback: asis` — that writes unverified metadata into the library.
5. **Summarize the result.** Run the post-import export scoped to `musicos_batch:<batch>` and report counts, new albums/artists, and specifically flag any album with an empty `mb_albumid` as needing a closer look (asis/unmatched import).
6. **Log and hand off.** Append one line to `beetsdir/logs/musicos-activity.log`: `<timestamp> ingest <batch> <n> albums, <n> flagged`. Suggest running `music-organize --batch <batch>` next.

## Common mistakes

- Trying to drive `beet import`'s interactive match-selection prompts directly through a non-interactive agent session instead of handing the command to the user's own terminal.
- Forgetting `--set musicos_batch=...`, which makes the follow-up `music-organize` pass unable to target exactly this import.
- Using `-q` without `--quiet-fallback skip`, silently accepting weak/asis matches.
- Doing any file reorganization or tag correction here — that's `music-organize`, not ingest.
