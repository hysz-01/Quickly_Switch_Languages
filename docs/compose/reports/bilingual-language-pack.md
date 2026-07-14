---
feature: bilingual-language-pack
status: delivered
specs:
  - docs/compose/specs/2026-07-14-bilingual-language-pack-design.md
plans:
  - docs/compose/plans/2026-07-14-bilingual-language-pack.md
  - docs/compose/plans/2026-07-14-custom-english-bilingual-pack.md
branch: master
commits: 1ff9cc3..working-tree
---

# Bilingual Language Pack — Final Report

## What Was Built

Quick Language Switcher now includes the foundation for safely baking and installing Blender bilingual language packs. The compatibility path still supports Blender 5.x Simplified Chinese source translations (`zh_HANS`) baked into `zh_en` and `en_zh` catalogs.

The preferences UI now also supports a custom English-pair path: choose Language 1 and Language 2 from Blender's available language picker, where exactly one side must be English, then install one generated bilingual language in the selected order. For example, `en_US` + `ja_JP` generates `en_ja` with English-first labels, while `zh_HANS` + `en_US` generates `zh_en` with Chinese-first labels.

The feature intentionally treats bilingual packs as installed Blender language resources, not as dynamic translation injection. It generates `.mo` files inside the add-on cache first, then installs them into Blender's `datafiles/locale` tree and patches the `languages` resource file with a marked block. Users are warned in the add-on preferences that this modifies Blender text resource files and requires restarting Blender.

## Architecture

`mo_utils.py` provides a pure Python GNU gettext `.mo` reader/writer through `MoCatalog`, `read_mo()`, and `write_mo()`. This avoids depending on external gettext tools such as `msgfmt` on Windows.

`bilingual_baker.py` owns bilingual catalog generation. It reads source `.mo` entries where the msgid is the English source string and msgstr is the selected non-English translation, then generates either the compatibility `zh_en`/`en_zh` catalogs or a single custom pair catalog through `bake_bilingual_pair_file()`.

`bilingual_installer.py` owns Blender resource modification. It patches `datafiles/locale/languages` using a `BEGIN/END Quick Language Switcher` block, copies generated `.mo` files into the selected output language folder, writes `bilingual_manifest.json`, and uninstalls only files listed in that manifest.

`preferences.py` exposes two add-on preference operators: `language_switcher.install_bilingual_pack` and `language_switcher.uninstall_bilingual_pack`. The UI warns users that installation modifies Blender language resources and requires restarting Blender.

`LANGUAGE_SWITCHER_OT_open_bilingual_language_menu` and `LANGUAGE_SWITCHER_OT_set_bilingual_language` provide the Language 1 / Language 2 picker. The opener only displays the popup, while the setter only writes the selected language, avoiding Blender operator property reuse between the two selectors. The picker reuses the same available-language source as the top-bar favorites add-language popup and filters out add-on-generated bilingual languages from `bilingual_manifest.json` plus the legacy `zh_en`/`en_zh` codes.

### Design Decisions

We chose installed locale resources because Blender 5.0 runtime probes showed `bpy.app.translations.register()` can translate add-on-owned strings but cannot override existing Blender core translations.

We chose new language codes (`zh_en`, `en_zh`) instead of replacing `zh_HANS` because this keeps Blender's original Simplified Chinese resources intact and makes uninstall precise.

We chose a pure Python `.mo` writer because Blender's bundled `_bl_i18n_utils` path depends on external `msgfmt`, and its commented internal `.mo` generator is marked as broken.

We chose manifest-driven uninstall because the Blender `languages` file may be edited by users or other tools after installation; uninstall should delete only add-on-owned resources.

We limited the first custom-pair version to one English side because Blender `.mo` catalogs already use English msgids as the stable join key. Arbitrary non-English + non-English pairs need additional translation alignment and fallback rules.

## Usage

Open Blender, enable Quick Language Switcher, then open the add-on preferences through `Manage Languages...`.

In `Bilingual Language Packs`, click the `Language 1` and `Language 2` buttons and select languages from the popup. Exactly one side must be `en_US`; the other side must have an installed Blender `.mo` file such as `zh_HANS` or `ja_JP`. Click `Install / Update Bilingual Packs`. The add-on bakes one bilingual `.mo` file in the selected order, patches Blender's `datafiles/locale/languages`, and reports that Blender must be restarted.

After restarting Blender, select the generated language code from Blender's language preferences or add that code to Quick Language Switcher's favorites.

To remove the installed language packs, click `Uninstall Bilingual Language Pack`, then restart Blender. Uninstall removes the marked language block and manifest-listed `.mo` files only.

## Verification

Automated verification completed:

- `pytest -q` -> `56 passed, 2 skipped`
- `python -m py_compile bilingual/baker.py bilingual/installer.py ui/preferences.py core/localization.py tests/test_localization.py tests/test_preferences_helpers.py` -> no output
- Blender 5.0.1 background register cycle -> `registered quick language switcher` and `unregistered quick language switcher`

The actual install button was not executed during automated verification because it intentionally modifies Blender's installed language resource files. Manual verification steps are documented in `docs/compose/reports/bilingual-manual-test-checklist.md`.

## Journey Log

- [lesson] Runtime probes showed dynamic add-on translation registration does not override existing Blender core translations, so complete bilingual UI requires installed locale resources.
- [pivot] The implementation avoids replacing `zh_HANS` and instead installs `zh_en`/`en_zh`, making rollback safer.
- [lesson] Real Blender package import caught relative import issues that ordinary pytest missed; Blender background registration is now part of verification.

## Source Materials

| File | Role | Notes |
|------|------|-------|
| `docs/compose/specs/2026-07-14-bilingual-language-pack-design.md` | Design spec | Defines safety boundaries, file layout, install/uninstall behavior |
| `docs/compose/plans/2026-07-14-bilingual-language-pack.md` | Implementation plan | Task-by-task TDD execution plan |
| `docs/compose/plans/2026-07-14-custom-english-bilingual-pack.md` | Follow-up implementation plan | Adds one custom English + non-English bilingual pack in selected order |
| `docs/compose/reports/bilingual-manual-test-checklist.md` | Manual verification | Restart-required Blender install/uninstall checklist |
