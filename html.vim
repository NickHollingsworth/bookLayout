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
"    To wrap current line in h1 tags:
"        @1
"    To wrap the next 8 lines in p tags:
"        8@p
"    To make more macros just record the relevant macro, for example to
"    surround the line with div tags as macro d (ie @d), then:
"        qd:Wrap div[Enter]jq
let @p = "I<p>\<Esc>A</p>\<Esc>j"
let @1 = "I<h1>\<Esc>A</h1>\<Esc>j"
let @2 = "I<h2>\<Esc>A</h2>\<Esc>j"
let @d = "I<div>\<Esc>A</div>\<Esc>j"

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
command! -range -nargs=1 VWrap execute "normal! c<<args>>\<C-r>\"</<args>>\<Esc>"

