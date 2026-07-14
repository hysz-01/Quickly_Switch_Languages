---
feature: plugin-file-structure
status: delivered
specs: []
plans:
  - docs/compose/plans/2026-07-14-plugin-file-structure.md
branch: master
commits: uncommitted-working-tree
---

# Plugin File Structure — Final Report

## What Was Built

The add-on is now organized by responsibility instead of keeping source, tests, JSON data, and bilingual utilities in the root directory. Blender still loads the add-on through root `__init__.py`, but internal modules now live under `ui/`, `core/`, and `bilingual/`.

Runtime JSON files now live under `data/`, and tests live under `tests/`. Generated `.mo` files remain under `generated/<version>/...` so existing bake output and installer behavior stay recognizable.

## Architecture

The root `__init__.py` remains Blender's external add-on entrypoint. It imports and registers `ui.preferences` and `ui.menu`.

`ui/` contains Blender UI code: menu operators, preference classes, bilingual install/uninstall UI, and registration functions. Because these files now run under `Quickly_switch_languages.ui`, they compute `ADDON_PACKAGE = __package__.split(".", 1)[0]` so `AddonPreferences.bl_idname`, `context.preferences.addons[...]`, and `bpy.ops.preferences.addon_show(module=...)` still target `Quickly_switch_languages`.

`core/` contains non-UI support code. `core/language_manager.py` owns favorites JSON behavior, and `core/paths.py` owns add-on root and data-file path resolution.

`bilingual/` contains all bilingual language-pack logic: `.mo` read/write in `mo.py`, bake rules in `baker.py`, install/uninstall in `installer.py`, and region scope presets in `scope.py`.

`data/` contains `languages.json` and `bilingual_manifest.json`. `tests/` contains all pytest files, updated to import the package layout instead of old root-level modules.

### Design Decisions

We kept root `__init__.py` because Blender expects a stable add-on entrypoint at the package root.

We did not move `generated/` because generated output is versioned and already separated from source code.

We removed stale direct-import fallbacks from bilingual submodules because the package layout now expects package-relative imports.

## Usage

For development, run tests from the add-on root:

```text
pytest -q
```

Compile the package modules with:

```text
python -m py_compile __init__.py ui/menu.py ui/preferences.py core/language_manager.py core/paths.py bilingual/mo.py bilingual/baker.py bilingual/installer.py bilingual/scope.py
```

Runtime data paths are resolved through:

```python
from Quickly_switch_languages.core.paths import addon_root, data_path
```

## Verification

Automated verification:

```text
pytest -q
32 passed, 2 skipped in 0.35s
```

Compile verification:

```text
python -m py_compile __init__.py ui/menu.py ui/preferences.py core/language_manager.py core/paths.py bilingual/mo.py bilingual/baker.py bilingual/installer.py bilingual/scope.py tests/test_integration.py
```

Blender runtime verification used `--factory-startup` to avoid double-registering the already-enabled add-on from user preferences:

```text
ADDON_REGISTER_OK
BILINGUAL_VERSION 5.0.1
BILINGUAL_LANGUAGES zh_en,en_zh
```

The bilingual install verification confirmed the manifest path is now `data/bilingual_manifest.json` and generated `.mo` output remains under `generated/5.0.1/...`.

## Journey Log

> Brief notes on what informed the final design. Not required reading.

- [lesson] Moving Blender UI modules into a subpackage changes `__package__`, so add-on IDs must derive the root package explicitly.
- [dead end] A normal Blender background registration test double-registered classes because the user environment already enabled the add-on; `--factory-startup` is the correct isolated registration check.
- [lesson] Tests that are skipped outside Blender can preserve stale import assumptions, so integration tests were updated even though regular pytest skips them.

## Source Materials

| File | Role | Notes |
|------|------|-------|
| `docs/compose/plans/2026-07-14-plugin-file-structure.md` | Implementation plan | Defines the target `ui/core/bilingual/data/tests` layout |
