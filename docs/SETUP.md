# Setup guide

Nothing is installed or configured yet. This is the checklist for standing up a real, working MusicOS — whenever you're ready, not before. The `music-setup` skill can drive most of this interactively; this document is the reference for what it's doing and why.

**Already have a beets library — your own `config.yaml`, `library.db`, and an already-organized collection?** Skip to [Adopting an existing beets library](#adopting-an-existing-beets-library) near the end instead of starting from step 1 — none of your existing config, database, or music files need to move.

## 1. Install beets

MusicOS doesn't vendor or fork beets — it depends on it purely as an installed CLI tool (every skill shells out to the `beet` command; nothing here `import`s beets as a Python library). Install it from PyPI, whichever way fits how you manage tools:

- **`pipx install beets`** — recommended for most people: an isolated global install, so `beet` is just a command on your PATH. This is what the rest of this guide assumes.
- **`uv tool install beets`** — equivalent, if you already use `uv` for tool management.
- **`pip install beets`** — into whatever virtualenv you're already using, if you'd rather manage it that way.

If you want to hack on beets itself or track its `master` branch, clone `github.com/beetbox/beets` **somewhere outside this repo** and follow beets' own `CONTRIBUTING.rst` (`uv sync` + `uv run beet`) — that's a separate concern from running MusicOS against a released version.

Entry point is `beets.ui:main`; `python -m beets` also works as a fallback with any of the above.

## 2. Set `BEETSDIR`

Beets needs to know where its config/database live — point it at this repo's `beetsdir/` folder.

**Windows (PowerShell):**
```powershell
setx BEETSDIR "<path-to-your-musicos-clone>\beetsdir"
```
`setx` is user-scoped and **requires a new shell/terminal** to take effect — check `$env:BEETSDIR` in a fresh window before assuming it's set.

**macOS/Linux (bash/zsh):** add to `~/.bashrc`, `~/.zshrc`, or equivalent, then open a new shell (or `source` the file):
```sh
export BEETSDIR="<path-to-your-musicos-clone>/beetsdir"
```

## 3. Turn the config template into a real config

Copy `beetsdir/config.example.yaml` to `beetsdir/config.yaml` and fill in:

- **`directory:`** — the external folder where music files actually live. **Never point this inside `MusicOS/`.** Choose deliberately — consider available disk space if this is a large collection.
- **`library:`** — usually fine left as the default `library.db`, which resolves inside `BEETSDIR`.
- **`paths:`** — already set up for single-letter artist folders plus `#/`, `Various Artists/`, and `Soundtracks/`. See `docs/LIBRARY-LAYOUT.md` for how it works and what to change if you want a different scheme — much cheaper to change now than after files exist under the old one.

## 4. Enable plugins

Only enable what's needed for v1 — all zero extra pip dependencies (see `docs/BEETS-CHEATSHEET.md` for the full verified list):

```yaml
plugins: export types missing duplicates unimported limit musicbrainz
```

Also pin these for reliable machine-parseable exports (see the export-formatting gotchas in `docs/BEETS-CHEATSHEET.md`):

```yaml
time_format: '%Y-%m-%d %H:%M:%S'
format_raw_length: yes
```

Extras (`fetchart`, `lastgenre`, etc.) can be added later by reinstalling beets with the relevant extra — e.g. `pipx install --force "beets[fetchart,lastgenre]"` (or the equivalent `pip install`/`uv tool install` form for whichever method you used in step 1) — deferred per `docs/ROADMAP.md`.

## 5. MusicBrainz awareness for a large first import

If importing a big existing collection at once, be aware of MusicBrainz's public API rate limits — large imports can take a while and may need to run in chunks. No special config needed for v1, just set expectations.

## 6. First import

1. `beet import --pretend <path>` — dry run, review what it proposes.
2. Real import, assisted mode: run the composed command yourself in your own terminal (see `music-ingest` skill — beets' match-selection prompt is an interactive TUI, best driven directly rather than through an agent's piped session).
3. Run `music-organize` to confirm placement and check for gaps.

## 7. `library.db` backup

`beetsdir/library.db` is the single source of truth for all your tags/metadata — back it up like any other important file (it's excluded from git via `.gitignore`, since it's a binary DB, not source).

## Verifying the setup worked

- `beet version` runs without error and lists `export` among enabled plugins.
- `beet move --pretend` (even against zero items) runs without error.
- `beet stats` returns a (possibly empty) report.

If any of these fail, see `music-setup`'s diagnosis steps.

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

MusicOS's skills need a few plugins your existing config might not enable yet: `export` (structured output for `music-query`/`music-lint`), `types`, `unimported`, `limit`, and optionally `smartplaylist` (only if you want `music-playlist`). **Append these to your existing `plugins:` line — don't replace it, and don't add them via a second `--config` overlay file.** Beets' config layering doesn't reliably merge list-valued options like `plugins:` across multiple files — a higher-priority source can simply take over that key rather than combining with a lower-priority one — so the only way to guarantee none of your existing plugins get silently dropped is a direct, one-line edit to your own `config.yaml`.

**You do not need to adopt MusicOS's `paths:` scheme** (the single-letter/`#`/`Various Artists`/`Soundtracks` layout from `docs/LIBRARY-LAYOUT.md`). If you're happy with your current organization, leave your existing `paths:` config exactly as it is — `music-organize`'s placement checks just compare against whatever `paths:` is currently configured, whatever that happens to be.

**If you do want to switch to MusicOS's scheme on an already-organized library**, that's a real reorganization of existing files, not a fresh layout with nothing to move yet. Treat it like any other `music-organize` change: edit `paths:`, run `beet move --pretend` to see every file that would move, review it carefully, and only then run `beet move` for real.

### What not to do

- **Don't run `beet import`** on music that's already in the library — that's for new music only, and running it against an already-imported collection is redundant at best and risks duplicate entries at worst.
- **Don't run `beet move`** until the user has explicitly decided whether to keep their existing organization or switch to MusicOS's scheme.
