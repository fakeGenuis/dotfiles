#!/usr/bin/env fish
# This file acts like ~/.profile and ~/.pam_enviroments in bash

if status is-login
    # fcitx
    set -gx GTK_IM_MODULE fcitx
    set -gx QT_IM_MODULE fcitx
    set -gx XMODIFIERS @im=fcitx
    set -gx SDL_IM_MODULE fcitx
    set -gx INPUT_METHOD fcitx

    # https://wiki.archlinux.org/title/HiDPI
    # set -gx QT_AUTO_SCREEN_SCALE_FACTOR 1
    set -gx QT_QPA_PLATFORMTHEME qt5ct
    set -gx VISUAL "emacsclient -c -a ''"
    set -gx EDITOR nvim
end
