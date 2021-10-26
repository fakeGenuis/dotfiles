function cfp --description "copy absolute or related path of file to clipboard"
    switch "$argv[1]"
        case "-h"
            echo "Usage: cfp [OPTIONS] path
copy path (absolute or related) of file to clipboard, copied content is also printed on screen

[Options]
    -a        copy absolute path, get $PWD with empty argv[2]
    -h        print help message
    -r        copy file path with respect to current directory
    -r.       same to -r, but add ./ if not start with
    default   same to -r, but replace $HOME with ~

    "
            return 0
        case "-a"
            set rdir "/"
            set prefix "/"
        case "-r"
            set rdir "."
            set prefix ""
        case "-r."
            set rdir "."
            set prefix "./"
        case "*"
            set rdir "$HOME"
            set prefix "~/"
    end
    if test -z $argv[2]
        if test -z $argv[1]
            set file "$PWD"
        else
            set file $argv[1]
        end
    else
        set file $argv[2]
    end
    if not test -e "$file"
        set_color red; echo !!! File "\"$file\"" not exist!; set_color normal;
        return 1
    end

    set fp "$prefix"(realpath "$file" --relative-to="$rdir")
    echo -n "$fp" | xsel -b
    set_color blue; echo -n "\"$fp\" "; set_color normal; echo copied to system clipboard!

    return 0
end
