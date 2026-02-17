" --- Text Helpers ---
" To load (source) these commands into vi/vim:
"     :so text.vim

" PJoin   (paragraph join)
" --------------------------------------------
" Strips all leading and trailing whitespace from every line in the range.
" On every line that contains at least one non-whitespace character...
"      joins from the current line to the line just before the next empty line.
" Usage: :PJoin (current paragraph) or :%PJoin (whole file)

function! Do_PJoin() range
    " 1. Clean the selection first (strip whitespace)
    execute a:firstline . "," . a:lastline . "s/^\\s*//e"
    execute a:firstline . "," . a:lastline . "s/\\s*$//e"

    " 2. Loop through the range backwards (to avoid line-number shift errors)
    let l:curr = a:lastline - 1
    while l:curr >= a:firstline
        " Get current and next line content
        let l:line1 = getline(l:curr)
        let l:line2 = getline(l:curr + 1)

        " If both lines have text, join them with a single space
        if l:line1 =~ '\S' && l:line2 =~ '\S'
            execute l:curr . "join"
        endif
        let l:curr -= 1
    endwhile
endfunction

" Map :PJoin to the function
command! -range PJoin <line1>,<line2>call Do_PJoin()


" PSplit  (paragraph split)
" --------------------------------------------
" (Note: &tw is vi's variable that holds current textwidth setting)
" Usage: :PSplit 40 (wraps current paragraph to 40 chars)
command! -nargs=1 PSplit let old_tw=&tw | set textwidth=<args> | normal! gqap | let &tw=old_tw

