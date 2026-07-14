# Add-on Localization Implementation Plan

> [!NOTE]
> This document may not reflect the current implementation.
> See the final report for up-to-date state:
> [Final Report](../reports/addon-localization.md)

> **For agentic workers:** REQUIRED SUB-SKILL: Use compose:subagent (recommended) or compose:execute to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add built-in translations for the add-on UI in English, Simplified Chinese, Traditional Chinese, and Japanese.

**Architecture:** Add a lightweight `core/localization.py` translation dictionary and `tr()` helper. UI modules call `tr()` for dynamic labels, button text, and report messages. Blender class registration labels remain safe static English unless a runtime text override is available in layout/operator calls.

**Tech Stack:** Python 3, Blender Python API, pytest.

## Global Constraints

- Translate add-on UI only; do not modify Blender built-in translations.
- Support `en_US`, `zh_HANS`/`zh_CN`, `zh_HANT`/`zh_TW`, and `ja_JP`.
- Fallback to English source text when a translation is missing.
- Do not translate user language names, language codes, manifest filenames, `zh_en`, or `en_zh`.
- Keep bake, install, and language-switch behavior unchanged.

---

### Task 1: Add Localization Core

**Files:**
- Create: `core/localization.py`
- Create: `tests/test_localization.py`

**Interfaces:**
- Produces `normalize_language(language_code: str | None) -> str`
- Produces `translate(text: str, language_code: str | None = None) -> str`
- Produces `tr(text: str) -> str`

- [ ] **Step 1: Write failing tests**

Add `tests/test_localization.py`:

```python
from Quickly_switch_languages.core.localization import normalize_language, translate


def test_normalize_language_aliases():
    assert normalize_language("zh_CN") == "zh_HANS"
    assert normalize_language("zh_TW") == "zh_HANT"
    assert normalize_language("ja_JP") == "ja_JP"
    assert normalize_language("en_US") == "en_US"


def test_translate_returns_supported_languages_and_falls_back():
    assert translate("Basic Language Switching", "zh_HANS") == "基础语言切换"
    assert translate("Basic Language Switching", "zh_HANT") == "基礎語言切換"
    assert translate("Basic Language Switching", "ja_JP") == "基本言語切り替え"
    assert translate("Missing String", "zh_HANS") == "Missing String"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest -q tests/test_localization.py`

Expected: FAIL because module does not exist.

- [ ] **Step 3: Implement localization module**

Create `core/localization.py` with:

```python
try:
    import bpy
except Exception:
    bpy = None


LANGUAGE_ALIASES = {
    "zh_CN": "zh_HANS",
    "zh_HANS": "zh_HANS",
    "zh_TW": "zh_HANT",
    "zh_HANT": "zh_HANT",
    "ja_JP": "ja_JP",
    "en_US": "en_US",
}

TRANSLATIONS = {
    "zh_HANS": {"Basic Language Switching": "基础语言切换"},
    "zh_HANT": {"Basic Language Switching": "基礎語言切換"},
    "ja_JP": {"Basic Language Switching": "基本言語切り替え"},
}


def normalize_language(language_code: str | None) -> str:
    return LANGUAGE_ALIASES.get(language_code or "en_US", "en_US")


def translate(text: str, language_code: str | None = None) -> str:
    language = normalize_language(language_code)
    return TRANSLATIONS.get(language, {}).get(text, text)


def tr(text: str) -> str:
    language = None
    if bpy is not None:
        try:
            language = bpy.context.preferences.view.language
        except Exception:
            language = None
    return translate(text, language)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest -q tests/test_localization.py`

Expected: PASS.

---

### Task 2: Fill Translation Dictionary

**Files:**
- Modify: `core/localization.py`
- Modify: `tests/test_localization.py`

**Interfaces:**
- Expands `TRANSLATIONS` coverage for current add-on fixed UI strings.

- [ ] **Step 1: Add coverage test for required UI strings**

Add representative strings covering Basic/Advanced/Experimental and operations:

```python
def test_required_ui_strings_have_all_non_english_translations():
    required = [
        "Basic Language Switching",
        "Advanced: Bilingual Language Packs",
        "Experimental: Region Scope",
        "Install / Update Bilingual Packs",
        "Uninstall Bilingual Packs",
        "Add Language...",
        "Manage Languages...",
        "Switched UI language to {name}",
    ]
    for language in ("zh_HANS", "zh_HANT", "ja_JP"):
        for text in required:
            assert translate(text, language) != text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest -q tests/test_localization.py::test_required_ui_strings_have_all_non_english_translations`

Expected: FAIL because dictionary is incomplete.

- [ ] **Step 3: Add dictionary entries**

Add translations for all fixed strings currently shown in `ui/menu.py` and `ui/preferences.py`. Include format-template strings such as `"Switched UI language to {name}"`, `"Favorites: {count} | Save after switch: {state}"`, and status values `"On"` / `"Off"`.

- [ ] **Step 4: Run localization tests**

Run: `pytest -q tests/test_localization.py`

Expected: PASS.

---

### Task 3: Apply Localization in UI Modules

**Files:**
- Modify: `ui/menu.py`
- Modify: `ui/preferences.py`
- Modify: `tests/test_menu.py`
- Modify: `tests/test_preferences_helpers.py`

**Interfaces:**
- Consumes `from ..core.localization import tr`

- [ ] **Step 1: Replace fixed UI labels with `tr()`**

Examples:

```python
row.label(text=tr("Basic Language Switching"), icon='PREFERENCES')
box.operator("language_switcher.show_add_language_menu", icon='ADD', text=tr("Add Language..."))
layout.operator("language_switcher.open_preferences", text=tr("Manage Languages..."), icon='PREFERENCES')
```

For formatted reports, use translated templates:

```python
self.report({'INFO'}, tr("Switched UI language to {name}").format(name=self.language_name))
```

- [ ] **Step 2: Keep dynamic/user-owned text unmodified**

Do not wrap language names, language codes, file paths, `zh_en`, `en_zh`, exception messages, or manifest filenames unless they are part of a fixed English sentence.

- [ ] **Step 3: Update tests that assert exact English text**

If any tests assert labels or reports, keep English expected values under default `en_US` fallback.

- [ ] **Step 4: Run UI-related tests**

Run: `pytest -q tests/test_localization.py tests/test_menu.py tests/test_preferences_helpers.py`

Expected: PASS.

---

### Task 4: Runtime Verification

**Files:**
- Modify only if runtime verification finds issues.

- [ ] **Step 1: Run full tests and compile**

Run:

```text
pytest -q
python -m py_compile core/localization.py ui/menu.py ui/preferences.py
```

Expected: tests pass and compile exits 0.

- [ ] **Step 2: Run Blender registration smoke test**

Expected: `ADDON_REGISTER_OK`.

- [ ] **Step 3: Run Blender translation smoke test**

Use Blender background script to assert:

```python
from Quickly_switch_languages.core.localization import translate
assert translate("Basic Language Switching", "zh_HANS") == "基础语言切换"
assert translate("Basic Language Switching", "zh_HANT") == "基礎語言切換"
assert translate("Basic Language Switching", "ja_JP") == "基本言語切り替え"
```

Expected: assertions pass.
