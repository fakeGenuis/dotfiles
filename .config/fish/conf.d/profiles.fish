# This file acts like ~/.profile and ~/.pam_enviroments in bash

if status is-interactive
    set -gx MANROFFOPT -c
    set -gx MANPAGER "sh -c 'col -bx | bat -l man -p'"
end

if status is-interactive && [ -t 0 ]
    # colored password prompt
    set -gx SUDO_PROMPT (string join '' \
        (set_color --bold red) '[sudo]' (set_color normal) ' ' \
        (set_color cyan) 'password for' (set_color normal) ' ' \
        (set_color magenta) '%p' (set_color normal) ': ')
end
