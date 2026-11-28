set -l _gen /usr/lib/systemd/user-environment-generators/30-systemd-environment-d-generator
if not set -q __ENV_D_LOADED; and test -x $_gen
    for line in ($_gen)
        set -l kv (string split -m 1 '=' -- $line)
        set -l val (string unescape -- $kv[2])
        if test "$kv[1]" = PATH
            set -gx PATH (string split ':' -- $val)
        else if not set -q $kv[1]
            set -gx $kv[1] $val
        end
    end
    set -gx __ENV_D_LOADED 1
end
