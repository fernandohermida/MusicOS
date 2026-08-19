"""Thin wrapper around `beet export` for music-query/music-organize/music-lint.

Runs `beet export -f json` and normalizes the beets export-formatting quirks
documented in docs/BEETS-CHEATSHEET.md before handing back plain Python data:

- Multi-value fields (genres, artists, mb_albumartistids, albumtypes, ...)
  come back from beets as "; "-joined strings, not JSON arrays. This script
  splits configured fields on "; " into real lists.
- Everything else passes through unchanged (dates/bools stay as the strings
  beets formatted them, per the gotchas doc — this script does not attempt
  to re-parse those, since correctness there needs a real library to verify).

Not a beets plugin, not part of the beets source tree — just a small,
stdlib-only helper the skills can shell out to instead of hand-rolling the
same `beet export` + json.loads + multi-value-split logic in every skill.

Usage:
    python scripts/library_snapshot.py [--albums] [--query QUERY]
        [--fields id,album,albumartist,...] [--out FILE]

With no arguments, exports all albums with a small default field set.
Prints normalized JSON to stdout unless --out is given.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys

# Fields beets joins with "; " when exporting — see
# docs/BEETS-CHEATSHEET.md's "export formatting gotchas". Extend this list
# if a real export run turns up others.
MULTI_VALUE_FIELDS = {
    "genres",
    "artists",
    "artists_sort",
    "artists_credit",
    "albumartists",
    "albumartists_sort",
    "albumartists_credit",
    "albumtypes",
    "mb_artistids",
    "mb_albumartistids",
    "style",
    "mood",
}

DEFAULT_ALBUM_FIELDS = [
    "id",
    "album",
    "albumartist",
    "albumartist_sort",
    "mb_albumid",
    "mb_releasegroupid",
    "mb_albumartistid",
    "mb_albumartistids",
    "albumtype",
    "albumtypes",
    "genres",
    "year",
    "label",
    "comp",
    "added",
    "musicos_batch",
]


def run_export(
    query: list[str], albums: bool, fields: list[str] | None
) -> list[dict]:
    cmd = ["beet", "export", "-f", "json"]
    if albums:
        cmd.append("-a")  # -a implies --library
    else:
        # Without -l, item exports read tags from disk file-by-file
        # (beetsplug/info.py's tag_data) instead of the DB, and silently
        # return [] on an empty query instead of "everything" -- see
        # docs/BEETS-CHEATSHEET.md's "Structured output" section.
        cmd.append("-l")
    if fields:
        cmd += ["-i", ",".join(fields)]
    cmd += query

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=False
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "`beet` not found on PATH — is beets installed? "
            "Run the music-setup skill (or see docs/SETUP.md) first."
        ) from exc
    if result.returncode != 0:
        raise RuntimeError(
            f"`{' '.join(cmd)}` failed (exit {result.returncode}): "
            f"{result.stderr.strip()}"
        )

    stdout = result.stdout.strip()
    if not stdout:
        return []
    return json.loads(stdout)


def normalize(records: list[dict]) -> list[dict]:
    normalized = []
    for record in records:
        entry = dict(record)
        for field in MULTI_VALUE_FIELDS:
            value = entry.get(field)
            if isinstance(value, str):
                entry[field] = (
                    [v for v in value.split("; ") if v] if value else []
                )
        normalized.append(entry)
    return normalized


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--albums",
        action="store_true",
        default=True,
        help="export albums (default) rather than items",
    )
    parser.add_argument(
        "--items",
        dest="albums",
        action="store_false",
        help="export items/tracks instead of albums",
    )
    parser.add_argument(
        "--query",
        nargs=argparse.REMAINDER,
        default=[],
        help="beets query terms, passed through as-is (put last)",
    )
    parser.add_argument(
        "--fields",
        default=",".join(DEFAULT_ALBUM_FIELDS),
        help="comma-separated field list for -i (default: a small album field set)",
    )
    parser.add_argument(
        "--out", default=None, help="write JSON here instead of stdout"
    )
    args = parser.parse_args()

    fields = [f for f in args.fields.split(",") if f] if args.fields else None

    try:
        records = run_export(args.query, args.albums, fields)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    normalized = normalize(records)
    output = json.dumps(normalized, indent=2, ensure_ascii=False)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(output)
    else:
        print(output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
