#!/usr/bin/fish
#
function swapfile --description "swap two file name"
    set usage "Usage: swapfile [Option] [file1] [file2]

    swap two files' name

    -s          swap with root privilege"

    if test "$argv[1]" = -s
        set smv sudo mv && set argv $argv[2..-1]
    else
        set smv mv
    end

    if test (count $argv) -ne 2
        echo "$usage"
    else
        set TEMPFILE .tmp.file
        echo "swap files' name: $argv[1] <-> $argv[2]"
        $smv "$argv[1]" $TEMPFILE && $smv "$argv[2]" "$argv[1]" && $smv $TEMPFILE "$argv[2]"
    end
end
