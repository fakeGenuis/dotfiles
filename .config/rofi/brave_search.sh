#!/usr/bin/env bash
# TODO maybe support for live suggestion?

SEARCH_QUERY="https://search.brave.com/search?q="
BROWSER=librewolf

# get default profile name of librewolf
DEFAULT_PROFILE=$(grep 'Default' ~/.librewolf/profiles.ini | cut -d'=' -f2 | cut -d'.' -f2 | tail -1)

# rofi-script mode, use this with
# =rofi -show search -modi 'search: ./brave_search.sh'=
if [[ $ROFI_RETV = '0' ]]; then
    printf "\x00prompt\x1f"
else
    if [[ -z "$ROFI_INFO" ]]; then
        "$BROWSER" -p "$DEFAULT_PROFILE" "$SEARCH_QUERY${1/ /+}"
    fi
fi

# dmenu mode, use this with
# =./brave_search.sh=
# keywords=$(rofi -dmenu -l 7 -theme-str 'textbox-prompt-colon {str: "󰜏"; padding: 0.2em 0.4em;}' -theme-str 'entry {placeholder: "Search with brave...";}')
# if [[ -n $keywords ]]; then
#     "${BROWSER[@]}" "$SEARCH_QUERY${keywords/ /+}"
# fi
