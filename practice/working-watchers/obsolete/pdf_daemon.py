import os
import sys
import time
import argparse
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from playwright.sync_api import sync_playwright

class PDFHandler(FileSystemEventHandler):
    def __init__(self, input_html, output_pdf, page_instance):
        self.input_html = os.path.abspath(input_html)
        self.output_pdf = output_pdf
        self.page = page_instance

    def on_modified(self, event):
        # Trigger only if our specific HTML file was modified
        if os.path.abspath(event.src_path) == self.input_html:
            self.render()

    def render(self):
        try:
            start_time = time.time()
            # Reload the warm page
            self.page.goto(f"file://{self.input_html}", wait_until="load")
            
            # Print to PDF (Sub-second because browser/fonts are cached)
            self.page.pdf(
                path=self.output_pdf,
                format="A4",
                print_background=True,
                prefer_css_page_size=True
            )
            elapsed = (time.time() - start_time) * 1000
            print(f"[{time.strftime('%H:%M:%S')}] PDF Updated in {elapsed:.0f}ms")
        except Exception as e:
            print(f"Render Error: {e}")

def main():
    parser = argparse.ArgumentParser(description="Persistent PDF Daemon")
    parser.add_argument("-i", "--input", default="preview.html", help="HTML file to watch")
    parser.add_argument("-o", "--output", default="magazine.pdf", help="PDF to generate")
    args = parser.parse_args()

    with sync_playwright() as p:
        # 1. Start Chromium ONCE and keep it open
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Initial render
        handler = PDFHandler(args.input, args.output, page)
        if os.path.exists(args.input):
            handler.render()

        # 2. Setup Watchdog Observer
        observer = Observer()
        # Watch the directory containing the file
        watch_dir = os.path.dirname(os.path.abspath(args.input))
        observer.schedule(handler, watch_dir, recursive=False)
        
        print(f"Daemon active. Watching {args.input}...")
        observer.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            browser.close()
        observer.join()

if __name__ == "__main__":
    main()

