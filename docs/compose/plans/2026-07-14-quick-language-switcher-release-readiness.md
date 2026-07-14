# Quick Language Switcher Release Readiness Implementation Plan

> [!NOTE]
> This document may not reflect the current implementation.
> See the final report for up-to-date state:
> [Final Report](../reports/release-readiness.md)

> **For agentic workers:** REQUIRED SUB-SKILL: Use compose:subagent (recommended) or compose:execute to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring the Blender 5.1.2 copy of `Quickly_switch_languages` to a minimal publishable state.

**Architecture:** Keep the existing `ui/`, `core/`, `bilingual/`, `data/`, and `tests/` structure. Treat bilingual locale installation as the highest-risk subsystem: unit-test manifest/languages accumulation, then verify Blender 5.1.2 registration and installation behavior with background smoke commands.

**Tech Stack:** Blender Python API, pytest, pure-Python `.mo` reader/writer, `blender_manifest.toml`.

## Global Constraints

- Target first: Blender 5.1.2 addon copy at `C:\Users\86177\AppData\Roaming\Blender Foundation\Blender\5.1\scripts\addons\Quickly_switch_languages`.
- Bilingual pack install must not auto-switch or persist Blender UI language to generated locale codes such as `en_ja` or `zh_en`.
- Multiple generated locale codes must coexist in Blender `datafiles/locale/languages` and in `bilingual_manifest.json`.
- Runtime user data belongs in Blender user config `quick_language_switcher`, not in plugin `data/`.
- Do not modify unrelated dirty worktree files or sibling addons.

---

### Task 1: Confirm multi-pack coexistence fix

**Covers:** release blocker T32

**Files:**
- Inspect: `bilingual/installer.py`
- Inspect: `tests/test_bilingual_installer.py`

**Interfaces:**
- Consumes: `install_bilingual_pair(..., manifest_path=...)`, `patch_languages_text(...)`, `write_merged_manifest(...)`
- Produces: evidence that sequential pair installation preserves all installed codes and files

- [ ] **Step 1: Run focused installer tests**

Run: `pytest tests/test_bilingual_installer.py -q`
Expected: `20 passed`

- [ ] **Step 2: Confirm the coexistence test covers sequential installs**

Check `tests/test_bilingual_installer.py::test_install_bilingual_pairs_accumulate_languages_and_manifest` verifies both `en_ja` and `zh_en` remain in `languages`, files, and manifest.

- [ ] **Step 3: Close T32 if the test and implementation are present**

Mark T32 done only after the focused test passes.

### Task 2: Update publish-facing metadata and docs

**Covers:** release readiness

**Files:**
- Modify: `README.md`
- Inspect: `blender_manifest.toml`
- Inspect: `LICENSE`

**Interfaces:**
- Consumes: existing add-on behavior and manifest values
- Produces: README that matches current features and risk boundaries

- [ ] **Step 1: Replace stale README claims**

Update README to reflect: top-bar `Switch Language`, favorites in user config, bilingual pack install risk, no auto language switch, multi-pack coexistence, emergency cleanup, and GPL-3.0-or-later license.

- [ ] **Step 2: Verify manifest publish fields**

Check `id`, `version`, `name`, `tagline`, `maintainer`, `type`, `tags`, `blender_version_min`, `license`, and `permissions` are present and consistent.

### Task 3: Run release verification

**Covers:** release readiness

**Files:**
- Verify: all Python source files
- Verify: tests

**Interfaces:**
- Consumes: finished code and README
- Produces: passing verification evidence

- [ ] **Step 1: Run full test suite**

Run: `pytest -q`
Expected: all tests pass.

- [ ] **Step 2: Compile key Python files**

Run: `python -m py_compile "__init__.py" "core\language_manager.py" "core\paths.py" "core\localization.py" "core\keymap.py" "ui\menu.py" "ui\preferences.py" "bilingual\installer.py" "bilingual\baker.py" "bilingual\mo.py" "bilingual\scope.py"`
Expected: no output and exit code 0.

- [ ] **Step 3: Run Blender 5.1.2 enable smoke**

Run Blender with `--factory-startup --background`, enable `Quickly_switch_languages`, and assert menu/operator registration succeeds.

- [ ] **Step 4: Run Blender 5.1.2 bilingual install smoke**

Install two bilingual pairs sequentially in background and assert `languages` contains both codes, manifest contains both codes, and current UI language remains unchanged.

### Task 4: Report release state

**Covers:** release readiness

**Files:**
- Optional report in conversation only unless major findings require a saved report

**Interfaces:**
- Consumes: verification output from Tasks 1-3
- Produces: clear release status and remaining risks

- [ ] **Step 1: Summarize status**

Report what passed, what changed, and any residual manual Blender UI checks needed.

- [ ] **Step 2: Mark T33 done only if verification passes**

If any release verification fails, keep T33 in progress or blocked with the exact failing command.
