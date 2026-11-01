"""Real Git checkout contracts for web text and binary assets."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("autocrlf", ["true", "input", "false"])
def test_web_text_checks_out_as_lf_without_changing_binary_assets(
    tmp_path: Path, autocrlf: str
) -> None:
    if shutil.which("git") is None:
        pytest.skip("Git is required for the checkout contract")

    def git(*arguments: str) -> bytes:
        return subprocess.check_output(["git", "-C", str(tmp_path), *arguments])

    git("init", "-q")
    git("config", "core.autocrlf", autocrlf)
    git("config", "core.safecrlf", "false")
    (tmp_path / ".gitattributes").write_bytes((ROOT / ".gitattributes").read_bytes())
    text = b"synthetic first line\nsynthetic second line\n"
    text_paths = ["web/package.json", "web/.prettierrc.json"] + [
        f"web/nested/synthetic.{extension}"
        for extension in (
            "json",
            "ts",
            "tsx",
            "md",
            "html",
            "js",
            "yml",
            "yaml",
            "jsx",
            "cjs",
            "mts",
            "mjs",
            "css",
        )
    ]
    binary_assets = {
        "web/electron/icons/AppIcon.icon/nested/metadata.json": b"tool-owned\r\nbytes\r\n",
        "web/electron/icons/synthetic.png": b"\x89PNG\x00\r\nsynthetic\xff",
    }
    fixtures = {**dict.fromkeys(text_paths, text), **binary_assets}
    for relative_path, data in fixtures.items():
        path = tmp_path / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    git("add", "--", ".gitattributes", "web")
    for relative_path in fixtures:
        (tmp_path / relative_path).unlink()
    git("checkout-index", "--all", "--force")

    for relative_path, expected in fixtures.items():
        assert (tmp_path / relative_path).read_bytes() == expected, (autocrlf, relative_path)
        assert git("show", f":{relative_path}") == expected, (autocrlf, relative_path)
    for relative_path in text_paths:
        attributes = git("check-attr", "eol", "--", relative_path).decode("utf-8")
        assert attributes.strip().endswith(": eol: lf"), attributes
    icon_attributes = git("check-attr", "text", "merge", "--", next(iter(binary_assets))).decode(
        "utf-8"
    )
    assert ": text: unset" in icon_attributes
    assert ": merge: unset" in icon_attributes
