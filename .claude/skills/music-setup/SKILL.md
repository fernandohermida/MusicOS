---
name: music-setup
description: Use when there's no working beets install/config yet for MusicOS, when BEETSDIR or beetsdir/config.yaml is missing or broken, when beet commands fail with config/library errors, when the path layout needs to be created or changed before any files are moved, or when the user already has an existing beets library/config/database and wants to start using MusicOS's skills with it.
---

# music-setup

## Overview

Bootstraps and diagnoses the beets install that every other MusicOS skill depends on: `BEETSDIR`, `beetsdir/config.yaml`, the required plugins, and the `paths:` block that defines the on-disk folder layout (single-letter artist folders plus `#/`, `Various Artists/`, `Soundtracks/` — no plugin, see `docs/LIBRARY-LAYOUT.md`). This is the only skill useful before any music exists in the library, and the one to reach for whenever another skill fails because the environment isn't set up right.

Full step-by-step instructions for a human live in `docs/SETUP.md` — this skill is the agent-driven version of that same checklist, plus diagnosis.

## When to use

- First-time setup: nothing under `beetsdir/` exists yet.
- `beet version` fails, or any `beet` command errors with a config/library-not-found message.
- The user wants to change the folder scheme or path template before committing to a layout.
- Any other skill reports it can't find `BEETSDIR` or `beetsdir/config.yaml`.
- **The user already has an existing beets library** (their own `config.yaml`, `library.db`, already-organized music) and wants MusicOS's skills to work with it — this is a distinct path, see "Adopting an existing library" below. Do not treat this like a fresh install.

Not for: importing music (`music-ingest`), fixing an already-configured library's file placement (`music-organize`).

## Quick reference

| Step | Command | Purpose |
|---|---|---|
| Confirm BEETSDIR | `echo $env:BEETSDIR` (PowerShell) | Must point at `MusicOS/beetsdir` (fresh install) |
| Find existing config | `beet config --path` | Prints the active config.yaml's path — the key existing-library detection command |
| Inspect existing config | `beet config` | Dumps the fully-resolved effective config: plugins, `directory:`, `paths:`, everything |
| Sanity check | `beet version` | Confirms beets is installed and config loads |
| Preview layout | `beet move --pretend` | Shows every proposed file move — **run before ever moving real files** |
| List plugins | `beet version` (prints enabled plugins) | Confirms `export`, etc. are active |

## Procedure: fresh install (nothing exists yet)

1. **Check `BEETSDIR`.** If unset or pointing elsewhere, this must be fixed before anything else — see `docs/SETUP.md` for the Windows `setx` incantation. A fresh shell is required after setting it.
2. **Check `beetsdir/config.yaml` exists.** If not, copy `beetsdir/config.example.yaml` to `beetsdir/config.yaml` and walk the user through the choices it leaves open:
   - `directory:` — the external folder where music files will actually live (never inside `MusicOS/`).
   - `library:` — usually left as the default relative path, resolves to `beetsdir/library.db`.
   - `paths:` — already set up for single-letter artist folders plus `#/`/`Various Artists/`/`Soundtracks/` (see `docs/LIBRARY-LAYOUT.md`); confirm this matches what the user actually wants before moving on.
3. **Confirm `beet version` runs clean** and lists the plugins from `docs/BEETS-CHEATSHEET.md`'s zero-extra-dependency set, especially `export` — it's load-bearing for every other skill.
4. **Preview the layout with `beet move --pretend`** even on an empty/new library — this is cheap and confirms the `paths:` config produces sane-looking paths before any real music exists. Show the user the output.
5. **Only after the user confirms the preview looks right**, hand off: suggest `music-ingest` to bring in the first batch of music.

## Procedure: adopting an existing library

Full rationale lives in `docs/SETUP.md`'s "Adopting an existing beets library" section — this is the condensed, skill-driven version.

1. **Locate what already exists.** Run `beet config --path` to find the active config; run `beet config` to see the full effective configuration (existing `plugins:`, `directory:`, `paths:`). Do this before touching anything.
2. **Ask the user, don't assume, on two separate decisions:**
   - Leave `BEETSDIR` where it is (**recommended, default**) vs. relocate config+DB into `MusicOS/beetsdir/`. Relocating means copying (never moving) `config.yaml`/`library.db`/`state.pickle` into `MusicOS/beetsdir/`, backing up the originals first, then repointing `BEETSDIR` and re-verifying with `beet config --path` and `beet stats`.
   - Keep their existing `paths:` scheme (**default — no reason to change it**) vs. adopt MusicOS's `#`/letter/`Various Artists`/`Soundtracks` scheme. Only touch `paths:` if the user explicitly asks to switch.
3. **Add missing plugins by editing their existing `plugins:` line directly — append, never replace it, and never via a second `--config` overlay file.** Config layering in beets doesn't reliably merge list-valued keys like `plugins:` across multiple files, so an overlay file risks silently dropping whatever plugins the user already had enabled. The plugins MusicOS needs: `export`, `types`, `unimported`, `limit`, optionally `smartplaylist`.
4. **If (and only if) the user opted to adopt MusicOS's `paths:` scheme**, that's a real reorganization of an already-populated library: `beet move --pretend` first, review every proposed move with the user, only then `beet move` for real — identical discipline to any `music-organize` change.
5. **Never run `beet import`** on this library during adoption — the music is already imported; that step is exclusively for new music via `music-ingest`.

## Common mistakes

- Skipping the `--pretend` preview and only discovering a bad path template after files have already moved.
- Setting `BEETSDIR` in the current shell only, then running a *new* Claude Code session/terminal where it's unset again — always re-check, don't assume it persisted.
- Confusing `directory:` (where music lives) with `library:` (where the DB file lives) — mixing these up puts the database inside the music folder or vice versa.
- Treating "adopt an existing library" like a fresh install: copying `config.example.yaml` over an existing `config.yaml`, or running `beet import`/`beet move` without the user explicitly deciding to reorganize first.
- Adding MusicOS's required plugins via a separate `--config` overlay file instead of editing the existing `plugins:` line directly — risks silently dropping the user's other plugins.
