#!/usr/bin/env fish
# https://wiki.archlinux.org/title/HiDPI

if status is-login
    set -l reso (xdpyinfo | grep dimension | awk '{print $2}' | cut -d'x' -f1)
    if test $reso -gt 2560
        set -gx GDK_SCALE 2
        set -gx GDK_DPI_SCALE 0.5
        set -gx QT_AUTO_SCREEN_SCALE_FACTOR 1
    end
end
