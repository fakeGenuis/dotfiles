#!/usr/bin/env python3
"""Inspect package declarations and local pacman state."""

import argparse
from graphlib import TopologicalSorter
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tomllib


def load_tree(filename):
    path = Path(filename).resolve()
    data = tomllib.loads(path.read_text())
    profiles = data.pop("profiles")
    bits = list(profiles.values())
    invalid_bits = any(type(bit) is not int or bit <= 0 or bit & (bit - 1) for bit in bits)
    if len(set(bits)) != len(bits) or invalid_bits:
        raise ValueError("profiles must assign a distinct single bit to each device")

    all_bits = sum(bits)
    root = load_declaration_file(path, data, all_bits, all_bits)
    root["profiles"] = profiles
    return root


def load_declaration_file(path, data, inherited, all_bits, mount="", stack=()):
    """Read one file; dependency names are resolved only within this file."""
    if path in stack:
        raise ValueError(f"File cycle: {path}")
    scope = {}

    def read_node(table, inherited_mask, local):
        name = ".".join(part for part in (mount, local) if part)
        mask = table.get("on", inherited_mask)
        if type(mask) is not int or mask < 0 or mask & ~all_bits:
            raise ValueError(f"{path} [{name}]: invalid on mask: {mask}")
        node = dict(
            file=str(path), node=name, local=local, on=mask,
            packages=table.get("packages", []), groups=table.get("groups", []),
            depends_on=table.get("depends_on", []), children=[],
        )
        scope[local] = node
        for key, value in table.items():
            if not isinstance(value, dict):
                continue
            child = f"{local}.{key}" if local else key
            node["children"].append(read_node(value, mask, child))

        if "directory" in table:
            mounted = load_mount(table, path, mask, all_bits, name, (*stack, path))
            if mounted is not None:
                node["children"].append(mounted)
        return node

    root = read_node(data, inherited, "")
    resolve_dependencies(scope, path)
    return root


def load_mount(table, source_path, mask, all_bits, name, stack):
    folder = Path(table["directory"]).expanduser()
    target = (source_path.parent / folder / "packages.toml").resolve()
    if not target.exists() and table.get("optional", False):
        return None
    contents = tomllib.loads(target.read_text())
    return load_declaration_file(target, contents, mask, all_bits, name, stack)


def resolve_dependencies(scope, path):
    for name, node in scope.items():
        missing = set(node["depends_on"]) - scope.keys()
        if missing:
            raise ValueError(f"{path} [{name}]: unknown dependencies: {', '.join(sorted(missing))}")
    graph = {name: node["depends_on"] for name, node in scope.items()}
    TopologicalSorter(graph).prepare()
    for node in scope.values():
        node["depends_on"] = [scope[name] for name in node["depends_on"]]


def node_entries(node, bit, width):
    """Select this node's entries, including per-package mask overrides."""
    entries = []
    for kind, key in (("package", "packages"), ("group", "groups")):
        for item in node[key]:
            name, mask = item, node["on"]
            if kind == "package" and ":" in item:
                name, suffix = item.rsplit(":", 1)
                if len(suffix) != width or set(suffix) - {"0", "1"}:
                    raise ValueError(f"{node['file']} [{node['node']}]: invalid package suffix: {item}")
                mask = int(suffix, 2)
            if not mask & bit:
                continue
            source = dict(file=node["file"], node=node["node"], on=f"0b{mask:0{width}b}")
            entries.append((kind, name, source))
    return entries


def project(root, profile):
    if profile not in root["profiles"]:
        raise ValueError(f"Unknown profile: {profile}; choose from {', '.join(root['profiles'])}")
    bit = root["profiles"][profile]
    width = max(root["profiles"].values()).bit_length()

    def visit(node):
        entries = node_entries(node, bit, width)
        for child in node["children"]:
            entries.extend(visit(child))
        # Restored leaves still require their ancestors' dependencies.
        if not (node["on"] & bit or entries):
            return entries
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


def pacman(*args):
    result = subprocess.run(["pacman", *args], capture_output=True, text=True,
                            env={**os.environ, "LC_ALL": "C"})
    if result.returncode:
        raise ValueError(result.stderr.strip() or f"pacman {' '.join(args)} failed")
    return result.stdout


def parse_package_fields(block):
    """Parse one pacman -Qi record, including wrapped field values."""
    fields = {}
    for line in block.splitlines():
        if line.startswith(" "):
            fields[key] += " " + line.strip()
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        fields[key] = value.strip()
    return fields


def package_words(fields, key):
    value = fields[key]
    return [] if value == "None" else value.split()


def installed_packages():
    packages = {}
    for block in pacman("-Qi").strip().split("\n\n"):
        fields = parse_package_fields(block)
        name = fields["Name"]
        explicit = fields["Install Reason"].startswith("Explicit")
        packages[name] = dict(
            name=name,
            installed=True,
            version=fields["Version"],
            description=fields["Description"],
            reason="explicit" if explicit else "dependency",
            provides=[re.split("[<>=]", value)[0]
                      for value in package_words(fields, "Provides")],
            required_by=package_words(fields, "Required By"),
            optional_for=package_words(fields, "Optional For"),
        )
    return packages


def expand_groups(entries):
    groups, packages = {}, {}
    if any(item["kind"] == "group" for item in entries):
        for line in pacman("-Sgg").splitlines():
            group, name = line.split()
            groups.setdefault(group, []).append(name)
    for item in entries:
        names = [item["name"]] if item["kind"] == "package" else groups.get(item["name"], [])
        if not names:
            raise ValueError(f"Unknown repository group: {item['name']}")
        for name in names:
            sources = packages.setdefault(name, [])
            for source in item["sources"]:
                source = dict(source, group=item["name"]) if item["kind"] == "group" else source
                if source not in sources:
                    sources.append(source)
    return packages


def compare(declared, installed):
    rows = {name: dict(info, declarations=[], sources=[]) for name, info in installed.items()}
    providers = {}
    for name, info in installed.items():
        for provided in info["provides"]:
            providers.setdefault(provided, []).append(name)
    for name, sources in declared.items():
        matches = [name] if name in installed else providers.get(name, [])
        if not matches:
            rows[name] = dict(name=name, installed=False, reason="missing", description="",
                              declarations=[name], sources=sources)
        for match in matches:
            rows[match]["declarations"].append(name)
            for source in sources:
                if source not in rows[match]["sources"]:
                    rows[match]["sources"].append(source)
    for row in rows.values():
        row["declared"] = bool(row["declarations"])
        row["orphan"] = (row["reason"] == "dependency"
                         and not row["required_by"] and not row["optional_for"])
    return [rows[name] for name in sorted(rows)]


def print_table(headers, rows):
    widths = [max(len(value) for value in column) for column in zip(headers, *rows)]
    color = sys.stdout.isatty() and "NO_COLOR" not in os.environ and os.environ.get("TERM") != "dumb"

    def line(values, code):
        text = "  ".join(value.ljust(width) for value, width in zip(values, widths)).rstrip()
        print(f"\033[{code}m{text}\033[0m" if color else text)

    colors = {"missing": "31", "undeclared": "33", "dependency": "36", "declared": "32"}
    line(headers, "1;36")
    for row in rows:
        if "missing" in row:
            state = "missing"
        elif "dependency" in row:
            state = "dependency"
        else:
            state = row[-1]
        line(row, colors.get(state, "0"))


def local_profile():
    try:
        result = subprocess.run(["yadm", "config", "--get", "local.class"],
                                capture_output=True, text=True)
    except FileNotFoundError:
        raise ValueError("yadm is not installed; select a profile with --profile NAME") from None
    if result.returncode == 1 or (result.returncode == 0 and not result.stdout.strip()):
        raise ValueError("yadm local.class is not set; run 'yadm config local.class NAME' "
                         "or use --profile NAME")
    if result.returncode != 0:
        raise ValueError(f"Cannot read yadm local.class: {result.stderr.strip()}")
    return result.stdout.strip()


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    # Shared arguments live here; command-specific options stay with their command.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--file", type=Path,
        default=Path(__file__).resolve().with_name("packages.toml"),
        help="Root package declaration file",
    )
    common.add_argument(
        "--profile",
        help="Profile name; check defaults to all profiles, other commands to yadm local.class",
    )

    output = argparse.ArgumentParser(add_help=False)
    formats = output.add_mutually_exclusive_group()
    formats.add_argument("--json", action="store_true", help="Include declaration sources")
    formats.add_argument("--names", action="store_true", help="Print package names only")

    check = commands.add_parser(
        "check", parents=[common], help="Validate declarations",
        description="Validate all profiles, or just the profile selected with --profile.",
    )
    check.set_defaults(handler=check_command)

    listing = commands.add_parser(
        "list", parents=[common, output], help="List selected declarations",
    )
    listing.set_defaults(handler=list_command)

    status = commands.add_parser(
        "status", parents=[common, output], help="Compare declarations with installed packages",
    )
    status.set_defaults(handler=query_command)

    missing = commands.add_parser(
        "missing", parents=[common, output], help="List declarations not installed",
    )
    missing.set_defaults(handler=query_command)

    undeclared = commands.add_parser(
        "undeclared", parents=[common, output], help="List installed packages not declared",
    )
    undeclared.add_argument(
        "--all", action="store_true", help="Include dependency-installed packages",
    )
    undeclared.set_defaults(handler=query_command)

    explain = commands.add_parser(
        "explain", parents=[common, output], help="Show package details and declaration sources",
    )
    explain.add_argument("query", help="Package name")
    explain.set_defaults(handler=query_command)
    return parser


def check_command(args):
    root = load_tree(args.file)
    profiles = [args.profile] if args.profile else list(root["profiles"])
    for profile in profiles:
        project(root, profile)
    print(f"Valid: {', '.join(profiles)}")


def selected_declarations(args):
    profile = args.profile if args.profile is not None else local_profile()
    return project(load_tree(args.file), profile)


def list_command(args):
    entries = selected_declarations(args)
    if args.names:
        # Expand groups for package-manager pipelines.
        for name in sorted(expand_groups(entries)):
            print(name)
        return
    if args.json:
        print(json.dumps(entries, indent=2))
        return
    print_table(("PACKAGE", "KIND"), [(item["name"], item["kind"]) for item in entries])


def filter_packages(rows, args):
    if args.command == "status":
        return [row for row in rows if row["reason"] == "explicit" or row["declared"]]
    if args.command == "missing":
        return [row for row in rows if not row["installed"]]
    if args.command == "undeclared":
        return [row for row in rows
                if row["installed"] and not row["declared"]
                and (args.all or row["reason"] == "explicit")]
    if args.command == "explain":
        matches = [row for row in rows
                   if args.query == row["name"] or args.query in row["declarations"]]
        if not matches:
            raise ValueError(f"Package not installed or declared: {args.query}")
        return matches
    raise ValueError(f"Unknown package query: {args.command}")


def query_command(args):
    declared = expand_groups(selected_declarations(args))
    rows = compare(declared, installed_packages())
    result = filter_packages(rows, args)
    print_packages(result, args)


def print_packages(rows, args):
    if args.json:
        print(json.dumps(rows, indent=2))
        return
    if args.names:
        for row in rows:
            print(row["name"])
        return
    if args.command == "explain":
        for row in rows:
            print_package_details(row)
        return
    table = [
        (row["name"], row["reason"], "declared" if row["declared"] else "undeclared")
        for row in rows
    ]
    print_table(("PACKAGE", "REASON", "DECLARATION"), table)


def print_package_details(package):
    print(package["name"])
    for key, value in package.items():
        if key == "name":
            continue
        if key == "sources":
            for source in value:
                group = f" (group: {source['group']})" if "group" in source else ""
                print(f"  source: {source['file']} [{source['node']}] {source['on']}{group}")
            continue
        text = ', '.join(value) if isinstance(value, list) else value
        print(f"  {key}: {text}")


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        args.handler(args)
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130
    except (OSError, ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
