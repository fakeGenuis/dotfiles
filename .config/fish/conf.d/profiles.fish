#!/usr/bin/env fish
# This file acts like ~/.profile and ~/.pam_enviroments in bash

if status is-login
    # fcitx
    set -gx GTK_IM_MODULE fcitx
    set -gx QT_IM_MODULE fcitx
    set -gx XMODIFIERS @im=fcitx
    set -gx SDL_IM_MODULE fcitx
    set -gx INPUT_METHOD fcitx

    set -gx QT_QPA_PLATFORMTHEME qt5ct
    set -gx VISUAL emacsclient -c -a \"\"
    set -gx EDITOR nvim
end
