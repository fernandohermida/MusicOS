---
name: music-query
description: Use when the user asks a question about their music collection — what they have, counts, gaps, recently added music, or anything answerable by looking at the library. Read-only — never moves files or changes tags.
---

# music-query

## Overview

Answers questions about the collection by running live `beet` commands directly — no cache, no pre-built synthesis layer to consult. Every answer should be traceable back to an actual command.

## When to use

- "Do I have...", "how many...", "list all...", "what did I add recently", "what's my longest album" — any factual question about the library.

Not for: changing anything (`music-organize`), bringing in new music (`music-ingest`), health/consistency checks the user didn't explicitly ask about (`music-lint`, though a query answer may surface a lint-worthy issue in passing).

## Quick reference

| Need | Command |
|---|---|
| Human-readable listing | `beet ls <query>` / `beet ls -a <query>` (albums) |
| Structured data to parse | `python3 scripts/library_snapshot.py [--items] [--fields k1,k2] [--query <query>]` — albums by default; wraps `beet export -f json`, always adds `-l` for tracks, and splits multi-value fields into real JSON lists |
| Raw export (if the script doesn't fit) | Tracks: `beet export -l -f json -i <keys> <query>` — **`-l` is mandatory**. Albums: `beet export -a -f json -i <keys> <query>` |
| Aggregate counts/sizes | `beet stats <query>` |
| Recently added | `beet ls -a 'added:-1w..'` (or any relative range) |
| Field discovery | `beet fields` — lists every known field name including flex attributes in use |

## Procedure

1. **Translate the question into a `beet` query.** See `docs/BEETS-CHEATSHEET.md` for verified syntax: `field:value` substring, `field:=value` exact, `field::regex`, ranges (`year:1990..1999`), relative dates (`added:-1w..`), sort suffixes (`year+`), negation (`^`/`-`), OR via spaced comma (`id:1 , id:2`).
2. **For anything you're going to parse or compute over, use `scripts/library_snapshot.py`** (or a raw `beet export -l -f json`) — `beet list -f '$a $b'` has no escaping and breaks on values containing spaces. Use `-f` text output only for direct human display. The whole library exports in seconds (~15k tracks), so export once and compute locally rather than running many small queries.
3. **Run it, read the output, answer directly.** Don't guess at library contents — if a fact isn't confirmed by a command you ran, don't state it as fact.
4. **Always cite** the command(s) run, so the answer is auditable.
5. If a question can't be answered from the library as-is (e.g. it needs an external fact), say so plainly rather than fabricating a data point.

## Common mistakes

- Parsing `beet list -f '$a $b'` output for multi-value or space-containing fields instead of switching to `beet export -f json`.
- Answering from assumption/memory of a previous query instead of re-running one — the library can change between turns.
- Forgetting that multi-value export fields (`genres`, `mb_albumartistids`, etc.) come out `"; "`-joined, not as JSON arrays — split on `"; "` before treating them as a list (`library_snapshot.py` already does this).
- **Running a raw track export without `-l`.** `beet export -f json` (no `-a`, no `-l`) reads tags off disk file-by-file: an empty query silently returns `[]`, and a real query over thousands of tracks takes many minutes. See `docs/BEETS-CHEATSHEET.md`'s "Structured output" section.
- **Exporting `genre` (singular).** Since beets 2.14 genre data lives only in the multi-value `genres` field; `-i genre` comes back as an empty string for every track, which looks like "nothing has a genre." Export `genres`. (Queries like `genre:jazz` still match, so this only bites exports.)
