# Default Favorites Three Languages Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use compose:subagent (recommended) or compose:execute to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Simplify the default top-bar language favorites to English, Simplified Chinese, and Japanese.

**Architecture:** Keep the existing `LanguageManager` JSON format. Update both the reset operator's in-code default list and the shipped `data/languages.json` seed data so new installs and reset actions produce the same three-language list.

**Tech Stack:** Python 3, Blender Python API, pytest.

## Global Constraints

- Default favorite order must be `en_US`, `zh_CN`, `ja_JP`.
- Keep user-owned language names and language codes untranslated.
- Do not change the available-language popup list.

---

### Task 1: Reduce Default Favorites

**Covers:** User request: keep only English, Simplified Chinese, and Japanese in default favorites.

**Files:**
- Modify: `ui/menu.py`
- Modify: `data/languages.json`
- Modify: `tests/test_menu.py`

**Interfaces:**
- Consumes `LANGUAGE_SWITCHER_OT_add_default_languages.execute(context)`.
- Produces reset defaults: `[{'code': 'en_US', 'name': 'English'}, {'code': 'zh_CN', 'name': '简体中文'}, {'code': 'ja_JP', 'name': '日本語'}]`.

- [ ] **Step 1: Write failing tests**

Add tests to `tests/test_menu.py` that execute `LANGUAGE_SWITCHER_OT_add_default_languages` with a fake `LanguageManager.update_favorites()` sink and assert the three-language list in order.

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest -q tests/test_menu.py::test_add_default_languages_uses_three_language_default`

Expected: FAIL because the current default list contains more than three languages.

- [ ] **Step 3: Update implementation and seed data**

In `ui/menu.py`, replace the `default_languages` list with exactly:

```python
default_languages = [
    {"code": "en_US", "name": "English"},
    {"code": "zh_CN", "name": "简体中文"},
    {"code": "ja_JP", "name": "日本語"},
]
```

In `data/languages.json`, replace `favorites` with the same three entries.

- [ ] **Step 4: Run targeted tests**

Run: `pytest -q tests/test_menu.py tests/test_integration.py`

Expected: PASS.

- [ ] **Step 5: Run full verification**

Run:

```text
python -m py_compile ui/menu.py tests/test_menu.py
pytest -q
```

Expected: compile exits 0 and tests pass.
