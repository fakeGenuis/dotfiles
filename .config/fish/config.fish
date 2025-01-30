# GPG ssh agent
set -gx GPG_TTY (tty)
set -gx SSH_AUTH_SOCK (gpgconf --list-dirs agent-ssh-socket)
gpg-connect-agent updatestartuptty /bye >/dev/null

if status is-interactive
    # Commands to run in interactive sessions can go here
    zoxide init fish | source
    set -gx STARSHIP_CONFIG ~/.config/starship/config.toml
    starship init fish | source
    test -e ~/.cache/wal/sequences && cat ~/.cache/wal/sequences
end

# emacs vterm shell-side configuration
if test "$INSIDE_EMACS" = vterm -a -f "$EMACS_VTERM_PATH/etc/emacs-vterm.fish"
    source "$EMACS_VTERM_PATH/etc/emacs-vterm.fish"
    # reset PAGER, (=cat in emacs 31)
    # https://github.com/akermu/emacs-libvterm/issues/745
    set -e PAGER
    # restore default fish_title
    source "/usr/share/fish/functions/fish_title.fish"
    function e --wraps=emacsclient --description 'alias e=emacsclient'
        emacsclient $argv
    end
end

# `neofetch` as fish greeting
function fish_greeting
end

# https://www.emacswiki.org/emacs/TrampMode
# https://stackoverflow.com/a/37421917
# fish with tramp
if test "$TERM" = dumb
    function fish_prompt
        echo "\$ "
    end
end
