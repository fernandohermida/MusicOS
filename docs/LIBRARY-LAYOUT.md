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
item_fields:
    # Alphabetical bucket: "A".."Z" or "#" for anything that doesn't start
    # with a letter (numbers, symbols, "3T", "2Pac", etc). Ignores a leading
    # English ("The"/"A"/"An") or Spanish definite ("El"/"La"/"Los"/"Las")
    # article for sorting purposes only — $albumartist itself (and the
    # folder name derived from it) is left untouched, so "The Beatles"
    # still reads "The Beatles" but buckets under B, not T, and "Las
    # Pelotas" still reads "Las Pelotas" but buckets under P, not L.
    initial: |
        name = albumartist or ''
        for article in ('the ', 'a ', 'an ', 'el ', 'la ', 'los ', 'las '):
            if name.lower().startswith(article):
                name = name[len(article):]
                break
        return name[0].upper() if name and name[0].isalpha() else '#'
    multidisc: 1 if (disctotal or 0) > 1 else 0

paths:
    albumtype:soundtrack: Soundtracks/$album%aunique{}/%if{$multidisc,$disc-}$track $artist - $title
    default: $initial/$albumartist/$album%aunique{}/%if{$multidisc,$disc-}$track $title
    singleton: $initial/Non-Album/$artist/$title
    comp: Various Artists/$album%aunique{}/%if{$multidisc,$disc-}$track $artist - $title
```

Two entirely different beets mechanisms are doing the work here, and it's worth understanding both:

### 1. The `$initial` computed field (via the `inline` plugin) — for the per-letter folders

Unlike a plain path template, `$initial` is Python code, computed once per item/album by the `inline` plugin and then used like any other field in the `paths:` templates below. It takes the first character of `$albumartist` (stripping a leading English article — "The"/"A"/"An" — or Spanish definite article — "El"/"La"/"Los"/"Las" — first, so "The Beatles" buckets under `B`, not `T`, and "Las Pelotas" buckets under `P`, not `L` — the stored `$albumartist` field itself is untouched, only the bucketing is affected), uppercases it, and falls back to the literal string `#` for anything that isn't alphabetic — not just for digits, but for **any** non-alphabetic leading character (symbols like `!!!` included, not only digits). `default` and `singleton` both reference `$initial` directly, so every artist gets its own single-letter folder (`Aphex Twin` → `A/`, `Beatles, The` → `B/`) with zero extra ranges to define. `singleton` uses `$artist` for the rest of its path (no album-level artist field on a standalone track), but still buckets via the same `$initial` field.

Only the *definite* Spanish articles are stripped (`el`/`la`/`los`/`las`), matching how "the" is stripped regardless of number in English — indefinite Spanish articles (`un`/`una`/`unos`/`unas`, the equivalent of "a"/"an") aren't in the list, since no artist in this library currently needs it; add them the same way if that changes.

An earlier version of this scheme used a path *template* (`%upper{%left{$albumartist,1}}`) plus a separate regex query key (`albumartist::^[0-9]`) to route only digit-leading artists to `#/`. That's been replaced by the single `$initial` field above — simpler (one mechanism instead of two) and broader (catches symbol-leading names too, not just digit-leading ones).

### 2. Path *keys* (`comp`, `albumtype:soundtrack`) — for the special categories

`comp` and `albumtype:soundtrack` aren't part of the path template language at all — they're **beets queries** used as config *keys*. This is a separate, documented beets feature: any key in `paths:` other than `default` is parsed as a query, and whichever album/item matches wins that path template. `comp` and `singleton` are recognized directly; anything else (like `albumtype:soundtrack`) is an ordinary query string. Confirmed straight from beets' own config reference: "in addition to `default`, `comp`, and `singleton`, you can condition path queries based on beets queries... The queries are tested in the order they appear in the configuration file... beets will use the path format for the *first* matching query" — `default` is always the fallback, evaluated last, regardless of where it's written.

**Order matters.** In the config above, `albumtype:soundtrack` is listed before `comp`, so a compilation soundtrack lands in `Soundtracks/`, not `Various Artists/`. Swap the order if you'd rather compilation status win.

## Why plain `$albumartist` instead of `$albumartist_sort`

An earlier version of this scheme preferred `$albumartist_sort` (MusicBrainz's sort-name field, e.g. "Beatles, The") so "The"-prefixed artists would file under their real letter rather than "T". That's been dropped for simplicity: `albumartist_sort` is only populated when an import gets a confident MusicBrainz match, so relying on it means asis/unmatched imports fall back to bucketing by an empty string. Plain `$albumartist` is always populated and never has that failure mode — the trade-off is that "The Beatles" files under `T`. If you'd rather have MusicBrainz-style sort-name bucketing back, swap `$albumartist`/`$artist` for `$albumartist_sort`/`$artist_sort` in the template lines above; just be aware of the empty-field caveat if a meaningful fraction of your collection is unmatched (check with `music-lint`'s unmatched-imports report).

## Non-alphanumeric artist names

Unlike the earlier template-based scheme (which only special-cased digit-leading names via a regex query key), `$initial`'s `isalpha()` check routes **any** non-alphabetic leading character — digits, symbols (`!!!`, `3T`-style, etc.) — into the same `#/` bucket, not just digits. There's no longer an unhandled edge case here: everything that isn't a plain letter falls into `#/` by construction, including an artist name that literally starts with the `#` character itself (a genuine, if rare, collision worth knowing about, but not one that needs a workaround).

## Changing the scheme later

Changing any of these templates or query keys after files already exist under the old scheme is safe but requires a reorganization pass: `beet move --pretend` will show every file that needs to move under the new config, then `beet move` (via the `music-organize` skill) actually relocates them. Always preview before applying.
