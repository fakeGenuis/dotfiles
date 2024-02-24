function GetMyIP --description 'alias GetMyIP=curl -s ipinfo.io | jq'
    curl -s ipinfo.io | jq
end
