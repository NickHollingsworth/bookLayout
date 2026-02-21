import os
import sys
import time
import argparse
import queue
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from playwright.sync_api import sync_playwright

# 1. Thread-safe Queue to pass messages from Watchdog to Playwright
render_queue = queue.Queue()

class SyncHandler(FileSystemEventHandler):
    def __init__(self, input_html_path):
        self.input_html_path = os.path.abspath(input_html_path)

    def on_modified(self, event):
        # When file changes, put a 'RENDER' command into the queue
        if os.path.abspath(event.src_path) == self.input_html_path:
            render_queue.put("RENDER")

def main():
    parser = argparse.ArgumentParser(description="Live Magazine Sync Daemon")
    parser.add_argument("-i", "--input", default="preview.html", help="HTML file to watch")
    parser.add_argument("-o", "--output", default="magazine.pdf", help="PDF to generate")
    args = parser.parse_args()

    input_url = f"file://{os.path.abspath(args.input)}"

    with sync_playwright() as p:
        # Start the browser on the Main Thread
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={'width': 794, 'height': 1123})
        page = context.new_page()
        page.emulate_media(media="print")

        # Function to actually do the work (runs on Main Thread)
        def do_render():
            try:
                start_time = time.time()
                page.goto(input_url, wait_until="load")
                page.pdf(
                    path=args.output,
                    format="A4",
                    print_background=True,
                    prefer_css_page_size=True
                )
                elapsed = (time.time() - start_time) * 1000
                print(f"[{time.strftime('%H:%M:%S')}] Sync: {elapsed:.0f}ms -> {args.output}")
            except Exception as e:
                print(f"Render Error: {e}")

        # Initial render
        if os.path.exists(args.input):
            do_render()

        # Setup Watchdog
        observer = Observer()
        handler = SyncHandler(args.input)
        watch_dir = os.path.dirname(os.path.abspath(args.input)) or "."
        observer.schedule(handler, watch_dir, recursive=False)
        observer.start()

        print(f"Daemon active. Watching: {args.input}")

        # 2. Main Loop: Check the queue for work
        try:
            while True:
                try:
                    # Check if Watchdog sent a message (wait 0.1s)
                    msg = render_queue.get(timeout=0.1)
                    if msg == "RENDER":
                        do_render()
                except queue.Empty:
                    # No work to do, just keep the loop alive
                    pass
                time.sleep(0.05)
        except KeyboardInterrupt:
            print("\nShutting down...")
            observer.stop()
            browser.close()
        
        observer.join()

if __name__ == "__main__":
    main()

