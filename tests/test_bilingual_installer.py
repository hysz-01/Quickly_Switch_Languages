import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
from Quickly_switch_languages.bilingual import installer as bilingual_installer
from Quickly_switch_languages.bilingual.mo import MoCatalog, read_mo, write_mo
patch_languages_text = bilingual_installer.patch_languages_text
unpatch_languages_text = bilingual_installer.unpatch_languages_text
uninstall_from_manifest = bilingual_installer.uninstall_from_manifest


ENTRIES = {
    "en_zh": "998:English + Chinese - English (简体中文):en_zh:100%",
    "zh_en": "999:Chinese + English - 简体中文 (English):zh_en:100%",
}


def test_patch_adds_marked_block_and_unpatch_removes_only_that_block():
    original = "# header\n1:English (US):en_US:100%\n13:Chinese (Simplified) - 简体中文:zh_HANS:100%\n"

    patched = patch_languages_text(original, ENTRIES)

    assert "# BEGIN Quick Language Switcher bilingual languages" in patched
    assert ENTRIES["en_zh"] in patched
    assert ENTRIES["zh_en"] in patched
    assert unpatch_languages_text(patched) == original


def test_patch_rejects_conflicting_existing_language_code():
    original = "1:English (US):en_US:100%\n77:Custom:zh_en:100%\n"

    with pytest.raises(ValueError, match="Conflicting language code"):
        patch_languages_text(original, ENTRIES)


def test_patch_rejects_conflicting_existing_language_id():
    original = "1:English (US):en_US:100%\n9821:Custom:custom_locale:100%\n"

    with pytest.raises(ValueError, match="Conflicting language id"):
        patch_languages_text(original, {"en_ja": "9821:English + Japanese:en_ja:100%"})


def test_patch_preserves_existing_addon_language_entries():
    original = patch_languages_text("1:English (US):en_US:100%\n", {"en_ja": "9821:English + Japanese:en_ja:100%"})

    patched = patch_languages_text(original, {"zh_en": "999:Chinese + English:zh_en:100%"})

    assert "9821:English + Japanese:en_ja:100%" in patched
    assert "999:Chinese + English:zh_en:100%" in patched


def test_patch_preserves_entries_from_multiple_addon_marker_blocks():
    original = (
        "1:English (US):en_US:100%\n"
        "# BEGIN Quick Language Switcher bilingual languages\n"
        "9821:English + Japanese:en_ja:100%\n"
        "# END Quick Language Switcher bilingual languages\n"
        "# BEGIN Quick Language Switcher bilingual languages\n"
        "9822:English + German:en_de:100%\n"
        "# END Quick Language Switcher bilingual languages\n"
    )

    patched = patch_languages_text(original, {"en_fr": "9823:English + French:en_fr:100%"})

    assert "9821:English + Japanese:en_ja:100%" in patched
    assert "9822:English + German:en_de:100%" in patched
    assert "9823:English + French:en_fr:100%" in patched


def test_uninstall_uses_manifest_and_leaves_unlisted_files(tmp_path):
    locale_root = tmp_path / "locale"
    languages_path = locale_root / "languages"
    manifest_path = tmp_path / "manifest.json"
    (locale_root / "zh_en" / "LC_MESSAGES").mkdir(parents=True)
    (locale_root / "en_zh" / "LC_MESSAGES").mkdir(parents=True)
    (locale_root / "zh_en" / "LC_MESSAGES" / "blender.mo").write_bytes(b"zh_en")
    (locale_root / "en_zh" / "LC_MESSAGES" / "blender.mo").write_bytes(b"en_zh")
    (locale_root / "zh_en" / "keep.txt").write_text("keep", encoding="utf-8")
    languages_path.write_text(patch_languages_text("1:English (US):en_US:100%\n", ENTRIES), encoding="utf-8")
    manifest_path.write_text(json.dumps({
        "installed_files": [
            "zh_en/LC_MESSAGES/blender.mo",
            "en_zh/LC_MESSAGES/blender.mo",
        ]
    }), encoding="utf-8")

    uninstall_from_manifest(locale_root, languages_path, manifest_path)

    assert "Quick Language Switcher" not in languages_path.read_text(encoding="utf-8")
    assert not (locale_root / "en_zh").exists()
    assert (locale_root / "zh_en" / "keep.txt").exists()


def test_uninstall_rejects_manifest_paths_outside_locale_root(tmp_path):
    locale_root = tmp_path / "locale"
    locale_root.mkdir()
    languages_path = locale_root / "languages"
    manifest_path = tmp_path / "manifest.json"
    outside = tmp_path / "outside.mo"
    languages_path.write_text("1:English (US):en_US:100%\n", encoding="utf-8")
    outside.write_bytes(b"do not delete")
    manifest_path.write_text(json.dumps({"installed_files": ["../outside.mo"]}), encoding="utf-8")

    with pytest.raises(ValueError, match="Unsafe installed file path"):
        uninstall_from_manifest(locale_root, languages_path, manifest_path)

    assert languages_path.read_text(encoding="utf-8") == "1:English (US):en_US:100%\n"
    assert outside.exists()


class _FailingWritePath:
    def __init__(self, real_path, fail_on_write_number):
        self.real_path = real_path
        self.fail_on_write_number = fail_on_write_number
        self.write_count = 0

    def __truediv__(self, other):
        return self.real_path / other

    def __fspath__(self):
        return str(self.real_path)

    def exists(self):
        return self.real_path.exists()

    def read_text(self, *args, **kwargs):
        return self.real_path.read_text(*args, **kwargs)

    def write_text(self, *args, **kwargs):
        self.write_count += 1
        if self.write_count == self.fail_on_write_number:
            self.real_path.write_text("CORRUPTED", encoding="utf-8")
            raise OSError("simulated write failure")
        return self.real_path.write_text(*args, **kwargs)


def test_install_and_patch_restores_languages_when_patch_write_fails(tmp_path):
    locale_root = tmp_path / "locale"
    locale_root.mkdir()
    real_languages = locale_root / "languages"
    original = "1:English (US):en_US:100%\n"
    real_languages.write_text(original, encoding="utf-8")
    source = tmp_path / "generated.mo"
    source.write_bytes(b"generated")
    failing_languages = _FailingWritePath(real_languages, fail_on_write_number=1)

    with pytest.raises(OSError, match="simulated write failure"):
        bilingual_installer._install_and_patch(
            locale_root,
            failing_languages,
            [("en_ja/LC_MESSAGES/blender.mo", source)],
            locale_root / "languages.quick_language_switcher.bak",
            {"en_ja": "9821:English + Japanese:en_ja:100%"},
        )

    assert real_languages.read_text(encoding="utf-8") == original
    assert not (locale_root / "en_ja").exists()


def test_uninstall_restores_languages_when_unpatch_write_fails(tmp_path):
    locale_root = tmp_path / "locale"
    locale_root.mkdir()
    real_languages = locale_root / "languages"
    patched = patch_languages_text("1:English (US):en_US:100%\n", ENTRIES)
    real_languages.write_text(patched, encoding="utf-8")
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps({"installed_files": []}), encoding="utf-8")
    failing_languages = _FailingWritePath(real_languages, fail_on_write_number=1)

    with pytest.raises(OSError, match="simulated write failure"):
        uninstall_from_manifest(locale_root, failing_languages, manifest_path)

    assert real_languages.read_text(encoding="utf-8") == patched


def test_install_bilingual_pack_bakes_copies_patches_and_writes_manifest(tmp_path):
    install_bilingual_pack = bilingual_installer.install_bilingual_pack
    locale_root = tmp_path / "locale"
    source_dir = locale_root / "zh_HANS" / "LC_MESSAGES"
    source_dir.mkdir(parents=True)
    write_mo(source_dir / "blender.mo", MoCatalog({
        "": "Content-Type: text/plain; charset=UTF-8\n",
        "File": "文件",
    }))
    (locale_root / "languages").write_text(
        "1:English (US):en_US:100%\n13:Chinese (Simplified) - 简体中文:zh_HANS:100%\n",
        encoding="utf-8",
    )
    addon_root = tmp_path / "addon"

    manifest = install_bilingual_pack(locale_root, "5.0.1", addon_root)

    assert (locale_root / "zh_en" / "LC_MESSAGES" / "blender.mo").exists()
    assert (locale_root / "en_zh" / "LC_MESSAGES" / "blender.mo").exists()
    assert "zh_en" in (locale_root / "languages").read_text(encoding="utf-8")
    assert (addon_root / "data" / "bilingual_manifest.json").exists()
    assert manifest["blender_version"] == "5.0.1"


def test_install_bilingual_pack_passes_scope_keywords_to_baker(tmp_path):
    install_bilingual_pack = bilingual_installer.install_bilingual_pack
    locale_root = tmp_path / "locale"
    source_dir = locale_root / "zh_HANS" / "LC_MESSAGES"
    source_dir.mkdir(parents=True)
    write_mo(source_dir / "blender.mo", MoCatalog({
        "": "Content-Type: text/plain; charset=UTF-8\n",
        "Node": "节点",
        "Save": "保存",
    }))
    (locale_root / "languages").write_text("1:English (US):en_US:100%\n13:Chinese (Simplified) - 简体中文:zh_HANS:100%\n", encoding="utf-8")
    addon_root = tmp_path / "addon"

    manifest = install_bilingual_pack(locale_root, "5.0.1", addon_root, scope_keywords={"Node"})
    installed = read_mo(locale_root / "zh_en" / "LC_MESSAGES" / "blender.mo")

    assert installed.entries["Node"] == "节点 (Node)"
    assert installed.entries["Save"] == "保存"
    assert manifest["scope_keywords"] == ["Node"]


def test_install_bilingual_pack_records_scope_metadata(tmp_path):
    install_bilingual_pack = bilingual_installer.install_bilingual_pack
    locale_root = tmp_path / "locale"
    source_dir = locale_root / "zh_HANS" / "LC_MESSAGES"
    source_dir.mkdir(parents=True)
    write_mo(source_dir / "blender.mo", MoCatalog({
        "": "Content-Type: text/plain; charset=UTF-8\n",
        "Mix": "混合",
        "Noise Texture": "噪波纹理",
    }))
    (locale_root / "languages").write_text(
        "1:English (US):en_US:100%\n13:Chinese (Simplified) - 简体中文:zh_HANS:100%\n",
        encoding="utf-8",
    )
    addon_root = tmp_path / "addon"

    manifest = install_bilingual_pack(
        locale_root,
        "5.0.1",
        addon_root,
        scope_keywords={"Mix", "Noise Texture"},
        scope_presets=["node_shader_geometry"],
    )

    assert manifest["scope_blender_version"] == "5.0.1"
    assert manifest["scope_presets"] == ["node_shader_geometry"]
    assert manifest["scope_keyword_count"] == 2


def test_install_bilingual_pair_installs_only_selected_order(tmp_path):
    locale_root = tmp_path / "locale"
    source_dir = locale_root / "ja_JP" / "LC_MESSAGES"
    source_dir.mkdir(parents=True)
    write_mo(source_dir / "blender.mo", MoCatalog({
        "": "Content-Type: text/plain; charset=UTF-8\n",
        "File": "ファイル",
    }))
    (locale_root / "languages").write_text(
        "1:English (US):en_US:100%\n42:Japanese - 日本語:ja_JP:100%\n",
        encoding="utf-8",
    )
    addon_root = tmp_path / "addon"

    manifest = bilingual_installer.install_bilingual_pair(
        locale_root,
        "5.0.1",
        addon_root,
        language1_code="en_US",
        language1_name="English",
        language2_code="ja_JP",
        language2_name="日本語",
    )

    assert (locale_root / "en_ja" / "LC_MESSAGES" / "blender.mo").exists()
    assert not (locale_root / "ja_en").exists()
    assert "en_ja" in (locale_root / "languages").read_text(encoding="utf-8")
    installed = read_mo(locale_root / "en_ja" / "LC_MESSAGES" / "blender.mo")
    assert installed.entries["File"] == "File (ファイル)"
    assert manifest["installed_language_codes"] == ["en_ja"]
    assert manifest["installed_language_ids"]["en_ja"] != 998
    assert manifest["installed_language_ids"]["en_ja"] != 999


def test_install_bilingual_pair_uses_stable_non_legacy_language_id(tmp_path):
    locale_root = tmp_path / "locale"
    source_dir = locale_root / "ja_JP" / "LC_MESSAGES"
    source_dir.mkdir(parents=True)
    write_mo(source_dir / "blender.mo", MoCatalog({
        "": "Content-Type: text/plain; charset=UTF-8\n",
        "File": "ファイル",
    }))
    (locale_root / "languages").write_text(
        "1:English (US):en_US:100%\n42:Japanese - 日本語:ja_JP:100%\n",
        encoding="utf-8",
    )

    bilingual_installer.install_bilingual_pair(
        locale_root,
        "5.0.1",
        tmp_path / "addon",
        language1_code="en_US",
        language1_name="English",
        language2_code="ja_JP",
        language2_name="日本語",
    )

    languages_text = (locale_root / "languages").read_text(encoding="utf-8")
    assert ":English + 日本語 - English (日本語):en_ja:100%" in languages_text
    assert "998:English + 日本語 - English (日本語):en_ja:100%" not in languages_text
    assert "999:English + 日本語 - English (日本語):en_ja:100%" not in languages_text


def test_install_bilingual_pair_avoids_existing_language_id(tmp_path):
    locale_root = tmp_path / "locale"
    source_dir = locale_root / "aaf" / "LC_MESSAGES"
    source_dir.mkdir(parents=True)
    write_mo(source_dir / "blender.mo", MoCatalog({
        "": "Content-Type: text/plain; charset=UTF-8\n",
        "File": "Aaf File",
    }))
    output_code = "en_aaf"
    conflicting_id = bilingual_installer._language_entry_id(output_code)
    (locale_root / "languages").write_text(
        f"1:English (US):en_US:100%\n{conflicting_id}:Existing:existing_locale:100%\n",
        encoding="utf-8",
    )

    manifest = bilingual_installer.install_bilingual_pair(
        locale_root,
        "5.0.1",
        tmp_path / "addon",
        language1_code="en_US",
        language1_name="English",
        language2_code="aaf_AA",
        language2_name="Aaf",
    )

    languages_text = (locale_root / "languages").read_text(encoding="utf-8")
    assert f"{conflicting_id}:English + Aaf" not in languages_text
    assert f":English + Aaf - English (Aaf):{output_code}:100%" in languages_text
    assert manifest["installed_language_ids"][output_code] != conflicting_id


def test_install_bilingual_pair_avoids_existing_addon_language_id(tmp_path):
    locale_root = tmp_path / "locale"
    source_dir = locale_root / "aaf" / "LC_MESSAGES"
    source_dir.mkdir(parents=True)
    write_mo(source_dir / "blender.mo", MoCatalog({
        "": "Content-Type: text/plain; charset=UTF-8\n",
        "File": "Aaf File",
    }))
    output_code = "en_aaf"
    conflicting_id = bilingual_installer._language_entry_id(output_code)
    (locale_root / "languages").write_text(
        "1:English (US):en_US:100%\n"
        "# BEGIN Quick Language Switcher bilingual languages\n"
        f"{conflicting_id}:Existing Addon:existing_addon:100%\n"
        "# END Quick Language Switcher bilingual languages\n",
        encoding="utf-8",
    )

    manifest = bilingual_installer.install_bilingual_pair(
        locale_root,
        "5.0.1",
        tmp_path / "addon",
        language1_code="en_US",
        language1_name="English",
        language2_code="aaf_AA",
        language2_name="Aaf",
    )

    assert manifest["installed_language_ids"][output_code] != conflicting_id


def test_available_language_entry_id_moves_legacy_conflict_to_generated_range():
    used = "999:Existing:existing_locale:100%\n"

    entry_id = bilingual_installer._available_language_entry_id("zh_en", used)

    assert 9000 <= entry_id <= 9999


def test_available_language_entry_id_raises_when_generated_range_full():
    used = "".join(
        f"{entry_id}:Existing {entry_id}:existing_{entry_id}:100%\n"
        for entry_id in range(9000, 10000)
    )

    with pytest.raises(ValueError, match="No available language id"):
        bilingual_installer._available_language_entry_id("en_aaf", used)


def test_install_bilingual_pairs_accumulate_languages_and_manifest(tmp_path):
    locale_root = tmp_path / "locale"
    ja_dir = locale_root / "ja_JP" / "LC_MESSAGES"
    zh_dir = locale_root / "zh_HANS" / "LC_MESSAGES"
    ja_dir.mkdir(parents=True)
    zh_dir.mkdir(parents=True)
    write_mo(ja_dir / "blender.mo", MoCatalog({"": "Content-Type: text/plain; charset=UTF-8\n", "File": "ファイル"}))
    write_mo(zh_dir / "blender.mo", MoCatalog({"": "Content-Type: text/plain; charset=UTF-8\n", "File": "文件"}))
    (locale_root / "languages").write_text(
        "1:English (US):en_US:100%\n13:Chinese (Simplified) - 简体中文:zh_HANS:100%\n42:Japanese - 日本語:ja_JP:100%\n",
        encoding="utf-8",
    )
    addon_root = tmp_path / "addon"
    manifest_path = tmp_path / "user_config" / "bilingual_manifest.json"

    bilingual_installer.install_bilingual_pair(
        locale_root,
        "5.1.2",
        addon_root,
        language1_code="en_US",
        language1_name="English",
        language2_code="ja_JP",
        language2_name="日本語",
        manifest_path=manifest_path,
    )
    manifest = bilingual_installer.install_bilingual_pair(
        locale_root,
        "5.1.2",
        addon_root,
        language1_code="zh_HANS",
        language1_name="简体中文",
        language2_code="en_US",
        language2_name="English",
        manifest_path=manifest_path,
    )

    languages_text = (locale_root / "languages").read_text(encoding="utf-8")
    assert ":en_ja:100%" in languages_text
    assert ":zh_en:100%" in languages_text
    assert (locale_root / "en_ja" / "LC_MESSAGES" / "blender.mo").exists()
    assert (locale_root / "zh_en" / "LC_MESSAGES" / "blender.mo").exists()
    assert set(manifest["installed_language_codes"]) == {"en_ja", "zh_en"}
    assert set(manifest["installed_files"]) == {
        "en_ja/LC_MESSAGES/blender.mo",
        "zh_en/LC_MESSAGES/blender.mo",
    }


def test_install_bilingual_pair_can_write_manifest_outside_addon_data(tmp_path):
    locale_root = tmp_path / "locale"
    source_dir = locale_root / "ja_JP" / "LC_MESSAGES"
    source_dir.mkdir(parents=True)
    write_mo(source_dir / "blender.mo", MoCatalog({
        "": "Content-Type: text/plain; charset=UTF-8\n",
        "File": "ファイル",
    }))
    (locale_root / "languages").write_text("1:English (US):en_US:100%\n42:Japanese - 日本語:ja_JP:100%\n", encoding="utf-8")
    addon_root = tmp_path / "addon"
    manifest_path = tmp_path / "user_config" / "bilingual_manifest.json"

    bilingual_installer.install_bilingual_pair(
        locale_root,
        "5.0.1",
        addon_root,
        language1_code="en_US",
        language1_name="English",
        language2_code="ja_JP",
        language2_name="日本語",
        manifest_path=manifest_path,
    )

    assert manifest_path.exists()
    assert not (addon_root / "data" / "bilingual_manifest.json").exists()


def test_emergency_cleanup_removes_manifest_files_for_arbitrary_pair(tmp_path):
    locale_root = tmp_path / "locale"
    target = locale_root / "en_de" / "LC_MESSAGES" / "blender.mo"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"bilingual")
    (locale_root / "languages").write_text(
        "1:English (US):en_US:100%\n"
        "# BEGIN Quick Language Switcher bilingual languages\n"
        "998:English + German:en_de:100%\n"
        "# END Quick Language Switcher bilingual languages\n",
        encoding="utf-8",
    )
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps({"installed_files": ["en_de/LC_MESSAGES/blender.mo"]}), encoding="utf-8")

    bilingual_installer.emergency_cleanup(locale_root, manifest_path)

    assert not (locale_root / "en_de").exists()
    assert not manifest_path.exists()


def test_emergency_cleanup_rejects_manifest_paths_outside_locale_root(tmp_path):
    locale_root = tmp_path / "locale"
    locale_root.mkdir()
    outside = tmp_path / "outside.mo"
    outside.write_bytes(b"do not delete")
    languages_path = locale_root / "languages"
    original_languages = patch_languages_text("1:English (US):en_US:100%\n", {"en_ja": "9821:English + Japanese:en_ja:100%"})
    languages_path.write_text(original_languages, encoding="utf-8")
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps({"installed_files": ["../outside.mo"]}), encoding="utf-8")

    with pytest.raises(ValueError, match="Unsafe installed file path"):
        bilingual_installer.emergency_cleanup(locale_root, manifest_path)

    assert languages_path.read_text(encoding="utf-8") == original_languages
    assert outside.exists()


def test_emergency_cleanup_ignores_non_list_installed_files_and_uses_marker(tmp_path):
    locale_root = tmp_path / "locale"
    target = locale_root / "en_ja" / "LC_MESSAGES" / "blender.mo"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"bilingual")
    languages_path = locale_root / "languages"
    languages_path.write_text(
        "1:English (US):en_US:100%\n"
        "# BEGIN Quick Language Switcher bilingual languages\n"
        "9821:English + Japanese:en_ja:100%\n"
        "# END Quick Language Switcher bilingual languages\n",
        encoding="utf-8",
    )
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps({"installed_files": "en_ja/LC_MESSAGES/blender.mo"}), encoding="utf-8")

    bilingual_installer.emergency_cleanup(locale_root, manifest_path)

    assert not target.exists()
    assert "Quick Language Switcher" not in languages_path.read_text(encoding="utf-8")


def test_emergency_cleanup_treats_non_dict_manifest_as_broken_and_uses_marker(tmp_path):
    locale_root = tmp_path / "locale"
    target = locale_root / "en_ja" / "LC_MESSAGES" / "blender.mo"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"bilingual")
    languages_path = locale_root / "languages"
    languages_path.write_text(
        "1:English (US):en_US:100%\n"
        "# BEGIN Quick Language Switcher bilingual languages\n"
        "9821:English + Japanese:en_ja:100%\n"
        "# END Quick Language Switcher bilingual languages\n",
        encoding="utf-8",
    )
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps([]), encoding="utf-8")

    bilingual_installer.emergency_cleanup(locale_root, manifest_path)

    assert not target.exists()
    assert "Quick Language Switcher" not in languages_path.read_text(encoding="utf-8")


def test_write_merged_manifest_ignores_bad_existing_field_types(tmp_path):
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps({
        "installed_language_codes": "bad",
        "installed_language_ids": "bad",
        "installed_files": "bad",
        "added_language_lines": "bad",
    }), encoding="utf-8")

    manifest = bilingual_installer.write_merged_manifest(manifest_path, {
        "installed_language_codes": ["en_ja"],
        "installed_language_ids": {"en_ja": 9821},
        "installed_files": ["en_ja/LC_MESSAGES/blender.mo"],
        "added_language_lines": ["9821:English + Japanese:en_ja:100%"],
    })

    assert manifest["installed_language_codes"] == ["en_ja"]
    assert manifest["installed_language_ids"] == {"en_ja": 9821}
    assert manifest["installed_files"] == ["en_ja/LC_MESSAGES/blender.mo"]


def test_write_merged_manifest_ignores_non_dict_existing_manifest(tmp_path):
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps([]), encoding="utf-8")

    manifest = bilingual_installer.write_merged_manifest(manifest_path, {
        "installed_language_codes": ["en_ja"],
        "installed_files": ["en_ja/LC_MESSAGES/blender.mo"],
    })

    assert manifest["installed_language_codes"] == ["en_ja"]
    assert manifest["installed_files"] == ["en_ja/LC_MESSAGES/blender.mo"]


def test_emergency_cleanup_unpatches_current_languages_without_restoring_stale_backup(tmp_path):
    locale_root = tmp_path / "locale"
    locale_root.mkdir()
    original = "1:English (US):en_US:100%\n"
    current = original + "2:Japanese - 日本語:ja_JP:100%\n"
    patched = current + "# BEGIN Quick Language Switcher bilingual languages\n999:Chinese + English:zh_en:100%\n# END Quick Language Switcher bilingual languages\n"
    (locale_root / "languages").write_text(patched, encoding="utf-8")
    (locale_root / "languages.quick_language_switcher.bak").write_text(original, encoding="utf-8")
    manifest_path = tmp_path / "missing.json"

    bilingual_installer.emergency_cleanup(locale_root, manifest_path)

    assert (locale_root / "languages").read_text(encoding="utf-8") == current


def test_emergency_cleanup_without_manifest_does_not_delete_unmarked_directory(tmp_path):
    locale_root = tmp_path / "locale"
    target = locale_root / "zh_en" / "LC_MESSAGES" / "blender.mo"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"not ours")
    (locale_root / "languages").write_text("1:English (US):en_US:100%\n", encoding="utf-8")

    bilingual_installer.emergency_cleanup(locale_root, tmp_path / "missing.json")

    assert target.exists()


def test_install_bilingual_pair_uses_blender_locale_directory_for_japanese(tmp_path):
    locale_root = tmp_path / "locale"
    source_dir = locale_root / "ja" / "LC_MESSAGES"
    source_dir.mkdir(parents=True)
    write_mo(source_dir / "blender.mo", MoCatalog({
        "": "Content-Type: text/plain; charset=UTF-8\n",
        "File": "ファイル",
    }))
    (locale_root / "languages").write_text(
        "1:English (US):en_US:100%\n42:Japanese - 日本語:ja_JP:100%\n",
        encoding="utf-8",
    )
    addon_root = tmp_path / "addon"

    manifest = bilingual_installer.install_bilingual_pair(
        locale_root,
        "5.0.1",
        addon_root,
        language1_code="en_US",
        language1_name="English",
        language2_code="ja_JP",
        language2_name="日本語",
    )

    assert (locale_root / "en_ja" / "LC_MESSAGES" / "blender.mo").exists()
    assert manifest["source_language"] == "ja_JP"


def test_source_mo_path_uses_real_locale_directory_for_modifier_codes(tmp_path):
    locale_root = tmp_path / "locale"
    (locale_root / "sr" / "LC_MESSAGES").mkdir(parents=True)
    (locale_root / "sr@latin" / "LC_MESSAGES").mkdir(parents=True)
    (locale_root / "sr" / "LC_MESSAGES" / "blender.mo").write_bytes(b"cyrillic")
    (locale_root / "sr@latin" / "LC_MESSAGES" / "blender.mo").write_bytes(b"latin")
    (locale_root / "languages").write_text(
        "28:Serbian (Latin) - Srpski latinica:sr_RS@latin:16%\n",
        encoding="utf-8",
    )

    assert bilingual_installer._source_mo_path(locale_root, "sr_RS@latin") == (
        locale_root / "sr@latin" / "LC_MESSAGES" / "blender.mo"
    )


def test_emergency_cleanup_unpatches_languages_and_removes_marker_files(tmp_path):
    locale_root = tmp_path / "locale"
    (locale_root / "zh_en" / "LC_MESSAGES").mkdir(parents=True)
    (locale_root / "zh_en" / "LC_MESSAGES" / "blender.mo").write_bytes(b"bilingual")
    (locale_root / "en_zh" / "LC_MESSAGES").mkdir(parents=True)
    (locale_root / "en_zh" / "LC_MESSAGES" / "blender.mo").write_bytes(b"bilingual")
    original_languages = "# header\n1:English (US):en_US:100%\n"
    (locale_root / "languages").write_text(original_languages, encoding="utf-8")
    (locale_root / "languages.quick_language_switcher.bak").write_text(original_languages, encoding="utf-8")
    patched = original_languages + "# BEGIN Quick Language Switcher bilingual languages\n999:Chinese + English:zh_en:100%\n# END Quick Language Switcher bilingual languages\n"
    (locale_root / "languages").write_text(patched, encoding="utf-8")
    manifest_path = tmp_path / "manifest.json"

    bilingual_installer.emergency_cleanup(locale_root, manifest_path)

    assert (locale_root / "languages").read_text(encoding="utf-8") == original_languages
    assert not (locale_root / "zh_en").exists()
    assert (locale_root / "en_zh").exists()
    assert (locale_root / "languages.quick_language_switcher.bak").exists()


def test_emergency_cleanup_without_manifest_and_marker_keeps_directory(tmp_path):
    locale_root = tmp_path / "locale"
    (locale_root / "zh_en" / "LC_MESSAGES").mkdir(parents=True)
    (locale_root / "zh_en" / "LC_MESSAGES" / "blender.mo").write_bytes(b"bilingual")
    original = "1:English (US):en_US:100%\n"
    (locale_root / "languages").write_text(original, encoding="utf-8")
    manifest_path = tmp_path / "nonexistent_manifest.json"

    bilingual_installer.emergency_cleanup(locale_root, manifest_path)

    assert (locale_root / "zh_en").exists()
    assert (locale_root / "languages").exists()
