# Defined in - @ line 1
function wslProxy --description "Set wsl use windows host proxy"
    switch $argv[1]
        case status
            pgrep -af ssh
        case on
            pgrep sshd 2&>/dev/null || sudo /usr/bin/sshd && git-bash.exe -c "ssh -R 8889:localhost:8883 -fCN wsl"
        case off
            git-bash.exe -c "kill `ps aux | awk '/ssh/ {print $1}'`"
    end
end
