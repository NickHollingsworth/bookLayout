How to send Chrome a Ctrl+R key combination from bash.
Also starts and stops a web server, launches and closes a chrome window in debug mode, has a config file.

Running the example
	start_dev.sh

This:
.   Loads the json config file with jq
.   Kills anything running on the desired port (in case server still running)
.   Launcher the browser on the desired port with a debug channel
.   Watches for changes of the specified file type in the specified directory
    using inotifywait
.   (with a slight 'debounce' pause to avoid being triggered several times
    for one event)
.   Sends a ctrl-r to the browser on its debug channel.
.   When you kill this script it catches that and kills the process/

Ports, things to watch for change, etc configured in
	config.json

Tidy up script kills anything runnig on the port (should not be needed)
	kill_dev.sh

------

to do the signalling

start chrome and launch the watcher with
	launch_dev.sh

on a change to anything in the directory it constructs a refresh 
message to that browser and sends it via chrome_trigger.py

only *md and *.css are watched

-----

How it works

1. Launch chrome and get it to use a specific port for remote debug.

    chrome.exe --remote-debugging-port=9222

If you already have chrome open for other purposes you must you must 
use a separate profile via the --user-data-dir flag. If you omit this, 
Chrome will simply open a new window in your existing session, which 
usually has debugging disabled by default for security.

    google-chrome \
	    --remote-debugging-port=9222 \
	    --user-data-dir="/tmp/chrome-debug" \
		"http://localhost:8000/yourpage.html"

note: chrome and chromium are interchangable in this scenario


2. Send chrome a ctrl-r

An external agent (like a Python or Node.js script) can connect to
    http://localhost:9222/json 
and send this json
    { "id": 1, "method": "Page.reload", "params": { "ignoreCache": false } }
setting ignoreCache to false (default) helps ensure the browser attempts 
to restore the scroll position.

if you need to find the websocket url from bash
	WS_URL=$(curl -s http://localhost:9222/json \
	    | jq -r '.[0].webSocketDebuggerUrl')

note: you could send the JSON command to the tab's websocket url
    echo '{"id": 1, "method": "Page.reload"}' | websocat -n1 "$WS_URL"
but websocat is not in the standard repositories

instead since have python and a venv environment set up
	pip install websocket-client

You should allow a debounce delay to avoid multiple triggers.

----

Other approaches:

LiveReload: A popular extension and accompanying agent that watches directories for changes in HTML, CSS, or JS and reloads the page automatically.

