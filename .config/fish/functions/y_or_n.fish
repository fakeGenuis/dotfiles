#!/usr/bin/env fish

# https://stackoverflow.com/a/29436423
function y_or_n --description "read yes or no with prompt and message"
    while true
        read -p "set_color green; echo -n "$argv" 'yes or no[y/n]:'; set_color normal;" yn
        switch "$yn"
            case y Y
                return 0
            case n N
                set_color red
                echo "Aborted!"
                set_color normal
                return 1
            case "*"
                set_color yellow
                echo -e "Wrong input!\n"
                set_color normal
        end
    end
end
