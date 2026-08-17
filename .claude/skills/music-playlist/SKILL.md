---
name: music-playlist
description: Use when the user wants to create or update .m3u playlists generated from saved queries against the library — e.g. "make a playlist of everything tagged jazz" or "regenerate my playlists." Not for one-off ad-hoc listening questions with no lasting playlist (that's music-query).
---

# music-playlist

## Overview

Generates and regenerates `.m3u` playlist files from saved beets queries, using the `smartplaylist` plugin — zero extra pip dependencies, already safe to enable by default. A playlist here is a named query (e.g. "everything tagged `genre:jazz`") that gets re-materialized into an `.m3u` file whenever asked, rather than a one-off answer that disappears into chat history.

## When to use

- "Make me a playlist of X" where X is expressible as a beets query (genre, artist, year range, flexible attribute, etc.).
- "Regenerate my playlists" after the library has changed (new imports, tag fixes).
- Not for a one-off "what should I listen to" question with no lasting artifact — that's `music-query`.

## Quick reference

| Need | Command / config |
|---|---|
| Define a playlist | Add an entry under `smartplaylist.playlists` in `beetsdir/config.yaml` |
| Regenerate all playlists | `beet splupdate` |
| Regenerate one playlist | `beet splupdate <PlaylistName>.m3u` |
| Preview without writing | `beet splupdate --pretend` |
| See which tracks matched (debug) | `beet -v splupdate` |

## Config shape

```yaml
smartplaylist:
  auto: no          # MusicOS keeps this off — regenerate explicitly via this skill, not silently on every DB change
  playlist_dir: <somewhere the user's music player can see>
  relative_to: <directory:, so paths in the .m3u work from the player's perspective>
  playlists:
    - name: 'Jazz.m3u'
      query: 'genre:jazz'
    - name: 'Recently Added.m3u'
      query: "added:-1w.."
```

`query` matches tracks/items; an optional `album_query` matches whole albums instead. `auto: yes` (the plugin's own default) regenerates every playlist after every database change — MusicOS turns this off deliberately so playlist generation stays an explicit, skill-driven action instead of a silent side effect of unrelated commands, consistent with how every other MusicOS operation works.

## Procedure

1. **New playlist request**: help the user express what they want as a beets query (reuse `music-query`'s query-building know-how and `docs/BEETS-CHEATSHEET.md`'s syntax table), add a `name`/`query` (or `album_query`) entry under `smartplaylist.playlists` in `beetsdir/config.yaml`, confirm the entry with the user before writing it.
2. **Generate/update**: run `beet splupdate` (all playlists) or `beet splupdate <name>.m3u` (just the one that changed) — this is a config-driven, non-destructive operation (it only writes `.m3u` files, never touches the library or audio files).
3. Report which playlists were written and how many tracks matched each; if a playlist matched zero tracks, flag it — the query is probably wrong (typo, no matching tags yet), not silently "an empty playlist is fine."

## Common mistakes

- Turning `smartplaylist.auto` on — this means every unrelated `beet` command potentially regenerates every playlist in the background, which is surprising and slow at scale; keep it explicit via this skill.
- Forgetting `relative_to` — if it doesn't match wherever the user's music player expects paths from, the generated `.m3u` won't resolve correctly even though `beet splupdate` reports success.
- Treating a zero-match playlist as normal — it almost always means the query needs fixing.
