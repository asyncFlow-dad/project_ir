#!/usr/bin/env python3
"""Render openclaw.json from openclaw.json5.tpl (regular file requirement)."""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
TEMPLATE_PATH = ROOT / "openclaw" / "openclaw.json5.tpl"
OUTPUT_PATH = ROOT / "openclaw" / "openclaw.json"

ROLE_PRESETS: dict[str, dict[str, str]] = {
    "dev": {
        "OPENCLAW_AGENT_NAME": "AI IR Dev",
        "OPENCLAW_AGENT_THEME": "engineering",
        "OPENCLAW_AGENT_EMOJI": "🛠️",
    },
    "qa": {
        "OPENCLAW_AGENT_NAME": "AI IR QA",
        "OPENCLAW_AGENT_THEME": "evaluation",
        "OPENCLAW_AGENT_EMOJI": "🧪",
    },
    "pm": {
        "OPENCLAW_AGENT_NAME": "AI IR PM",
        "OPENCLAW_AGENT_THEME": "planning",
        "OPENCLAW_AGENT_EMOJI": "📋",
    },
}


def load_env_file(path: Path) -> None:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key, value = key.strip(), value.strip()
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        if key and key not in os.environ:
            os.environ[key] = value


def json_array(values: list[str]) -> str:
    return json.dumps(values, ensure_ascii=False)


def build_defaults() -> dict[str, str]:
    role = os.environ.get("OPENCLAW_ROLE", "dev").lower()
    preset = ROLE_PRESETS.get(role, ROLE_PRESETS["dev"])

    owner_id = os.environ.get("TELEGRAM_OWNER_ID", "").strip()
    dm_policy = os.environ.get("TELEGRAM_DM_POLICY", "").strip()
    if not dm_policy:
        dm_policy = "allowlist" if owner_id else "pairing"

    allow_from = [owner_id] if owner_id else []
    group_policy = os.environ.get("TELEGRAM_GROUP_POLICY", "allowlist").strip() or "allowlist"
    telegram_enabled = os.environ.get("TELEGRAM_ENABLED", "true").strip().lower() not in {
        "0",
        "false",
        "no",
    }

    webhook_url = os.environ.get("TELEGRAM_WEBHOOK_URL", "").strip()
    webhook_secret = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "").strip()
    webhook_path = os.environ.get(
        "TELEGRAM_WEBHOOK_PATH",
        f"/telegram/{role}",
    ).strip()

    defaults: dict[str, str] = {
        "OPENCLAW_GATEWAY_PORT": os.environ.get("OPENCLAW_GATEWAY_PORT", "19809"),
        "OPENCLAW_GATEWAY_BIND": os.environ.get("OPENCLAW_GATEWAY_BIND", "loopback"),
        "OPENCLAW_GATEWAY_TOKEN": os.environ.get(
            "OPENCLAW_GATEWAY_TOKEN",
            "replace-me-local-gateway-token",
        ),
        "OPENCLAW_WORKSPACE_DIR": os.environ.get("OPENCLAW_WORKSPACE_DIR", "."),
        "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", "sk-ant-placeholder"),
        "ANTHROPIC_MODEL_ID": os.environ.get("ANTHROPIC_MODEL_ID", "claude-sonnet-4-5"),
        "ANTHROPIC_MODEL_NAME": os.environ.get("ANTHROPIC_MODEL_NAME", "Claude Sonnet 4.5"),
        "TELEGRAM_ENABLED": "true" if telegram_enabled else "false",
        "TELEGRAM_DM_POLICY": dm_policy,
        "TELEGRAM_ALLOW_FROM": json_array(allow_from),
        "TELEGRAM_GROUP_POLICY": group_policy,
        "TELEGRAM_GROUP_ALLOW_FROM": json_array(allow_from),
        **preset,
    }

    if webhook_url and webhook_secret:
        defaults["TELEGRAM_WEBHOOK_BLOCK"] = json.dumps(
            {
                "webhookUrl": webhook_url,
                "webhookSecret": webhook_secret,
                "webhookPath": webhook_path,
                "webhookHost": os.environ.get("TELEGRAM_WEBHOOK_HOST", "0.0.0.0"),
                "webhookPort": int(os.environ.get("TELEGRAM_WEBHOOK_PORT", "8787")),
            },
            indent=6,
        ).replace("\n", "\n      ")
    else:
        defaults["TELEGRAM_WEBHOOK_BLOCK"] = ""

    return defaults


def render_template(template: str, values: dict[str, str]) -> str:
    rendered = template
    for key, value in values.items():
        rendered = rendered.replace(f"${{{key}}}", value)

    remaining = re.findall(r"\$\{([^}]+)\}", rendered)
    if remaining:
        missing = ", ".join(sorted(set(remaining)))
        raise SystemExit(f"Unresolved template variables: {missing}")
    return rendered


def inject_webhook_block(rendered: str, webhook_block: str) -> str:
    if not webhook_block:
        return rendered
    needle = '"configWrites": false'
    insertion = f'{needle},\n      {webhook_block.lstrip()}'
    return rendered.replace(needle, insertion, 1)


def main() -> int:
    load_env_file(ENV_PATH)
    if not TEMPLATE_PATH.exists():
        print(f"Template not found: {TEMPLATE_PATH}", file=sys.stderr)
        return 1

    values = build_defaults()
    webhook_block = values.pop("TELEGRAM_WEBHOOK_BLOCK", "")
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    rendered = inject_webhook_block(render_template(template, values), webhook_block)

    json.loads(rendered)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(rendered + "\n", encoding="utf-8")
    os.chmod(OUTPUT_PATH, 0o600)
    print(f"Wrote {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
