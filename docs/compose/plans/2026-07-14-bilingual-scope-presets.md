# Bilingual Scope Presets Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use compose:subagent (recommended) or compose:execute to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let users choose which Blender UI vocabulary areas receive bilingual bake, defaulting to Node / Shader / Geometry Nodes instead of full-interface bilingual text.

**Architecture:** Add a focused scope preset module that maps preset IDs to keyword lists. Extend `bilingual_baker.py` to accept `scope_keywords` and only bilingualize matching msgids after the existing safety filters pass. Add Blender preferences controls for the default node scope and a custom keyword string.

**Tech Stack:** Python standard library, pytest, Blender Python API.

## Global Constraints

- Default scope is `node_shader_geometry`.
- Non-matching msgids keep the original Chinese translation.
- Existing safety filters remain mandatory: skip gettext context `\x04`, printf `%` placeholders, fmt `{}` fields, and over-width combined strings.
- Do not reintroduce full-interface bilingual bake as the default.
- The first UI version may use Boolean preset toggles and a comma-separated custom keyword string.

---

### Task 1: Scope Presets And Baker Filtering

**Files:**
- Create: `bilingual_scope.py`
- Modify: `bilingual_baker.py`
- Modify: `test_bilingual_baker.py`

**Interfaces:**
- Produces: `DEFAULT_SCOPE_PRESET = "node_shader_geometry"`
- Produces: `SCOPE_PRESETS: dict[str, dict]`
- Produces: `get_scope_keywords(enabled_presets: list[str] | None = None, custom_keywords: str = "") -> set[str]`
- Modifies: `bake_bilingual_catalogs(source: MoCatalog, scope_keywords: set[str] | None = None) -> dict[str, MoCatalog]`
- Modifies: `bake_bilingual_files(source_mo: Path, output_root: Path, scope_keywords: set[str] | None = None) -> dict[str, Path]`

- [ ] Write failing tests for keyword filtering:

```python
def test_bake_only_combines_matching_scope_keywords():
    source = MoCatalog({
        "Node": "节点",
        "Save": "保存",
    })

    result = bake_bilingual_catalogs(source, scope_keywords={"Node"})

    assert result["zh_en"].entries["Node"] == "节点 (Node)"
    assert result["zh_en"].entries["Save"] == "保存"
```

- [ ] Write failing tests for preset keyword collection:

```python
def test_get_scope_keywords_combines_presets_and_custom_keywords():
    from bilingual_scope import get_scope_keywords

    keywords = get_scope_keywords(["node_shader_geometry"], "Bake, Custom Term")

    assert "Node" in keywords
    assert "Shader" in keywords
    assert "Bake" in keywords
    assert "Custom Term" in keywords
```

- [ ] Implement `bilingual_scope.py`:

```python
DEFAULT_SCOPE_PRESET = "node_shader_geometry"

SCOPE_PRESETS = {
    "node_shader_geometry": {
        "label": "Node / Shader / Geometry Nodes",
        "keywords": [
            "Node", "Nodes", "Shader", "Socket", "Input", "Output",
            "Geometry", "Geometry Nodes", "Group", "Attribute", "Field",
            "Vector", "Color", "Value", "Normal", "UV", "Image",
            "Material", "Texture", "Principled", "BSDF",
        ],
    },
    "material_texture": {
        "label": "Material / Texture",
        "keywords": ["Material", "Texture", "Image", "Color", "Alpha", "Normal", "Roughness", "Metallic"],
    },
    "animation_rigging": {
        "label": "Animation / Rigging",
        "keywords": ["Animation", "Action", "Keyframe", "Rig", "Bone", "Armature", "Pose", "Constraint"],
    },
    "viewport_navigation": {
        "label": "Viewport / Navigation",
        "keywords": ["Viewport", "View", "Navigation", "Camera", "Orbit", "Pan", "Zoom", "Gizmo"],
    },
}


def get_scope_keywords(enabled_presets=None, custom_keywords=""):
    presets = enabled_presets or [DEFAULT_SCOPE_PRESET]
    keywords = set()
    for preset in presets:
        keywords.update(SCOPE_PRESETS.get(preset, {}).get("keywords", []))
    for item in custom_keywords.split(","):
        keyword = item.strip()
        if keyword:
            keywords.add(keyword)
    return keywords
```

- [ ] Update `bilingual_baker.py` to skip non-matching msgids before `_can_combine()`:

```python
def _matches_scope(msgid: str, scope_keywords: set[str] | None) -> bool:
    if scope_keywords is None:
        return True
    return any(keyword.casefold() in msgid.casefold() for keyword in scope_keywords)
```

- [ ] Run: `pytest -q test_bilingual_baker.py`

Expected: PASS.

---

### Task 2: Installer Passes Scope Keywords

**Files:**
- Modify: `bilingual_installer.py`
- Modify: `test_bilingual_installer.py`

**Interfaces:**
- Modifies: `install_bilingual_pack(locale_root: Path, blender_version: str, addon_root: Path, scope_keywords: set[str] | None = None) -> dict`

- [ ] Add a test that install passes scope filtering by inspecting generated output for an included and excluded term.
- [ ] Update `install_bilingual_pack()` to pass `scope_keywords` into `bake_bilingual_files()`.
- [ ] Store sorted `scope_keywords` in manifest as `scope_keywords` when provided.
- [ ] Run: `pytest -q test_bilingual_installer.py test_bilingual_baker.py`

Expected: PASS.

---

### Task 3: Preferences UI Scope Controls

**Files:**
- Modify: `preferences.py`

**Interfaces:**
- Consumes: `get_scope_keywords()` from `bilingual_scope.py`
- Adds Boolean preferences:
  - `bilingual_scope_node_shader_geometry`
  - `bilingual_scope_material_texture`
  - `bilingual_scope_animation_rigging`
  - `bilingual_scope_viewport_navigation`
- Adds String preference: `bilingual_custom_keywords`

- [ ] Add imports:

```python
from .bilingual_scope import get_scope_keywords
```

- [ ] Add Boolean/String properties to `QuickLanguageSwitcherPreferences`.
- [ ] Update install operator to build enabled preset list and pass `scope_keywords`.
- [ ] Add UI controls under `Bilingual Language Packs`.
- [ ] Run: `python -m py_compile preferences.py bilingual_scope.py bilingual_baker.py bilingual_installer.py`.
- [ ] Run: `pytest -q`.

Expected: all tests pass.

---

### Task 4: Re-bake And Install Default Scoped Pack

**Files:**
- No source changes expected.

- [ ] Run install through Blender background using default preferences-equivalent scope keywords from `node_shader_geometry`.
- [ ] Verify a fresh Blender process sees `zh_en` and `en_zh`.
- [ ] Verify generated `zh_en` changed entries are far fewer than full bake and include node/shader terms.
- [ ] Report that Blender must be restarted for UI validation.

---

## Self-Review

- No placeholders remain.
- The scope module is independent and testable.
- Existing safety filters remain in `bilingual_baker.py`.
- UI state maps to install behavior through `get_scope_keywords()`.
