# Custom English Bilingual Pack Implementation Plan

> [!NOTE]
> This document may not reflect the current implementation.
> See the final report for up-to-date state:
> [Final Report](../reports/bilingual-language-pack.md)

> **For agentic workers:** REQUIRED SUB-SKILL: Use compose:subagent (recommended) or compose:execute to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let users choose Language 1 and Language 2 for one generated bilingual pack, with one side required to be English and the other side using an installed Blender `.mo` language.

**Architecture:** Keep the existing fixed `zh_en`/`en_zh` APIs for tests and compatibility, but add a pair-based baker/installer path. The pair path reads the non-English `.mo`, combines it with English msgids, and generates exactly one language code based on current order, such as `zh_en` or `en_ja` style names. Preferences provide two language code fields; users can swap Language 1 and Language 2 to reverse display order.

**Tech Stack:** Python 3, Blender Python API, pytest.

## Global Constraints

- First version supports exactly one English side and one non-English side.
- Installing a custom pair generates one bilingual language only.
- Swapping Language 1 and Language 2 reverses output order.
- Existing scope keyword filtering remains supported.
- Do not implement arbitrary non-English + non-English pairs in this iteration.

---

### Task 1: Add Pair-Based Bilingual Baking and Install

**Covers:** User request: choose source/target as Language 1 / Language 2, with one English side, and install only the selected order.

**Files:**
- Modify: `bilingual/baker.py`
- Modify: `bilingual/installer.py`
- Modify: `ui/preferences.py`
- Modify: `tests/test_bilingual_baker.py`
- Modify: `tests/test_bilingual_installer.py`
- Modify: `tests/test_preferences_helpers.py`

**Interfaces:**
- Produces `bilingual_language_code(language1_code: str, language2_code: str) -> str`.
- Produces `bake_bilingual_pair_file(source_mo: Path, output_root: Path, output_code: str, english_first: bool, scope_keywords: set[str] | None = None) -> Path`.
- Extends `install_bilingual_pack(..., language1_code="zh_HANS", language1_name="简体中文", language2_code="en_US", language2_name="English")`.

- [ ] **Step 1: Write failing tests**

Add tests proving pair baking reverses order, installer installs one generated code, and preferences reject pairs where neither or both sides are English.

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest -q tests/test_bilingual_baker.py tests/test_bilingual_installer.py tests/test_preferences_helpers.py`

Expected: FAIL because pair APIs and preference fields do not exist yet.

- [ ] **Step 3: Implement minimal pair support**

Add the pair baker, dynamic installer entry, and preference fields `bilingual_language_1` / `bilingual_language_2`. Validate exactly one side normalizes to `en_US` before install.

- [ ] **Step 4: Run targeted tests**

Run: `pytest -q tests/test_bilingual_baker.py tests/test_bilingual_installer.py tests/test_preferences_helpers.py`

Expected: PASS.

- [ ] **Step 5: Run full verification**

Run:

```text
python -m py_compile bilingual/baker.py bilingual/installer.py ui/preferences.py
pytest -q
```

Expected: compile exits 0 and tests pass.
