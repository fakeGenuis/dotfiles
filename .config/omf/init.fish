set -gx STARSHIP_CONFIG ~/.config/starship/config.toml
starship init fish | source

# emacs vterm shell-side configuration
if test "$INSIDE_EMACS" = vterm -a -f "$EMACS_VTERM_PATH/etc/emacs-vterm.fish"
    source "$EMACS_VTERM_PATH/etc/emacs-vterm.fish"
    function fish_title
        echo (status current-command) ':' (pwd)
    end
end

function fish_greeting
end

function ranger
    if test -z "$RANGER_LEVEL"
        /usr/bin/ranger "$argv"
    else
        exit
    end
end

# https://www.emacswiki.org/emacs/TrampMode
# https://stackoverflow.com/a/37421917
# fish with tramp
if test "$TERM" = dumb
    function fish_prompt
        echo "\$ "
    end
end
