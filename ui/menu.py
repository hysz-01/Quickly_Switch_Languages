import bpy
from bpy.types import Menu, Operator
from pathlib import Path

from ..core.language_manager import LanguageManager
from ..core.localization import normalize_language, tr
from ..core.paths import data_path, user_data_path
from ..core.addon import addon_package_name


ADDON_PACKAGE = addon_package_name(__package__)

_favorites_cache: tuple[float, list[dict]] | None = None


def _cached_favorites(json_path: Path) -> list[dict]:
    global _favorites_cache
    mtime = json_path.stat().st_mtime if json_path.exists() else 0
    if _favorites_cache is not None and _favorites_cache[0] == mtime:
        return _favorites_cache[1]
    manager = LanguageManager(str(json_path), str(data_path("languages.json")))
    favorites = manager.get_favorites()
    _favorites_cache = (mtime, favorites)
    return favorites


def _favorites_from_preferences(context) -> list[dict]:
    try:
        prefs = context.preferences.addons[ADDON_PACKAGE].preferences
    except (AttributeError, KeyError):
        return []
    return [
        {"code": lang.code, "name": lang.name}
        for lang in prefs.favorites
        if lang.code and lang.name
    ]


def _menu_favorites(context) -> list[dict]:
    favorites = _favorites_from_preferences(context)
    if favorites:
        return favorites
    return _cached_favorites(user_data_path("languages.json"))


def _switch_language(context, operator, language_code: str, language_name: str):
    target = normalize_language(language_code)
    try:
        context.preferences.view.language = target
    except (TypeError, ValueError) as exc:
        operator.report({'ERROR'}, tr("Language is not available in Blender yet: {code}. Install it or restart Blender to refresh the language list.").format(code=target))
        return {'CANCELLED'}
    operator.report({'INFO'}, tr("Switched UI language to {name}").format(name=language_name))
    return {'FINISHED'}


class LANGUAGE_SWITCHER_MT_menu(Menu):
    bl_label = "Switch Language"
    bl_idname = "LANGUAGE_SWITCHER_MT_menu"

    def draw(self, context):
        layout = self.layout
        favorites = _menu_favorites(context)

        if not favorites:
            layout.operator("language_switcher.add_default_languages", text=tr("Add Default Languages"))
            return

        for lang in favorites:
            op = layout.operator(
                "language_switcher.switch_language",
                text=f"{lang['name']} ({lang['code']})",
                icon='WORLD'
            )
            op.language_code = lang['code']
            op.language_name = lang['name']

        layout.separator()
        layout.operator("language_switcher.open_preferences", text=tr("Manage Languages..."), icon='PREFERENCES')


class LANGUAGE_SWITCHER_OT_switch_language(Operator):
    """Switch Blender interface language"""
    bl_idname = "language_switcher.switch_language"
    bl_label = "Switch Language"
    bl_options = {'REGISTER', 'UNDO'}

    language_code: bpy.props.StringProperty()
    language_name: bpy.props.StringProperty()

    def execute(self, context):
        return _switch_language(context, self, self.language_code, self.language_name)


class LANGUAGE_SWITCHER_OT_open_preferences(Operator):
    """Open addon preferences"""
    bl_idname = "language_switcher.open_preferences"
    bl_label = "Open Preferences"

    def execute(self, context):
        bpy.ops.preferences.addon_show(module=ADDON_PACKAGE)
        return {'FINISHED'}


class LANGUAGE_SWITCHER_OT_add_default_languages(Operator):
    """Add default language list"""
    bl_idname = "language_switcher.add_default_languages"
    bl_label = "Add Default Languages"

    def execute(self, context):
        json_path = user_data_path("languages.json")
        default_languages = [
            {"code": "en_US", "name": "English"},
            {"code": "zh_HANS", "name": "简体中文"},
            {"code": "ja_JP", "name": "日本語"},
        ]

        manager = LanguageManager(str(json_path), str(data_path("languages.json")))
        manager.update_favorites(default_languages)
        global _favorites_cache
        _favorites_cache = None

        self.report({'INFO'}, tr("Default languages added to the top-bar switcher"))
        return {'FINISHED'}


class LANGUAGE_SWITCHER_OT_popup_language_switcher(Operator):
    """Quick language switcher popup at mouse cursor"""
    bl_idname = "language_switcher.popup_language_switcher"
    bl_label = "Switch Language"
    bl_options = {'REGISTER', 'UNDO'}

    language_code: bpy.props.StringProperty()
    language_name: bpy.props.StringProperty()

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self, width=280)

    def draw(self, context):
        layout = self.layout
        favorites = _menu_favorites(context)

        layout.label(text=tr("Switch Language"), icon='WORLD')
        layout.separator()

        if not favorites:
            layout.operator("language_switcher.add_default_languages", text=tr("Add Default Languages"))
            return

        col = layout.column(align=True)
        for lang in favorites:
            props = col.operator(
                "language_switcher.popup_language_switcher",
                text=f"{lang['name']} ({lang['code']})",
                icon='WORLD',
            )
            props.language_code = lang['code']
            props.language_name = lang['name']

        layout.separator()
        layout.operator("language_switcher.open_preferences", text=tr("Manage Languages..."), icon='PREFERENCES')

    def execute(self, context):
        if self.language_code:
            return _switch_language(context, self, self.language_code, self.language_name)
        return {'FINISHED'}


def draw_menu(self, context):
    """Draw function for top menu bar"""
    layout = self.layout
    layout.separator()
    layout.menu(LANGUAGE_SWITCHER_MT_menu.bl_idname, icon='WORLD')


# Registration
classes = (
    LANGUAGE_SWITCHER_MT_menu,
    LANGUAGE_SWITCHER_OT_switch_language,
    LANGUAGE_SWITCHER_OT_open_preferences,
    LANGUAGE_SWITCHER_OT_add_default_languages,
    LANGUAGE_SWITCHER_OT_popup_language_switcher,
)


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    bpy.types.TOPBAR_MT_editor_menus.append(draw_menu)


def unregister():
    from bpy.utils import unregister_class
    bpy.types.TOPBAR_MT_editor_menus.remove(draw_menu)
    for cls in reversed(classes):
        unregister_class(cls)
