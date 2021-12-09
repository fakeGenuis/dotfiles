set -gx STARSHIP_CONFIG ~/.config/starship/config.toml
starship init fish | source

# emacs vterm shell-side configuration
if test "$INSIDE_EMACS" = vterm -a -f "$EMACS_VTERM_PATH/etc/emacs-vterm.fish"
    source "$EMACS_VTERM_PATH/etc/emacs-vterm.fish"
    function fish_title
        echo (status current-command) ':' (pwd)
    end
    function e
        emacsclient $argv
    end
end

function fish_greeting
end

# https://wiki.archlinux.org/title/Ranger#Preventing_nested_ranger_instances
# not safe when inside tmux, $RANGER_LEVEL == 1, tmux bug? 
# function ranger
#     if test -n "$RANGER_LEVEL"
#         echo -n "You are in ranger level "; set_color red; echo "$RANGE_LEVEL"; set_color normal;
#     end
#     /usr/bin/ranger "$argv"
# end

# https://www.emacswiki.org/emacs/TrampMode
# https://stackoverflow.com/a/37421917
# fish with tramp
if test "$TERM" = dumb
    function fish_prompt
        echo "\$ "
    end
end
