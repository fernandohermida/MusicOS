# beets cheatsheet

Verified query syntax and CLI recipes the skills rely on, plus the gotchas that will bite you if ignored. Everything here was checked against beets' source at the version noted in `docs/SETUP.md`, not assumed — file:line references point at that source and may drift on later beets releases. MusicOS doesn't vendor beets' source itself (see `docs/SETUP.md`); these citations are for verification, not navigation within this repo.

## Query syntax (`beets/docs/reference/query.rst`)

| Form | Meaning |
|---|---|
| `field:value` | Substring match |
| `field:=value` | Exact match, case-sensitive |
| `field:=~value` | Exact match, case-insensitive |
| `field::regex` | Regex match (extra colon) |
| `:regex` | Regex match across all fields |
| `field:min..max` | Numeric/date range, either side optional |
| `added:-1w..` | Relative date range (e.g. "added in the last week") |
| `year:1990..1999` | Numeric range |
| `-field:value` / `^field:value` | Negation |
| `field+` / `field-` | Sort ascending/descending by field, chainable |
| `id:1 , id:2` | OR — note the **spaced comma**; `id:1,id:2` (no spaces) is parsed as one keyword, not two |
| `path:...` | Match by file path |

Always put `--` before a query that starts with a shell-special character (e.g. `^`), or the shell/option-parser will misinterpret it: `beet ls -- '^mb_albumid::.'`.

## Path-format query keys (`docs/reference/config.rst`)

Any key in the `paths:` config section other than `default` is parsed as a beets **query**, not a template — `comp` and `singleton` are recognized directly, and anything else (e.g. `albumtype:soundtrack`) is an ordinary query string like the ones above, including regex (`field::regex`). Confirmed straight from beets' own docs: "queries are tested in the order they appear in the configuration file... beets will use the path format for the first matching query" — `default` is always the fallback, evaluated last regardless of its position. This is the mechanism `docs/LIBRARY-LAYOUT.md`'s on-disk scheme relies on instead of a plugin.

**`%if` in path *templates* has no comparison/regex support** — it only tests whether a string is empty/`"0"`/`"false"`. Anything that needs a character-class or pattern test (e.g. "does this artist name start with a digit?") has to be expressed as a query-based path *key*, not inside a template.

## Structured output: `beet export` over `beet list -f`

`beet export` (`beetsplug/export.py` in the beets source) is the reliable path for anything you're going to parse:

```
beet export [-l | -a] [-i key1,key2,...] [-f json|jsonlines|csv|xml] [-o file] [query...]
```

- `-a` for albums, default is items/tracks.
- `-i` restricts to specific fields (cheaper, cleaner output).
- `-f json` is the default recommendation for agent parsing.
- **Always pass `-l`/`--library` for item exports too** (`-a` already implies it for albums). Without it, `beet export` reads tags straight off disk per matched file (`beetsplug/info.py`'s `tag_data`) instead of the DB (`library_data`) — confirmed against a real ~16k-track library: an empty query silently returns `[]` (the `tag_data` code path only queries the library at all `if query:` — empty args skip it entirely), and a real query matching thousands of items takes minutes instead of seconds, since every match gets its audio file individually opened and parsed. `scripts/library_snapshot.py`'s `run_export` always adds `-l` for the non-album case for exactly this reason — don't build a raw `beet export` call for items without it.

`beet list -f '$field1 $field2' <query>` also works for quick human-readable text, but has **no escaping** — a field value containing a space breaks naive whitespace-splitting. Don't parse `-f` text output programmatically; use `export` instead.

### Export formatting gotchas (verified against `beets/dbcore/types.py` in the beets source)

- **Dates** (`added`, `mtime`) format as local-time strings via `strftime`, not epoch — timezone/format can vary by machine and by the `time_format` config. Pin `time_format` in config for consistent parsing (see `docs/SETUP.md`).
- **Booleans** (`comp`) format as the literal strings `"True"`/`"False"`, not JSON booleans.
- **Multi-value fields** (`genres`, `albumartists`, `mb_albumartistids`, `albumtypes`, `artists`) are `"; "`-joined single strings, **not** JSON arrays. Split on `"; "` before treating as a list.
- **`genre` (singular) is gone as a stored field since beets 2.14** — `beet fields` lists only `genres`. `beet export -i genre` returns `""` for every record (it looks like nothing is tagged), while `-i genres` carries the real data. Query syntax still accepts `genre:jazz` (same results as `genres:jazz`), so only exports are affected.
- **`length`** formats as `"M:SS"` unless `format_raw_length: yes` is set (recommended in `docs/SETUP.md` for machine-readable exports).

### Custom computed fields (via `inline`)

Beyond `$initial`/`$multidisc` (used in `paths:`, see `docs/LIBRARY-LAYOUT.md`), a config can define `album_fields`/`item_fields` for query/display purposes with no path role at all. Example confirmed on a real library: an `album_fields.quality` field returning `[FLAC 16-44]`, `[MP3 320]`, or `[MUTT]` (mixed formats in one album) — usable in `music-query` answers (`beet ls -f '$album ($quality)'`) or as a query filter. Check `beet fields` on the active config before assuming only the fields listed in this doc exist; a real config may define more.

## Zero-extra-dependency plugins usable in v1

Checked against the installed beets package's `Provides-Extra` metadata (`python3 -c "import importlib.metadata as m; print(m.metadata('beets').get_all('Provides-Extra'))"`) — none of these require an extra:

`export`, `info`, `types`, `missing`, `duplicates`, `unimported`, `mbsync`, `fromfilename`, `inline`, `edit`, `hook`, `ftintitle`, `substitute`.

`edit`, `fromfilename`, `ftintitle`, `scrub`, and `info` are confirmed not just zero-dependency in theory but actually enabled and running, verified against a real `beet version` output on a live 15k-track library (see "What's actually running" below). `hook` remains deliberately unused — it's the exact auto-organize-on-import mechanism `docs/ROADMAP.md` defers. `substitute` and `importadded` are plausible additions (same zero-dependency class as the others) but are **unverified speculation** — neither has been run against a real beets install; treat them as candidates to test, not confirmed-safe recommendations, until someone actually enables and checks them.

One with a caveat worth knowing before assuming "zero-dependency" means "zero setup":
- **`convert`** — no pip extra at all, but needs the external `ffmpeg` binary on `PATH` (not installed by beets or MusicOS).

Anything else needs reinstalling beets with the relevant pip extra (e.g. `pipx install --force "beets[fetchart,lastgenre]"`). `fetchart`, `lastgenre`, and `embedart` are used by `music-curate`; `lyrics` and `titlecase` aren't used by any MusicOS skill (`lyrics` deliberately excluded, see `docs/ROADMAP.md`). `chroma` is enabled on at least one real MusicOS library (see below) but has no dedicated skill orchestrating it — it works automatically alongside `musicbrainz` once configured. `replaygain` and `badfiles` are documented as candidate opt-in extras below. `discogs` is a special case — see "Autotagger sources: MusicBrainz only" below before enabling it.

## What's actually running (verified against a real library)

There is no packaged `config.example.yaml` template in this repo currently (see `docs/SETUP.md`'s note on building `config.yaml` by hand). The plugin/config choices below are transcribed from a real, working `beetsdir/config.yaml` against a 15,002-track / 95.2 GiB library (1,157 albums, 457 album artists; `beet stats -e`, 2026-09-28), cross-checked with `beet version`'s actual enabled-plugins output — treat this as the reference "what a mature MusicOS config looks like," not an aspirational list:

`beet version` plugins: `musicbrainz fetchart embedart lastgenre duplicates missing convert scrub ftintitle inline fromfilename mbsync info edit export types unimported chroma`. (`limit` used to be in this list; it was dropped after beets 2.14 deprecated it — use `beet ls -l <number>` instead.)

- **`fetchart`/`lastgenre`/`embedart` all run with `auto: yes`** — they fire automatically during `beet import`, not just on manual invocation. `music-curate` is mainly for backfilling material imported before these were configured, forcing a re-fetch, or normalizing genres on demand — not "turning enrichment on" (it's already on).
- **`chroma`** (acoustic fingerprinting, needs `acoustid.apikey` + the external `fpcalc` binary — confirmed present at `/usr/local/bin/fpcalc` on this setup) augments MusicBrainz matching with audio-fingerprint-based candidates. Unlike `discogs` (below), it still resolves to MusicBrainz IDs, so it doesn't carry the same `mbsync`-breaking risk.
- **`scrub`** — this real config currently runs `scrub.auto: yes` (strips extraneous tags on every write). MusicOS's documented recommendation is the opposite: `scrub` enabled but **not** auto — see the "Commands the skills rely on" table below for the on-demand `beet scrub <query>` form, which is the model to follow for new setups. If you have `scrub.auto: yes` in a real config, decide deliberately whether to keep it — auto-stripping on every write is in tension with this project's always-preview invariant, even though it's been running that way without apparent issue.

## Autotagger sources: MusicBrainz only

**Do not add a second autotagger source (`discogs`, `deezer`, `spotify`, etc.) to `plugins:` unless you've thought through the `mbsync` interaction.** A real MusicOS config was found with a fully configured `discogs.user_token` but `discogs` deliberately left *out* of `plugins:`, with this reasoning written directly in the config: a second autotagger source can win a match and write a non-MusicBrainz ID into `mb_albumid`, which breaks `mbsync` (which assumes a MusicBrainz ID). If MusicBrainz coverage gaps are a real problem for a given collection (plausible for deep-catalog/regional releases), that's a legitimate reason to reconsider — but it's a deliberate tradeoff to make with the user, not a default "add more autotagger sources" recommendation.

## Other candidate plugins (not yet adopted anywhere)

Not part of any real MusicOS library's config yet — genuine gaps/enhancements worth considering, not verified beyond "the plugin exists and does this":

| Plugin | Needs | What it's for |
|---|---|---|
| `replaygain` | An audio analysis backend on `PATH` — `ffmpeg`, `gstreamer`, or the `bs1770gain` binary (beets supports any of the three; pick one) | Volume/loudness normalization across an eclectic collection where masters vary wildly (quiet acoustic jazz vs. loud modern hip-hop/electronic). No MusicOS skill calls it yet — would need a home (likely `music-curate`, as a third enrichment step) before it's more than "installed." |
| `badfiles` | External `mp3val` binary for MP3 integrity checks; FLAC checks reuse the `flac` binary already needed for FLAC files | Corrupted-file detection via `beet bad <query>` — a real gap in `music-lint` today, which checks placement/duplicates/completeness but never whether a file is silently corrupt. Would add a new row to `music-lint`'s check table, gated behind the same "extras must be installed first" preflight `music-curate` already uses for `fetchart`/`lastgenre`. |

## Import safety config (`import:`, `match:`, `duplicates:`)

`music-ingest` depends on these being set correctly in `config.yaml` before any unattended import runs. Verified against the installed beets' `config_default.yaml` (for defaults) and `ui/commands/import_/session.py` (for behavior):

| Key | Beets' own default | MusicOS setting | Why |
|---|---|---|---|
| `import.quiet` | `no` | `yes` | Suppresses all interactive prompts, unconditionally — the mechanism that makes unattended import safe/non-hanging, confirmed in `_summary_judgment()`. Baked into config (not just passed as `-q` per-invocation) so even an ad-hoc manual `beet import` is safe by default. |
| `import.quiet_fallback` | `skip` | `skip` | What happens to an album with no strong match when quiet. `skip`: left out of the library entirely, logged as `skip <path>` in the `-l` file. `asis` (do not use): writes unverified guessed tags into the library. |
| `import.duplicate_action` | `ask` | `upgrade` | What happens when an incoming album/item duplicates one already in the library (matched on `import.duplicate_keys`, default album `albumartist album` / item `artist title`). `upgrade` (beets 2.14.1, `importer/tasks.py` `resolve_upgrade`): per track, a new track is kept only if its `bitrate` is strictly higher than the matching old track's; superseded old files are deleted from disk (if under `directory:`) and the new tracks are grafted onto the existing album; if no track is better it degrades to `skip`. Bitrate is the only criterion: lossless beats lossy, but WAV also "beats" FLAC of the same resolution, and a partial incoming album yields a mixed-format album. `skip` is the safe alternative (never replace anything). **Config-only — no CLI flag exists for this.** Left at the `ask` default, it hangs a non-interactive run on the first duplicate. |
| `import.resume` | `ask` | `no` | `yes`/`ask` can hang or hide state in a non-interactive run; MusicOS batches are short enough that resuming an interrupted run isn't worth the complexity. |
| `import.incremental` / `incremental_skip_later` | `no` / — | `yes` / `yes` | Re-running the same source path is a no-op for already-seen files; skipped albums don't keep resurfacing on every re-run. |
| `match.strong_rec_thresh` | `0.04` | `0.20` | Threshold below which a match counts as "strong" and auto-applies in quiet mode. Loosened from the beets default because real matches on this library land around `.17`. |
| `match.max_rec.missing_tracks` / `.unmatched_tracks` | not capped | `strong` / `strong` | Caps the recommendation level when an otherwise-strong match has missing or unmatched tracks (common with deluxe/live-edition mismatches) — prevents those from auto-escalating past `strong` in quiet mode. |
| `duplicates.keys` / `strict` | — | `[albumartist, album, year]` / `yes` | As-is or skip-fallback imports may lack an `mb_albumid` to key duplicate detection on, so MusicOS keys on these tag fields instead; `strict: yes` ignores matches where a key is unset. |
| `import.remux_mp3_in_wav` | `no` | `no` | Off — this beets feature can delete the source file in edge cases; left at the safe default deliberately, not left unset by accident. |
| `import.group_albums` | `no` | `no` | Off — loose files are grouped into albums by their tags, not by folder structure. |

Skip-log status strings you'll actually see in a `-l LOGPATH` file under this config: `skip`, `duplicate-skip`, and `duplicate-keep`. `duplicate-keep` is a beets 2.14.1 mislabel: `ImportSession.log_choice` (`beets/importer/session.py`) checks `choice_flag in (ASIS, APPLY)` before `task.skip`, so an album that matched strongly and was then skipped as a duplicate is logged as `duplicate-keep` — it was **not** imported. Under `duplicate_action: upgrade` a successful upgrade is **also** logged as `duplicate-keep` (same code path), so the log alone can't tell an upgrade from a declined duplicate — check whether items from that path carry the batch's `musicos_batch` (item-level query; upgraded tracks are grafted onto the old album row). `asis` and `duplicate-replace` can't occur with `quiet_fallback: skip` / `duplicate_action: upgrade`. `beet import --pretend` never runs duplicate resolution, so it can't preview upgrades.

## Commands the skills rely on

| Command | Used by | Notes |
|---|---|---|
| `beet import --pretend <path>` | `music-ingest` | Dry run, no changes |
| `beet import --set K=V ...` | `music-ingest` | Applies to album + every item, template-expanded (`beets/importer/tasks.py:476-495`, `set_fields`) |
| `beet import -q --quiet-fallback skip <path>` | `music-ingest` | The only import mode now — strong matches apply automatically, ambiguous albums are skipped (never written in with guessed tags), duplicates replace old tracks only where higher bitrate, requires `quiet_fallback: skip` + `duplicate_action: upgrade` (or `skip`) already set in `config.yaml` |
| `beet import -t <path>` | `music-ingest` (manual-review fallback only) | Genuinely interactive timid mode — the one exception composed and handed to the user's own terminal, scoped only to paths `-l` logged as `skip` |
| `beet move --pretend` | `music-organize`, `music-lint` | Shows path drift without moving files (`beets/ui/commands/move.py:111-112`, the `opts.pretend` branch of `move_objects`) |
| `beet move` | `music-organize` | Physically relocates files to match current config |
| `beet duplicates -a` / `beet duplicates -k mb_trackid -k mb_albumid` | `music-organize`, `music-lint` | Report-only, never auto-resolve. Always pass `-a` or explicit `-k`: plain `beet duplicates` runs in item mode (beets 2.14.1) with the album-level `duplicates.keys`, so every track matches its album-mates |
| `beet missing` | `music-organize`, `music-lint` | Incomplete albums |
| `beet unimported` | `music-lint` | Files under `directory:` not in the DB |
| `beet ls singleton:true` | `music-lint` | Tracks with no album |
| `beet export -l -f json` / `beet export -a -f json` | `music-query` (via `scripts/library_snapshot.py`) | Structured output — `-l` is mandatory for track exports, see "Structured output" above |
| `beet stats <query>` | `music-query` | Aggregate counts/sizes |
| `beet fields` | `music-query` | Lists all known fields, including flex attributes in use |
| `beet modify -W <query> field=value` | `music-organize` (optional) | `-W` is **mandatory** unless you intend to rewrite the audio file's embedded tags too (`beets/ui/commands/modify.py:209` resolves write via `ui.should_write`, which defaults to `import.write`; `-W`/`--nowrite` defined at `:240-245`) |
| `beet edit <query>` | `music-organize` (optional) | Opens matched items/albums in `$EDITOR` for interactive bulk field edits; requires the `edit` plugin |
| `beet scrub <query>` | `music-organize` (optional) | Strips extraneous/junk tags (encoder tags, ripper comments) not part of beets' managed field set; requires the `scrub` plugin. Recommended as on-demand only — leave `scrub.auto` unset/`no`, not automatic-on-write (see "What's actually running" above for why one real config's `scrub.auto: yes` is worth reconsidering) |
| `beet embedart <query>` | `music-curate` (optional) | Embeds already-fetched art (or a manually-placed `cover.jpg`) into the audio files' own tags; requires the `embedart` extra. Often `auto: yes` already (fires on import) — this command is for backfilling art on material imported before that, or a specific forced re-embed |
| `beet fetchart [-f] [-q] <query>` | `music-curate` | Needs the `fetchart` extra; `-f`/`--force` re-fetches existing art, writes a sibling `cover.jpg` (not embedded). A manually-placed `cover.jpg`/`folder.jpg` in the album folder is only picked up if `filesystem` is in `fetchart.sources` (`config.yaml`) — it's not a beets default you get for free just by enabling the plugin, and beets' own shipped default list puts `filesystem` first, before any network source. Local matching is name-based only (`cover`/`front`/`art`/`album`/`folder`, via `cover_names`), not "any image in the folder" |
| `beet lastgenre [-A] [-p] <query>` | `music-curate` | Needs the `lastgenre` extra; `-A` = per-track not per-album, `-p`/`--pretend` previews; overwriting existing genres is a `force:` config option, not a CLI flag |
| `beet config --path` | manual diagnosis (`docs/SETUP.md`) | Prints the path of the currently active config.yaml — the key existing-library detection command |
| `beet config` | manual diagnosis (`docs/SETUP.md`) | Dumps the fully-resolved effective config (plugins, `directory:`, `paths:`, everything) |
| `beet import -L -t -- '^mb_albumid::.'` | `music-organize` (optional) | Retroactively re-matches already-in-library albums with a blank `mb_albumid` — see "Re-matching backlog imports" below |

## Re-matching backlog imports (no `mb_albumid`)

`beet ls -- '^mb_albumid::.'` (see "Unmatched imports" above) only *detects* albums with no MusicBrainz match — it doesn't fix anything. If that list is non-empty, first check *why*: `import.log`'s `asis`/`skip`/`duplicate-*` lines don't carry a reason, but a large `asis` count relative to `skip` is a strong signal that `quiet_fallback` was set to `asis` at some point in the past (writes an album in without ever attempting a match) rather than the project's required `skip`. Fix `quiet_fallback` in `config.yaml` first if so — otherwise every future import re-creates the same backlog.

To clear an existing backlog once the config is correct, retag the affected albums **in place** — no re-copying from outside the library, no risk of duplicating files:

```
beet import -L -t -- '^mb_albumid::.'
```

- `-L`/`--library` — selects items already in the library matching the query and re-runs them through the normal autotagger workflow, instead of importing new files from disk.
- `-t`/`--timid` — forces a confirmation prompt for every single proposed match, for this one invocation, regardless of the config's `quiet: yes` default. This is what makes the command safe to run as a manual, supervised backlog-clearing pass: nothing gets applied without the user seeing and approving it album by album.
- This does **not** change the `quiet: yes` / `quiet_fallback: skip` invariant that keeps `music-ingest`'s automated import path non-interactive — `-t` only overrides it for this specific one-off command.
- Normal `move`/path-scheme behavior still applies: a folder only gets relocated if the corrected tags actually change its computed path (e.g. a corrected album title).

## Uncertainties not yet verified against a real library

These are flagged, not assumed resolved — re-check once `docs/SETUP.md` has been completed and real music exists:

1. ~~Whether `beet import`'s interactive TUI degrades gracefully or hangs under a non-TTY session.~~ Resolved: moot for the default unattended path. `import.quiet: yes` (or `-q`) never opens an interactive prompt at all — confirmed against the installed beets' `ui/commands/import_/session.py`, whose `_summary_judgment()` short-circuits straight to an `Action` (`APPLY`/`SKIP`/`ASIS`) in quiet mode regardless of TTY. The one remaining genuinely interactive path is `-t`/timid mode, used only for manual review of albums `music-ingest` skipped — and that command is deliberately composed and handed to the user's own terminal, never driven through the agent's session. See the import-safety config section below.
2. If you switch to the optional `$albumartist_sort`/`$artist_sort` variant (see `docs/LIBRARY-LAYOUT.md`), whether those fields are reliably populated for this specific collection — not a concern with the default plain-`$albumartist` scheme.
3. Exact JSON shapes for `comp`/`genres`/`added`/`length` from a real `beet export -a -f json` run.
4. ~~Whether `beet export` on an empty/no-match query returns `[]` cleanly vs. a non-zero exit.~~ Resolved: exit is always `0`; an empty query returns `[]` cleanly for albums (`-a`, or any `-l` export) but see the `-l` gotcha above for the items-without-`-l` trap, which looks like the same symptom but for a different reason.
5. Windows console encoding for non-ASCII artist names, and whether `path:` queries handle backslash separators.
