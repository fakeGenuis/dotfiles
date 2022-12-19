#!/usr/bin/env bash
install="paru -S --needed --noconfirm"
to_install=()

# English fonts
to_install+=(ttf-sarasa-ui-sc adobe-source-serif-fonts)
# to_install+=(gentium-plus-font)

# Monospace fonts
to_install+=(ttf-firacode-nerd)
# to_install+=(ttf-bqn386-git ttf-recursive)

# TODO download MononokiLiga Nerd Font Mono from a git repository
#

# Chinese fonts
to_install+=(wqy-microhei ttf-lxgw-wenkai ttf-kose-git)
# to_install+=(ttf-arphic-ukai)

"$install" "${to_install[@]}"
