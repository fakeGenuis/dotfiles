#!/usr/bin/env fish

# Defined in - @ line 1
function tunnelOn --description "toggle status of ssh to server"
    switch "$argv[1]"
        case -grasp
            set -l pid (pgrep -a ssh | grep "$argv[2]" | grep 3664 | cut -d' ' -f1)
            if test -n "$pid"
                set_color red
                echo "An ssh tunnel of grasp is already on!"
                set_color normal
                y_or_n "close it\?" && kill "$pid"
            else
                ssh -fCN "$argv[2]" -L 3664:localhost:3664
            end
        case -vnc
            set -l pid (pgrep -a ssh | grep "$argv[2]" | grep 5014 | cut -d' ' -f1)
            if test -n "$pid"
                set_color red
                echo "An ssh tunnel of vnc is already on!"
                set_color normal
                y_or_n "close it\?" && kill "$pid"
            else
                ssh -fCN "$argv[2]" -L 5014:localhost:50114
            end
        case -h
            echo "Usage: tunnelOn [Options] sshName
toggle on ssh port forward for services

[Options]
    -h              print help message
    -grasp          grasp service, use local port 3664
    -vnc            vnc service, use local port 5014
    "
    end
end
