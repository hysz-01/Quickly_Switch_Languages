---
feature: release-readiness
status: delivered
specs: []
plans:
  - docs/compose/plans/2026-07-14-quick-language-switcher-release-readiness.md
branch: master
commits: 1ff9cc3a8693693dc54c47b293569e04976d5df0..working-tree
---

# Quick Language Switcher Release Readiness — Final Report

## What Was Built

The Blender 5.1.2 copy of `Quickly_switch_languages` was brought through a minimal release-readiness pass. The known release blocker for multiple bilingual language packs was verified fixed: sequential installs preserve both generated locale entries in Blender's `languages` file and keep both installed files in `bilingual_manifest.json`.

The publish-facing README was rewritten to match the current add-on behavior. It now documents the top-bar `Switch Language` menu, `Shift+Ctrl+L` popup shortcut, user-config favorite storage, bilingual pack risks, multi-pack coexistence, no automatic language switching during install, emergency cleanup boundaries, developer checks, and GPL-3.0-or-later licensing.

The verified 5.1.2 add-on copy was then synchronized into the Blender 5.0 and 4.5 add-on directories. The previous 4.5 double-nested `Quickly_switch_languages\Quickly_switch_languages` directory was removed so Blender can load the package from the normal add-on root.

## Architecture

The add-on keeps its current package structure: `ui/` owns Blender operators and preferences UI, `core/` owns language persistence and localization helpers, and `bilingual/` owns `.mo` baking plus install/uninstall behavior. Runtime user files are routed through `core.paths.user_data_path()` so favorites and bilingual manifest state live under Blender user config instead of the add-on package data directory.

The bilingual installer writes generated `.mo` files under separate locale directories such as `en_ja/LC_MESSAGES/blender.mo` and patches Blender's `datafiles/locale/languages` inside a Quick Language Switcher marker block. Existing marker-block entries are merged with new entries so installing a later bilingual pair does not remove earlier generated locales.

### Design Decisions

We treat locale installation as a high-risk advanced feature because it modifies Blender installation resources. The README now explicitly documents that risk and tells users that install only creates resources; the user must restart Blender and manually select the generated locale.

We keep release readiness scoped to Blender 5.1.2 first because that is the currently tested target. 5.0 and 4.5 synchronization remain separate follow-up work, not part of this pass.

## Usage

Users enable the add-on in Blender preferences and use the top-bar `Switch Language` menu or `Shift+Ctrl+L` popup to switch among favorites. Advanced users can install bilingual language packs from the add-on preferences, restart Blender, and then select the generated locale in `Preferences > Interface > Language`.

For release verification, run:

```powershell
pytest -q
python -m py_compile "__init__.py" "core\language_manager.py" "core\paths.py" "core\localization.py" "core\keymap.py" "ui\menu.py" "ui\preferences.py" "bilingual\installer.py" "bilingual\baker.py" "bilingual\mo.py" "bilingual\scope.py"
```

Use Blender with `--factory-startup --background` for add-on registration smoke tests.

## Verification

- `pytest tests/test_bilingual_installer.py -q` produced `20 passed in 0.54s`.
- `pytest -q` produced `84 passed, 2 skipped`.
- `python -m py_compile ...` completed with no output.
- Blender 5.1.2 registration smoke printed `ADDON_ENABLED True`, `HAS_MENU True`, and `HAS_INSTALL_OP True`.
- Blender 5.1.2 bilingual multi-pack smoke installed `en_ja` and `zh_en` sequentially, printed `LANGUAGE_STATES zh_HANS zh_HANS zh_HANS`, confirmed both `LANGUAGES_HAS_EN_JA True` and `LANGUAGES_HAS_ZH_EN True`, and confirmed manifest codes/files contain both generated locales.
- 5.1.2 release hygiene check added `.gitignore` and cleaned `__pycache__/`, `.pytest_cache/`, `user_data/`, and `generated/` runtime artifacts from the publishable tree.
- Blender 5.0 synced copy: `pytest -q` produced `84 passed, 2 skipped`; `py_compile` completed with no output; registration smoke printed `ADDON_ENABLED True`, `HAS_MENU True`, and `HAS_INSTALL_OP True`; `en_US + ja_JP -> en_ja` install/uninstall smoke completed and preserved UI language as `en_US`.
- Blender 4.5 synced copy: `pytest -q` produced `84 passed, 2 skipped`; `py_compile` completed with no output; registration smoke printed `ADDON_ENABLED True`, `HAS_MENU True`, and `HAS_INSTALL_OP True`; `zh_HANS + en_US -> zh_en` install/uninstall smoke completed and preserved UI language as `zh_HANS`. Blender 4.5 still prints Blender's compatibility warning because the add-on declares Blender 5.0.0 minimum.
- Blender 5.0 environment note: the current local Blender 5.0.1 install has no `zh_HANS/LC_MESSAGES/blender.mo`; attempting `zh_HANS + en_US` correctly reports a recoverable source `.mo` missing error. Japanese-source bilingual install was used for the positive 5.0 smoke test.

## Journey Log

> Brief notes on what informed the final design. Not required reading.

- [lesson] The release README must be checked against code and smoke evidence, not only intended design, because locale install behavior has changed repeatedly.
- [lesson] Multiple bilingual pack coexistence needs both unit coverage and a real Blender smoke test because the user-facing failure appears after Blender reloads its language list.
- [pivot] Scope stayed on Blender 5.1.2 first after user confirmation; older Blender copies are not considered release-ready by this report.

## Source Materials

| File | Role | Notes |
|------|------|-------|
| `docs/compose/plans/2026-07-14-quick-language-switcher-release-readiness.md` | Implementation plan | Complete for 5.1.2 release-readiness pass |
