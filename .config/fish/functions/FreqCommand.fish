# Defined in - @ line 1
function FreqCommand --description "Get frequently used command"
  history | awk '{print $1}' | sort | uniq -c | sort -rn | head $argv;
end
