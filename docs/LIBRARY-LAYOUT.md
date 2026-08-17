# Library layout

## What we're building

The music collection (outside `MusicOS/`, at whatever folder `directory:` points to) is organized into single-letter folders, one per artist's starting letter, plus three special categories:

```
<library folder>/
├── A/
│   └── Aphex Twin/<album folders...>
├── B/
│   └── Beatles, The/<album folders...>   (or "The Beatles", see below)
├── ...
├── Z/
├── #/
│   └── 3 Doors Down/<album folders...>
├── Various Artists/
│   └── <compilation album folders...>
└── Soundtracks/
    └── <soundtrack album folders...>
```

This is implemented entirely through beets' own `paths:` config — **no plugin involved**. An earlier version of this scheme used beets' built-in `bucket` plugin to group artists into alphabetical *ranges* (`0-C`, `D-F`, ...); that's been dropped in favor of plain per-letter folders and plain config, per a deliberate simplification: fewer moving parts, nothing beyond what beets ships with by default.

## The config

```yaml
paths:
  singleton: "%upper{%left{$artist,1}}/$artist/Non-Album/$title"
  albumtype:soundtrack: Soundtracks/$album%aunique{}/$track $title
  comp: Various Artists/$album%aunique{}/$track $title
  albumartist::^[0-9]: "#/$albumartist/$album%aunique{}/$track $title"
  default: "%upper{%left{$albumartist,1}}/$albumartist/$album%aunique{}/$track $title"
```

Two entirely different beets mechanisms are doing the work here, and it's worth understanding both:

### 1. Path *templates* (`%upper`, `%left`, ...) — for the per-letter folders

`%left{$albumartist,1}` takes the first character of the artist name; `%upper{...}` uppercases it. So `default` alone gives every artist its own single-letter folder (`Aphex Twin` → `A/`, `Beatles, The` → `B/`) with zero extra config — no ranges to define, no plugin. `singleton` does the same thing for standalone tracks (no album), using `$artist` instead of `$albumartist` since singletons have no album-level artist field.

### 2. Path *keys* (`comp`, `albumtype:soundtrack`, the `::^[0-9]` line) — for the special categories

The other three entries aren't part of the path template language at all — they're **beets queries** used as config *keys*. This is a separate, documented beets feature: any key in `paths:` other than `default` is parsed as a query, and whichever album/item matches wins that path template. `comp` and `singleton` are recognized directly; anything else (like `albumtype:soundtrack`) is an ordinary query string. Confirmed straight from beets' own config reference: "in addition to `default`, `comp`, and `singleton`, you can condition path queries based on beets queries... The queries are tested in the order they appear in the configuration file... beets will use the path format for the *first* matching query" — `default` is always the fallback, evaluated last, regardless of where it's written.

**Order matters.** In the config above, `albumtype:soundtrack` is listed before `comp`, so a compilation soundtrack lands in `Soundtracks/`, not `Various Artists/`. Swap the order if you'd rather compilation status win.

**The digit-leading `#` bucket is the one piece that genuinely needs the query mechanism, not the template mechanism.** Beets' `%if` template function only tests whether a string is empty/`"0"`/`"false"` — it has no comparison or regex support, so there's no way to ask "does this artist name start with a digit?" from *inside* a path template. Queries, on the other hand, support regex directly (`field::regex`), so `albumartist::^[0-9]` — a normal beets query, evaluated the same way `comp` or `albumtype:soundtrack` is — does exactly this: any album whose `albumartist` starts with a digit routes to `#/` before ever reaching the letter-bucketing `default` template. This is the reason the config above needs *two* different mechanisms instead of one: the template language can bucket by letter, but only the query language can classify by character type. (The `#` name is a common convention for "numeric-leading" sections in alphabetized media listings — it's just a literal folder name here, not special syntax.)

## Why plain `$albumartist` instead of `$albumartist_sort`

An earlier version of this scheme preferred `$albumartist_sort` (MusicBrainz's sort-name field, e.g. "Beatles, The") so "The"-prefixed artists would file under their real letter rather than "T". That's been dropped for simplicity: `albumartist_sort` is only populated when an import gets a confident MusicBrainz match, so relying on it means asis/unmatched imports fall back to bucketing by an empty string. Plain `$albumartist` is always populated and never has that failure mode — the trade-off is that "The Beatles" files under `T`. If you'd rather have MusicBrainz-style sort-name bucketing back, swap `$albumartist`/`$artist` for `$albumartist_sort`/`$artist_sort` in the template lines above; just be aware of the empty-field caveat if a meaningful fraction of your collection is unmatched (check with `music-lint`'s unmatched-imports report).

## Non-alphanumeric artist names

Anything that's neither alphabetic nor caught by the digit regex (an artist name starting with a symbol, e.g. `!!!`) falls through to `default` and gets a literal single-character folder for whatever that character is — note this could theoretically produce a folder literally named `#` if an artist name starts with that character, colliding with the digit bucket's folder; a rare enough edge case not to design around up front, but worth knowing about. This wasn't asked for and isn't handled specially — easy to special-case later with another regex query key (`albumartist::^[^a-zA-Z0-9]`) if it turns out to matter for your collection.

## Changing the scheme later

Changing any of these templates or query keys after files already exist under the old scheme is safe but requires a reorganization pass: `beet move --pretend` will show every file that needs to move under the new config, then `beet move` (via the `music-organize` skill) actually relocates them. Always preview before applying.
