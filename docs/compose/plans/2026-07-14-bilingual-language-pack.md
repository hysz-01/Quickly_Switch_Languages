# Bilingual Language Pack Implementation Plan

> [!NOTE]
> This document may not reflect the current implementation.
> See the final report for up-to-date state:
> [Final Report](../reports/bilingual-language-pack.md)

> **For agentic workers:** REQUIRED SUB-SKILL: Use compose:subagent (recommended) or compose:execute to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a safe, reversible workflow for baking and installing Blender 5.x `zh_HANS` bilingual language packs as `zh_en` and `en_zh`.

**Architecture:** Keep translation baking and Blender resource installation separate. Pure Python modules parse/write `.mo`, generate bilingual catalogs, patch `datafiles/locale/languages`, and track installed files in a manifest; Blender UI operators call these modules and warn users before modifying Blender language resources.

**Tech Stack:** Python standard library, Blender Python API, pytest, GNU gettext `.mo` binary format.

## Global Constraints

- First implementation supports only source language `zh_HANS` and output language codes `zh_en` and `en_zh`.
- Do not replace `zh_HANS/LC_MESSAGES/blender.mo`.
- Do not edit `_bl_i18n_utils/settings.py`.
- Do not monkey patch `bpy.app.translations` or Blender translation functions.
- Generated files are cached under `generated/<blender_version>/...` inside the add-on.
- Installed files are copied into Blender's `datafiles/locale` folder.
- Installation and uninstall require a Blender restart to take effect.
- No privilege escalation; report non-writable Blender resource folders.
- All resource modifications must be reversible via manifest-driven uninstall.

---

## File Structure

- Create `mo_utils.py`: pure Python `.mo` reader/writer and `MoCatalog` data structure.
- Create `bilingual_baker.py`: turns a source `zh_HANS` `.mo` into `zh_en` and `en_zh` catalogs.
- Create `bilingual_installer.py`: detects Blender locale paths, patches `languages`, copies installed `.mo` files, writes manifest, uninstalls installed resources.
- Create `test_mo_utils.py`: unit tests for `.mo` parsing/writing.
- Create `test_bilingual_baker.py`: unit tests for bilingual generation rules.
- Create `test_bilingual_installer.py`: unit tests for languages patching, conflict detection, manifest uninstall.
- Modify `preferences.py`: add a Bilingual Language Packs UI section and operators.
- Modify `__init__.py`: register any new operators through `preferences.register()` only; no new top-level Blender imports outside existing guarded flow.

---

### Task 1: Pure Python `.mo` Reader And Writer

**Covers:** [S5, S11]

**Files:**
- Create: `mo_utils.py`
- Create: `test_mo_utils.py`

**Interfaces:**
- Produces: `MoCatalog(entries: dict[str, str])`
- Produces: `read_mo(path: str | os.PathLike) -> MoCatalog`
- Produces: `write_mo(path: str | os.PathLike, catalog: MoCatalog) -> None`

- [ ] **Step 1: Write failing roundtrip test**

Create `test_mo_utils.py` with:

```python
from pathlib import Path

from mo_utils import MoCatalog, read_mo, write_mo


def test_write_then_read_roundtrips_context_and_header(tmp_path):
    path = tmp_path / "blender.mo"
    catalog = MoCatalog({
        "": "Content-Type: text/plain; charset=UTF-8\n",
        "File": "文件",
        "Operator\x04Open": "打开",
    })

    write_mo(path, catalog)
    result = read_mo(path)

    assert result.entries == catalog.entries
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest -q test_mo_utils.py`

Expected: FAIL with `ModuleNotFoundError: No module named 'mo_utils'`.

- [ ] **Step 3: Implement minimal `.mo` read/write**

Create `mo_utils.py`:

```python
import os
import struct
from dataclasses import dataclass
from pathlib import Path


_MO_MAGIC_LE = 0x950412DE
_MO_MAGIC_BE = 0xDE120495


@dataclass(frozen=True)
class MoCatalog:
    entries: dict[str, str]


def read_mo(path: str | os.PathLike) -> MoCatalog:
    data = Path(path).read_bytes()
    magic = struct.unpack("<I", data[:4])[0]
    if magic == _MO_MAGIC_LE:
        endian = "<"
    elif magic == _MO_MAGIC_BE:
        endian = ">"
    else:
        raise ValueError("Invalid .mo magic number")

    _magic, _revision, count, original_offset, translated_offset, _hash_size, _hash_offset = struct.unpack(
        endian + "7I", data[:28]
    )
    entries = {}
    for index in range(count):
        orig_len, orig_pos = struct.unpack(endian + "2I", data[original_offset + index * 8:original_offset + (index + 1) * 8])
        trans_len, trans_pos = struct.unpack(endian + "2I", data[translated_offset + index * 8:translated_offset + (index + 1) * 8])
        original = data[orig_pos:orig_pos + orig_len].decode("utf-8")
        translated = data[trans_pos:trans_pos + trans_len].decode("utf-8")
        entries[original] = translated
    return MoCatalog(entries)


def write_mo(path: str | os.PathLike, catalog: MoCatalog) -> None:
    items = sorted(catalog.entries.items(), key=lambda item: item[0])
    ids = [key.encode("utf-8") for key, _value in items]
    strs = [value.encode("utf-8") for _key, value in items]

    count = len(items)
    header_size = 28
    original_table_offset = header_size
    translated_table_offset = original_table_offset + count * 8
    string_offset = translated_table_offset + count * 8

    original_table = []
    translated_table = []
    string_data = bytearray()

    for msgid in ids:
        original_table.append((len(msgid), string_offset + len(string_data)))
        string_data.extend(msgid + b"\0")

    for msgstr in strs:
        translated_table.append((len(msgstr), string_offset + len(string_data)))
        string_data.extend(msgstr + b"\0")

    output = bytearray()
    output.extend(struct.pack("<7I", _MO_MAGIC_LE, 0, count, original_table_offset, translated_table_offset, 0, 0))
    for length, offset in original_table:
        output.extend(struct.pack("<2I", length, offset))
    for length, offset in translated_table:
        output.extend(struct.pack("<2I", length, offset))
    output.extend(string_data)

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(output)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest -q test_mo_utils.py`

Expected: PASS.

---

### Task 2: Bilingual Bake Rules

**Covers:** [S2, S4, S5, S11]

**Files:**
- Create: `bilingual_baker.py`
- Create: `test_bilingual_baker.py`

**Interfaces:**
- Consumes: `MoCatalog` from `mo_utils.py`
- Produces: `bake_bilingual_catalogs(source: MoCatalog) -> dict[str, MoCatalog]`
- Produces: `bake_bilingual_files(source_mo: Path, output_root: Path) -> dict[str, Path]`

- [ ] **Step 1: Write failing bake tests**

Create `test_bilingual_baker.py`:

```python
from mo_utils import MoCatalog
from bilingual_baker import bake_bilingual_catalogs


def test_bake_generates_chinese_first_and_english_first_catalogs():
    source = MoCatalog({
        "": "Content-Type: text/plain; charset=UTF-8\n",
        "File": "文件",
        "Save As": "另存为",
    })

    result = bake_bilingual_catalogs(source)

    assert result["zh_en"].entries[""] == source.entries[""]
    assert result["zh_en"].entries["File"] == "文件 / File"
    assert result["en_zh"].entries["File"] == "File / 文件"


def test_bake_preserves_empty_identical_and_placeholder_mismatch_entries():
    source = MoCatalog({
        "": "Content-Type: text/plain; charset=UTF-8\n",
        "Untranslated": "",
        "Same": "Same",
        "Value: %s": "值：%d",
        "Name: %s": "名称：%s",
    })

    result = bake_bilingual_catalogs(source)

    assert result["zh_en"].entries["Untranslated"] == ""
    assert result["zh_en"].entries["Same"] == "Same"
    assert result["zh_en"].entries["Value: %s"] == "值：%d"
    assert result["zh_en"].entries["Name: %s"] == "名称：%s / Name: %s"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest -q test_bilingual_baker.py`

Expected: FAIL with `ModuleNotFoundError: No module named 'bilingual_baker'`.

- [ ] **Step 3: Implement minimal baker**

Create `bilingual_baker.py`:

```python
import re
from pathlib import Path

from mo_utils import MoCatalog, read_mo, write_mo


OUTPUT_LANGUAGES = ("zh_en", "en_zh")
_PLACEHOLDER_RE = re.compile(r"%(?:\([^)]+\))?[#0 +\-]*(?:\d+|\*)?(?:\.\d+)?[hlL]?[diouxXeEfFgGcrs%]|\{[^{}]+\}")


def _placeholders(text: str) -> list[str]:
    return _PLACEHOLDER_RE.findall(text)


def _can_combine(msgid: str, msgstr: str) -> bool:
    return bool(msgid and msgstr and msgid != msgstr and _placeholders(msgid) == _placeholders(msgstr))


def bake_bilingual_catalogs(source: MoCatalog) -> dict[str, MoCatalog]:
    zh_en = {}
    en_zh = {}
    for msgid, msgstr in source.entries.items():
        if msgid == "" or not _can_combine(msgid, msgstr):
            zh_en[msgid] = msgstr
            en_zh[msgid] = msgstr
            continue
        zh_en[msgid] = f"{msgstr} / {msgid}"
        en_zh[msgid] = f"{msgid} / {msgstr}"
    return {
        "zh_en": MoCatalog(zh_en),
        "en_zh": MoCatalog(en_zh),
    }


def bake_bilingual_files(source_mo: Path, output_root: Path) -> dict[str, Path]:
    catalogs = bake_bilingual_catalogs(read_mo(source_mo))
    outputs = {}
    for lang_code, catalog in catalogs.items():
        output_path = output_root / lang_code / "LC_MESSAGES" / "blender.mo"
        write_mo(output_path, catalog)
        outputs[lang_code] = output_path
    return outputs
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest -q test_bilingual_baker.py test_mo_utils.py`

Expected: PASS.

---

### Task 3: Languages File Patching And Manifest Uninstall

**Covers:** [S6, S7, S8, S9, S10, S11]

**Files:**
- Create: `bilingual_installer.py`
- Create: `test_bilingual_installer.py`

**Interfaces:**
- Produces: `BEGIN_MARKER`, `END_MARKER`
- Produces: `patch_languages_text(text: str, entries: dict[str, str]) -> str`
- Produces: `unpatch_languages_text(text: str) -> str`
- Produces: `write_manifest(path: Path, manifest: dict) -> None`
- Produces: `read_manifest(path: Path) -> dict`
- Produces: `uninstall_from_manifest(locale_root: Path, languages_path: Path, manifest_path: Path) -> None`

- [ ] **Step 1: Write failing patcher tests**

Create `test_bilingual_installer.py`:

```python
import json
from pathlib import Path

import pytest

from bilingual_installer import (
    patch_languages_text,
    unpatch_languages_text,
    uninstall_from_manifest,
)


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest -q test_bilingual_installer.py`

Expected: FAIL with `ModuleNotFoundError: No module named 'bilingual_installer'`.

- [ ] **Step 3: Implement patcher and manifest uninstall**

Create `bilingual_installer.py`:

```python
import json
import os
import re
import shutil
from pathlib import Path


BEGIN_MARKER = "# BEGIN Quick Language Switcher bilingual languages"
END_MARKER = "# END Quick Language Switcher bilingual languages"


def _language_codes(text: str) -> set[str]:
    codes = set()
    for line in text.splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split(":")
        if len(parts) >= 3:
            codes.add(parts[2])
    return codes


def unpatch_languages_text(text: str) -> str:
    pattern = re.compile(rf"\n?{re.escape(BEGIN_MARKER)}.*?{re.escape(END_MARKER)}\n?", re.DOTALL)
    result = pattern.sub("\n", text)
    while "\n\n\n" in result:
        result = result.replace("\n\n\n", "\n\n")
    return result


def patch_languages_text(text: str, entries: dict[str, str]) -> str:
    clean = unpatch_languages_text(text)
    existing_codes = _language_codes(clean)
    for code in entries:
        if code in existing_codes:
            raise ValueError(f"Conflicting language code: {code}")
    block = "\n".join([BEGIN_MARKER, *entries.values(), END_MARKER]) + "\n"
    separator = "" if clean.endswith("\n") else "\n"
    return clean + separator + block


def write_manifest(path: Path, manifest: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def read_manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _remove_empty_parents(path: Path, stop_at: Path) -> None:
    current = path
    while current != stop_at and current.exists():
        try:
            current.rmdir()
        except OSError:
            return
        current = current.parent


def uninstall_from_manifest(locale_root: Path, languages_path: Path, manifest_path: Path) -> None:
    manifest = read_manifest(manifest_path)
    if languages_path.exists():
        languages_path.write_text(unpatch_languages_text(languages_path.read_text(encoding="utf-8")), encoding="utf-8")
    for relative in manifest.get("installed_files", []):
        target = locale_root / Path(relative)
        if target.exists():
            target.unlink()
        _remove_empty_parents(target.parent, locale_root)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest -q test_bilingual_installer.py`

Expected: PASS.

---

### Task 4: Blender Locale Install Service

**Covers:** [S3, S4, S6, S7, S10, S11]

**Files:**
- Modify: `bilingual_installer.py`
- Modify: `test_bilingual_installer.py`

**Interfaces:**
- Consumes: `bake_bilingual_files(source_mo: Path, output_root: Path) -> dict[str, Path]`
- Produces: `BILINGUAL_LANGUAGE_ENTRIES`
- Produces: `install_bilingual_pack(locale_root: Path, blender_version: str, addon_root: Path) -> dict`

- [ ] **Step 1: Add failing install service test**

Append to `test_bilingual_installer.py`:

```python
from mo_utils import MoCatalog, write_mo
from bilingual_installer import install_bilingual_pack


def test_install_bilingual_pack_bakes_copies_patches_and_writes_manifest(tmp_path):
    locale_root = tmp_path / "locale"
    source_dir = locale_root / "zh_HANS" / "LC_MESSAGES"
    source_dir.mkdir(parents=True)
    write_mo(source_dir / "blender.mo", MoCatalog({"": "Content-Type: text/plain; charset=UTF-8\n", "File": "文件"}))
    (locale_root / "languages").write_text("1:English (US):en_US:100%\n13:Chinese (Simplified) - 简体中文:zh_HANS:100%\n", encoding="utf-8")
    addon_root = tmp_path / "addon"

    manifest = install_bilingual_pack(locale_root, "5.0.1", addon_root)

    assert (locale_root / "zh_en" / "LC_MESSAGES" / "blender.mo").exists()
    assert (locale_root / "en_zh" / "LC_MESSAGES" / "blender.mo").exists()
    assert "zh_en" in (locale_root / "languages").read_text(encoding="utf-8")
    assert (addon_root / "bilingual_manifest.json").exists()
    assert manifest["blender_version"] == "5.0.1"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest -q test_bilingual_installer.py::test_install_bilingual_pack_bakes_copies_patches_and_writes_manifest`

Expected: FAIL with `ImportError` or `AttributeError` for `install_bilingual_pack`.

- [ ] **Step 3: Implement install service**

Append to `bilingual_installer.py`:

```python
import hashlib

from bilingual_baker import bake_bilingual_files


BILINGUAL_LANGUAGE_ENTRIES = {
    "en_zh": "998:English + Chinese - English (简体中文):en_zh:100%",
    "zh_en": "999:Chinese + English - 简体中文 (English):zh_en:100%",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _require_writable(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)
    if not os.access(path, os.W_OK):
        raise PermissionError(f"Not writable: {path}")


def install_bilingual_pack(locale_root: Path, blender_version: str, addon_root: Path) -> dict:
    languages_path = locale_root / "languages"
    source_mo = locale_root / "zh_HANS" / "LC_MESSAGES" / "blender.mo"
    _require_writable(locale_root)
    _require_writable(languages_path)
    if not source_mo.exists():
        raise FileNotFoundError(source_mo)

    generated_root = addon_root / "generated" / blender_version
    generated = bake_bilingual_files(source_mo, generated_root)

    backup_path = locale_root / "languages.quick_language_switcher.bak"
    if not backup_path.exists():
        shutil.copy2(languages_path, backup_path)

    installed_files = []
    try:
        for code, source in generated.items():
            target = locale_root / code / "LC_MESSAGES" / "blender.mo"
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            installed_files.append(str(Path(code) / "LC_MESSAGES" / "blender.mo"))

        original_languages = languages_path.read_text(encoding="utf-8")
        languages_path.write_text(patch_languages_text(original_languages, BILINGUAL_LANGUAGE_ENTRIES), encoding="utf-8")
    except Exception:
        for relative in installed_files:
            target = locale_root / Path(relative)
            if target.exists():
                target.unlink()
            _remove_empty_parents(target.parent, locale_root)
        raise

    manifest = {
        "blender_version": blender_version,
        "locale_root": str(locale_root),
        "source_language": "zh_HANS",
        "source_mo_hash": _sha256(source_mo),
        "languages_hash_before": hashlib.sha256(original_languages.encode("utf-8")).hexdigest(),
        "installed_language_codes": ["zh_en", "en_zh"],
        "installed_files": installed_files,
        "added_language_lines": list(BILINGUAL_LANGUAGE_ENTRIES.values()),
    }
    write_manifest(addon_root / "bilingual_manifest.json", manifest)
    return manifest
```

- [ ] **Step 4: Run installer tests**

Run: `pytest -q test_bilingual_installer.py test_bilingual_baker.py test_mo_utils.py`

Expected: PASS.

---

### Task 5: Blender Preferences UI And Operators

**Covers:** [S3, S6, S8, S9, S10]

**Files:**
- Modify: `preferences.py`
- Modify: `test_preferences.py` only if adding Blender-script assertions is practical; otherwise keep manual Blender verification in `test_integration.py` comments.

**Interfaces:**
- Consumes: `install_bilingual_pack(locale_root: Path, blender_version: str, addon_root: Path) -> dict`
- Consumes: `uninstall_from_manifest(locale_root: Path, languages_path: Path, manifest_path: Path) -> None`

- [ ] **Step 1: Add operators to preferences.py**

Add imports near the top:

```python
from pathlib import Path
from .bilingual_installer import install_bilingual_pack, uninstall_from_manifest
```

Add helper:

```python
def _get_locale_root():
    return Path(bpy.utils.resource_path('LOCAL')) / "datafiles" / "locale"
```

Add operator classes before `QuickLanguageSwitcherPreferences`:

```python
class LANGUAGE_SWITCHER_OT_install_bilingual_pack(Operator):
    """Bake and install bilingual Blender language packs"""
    bl_idname = "language_switcher.install_bilingual_pack"
    bl_label = "Install Bilingual Language Pack"
    bl_options = {'REGISTER'}

    def execute(self, context):
        addon_root = Path(__file__).parent
        locale_root = _get_locale_root()
        try:
            install_bilingual_pack(locale_root, bpy.app.version_string, addon_root)
        except Exception as exc:
            self.report({'ERROR'}, f"Failed to install bilingual language pack: {exc}")
            return {'CANCELLED'}
        self.report({'INFO'}, "Bilingual language pack installed. Restart Blender to use zh_en/en_zh.")
        return {'FINISHED'}


class LANGUAGE_SWITCHER_OT_uninstall_bilingual_pack(Operator):
    """Uninstall bilingual Blender language packs installed by this add-on"""
    bl_idname = "language_switcher.uninstall_bilingual_pack"
    bl_label = "Uninstall Bilingual Language Pack"
    bl_options = {'REGISTER'}

    def execute(self, context):
        addon_root = Path(__file__).parent
        locale_root = _get_locale_root()
        manifest_path = addon_root / "bilingual_manifest.json"
        try:
            uninstall_from_manifest(locale_root, locale_root / "languages", manifest_path)
        except Exception as exc:
            self.report({'ERROR'}, f"Failed to uninstall bilingual language pack: {exc}")
            return {'CANCELLED'}
        self.report({'INFO'}, "Bilingual language pack uninstalled. Restart Blender to update language list.")
        return {'FINISHED'}
```

- [ ] **Step 2: Register operators**

Add both classes to `classes` before `QuickLanguageSwitcherPreferences`:

```python
    LANGUAGE_SWITCHER_OT_install_bilingual_pack,
    LANGUAGE_SWITCHER_OT_uninstall_bilingual_pack,
```

- [ ] **Step 3: Add warning UI section**

Inside `QuickLanguageSwitcherPreferences.draw()`, after General Settings and before Favorite Languages, add:

```python
        box = layout.box()
        box.label(text="Bilingual Language Packs", icon='WORLD')
        box.label(text="This modifies Blender language resource files and requires restarting Blender.", icon='ERROR')
        box.label(text="The add-on backs up the languages file and installs zh_en/en_zh as separate languages.")
        row = box.row(align=True)
        row.operator("language_switcher.install_bilingual_pack", icon='IMPORT')
        row.operator("language_switcher.uninstall_bilingual_pack", icon='TRASH')
```

- [ ] **Step 4: Run syntax and unit tests**

Run: `python -m py_compile preferences.py bilingual_installer.py bilingual_baker.py mo_utils.py`

Expected: no output.

Run: `pytest -q`

Expected: all pure Python tests pass; Blender-only tests are skipped outside Blender.

---

### Task 6: Blender Manual Verification Script

**Covers:** [S11]

**Files:**
- Modify: `test_integration.py`
- Create: `docs/compose/reports/bilingual-manual-test-checklist.md`

**Interfaces:**
- Consumes: Blender UI operators from Task 5.

- [ ] **Step 1: Add checklist report**

Create `docs/compose/reports/bilingual-manual-test-checklist.md`:

```markdown
# Bilingual Language Pack Manual Test Checklist

1. Open Blender 5.0.1 portable.
2. Enable Quick Language Switcher.
3. Open add-on preferences through `Manage Languages...`.
4. Click `Install Bilingual Language Pack`.
5. Confirm the report says restart is required.
6. Restart Blender.
7. Open Preferences > Interface > Translation > Language.
8. Confirm `zh_en` and `en_zh` appear.
9. Switch to `zh_en` and verify UI labels show Chinese plus English.
10. Switch to `en_zh` and verify UI labels show English plus Chinese.
11. Open Quick Language Switcher preferences.
12. Click `Uninstall Bilingual Language Pack`.
13. Restart Blender.
14. Confirm `zh_en` and `en_zh` no longer appear.
```

- [ ] **Step 2: Run available verification**

Run: `pytest -q`

Expected: all pure Python tests pass; Blender-only tests are skipped outside Blender.

Run: `python -m py_compile *.py`

Expected: no syntax errors.

---

## Self-Review

- Spec coverage: Tasks cover [S1] through [S11]. [S1] is reflected in the architecture and Task 5 constraints; [S2]-[S11] have explicit task coverage.
- Placeholder scan: No `TBD`, `TODO`, or unspecified test steps remain.
- Type consistency: `MoCatalog`, `read_mo`, `write_mo`, `bake_bilingual_catalogs`, `bake_bilingual_files`, `patch_languages_text`, `unpatch_languages_text`, `install_bilingual_pack`, and `uninstall_from_manifest` signatures are defined before use.
