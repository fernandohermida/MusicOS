# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What MusicOS is

MusicOS is an agent-driven layer for organizing a real, physical music collection using [beets](https://beets.io/) as the underlying library engine. Beets is a runtime dependency only — installed from PyPI (`pipx install beets` or equivalent, see `docs/SETUP.md`), never vendored or forked into this repo. Every skill and script here shells out to the `beet` CLI; nothing in this repo `import`s beets as a Python library. There is no wiki, knowledge base, or markdown synthesis layer here — the thing being maintained is the actual collection: audio files on disk plus beets' SQLite-backed tag database. See `docs/ROADMAP.md` for what's intentionally not built yet.

Agent work happens through five Claude Code skills under `.claude/skills/`, each a thin orchestration layer over the stock `beet` CLI — no custom beets plugin code is part of this project. There is no `music-setup` skill; `BEETSDIR`/`config.yaml`/plugins/path layout are set up by hand once, following `docs/SETUP.md`, not through an agent-driven bootstrap step.

| Skill | Does |
|---|---|
| `music-ingest` | `beet import` only — bringing new music into the library. Nothing else. |
| `music-organize` | Fix on-disk placement (`beet move`), find duplicates/gaps (`beet duplicates`/`missing`/`unimported`), optional tag correction |
| `music-curate` | Album art (`fetchart`) and genre enrichment (`lastgenre`) — needs extra pip packages, deliberately excludes lyrics |
| `music-query` | Answer questions by running live `beet` queries/exports — no caching, no synthesis |
| `music-lint` | Health-check the library: placement drift, duplicates, incomplete albums, unmatched imports |

## Directory map

```
MusicOS/
├── .claude-plugin/  # plugin.json + marketplace.json — makes this repo an installable Claude Code plugin
├── .claude/skills/  # the five skills above (also auto-loads as project skills for anyone who clones this repo)
├── beetsdir/        # BEETSDIR: config.yaml, library.db, logs/, exports/ (set up by hand per docs/SETUP.md)
├── docs/            # SETUP.md, LIBRARY-LAYOUT.md, BEETS-CHEATSHEET.md, ROADMAP.md
├── scripts/         # library_snapshot.py — thin `beet export` wrapper (always `-l` for tracks) used by music-query;
│                    # build_wall.py — exports cover art + albums.js for the album wall
└── wall/            # index.html — static, dependency-free animated album-cover wall (covers/ + albums.js are generated, gitignored)
```

There is no `beets/` directory in this repo — beets is installed separately (see `docs/SETUP.md`), not vendored here. Docs that cite specific `beets` source file:line references (`docs/BEETS-CHEATSHEET.md`, `docs/LIBRARY-LAYOUT.md`) were verified against the beets version noted in `docs/SETUP.md` and may drift on later beets releases.

**The actual music files live outside MusicOS entirely**, in a folder the user designates via `directory:` in `beetsdir/config.yaml` (see `docs/SETUP.md`). That folder is organized into single-letter artist folders (`A/`, `B/`, ...) plus `#/`, `Various Artists/`, and `Soundtracks/`, using nothing but beets' own `paths:` config — no plugin — see `docs/LIBRARY-LAYOUT.md` for the exact scheme and rationale.

## Invariants

- **Never vendor or fork beets into this repo.** It's a separate, independently-maintained upstream project, depended on only as an installed CLI tool (see `docs/SETUP.md`).
- **No new beets plugin code.** All behavior comes from shelling out to the stock `beet` CLI (`import`, `move`, `export`, `modify`, `duplicates`, `missing`, `unimported`, etc.) plus the zero-extra-dependency plugins listed in `docs/BEETS-CHEATSHEET.md`.
- **`beet modify` writes audio file tags by default.** Any bookkeeping-only write must pass `-W` or it will rewrite files on disk.
- **Always preview before moving files.** `beet move --pretend` (or `beet import --pretend`) before the real command, every time — these operations touch the user's actual files.
- **The library is the source of truth.** No parallel notes/wiki/synthesis artifact exists to disagree with it.


## Where to look next

- Setting things up for the first time: `docs/SETUP.md`.
- The on-disk path scheme and why it works this way: `docs/LIBRARY-LAYOUT.md`.
- Verified `beet` query syntax, export formatting gotchas, and CLI recipes the skills rely on: `docs/BEETS-CHEATSHEET.md`.
- What's deliberately deferred (lyrics, auto-triggered organize): `docs/ROADMAP.md`.
