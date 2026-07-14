# Blender Verification and Release Package Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use compose:subagent (recommended) or compose:execute to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Verify Quick Language Switcher in a real Blender background process and produce a clean, installable version 1.0.0 ZIP archive.

**Architecture:** Use Blender's `--factory-startup --background` mode with a temporary user configuration directory to load the add-on from the workspace, register it, verify its registered menu/operator integration, and unregister it. After successful verification, archive only extension/package source files and documentation into `dist/quickly_switch_languages-1.0.0.zip`; exclude tests, generated files, runtime state, tool metadata, and previous archives.

**Tech Stack:** Blender 5.x Python runtime, PowerShell, Python standard library ZIP tooling, pytest.

## Global Constraints

- Do not install or modify a generated bilingual locale pack during release verification.
- Use `--factory-startup --background` and an isolated Blender user directory.
- Do not include `tests/`, `generated/`, `user_data/`, `.mimocode/`, `__pycache__/`, `.pytest_cache/`, or any ZIP archive inside the release ZIP.
- The release ZIP must contain one top-level `quickly_switch_languages/` directory with `blender_manifest.toml` at its root.
- Release packaging is permitted only after the Blender smoke test, pytest suite, and py_compile pass.

---

### Task 1: Run Real Blender Smoke Test

**Files:**
- Test only: temporary Blender Python expression and temporary user directory.

- [ ] **Step 1: Check Blender version**

Run:

```powershell
& "F:\Blender_Port\Dev\build_windows_Lite_x64_vc18_Release\bin\Release\blender.exe" --version
```

Expected: Blender 5.x reports successfully.

- [ ] **Step 2: Run isolated registration smoke test**

Run Blender with `--factory-startup --background`, point `BLENDER_USER_CONFIG` at a temporary directory, prepend the workspace parent to `sys.path`, then execute:

```python
import bpy
import Quickly_switch_languages as addon

addon.register()
assert hasattr(bpy.types, "LANGUAGE_SWITCHER_OT_switch_language")
assert hasattr(bpy.types, "LANGUAGE_SWITCHER_OT_install_bilingual_pack")
addon.unregister()
```

Expected: process exits 0; no traceback is emitted.

### Task 2: Re-run Automated Release Gates

**Files:**
- Test only.

- [ ] **Step 1: Run full tests**

Run: `pytest -q`

Expected: all tests pass.

- [ ] **Step 2: Compile package modules**

Run the documented `python -m py_compile` command for all add-on modules.

Expected: command exits 0 with no syntax errors.

### Task 3: Build and Inspect Release ZIP

**Files:**
- Create: `dist/quickly_switch_languages-1.0.0.zip`

- [ ] **Step 1: Build archive after all gates pass**

Use Python `zipfile` to package only:

```text
__init__.py
blender_manifest.toml
LICENSE
README.md
DEVELOPMENT.md
core/
ui/
bilingual/
data/
```

Archive names are prefixed with `quickly_switch_languages/`.

- [ ] **Step 2: Inspect archive content**

Use Python `zipfile` to assert:

```text
quickly_switch_languages/blender_manifest.toml exists
quickly_switch_languages/__init__.py exists
no entry contains tests/, generated/, user_data/, .mimocode/, __pycache__/, .pytest_cache/
```

- [ ] **Step 3: Report artifact location and gate output**

Provide ZIP path, byte size, Blender version, smoke-test result, unit-test result, and compile result.

---

## Self-Review

- The plan validates real Blender registration before packaging.
- The archive content is explicit and avoids all runtime/test/tool artifacts.
- The expected ZIP layout matches Blender extension installation requirements.
