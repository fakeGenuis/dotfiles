# Package declaration plan

## Phase 1: Declaration engine

- [x] Add `pkgdecl.py` with `check` and `list` commands.
- [x] Use `packages.toml` as the default configuration.
- [x] Read device bits from configuration; check masks and package suffixes.
- [x] Project the tree with inherited masks and explicit overrides.
- [x] Mount external files without moving or tracking them.
- [x] Preserve package and group sources when merging declarations.
- [x] Check dependencies without enabling excluded nodes.
- [x] Test overrides, mounts, cycles, conflicts, and CLI failures.
- [x] Document the format and verify the local declarations.

## Phase 2: Installed state

- [x] Read package groups and installed state through pacman.
- [x] Report missing, dependency-installed, and undeclared packages.
- [x] Account for providers and distinguish orphans from explicit packages.
- [x] List, explain, and search packages.
- [x] Offer plain package-name output for shell pipelines.

## Phase 3: Declaration editing

- [x] Adopt installed packages into a selected file and subtree.
- [x] Default adoption to the current device.
- [x] Preview edits and preserve comments and formatting.
- [x] Keep private declarations in their chosen external files.
- [x] Add a numbered tidy flow with batch selection and final confirmation.

## Boundaries

- Device names and bits are defined in `packages.toml`.
- Explicit masks replace inherited masks; excluded parents do not stop traversal.
- Dependencies are constraints, not selection rules.
- External files remain external; plain package lists inherit their mount mask.
- Phase 1 performs no package-manager queries or system changes.
- Installation and removal remain the responsibility of pacman or paru.

## Implementation style

- Keep plain functions and dictionaries; add abstractions only when needed.
- Avoid schema frameworks, field whitelists, and legacy compatibility modes.
- Check core semantics rather than every possible malformed input.
- Keep comments, documentation, and tests concise.
