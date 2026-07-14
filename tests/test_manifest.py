from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parents[1]


def test_manifest_website_is_absent_or_non_empty():
    manifest = tomllib.loads((ROOT / "blender_manifest.toml").read_text(encoding="utf-8"))

    assert manifest.get("website", "https://example.invalid")
