# Setup guide

This is the checklist for standing up a working MusicOS from scratch. There's no setup skill to drive this interactively; follow this checklist by hand (or have an agent follow it step by step, reading and editing `beetsdir/config.yaml` directly, same as any other file in the repo).

**Already have a beets library — your own `config.yaml`, `library.db`, and an already-organized collection?** Skip to [Adopting an existing beets library](#adopting-an-existing-beets-library) near the end instead of starting from step 1 — none of your existing config, database, or music files need to move.

## 1. Install beets

MusicOS doesn't vendor or fork beets — it depends on it purely as an installed CLI tool (every skill shells out to the `beet` command; nothing here `import`s beets as a Python library). Install it from PyPI, whichever way fits how you manage tools:

- **`pipx install beets`** — recommended for most people: an isolated global install, so `beet` is just a command on your PATH. This is what the rest of this guide assumes.
- **`uv tool install beets`** — equivalent, if you already use `uv` for tool management.
- **`pip install beets`** — into whatever virtualenv you're already using, if you'd rather manage it that way.

If you want to hack on beets itself or track its `master` branch, clone `github.com/beetbox/beets` **somewhere outside this repo** and follow beets' own `CONTRIBUTING.rst` (`uv sync` + `uv run beet`) — that's a separate concern from running MusicOS against a released version.

Entry point is `beets.ui:main`; `python -m beets` also works as a fallback with any of the above.

**Verified beets version: 2.14.1** (Python 3.13). The beets source file:line references in `docs/BEETS-CHEATSHEET.md` and `docs/LIBRARY-LAYOUT.md` were checked against this release — re-check them after upgrading. Upgrade in place with `pipx upgrade beets` (or `pip install -U "beets[fetchart,lastgenre,embedart,chroma]"` inside a manual venv), and back up `library.db` first — a new release can migrate the database schema.

**Don't enable the `limit` plugin.** It's deprecated as of beets 2.14 (removed in 3.0.0) and prints a warning on every `beet` command; use the built-in `beet ls -l <number>` instead.

## 2. Set `BEETSDIR`

Beets needs to know where its config/database live — point it at this repo's `beetsdir/` folder.

**Windows (PowerShell):**
```powershell
setx BEETSDIR "<path-to-your-musicos-clone>\beetsdir"
```
`setx` is user-scoped and **requires a new shell/terminal** to take effect — check `$env:BEETSDIR` in a fresh window before assuming it's set.

**macOS/Linux (bash/zsh):** add the export below, then open a new shell (or `source` the file):
```sh
export BEETSDIR="<path-to-your-musicos-clone>/beetsdir"
```
- **zsh:** `~/.zshrc`.
- **bash on macOS:** `~/.bash_profile` — Terminal.app launches bash as a *login* shell, and login shells don't read `~/.bashrc` unless `.bash_profile` explicitly sources it. Putting the export in `~/.bashrc` alone will silently not take effect.
- **bash on Linux:** `~/.bashrc` (interactive non-login shells) — add it to `~/.bash_profile`/`~/.profile` too if you also use login shells.

**If you installed beets into a manual venv instead of via `pipx`/`uv tool`** (which auto-register `beet` on `PATH`), also symlink the binary into a directory that's unconditionally on `PATH`, e.g.:
```sh
ln -s <path-to-your-musicos-clone>/beetsdir/venv/bin/beet /usr/local/bin/beet
```

**Non-interactive/non-login shells (cron, CI, automation tools like Claude Code's Bash tool) never source `~/.bash_profile`/`~/.bashrc`/`~/.zshrc` at all** — any `export` in those files (`BEETSDIR`, `PATH`, `SSL_CERT_FILE`, below) is invisible to them. Symlinking `beet` onto an already-on-`PATH` directory (above) fixes resolution; `BEETSDIR` and `SSL_CERT_FILE` have no equivalent workaround, so such tools must pass them explicitly per-invocation, e.g. `BEETSDIR=... SSL_CERT_FILE=... beet ...`, rather than assuming the profile export applies.

**macOS Python-framework venvs may need `SSL_CERT_FILE` set explicitly.** These builds don't verify TLS against the OS trust store, so network-dependent plugins that use their own SSL context rather than `requests` (`musicbrainz`/`musicbrainzngs`, and `lastgenre`'s Last.fm lookups via `pylast`) fail with `CERTIFICATE_VERIFY_FAILED` — or, worse, **fail silently and just look like "no match found."** If MusicBrainz matches or Last.fm genres seem suspiciously absent, run with `-vv` and check for this before assuming there's really no match:
```sh
export SSL_CERT_FILE="<path-to-your-musicos-clone>/beetsdir/venv/lib/python3.13/site-packages/certifi/cacert.pem"
```
(adjust the Python version in the path to match your venv). `requests`-based plugins bundle their own `certifi` bundle and aren't affected.

## 3. Write a real config

**There is no packaged config template in this repo right now** — build `beetsdir/config.yaml` by hand, following this walkthrough. At minimum, set:

- **`directory:`** — the external folder where music files actually live. **Never point this inside `MusicOS/`.** Choose deliberately — consider available disk space if this is a large collection.
- **`library:`** — usually fine left as the default `library.db`, which resolves inside `BEETSDIR`.
- **`paths:`** — see `docs/LIBRARY-LAYOUT.md` for the full recommended `paths:`/`item_fields:` block (single-letter artist folders via a computed `$initial` field, so digit/symbol-leading and "The"/"A"/"El"/"La"-prefixed artists bucket correctly, plus `#/`, `Various Artists/`, and `Soundtracks/`) and what to change if you want a different scheme — much cheaper to change now than after files exist under the old one. That doc also covers `asciify_paths`/`per_disc_numbering`, two more settings worth deciding on at the same time since they affect what actually lands on disk.

## 4. Enable plugins

Start with the zero-extra-dependency v1 set (see `docs/BEETS-CHEATSHEET.md` for the full verified list, including which of these are confirmed actually running on a real library vs. still-unverified candidates):

```yaml
plugins: export types missing duplicates unimported musicbrainz mbsync inline edit fromfilename ftintitle scrub info
```

Also pin these for reliable machine-parseable exports (see the export-formatting gotchas in `docs/BEETS-CHEATSHEET.md`):

```yaml
time_format: '%Y-%m-%d %H:%M:%S'
format_raw_length: yes
```

Extras (`fetchart`, `lastgenre`, `embedart`, `chroma`, `replaygain`, `badfiles`, etc. — see `docs/BEETS-CHEATSHEET.md`'s "What's actually running" and "Other candidate plugins" sections) can be added later by reinstalling beets with the relevant extra — e.g. `pipx install --force "beets[fetchart,lastgenre]"` (or the equivalent `pip install`/`uv tool install` form for whichever method you used in step 1). If you're tempted to add a second autotagger source (`discogs`, `deezer`, `spotify`) alongside `musicbrainz`, read `docs/BEETS-CHEATSHEET.md`'s "Autotagger sources: MusicBrainz only" section first — it can silently break `mbsync`.

## 5. MusicBrainz awareness for a large first import

If importing a big existing collection at once, be aware of MusicBrainz's public API rate limits — large imports can take a while and may need to run in chunks. No special config needed for v1, just set expectations.

## 6. First import

1. `beet import --pretend <path>` — dry run, review what it proposes.
2. Real import, unattended: `beet import -q --quiet-fallback skip <path>`. With `quiet_fallback: skip` and `duplicate_action: upgrade` (or `skip`) set in `config.yaml` (per step 3), this never opens an interactive prompt — it's safe to run directly, including from an agent's non-interactive session. Albums with no strong match are skipped rather than guessed at; albums that duplicate something already in the library replace the old tracks only where the new ones have a higher bitrate (the old files are deleted), otherwise they're skipped; see `music-ingest`'s skip-log review step for how to see what got skipped, and its `-t`/timid manual-review fallback (genuinely interactive, run in your own terminal) for resolving specific ones by hand.
3. Run `music-organize` to confirm placement and check for gaps.

## 7. `library.db` backup

`beetsdir/library.db` is the single source of truth for all your tags/metadata — back it up like any other important file (it's excluded from git via `.gitignore`, since it's a binary DB, not source).

## Verifying the setup worked

- `beet version` runs without error and lists `export` among enabled plugins.
- `beet move --pretend` (even against zero items) runs without error.
- `beet stats` returns a (possibly empty) report.

If any of these fail, re-check `BEETSDIR` (step 2) and the `config.yaml` you wrote in step 3 — `beet -vv version` will usually show which config file it actually loaded and why a plugin failed to start.

## Adopting an existing beets library

If you already run beets against a real collection — your own `config.yaml`, `library.db`, and an already-organized `directory:` — steps 1–6 above don't apply. Here's the safe way to get MusicOS's skills working with what you already have, without re-importing anything or risking your existing config.

### Find out where things already live

1. Confirm beets is on PATH and see your active config: `beet config --path` prints the path to whichever `config.yaml` is currently in effect (your `BEETSDIR`, or one of the OS-default locations beets searches when `BEETSDIR` isn't set).
2. `beet config` with no flags dumps your fully-resolved effective configuration — enabled plugins, `directory:`, `paths:`, everything. Read through it before changing anything.

### Decide: leave it where it is, or centralize under `MusicOS/beetsdir/`?

**Recommended: leave everything exactly where it is.** Every MusicOS skill just shells out to `beet` — as long as `beet` resolves to your existing config wherever it already lives, the skills work immediately. There's nothing to move. Skip straight to "Add what MusicOS needs" below.

**Only if you specifically want everything centralized under `MusicOS/beetsdir/`:**
1. Back up first — copy (don't move) your existing `config.yaml`, `library.db`, and `state.pickle` (if present) somewhere safe.
2. Copy — never move — those same files into `MusicOS/beetsdir/`. Don't overwrite anything already there without checking what it is first.
3. Point `BEETSDIR` at `MusicOS/beetsdir` (step 2 above), open a fresh shell, and confirm `beet config --path` now resolves to the new location.
4. Confirm `beet stats` and `beet ls` show the same library contents as before. Only once that checks out should you consider removing the originals — no rush.

Either way, **your actual music files never need to move**, and neither does `directory:` — this is only about where `config.yaml`/`library.db` live, not where your audio is.

### Add what MusicOS needs, without touching what you already have

MusicOS's skills need a few plugins your existing config might not enable yet: `export` (structured output for `music-query`/`music-lint`), `types`, and `unimported`. **Append these to your existing `plugins:` line — don't replace it, and don't add them via a second `--config` overlay file.** Beets' config layering doesn't reliably merge list-valued options like `plugins:` across multiple files — a higher-priority source can simply take over that key rather than combining with a lower-priority one — so the only way to guarantee none of your existing plugins get silently dropped is a direct, one-line edit to your own `config.yaml`.

**You do not need to adopt MusicOS's `paths:` scheme** (the single-letter/`#`/`Various Artists`/`Soundtracks` layout from `docs/LIBRARY-LAYOUT.md`). If you're happy with your current organization, leave your existing `paths:` config exactly as it is — `music-organize`'s placement checks just compare against whatever `paths:` is currently configured, whatever that happens to be.

**If you do want to switch to MusicOS's scheme on an already-organized library**, that's a real reorganization of existing files, not a fresh layout with nothing to move yet. Treat it like any other `music-organize` change: edit `paths:`, run `beet move --pretend` to see every file that would move, review it carefully, and only then run `beet move` for real.

### What not to do

- **Don't run `beet import`** on music that's already in the library — that's for new music only, and running it against an already-imported collection is redundant at best and risks duplicate entries at worst.
- **Don't run `beet move`** until the user has explicitly decided whether to keep their existing organization or switch to MusicOS's scheme.
