# Defined in - @ line 1
function FreqCommand --wraps=history\ \|\ awk\ \'\{print\ \$4\}\'\ \|\ sort\ \|\ uniq\ -c\ \|\ sort\ -rn\ \|\ head --wraps=history\ \|\ awk\ \'\{print\ \$1\}\'\ \|\ sort\ \|\ uniq\ -c\ \|\ sort\ -rn\ \|\ head --description alias\ FreqCommand=history\ \|\ awk\ \'\{print\ \$1\}\'\ \|\ sort\ \|\ uniq\ -c\ \|\ sort\ -rn\ \|\ head
  history | awk '{print $1}' | sort | uniq -c | sort -rn | head $argv;
end
