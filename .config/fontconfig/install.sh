#!/usr/bin/env bash
install=(paru -S --needed --noconfirm)
to_install=()

# English fonts
to_install+=(ttf-sarasa-ui-sc)
# to_install+=(gentium-plus-font)

# Monospace fonts
to_install+=(ttf-firacode-nerd)
# to_install+=(ttf-bqn386-git ttf-recursive)

# TODO download MononokiLiga Nerd Font Mono from a git repository
#

# Chinese fonts
to_install+=(wqy-microhei ttf-lxgw-wenkai ttf-kose-git ttf-arphic-ukai)
# to_install+=()

# icon/emoji/unicode fonts
to_install+=(quivira noto-fonts-emoji ttf-firacode-nerd)

"${install[@]}" "${to_install[@]}"
