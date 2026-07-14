bl_info = {
    "name": "Quick Language Switcher",
    "author": "Hysz",
    "version": (1, 0, 0),
    "blender": (5, 0, 0),
    "location": "Topbar Menu  |  Shift+Ctrl+L",
    "description": "Quickly switch Blender interface language with bilingual pack support",
    "category": "Interface",
}

_submodules = ["ui.menu", "ui.preferences", "core.keymap"]

try:
    import bpy
    _has_blender_ui = hasattr(bpy.types, "Menu")
except Exception:
    _has_blender_ui = False

if _has_blender_ui and "bpy" in locals():
    import importlib
    import sys
    for mod_name in _submodules:
        qualified_name = f"{__package__}.{mod_name}"
        if qualified_name in sys.modules:
            importlib.reload(sys.modules[qualified_name])

if _has_blender_ui:
    from .ui import menu
    from .ui import preferences
    from .core import keymap
else:
    menu = None
    preferences = None
    keymap = None

def register():
    if not _has_blender_ui:
        raise RuntimeError("Quick Language Switcher can only be registered inside Blender")
    preferences.register()
    menu.register()
    keymap.register()

def unregister():
    if not _has_blender_ui:
        return
    preferences.cleanup_bilingual_pack_on_unregister()
    keymap.unregister()
    menu.unregister()
    preferences.unregister()
