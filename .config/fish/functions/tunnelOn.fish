#!/usr/bin/env fish

# Defined in - @ line 1
function ssh_forward
    set -l host "$argv[1]"
    set -l port "$argv[2]"
    set -l name "$argv[3]"
    set -l pid (pgrep -a ssh | grep "$host" | grep "$port" | cut -d' ' -f1)
    if test -n "$pid"
        set_color red
        echo "An ssh tunnel of $name is already on!"
        set_color normal
        y_or_n "close it\?" && kill "$pid"
    else
        ssh -fCN "$host" -L "$port":localhost:"$port"
    end
end

function tunnelOn --description "toggle status of ssh to server"
    switch "$argv[1]"
        case -grasp
            ssh_forward "$argv[2]" 3664 grasp
        case -vnc
            ssh_forward "$argv[2]" 5014 vnc
        case -proxy
            ssh_forward "$argv[2]" 8889 proxy
        case -h
            echo "Usage: tunnelOn [Options] sshName
toggle on ssh port forward for services

[Options]
    -h              print help message
    -grasp          grasp service, use local port 3664
    -vnc            vnc service, use local port 5014
    -proxy          proxy service, use local port 8889
    "
    end
end
