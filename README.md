# MusicOS

Agent-driven organization of a real music collection, built on the [beets](https://beets.io/) CLI, distributed as a Claude Code plugin.

This is not a wiki or a knowledge base — it's a set of Claude Code skills that make it easy to bring new music into a personal library and keep it well organized: correct tags, correct on-disk placement, no duplicates, no gaps.

- **Agents/config/docs live here, in `MusicOS/`.**
- **The actual music files live in a separate folder outside `MusicOS`**, organized into single-letter artist folders (`A/`, `B/`, ...) plus `#/`, `Various Artists/`, and `Soundtracks/` — set up entirely through beets' own config, no plugin required.
- **Beets itself is a runtime dependency, not vendored here.** Install it separately (`pipx install beets` or equivalent); every skill just shells out to the `beet` command.

## Install

Two ways to use MusicOS, both from this same repo:

**As a portable Claude Code plugin** (works from any project, not just a clone of this repo):
```
/plugin marketplace add <owner>/musicos
/plugin install musicos@musicos
```
Skills are then available namespaced, e.g. `musicos:music-setup`.

**By cloning this repo directly** and opening it in Claude Code — the skills under `.claude/skills/` auto-load for that project, invoked without the `musicos:` prefix.

Either way, you still need beets installed (see `docs/SETUP.md`) — MusicOS doesn't include it.

## Get started

Nothing is configured yet. Start with `docs/SETUP.md`, or just ask Claude Code to run the `music-setup` skill.

See `CLAUDE.md` for the full architecture and invariants, `docs/ROADMAP.md` for what's intentionally not built yet, and `CONTRIBUTING.md` if you'd like to contribute.
