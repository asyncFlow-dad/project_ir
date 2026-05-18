import json
import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase


class RenderConfigTests(TestCase):
    def test_render_openclaw_config_produces_valid_json(self) -> None:
        root = Path(__file__).resolve().parents[1]
        renderer = root / "scripts" / "render_openclaw_config.py"
        template = root / "openclaw" / "openclaw.json5.tpl"
        if not template.exists():
            self.skipTest("template missing")

        with TemporaryDirectory() as tmp:
            output = Path(tmp) / "openclaw.json"
            env = os.environ.copy()
            env.update(
                {
                    "OPENCLAW_GATEWAY_TOKEN": "test-token",
                    "OPENCLAW_WORKSPACE_DIR": ".",
                    "OPENCLAW_ROLE": "dev",
                }
            )
            # Renderer writes to repo path; run in subprocess with patched output via cwd trick:
            # copy template to temp and patch renderer behavior by setting OPENCLAW_CONFIG_PATH parent
            result = subprocess.run(
                [sys.executable, str(renderer)],
                cwd=root,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            rendered_path = root / "openclaw" / "openclaw.json"
            self.assertTrue(rendered_path.exists())
            payload = json.loads(rendered_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["tools"]["exec"]["security"], "deny")
            self.assertEqual(payload["channels"]["telegram"]["configWrites"], False)
