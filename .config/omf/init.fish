# color themes
set -g theme_date_format "+%a %H:%M"
set -g theme_nerd_fonts yes
set -g theme_color_scheme nord
set -g theme_powerline_fonts yes
set -g theme_title_display_process yes

# emacs vterm shell-side configuration
if test "$INSIDE_EMACS" = 'vterm' -a -f "$EMACS_VTERM_PATH/etc/emacs-vterm.fish"
   source "$EMACS_VTERM_PATH/etc/emacs-vterm.fish"
   function fish_title
       echo (status current-command) ':' (pwd)
   end
end

# https://www.emacswiki.org/emacs/TrampMode
# https://stackoverflow.com/a/37421917
# fish with tramp
if test "$TERM" = "dumb"
    function fish_prompt
        echo "\$ "
    end
end

function fish_greeting; end

function ranger
    if test -z "$RANGER_LEVEL"
        /usr/bin/ranger "$argv"
    else
        exit
    end
end
