---
feature: collapsible-preference-sections
status: delivered
specs: []
plans:
  - docs/compose/plans/2026-07-14-collapsible-preference-sections.md
branch: master
commits: uncommitted-working-tree
---

# Collapsible Preference Sections — Final Report

## What Was Built

The add-on preferences panel now supports collapsible sections for `Basic Language Switching`, `Advanced: Bilingual Language Packs`, and `Experimental: Region Scope`. This keeps the panel compact when opened while preserving quick status visibility.

Basic opens by default because it contains everyday controls. Advanced and Experimental are collapsed by default because they are less frequently used and have more complex/risk-sensitive settings.

## Architecture

`ui/preferences.py` now defines three UI-state properties on `QuickLanguageSwitcherPreferences`: `show_basic_language_switching`, `show_advanced_bilingual`, and `show_experimental_scope`.

Each section header uses a small disclosure triangle through `_section_icon()`, returning `TRIA_DOWN` when open and `TRIA_RIGHT` when closed. Collapsed sections still render status summaries: Basic shows favorites/save state, Advanced shows manifest status, and Experimental shows selected region/custom keyword counts.

`_manifest_summary()` now safely handles unreadable or broken manifest JSON so the preferences panel can still render even if `data/bilingual_manifest.json` is damaged.

### Design Decisions

We defaulted Basic open and Advanced/Experimental closed because this matches task frequency and risk: daily language switching should be immediately available, while bilingual install and experimental scope options should not dominate the first view.

We kept the clickable target to the Blender-native triangle property rather than making the whole label row interactive because Blender label rows are not naturally toggle controls.

## Usage

Open the add-on preferences. Use the triangle beside each section title to expand or collapse that section.

Collapsed summaries remain visible:

```text
Favorites: N | Save after switch: On/Off
Installed manifest: Blender 5.0.1, 538 keywords
Selected regions: N | Custom keywords: N
```

## Verification

Automated verification:

```text
pytest -q
36 passed, 2 skipped in 0.36s
```

Compile verification:

```text
python -m py_compile ui/preferences.py tests/test_preferences_helpers.py
```

Blender runtime verification:

```text
ADDON_REGISTER_OK
BILINGUAL_KEYWORDS 538
BILINGUAL_LANGUAGES zh_en,en_zh
```

## Journey Log

> Brief notes on what informed the final design. Not required reading.

- [lesson] Collapsed sections that read external state need defensive summary helpers; otherwise broken manifest files can break the entire preferences panel.
- [lesson] Settings UIs should preserve status visibility even when details are collapsed.

## Source Materials

| File | Role | Notes |
|------|------|-------|
| `docs/compose/plans/2026-07-14-collapsible-preference-sections.md` | Implementation plan | Defines default open states, section summaries, and runtime verification |
