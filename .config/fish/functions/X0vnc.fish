#!/usr/bin/env fish

function X0vnc --description "x0vnc on, off or show status"
    switch "$argv[1]"
        case on
            pgrep x0vnc >/dev/null && begin
                echo "a x0vncserver already running!!"
                X0vnc status
            end || begin
                tmux has-session -t vnc || tmux new-session -t vnc -d
                tmux attach -t vnc\; new-window 'x0vncserver -rfbauth ~/.vnc/passwd -display :0 -localhost -rfbport 50114 -AlwaysShared'\; detach
            end
        case off
            pkill x0vncserver
        case status
            pgrep -a x0vncserver
    end
end
