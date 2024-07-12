#!/usr/bin/env fish

# Defined in - @ line 1
function ssh_forward
    set -l host "$argv[1]"
    set -l name "$argv[2]"
    set -l lport "$argv[3]"
    set -l rport "$argv[4]"
    set -l pid (pgrep -a ssh | grep "$host" | grep "$lport" | cut -d' ' -f1)
    if test -n "$pid"
        set_color red
        echo "An ssh tunnel of $name on $lport is already on!"
        set_color normal
        y_or_n "close it\?" && kill "$pid"
    else
        ssh -fCN "$host" -L "$lport":localhost:"$rport"
    end
end

function tunnelOn --description "toggle status of ssh to server"
    switch "$argv[1]"
        case -grasp
            ssh_forward "$argv[2]" grasp 3664 3664
        case -vnc
            ssh_forward "$argv[2]" vnc 30114 50114
        case -proxy
            ssh_forward "$argv[2]" proxy 8889 8889
        case -ollama
            ssh_forward "$argv[2]" proxy 11434 11434
        case -h
            echo "Usage: tunnelOn [Options] sshName
toggle on ssh port forward for services

[Options]
    -h              print help message
    -grasp          grasp service, use local port 3664
    -vnc            vnc service, use local port 3014
    -proxy          proxy service, use local port 8889
    "
    end
end
