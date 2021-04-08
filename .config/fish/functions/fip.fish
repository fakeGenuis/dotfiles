function fip --description "copy absolute path of file to clipboard"
  if not set -q argv[1]
    set fp $PWD
  else
    if not test -e "$argv[1]"
      echo File not exist!
      return
    end
    set fp (realpath "$argv[1]")
  end
  echo -n $fp | xsel -b
  echo $fp
end

