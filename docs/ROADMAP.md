# Roadmap: deliberately deferred

Everything below is out of scope for v1, on purpose. Listed here so the reasoning doesn't get lost, and so future work doesn't quietly re-litigate decisions already made.

## Lyrics

`music-curate` covers album art (`fetchart`) and genre normalization (`lastgenre`) but deliberately excludes the `lyrics` plugin. Lyrics fetching/storage raises separate questions (licensing of fetched lyrics text, where/how to store it, whether it belongs in file tags at all) that haven't been worked through — left out until there's a reason to.

## `--research` mode for deeper query answers

Web-lookup-backed answers (beyond what's in the library/MusicBrainz) were considered and explicitly rejected for this project's scope — see the "not a wiki" framing in `CLAUDE.md`. If ever reconsidered, it would need to stay clearly separated from library facts, not blended into `music-query`'s output.

## Auto-triggered organize on import

Beets has a plugin event system (`item_imported`/`album_imported`/`cli_exit`, or the zero-code `hook` plugin — see `beets/plugins.py` in the beets source) that could auto-run `music-organize`-equivalent logic every time `beet import` runs, without an explicit skill invocation. Deferred because it requires either new plugin code or the `hook` plugin wired to a script — a step up in complexity from "Claude skills shelling out to stock `beet`," which is the deliberate v1 constraint (see `CLAUDE.md`'s invariants). Revisit only if explicit skill invocation becomes friction in practice.

## Playlists

A `music-playlist` skill (`.m3u` generation from saved queries via the `smartplaylist` plugin) existed briefly and was removed: `smartplaylist` was never enabled on the real library, so the skill couldn't run. If playlists come back, re-add `smartplaylist` to `plugins:` with `auto: no` (keep generation an explicit action) and a `relative_to:` that matches the music player's path expectations.
