# Defined via `source`
function e --wraps=emacsclient --description 'alias e=emacsclient'
    emacsclient -c -a emacs $argv
end
