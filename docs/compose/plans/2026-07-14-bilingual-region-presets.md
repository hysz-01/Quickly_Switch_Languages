# Bilingual Region Presets Implementation Plan

> [!NOTE]
> This document may not reflect the current implementation.
> See the final report for up-to-date state:
> [Final Report](../reports/bilingual-region-presets.md)

> **For agentic workers:** REQUIRED SUB-SKILL: Use compose:subagent (recommended) or compose:execute to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add common region-based bilingual scope presets with explicit Blender-version-aware runtime expansion.

**Architecture:** Keep bake filtering strict and exact-match based. Expand `bilingual_scope.py` with curated static presets for common Blender areas, and only add Blender runtime-derived names for the current running `bpy.app.version_string`. Preferences map directly to preset IDs, and install manifest records the Blender version and selected preset IDs alongside resolved keywords.

**Tech Stack:** Python 3, Blender Python API, gettext `.mo` files, pytest.

## Global Constraints

- Do not reintroduce substring matching for scope filtering.
- Do not overwrite Blender source `zh_HANS`; continue installing only `zh_en` and `en_zh`.
- Dynamic node names are version-specific and must be collected from the current running Blender version only.
- Record selected preset IDs, resolved keyword count, and Blender version in the install manifest.
- Preserve existing placeholder/context safety filters in `bilingual_baker.py`.

---

### Task 1: Region Preset Catalog

**Covers:** region preset catalog, version-aware runtime source

**Files:**
- Modify: `bilingual_scope.py`
- Test: `test_bilingual_baker.py`

**Interfaces:**
- Consumes: existing `SCOPE_PRESETS`, `get_scope_keywords(enabled_presets=None, custom_keywords="", bpy_module=None)`
- Produces: expanded `SCOPE_PRESETS` with preset IDs `node_shader_geometry`, `material_texture`, `animation_rigging`, `viewport_navigation`, `modeling_mesh`, `sculpt_paint`, `compositor_vfx`, `render_lighting`
- Produces: `get_scope_keywords(..., blender_version: str | None = None) -> set[str]`

- [ ] **Step 1: Write failing preset tests**

Add tests to `test_bilingual_baker.py`:

```python
def test_common_region_presets_include_expected_terms():
    presets = bilingual_scope.SCOPE_PRESETS

    assert "modeling_mesh" in presets
    assert "Sculpt / Paint" == presets["sculpt_paint"]["label"]
    assert "Bevel" in presets["modeling_mesh"]["keywords"]
    assert "Brush" in presets["sculpt_paint"]["keywords"]
    assert "Color Balance" in presets["compositor_vfx"]["keywords"]
    assert "Cycles" in presets["render_lighting"]["keywords"]


def test_get_scope_keywords_combines_multiple_common_regions():
    keywords = bilingual_scope.get_scope_keywords(["modeling_mesh", "render_lighting"])

    assert "Bevel" in keywords
    assert "Extrude" in keywords
    assert "Render" in keywords
    assert "Light" in keywords
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest -q test_bilingual_baker.py::test_common_region_presets_include_expected_terms test_bilingual_baker.py::test_get_scope_keywords_combines_multiple_common_regions`

Expected: FAIL because new preset IDs do not exist.

- [ ] **Step 3: Implement expanded static presets**

Modify `bilingual_scope.py` by adding these curated exact-match terms:

```python
"modeling_mesh": {
    "label": "Modeling / Mesh",
    "keywords": [
        "Mesh", "Vertex", "Vertices", "Edge", "Edges", "Face", "Faces",
        "Normal", "Normals", "Extrude", "Inset", "Bevel", "Loop Cut",
        "Subdivide", "Merge", "Separate", "Dissolve", "Knife", "Fill",
        "Triangulate", "Smooth", "Shade Smooth", "Edit Mode", "Object Mode",
    ],
},
"sculpt_paint": {
    "label": "Sculpt / Paint",
    "keywords": [
        "Sculpt", "Brush", "Stroke", "Radius", "Strength", "Smooth",
        "Mask", "Paint", "Texture Paint", "Vertex Paint", "Weight Paint",
        "Clone", "Smear", "Draw", "Inflate", "Grab", "Crease",
    ],
},
"compositor_vfx": {
    "label": "Compositor / VFX",
    "keywords": [
        "Compositor", "Composite", "Viewer", "Render Layers", "Image",
        "Alpha Over", "Color Balance", "Color Correction", "Hue/Saturation",
        "Glare", "Blur", "Defocus", "Mask", "Keying", "Cryptomatte",
    ],
},
"render_lighting": {
    "label": "Render / Lighting",
    "keywords": [
        "Render", "Rendering", "Light", "Lighting", "World", "Camera",
        "Cycles", "Eevee", "Sample", "Samples", "Shadow", "Ambient Occlusion",
        "Raytracing", "Denoise", "Exposure", "Color Management",
    ],
},
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest -q test_bilingual_baker.py::test_common_region_presets_include_expected_terms test_bilingual_baker.py::test_get_scope_keywords_combines_multiple_common_regions`

Expected: PASS.

---

### Task 2: Version-Aware Runtime Keywords and Manifest Metadata

**Covers:** version-specific behavior, manifest traceability

**Files:**
- Modify: `bilingual_scope.py`
- Modify: `bilingual_installer.py`
- Modify: `preferences.py`
- Test: `test_bilingual_baker.py`
- Test: `test_bilingual_installer.py`

**Interfaces:**
- Consumes: `get_scope_keywords(enabled_presets, custom_keywords, bpy_module, blender_version)`
- Produces: manifest fields `scope_presets`, `scope_keyword_count`, `scope_blender_version`

- [ ] **Step 1: Write failing version metadata tests**

Add tests:

```python
def test_get_scope_keywords_accepts_version_for_runtime_collection():
    class FakeRna:
        def __init__(self, name):
            self.name = name

    class FakeTypes:
        ShaderNodeMix = type("ShaderNodeMix", (), {"bl_rna": FakeRna("Mix")})

        @classmethod
        def __dir__(cls):
            return ["ShaderNodeMix"]

    class FakeBpy:
        types = FakeTypes

    keywords = bilingual_scope.get_scope_keywords(["node_shader_geometry"], bpy_module=FakeBpy, blender_version="5.0.1")

    assert "Mix" in keywords
```

Add to `test_bilingual_installer.py`:

```python
def test_install_bilingual_pack_records_scope_metadata(tmp_path):
    locale_root = _make_locale_root(tmp_path)
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest -q test_bilingual_baker.py::test_get_scope_keywords_accepts_version_for_runtime_collection test_bilingual_installer.py::test_install_bilingual_pack_records_scope_metadata`

Expected: FAIL because `blender_version` and `scope_presets` parameters are not wired through.

- [ ] **Step 3: Implement metadata plumbing**

Modify signatures:

```python
def get_scope_keywords(enabled_presets=None, custom_keywords="", bpy_module=None, blender_version=None):
```

The `blender_version` parameter is recorded by callers and reserved for version-specific branching; runtime keyword collection still reads from the provided `bpy_module` for the current Blender process.

Modify `install_bilingual_pack` signature:

```python
def install_bilingual_pack(locale_root: Path, blender_version: str, addon_root: Path, scope_keywords: set[str] | None = None, scope_presets: list[str] | None = None) -> dict:
```

Add manifest fields when scope is provided:

```python
manifest["scope_blender_version"] = blender_version
manifest["scope_keyword_count"] = len(scope_keywords)
if scope_presets is not None:
    manifest["scope_presets"] = list(scope_presets)
```

Modify `preferences.py` install call:

```python
scope_keywords = get_scope_keywords(
    enabled_presets,
    prefs.bilingual_custom_keywords,
    bpy_module=bpy,
    blender_version=bpy.app.version_string,
)
install_bilingual_pack(
    locale_root,
    bpy.app.version_string,
    addon_root,
    scope_keywords=scope_keywords,
    scope_presets=enabled_presets,
)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest -q test_bilingual_baker.py::test_get_scope_keywords_accepts_version_for_runtime_collection test_bilingual_installer.py::test_install_bilingual_pack_records_scope_metadata`

Expected: PASS.

---

### Task 3: Preferences UI for Common Regions

**Covers:** user-selectable region switching

**Files:**
- Modify: `preferences.py`
- Test: `test_bilingual_baker.py`

**Interfaces:**
- Consumes: `SCOPE_PRESETS` IDs and labels
- Produces: Boolean preferences for `modeling_mesh`, `sculpt_paint`, `compositor_vfx`, `render_lighting`

- [ ] **Step 1: Write failing UI mapping test**

Add a pure helper in `preferences.py` during implementation:

```python
def _enabled_bilingual_presets(prefs):
    ...
```

Add test:

```python
def test_enabled_bilingual_presets_includes_new_regions():
    class Prefs:
        bilingual_scope_node_shader_geometry = True
        bilingual_scope_material_texture = False
        bilingual_scope_animation_rigging = False
        bilingual_scope_viewport_navigation = False
        bilingual_scope_modeling_mesh = True
        bilingual_scope_sculpt_paint = True
        bilingual_scope_compositor_vfx = False
        bilingual_scope_render_lighting = True

    from preferences import _enabled_bilingual_presets

    assert _enabled_bilingual_presets(Prefs()) == [
        "node_shader_geometry",
        "modeling_mesh",
        "sculpt_paint",
        "render_lighting",
    ]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest -q test_preferences.py::test_enabled_bilingual_presets_includes_new_regions`

Expected: FAIL because helper and properties do not exist.

- [ ] **Step 3: Implement helper and UI properties**

Add properties to `QuickLanguageSwitcherPreferences`:

```python
bilingual_scope_modeling_mesh: BoolProperty(name="Modeling / Mesh", description="Bilingualize common modeling and mesh terms", default=False)
bilingual_scope_sculpt_paint: BoolProperty(name="Sculpt / Paint", description="Bilingualize sculpting and painting terms", default=False)
bilingual_scope_compositor_vfx: BoolProperty(name="Compositor / VFX", description="Bilingualize compositor and VFX terms", default=False)
bilingual_scope_render_lighting: BoolProperty(name="Render / Lighting", description="Bilingualize render and lighting terms", default=False)
```

Add them to `_enabled_bilingual_presets()` and draw them in the same checkbox column.

- [ ] **Step 4: Run UI mapping test**

Run: `pytest -q test_preferences.py::test_enabled_bilingual_presets_includes_new_regions`

Expected: PASS or SKIPPED if Blender-only test module skips outside Blender. If skipped, validate via `python -m py_compile preferences.py`.

---

### Task 4: Verification and Reinstall

**Covers:** end-to-end bake/install behavior

**Files:**
- Modify generated install output under `generated/<version>/...`
- Modify Blender locale install target through existing installer

**Interfaces:**
- Consumes: completed Tasks 1-3
- Produces: installed `zh_en` and `en_zh` language packs for the current Blender version

- [ ] **Step 1: Run full tests**

Run: `pytest -q`

Expected: all non-Blender tests pass, Blender-only tests may skip.

- [ ] **Step 2: Compile changed modules**

Run: `python -m py_compile bilingual_baker.py bilingual_scope.py bilingual_installer.py preferences.py`

Expected: exit code 0, no output.

- [ ] **Step 3: Reinstall with Blender 5.0.1 background**

Run the existing Blender background install command using `get_scope_keywords(..., blender_version=bpy.app.version_string)` and `install_bilingual_pack(..., scope_presets=[...])`.

Expected output includes current version, keyword count, and language codes `zh_en,en_zh`.

- [ ] **Step 4: Sample generated `.mo` output**

Run a Python sample over `generated/5.0.1/zh_en/LC_MESSAGES/blender.mo` checking:

```text
Mix -> contains (Mix)
Bevel -> contains (Bevel) when Modeling / Mesh is selected
WindowManager\x04Input -> unchanged or missing
Audio Mixing Buffer -> unchanged
```

Expected: selected region terms are bilingualized, known non-region examples remain unchanged.
