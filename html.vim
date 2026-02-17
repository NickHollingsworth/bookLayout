" --- HTML Helpers ---
" To load (source) these commands into vi/vim:
"     :so html.vim

" Wrap <tag> (with trailing space stripping)
" --------------------------------------------
"    Inserts the given tag before the first none whitespace character and 
"    at the end (having also stripped any trailing whitespace).
"    To wrap current line in <div>
"        :Wrap div
"    To wrap the next 8 lines in <p>
"        :.,+7Wrap p
"    Or:
"        8V:Wrap p
"    To wrap every line containing 'Chapter' in a h1:
"        :g/Chapter/Wrap h1
command! -nargs=1 Wrap s/\s\+$//e | execute "normal! I<<args>>\<Esc>A</<args>>\<Esc>"

" Wrap Macros 
" --------------------------------------------
"    Inserts its opening tag before the first none whitespace character and 
"    its closing tag at the end (having also stripped any trailing whitespace).
"    (Note: Have used UPPERCASE registers in the hope it reduces the change
"    they get overwritten by macros the user records durig the session).
"    To wrap current line in tags:
"        @P       for <p>
"        @O       for <h1>  (level One)
"        @T       for <h2>  (level Two)
"        @H       for <h3>  (level tHree)
"        @F       for <h4>  (level Four)
"        @D       for <div>
"    To wrap the next 8 lines in p tags:
"        8@P
"    To make more macros just record the relevant macro, for example to
"    surround the line with span tags as macro s (ie @s), then:
"        qd:Wrap span[Enter]jq
let @P = "I<p>\<Esc>A</p>\<Esc>j"
let @O = "I<h1>\<Esc>A</h1>\<Esc>j"
let @T = "I<h2>\<Esc>A</h2>\<Esc>j"
let @H = "I<h3>\<Esc>A</h3>\<Esc>j"
let @F = "I<h4>\<Esc>A</h4>\<Esc>j"
let @D = "I<div>\<Esc>A</div>\<Esc>j"

" Clean 
" --------------------------------------------
"    Removes trailing whitespace and strips trailing hyphons from the selected
"    lines.
"    (trailing hyphons often result from breaking words to fit columns widths)
"    To clean current line:
"        :Clean
"    To clean whole file:
"        :%Clean
"    To clean visual selection
"        v (and select lines) :Clean
command! -range Clean <line1>,<line2>s/\s\+$//e | <line1>,<line2>s/-\n//ge

" JoinWrap <tag> 
" --------------------------------------------
"     Joins the selected lines into one and wraps them in a tag
"     To join selected lines and wrap in a <p>:
"         press v, highlight the lines, type :JoinWrap p Enter
"     To join lines 10 to 15 and wrap in a div:
"         :10,15JoinWrap div Enter
command! -range -nargs=1 JoinWrap <line1>,<line2>join | <line1>s/\s\+$//e | execute "normal! I<<args>>\<Esc>A</<args>>\<Esc>"

" VWrap <tag> 
" --------------------------------------------
"     Wraps visually selected words in a given tag.
"     To wrap the next 4 words in <strong>:
"         v4w:VWrap strong
"     To wrap up to and *including* the next period in a <h2>:
"         vf.:VWrap h2
"     (note: f finds and moves onto the character, t moves before 'till' it)
"     You cant repeat something like vf.:VWrap strong, but you can record 
"     it as a macro with:
"         qsvf.:VWrap strong[Enter][Enter]
"     (note: the second enter is to position on the next line, but it could be
"     more complex to locate the next position to wrap with strong).
"     Then execute the macro as normal with @s and repeat it with @@.
"     (note: the gv in the command 'gets back' your visual selection which
"     disappears when you type : to enter the command).
" VWrap <tag> - Works correctly with sub-line visual selections
command! -range -nargs=1 VWrap execute "normal! gvc<<args>>\<C-r>\"</<args>>\<Esc>"


