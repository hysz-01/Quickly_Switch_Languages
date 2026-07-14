# Preferences Interaction Implementation Plan

> [!NOTE]
> This document may not reflect the current implementation.
> See the final report for up-to-date state:
> [Final Report](../reports/preferences-interaction.md)

> **For agentic workers:** REQUIRED SUB-SKILL: Use compose:subagent (recommended) or compose:execute to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve the add-on preferences interaction by separating basic, advanced, and experimental features and making operation feedback more specific.

**Architecture:** Keep all behavior in the current modules. Add small pure helpers in `ui/preferences.py` for status summaries so they can be tested without Blender UI rendering. Update preference panel grouping and operator reports without changing bake, install, or scope algorithms.

**Tech Stack:** Python 3, Blender Python API, pytest.

## Global Constraints

- Do not change bilingual bake semantics.
- Do not add blocking confirmation dialogs in this pass.
- Basic features are normal language switching and favorites management.
- Advanced features are stable bilingual pack install/uninstall actions.
- Experimental features are region scope and custom keyword controls.
- Every operation report must say what happened or what the user should do next.

---

### Task 1: Add Testable Interaction Summary Helpers

**Files:**
- Modify: `ui/preferences.py`
- Modify: `tests/test_preferences.py`

**Interfaces:**
- Produces `_custom_keyword_count(custom_keywords: str) -> int`
- Produces `_scope_summary(prefs) -> str`
- Produces `_manifest_summary(path: Path) -> str`

- [ ] **Step 1: Write failing helper tests**

Add tests to `tests/test_preferences.py`:

```python
def test_scope_summary_counts_selected_regions_and_custom_keywords():
    from Quickly_switch_languages.ui.preferences import _scope_summary

    class Prefs:
        bilingual_scope_node_shader_geometry = True
        bilingual_scope_material_texture = False
        bilingual_scope_animation_rigging = False
        bilingual_scope_viewport_navigation = False
        bilingual_scope_modeling_mesh = True
        bilingual_scope_sculpt_paint = False
        bilingual_scope_compositor_vfx = False
        bilingual_scope_render_lighting = False
        bilingual_custom_keywords = "Bake, Custom Term"

    assert _scope_summary(Prefs()) == "Selected regions: 2 | Custom keywords: 2"
```

```python
def test_manifest_summary_reports_installed_version(tmp_path):
    from Quickly_switch_languages.ui.preferences import _manifest_summary

    manifest = tmp_path / "bilingual_manifest.json"
    manifest.write_text('{"scope_blender_version":"5.0.1","scope_keyword_count":538}', encoding="utf-8")

    assert _manifest_summary(manifest) == "Installed manifest: Blender 5.0.1, 538 keywords"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest -q tests/test_preferences.py::test_scope_summary_counts_selected_regions_and_custom_keywords tests/test_preferences.py::test_manifest_summary_reports_installed_version`

Expected: FAIL because helpers do not exist.

- [ ] **Step 3: Implement helpers**

Add to `ui/preferences.py`:

```python
import json


def _custom_keyword_count(custom_keywords: str) -> int:
    return len([item for item in custom_keywords.split(",") if item.strip()])


def _scope_summary(prefs) -> str:
    return f"Selected regions: {len(_enabled_bilingual_presets(prefs))} | Custom keywords: {_custom_keyword_count(prefs.bilingual_custom_keywords)}"


def _manifest_summary(path: Path) -> str:
    if not path.exists():
        return "Installed manifest: not found"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    version = manifest.get("scope_blender_version") or manifest.get("blender_version", "unknown")
    count = manifest.get("scope_keyword_count", 0)
    return f"Installed manifest: Blender {version}, {count} keywords"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest -q tests/test_preferences.py::test_scope_summary_counts_selected_regions_and_custom_keywords tests/test_preferences.py::test_manifest_summary_reports_installed_version`

Expected: PASS.

---

### Task 2: Rework Preference Panel Copy and Grouping

**Files:**
- Modify: `ui/preferences.py`

**Interfaces:**
- Consumes helpers from Task 1.
- Produces three visible preference sections: `Basic Language Switching`, `Advanced: Bilingual Language Packs`, `Experimental: Region Scope`.

- [ ] **Step 1: Update draw structure**

In `QuickLanguageSwitcherPreferences.draw()`, replace the current `General Settings`, `Bilingual Language Packs`, and `Favorite Languages` layout with:

```python
box = layout.box()
box.label(text="Basic Language Switching", icon='PREFERENCES')
box.prop(self, "save_after_switch")
box.label(text="Manage languages shown in the top-bar switcher.", icon='INFO')
```

Then render the favorites list and add/remove/reorder controls in the same Basic box.

Add an Advanced box:

```python
box = layout.box()
box.label(text="Advanced: Bilingual Language Packs", icon='WORLD')
box.label(text="Installs separate zh_en/en_zh languages into Blender's locale folder.", icon='INFO')
box.label(text="Backs up the languages file. Restart Blender after install or uninstall.", icon='ERROR')
box.label(text=_manifest_summary(data_path("bilingual_manifest.json")), icon='FILE_TICK')
row = box.row(align=True)
row.operator("language_switcher.install_bilingual_pack", icon='IMPORT', text="Install / Update Bilingual Packs")
row.operator("language_switcher.uninstall_bilingual_pack", icon='TRASH', text="Uninstall Bilingual Packs")
```

Add an Experimental box below Advanced:

```python
box = layout.box()
box.label(text="Experimental: Region Scope", icon='FILTER')
box.label(text="Affects the next bilingual pack install; it does not change the current language immediately.", icon='INFO')
box.label(text="Uses exact English labels. Same-name UI labels may still be included.", icon='ERROR')
box.label(text=_scope_summary(self), icon='INFO')
```

Move all region checkboxes and `bilingual_custom_keywords` into this Experimental box.

- [ ] **Step 2: Compile UI module**

Run: `python -m py_compile ui/preferences.py`

Expected: exit code 0.

---

### Task 3: Improve Operator Reports

**Files:**
- Modify: `ui/preferences.py`
- Modify: `ui/menu.py`
- Modify: `tests/test_menu.py`

**Interfaces:**
- Produces clearer `self.report()` messages for common operations.

- [ ] **Step 1: Improve language management reports**

Use these messages:

```python
self.report({'ERROR'}, "Choose a language before adding it.")
self.report({'WARNING'}, f"Language is already in favorites: {self.language_code}")
self.report({'INFO'}, f"Added language: {self.language_name}")
self.report({'WARNING'}, "Select a language before removing.")
self.report({'INFO'}, f"Removed language: {lang.name}")
```

- [ ] **Step 2: Improve bilingual install reports**

Use these messages:

```python
self.report({'INFO'}, f"Installed bilingual packs for Blender {bpy.app.version_string}. Restart Blender, then choose zh_en or en_zh.")
self.report({'INFO'}, "Uninstalled bilingual packs. Restart Blender to refresh the language list.")
```

- [ ] **Step 3: Improve switch report**

In `ui/menu.py`, change switch report to:

```python
self.report({'INFO'}, f"Switched UI language to {self.language_name}")
```

- [ ] **Step 4: Run tests**

Run: `pytest -q tests/test_menu.py tests/test_preferences.py`

Expected: PASS or Blender-only preference tests skip outside Blender.

---

### Task 4: Verify Blender Runtime

**Files:**
- Modify only if verification reveals runtime import or UI draw errors.

- [ ] **Step 1: Run full tests and compile**

Run:

```text
pytest -q
python -m py_compile ui/preferences.py ui/menu.py
```

Expected: tests pass and compile exits 0.

- [ ] **Step 2: Run Blender registration smoke test**

Run Blender `--factory-startup --background` registration/import smoke test.

Expected: `ADDON_REGISTER_OK`.

- [ ] **Step 3: Run Blender install smoke test**

Run the bilingual install smoke test through new UI/import paths.

Expected: install succeeds and reports `zh_en,en_zh`.
