---
feature: addon-localization
status: delivered
specs: []
plans:
  - docs/compose/plans/2026-07-14-addon-localization.md
  - docs/compose/plans/2026-07-14-experimental-scope-enable.md
branch: master
commits: uncommitted
---

# Add-on Localization — Final Report

## What Was Built

The add-on now has built-in translations for its own UI in English, Simplified Chinese, Traditional Chinese, and Japanese. The translated surface covers the add-on's menu text, preference panel section labels, action buttons, status summaries, and operator report messages while leaving Blender-owned language names, language codes, file paths, and bilingual pack identifiers such as `zh_en` and `en_zh` untouched.

Missing translations fall back to the original English source text, so untranslated or newly added strings remain safe to render. Chinese aliases are normalized so `zh_CN` maps to `zh_HANS` and `zh_TW` maps to `zh_HANT`.

The Experimental Region Scope controls now have a separate enable checkbox. When disabled, installing bilingual language packs uses the default full advanced behavior; when enabled, the selected region presets and custom keywords constrain the next bilingual pack install.

## Architecture

Localization is centralized in `core/localization.py`. That module defines `LANGUAGE_ALIASES`, a `TRANSLATIONS` dictionary, `normalize_language(language_code)`, `translate(text, language_code=None)`, and `tr(text)`. `translate()` is deterministic and testable outside Blender; `tr()` reads `bpy.context.preferences.view.language` when Blender is available and falls back to English if Blender context is unavailable.

`ui/menu.py` imports `tr()` and applies it only to runtime display text: menu operator labels supplied through `layout.operator(..., text=...)` and report messages. Operator and menu `bl_label` values remain static English because they are Blender registration metadata rather than reliable runtime UI text.

`ui/preferences.py` imports `tr()` for fixed add-on-owned UI strings. It localizes helper summaries (`_scope_summary()` and `_manifest_summary()`), runtime preference panel labels, compact icon-button tooltips, visible property names for add-on preferences, language-management reports, and bilingual-pack install/uninstall reports.

Experimental scope activation is isolated in `_install_scope_settings(prefs, bpy_module)`. That helper returns `(None, [])` when `enable_experimental_scope` is false, preserving the default full install path, and returns generated scope keywords plus enabled preset IDs when the checkbox is true. `LANGUAGE_SWITCHER_OT_install_bilingual_pack.execute()` consumes this helper before calling `install_bilingual_pack()`.

### Design Decisions

We chose a lightweight dictionary helper because the add-on only needs to translate its own compact UI surface and does not need `.po/.mo` compilation. This keeps packaging simple and makes tests independent of Blender's translation registry.

We kept dynamic/user-owned values unmodified because language names, language codes, file paths, manifest filenames, and bilingual pack identifiers must remain exact operational data. Translated templates use `.format()` placeholders so only the fixed sentence structure is localized.

We made Experimental Region Scope opt-in because region scoping narrows generated bilingual labels and should not silently affect the normal advanced install path. The collapsible section still controls visibility; the new checkbox controls behavior.

## Usage

Users do not need to configure anything in the add-on. The add-on UI follows Blender's current interface language when `tr()` can read it from preferences.

To use scoped bilingual packs, open Preferences, expand `Experimental: Region Scope`, enable `Enable Experimental Region Scope`, select regions or enter custom keywords, then run `Install / Update Bilingual Packs`. Leave the checkbox disabled to install the default full bilingual packs.

Developers can add a new localizable string by using `tr("English source text")` at the UI call site and adding entries for that exact source text under `zh_HANS`, `zh_HANT`, and `ja_JP` in `core/localization.py`. For formatted messages, use a stable template, for example `tr("Switched UI language to {name}").format(name=language_name)`.

## Verification

Verification was run after implementation:

- `python -m py_compile core/localization.py ui/preferences.py tests/test_preferences_helpers.py tests/test_localization.py` completed with exit code 0.
- `pytest -q` reported `45 passed, 2 skipped`.
- Focused experimental toggle tests reported `6 passed`.

The localization tests cover language alias normalization, fallback behavior, and representative required UI strings across all non-English translation dictionaries. Existing menu and preference helper tests confirm English fallback remains stable in a non-Blender test environment.

## Journey Log

> Brief notes on what informed the final design. Not required reading.

- [lesson] Keep Blender registration labels static unless the text is supplied at runtime; class metadata is not a reliable place for context-sensitive translation.
- [lesson] Helper summaries should translate their templates before formatting, so dynamic counts and versions remain unchanged while surrounding UI text localizes.

## Source Materials

| File | Role | Notes |
|------|------|-------|
| `docs/compose/plans/2026-07-14-addon-localization.md` | Implementation plan | Complete; final implementation uses the planned `core/localization.py` and `tr()` helper approach. |
| `docs/compose/plans/2026-07-14-experimental-scope-enable.md` | Follow-up implementation plan | Complete; adds explicit opt-in behavior for Experimental Region Scope. |
