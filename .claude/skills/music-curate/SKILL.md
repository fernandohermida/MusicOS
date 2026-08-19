---
name: music-curate
description: Use when the user wants to fetch album art or normalize/fill in genre tags for albums already in the library — deeper metadata enrichment beyond what music-organize does. Not for lyrics (out of scope for this project) and not for basic tag resync (that's music-organize's mbsync step).
---

# music-curate

## Overview

Deeper metadata enrichment for albums already in the library, using two beets plugins that need extra pip dependencies beyond the zero-dependency v1 set: `fetchart` (album art) and `lastgenre` (genre normalization via Last.fm). Deliberately excludes lyrics — not part of this project's scope. Kept as its own skill rather than folded into `music-organize` because these plugins need extras that aren't installed by default, and their behavior (network calls to art/genre sources) is different enough to want explicit, separate invocation.

## When to use

- "Fetch album art for my library" / "find missing cover art."
- "Fill in / clean up genre tags" / "normalize genres."
- An album is missing art or has no genre, and the user wants it filled in from an external source (Last.fm, cover art databases) rather than typed in manually.

Not for: lyrics (deliberately out of scope), basic tag resync from MusicBrainz (`music-organize`'s `mbsync` step), moving/renaming files (`music-organize`).

## Preflight: extras must be installed first

Unlike every other MusicOS skill, this one depends on plugins that need extra pip packages. Before doing anything:

1. Check whether `fetchart`/`lastgenre` are already in the enabled plugins list (`beet version` prints them, or read `beetsdir/config.yaml`).
2. If not, this is a one-time setup step, not something to silently fix: tell the user they need to reinstall beets with the extras, e.g. `pipx install --force "beets[fetchart,lastgenre]"` (or the `pip`/`uv tool` equivalent for however they installed it — see `docs/SETUP.md`), then add `fetchart lastgenre` to the `plugins:` line in `beetsdir/config.yaml`.
3. Only proceed to the actual curation steps below once both plugins show up in `beet version`'s enabled-plugins list.
4. **If invoking `beet` from a non-interactive shell (this is the normal case for an agent's Bash tool)**, don't trust that `~/.bash_profile`/`~/.bashrc`/`~/.zshrc` exports actually reached the process — those files aren't sourced by non-login/non-interactive shells at all. Confirm `beet version`'s `data directory:`/library path (add `-vv`) actually matches this repo's `beetsdir/`, not some other cached `BEETSDIR`. If it's a manual venv install, also confirm `beet -vv lastgenre <query>` isn't logging `CERTIFICATE_VERIFY_FAILED` (macOS Python-framework builds need `SSL_CERT_FILE` pointed at the venv's `certifi` bundle) — that failure mode is silent otherwise and looks identical to "no genre found." See `docs/SETUP.md`'s "Non-interactive/non-login shells" note for the fix; pass `BEETSDIR=...`/`SSL_CERT_FILE=...` inline per command rather than assuming a profile export applies.

Don't add these plugins to the base config for someone who hasn't installed the extras — beets will fail to start entirely if a listed plugin's dependency is missing.

## Quick reference

| Need | Command | Notes |
|---|---|---|
| Fetch missing album art | `beet fetchart <query>` | Skips albums that already have art |
| Re-fetch art even if present | `beet fetchart -f <query>` | `-f`/`--force` |
| Quiet output (only fetched/not-found) | `beet fetchart -q <query>` | |
| Fill in missing genres | `beet lastgenre <query>` | Album-level by default |
| Genres per-track instead of per-album | `beet lastgenre -A <query>` | |
| Preview genre changes | `beet lastgenre -p <query>` | `-p`/`--pretend` |

## Procedure

1. Run the preflight check above. If extras aren't installed, stop and walk the user through installing them — don't attempt a workaround.
2. **Album art**: scope a query to what the user asked about (a specific artist/album, or the whole library). Run `beet fetchart <query>` first without `-f` so existing art isn't needlessly re-fetched; only add `-f` if the user explicitly wants art refreshed. Art is written as a `cover.jpg` file alongside the music files by default — it is **not embedded into the audio file tags** (that would need the separate `embedart` plugin, which also needs Pillow — out of scope here, see `docs/ROADMAP.md`).
3. **Genres**: run `beet lastgenre <query>`, or `beet lastgenre -p <query>` first if the user wants to preview before committing. Note there's no CLI force flag for overwriting an existing genre tag — that's controlled by the `force` config option under `lastgenre:` in `beetsdir/config.yaml`, not a command-line switch. If the user wants to overwrite existing genres, confirm with them before changing that config setting, and confirm again before running the command with it on (this is a bulk tag-overwrite, treat it with the same care as any other bulk `music-organize` metadata change).
4. Report what was fetched/changed and what still has no art or genre, so the user knows what's left.

## Common mistakes

- Enabling `fetchart`/`lastgenre` in config before the corresponding pip extras are installed — beets won't start at all.
- Running `beet fetchart -f` or setting `lastgenre.force: yes` by default — both overwrite existing data; only do this when the user explicitly asks to refresh what's already there.
- Assuming album art gets embedded into file tags — by default it's a sibling `cover.jpg`, not embedded.
- Treating this as the place for lyrics — that's explicitly out of scope for MusicOS.
- Trusting a "no genre found" result at face value without checking for a silent `SSL_CERT_FILE`/`BEETSDIR` env problem first (see preflight step 4) — an agent's non-interactive shell won't have sourced the user's profile exports.
