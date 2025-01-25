#!/usr/bin/env fish

if status is-login; and string match -qri wsl (uname -a)
    # if no $DISPLAY export, wslg (windows official) is used
    # set -gx DISPLAY (cat /etc/resolv.conf | grep nameserver | awk '{print $2; exit;}'):0.0 #GWSL
    # set -gx PULSE_SERVER tcp:(cat /etc/resolv.conf | grep nameserver | awk '{print $2; exit;}') #GWSL
    set -gx LIBGL_ALWAYS_INDIRECT 1 #GWSL
    set -gx GDK_SCALE 2 #GWSL
    set -gx QT_SCALE_FACTOR 2 #GWSL
    # proxy in wsl (set network mode to mirrored solves everything!)
    # now ALL_PROXY can be a fixed environment variable
end
