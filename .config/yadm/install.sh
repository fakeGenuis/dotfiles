#!/usr/bin/bash

INSTALLER=(paru -S --needed -)
REMOVER=(paru -Rs -)

./GetPackages.py >installed
./GetPackages.py | "${INSTALLER[@]}"
./GetPackages.py --remove | "${REMOVER[@]}"
