deactivate 2>/dev/null || true
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install markdown-it-py mdit-py-plugins linkify-it-py uc-micro-py watchdog

