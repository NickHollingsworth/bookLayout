Uses two different ways to watch for changes and trigger action:
.   inotifywait is used inside watch_magazine.sh
.   watchdog is used in sync_daemon.py



Setup: You open three terminals (and a pdf viewer)
Terminal 1: Run sync_daemon.py (The viewer window pops up).
Terminal 2: Run ./watch_magazine.sh (The silent observer).
Terminal 3: Open vi article.md.


1. Open a terminal to launch the chromium browser that will 
   show the intermediate html (review.html) and update when it changes

    python3 sync_daemon.py -i preview.html -o magazine.pdf

	note: it might struggle if there isnt already a review.html to display

2. Open another terminal 

3. Open a pdf viewer that looks at the magazine.pdf

4. In a third window edit your markdown and css. 

    magazine.md    your markdown with ::: section marks and css classes etc
    magazine.css   styling and layout rules

----

When magazine.md changes because you save the file
    . watch_magazine.sh spots this using inotify and calls python3 md2html.py
	. which uses the python markdown libraries to turn the markdown
	  into preview.html
	      . uses attr plugin to process css attributes in the markdown
	. sync_daemon.py spots preview.html changed and 
	  1. reloads the view in chromium so you see the change in the browser
	  2. uses a second headless chromium to print the result of the html 
	     and css to magazine.pdf
	. the pdf viewer updates so you see the change to magazine.pdf

Debugging: If things look wrong, you use F12 (DevTools) in the Chromium window to inspect the CSS Grid cells.


Notes:
.   The Signal (Queue): sync_daemon.py detects the new preview.html. 
    It places a "RENDER" message into a thread-safe queue.
.   The Render (Chromium): The persistent Chromium window sees the 
    queue message, reloads the page (showing you the layout), and 
	simultaneously calls the .pdf() command.

Decoupled: If your Markdown has an error, the HTML generator fails, but your Browser and PDF engines stay "warm" and don't crash.

