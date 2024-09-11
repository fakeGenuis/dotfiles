#!/bin/bash

pkill -9 picom
pkill -9 redshift
source ~/.config/awesome/scripts/screensaver.sh
run openrgb --noautoconnect -m off
