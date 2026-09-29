---
name: music-organize
description: Use when placing newly ingested music into its letter/artist folder, or whenever files might be misplaced relative to the configured layout, tags look wrong, or the library might have duplicates or incomplete albums. Not for bringing new music in (that's music-ingest) and not for answering questions about the collection (that's music-query).
---

# music-organize

## Overview

Does the actual organizing work: moves files into their correct letter/artist/album folders (or `#/`, `Various Artists/`, `Soundtracks/` as appropriate), and sweeps for duplicates, incomplete albums, and unmatched imports. Acts directly on real files and the beets database — there is no markdown or notes output, only a summary to the user and one line in the shared operational log.

## When to use

- Right after `music-ingest` finishes a batch (the suggested next step).
- Files seem to be in the wrong letter/artist folder (e.g. after changing the `paths:` scheme).
- Suspected duplicates, incomplete albums, or albums that never got a good MusicBrainz match.

Not for: importing new music (`music-ingest`), answering questions without changing anything (`music-query`).

## Quick reference

| Step | Command | Purpose |
|---|---|---|
| Preview moves | `beet move --pretend [--batch <id> \| <query>]` | Shows misplaced files without touching them |
| Apply moves | `beet move [--batch <id> \| <query>]` | Physically relocates files to match current config |
| Duplicates | `beet duplicates` | Finds duplicate tracks/albums |
| Incomplete albums | `beet missing` | Finds albums missing tracks |
| Unmatched imports | `beet ls -- '^mb_albumid::.'` | Albums with no MusicBrainz match — needs `--` before a query starting with `^` |
| Resync tags | `beet mbsync [query]` | Re-fetches tags from MusicBrainz for matched items |

## Procedure

1. **Preview.** Run `beet move --pretend`, scoped to `--set musicos_batch:<batch>` if following up on a specific ingest, or a broader query (even unscoped) for a general tidy-up pass. Report every proposed move to the user.
2. **Confirm, then apply.** Only after the user agrees, run the same scope through `beet move` for real.
3. **Metadata-gap sweep:**
   - `beet duplicates` — report any hits, let the user decide what to do (don't auto-delete).
   - `beet missing` — report incomplete albums.
   - `beet ls -- '^mb_albumid::.'` — albums with no MusicBrainz match at all; these are the ones most likely to be misfiled or mistagged.
4. **Optional metadata correction** (only with explicit user confirmation per change, never silently): `beet mbsync <query>` to resync tags with MusicBrainz for a specific album, `beet edit <query>` for interactive bulk fixes, `beet modify -W <query> field=value` for a one-off correction (remember `-W`, or it rewrites the file's embedded tags too — which is usually fine here, since that's the point, but be deliberate about it), `beet scrub <query>` to strip extraneous junk tags (encoder tags, ripper comments) a file picked up before it entered the library — recommended on-demand only, not automatic; if `scrub.auto: yes` is set in a real `config.yaml`, that's worth flagging to the user as a tension with this project's always-preview invariant rather than assuming it's fine (see `docs/BEETS-CHEATSHEET.md`'s note).
   - For the "Unmatched imports" finding specifically: `beet mbsync` can't help, since it only resyncs items that already have a match — there's nothing for it to resync. The remediation is `beet import -L -t -- '^mb_albumid::.'`, run interactively so the user approves or skips each proposed MusicBrainz match one album at a time (see "Re-matching backlog imports" in `docs/BEETS-CHEATSHEET.md`). Same rule as everything else in this step: never run it unattended/quiet, and never treat it as something to batch-apply without the user watching.
5. **Log.** Append one summary line to `beetsdir/logs/musicos-activity.log`: what moved, what was flagged, what was fixed.

## Common mistakes

- Running `beet move` for real without a `--pretend` preview and user confirmation first — this moves actual files.
- Auto-resolving duplicates or auto-deleting anything `beet duplicates`/`beet missing` surfaces — these are for the user to decide, not to act on unilaterally.
- Forgetting the `--` separator before a query that starts with `^` or another shell-special character (`beet ls -- '^mb_albumid::.'`), which otherwise gets misparsed as an option.
- Trusting `beet move` for a case-only path change. The library drive is exFAT (case-insensitive): when a re-tag/`mbsync`/`import -L` changes only capitalization, beets updates the DB path but the on-disk name keeps its old case, and `beet unimported` then flags every file. After any such re-tag, check `beet unimported` and apply a case-only rename (via a temp name) to the DB spelling.
- Merging two album rows with `beet modify -W -M album_id=<target> album_id:<source>` — the album_id change did not persist in that form (2026-09-29, Justice ✝). The form that worked (KoL, same day) wrote tags: `beet modify -y album_id=<target> album=... mb_albumid=... album_id:<source>`.
