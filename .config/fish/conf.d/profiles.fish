#!/usr/bin/env fish
# This file acts like ~/.profile and ~/.pam_enviroments in bash

if status is-login
    # fcitx
    set -gx GTK_IM_MODULE fcitx
    set -gx QT_IM_MODULE fcitx
    set -gx XMODIFIERS @im=fcitx
    set -gx SDL_IM_MODULE fcitx
    set -gx INPUT_METHOD fcitx

    set -gx QT_QPA_PLATFORMTHEME qt6ct
    set -gx VISUAL "emacsclient -c -a= -F '((height . 50) (width . 150))'"
    set -gx EDITOR nvim

    # bat related
    set -gx MANROFFOPT -c
    set -gx MANPAGER "sh -c 'col -bx | bat -l man -p'"
end

if status is-interactive
    # colored password prompt
    # not work in ~status is-login~, error "tput: No value for $TERM and no -T specified"
    set -gx SUDO_PROMPT "$(tput setaf 1 bold)""[sudo]$(tput sgr0)" \
        "$(tput setaf 6)password for$(tput sgr0) $(tput setaf 5)%p$(tput sgr0): "
end
