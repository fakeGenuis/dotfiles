# Defined in - @ line 1
function GetMyIP --wraps='curl -L tool.lu/ip' --description 'alias GetMyIP=curl -L tool.lu/ip'
    curl -L ip.tool.lu $argv
end
