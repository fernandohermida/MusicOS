# Contributing to MusicOS

Thanks for considering a contribution. MusicOS is a small set of Claude Code skills orchestrating the stock `beets` CLI — see `CLAUDE.md` for the architecture and invariants before making changes.

## Scope

- No new beets plugin code. Everything shells out to the stock `beet` CLI plus the zero-extra-dependency plugins listed in `docs/BEETS-CHEATSHEET.md`. See `docs/ROADMAP.md` for what's deliberately deferred and why.
- No wiki/notes/synthesis layer. The library (files + beets' database) is the only source of truth — see `CLAUDE.md`'s invariants.
- Never vendor or fork beets into this repo — it's a runtime dependency only (`docs/SETUP.md`).

## Making changes to a skill

Each skill lives at `.claude/skills/<name>/SKILL.md`. Keep the frontmatter `description` focused purely on *when* to use the skill (starts with "Use when...") — not a summary of what it does — since Claude reads the description to decide whether to load the skill at all; a description that pre-summarizes the workflow tends to get followed instead of the actual body. If a change affects any `beet` command's exact behavior, re-verify it against a real beets install and update `docs/BEETS-CHEATSHEET.md`'s citations rather than assuming the old ones still hold — beets releases can change formatting/output details.

## Releasing a new plugin version

MusicOS is distributed as a Claude Code plugin via `.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json`. Two things are easy to get wrong here, both confirmed against Claude Code's own docs:

1. **`version` in `plugin.json` must be bumped on every release that should reach existing installs.** `/plugin update` and auto-update compare this string; if it's unchanged, users stay on the old cached copy with no error or warning telling them anything's stale.
2. **Never set `version` in both `plugin.json` and the marketplace entry in `marketplace.json`.** If both are set, `plugin.json`'s value silently wins — a maintainer editing only the marketplace entry can be fooled into thinking they've shipped a new version when they haven't.

Checklist for a release:
- [ ] Bump `version` in `.claude-plugin/plugin.json` (semver).
- [ ] Confirm `.claude-plugin/marketplace.json` does *not* also set `version` for this plugin entry.
- [ ] `python -c "import json; json.load(open('.claude-plugin/plugin.json')); json.load(open('.claude-plugin/marketplace.json'))"` — both parse.
- [ ] If any `beet` command behavior changed, update `docs/BEETS-CHEATSHEET.md`.

## Reporting issues / discussing ideas

Open a GitHub issue on this repo. If your question is more about beets itself (not MusicOS), beets has its own [GitHub Discussions](https://github.com/beetbox/beets/discussions) — MusicOS isn't a beets plugin, so beets' own issue tracker isn't the right place for MusicOS-specific bugs.
