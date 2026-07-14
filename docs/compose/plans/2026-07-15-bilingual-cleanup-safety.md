# Bilingual Cleanup Safety Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use compose:subagent (recommended) or compose:execute to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make generated bilingual locale cleanup safe on add-on unregister while keeping manual cleanup strict and visible to users.

**Architecture:** Keep the existing automatic cleanup-on-unregister product behavior, but split cleanup into two entry points: strict cleanup for user-triggered operators and best-effort cleanup for add-on unregister. Tighten installer rollback and documentation without restructuring the add-on.

**Tech Stack:** Blender Python add-on, pytest, pathlib, JSON manifest, GNU gettext `.mo` locale files.

## Global Constraints

- Disabling the add-on should attempt to remove generated bilingual `.mo` files and language entries to keep Blender's locale directory clean.
- User-triggered cleanup must remain strict: failures should be reported to the operator instead of silently swallowed.
- Unregister-triggered cleanup must be best-effort: failures must not prevent keymap, menu, or class unregister from continuing.
- Cleanup must only remove files recorded by the manifest or language codes declared inside this add-on's marker block.
- Do not broaden directory scanning beyond files/directories explicitly tied to this add-on.
- Keep changes minimal and focused; do not refactor unrelated preferences UI behavior.

---

### Task 1: Split Strict and Best-Effort Cleanup Entrypoints

**Covers:** cleanup lifecycle split, unregister safety.

**Files:**
- Modify: `ui/preferences.py:158-167`
- Modify: `__init__.py:43-49`
- Test: `tests/test_preferences_helpers.py:435-489`

**Interfaces:**
- Consumes: existing `cleanup_bilingual_pack() -> None` behavior.
- Produces: new `cleanup_bilingual_pack_on_unregister() -> None` that swallows cleanup exceptions for add-on unregister only.

- [ ] **Step 1: Write failing tests**

Add tests in `tests/test_preferences_helpers.py` near existing cleanup/unregister tests:

```python
def test_cleanup_bilingual_pack_on_unregister_swallows_cleanup_errors(monkeypatch):
    preferences = _load_preferences()

    def fail_cleanup():
        raise PermissionError("locked locale")

    monkeypatch.setattr(preferences, "cleanup_bilingual_pack", fail_cleanup)

    preferences.cleanup_bilingual_pack_on_unregister()


def test_addon_unregister_uses_best_effort_bilingual_cleanup(monkeypatch):
    _install_fake_bpy()
    sys.modules.pop("Quickly_switch_languages", None)
    import Quickly_switch_languages as addon
    calls = []

    monkeypatch.setattr(addon, "_has_blender_ui", True)
    monkeypatch.setattr(addon, "keymap", types.SimpleNamespace(unregister=lambda: calls.append("keymap")))
    monkeypatch.setattr(addon, "menu", types.SimpleNamespace(unregister=lambda: calls.append("menu")))
    monkeypatch.setattr(addon, "preferences", types.SimpleNamespace(
        cleanup_bilingual_pack_on_unregister=lambda: calls.append("cleanup_best_effort"),
        unregister=lambda: calls.append("preferences"),
    ))

    addon.unregister()

    assert calls == ["cleanup_best_effort", "keymap", "menu", "preferences"]
```

Update the existing `test_addon_unregister_runs_bilingual_cleanup` expectation to use `cleanup_bilingual_pack_on_unregister` instead of `cleanup_bilingual_pack`.

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/test_preferences_helpers.py::test_cleanup_bilingual_pack_on_unregister_swallows_cleanup_errors tests/test_preferences_helpers.py::test_addon_unregister_uses_best_effort_bilingual_cleanup -q`

Expected: FAIL because `cleanup_bilingual_pack_on_unregister` does not exist and `unregister()` still calls strict cleanup.

- [ ] **Step 3: Implement minimal cleanup split**

In `ui/preferences.py`, keep strict cleanup unchanged and add:

```python
def cleanup_bilingual_pack_on_unregister() -> None:
    try:
        cleanup_bilingual_pack()
    except Exception:
        pass
```

In `__init__.py`, change:

```python
preferences.cleanup_bilingual_pack()
```

to:

```python
preferences.cleanup_bilingual_pack_on_unregister()
```

- [ ] **Step 4: Run task tests**

Run: `pytest tests/test_preferences_helpers.py::test_cleanup_bilingual_pack_on_unregister_swallows_cleanup_errors tests/test_preferences_helpers.py::test_addon_unregister_uses_best_effort_bilingual_cleanup tests/test_preferences_helpers.py::test_cleanup_bilingual_pack_uninstalls_from_manifest -q`

Expected: PASS.

---

### Task 2: Add Rollback for Install and Uninstall Language File Writes

**Covers:** safe locale file modification, cleanup reliability.

**Files:**
- Modify: `bilingual/installer.py:175-183`
- Modify: `bilingual/installer.py:265-294`
- Test: `tests/test_bilingual_installer.py`

**Interfaces:**
- Consumes: existing `unpatch_languages_text(text: str) -> str` and `patch_languages_text(text: str, entries: dict[str, str]) -> str`.
- Produces: rollback behavior inside `_install_and_patch()` and `uninstall_from_manifest()`.

- [ ] **Step 1: Write failing tests**

Add tests to `tests/test_bilingual_installer.py`:

```python
class _FailingWritePath:
    def __init__(self, real_path, fail_on_write_number):
        self.real_path = real_path
        self.fail_on_write_number = fail_on_write_number
        self.write_count = 0

    def exists(self):
        return self.real_path.exists()

    def read_text(self, *args, **kwargs):
        return self.real_path.read_text(*args, **kwargs)

    def write_text(self, *args, **kwargs):
        self.write_count += 1
        if self.write_count == self.fail_on_write_number:
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
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/test_bilingual_installer.py::test_install_and_patch_restores_languages_when_patch_write_fails tests/test_bilingual_installer.py::test_uninstall_restores_languages_when_unpatch_write_fails -q`

Expected: FAIL because rollback is not implemented.

- [ ] **Step 3: Implement rollback**

In `_install_and_patch()`, initialize `original = None` before `try`. After reading original, if later write fails, best-effort restore original before removing copied files:

```python
installed_files: list[str] = []
original = None
try:
    ...
    original = languages_path.read_text(encoding="utf-8")
    languages_path.write_text(patch_languages_text(original, language_entries), encoding="utf-8")
except Exception:
    if original is not None:
        try:
            languages_path.write_text(original, encoding="utf-8")
        except OSError:
            pass
    ...
    raise
```

In `uninstall_from_manifest()`, read original before writing unpatched text and restore it if write fails:

```python
if languages_path.exists():
    original = languages_path.read_text(encoding="utf-8")
    try:
        languages_path.write_text(unpatch_languages_text(original), encoding="utf-8")
    except Exception:
        try:
            languages_path.write_text(original, encoding="utf-8")
        except OSError:
            pass
        raise
```

- [ ] **Step 4: Run task tests**

Run: `pytest tests/test_bilingual_installer.py::test_install_and_patch_restores_languages_when_patch_write_fails tests/test_bilingual_installer.py::test_uninstall_restores_languages_when_unpatch_write_fails tests/test_bilingual_installer.py::test_uninstall_uses_manifest_and_leaves_unlisted_files -q`

Expected: PASS.

---

### Task 3: Document Automatic Cleanup-on-Unregister Behavior

**Covers:** user-visible lifecycle semantics.

**Files:**
- Modify: `README.md:48-70`
- Modify: `ui/preferences.py:590-593`
- Test: `tests/test_preferences_helpers.py:323-357`

**Interfaces:**
- Consumes: existing `tr(text: str) -> str` translation helper.
- Produces: visible warning text that generated bilingual packs are removed when the add-on is disabled.

- [ ] **Step 1: Write failing test**

Add to `tests/test_preferences_helpers.py` near advanced-section draw tests:

```python
def test_advanced_section_warns_generated_packs_are_removed_on_disable():
    preferences = _load_preferences()
    prefs = preferences.QuickLanguageSwitcherPreferences()
    prefs.layout = _FakeLayout()
    prefs.favorites = _FakeFavorites()
    prefs.favorites_index = 0
    prefs.show_basic_language_switching = False
    prefs.show_advanced_bilingual = True
    prefs.show_experimental_scope = False
    prefs.enable_experimental_scope = False
    prefs.bilingual_language_1 = "zh_HANS"
    prefs.bilingual_language_2 = "en_US"
    prefs.bilingual_scope_node_shader_geometry = True
    prefs.bilingual_scope_material_texture = False
    prefs.bilingual_scope_animation_rigging = False
    prefs.bilingual_scope_viewport_navigation = False
    prefs.bilingual_scope_modeling_mesh = False
    prefs.bilingual_scope_sculpt_paint = False
    prefs.bilingual_scope_compositor_vfx = False
    prefs.bilingual_scope_render_lighting = False
    prefs.bilingual_custom_keywords = ""

    prefs.draw(types.SimpleNamespace())

    assert any(
        call[0] == "label" and call[1] == "Generated bilingual packs are removed automatically when this add-on is disabled."
        for call in prefs.layout.calls
    )
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest tests/test_preferences_helpers.py::test_advanced_section_warns_generated_packs_are_removed_on_disable -q`

Expected: FAIL because the warning label is not displayed.

- [ ] **Step 3: Add UI warning and README text**

In `ui/preferences.py`, add this label inside the expanded advanced bilingual section after the restart note:

```python
box.label(text=tr("Generated bilingual packs are removed automatically when this add-on is disabled."), icon='ERROR')
```

In `README.md`, add under `## Bilingual Language Packs`:

```markdown
Generated bilingual packs are removed automatically when the add-on is disabled or unregistered. This is intentional: the add-on restores Blender's locale directory to a clean state when it is not active. Re-enable the add-on and install the bilingual pack again if you need it later.
```

In `## Safety Boundaries`, add:

```markdown
- Disabling or unregistering the add-on attempts a best-effort cleanup of generated bilingual locale files.
```

- [ ] **Step 4: Run task tests**

Run: `pytest tests/test_preferences_helpers.py::test_advanced_section_warns_generated_packs_are_removed_on_disable -q`

Expected: PASS.

---

### Task 4: Full Verification

**Covers:** regression safety.

**Files:**
- Test only.

**Interfaces:**
- Consumes: all previous task changes.
- Produces: verified passing test and compile output.

- [ ] **Step 1: Run unit tests**

Run: `pytest -q`

Expected: all tests pass.

- [ ] **Step 2: Compile key modules**

Run: `python -m py_compile "__init__.py" "core\language_manager.py" "core\paths.py" "core\localization.py" "core\keymap.py" "ui\menu.py" "ui\preferences.py" "bilingual\installer.py" "bilingual\baker.py" "bilingual\mo.py" "bilingual\scope.py"`

Expected: command exits with status 0 and prints no syntax errors.

- [ ] **Step 3: Summarize implementation**

Report changed behavior:

```text
- Add-on unregister now invokes best-effort bilingual cleanup, so cleanup failures do not block unregister.
- Manual uninstall remains strict and reports cleanup errors to the user.
- Installer and uninstaller restore the languages file when write failures occur.
- Preferences UI and README document that disabling the add-on removes generated bilingual packs.
```

---

## Self-Review

- Spec coverage: The agreed behavior is covered by Tasks 1-3, and regression verification is covered by Task 4.
- Placeholder scan: No placeholders or deferred implementation steps remain.
- Type consistency: New public helper is consistently named `cleanup_bilingual_pack_on_unregister() -> None`; strict helper remains `cleanup_bilingual_pack() -> None`.
