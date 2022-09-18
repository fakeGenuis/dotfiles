#!/usr/bin/env fish

# English fonts
set -a 2install ttf-sarasa-ui-sc adobe-source-serif-fonts
# Monospace fonts
set -a 2install nerd-fonts-fira-code
# TODO download MononokiLiga Nerd Font Mono from a git repository

if [ (yadm config --get local.class) = personal ]
    # Chinese fonts
    set -a 2install ttf-lxgw-wenkai ttf-kose-git
end

paru -S --needed --noconfirm $2install
