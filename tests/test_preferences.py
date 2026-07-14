"""
Test script for preferences.py changes
This script can be run in Blender's Python interpreter to test the functionality
"""
import bpy
import pytest
import sys
import os
from pathlib import Path

if not hasattr(bpy, "app"):
    pytest.skip("Blender preferences tests must run inside Blender", allow_module_level=True)

# Add the addons path to sys.path so package-relative imports work.
addon_root = Path(__file__).resolve().parents[1]
addons_root = addon_root.parent
if str(addons_root) not in sys.path:
    sys.path.insert(0, str(addons_root))

# Test 1: Check if bpy.app.translations.available_translations exists
print("Test 1: Checking bpy.app.translations.available_translations...")
try:
    available = bpy.app.translations.available_translations
    if available:
        print(f"  ✓ Found {len(available)} available languages")
        print(f"  Sample languages: {list(available.items())[:5]}")
    else:
        print("  ✗ No languages found")
except AttributeError as e:
    print(f"  ✗ Attribute not found: {e}")
except Exception as e:
    print(f"  ✗ Error: {e}")

# Test 2: Import preferences module
print("\nTest 2: Importing preferences module...")
try:
    from Quickly_switch_languages.ui.preferences import LANGUAGE_SWITCHER_OT_show_add_language_menu
    print("  ✓ Successfully imported LANGUAGE_SWITCHER_OT_show_add_language_menu")
    
    # Test the get_available_languages method
    operator = LANGUAGE_SWITCHER_OT_show_add_language_menu()
    languages = operator.get_available_languages()
    print(f"  ✓ get_available_languages() returned {len(languages)} languages")
    
except ImportError as e:
    print(f"  ✗ Import error: {e}")
except Exception as e:
    print(f"  ✗ Error: {e}")

# Test 3: Check if the new operator is properly defined
print("\nTest 3: Checking operator definition...")
try:
    from Quickly_switch_languages.ui.preferences import LANGUAGE_SWITCHER_OT_show_add_language_menu
    operator = LANGUAGE_SWITCHER_OT_show_add_language_menu
    
    # Check required attributes
    assert hasattr(operator, 'bl_idname'), "Missing bl_idname"
    assert hasattr(operator, 'bl_label'), "Missing bl_label"
    assert hasattr(operator, 'execute'), "Missing execute method"
    assert hasattr(operator, 'draw'), "Missing draw method"
    assert hasattr(operator, 'get_available_languages'), "Missing get_available_languages method"
    
    print("  ✓ Operator definition is correct")
    
except AssertionError as e:
    print(f"  ✗ Assertion failed: {e}")
except Exception as e:
    print(f"  ✗ Error: {e}")

print("\nAll tests completed!")


def test_enabled_bilingual_presets_includes_new_regions():
    from Quickly_switch_languages.ui.preferences import _enabled_bilingual_presets

    class Prefs:
        bilingual_scope_node_shader_geometry = True
        bilingual_scope_material_texture = False
        bilingual_scope_animation_rigging = False
        bilingual_scope_viewport_navigation = False
        bilingual_scope_modeling_mesh = True
        bilingual_scope_sculpt_paint = True
        bilingual_scope_compositor_vfx = False
        bilingual_scope_render_lighting = True

    assert _enabled_bilingual_presets(Prefs()) == [
        "node_shader_geometry",
        "modeling_mesh",
        "sculpt_paint",
        "render_lighting",
    ]
