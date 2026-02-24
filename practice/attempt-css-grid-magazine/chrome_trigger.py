import sys, json, websocket

def send(ws_url, method, params):
    try:
        ws = websocket.create_connection(ws_url)
        ws.send(json.dumps({"id": 1, "method": method, "params": params}))
        ws.close()
        print(f"Sent {method}")
    except Exception as e:
        print(f"Error: {e}")

def key_sequence(ws_url, char):
    v_code = ord(char.upper())
    ws = websocket.create_connection(ws_url)
    # Send the triple-tap sequence for a perfect user simulation
    for i, t in enumerate(["keyDown", "char", "keyUp"]):
        p = {"type": t, "key": char, "text": char, "windowsVirtualKeyCode": v_code}
        ws.send(json.dumps({"id": i, "method": "Input.dispatchKeyEvent", "params": p}))
    ws.close()
    print(f"Sent KeyPress: {char}")

if __name__ == "__main__":
    url, cmd = sys.argv[1], sys.argv[2]
    
    if cmd == "reload":
        send(url, "Page.reload", {"ignoreCache": False})
    elif cmd == "goto":
        send(url, "Page.navigate", {"url": sys.argv[3]})
    elif cmd == "key":
        key_sequence(url, sys.argv[3])
    elif cmd == "close":
        send(url, "Browser.close", {})

