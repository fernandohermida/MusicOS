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
| Structured data to parse | `beet export -f json [-a] -i <keys> <query>` |
| Aggregate counts/sizes | `beet stats <query>` |
| Recently added | `beet ls -a 'added:-1w..'` (or any relative range) |
| Field discovery | `beet fields` — lists every known field name including flex attributes in use |

## Procedure

1. **Translate the question into a `beet` query.** See `docs/BEETS-CHEATSHEET.md` for verified syntax: `field:value` substring, `field:=value` exact, `field::regex`, ranges (`year:1990..1999`), relative dates (`added:-1w..`), sort suffixes (`year+`), negation (`^`/`-`), OR via spaced comma (`id:1 , id:2`).
2. **Prefer `beet export -f json`** for anything you're going to parse or compute over — `beet list -f '$a $b'` has no escaping and breaks on values containing spaces. Use `-f` text output only for direct human display.
3. **Run it, read the output, answer directly.** Don't guess at library contents — if a fact isn't confirmed by a command you ran, don't state it as fact.
4. **Always cite** the command(s) run, so the answer is auditable.
5. If a question can't be answered from the library as-is (e.g. it needs an external fact), say so plainly rather than fabricating a data point.

## Common mistakes

- Parsing `beet list -f '$a $b'` output for multi-value or space-containing fields instead of switching to `beet export -f json`.
- Answering from assumption/memory of a previous query instead of re-running one — the library can change between turns.
- Forgetting that multi-value export fields (`genres`, `mb_albumartistids`, etc.) come out `"; "`-joined, not as JSON arrays — split on `"; "` before treating them as a list.
