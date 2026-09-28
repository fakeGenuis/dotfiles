#!/usr/bin/env python3
"""Read package declarations without querying pacman."""

import argparse
from graphlib import TopologicalSorter
import json
from pathlib import Path
import sys
import tomllib


def load_tree(filename):
    path = Path(filename).resolve()
    data = tomllib.loads(path.read_text())
    profiles = data.pop("profiles")
    bits = list(profiles.values())
    if len(set(bits)) != len(bits) or any(type(b) is not int or b <= 0 or b & (b - 1) for b in bits):
        raise ValueError("profiles must assign a distinct single bit to each device")
    all_bits = sum(bits)

    def load_file(path, data, inherited, mount, stack):
        if path in stack:
            raise ValueError(f"File cycle: {path}")
        scope = {}

        def read_node(table, inherited, local):
            name = ".".join(part for part in (mount, local) if part)
            mask = table.get("on", inherited)
            if type(mask) is not int or mask < 0 or mask & ~all_bits:
                raise ValueError(f"{path} [{name}]: invalid on mask: {mask}")
            node = dict(file=str(path), node=name, on=mask,
                        packages=table.get("packages", []), groups=table.get("groups", []),
                        depends_on=table.get("depends_on", []), children=[])
            scope[local] = node
            for key, value in table.items():
                if isinstance(value, dict):
                    child = f"{local}.{key}" if local else key
                    node["children"].append(read_node(value, mask, child))
            if "directory" in table:
                folder = Path(table["directory"]).expanduser()
                target = (path.parent / folder / "packages.toml").resolve()
                if target.exists() or not table.get("optional", False):
                    contents = tomllib.loads(target.read_text())
                    node["children"].append(load_file(target, contents, mask, name, (*stack, path)))
            return node

        root = read_node(data, inherited, "")
        for name, node in scope.items():
            missing = set(node["depends_on"]) - scope.keys()
            if missing:
                raise ValueError(f"{path} [{name}]: unknown dependencies: {', '.join(sorted(missing))}")
        TopologicalSorter({name: node["depends_on"] for name, node in scope.items()}).prepare()
        for node in scope.values():
            node["depends_on"] = [scope[name] for name in node["depends_on"]]
        return root

    root = load_file(path, data, all_bits, "", ())
    root["profiles"] = profiles
    return root


def project(root, profile):
    if profile not in root["profiles"]:
        raise ValueError(f"Unknown profile: {profile}; choose from {', '.join(root['profiles'])}")
    bit = root["profiles"][profile]
    width = max(root["profiles"].values()).bit_length()

    def visit(node):
        entries = []
        for kind, key in (("package", "packages"), ("group", "groups")):
            for item in node[key]:
                name, mask = item, node["on"]
                if kind == "package" and ":" in item:
                    name, suffix = item.rsplit(":", 1)
                    if len(suffix) != width or set(suffix) - {"0", "1"}:
                        raise ValueError(f"{node['file']} [{node['node']}]: invalid package suffix: {item}")
                    mask = int(suffix, 2)
                if mask & bit:
                    source = dict(file=node["file"], node=node["node"], on=f"0b{mask:0{width}b}")
                    entries.append((kind, name, source))
        for child in node["children"]:
            entries.extend(visit(child))
        # Restored leaves still require their ancestors' dependencies.
        if node["on"] & bit or entries:
            for dependency in node["depends_on"]:
                if not dependency["on"] & bit:
                    raise ValueError(f"{node['file']} [{node['node']}]: {profile}: "
                                     f"dependency excluded: {dependency['node']}")
        return entries

    merged = {}
    for kind, name, source in visit(root):
        sources = merged.setdefault((kind, name), [])
        if source not in sources:
            sources.append(source)
    return [dict(kind=kind, name=name, sources=sources)
            for (kind, name), sources in sorted(merged.items())]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("check", "list"):
        command = commands.add_parser(name)
        command.add_argument("--file", type=Path,
                             default=Path(__file__).resolve().with_name("packages.toml"))
        command.add_argument("--profile", required=name == "list",
                             help="Device name from profiles; check defaults to all devices")
        if name == "list":
            command.add_argument("--json", action="store_true", help="Include declaration sources")
    args = parser.parse_args(argv)
    try:
        root = load_tree(args.file)
        if args.command == "check":
            profiles = [args.profile] if args.profile else list(root["profiles"])
            for profile in profiles:
                project(root, profile)
            print(f"Valid: {', '.join(profiles)}")
        else:
            result = project(root, args.profile)
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                for item in result:
                    print(f"{item['kind']}\t{item['name']}")
    except (OSError, ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
