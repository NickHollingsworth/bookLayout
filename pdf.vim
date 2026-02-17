" --- PDF Helpers ---
" To load (source) these commands into vi/vim:
"     :so pdf.vim

" CutPdf
" --------------------------------------------
"     Gets the text from the specified page in the pdf
"     then cuts to give only column start to end inclusive.
"     To set the pdf to be used:
"         :SetPdf /home/user/Documents/Whatever.pdf
"         (note: Tab will autocomplete filenames)
"     To insert columns 1 through 30 of page 3 from the pdf:
"         :CutPdf 3 1 30
"     To check what pdf you would work on
"         :ShowPdf
"
" A global variable that specifies the pdf to use.
let g:pdf_path = "/home/user/Documents/default.pdf"

" A function to do the extraction, cut and insert from the pdf.
function! PullPdf(page, start, end)
    " Check if the file exists before running (Linux check)
    if filereadable(g:pdf_path)
        let l:cmd = "pdftotext -f " . a:page . " -l " . a:page . " -layout " . shellescape(g:pdf_path) . " - | cut -c" . a:start . "-" . a:end
        execute "read !" . l:cmd
    else
        echoerr "PDF Error: File not found at " . g:pdf_path
		echoerr "    To change the file being used:"
		echoerr "        :SetPdf your path and filename"
    endif
endfunction

" Command to the change the pdf being worked on (for this session)
"     The <q-args> ensures the entire string (including spaces) is captured
"     Usage: :SetPdf /path/to/new/document.pdf
command! -nargs=1 -complete=file SetPdf let g:pdf_path = <q-args>

" Command to show what the pdf is currently set to
command! ShowPdf echo "Current Pdf: " . g:pdf_path

" Create a shortcut command: :CutPdf page start end
command! -nargs=+ CutPdf call PullPdf(<f-args>)

