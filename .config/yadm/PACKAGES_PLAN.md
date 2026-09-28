# Package declaration plan

## Phase 1: Declaration engine

- [ ] Add `pkgdecl.py` with `check` and `list` commands.
- [ ] Use `packages.toml` as the default configuration.
- [ ] Validate masks, package suffixes, and field types.
- [ ] Project the tree with inherited masks and explicit overrides.
- [ ] Mount external files without moving or tracking them.
- [ ] Preserve package and group sources when merging declarations.
- [ ] Check dependencies without enabling excluded nodes.
- [ ] Test overrides, mounts, cycles, conflicts, and CLI failures.
- [ ] Document the format and verify the local declarations.

## Phase 2: Installed state

- [ ] Read package groups and installed state through pacman.
- [ ] Report missing, dependency-installed, and undeclared packages.
- [ ] Account for providers and distinguish orphans from explicit packages.
- [ ] List, explain, and search packages.
- [ ] Offer plain package-name output for shell pipelines.

## Phase 3: Declaration editing

- [ ] Adopt installed packages into a selected file and subtree.
- [ ] Default adoption to the current device.
- [ ] Preview edits and preserve comments and formatting.
- [ ] Keep private declarations in their chosen external files.

## Boundaries

- Device bits are personal=4, laboratory=2, laptop=1.
- Explicit masks replace inherited masks; excluded parents do not stop traversal.
- Dependencies are constraints, not selection rules.
- External files remain external; plain package lists inherit their mount mask.
- Phase 1 performs no package-manager queries or system changes.
- Installation and removal remain the responsibility of pacman or paru.
