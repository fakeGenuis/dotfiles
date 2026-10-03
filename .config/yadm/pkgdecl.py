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
            node = dict(file=str(path), node=name, local=local, on=mask,
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


def pacman(*args):
    result = subprocess.run(["pacman", *args], capture_output=True, text=True,
                            env={**os.environ, "LC_ALL": "C"})
    if result.returncode:
        raise ValueError(result.stderr.strip() or f"pacman {' '.join(args)} failed")
    return result.stdout


def installed_packages():
    packages = {}
    for block in pacman("-Qi").strip().split("\n\n"):
        fields = {}
        for line in block.splitlines():
            if line.startswith(" "):
                fields[key] += " " + line.strip()
            else:
                key, value = line.split(":", 1)
                key = key.strip()
                fields[key] = value.strip()
        def words(key):
            return [] if fields[key] == "None" else fields[key].split()
        name = fields["Name"]
        packages[name] = dict(name=name, installed=True, version=fields["Version"],
                              description=fields["Description"],
                              reason="explicit" if fields["Install Reason"].startswith("Explicit") else "dependency",
                              provides=[re.split("[<>=]", p)[0] for p in words("Provides")],
                              required_by=words("Required By"), optional_for=words("Optional For"))
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

    line(headers, "1;36")
    for row in rows:
        state = "missing" if "missing" in row else "dependency" if "dependency" in row else row[-1]
        line(row, {"missing": "31", "undeclared": "33", "dependency": "36", "declared": "32"}.get(state, "0"))


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


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("check", "list", "status", "missing", "undeclared", "explain"):
        command = commands.add_parser(name)
        command.add_argument("--file", type=Path,
                             default=Path(__file__).resolve().with_name("packages.toml"))
        command.add_argument("--profile",
                             help="Device name from profiles; defaults to yadm local.class "
                                  "(check defaults to all devices)")
        if name != "check":
            output = command.add_mutually_exclusive_group()
            output.add_argument("--json", action="store_true", help="Include declaration sources")
            output.add_argument("--names", action="store_true", help="Print package names only")
        if name == "undeclared":
            command.add_argument("--all", action="store_true", help="Include dependency-installed packages")
        if name == "explain":
            command.add_argument("query", help="Package name")
    args = parser.parse_args(argv)
    try:
        if args.profile is None and args.command != "check":
            args.profile = local_profile()
        root = load_tree(args.file)
        if args.command == "check":
            profiles = [args.profile] if args.profile else list(root["profiles"])
            for profile in profiles:
                project(root, profile)
            print(f"Valid: {', '.join(profiles)}")
            return 0
        result = project(root, args.profile)
        if args.command == "list":
            if args.names:
                for name in sorted(expand_groups(result)):
                    print(name)
                return 0
        else:
            result = compare(expand_groups(result), installed_packages())
            filters = {
                "status": lambda r: r["reason"] == "explicit" or r["declared"],
                "missing": lambda r: not r["installed"],
                "undeclared": lambda r: r["installed"] and not r["declared"]
                    and (args.all or r["reason"] == "explicit"),
                "explain": lambda r: args.query == r["name"] or args.query in r["declarations"],
            }
            result = [row for row in result if filters[args.command](row)]
            if args.command == "explain" and not result:
                raise ValueError(f"Package not installed or declared: {args.query}")
        if args.json:
            print(json.dumps(result, indent=2))
        elif not args.names and args.command != "explain":
            if args.command == "list":
                print_table(("PACKAGE", "KIND"), [(item["name"], item["kind"]) for item in result])
            else:
                print_table(("PACKAGE", "REASON", "DECLARATION"), [
                    (item["name"], item["reason"], "declared" if item["declared"] else "undeclared")
                    for item in result])
        else:
            for item in result:
                if args.names:
                    print(item["name"])
                elif args.command == "explain":
                    print(item["name"])
                    for key, value in item.items():
                        if key == "sources":
                            for source in value:
                                group = f" (group: {source['group']})" if "group" in source else ""
                                print(f"  source: {source['file']} [{source['node']}] {source['on']}{group}")
                        elif key != "name":
                            print(f"  {key}: {', '.join(value) if isinstance(value, list) else value}")
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130
    except (OSError, ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
