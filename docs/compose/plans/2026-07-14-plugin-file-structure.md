# Plugin File Structure Implementation Plan

> [!NOTE]
> This document may not reflect the current implementation.
> See the final report for up-to-date state:
> [Final Report](../reports/plugin-file-structure.md)

> **For agentic workers:** REQUIRED SUB-SKILL: Use compose:subagent (recommended) or compose:execute to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reorganize the add-on into intuitive `ui/`, `core/`, `bilingual/`, `data/`, and `tests/` folders without changing runtime behavior.

**Architecture:** Keep `__init__.py` as the Blender add-on entrypoint. Move UI modules into `ui/`, language/data helpers into `core/`, bilingual language-pack code into `bilingual/`, JSON runtime data into `data/`, and tests into `tests/`. Update relative imports and path helpers so Blender registration, pytest, and background install continue to work.

**Tech Stack:** Python 3, Blender Python API, pytest, gettext `.mo` utilities.

## Global Constraints

- Do not change user-facing behavior while restructuring.
- Do not move `generated/`; generated `.mo` output stays at `generated/<version>/...`.
- Move `languages.json` and `bilingual_manifest.json` to `data/` and update all code paths.
- Keep `__init__.py` at add-on root as Blender's external entrypoint.
- Use package-relative imports in production modules.
- Keep tests runnable with `pytest -q` from the add-on root.

---

### Task 1: Create Package Folders and Move Core Modules

**Covers:** folder structure, module boundaries

**Files:**
- Create: `ui/__init__.py`
- Create: `core/__init__.py`
- Create: `bilingual/__init__.py`
- Move: `menu.py` -> `ui/menu.py`
- Move: `preferences.py` -> `ui/preferences.py`
- Move: `language_manager.py` -> `core/language_manager.py`
- Move: `mo_utils.py` -> `bilingual/mo.py`
- Move: `bilingual_baker.py` -> `bilingual/baker.py`
- Move: `bilingual_installer.py` -> `bilingual/installer.py`
- Move: `bilingual_scope.py` -> `bilingual/scope.py`

**Interfaces:**
- Produces import paths: `.ui.menu`, `.ui.preferences`, `.core.language_manager`, `.bilingual.mo`, `.bilingual.baker`, `.bilingual.installer`, `.bilingual.scope`

- [ ] **Step 1: Move files with package folders**

Use filesystem moves or patches to create the folder layout and remove root-level copies.

- [ ] **Step 2: Update production imports**

Required import changes:

```python
# __init__.py
_submodules = ["ui.menu", "ui.preferences"]
from .ui import menu
from .ui import preferences

# ui/menu.py
from ..core.language_manager import LanguageManager

# ui/preferences.py
from ..core.language_manager import LanguageManager
from ..bilingual.installer import install_bilingual_pack, uninstall_from_manifest
from ..bilingual.scope import get_scope_keywords

# bilingual/baker.py
from .mo import MoCatalog, read_mo, write_mo

# bilingual/installer.py
from .baker import bake_bilingual_files
```

- [ ] **Step 3: Compile package modules**

Run: `python -m py_compile __init__.py ui/menu.py ui/preferences.py core/language_manager.py bilingual/mo.py bilingual/baker.py bilingual/installer.py bilingual/scope.py`

Expected: exit code 0.

---

### Task 2: Move Runtime Data and Add Path Helpers

**Covers:** data folder clarity, behavior preservation

**Files:**
- Create: `core/paths.py`
- Move: `languages.json` -> `data/languages.json`
- Move: `bilingual_manifest.json` -> `data/bilingual_manifest.json`
- Modify: `ui/menu.py`
- Modify: `ui/preferences.py`
- Modify: `bilingual/installer.py`

**Interfaces:**
- Produces `addon_root() -> Path`, `data_path(filename: str) -> Path`

- [ ] **Step 1: Write path helper implementation**

Create `core/paths.py`:

```python
from pathlib import Path


def addon_root() -> Path:
    return Path(__file__).resolve().parents[1]


def data_path(filename: str) -> Path:
    return addon_root() / "data" / filename
```

- [ ] **Step 2: Update JSON path callers**

Replace `os.path.dirname(__file__) / languages.json` logic with:

```python
from ..core.paths import data_path
json_path = data_path("languages.json")
```

Update manifest path in `ui/preferences.py` to:

```python
manifest_path = data_path("bilingual_manifest.json")
```

Update `bilingual/installer.py` calls to write/read manifest at `addon_root / "data" / "bilingual_manifest.json"`.

- [ ] **Step 3: Run data-path tests**

Run: `pytest -q tests/test_language_manager.py tests/test_menu.py tests/test_bilingual_installer.py`

Expected: PASS or Blender-only skips for Blender-dependent tests.

---

### Task 3: Move Tests and Update Test Imports

**Covers:** test folder clarity

**Files:**
- Create: `tests/__init__.py`
- Move: root `test_*.py` -> `tests/test_*.py`
- Modify: tests import helpers

**Interfaces:**
- Tests import package modules through `Quickly_switch_languages.*` or local path setup from `tests/`.

- [ ] **Step 1: Move test files**

Move all root `test_*.py` files into `tests/`.

- [ ] **Step 2: Update test import helpers**

For pure-Python tests, replace direct same-directory loading with package imports or load from parent paths. Example:

```python
ROOT = Path(__file__).resolve().parents[1]
```

Update module filenames:

```python
ROOT / "bilingual" / "mo.py"
ROOT / "bilingual" / "baker.py"
ROOT / "bilingual" / "scope.py"
ROOT / "bilingual" / "installer.py"
ROOT / "core" / "language_manager.py"
ROOT / "ui" / "menu.py"
ROOT / "ui" / "preferences.py"
```

- [ ] **Step 3: Run all tests**

Run: `pytest -q`

Expected: all non-Blender tests pass, Blender-only tests may skip.

---

### Task 4: Blender Runtime Verification

**Covers:** Blender add-on entrypoint, UI registration, bilingual install path

**Files:**
- Modify only if verification reveals import path issues.

**Interfaces:**
- Consumes final package layout from Tasks 1-3.

- [ ] **Step 1: Verify Blender import and registration**

Run Blender background import:

```powershell
& "F:\Blender\Software\blender-5.0.1-windows-x64\blender.exe" --background --python-expr "import sys, importlib; sys.path.insert(0, r'C:\Users\86177\AppData\Roaming\Blender Foundation\Blender\5.0\scripts\addons'); addon=importlib.import_module('Quickly_switch_languages'); addon.register(); addon.unregister(); print('ADDON_REGISTER_OK')"
```

Expected: prints `ADDON_REGISTER_OK` and exits 0.

- [ ] **Step 2: Verify bilingual install still works**

Run Blender background install using new import paths:

```python
from Quickly_switch_languages.bilingual.scope import get_scope_keywords
from Quickly_switch_languages.bilingual.installer import install_bilingual_pack
from Quickly_switch_languages.core.paths import addon_root
```

Expected: manifest is written to `data/bilingual_manifest.json`, generated output remains under `generated/<version>/...`, and installed language codes are `zh_en,en_zh`.

- [ ] **Step 3: Final verification**

Run:

```text
pytest -q
python -m py_compile __init__.py ui/menu.py ui/preferences.py core/language_manager.py core/paths.py bilingual/mo.py bilingual/baker.py bilingual/installer.py bilingual/scope.py
```

Expected: tests pass and compile exits 0.
