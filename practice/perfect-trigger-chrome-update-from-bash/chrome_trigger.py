import sys
import json
from websocket import create_connection

def reload_chrome(ws_url):
    try:
        # Connect to the Chrome Tab
        ws = create_connection(ws_url)
        
        # This JSON payload tells Chrome: "Reload, but don't force-clear cache"
        # This 'ignoreCache: False' is what keeps your scroll position exactly the same.
        payload = {
            "id": 1, 
            "method": "Page.reload", 
            "params": {"ignoreCache": False}
        }
        
        ws.send(json.dumps(payload))
        ws.close()
        print("Successfully signaled Chrome.")
    except Exception as e:
        print(f"Error connecting to Chrome: {e}")

if __name__ == "__main__":
    # The Bash script passes the WebSocket URL as the first argument
    if len(sys.argv) > 1:
        reload_chrome(sys.argv[1])
    else:
        print("No WebSocket URL provided.")

