# This file acts like ~/.profile and ~/.pam_enviroments in bash

if status is-login
    # set -gx QT_QPA_PLATFORMTHEME qt6ct
    set -gx VISUAL "emacsclient -c -a= -F '((height . 50) (width . 150))'"
    set -gx EDITOR "emacsclient -c -s utility -a= -nw"

    # bat related
    set -gx MANROFFOPT -c
    set -gx MANPAGER "sh -c 'col -bx | bat -l man -p'"

    # Default NET interface Name, /for btop template/
    set -gx DNETN (ip route show default | awk '/default/ {print $5}')
end

if status is-interactive && [ -t 0 ]
    # colored password prompt
    set -gx SUDO_PROMPT (string join '' \
        (set_color --bold red) '[sudo]' (set_color normal) ' ' \
        (set_color cyan) 'password for' (set_color normal) ' ' \
        (set_color magenta) '%p' (set_color normal) ': ')
end
