---
name: music-curate
description: Use when the user wants to fetch album art or normalize/fill in genre tags for albums already in the library — deeper metadata enrichment beyond what music-organize does. Not for lyrics (out of scope for this project) and not for basic tag resync (that's music-organize's mbsync step).
---

# music-curate

## Overview

Deeper metadata enrichment for albums already in the library, using beets plugins that need extra pip dependencies beyond the zero-dependency v1 set: `fetchart` (album art), `lastgenre` (genre normalization via Last.fm), and optionally `embedart` (embeds art into the file's own tags instead of a sibling `cover.jpg`). Deliberately excludes lyrics — not part of this project's scope. Kept as its own skill rather than folded into `music-organize` because these plugins need extras that aren't installed by default, and their behavior (network calls to art/genre sources) is different enough to want explicit, separate invocation.

**Check whether these already run automatically before assuming this skill is "turning enrichment on."** A real MusicOS library was found with `fetchart.auto: yes`, `lastgenre.auto: yes`, and `embedart.auto: yes` all set — meaning art/genre/embedding already fire on every `music-ingest` import, with no separate step needed. On a config like that, this skill's actual job is backfilling material imported *before* those settings existed, forcing a re-fetch/re-embed on specific albums, or genre cleanup — not initial enrichment. Always check `beet config` for the `auto:` value under each plugin before framing the work to the user as "let's go fetch this."

## When to use

- "Fetch album art for my library" / "find missing cover art."
- "Fill in / clean up genre tags" / "normalize genres."
- "Embed album art into the files" / art shows up in some players but not others (embedded vs. sibling-file art).
- An album is missing art or has no genre, and the user wants it filled in from an external source (Last.fm, cover art databases) rather than typed in manually.

Not for: lyrics (deliberately out of scope), basic tag resync from MusicBrainz (`music-organize`'s `mbsync` step), moving/renaming files (`music-organize`).

## Preflight: extras must be installed first

Unlike every other MusicOS skill, this one depends on plugins that need extra pip packages. Before doing anything:

1. Check whether `fetchart`/`lastgenre` (and `embedart`, if the user wants embedded art) are already in the enabled plugins list (`beet version` prints them, or read `beetsdir/config.yaml`), **and** whether each already has `auto: yes` (`beet config` shows the resolved settings) — that changes whether this skill's job is "enable enrichment" or "backfill/force-refresh" (see the Overview note above).
2. If a needed plugin isn't enabled, this is a one-time setup step, not something to silently fix: tell the user they need to reinstall beets with the extras, e.g. `pipx install --force "beets[fetchart,lastgenre,embedart]"` (drop `embedart` if they don't want it) (or the `pip`/`uv tool` equivalent for however they installed it — see `docs/SETUP.md`), then add the corresponding plugin names to the `plugins:` line in `beetsdir/config.yaml`.
3. Only proceed to the actual curation steps below once the relevant plugins show up in `beet version`'s enabled-plugins list.
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
| Embed art into file tags (opt-in) | `beet embedart <query>` | Needs the `embedart` extra; embeds whatever art `fetchart` already wrote (or a manually-placed `cover.jpg`) into the file itself |

## Procedure

1. Run the preflight check above. If extras aren't installed, stop and walk the user through installing them — don't attempt a workaround.
2. **Album art**: scope a query to what the user asked about (a specific artist/album, or the whole library). If `fetchart.auto: yes`, most of the library will already have art from import time — `beet fetchart <query>` without `-f` is then mainly useful for material imported before `fetchart` was enabled, or albums that had no match at import time; run it without `-f` regardless so existing art isn't needlessly re-fetched, and only add `-f` if the user explicitly wants art refreshed. Art is written as a `cover.jpg` file alongside the music files by default — it is **not embedded into the audio file tags** unless `embedart` is also enabled (auto or step 3 below).
3. **Embed art (skip if `embedart.auto: yes` already handles it; otherwise, only if the user asks and `embedart` is confirmed installed in preflight)**: run `beet embedart <query>` to embed the art `fetchart` already wrote (or a manually-placed `cover.jpg`) into the audio files' own tags — needed for players that don't read sibling image files. This rewrites the audio files themselves; treat it with the same care as any other bulk file-modifying step and confirm scope with the user first.
4. **Genres**: run `beet lastgenre <query>`, or `beet lastgenre -p <query>` first if the user wants to preview before committing. Note there's no CLI force flag for overwriting an existing genre tag — that's controlled by the `force` config option under `lastgenre:` in `beetsdir/config.yaml`, not a command-line switch. If the user wants to overwrite existing genres, confirm with them before changing that config setting, and confirm again before running the command with it on (this is a bulk tag-overwrite, treat it with the same care as any other bulk `music-organize` metadata change).
5. Report what was fetched/changed/embedded and what still has no art or genre, so the user knows what's left.

## Common mistakes

- Enabling `fetchart`/`lastgenre`/`embedart` in config before the corresponding pip extras are installed — beets won't start at all.
- Running `beet fetchart -f` or setting `lastgenre.force: yes` by default — both overwrite existing data; only do this when the user explicitly asks to refresh what's already there.
- Assuming album art gets embedded into file tags — by default it's a sibling `cover.jpg`, not embedded; embedding is the separate, opt-in `embedart` step.
- Treating this as the place for lyrics — that's explicitly out of scope for MusicOS.
- Trusting a "no genre found" result at face value without checking for a silent `SSL_CERT_FILE`/`BEETSDIR` env problem first (see preflight step 4) — an agent's non-interactive shell won't have sourced the user's profile exports.
- Expecting `beet fetchart -f` to improve a bad cover. With `-f` it skips the local `cover.jpg` and re-downloads from the first online source, and the Cover Art Archive image for the exact matched release is often a poor scan (photo of a regional edition). Check the result (`md5`/`sips`) against the old file. For a better image, download the release group's front (`https://coverartarchive.org/release-group/<rg-id>/front-1200`), view it, copy it over `cover.jpg`, and embed it with `beet embedart -y -f <cover.jpg> <query>`. Don't run `fetchart -f` again afterward; it would overwrite it.
