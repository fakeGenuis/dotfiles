#!/usr/bin/env fish

if string match -qri wsl (uname -a)
    # if no $DISPLAY export, wslg (windows official) is used
    set -gx DISPLAY (cat /etc/resolv.conf | grep nameserver | awk '{print $2; exit;}'):0.0 #GWSL
    # set -gx PULSE_SERVER tcp:(cat /etc/resolv.conf | grep nameserver | awk '{print $2; exit;}') #GWSL
    set -gx LIBGL_ALWAYS_INDIRECT 1 #GWSL
    set -gx GDK_SCALE 2 #GWSL
    set -gx QT_SCALE_FACTOR 2 #GWSL
    # proxy in wsl (set listen on 0.0.0.0 on windows proxy software)
    set -gx ALL_PROXY (cat /etc/resolv.conf | grep nameserver | awk '{ print $2 }'):8883
    # emacsclient -e 1 &>/dev/null || env LC_CTYPE='zh_CN.UTF-8' emacs --daemon &
end
