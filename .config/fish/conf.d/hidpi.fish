#!/usr/bin/env fish
# https://wiki.archlinux.org/title/HiDPI

if status is-login; and test -n "$DISPLAY"
    set XDPI (xdpyinfo | grep resolution | awk '{print $2}' | cut -d'x' -f1)
    # fractional scaled dpi (1.25, 1.5, ., 2) x 96
    set -gx XDPI (echo "scale=0; ($XDPI + 12)/24*24" | bc -l)
    set -gx QT_AUTO_SCREEN_SCALE_FACTOR 1
    set -gx QT_ENABLE_HIGHDPI_SCALING 1
    # GDK should aware `Xft.dpi'
    if test "$XDPI" -gt 144
        # GDK 3 not support fractional scaling
        set -gx GDK_SCALE 2
        set -gx GDK_DPI_SCALE 0.5
    end
end
