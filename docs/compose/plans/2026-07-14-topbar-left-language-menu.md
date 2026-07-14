# Topbar Left Language Menu Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use compose:subagent (recommended) or compose:execute to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the `Switch Languages to` topbar menu from Blender's right-aligned header area to the left-aligned topbar area near menus/workspaces.

**Architecture:** Keep the existing menu class and operator behavior unchanged. Change only the topbar draw callback so it draws for `context.region.alignment == 'LEFT'` instead of `RIGHT`, using Blender's public `TOPBAR_HT_upper_bar.append()` API.

**Tech Stack:** Python 3, Blender Python API, pytest.

## Global Constraints

- Do not monkeypatch Blender's built-in topbar drawing code.
- Do not change language switching behavior or favorites loading.
- Keep existing menu label and contents unchanged.

---

### Task 1: Draw Language Menu on Left Topbar

**Covers:** User request: put the language menu between the left menu bar and workspace area as closely as Blender's public header API allows.

**Files:**
- Modify: `ui/menu.py`
- Modify: `tests/test_menu.py`

**Interfaces:**
- Consumes: `draw_menu(self, context)`.
- Produces: left-aligned topbar rendering by drawing only when `context.region.alignment == 'LEFT'`.

- [ ] **Step 1: Write failing tests**

Add tests to `tests/test_menu.py` using a fake layout and fake context:

```python
def test_draw_menu_renders_on_left_region():
    menu, _bpy = _load_menu_module()
    calls = []
    self = types.SimpleNamespace(layout=_FakeTopbarLayout(calls))
    context = types.SimpleNamespace(region=types.SimpleNamespace(alignment='LEFT'))

    menu.draw_menu(self, context)

    assert ('separator',) in calls
    assert ('menu', 'LANGUAGE_SWITCHER_MT_menu', {'icon': 'WORLD'}) in calls


def test_draw_menu_skips_right_region():
    menu, _bpy = _load_menu_module()
    calls = []
    self = types.SimpleNamespace(layout=_FakeTopbarLayout(calls))
    context = types.SimpleNamespace(region=types.SimpleNamespace(alignment='RIGHT'))

    menu.draw_menu(self, context)

    assert calls == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest -q tests/test_menu.py::test_draw_menu_renders_on_left_region tests/test_menu.py::test_draw_menu_skips_right_region`

Expected: FAIL because the current callback skips left and renders on right.

- [ ] **Step 3: Implement minimal behavior**

Change `ui/menu.py`:

```python
def draw_menu(self, context):
    """Draw function for top menu bar"""
    if context.region.alignment != 'LEFT':
        return

    layout = self.layout
    layout.separator()
    layout.menu(LANGUAGE_SWITCHER_MT_menu.bl_idname, icon='WORLD')
```

- [ ] **Step 4: Run targeted tests**

Run: `pytest -q tests/test_menu.py`

Expected: PASS.

- [ ] **Step 5: Run full verification**

Run:

```text
python -m py_compile ui/menu.py tests/test_menu.py
pytest -q
```

Expected: compile exits 0 and tests pass.
