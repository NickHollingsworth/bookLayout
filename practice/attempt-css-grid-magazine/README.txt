How to send Chrome a Ctrl+R key combination from bash.

to do the signalling

start chrome and launch the watcher with
	launch_dev.sh

on a change to anything in the directory it constructs a refresh 
message to that browser and sends it via chrome_trigger.py

only *md and *.css are watched

JSON Messages 
-------------

The transport mechanism is identical for every command. 
You open the WebSocket, send a JSON-RPC string, and close it. 
Only the method and params inside the JSON change.

1. Refresh the tab (Mimics Ctrl+R.)

json
{
  "id": 1,
  "method": "Page.reload",
  "params": { "ignoreCache": false }
}

2. Change URL( Redirects the tab to a new address.)

json
{
  "id": 1,
  "method": "Page.navigate",
  "params": { "url": "https://google.com" }
}

3. Close the tab

json
{
  "id": 1,
  "method": "Target.closeTarget",
  "params": { "targetId": "YOUR_TARGET_ID" }
}
Note: to kill the entire browser, use Browser.close with no params.

4. Simulate a keypress (for example simulate the user pressing the 'b' key)

Three messages sent in sequence: keyDown, char, keyUpr. 

To simulate a simple lowercase 'b':
json
{
	"id":1, 
	"method":"Input.dispatchKeyEvent", 
	"params":
		{"type":"keyDown", "key":"b", "windowsVirtualKeyCode":66}
}
{
	"id":2, 
	"method":"Input.dispatchKeyEvent", 
	"params":
		{"type":"char", "text":"b"}
}
{
	"id":3, 
	"method":"Input.dispatchKeyEvent", 
	"params":
		{"type":"keyUp", "key":"b", "windowsVirtualKeyCode":66}
}


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

