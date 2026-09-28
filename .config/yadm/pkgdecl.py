#!/usr/bin/env python3
"""Read and validate package declarations without querying pacman."""

import argparse
import json
import re
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path


PROFILES = {"personal": 4, "laboratory": 2, "laptop": 1}
FIELDS = {"title", "on", "packages", "groups", "depends_on", "directory",
          "optional", "enable_default"}


class DeclarationError(ValueError):
    """Invalid or incomplete declarations."""


@dataclass(frozen=True)
class Source:
    file: Path
    node: str

    def __str__(self):
        return f"{self.file} [{self.node or '<root>'}]"


@dataclass(frozen=True)
class Entry:
    kind: str
    name: str
    mask: int
    source: Source


@dataclass(eq=False)
class Node:
    source: Source
    mask: int
    entries: list[Entry] = field(default_factory=list)
    children: list["Node"] = field(default_factory=list)
    dependencies: list["Node"] = field(default_factory=list)


def fail(source, message):
    raise DeclarationError(f"{source}: {message}")


def strings(value, source, name):
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item or item.strip() != item
        for item in value
    ):
        fail(source, f"{name} must be a list of nonempty strings")
    return value


def load_tree(filename: Path) -> Node:
    """Mount files into one tree; resolve dependencies within each source file."""

    def load_file(path, inherited, mount, stack):
        path = path.resolve()
        if path in stack:
            chain = " -> ".join(str(p) for p in (*stack, path))
            raise DeclarationError(f"File cycle: {chain}")
        try:
            with path.open("rb") as stream:
                data = tomllib.load(stream)
        except (OSError, ValueError) as exc:
            raise DeclarationError(f"{path}: {exc}") from exc

        scope = {}
        references = []

        def read_node(table, parent_mask, local_path):
            node_path = ".".join(part for part in (mount, local_path) if part)
            source = Source(path, node_path)
            mask = table.get("on", parent_mask)
            if type(mask) is not int or not 0 <= mask <= 7:
                fail(source, "on must be an integer mask from 0 to 7")
            for key, value in table.items():
                if key not in FIELDS and not isinstance(value, dict):
                    fail(source, f"Unknown field: {key}")
            if "title" in table and not isinstance(table["title"], str):
                fail(source, "title must be a string")
            # Existing external files use this inert header.
            if "enable_default" in table and table["enable_default"] is not True:
                fail(source, "Only legacy enable_default=true is supported; use on")
            optional = table.get("optional", False)
            if type(optional) is not bool or ("optional" in table and "directory" not in table):
                fail(source, "optional must be a boolean on a directory mount")

            node = Node(source, mask)
            if local_path in scope:
                fail(source, "Ambiguous node path; do not use dots inside node names")
            scope[local_path] = node
            for kind, key in (("package", "packages"), ("group", "groups")):
                for item in strings(table.get(key, []), source, key):
                    name, item_mask = item, mask
                    if kind == "package" and ":" in item:
                        name, suffix = item.rsplit(":", 1)
                        if not re.fullmatch(r"[01]{3}", suffix):
                            fail(source, f"Invalid package suffix: {item}")
                        item_mask = int(suffix, 2)
                    if not name or ":" in name or any(c.isspace() for c in name):
                        fail(source, f"Invalid {kind} name: {item}")
                    node.entries.append(Entry(kind, name, item_mask, source))
            deps = strings(table.get("depends_on", []), source, "depends_on")
            references.append((node, deps))

            for key, value in table.items():
                if key not in FIELDS:
                    if not key or "." in key:
                        fail(source, "Node names must be nonempty and contain no dots")
                    child_path = f"{local_path}.{key}" if local_path else key
                    node.children.append(read_node(value, mask, child_path))

            if "directory" in table:
                directory = table["directory"]
                if not isinstance(directory, str) or not directory.strip():
                    fail(source, "directory must be a nonempty string")
                folder = Path(directory).expanduser()
                if not folder.is_absolute():
                    folder = path.parent / folder
                target = folder / "packages.toml"
                if optional and not target.exists():
                    return node
                node.children.append(load_file(target, mask, node_path, (*stack, path)))
            return node

        root = read_node(data, inherited, "")
        for node, names in references:
            for name in names:
                if name not in scope:
                    fail(node.source, f"Unknown dependency: {name}")
                node.dependencies.append(scope[name])
        return root

    root = load_file(Path(filename), 7, "", ())
    validate_cycles(root)
    return root


def walk(root):
    yield root
    for child in root.children:
        yield from walk(child)


def validate_cycles(root):
    done, active = set(), []

    def visit(node):
        if node in active:
            chain = " -> ".join(str(n.source) for n in active + [node])
            raise DeclarationError(f"Dependency cycle: {chain}")
        if node in done:
            return
        active.append(node)
        for dependency in node.dependencies:
            visit(dependency)
        active.pop()
        done.add(node)

    for node in walk(root):
        visit(node)


def project(root: Node, profile: str) -> list[Entry]:
    """Select leaves and enforce constraints along their ancestor paths."""
    bit = PROFILES[profile]

    def visit(node):
        entries = [entry for entry in node.entries if entry.mask & bit]
        for child in node.children:
            entries.extend(visit(child))
        # A re-enabled descendant still needs its ancestor's constraints.
        if node.mask & bit or entries:
            for dependency in node.dependencies:
                if not dependency.mask & bit:
                    fail(node.source, f"{profile}: dependency excluded: {dependency.source}")
        return entries

    return visit(root)


def summarize(entries):
    """Merge names while retaining every selected declaration source."""
    merged = {}
    for entry in entries:
        sources = merged.setdefault((entry.kind, entry.name), [])
        source = {"file": str(entry.source.file), "node": entry.source.node,
                  "on": f"0b{entry.mask:03b}"}
        if source not in sources:
            sources.append(source)
    return [{"kind": kind, "name": name, "sources": sources}
            for (kind, name), sources in sorted(merged.items())]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (("check", "Validate declarations"),
                            ("list", "List selected package and group declarations")):
        command = commands.add_parser(name, help=help_text)
        command.add_argument("--file", type=Path,
                             default=Path(__file__).resolve().with_name("packages.toml"))
        command.add_argument("--profile", choices=PROFILES, required=name == "list",
                             help="Device profile; check defaults to all profiles")
        if name == "list":
            command.add_argument("--json", action="store_true", help="Include declaration sources")
    args = parser.parse_args(argv)
    try:
        root = load_tree(args.file)
        if args.command == "check":
            profiles = [args.profile] if args.profile else list(PROFILES)
            for profile in profiles:
                project(root, profile)
            print(f"Valid: {', '.join(profiles)}")
        else:
            result = summarize(project(root, args.profile))
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                for item in result:
                    print(f"{item['kind']}\t{item['name']}")
    except DeclarationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
