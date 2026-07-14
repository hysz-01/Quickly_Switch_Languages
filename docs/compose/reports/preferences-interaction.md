---
feature: preferences-interaction
status: delivered
specs: []
plans:
  - docs/compose/plans/2026-07-14-preferences-interaction.md
branch: master
commits: uncommitted-working-tree
---

# Preferences Interaction — Final Report

## What Was Built

The add-on preferences panel now separates everyday language switching, advanced bilingual language-pack installation, and experimental region-scoped bilingual baking into distinct sections. This makes the UI communicate risk and scope before the user acts.

Basic language switching contains normal favorites management and save-after-switch behavior. Advanced bilingual language packs contains install/update and uninstall operations that modify Blender locale resources. Experimental region scope contains the region checkboxes and custom keywords that affect the next bilingual pack install.

Operation reports now use clearer action-oriented messages, including what happened and what the user should do next when a restart is required or an operation fails.

## Architecture

`ui/preferences.py` remains the single owner of the add-on preferences panel. It now includes small pure helpers for interaction summaries: `_custom_keyword_count()`, `_scope_summary()`, and `_manifest_summary()`.

The draw method renders three sections: `Basic Language Switching`, `Advanced: Bilingual Language Packs`, and `Experimental: Region Scope`. Advanced shows the current manifest summary from `data/bilingual_manifest.json`; Experimental shows selected region count and custom keyword count.

`ui/menu.py` keeps top-bar language switching behavior but uses clearer report text when switching languages or adding defaults.

### Design Decisions

We used convention-mode settings UI rather than visual novelty because this is a dense Blender preference screen where clarity, grouping, and predictable labels matter more than distinctive styling.

We kept region scope under Experimental because it affects the next bake/install operation and relies on exact-label matching; it is not an immediate language switch and can still include same-name labels from other UI contexts.

We did not add modal confirmation dialogs in this pass because the request focused on reminders and hierarchy, and blocking dialogs would make routine updates heavier.

## Usage

Open the add-on preferences. Use `Basic Language Switching` for normal top-bar language favorites and the save-after-switch option.

Use `Advanced: Bilingual Language Packs` to install/update or uninstall `zh_en` and `en_zh`. The section explains that Blender locale resources are modified, a backup is made, and Blender must be restarted.

Use `Experimental: Region Scope` before installing/updating bilingual packs. These choices affect the next install only; they do not change the current language immediately.

## Verification

Automated verification:

```text
pytest -q
34 passed, 2 skipped in 0.32s
```

Compile verification:

```text
python -m py_compile ui/preferences.py ui/menu.py tests/test_preferences_helpers.py
```

Blender runtime verification:

```text
ADDON_REGISTER_OK
BILINGUAL_KEYWORDS 538
BILINGUAL_LANGUAGES zh_en,en_zh
```

The install verification restored the all-region bilingual pack state after the smoke test.

## Journey Log

> Brief notes on what informed the final design. Not required reading.

- [lesson] Blender preference panels benefit more from conventional grouping than visual distinctiveness; the useful design move is hierarchy, not decoration.
- [lesson] Experimental region scope needs explicit “next install only” wording because users may otherwise expect immediate language switching.
- [lesson] Failure reports should name a next action, such as checking locale folder permissions or the manifest path.

## Source Materials

| File | Role | Notes |
|------|------|-------|
| `docs/compose/plans/2026-07-14-preferences-interaction.md` | Implementation plan | Defines Basic / Advanced / Experimental grouping and feedback copy |
