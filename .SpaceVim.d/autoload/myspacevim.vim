function! myspacevim#before() abort
  set wrap                                                                                                                           
  au FileType vim set nowrap
  au FileType cpp set tabstop=4 shiftwidth=4
endfunction
