---
feature: bilingual-region-presets
status: delivered
specs: []
plans:
  - docs/compose/plans/2026-07-14-bilingual-region-presets.md
branch: master
commits: uncommitted-working-tree
---

# Bilingual Region Presets — Final Report

## What Was Built

The bilingual language pack workflow now supports common region-based scope presets instead of a single node-focused scope. Users can choose separate areas in the add-on preferences, then bake/install `zh_en` and `en_zh` packs using only the selected regions.

The available regions are `Node / Shader / Geometry Nodes`, `Material / Texture`, `Animation / Rigging`, `Viewport / Navigation`, `Modeling / Mesh`, `Sculpt / Paint`, `Compositor / VFX`, and `Render / Lighting`. The default remains node/shader/geometry focused; the added regions are opt-in from the preferences UI.

The install manifest now records the Blender version used for scope resolution, the selected preset IDs, and the resolved keyword count. This makes generated packs traceable across version differences such as Blender 3.6, 4.5, 5.0, and future 5.2 builds.

## Architecture

`bilingual_scope.py` owns the region preset catalog and runtime keyword expansion. Static presets provide curated exact-match English terms for common Blender areas, while `collect_blender_node_keywords()` reads current-version node RNA labels from `bpy.types` for `ShaderNode*`, `GeometryNode*`, `CompositorNode*`, and `FunctionNode*` classes.

`preferences.py` maps each checkbox to a preset ID through `_enabled_bilingual_presets()`. During install, the operator passes the selected preset IDs, current `bpy.app.version_string`, and current `bpy` module to `get_scope_keywords()`, then forwards the resolved keywords and preset list to `install_bilingual_pack()`.

`bilingual_installer.py` continues to generate and install separate `zh_en` and `en_zh` language packs without modifying `zh_HANS`. The manifest records `scope_keywords`, `scope_blender_version`, `scope_keyword_count`, and `scope_presets` when scope filtering is active.

### Design Decisions

We kept scope matching as exact case-insensitive equality because substring matching caused non-target UI text to be bilingualized by broad terms such as `Input`, `Output`, `Color`, and `View`.

We made runtime node expansion version-specific by collecting labels from the running Blender process and recording `scope_blender_version` in the manifest. This avoids pretending a keyword set collected from Blender 5.0 is authoritative for 3.6, 4.5, or 5.2.

We kept broad areas opt-in because regions like `Render / Lighting` and `Viewport / Navigation` contain short shared terms such as `Camera`, `Image`, and `View`; exact matching reduces false positives but cannot fully infer UI intent from a global `.mo` dictionary.

## Usage

Open Blender Preferences, find the `Bilingual Language Packs` section, and choose the desired bilingual scope checkboxes. The install button bakes the selected regions into `zh_en` and `en_zh`; Blender must be restarted before those language entries are available in the language selector.

The `Custom Keywords` field remains available for user-specific additions. Custom entries are comma-separated exact English msgids and are added to the selected preset keywords during bake.

The current Blender 5.0.1 verification install used all eight region presets and recorded:

```text
BILINGUAL_VERSION 5.0.1
BILINGUAL_KEYWORDS 538
BILINGUAL_PRESETS node_shader_geometry,material_texture,animation_rigging,viewport_navigation,modeling_mesh,sculpt_paint,compositor_vfx,render_lighting
BILINGUAL_LANGUAGES zh_en,en_zh
```

## Verification

Automated verification:

```text
pytest -q
32 passed, 2 skipped in 0.35s
```

Compile verification:

```text
python -m py_compile bilingual_baker.py bilingual_scope.py bilingual_installer.py preferences.py test_preferences.py
```

Blender runtime verification confirmed preference mapping and successful install under Blender 5.0.1. Generated `.mo` sampling showed selected region terms are bilingualized while known unsafe/non-target examples remain unchanged:

```text
Mix => 混合 (Mix)
Noise Texture => 噪波纹理 (Noise Texture)
Bevel => 倒角 (Bevel)
Brush => 笔刷 (Brush)
Color Balance => 色彩平衡 (Color Balance)
Light => 灯光 (Light)
Audio Mixing Buffer => 音频的混音缓冲区
WindowManager\x04Input => missing or unchanged
```

## Journey Log

- [lesson] The Blender `.mo` file is global, not separated by editor region, so region support must be implemented as explicit allowlists plus safety filters.
- [pivot] Runtime node collection via `Node.__subclasses__()` only exposed `NodeInternal` in Blender 5.0.1, so node labels are collected from `bpy.types` class prefixes instead.
- [lesson] Exact matching avoids sentence bleed, but short exact labels can still appear in several contexts; broad regions remain opt-in.

## Source Materials

| File | Role | Notes |
|------|------|-------|
| `docs/compose/plans/2026-07-14-bilingual-region-presets.md` | Implementation plan | Covers region presets, version metadata, UI mapping, verification |
