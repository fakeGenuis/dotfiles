# Defined in - @ line 1
function wslProxy --description "Set wsl use windows host proxy"
    switch $argv[1]
        case status
            ps aux | grep ssh
        case on
            sudo subsystemctl start && sudo subsystemctl exec /usr/bin/sshd && git-bash.exe -c "ssh -R 8889:localhost:8889 -fCN wsl"
        case off
            git-bash.exe -c "kill `ps aux | awk '/ssh/ {print $1}'`"
    end
end
