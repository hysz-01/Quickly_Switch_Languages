"""
Integration test for Quick Language Switcher addon.
Run this script in Blender's Python console or Text Editor to test the addon.
"""
import bpy
import pytest
import sys
from pathlib import Path

if not hasattr(bpy, "data"):
    pytest.skip("Blender integration tests must run inside Blender", allow_module_level=True)

addon_root = Path(__file__).resolve().parents[1]
addons_root = addon_root.parent
if str(addons_root) not in sys.path:
    sys.path.insert(0, str(addons_root))

print("=" * 60)
print("Quick Language Switcher - Integration Test")
print("=" * 60)

results = []

def test(name, func):
    """Run a test and record the result."""
    try:
        func()
        print(f"✓ {name}")
        results.append((name, True))
    except Exception as e:
        print(f"✗ {name}: {e}")
        results.append((name, False))

# Test 1: Check addon is registered
def test_addon_registered():
    addon_name = "Quickly_switch_languages"
    assert addon_name in bpy.context.preferences.addons, f"Addon '{addon_name}' not found in registered addons"

test("Addon is registered", test_addon_registered)

# Test 2: Check preferences exist
def test_preferences_exist():
    prefs = bpy.context.preferences.addons["Quickly_switch_languages"].preferences
    assert hasattr(prefs, 'favorites'), "Missing favorites property"
    assert hasattr(prefs, 'favorites_index'), "Missing favorites_index property"

test("Preferences exist with correct properties", test_preferences_exist)

# Test 3: Check favorites are loaded
def test_favorites_loaded():
    prefs = bpy.context.preferences.addons["Quickly_switch_languages"].preferences
    assert len(prefs.favorites) > 0, "No favorites loaded"

test("Favorites are loaded from JSON", test_favorites_loaded)

# Test 4: Check menu operator exists
def test_switch_operator_exists():
    assert hasattr(bpy.ops.language_switcher, 'switch_language'), "switch_language operator not found"

test("Switch language operator exists", test_switch_operator_exists)

# Test 5: Check current language can be read
def test_current_language_readable():
    current = bpy.context.preferences.view.language
    assert current is not None, "Cannot read current language"
    print(f"    Current language: {current}")

test("Current language is readable", test_current_language_readable)

# Test 6: Check menu is registered in editor menus
def test_menu_in_topbar():
    assert hasattr(bpy.types, 'TOPBAR_MT_editor_menus'), "TOPBAR_MT_editor_menus not found"
    from Quickly_switch_languages.ui.menu import draw_menu
    assert draw_menu is not None, "draw_menu function not found"
    assert draw_menu in bpy.types.TOPBAR_MT_editor_menus._dyn_ui_initialize(), "draw_menu not appended to editor menus"

test("Menu is registered in editor menus", test_menu_in_topbar)

# Test 7: Test JSON file exists and is valid
def test_json_file_valid():
    import json
    json_path = addon_root / "data" / "languages.json"
    assert json_path.exists(), "data/languages.json not found"
    with json_path.open('r', encoding='utf-8') as f:
        data = json.load(f)
    assert "favorites" in data, "Missing 'favorites' key in JSON"
    assert len(data["favorites"]) > 0, "No favorites in JSON"

test("languages.json exists and is valid", test_json_file_valid)

# Test 8: Test LanguageManager
def test_language_manager():
    from Quickly_switch_languages.core.language_manager import LanguageManager
    manager = LanguageManager(str(addon_root / "data" / "languages.json"))
    favorites = manager.get_favorites()
    assert len(favorites) > 0, "LanguageManager returned no favorites"

test("LanguageManager works correctly", test_language_manager)

# Test 9: Check all classes are registered
def test_classes_registered():
    from Quickly_switch_languages.ui.menu import LANGUAGE_SWITCHER_MT_menu, LANGUAGE_SWITCHER_OT_switch_language
    from Quickly_switch_languages.ui.preferences import QuickLanguageSwitcherPreferences, LanguageItem
    assert LANGUAGE_SWITCHER_MT_menu is not None
    assert LANGUAGE_SWITCHER_OT_switch_language is not None
    assert QuickLanguageSwitcherPreferences is not None
    assert LanguageItem is not None

test("All addon classes are registered", test_classes_registered)

# Summary
print("=" * 60)
passed = sum(1 for _, ok in results if ok)
failed = sum(1 for _, ok in results if not ok)
print(f"Results: {passed} passed, {failed} failed, {len(results)} total")
print("=" * 60)

if failed == 0:
    print("All tests PASSED!")
else:
    print("Some tests FAILED!")
    for name, ok in results:
        if not ok:
            print(f"  - {name}")
