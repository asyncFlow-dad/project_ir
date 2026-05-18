#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"


def load_env_file(path: Path, override: bool = False) -> None:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        if override or key not in os.environ:
            os.environ[key] = value


def resolve_from_root(value: str | None, fallback: str) -> str:
    raw = value or fallback
    path = Path(raw)
    return str(path if path.is_absolute() else ROOT / path)


def ensure_rendered_config() -> None:
    template = ROOT / "openclaw" / "openclaw.json5.tpl"
    renderer = ROOT / "scripts" / "render_openclaw_config.py"
    config_path = resolve_from_root(
        os.environ.get("OPENCLAW_CONFIG_PATH"),
        "openclaw/openclaw.json",
    )
    if template.exists() and renderer.exists():
        subprocess.run([sys.executable, str(renderer)], cwd=ROOT, check=False)
        os.environ["OPENCLAW_CONFIG_PATH"] = config_path


def main() -> int:
    load_env_file(ENV_PATH, override=True)
    ensure_rendered_config()
    os.environ["OPENCLAW_CONFIG_PATH"] = resolve_from_root(
        os.environ.get("OPENCLAW_CONFIG_PATH"),
        "openclaw/openclaw.json",
    )
    os.environ["OPENCLAW_STATE_DIR"] = resolve_from_root(
        os.environ.get("OPENCLAW_STATE_DIR"),
        ".openclaw-state",
    )
    os.environ["OPENCLAW_LAUNCHD_LABEL"] = "ai.openclaw.ir-project"
    os.environ.pop("OPENCLAW_PROFILE", None)

    local_openclaw = ROOT / "node_modules" / ".bin" / "openclaw"
    command = str(local_openclaw if local_openclaw.exists() else "openclaw")
    return subprocess.run([command, *sys.argv[1:]], cwd=ROOT, env=os.environ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
