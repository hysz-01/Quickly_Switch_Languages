# Experimental Scope Enable Toggle Implementation Plan

> [!NOTE]
> This document may not reflect the current implementation.
> See the final report for up-to-date state:
> [Final Report](../reports/addon-localization.md)

> **For agentic workers:** REQUIRED SUB-SKILL: Use compose:subagent (recommended) or compose:execute to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a separate enable checkbox for Experimental Region Scope so region-scoped bilingual baking only applies when explicitly enabled.

**Architecture:** Keep the existing collapsible Experimental section as a visibility control. Add a new `enable_experimental_scope` preference that gates install-time scope generation: disabled means pass `scope_keywords=None` and `scope_presets=[]` to the installer, preserving default full bilingual pack behavior. Enabled means use the existing preset/custom-keyword controls exactly as before.

**Tech Stack:** Python 3, Blender Python API, pytest.

## Global Constraints

- Keep the change limited to preferences UI, install-time scope selection, tests, and localization strings.
- Do not change bilingual baking or installer internals.
- Default behavior must be unchanged for existing users unless they explicitly enable Experimental Region Scope.
- Keep the collapsible Experimental section UI pattern.

---

### Task 1: Gate Experimental Scope at Install Time

**Covers:** User request: only apply experimental scope when enabled; otherwise fall back to default advanced behavior.

**Files:**
- Modify: `ui/preferences.py`
- Modify: `core/localization.py`
- Modify: `tests/test_preferences_helpers.py`

**Interfaces:**
- Consumes existing `_enabled_bilingual_presets(prefs) -> list[str]` and `get_scope_keywords(...)`.
- Produces new preference property `enable_experimental_scope: BoolProperty`.
- Produces new helper `_install_scope_settings(prefs, bpy_module) -> tuple[set[str] | None, list[str]]`.

- [ ] **Step 1: Write failing tests**

Add tests to `tests/test_preferences_helpers.py`:

```python
def test_install_scope_settings_falls_back_to_default_when_experimental_disabled():
    preferences = _load_preferences()

    class Prefs:
        enable_experimental_scope = False
        bilingual_scope_node_shader_geometry = True
        bilingual_scope_material_texture = False
        bilingual_scope_animation_rigging = False
        bilingual_scope_viewport_navigation = False
        bilingual_scope_modeling_mesh = True
        bilingual_scope_sculpt_paint = False
        bilingual_scope_compositor_vfx = False
        bilingual_scope_render_lighting = False
        bilingual_custom_keywords = "Node, Custom"

    scope_keywords, scope_presets = preferences._install_scope_settings(Prefs(), preferences.bpy)

    assert scope_keywords is None
    assert scope_presets == []


def test_install_scope_settings_uses_presets_when_experimental_enabled():
    preferences = _load_preferences()

    class Prefs:
        enable_experimental_scope = True
        bilingual_scope_node_shader_geometry = True
        bilingual_scope_material_texture = False
        bilingual_scope_animation_rigging = False
        bilingual_scope_viewport_navigation = False
        bilingual_scope_modeling_mesh = True
        bilingual_scope_sculpt_paint = False
        bilingual_scope_compositor_vfx = False
        bilingual_scope_render_lighting = False
        bilingual_custom_keywords = "Custom"

    scope_keywords, scope_presets = preferences._install_scope_settings(Prefs(), preferences.bpy)

    assert "node_shader_geometry" in scope_presets
    assert "modeling_mesh" in scope_presets
    assert "Custom" in scope_keywords
```

Extend the fake preference fixture used for `draw()` tests with `enable_experimental_scope = False`, then add:

```python
def test_experimental_section_draws_enable_checkbox_when_expanded():
    preferences = _load_preferences()
    prefs = preferences.QuickLanguageSwitcherPreferences()
    prefs.layout = _FakeLayout()
    prefs.favorites = _FakeFavorites()
    prefs.favorites_index = 0
    prefs.show_basic_language_switching = False
    prefs.show_advanced_bilingual = False
    prefs.show_experimental_scope = True
    prefs.enable_experimental_scope = False
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

    assert ("prop", "enable_experimental_scope", {}) in prefs.layout.calls
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest -q tests/test_preferences_helpers.py::test_install_scope_settings_falls_back_to_default_when_experimental_disabled tests/test_preferences_helpers.py::test_install_scope_settings_uses_presets_when_experimental_enabled tests/test_preferences_helpers.py::test_experimental_section_draws_enable_checkbox_when_expanded`

Expected: FAIL because `_install_scope_settings` and `enable_experimental_scope` are not implemented.

- [ ] **Step 3: Implement minimal behavior**

In `ui/preferences.py`, add helper near `_scope_summary()`:

```python
def _install_scope_settings(prefs, bpy_module):
    if not prefs.enable_experimental_scope:
        return None, []
    enabled_presets = _enabled_bilingual_presets(prefs)
    return (
        get_scope_keywords(
            enabled_presets,
            prefs.bilingual_custom_keywords,
            bpy_module=bpy_module,
            blender_version=bpy_module.app.version_string,
        ),
        enabled_presets,
    )
```

Update `LANGUAGE_SWITCHER_OT_install_bilingual_pack.execute()` to call `_install_scope_settings(prefs, bpy)` and pass the returned `scope_keywords` / `scope_presets` to `install_bilingual_pack()`.

Add the new preference property in `QuickLanguageSwitcherPreferences`:

```python
enable_experimental_scope: BoolProperty(
    name=tr("Enable Experimental Region Scope"),
    description="Use selected regions and custom keywords for the next bilingual pack install",
    default=False,
)
```

Render it at the top of the expanded Experimental section:

```python
if self.show_experimental_scope:
    box.prop(self, "enable_experimental_scope")
    box.label(text=tr("When disabled, bilingual pack installation uses the default full scope."), icon='INFO')
```

Add translations for `"Enable Experimental Region Scope"` and `"When disabled, bilingual pack installation uses the default full scope."` in `core/localization.py`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest -q tests/test_preferences_helpers.py`

Expected: PASS.

- [ ] **Step 5: Run full verification**

Run:

```text
python -m py_compile core/localization.py ui/preferences.py tests/test_preferences_helpers.py
pytest -q
```

Expected: compile exits 0 and tests pass.
