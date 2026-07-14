# Quick Language Switcher Release Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use compose:subagent (recommended) or compose:execute to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the remaining release-blocking cleanup edge cases for Quick Language Switcher's bilingual locale installer.

**Architecture:** Keep the existing safety-first policy: generated bilingual locale files are external Blender installation modifications and should be cleaned when the add-on unregisters. Harden only the cleanup/recovery layer with small helpers for manifest normalization, marker-derived current-language switching, bounded language ID allocation, and best-effort documentation.

**Tech Stack:** Blender Python add-on, pytest, pathlib, JSON manifest, Blender locale `languages` file, GNU gettext `.mo` files.

## Global Constraints

- Generated bilingual `.mo` files and `datafiles/locale/languages` entries must be removed on add-on unregister/disable when possible.
- Manual cleanup should report errors; unregister cleanup should be best-effort and must not block add-on disable.
- Emergency cleanup must not rely on a valid manifest before attempting marker-based cleanup.
- Cleanup must not delete files outside `locale_root` or anything other than `LC_MESSAGES/blender.mo` targets recorded by manifest or marker-derived language codes.
- Preserve minimal focused changes; do not refactor unrelated preferences UI or favorites logic.

---

### Task 1: Make Emergency Cleanup Tolerate Bad Manifest During Language Switching

**Files:**
- Modify: `ui/preferences.py:170-180`, `ui/preferences.py:471-480`
- Test: `tests/test_preferences_helpers.py`

**Interfaces:**
- Produces: `_switch_from_installed_bilingual_language(manifest_path: Path) -> None` that returns silently on unreadable or schema-bad manifests.

- [ ] **Step 1: Write failing tests**

Add tests near existing cleanup tests:

```python
def test_switch_from_installed_bilingual_language_ignores_broken_manifest(tmp_path):
    preferences = _load_preferences()
    manifest = tmp_path / "bilingual_manifest.json"
    manifest.write_text("{broken", encoding="utf-8")

    preferences._switch_from_installed_bilingual_language(manifest)


def test_emergency_cleanup_operator_runs_cleanup_with_broken_manifest(monkeypatch, tmp_path):
    preferences = _load_preferences()
    manifest = tmp_path / "bilingual_manifest.json"
    manifest.write_text("{broken", encoding="utf-8")
    calls = []

    monkeypatch.setattr(preferences, "_get_locale_root", lambda: tmp_path / "locale")
    monkeypatch.setattr(preferences, "user_data_path", lambda _filename: manifest)
    monkeypatch.setattr(preferences, "emergency_cleanup", lambda *_args: calls.append("cleanup"))

    operator = preferences.LANGUAGE_SWITCHER_OT_emergency_cleanup()
    operator.report = lambda _level, _message: None

    result = operator.execute(types.SimpleNamespace())

    assert result == {'FINISHED'}
    assert calls == ["cleanup"]
```

- [ ] **Step 2: Verify RED**

Run: `pytest tests/test_preferences_helpers.py::test_switch_from_installed_bilingual_language_ignores_broken_manifest tests/test_preferences_helpers.py::test_emergency_cleanup_operator_runs_cleanup_with_broken_manifest -q`

Expected: at least one test fails because broken manifest currently blocks the helper/operator path.

- [ ] **Step 3: Implement minimal fix**

Wrap manifest parsing and type validation in `_switch_from_installed_bilingual_language()`:

```python
try:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError, UnicodeDecodeError):
    return
codes = manifest.get("installed_language_codes", [])
if not isinstance(codes, list):
    return
installed_codes = {code for code in codes if isinstance(code, str)}
```

- [ ] **Step 4: Verify GREEN**

Run the two tests from Step 2 plus existing emergency cleanup language-switch test.

---

### Task 2: Normalize Manifest Schema for Cleanup and Merge

**Files:**
- Modify: `bilingual/installer.py:142-178`, `bilingual/installer.py:204-259`
- Test: `tests/test_bilingual_installer.py`

**Interfaces:**
- Produces manifest helper functions that treat non-list `installed_files`, `installed_language_codes`, and `added_language_lines` as empty lists, and non-dict `installed_language_ids` as empty dict.

- [ ] **Step 1: Write failing tests**

Add tests:

```python
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
```

- [ ] **Step 2: Verify RED**

Run both tests and confirm failure.

- [ ] **Step 3: Implement minimal schema helpers**

Add small helpers in `bilingual/installer.py`:

```python
def _manifest_list(manifest: dict, key: str) -> list:
    value = manifest.get(key, [])
    return value if isinstance(value, list) else []

def _manifest_dict(manifest: dict, key: str) -> dict:
    value = manifest.get(key, {})
    return value if isinstance(value, dict) else {}
```

Use them in `merge_manifest()`, `uninstall_from_manifest()`, and `emergency_cleanup()`.

- [ ] **Step 4: Verify GREEN**

Run the new tests plus existing manifest cleanup tests.

---

### Task 3: Handle Marker-Only Current-Language Cleanup and Bound Language ID Allocation

**Files:**
- Modify: `ui/preferences.py`
- Modify: `bilingual/installer.py:66-71`
- Test: `tests/test_preferences_helpers.py`, `tests/test_bilingual_installer.py`

**Interfaces:**
- Produces bounded `_available_language_entry_id(language_code: str, languages_text: str) -> int` that raises when IDs above 9999 would be needed.
- Produces marker-based language switching before emergency cleanup when manifest is missing but marker block exists.

- [ ] **Step 1: Write failing tests**

Add language ID bound test:

```python
def test_available_language_entry_id_raises_when_generated_range_full():
    used = "".join(f"{entry_id}:Existing {entry_id}:existing_{entry_id}:100%\n" for entry_id in range(9000, 10000))

    with pytest.raises(ValueError, match="No available language id"):
        bilingual_installer._available_language_entry_id("en_aaf", used)
```

Add marker-only language switch test if a lightweight helper is added in preferences.

- [ ] **Step 2: Verify RED**

Run the new ID-bound test and confirm failure.

- [ ] **Step 3: Implement bounded ID allocation**

Change loop:

```python
while entry_id in existing_ids and entry_id <= 9999:
    entry_id += 1
if entry_id > 9999:
    raise ValueError("No available language id for generated locale")
```

For marker-only current-language switching, add a small local helper in `ui/preferences.py` that reads `locale_root / "languages"`, extracts marker codes using installer helper if exposed, or keep this as a follow-up if it requires broadening public installer API.

- [ ] **Step 4: Verify GREEN**

Run relevant tests.

---

### Task 4: Best-Effort Documentation and Final Verification

**Files:**
- Modify: `README.md:60-72`
- Test: full suite and py_compile.

- [ ] **Step 1: Update README wording**

Change absolute wording to best-effort wording:

```markdown
The add-on attempts to remove generated bilingual packs automatically when disabled or unregistered.
```

- [ ] **Step 2: Run full verification**

Run: `pytest -q`

Expected: all tests pass.

Run: `python -m py_compile "__init__.py" "core\language_manager.py" "core\paths.py" "core\localization.py" "core\keymap.py" "ui\menu.py" "ui\preferences.py" "bilingual\installer.py" "bilingual\baker.py" "bilingual\mo.py" "bilingual\scope.py"`

Expected: no syntax errors.

---

## Self-Review

- Coverage: Plan covers every release-blocking finding from the final review: bad manifest cleanup, schema normalization, marker-only current-language cleanup, bounded ID allocation, README best-effort wording.
- Placeholder scan: No TODO/TBD placeholders remain.
- Scope: Changes are limited to cleanup/recovery safety and docs; no unrelated UI/favorites refactor.
