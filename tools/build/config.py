from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

#-----------------------------------------------------------
# read directory names and other config from config file.
#-----------------------------------------------------------
@dataclass(frozen=True)
class BuildConfig:
    src_dir: str = "src"
    preprocess_dir: str = "tmp/step-1-enhanced-md"
    build_dir: str = "tmp/step-2-resulting-html"
    template: str = "tools/templates/page.html"
    css: str = "../../tools/style/style.css"
    dev_js: str = "../../tools/scripts/reload.js"


def require_nonempty(name: str, value: str | None) -> str:
    if value is None or not str(value).strip():
        raise ValueError(f"Required setting '{name}' is not set (check config file or CLI).")
    return value


def parse_kv_config(path: Path) -> dict[str, str]:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    data: dict[str, str] = {}
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"{path}:{lineno}: expected 'key = value' (missing '='): {raw!r}")

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if not key:
            raise ValueError(f"{path}:{lineno}: empty key in line: {raw!r}")
        if value == "":
            raise ValueError(f"{path}:{lineno}: empty value for key '{key}'")

        data[key] = value

    return data


def load_build_config(path: Path) -> BuildConfig:
    raw = parse_kv_config(path)

    allowed = {"src_dir", "preprocess_dir", "build_dir", "template", "css", "dev_js"}
    unknown = sorted(set(raw.keys()) - allowed)
    if unknown:
        raise ValueError(f"{path}: unknown config keys: {', '.join(unknown)}")

    return BuildConfig(
        src_dir=raw.get("src_dir", BuildConfig.src_dir),
        preprocess_dir=raw.get("preprocess_dir", BuildConfig.preprocess_dir),
        build_dir=raw.get("build_dir", BuildConfig.build_dir),
        template=raw.get("template", BuildConfig.template),
        css=raw.get("css", BuildConfig.css),
        dev_js=raw.get("dev_js", BuildConfig.dev_js),
    )

