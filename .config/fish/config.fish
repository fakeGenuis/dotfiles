# https://www.emacswiki.org/emacs/TrampMode
# https://stackoverflow.com/a/37421917
# fish with tramp
if test "$TERM" = dumb
    function fish_prompt
        echo "\$ "
    end
    return
end

set -g fish_greeting

# GPG ssh agent
if not set -q SSH_AUTH_SOCK
    set -gx SSH_AUTH_SOCK (gpgconf --list-dirs agent-ssh-socket)
end
if status is-interactive; and isatty stdin
    set -gx GPG_TTY (tty)
    # Preserve GUI pinentry routing; background shells must not redirect it.
    if set -q DISPLAY; and test -n "$DISPLAY"
        gpg-connect-agent updatestartuptty /bye >/dev/null
    end
end

if status is-interactive
    # Commands to run in interactive sessions can go here
    zoxide init fish | source
    starship init fish | source
    direnv hook fish | source
end

# emacs vterm shell-side configuration
if test "$INSIDE_EMACS" = vterm -a -f "$EMACS_VTERM_PATH/etc/emacs-vterm.fish"
    set -gx TERM xterm-256color
    source "$EMACS_VTERM_PATH/etc/emacs-vterm.fish"
    # reset PAGER, (=cat in emacs 31)
    # https://github.com/akermu/emacs-libvterm/issues/745
    set -e PAGER
end
