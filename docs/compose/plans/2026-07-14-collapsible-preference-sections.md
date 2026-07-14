# Collapsible Preference Sections Implementation Plan

> [!NOTE]
> This document may not reflect the current implementation.
> See the final report for up-to-date state:
> [Final Report](../reports/collapsible-preference-sections.md)

> **For agentic workers:** REQUIRED SUB-SKILL: Use compose:subagent (recommended) or compose:execute to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the add-on preference sections collapsible so the panel no longer opens as one long wall of controls.

**Architecture:** Add three Boolean UI-state properties to `QuickLanguageSwitcherPreferences` and render each section header as a triangle-toggle row. Basic opens by default; Advanced and Experimental are collapsed by default but keep one-line status summaries visible.

**Tech Stack:** Python 3, Blender Python API, pytest.

## Global Constraints

- Do not change install, bake, or language-switch behavior.
- Basic Language Switching defaults expanded.
- Advanced and Experimental default collapsed.
- Collapsed sections must still show a short status summary.
- Use Blender-native disclosure triangle icons: `TRIA_DOWN` for expanded, `TRIA_RIGHT` for collapsed.

---

### Task 1: Add Collapsible Section State and Header Helper

**Files:**
- Modify: `ui/preferences.py`
- Modify: `tests/test_preferences_helpers.py`

**Interfaces:**
- Produces `_section_icon(is_open: bool) -> str`
- Produces Boolean properties `show_basic_language_switching`, `show_advanced_bilingual`, `show_experimental_scope`

- [ ] **Step 1: Write failing icon helper test**

Add to `tests/test_preferences_helpers.py`:

```python
def test_section_icon_matches_open_state():
    preferences = _load_preferences()

    assert preferences._section_icon(True) == "TRIA_DOWN"
    assert preferences._section_icon(False) == "TRIA_RIGHT"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest -q tests/test_preferences_helpers.py::test_section_icon_matches_open_state`

Expected: FAIL because `_section_icon` does not exist.

- [ ] **Step 3: Implement helper and properties**

Add helper:

```python
def _section_icon(is_open: bool) -> str:
    return 'TRIA_DOWN' if is_open else 'TRIA_RIGHT'
```

Add properties to `QuickLanguageSwitcherPreferences`:

```python
show_basic_language_switching: BoolProperty(name="Show Basic Language Switching", default=True)
show_advanced_bilingual: BoolProperty(name="Show Advanced Bilingual Packs", default=False)
show_experimental_scope: BoolProperty(name="Show Experimental Region Scope", default=False)
```

- [ ] **Step 4: Run helper test**

Run: `pytest -q tests/test_preferences_helpers.py::test_section_icon_matches_open_state`

Expected: PASS.

---

### Task 2: Render Collapsible Sections

**Files:**
- Modify: `ui/preferences.py`

**Interfaces:**
- Consumes section state properties and `_section_icon()`.

- [ ] **Step 1: Replace static labels with toggle rows**

For each section, draw a header row like:

```python
row = box.row(align=True)
row.prop(self, "show_basic_language_switching", icon=_section_icon(self.show_basic_language_switching), icon_only=True, emboss=False)
row.label(text="Basic Language Switching", icon='PREFERENCES')
```

- [ ] **Step 2: Gate content by section state**

Render Basic details only when `self.show_basic_language_switching` is true. When false, show:

```python
box.label(text=f"Favorites: {len(self.favorites)} | Save after switch: {'On' if self.save_after_switch else 'Off'}", icon='INFO')
```

Render Advanced details only when `self.show_advanced_bilingual` is true. When false, keep `_manifest_summary(...)` visible.

Render Experimental details only when `self.show_experimental_scope` is true. When false, keep `_scope_summary(self)` visible.

- [ ] **Step 3: Compile UI module**

Run: `python -m py_compile ui/preferences.py`

Expected: exit code 0.

---

### Task 3: Runtime Verification

**Files:**
- Modify only if verification reveals issues.

- [ ] **Step 1: Run full tests**

Run: `pytest -q`

Expected: all tests pass.

- [ ] **Step 2: Run Blender registration smoke test**

Run Blender `--factory-startup --background` registration smoke test.

Expected: `ADDON_REGISTER_OK`.

- [ ] **Step 3: Run Blender install smoke test**

Run existing bilingual install smoke test.

Expected: install succeeds and language codes are `zh_en,en_zh`.
