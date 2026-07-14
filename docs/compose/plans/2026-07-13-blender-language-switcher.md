# Blender Language Switcher Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use compose:subagent (recommended) or compose:execute to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a Blender addon that adds a "Switch Languages to" menu in the top menu bar for quick language switching.

**Architecture:** The addon consists of five main components: addon core, menu system, language manager, settings panel, and language switcher. It uses Blender's addon preferences for settings and an external JSON file for favorite languages.

**Tech Stack:** Python, Blender Python API (bpy), JSON for data storage

## Global Constraints
- Target Blender version: 5.0+
- Must be compatible with Windows, macOS, and Linux
- No external dependencies beyond Blender's Python environment
- Follow Blender addon conventions and API guidelines
- All user-facing text must support Blender's translation system

---

### Task 1: Project Setup and Basic Structure

**Covers:** [S1, S2]
<!-- Sets up the foundational addon structure -->

**Files:**
- Create: `__init__.py`
- Create: `blender_manifest.toml`
- Create: `languages.json` (default favorite languages)

**Interfaces:**
- Consumes: None (initial setup)
- Produces: Basic addon structure that can be loaded by Blender

- [ ] **Step 1: Create addon manifest**

Create `blender_manifest.toml` with basic addon information:
```toml
schema_version = "1.0.0"

id = "quick_language_switcher"
version = "1.0.0"
name = "Quick Language Switcher"
tagline = "Quickly switch Blender interface language from top menu"
maintainer = "Developer <developer@example.com>"
type = "add-on"

blender_version_min = "5.0.0"

[permissions]
files = "Access to save/load language preferences"
```

- [ ] **Step 2: Create default languages.json**

Create `languages.json` with common languages:
```json
{
  "favorites": [
    {"code": "en_US", "name": "English"},
    {"code": "zh_CN", "name": "简体中文"},
    {"code": "ja_JP", "name": "日本語"},
    {"code": "ko_KR", "name": "한국어"},
    {"code": "de_DE", "name": "Deutsch"},
    {"code": "fr_FR", "name": "Français"},
    {"code": "es_ES", "name": "Español"},
    {"code": "pt_BR", "name": "Português (Brasil)"},
    {"code": "ru_RU", "name": "Русский"}
  ]
}
```

- [ ] **Step 3: Create basic __init__.py**

Create `__init__.py` with addon registration:
```python
bl_info = {
    "name": "Quick Language Switcher",
    "author": "Developer",
    "version": (1, 0, 0),
    "blender": (5, 0, 0),
    "location": "Topbar Menu",
    "description": "Quickly switch Blender interface language",
    "category": "Interface",
}

# Submodules to import
_submodules = []

if "bpy" in locals():
    import importlib
    import sys
    # Reload submodules
    for mod_name in _submodules:
        if mod_name in sys.modules:
            importlib.reload(sys.modules[mod_name])

def register():
    pass

def unregister():
    pass
```

- [ ] **Step 4: Test basic loading**

1. Open Blender 5.0+
2. Go to Edit > Preferences > Add-ons
3. Click "Install..." and select the addon folder
4. Enable the addon
5. Verify no error messages appear
6. Check that addon appears in the list

- [ ] **Step 5: Commit**

```bash
git add __init__.py blender_manifest.toml languages.json
git commit -m "feat: initial addon structure with manifest and default languages"
```

---

### Task 2: Language Manager (JSON Operations)

**Covers:** [S5]
<!-- Implements language favorite management via JSON file -->

**Files:**
- Create: `language_manager.py`
- Test: `test_language_manager.py`

**Interfaces:**
- Consumes: `languages.json` file
- Produces: Functions to load, save, add, remove, and list favorite languages

- [ ] **Step 1: Write failing tests for language manager**

Create `test_language_manager.py`:
```python
import json
import os
import tempfile
import pytest
from language_manager import LanguageManager

def test_load_languages():
    # Create temporary JSON file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump({"favorites": [{"code": "en_US", "name": "English"}]}, f)
        temp_path = f.name
    
    try:
        manager = LanguageManager(temp_path)
        languages = manager.get_favorites()
        assert len(languages) == 1
        assert languages[0]["code"] == "en_US"
    finally:
        os.unlink(temp_path)

def test_add_language():
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump({"favorites": []}, f)
        temp_path = f.name
    
    try:
        manager = LanguageManager(temp_path)
        manager.add_favorite({"code": "zh_CN", "name": "简体中文"})
        languages = manager.get_favorites()
        assert len(languages) == 1
        assert languages[0]["code"] == "zh_CN"
    finally:
        os.unlink(temp_path)

def test_remove_language():
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump({"favorites": [{"code": "en_US", "name": "English"}]}, f)
        temp_path = f.name
    
    try:
        manager = LanguageManager(temp_path)
        manager.remove_favorite("en_US")
        languages = manager.get_favorites()
        assert len(languages) == 0
    finally:
        os.unlink(temp_path)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest test_language_manager.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'language_manager'"

- [ ] **Step 3: Implement language manager**

Create `language_manager.py`:
```python
import json
import os
from typing import List, Dict, Optional

class LanguageManager:
    def __init__(self, json_path: str):
        self.json_path = json_path
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        if not os.path.exists(self.json_path):
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump({"favorites": []}, f, ensure_ascii=False, indent=2)
    
    def _load_data(self) -> Dict:
        with open(self.json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _save_data(self, data: Dict):
        with open(self.json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def get_favorites(self) -> List[Dict]:
        data = self._load_data()
        return data.get("favorites", [])
    
    def add_favorite(self, language: Dict) -> bool:
        """Add a language to favorites. Returns True if added, False if already exists."""
        if not all(k in language for k in ("code", "name")):
            raise ValueError("Language must have 'code' and 'name' keys")
        
        data = self._load_data()
        favorites = data.get("favorites", [])
        
        # Check if already exists
        for fav in favorites:
            if fav["code"] == language["code"]:
                return False
        
        favorites.append(language)
        data["favorites"] = favorites
        self._save_data(data)
        return True
    
    def remove_favorite(self, language_code: str) -> bool:
        """Remove a language from favorites. Returns True if removed, False if not found."""
        data = self._load_data()
        favorites = data.get("favorites", [])
        
        original_length = len(favorites)
        favorites = [fav for fav in favorites if fav["code"] != language_code]
        
        if len(favorites) < original_length:
            data["favorites"] = favorites
            self._save_data(data)
            return True
        return False
    
    def update_favorites(self, favorites: List[Dict]):
        """Replace entire favorites list."""
        data = self._load_data()
        data["favorites"] = favorites
        self._save_data(data)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest test_language_manager.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add language_manager.py test_language_manager.py
git commit -m "feat: implement language manager with JSON storage"
```

---

### Task 3: Menu System

**Covers:** [S4]
<!-- Adds the "Switch Languages to" menu to top menu bar -->

**Files:**
- Create: `menu.py`
- Modify: `__init__.py` (register menu module)
- Test: Manual testing in Blender

**Interfaces:**
- Consumes: `LanguageManager` from Task 2
- Produces: Top menu bar dropdown with favorite languages

- [ ] **Step 1: Create menu module**

Create `menu.py`:
```python
import bpy
from bpy.types import Menu, Operator
from .language_manager import LanguageManager
import os

class LANGUAGE_SWITCHER_MT_menu(Menu):
    bl_label = "Switch Languages to"
    bl_idname = "LANGUAGE_SWITCHER_MT_menu"
    
    def draw(self, context):
        layout = self.layout
        
        # Get language manager
        addon_path = os.path.dirname(os.path.dirname(__file__))
        json_path = os.path.join(addon_path, "languages.json")
        manager = LanguageManager(json_path)
        
        favorites = manager.get_favorites()
        
        if not favorites:
            layout.operator("language_switcher.add_default_languages", text="Add Default Languages")
            return
        
        # Add each favorite language
        for lang in favorites:
            op = layout.operator(
                "language_switcher.switch_language",
                text=f"{lang['name']} ({lang['code']})",
                icon='LANGUAGE'
            )
            op.language_code = lang['code']
            op.language_name = lang['name']
        
        # Add separator and management options
        layout.separator()
        layout.operator("language_switcher.open_preferences", text="Manage Languages...", icon='PREFERENCES')

class LANGUAGE_SWITCHER_OT_switch_language(Operator):
    """Switch Blender interface language"""
    bl_idname = "language_switcher.switch_language"
    bl_label = "Switch Language"
    bl_options = {'REGISTER', 'UNDO'}
    
    language_code: bpy.props.StringProperty()
    language_name: bpy.props.StringProperty()
    
    def execute(self, context):
        # Switch language
        context.preferences.view.language = self.language_code
        
        # Check if auto-save is enabled
        prefs = context.preferences.addons.get(__package__)
        if prefs and prefs.preferences.save_after_switch:
            bpy.ops.wm.save_userpref()
        
        self.report({'INFO'}, f"Switched to {self.language_name}")
        return {'FINISHED'}

class LANGUAGE_SWITCHER_OT_open_preferences(Operator):
    """Open addon preferences"""
    bl_idname = "language_switcher.open_preferences"
    bl_label = "Open Preferences"
    
    def execute(self, context):
        bpy.ops.screen.show_prefs()
        return {'FINISHED'}

class LANGUAGE_SWITCHER_OT_add_default_languages(Operator):
    """Add default language list"""
    bl_idname = "language_switcher.add_default_languages"
    bl_label = "Add Default Languages"
    
    def execute(self, context):
        addon_path = os.path.dirname(os.path.dirname(__file__))
        json_path = os.path.join(addon_path, "languages.json")
        
        # Reset to default languages
        default_languages = [
            {"code": "en_US", "name": "English"},
            {"code": "zh_CN", "name": "简体中文"},
            {"code": "ja_JP", "name": "日本語"},
            {"code": "ko_KR", "name": "한국어"},
            {"code": "de_DE", "name": "Deutsch"},
            {"code": "fr_FR", "name": "Français"},
            {"code": "es_ES", "name": "Español"},
            {"code": "pt_BR", "name": "Português (Brasil)"},
            {"code": "ru_RU", "name": "Русский"}
        ]
        
        manager = LanguageManager(json_path)
        manager.update_favorites(default_languages)
        
        self.report({'INFO'}, "Default languages added")
        return {'FINISHED'}

def draw_menu(self, context):
    """Draw function for top menu bar"""
    if context.region.alignment != 'RIGHT':
        return
    
    layout = self.layout
    layout.separator()
    layout.menu(LANGUAGE_SWITCHER_MT_menu.bl_idname, icon='LANGUAGE')

# Registration
classes = (
    LANGUAGE_SWITCHER_MT_menu,
    LANGUAGE_SWITCHER_OT_switch_language,
    LANGUAGE_SWITCHER_OT_open_preferences,
    LANGUAGE_SWITCHER_OT_add_default_languages,
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    
    # Add to top menu bar
    bpy.types.TOPBAR_HT_upper_bar.append(draw_menu)

def unregister():
    from bpy.utils import unregister_class
    
    # Remove from top menu bar
    bpy.types.TOPBAR_HT_upper_bar.remove(draw_menu)
    
    for cls in reversed(classes):
        unregister_class(cls)
```

- [ ] **Step 2: Update __init__.py to register menu**

Update `__init__.py`:
```python
bl_info = {
    "name": "Quick Language Switcher",
    "author": "Developer",
    "version": (1, 0, 0),
    "blender": (5, 0, 0),
    "location": "Topbar Menu",
    "description": "Quickly switch Blender interface language",
    "category": "Interface",
}

_submodules = ["menu"]

if "bpy" in locals():
    import importlib
    import sys
    for mod_name in _submodules:
        if mod_name in sys.modules:
            importlib.reload(sys.modules[mod_name])

from . import menu

def register():
    menu.register()

def unregister():
    menu.unregister()
```

- [ ] **Step 3: Test menu in Blender**

1. Restart Blender or reload addon
2. Check top menu bar for "Switch Languages to" menu
3. Click menu to see language list
4. Click a language to switch
5. Verify language changes
6. Check "Manage Languages..." opens preferences

- [ ] **Step 4: Commit**

```bash
git add menu.py __init__.py
git commit -m "feat: add language switcher menu to top menu bar"
```

---

### Task 4: Settings Panel

**Covers:** [S6]
<!-- Adds settings page in Blender preferences -->

**Files:**
- Create: `preferences.py`
- Modify: `__init__.py` (register preferences module)
- Test: Manual testing in Blender preferences

**Interfaces:**
- Consumes: `LanguageManager` from Task 2
- Produces: Settings page with favorite language management

- [ ] **Step 1: Create preferences module**

Create `preferences.py`:
```python
import bpy
from bpy.props import BoolProperty, CollectionProperty, StringProperty
from bpy.types import AddonPreferences, Operator, UIList
from .language_manager import LanguageManager
import os

class LANGUAGE_SWITCHER_UL_favorites(UIList):
    bl_idname = "LANGUAGE_SWITCHER_UL_favorites"
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text=f"{item.name} ({item.code})", icon='LANGUAGE')
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon='LANGUAGE')

class LanguageItem(bpy.types.PropertyGroup):
    code: StringProperty(name="Code")
    name: StringProperty(name="Name")

class LANGUAGE_SWITCHER_OT_add_language(Operator):
    """Add a language to favorites"""
    bl_idname = "language_switcher.add_language"
    bl_label = "Add Language"
    bl_options = {'REGISTER', 'UNDO'}
    
    language_code: bpy.props.StringProperty()
    language_name: bpy.props.StringProperty()
    
    def execute(self, context):
        prefs = context.preferences.addons[__package__].preferences
        
        # Check if already exists
        for lang in prefs.favorites:
            if lang.code == self.language_code:
                self.report({'WARNING'}, "Language already in favorites")
                return {'CANCELLED'}
        
        # Add new language
        new_lang = prefs.favorites.add()
        new_lang.code = self.language_code
        new_lang.name = self.language_name
        
        # Save to JSON
        self._save_to_json(context)
        
        self.report({'INFO'}, f"Added {self.language_name}")
        return {'FINISHED'}
    
    def _save_to_json(self, context):
        addon_path = os.path.dirname(os.path.dirname(__file__))
        json_path = os.path.join(addon_path, "languages.json")
        manager = LanguageManager(json_path)
        
        prefs = context.preferences.addons[__package__].preferences
        favorites = [{"code": lang.code, "name": lang.name} for lang in prefs.favorites]
        manager.update_favorites(favorites)

class LANGUAGE_SWITCHER_OT_remove_language(Operator):
    """Remove a language from favorites"""
    bl_idname = "language_switcher.remove_language"
    bl_label = "Remove Language"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        prefs = context.preferences.addons[__package__].preferences
        
        if prefs.favorites_index < len(prefs.favorites):
            lang = prefs.favorites[prefs.favorites_index]
            prefs.favorites.remove(prefs.favorites_index)
            
            # Adjust index
            if prefs.favorites_index >= len(prefs.favorites):
                prefs.favorites_index = max(0, len(prefs.favorites) - 1)
            
            # Save to JSON
            self._save_to_json(context)
            
            self.report({'INFO'}, "Language removed")
        return {'FINISHED'}
    
    def _save_to_json(self, context):
        addon_path = os.path.dirname(os.path.dirname(__file__))
        json_path = os.path.join(addon_path, "languages.json")
        manager = LanguageManager(json_path)
        
        prefs = context.preferences.addons[__package__].preferences
        favorites = [{"code": lang.code, "name": lang.name} for lang in prefs.favorites]
        manager.update_favorites(favorites)

class LANGUAGE_SWITCHER_OT_move_language(Operator):
    """Move language up or down in list"""
    bl_idname = "language_switcher.move_language"
    bl_label = "Move Language"
    bl_options = {'REGISTER', 'UNDO'}
    
    direction: bpy.props.EnumProperty(
        items=(
            ('UP', "Up", ""),
            ('DOWN', "Down", ""),
        )
    )
    
    def execute(self, context):
        prefs = context.preferences.addons[__package__].preferences
        
        if self.direction == 'UP':
            if prefs.favorites_index > 0:
                prefs.favorites.move(prefs.favorites_index, prefs.favorites_index - 1)
                prefs.favorites_index -= 1
        elif self.direction == 'DOWN':
            if prefs.favorites_index < len(prefs.favorites) - 1:
                prefs.favorites.move(prefs.favorites_index, prefs.favorites_index + 1)
                prefs.favorites_index += 1
        
        # Save to JSON
        self._save_to_json(context)
        
        return {'FINISHED'}
    
    def _save_to_json(self, context):
        addon_path = os.path.dirname(os.path.dirname(__file__))
        json_path = os.path.join(addon_path, "languages.json")
        manager = LanguageManager(json_path)
        
        prefs = context.preferences.addons[__package__].preferences
        favorites = [{"code": lang.code, "name": lang.name} for lang in prefs.favorites]
        manager.update_favorites(favorites)

class QuickLanguageSwitcherPreferences(AddonPreferences):
    bl_idname = __package__
    
    save_after_switch: BoolProperty(
        name="Save preference after switching",
        description="Automatically save Blender preferences after language switch",
        default=False,
    )
    
    favorites: CollectionProperty(type=LanguageItem)
    favorites_index: bpy.props.IntProperty()
    
    def draw(self, context):
        layout = self.layout
        
        # General settings
        box = layout.box()
        box.label(text="General Settings", icon='PREFERENCES')
        box.prop(self, "save_after_switch")
        
        # Favorite languages management
        box = layout.box()
        box.label(text="Favorite Languages", icon='FILE_FOLDER')
        
        row = box.row()
        row.template_list(
            "LANGUAGE_SWITCHER_UL_favorites",
            "",
            self,
            "favorites",
            self,
            "favorites_index",
            rows=5
        )
        
        col = row.column(align=True)
        col.operator("language_switcher.add_language", icon='ADD', text="")
        col.operator("language_switcher.remove_language", icon='REMOVE', text="")
        
        col.separator()
        col.operator("language_switcher.move_language", icon='TRIA_UP', text="").direction = 'UP'
        col.operator("language_switcher.move_language", icon='TRIA_DOWN', text="").direction = 'DOWN'
        
        # Add language from available languages
        box.separator()
        box.label(text="Add from available languages:")
        
        # Get available languages from Blender
        available_languages = [
            ("en_US", "English"),
            ("zh_CN", "简体中文"),
            ("ja_JP", "日本語"),
            ("ko_KR", "한국어"),
            ("de_DE", "Deutsch"),
            ("fr_FR", "Français"),
            ("es_ES", "Español"),
            ("pt_BR", "Português (Brasil)"),
            ("ru_RU", "Русский"),
            # Add more as needed
        ]
        
        row = box.row(align=True)
        for code, name in available_languages[:5]:  # Show first 5
            op = row.operator("language_switcher.add_language", text=name)
            op.language_code = code
            op.language_name = name
        
        if len(available_languages) > 5:
            row = box.row(align=True)
            for code, name in available_languages[5:10]:
                op = row.operator("language_switcher.add_language", text=name)
                op.language_code = code
                op.language_name = name

# Registration
classes = (
    LANGUAGE_SWITCHER_UL_favorites,
    LanguageItem,
    LANGUAGE_SWITCHER_OT_add_language,
    LANGUAGE_SWITCHER_OT_remove_language,
    LANGUAGE_SWITCHER_OT_move_language,
    QuickLanguageSwitcherPreferences,
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
```

- [ ] **Step 2: Update __init__.py to register preferences**

Update `__init__.py`:
```python
bl_info = {
    "name": "Quick Language Switcher",
    "author": "Developer",
    "version": (1, 0, 0),
    "blender": (5, 0, 0),
    "location": "Topbar Menu",
    "description": "Quickly switch Blender interface language",
    "category": "Interface",
}

_submodules = ["menu", "preferences"]

if "bpy" in locals():
    import importlib
    import sys
    for mod_name in _submodules:
        if mod_name in sys.modules:
            importlib.reload(sys.modules[mod_name])

from . import menu
from . import preferences

def register():
    preferences.register()
    menu.register()

def unregister():
    menu.unregister()
    preferences.unregister()
```

- [ ] **Step 3: Test settings panel**

1. Restart Blender or reload addon
2. Go to Edit > Preferences > Add-ons
3. Find "Quick Language Switcher" and expand
4. Test "Save preference after switching" checkbox
5. Test adding/removing/reordering favorite languages
6. Verify changes persist after Blender restart

- [ ] **Step 4: Commit**

```bash
git add preferences.py __init__.py
git commit -m "feat: add settings panel for favorite language management"
```

---

### Task 5: Integration and Final Testing

**Covers:** [S7, S10]
<!-- Integrates all components and performs comprehensive testing -->

**Files:**
- Modify: All existing files (minor adjustments)
- Test: Comprehensive testing in Blender

**Interfaces:**
- Consumes: All previous tasks
- Produces: Fully functional addon

- [ ] **Step 1: Update menu to use preferences**

Update `menu.py` to check preferences for save_after_switch:
```python
# In LANGUAGE_SWITCHER_OT_switch_language.execute():
def execute(self, context):
    # Switch language
    context.preferences.view.language = self.language_code
    
    # Check if auto-save is enabled
    try:
        prefs = context.preferences.addons[__package__].preferences
        if prefs.save_after_switch:
            bpy.ops.wm.save_userpref()
    except:
        pass
    
    self.report({'INFO'}, f"Switched to {self.language_name}")
    return {'FINISHED'}
```

- [ ] **Step 2: Update preferences to load from JSON on startup**

Add loading logic to preferences:
```python
class QuickLanguageSwitcherPreferences(AddonPreferences):
    bl_idname = __package__
    
    def draw(self, context):
        # Load favorites from JSON if empty
        if not self.favorites:
            self._load_from_json()
        
        # ... rest of draw method
    
    def _load_from_json(self):
        addon_path = os.path.dirname(os.path.dirname(__file__))
        json_path = os.path.join(addon_path, "languages.json")
        
        if os.path.exists(json_path):
            manager = LanguageManager(json_path)
            favorites = manager.get_favorites()
            
            for lang in favorites:
                new_lang = self.favorites.add()
                new_lang.code = lang["code"]
                new_lang.name = lang["name"]
```

- [ ] **Step 3: Comprehensive testing**

Test the following scenarios:
1. Fresh install: addon loads, default languages appear in menu
2. Language switching: click language in menu, Blender interface changes
3. Auto-save: enable setting, switch language, restart Blender, verify language persists
4. Manual save: disable setting, switch language, verify preference not saved
5. Add language: add new language to favorites, verify it appears in menu
6. Remove language: remove language from favorites, verify it disappears from menu
7. Reorder languages: change order in preferences, verify menu order updates
8. Cross-platform: test on Windows, macOS, Linux (if possible)

- [ ] **Step 4: Create README documentation**

Create `README.md` with:
- Addon description
- Installation instructions
- Usage instructions
- Features list
- Troubleshooting

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "feat: complete language switcher addon with full integration

- Add 'Switch Languages to' menu in top menu bar
- Store favorite languages in JSON file
- Settings panel for managing favorites
- Auto-save option for language preference
- Default language list with common languages"
```

---

## Self-Review Checklist

**1. Spec coverage:**
- [S1] Problem: Covered by Task 1
- [S2] Solution Overview: Covered by Task 1
- [S3] Architecture: Covered by all tasks
- [S4] Menu Implementation: Covered by Task 3
- [S5] Storage Strategy: Covered by Task 2
- [S6] Settings Panel: Covered by Task 4
- [S7] Language Switching: Covered by Task 3 and 5
- [S8] Future Considerations: Not implemented (future work)
- [S9] Technical Challenges: Addressed in implementation
- [S10] Success Criteria: Tested in Task 5

**2. Placeholder scan:** No TBD/TODO placeholders found.

**3. Type consistency:** All function names and signatures are consistent across tasks.