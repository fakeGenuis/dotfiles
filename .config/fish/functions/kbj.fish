function kbj --wraps='kill -9 (jobs | tail -1 | cut -f2)' --description 'alias kbj=kill -9 (jobs | tail -1 | cut -f2)'
  kill -9 (jobs | tail -1 | cut -f2) $argv; 
end
