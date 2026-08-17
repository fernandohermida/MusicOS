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

`beet list -f '$field1 $field2' <query>` also works for quick human-readable text, but has **no escaping** — a field value containing a space breaks naive whitespace-splitting. Don't parse `-f` text output programmatically; use `export` instead.

### Export formatting gotchas (verified against `beets/dbcore/types.py` in the beets source)

- **Dates** (`added`, `mtime`) format as local-time strings via `strftime`, not epoch — timezone/format can vary by machine and by the `time_format` config. Pin `time_format` in config for consistent parsing (see `docs/SETUP.md`).
- **Booleans** (`comp`) format as the literal strings `"True"`/`"False"`, not JSON booleans.
- **Multi-value fields** (`genres`, `albumartists`, `mb_albumartistids`, `albumtypes`, `artists`) are `"; "`-joined single strings, **not** JSON arrays. Split on `"; "` before treating as a list.
- **`length`** formats as `"M:SS"` unless `format_raw_length: yes` is set (recommended in `docs/SETUP.md` for machine-readable exports).

## Zero-extra-dependency plugins usable in v1

Checked against `beets/pyproject.toml`'s `[project.optional-dependencies]` — none of these require an extra:

`export`, `info`, `types`, `missing`, `duplicates`, `unimported`, `limit`, `smartplaylist`, `mbsync`, `fromfilename`, `inline`, `edit`, `hook`.

Anything else needs reinstalling beets with the relevant pip extra (e.g. `pipx install --force "beets[fetchart,lastgenre]"`). `fetchart` and `lastgenre` are used by `music-curate` (opt-in, not in the base plugin list — see `docs/SETUP.md`); `lyrics`, `chroma`, `discogs`, etc. aren't used by any MusicOS skill (`lyrics` deliberately excluded, see `docs/ROADMAP.md`).

## Commands the skills rely on

| Command | Used by | Notes |
|---|---|---|
| `beet import --pretend <path>` | `music-ingest` | Dry run, no changes |
| `beet import --set K=V ...` | `music-ingest` | Applies to album + every item, template-expanded (`beets/importer/tasks.py:469-486`) |
| `beet import -q --quiet-fallback skip` | `music-ingest` | Unattended mode — strong matches only, ambiguous ones skipped |
| `beet move --pretend` | `music-setup`, `music-organize`, `music-lint` | Shows path drift without moving files (`beets/ui/commands/move.py:169-194`) |
| `beet move` | `music-organize` | Physically relocates files to match current config |
| `beet duplicates` | `music-organize`, `music-lint` | Report-only, never auto-resolve |
| `beet missing` | `music-organize`, `music-lint` | Incomplete albums |
| `beet unimported` | `music-lint` | Files under `directory:` not in the DB |
| `beet ls singleton:true` | `music-lint` | Tracks with no album |
| `beet export -f json` | `music-query`, `music-organize`, `music-lint` | Structured output |
| `beet stats <query>` | `music-query` | Aggregate counts/sizes |
| `beet fields` | `music-query` | Lists all known fields, including flex attributes in use |
| `beet modify -W <query> field=value` | `music-organize` (optional) | `-W` is **mandatory** unless you intend to rewrite the audio file's embedded tags too (`beets/ui/commands/modify.py:162`) |
| `beet fetchart [-f] [-q] <query>` | `music-curate` | Needs the `fetchart` extra; `-f`/`--force` re-fetches existing art, writes a sibling `cover.jpg` (not embedded) |
| `beet lastgenre [-A] [-p] <query>` | `music-curate` | Needs the `lastgenre` extra; `-A` = per-track not per-album, `-p`/`--pretend` previews; overwriting existing genres is a `force:` config option, not a CLI flag |
| `beet splupdate [name.m3u ...]` | `music-playlist` | Regenerates playlists from `smartplaylist.playlists`; `--pretend` previews, zero extra dependencies |
| `beet config --path` | `music-setup` | Prints the path of the currently active config.yaml — the key existing-library detection command |
| `beet config` | `music-setup` | Dumps the fully-resolved effective config (plugins, `directory:`, `paths:`, everything) |

## Uncertainties not yet verified against a real library

These are flagged, not assumed resolved — re-check once `docs/SETUP.md` has been completed and real music exists:

1. Whether `beet import`'s interactive TUI degrades gracefully or hangs under a non-TTY session.
2. If you switch to the optional `$albumartist_sort`/`$artist_sort` variant (see `docs/LIBRARY-LAYOUT.md`), whether those fields are reliably populated for this specific collection — not a concern with the default plain-`$albumartist` scheme.
3. Exact JSON shapes for `comp`/`genres`/`added`/`length` from a real `beet export -a -f json` run.
4. Whether `beet export` on an empty/no-match query returns `[]` cleanly vs. a non-zero exit.
5. Windows console encoding for non-ASCII artist names, and whether `path:` queries handle backslash separators.
