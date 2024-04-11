#!/usr/bin/env fish
# https://wiki.archlinux.org/title/HiDPI

if status is-login; and test -n "$DISPLAY"
    set XDPI (xdpyinfo | grep resolution | awk '{print $2}' | cut -d'x' -f1)
    # fractional scaled dpi (1.25, 1.5, ., 2) x 96
    set -gx XDPI (echo "scale=0; 24*($XDPI/24 + 1)/1" | bc)
    if test "$XDPI" -gt 144
        set -gx GDK_SCALE 2
        set -gx GDK_DPI_SCALE 0.5
        set -gx QT_AUTO_SCREEN_SCALE_FACTOR 1
    end
end
