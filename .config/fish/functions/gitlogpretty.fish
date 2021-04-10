# Defined in - @ line 1
function gitlogpretty --description "pretty format of git log"
  git log --graph --pretty='%Cred%h%Creset -%C(auto)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset' --all $argv;
end
