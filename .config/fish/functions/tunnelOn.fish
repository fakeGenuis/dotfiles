#!/usr/bin/env fish

# Defined in - @ line 1
function tunnelOn --description "change status of ssh to server"
    switch "$argv[1]"
        case grasp
            ssh -fCN $argv[2] -L 3664:localhost:3664
        case vnc
            ssh -fCN $argv[2] -L 5014:localhost:50114
        case off
            kill (ps aux | grep ssh | awk '/PRD/ {print $2}')
    end
end
