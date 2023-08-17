#!/usr/bin/env python3

import tomli, sys, os

with open("packages.toml", "rb") as f:
    conf = tomli.load(f)
default = conf["enable_default"]


def install() -> list:
    """Get all packages needed to be installed."""
    all_install = []
    for module in conf:
        if type(conf[module]) is dict and (conf[module].get("enabled", default)):
            all_install += conf[module]["packages"]
    return all_install


def remove() -> list:
    """Get packages already installed but not owned by any module"""
    if not os.path.isfile("installed"):
        return []

    with open("installed", "r") as f:
        installed = [line.rstrip() for line in f.readlines()]

    return [package for package in installed if package not in install()]


if len(sys.argv) > 1 and sys.argv[1] == "--remove":
    print("\n".join(remove()))
else:
    print("\n".join(install()))
