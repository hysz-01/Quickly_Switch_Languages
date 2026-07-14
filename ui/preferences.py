import json

import bpy
from bpy.props import BoolProperty, CollectionProperty, StringProperty
from bpy.types import AddonPreferences, Operator, UIList
from ..core.language_manager import LanguageManager
from ..core.localization import tr
from ..core.paths import addon_root, data_path, user_data_path
from ..core.addon import addon_package_name
from ..bilingual.baker import bilingual_language_code
from ..bilingual.installer import install_bilingual_pair, uninstall_from_manifest, emergency_cleanup, _marked_language_codes
from ..bilingual.scope import get_scope_keywords
from pathlib import Path


ADDON_PACKAGE = addon_package_name(__package__)


def _get_locale_root():
    for resource_type in ('LOCAL', 'SYSTEM'):
        locale_root = Path(bpy.utils.resource_path(resource_type)) / "datafiles" / "locale"
        if locale_root.exists():
            return locale_root
    return Path(bpy.utils.resource_path('LOCAL')) / "datafiles" / "locale"


def _enabled_bilingual_presets(prefs):
    enabled_presets = []
    if prefs.bilingual_scope_node_shader_geometry:
        enabled_presets.append("node_shader_geometry")
    if prefs.bilingual_scope_material_texture:
        enabled_presets.append("material_texture")
    if prefs.bilingual_scope_animation_rigging:
        enabled_presets.append("animation_rigging")
    if prefs.bilingual_scope_viewport_navigation:
        enabled_presets.append("viewport_navigation")
    if prefs.bilingual_scope_modeling_mesh:
        enabled_presets.append("modeling_mesh")
    if prefs.bilingual_scope_sculpt_paint:
        enabled_presets.append("sculpt_paint")
    if prefs.bilingual_scope_compositor_vfx:
        enabled_presets.append("compositor_vfx")
    if prefs.bilingual_scope_render_lighting:
        enabled_presets.append("render_lighting")
    return enabled_presets


def _custom_keyword_count(custom_keywords: str) -> int:
    return len([item for item in custom_keywords.split(",") if item.strip()])


def _scope_summary(prefs) -> str:
    if not getattr(prefs, "enable_experimental_scope", False):
        return tr("Experimental scope: disabled")
    return tr("Selected regions: {count} | Custom keywords: {keywords}").format(
        count=len(_enabled_bilingual_presets(prefs)),
        keywords=_custom_keyword_count(prefs.bilingual_custom_keywords),
    )


def _install_scope_settings(prefs, bpy_module):
    if not prefs.enable_experimental_scope:
        return None, []
    enabled_presets = _enabled_bilingual_presets(prefs)
    return (
        get_scope_keywords(
            enabled_presets,
            prefs.bilingual_custom_keywords,
            bpy_module=bpy_module,
            blender_version=bpy_module.app.version_string,
        ),
        enabled_presets,
    )


def _bilingual_pair_settings(language1_code: str, language2_code: str) -> tuple[str, str]:
    language1 = "zh_HANS" if language1_code == "zh_CN" else language1_code
    language2 = "zh_HANS" if language2_code == "zh_CN" else language2_code
    english_count = len([code for code in (language1, language2) if code == "en_US"])
    if english_count != 1:
        raise ValueError("Choose one English language and one non-English language.")
    return language1, language2


def _language_name(language_code: str) -> str:
    return {
        "en_US": "English",
        "zh_CN": "简体中文",
        "zh_HANS": "简体中文",
        "ja_JP": "日本語",
    }.get(language_code, language_code)


def _available_languages():
    try:
        items = bpy.types.PreferencesView.bl_rna.properties["language"].enum_items
        languages = {item.identifier: item.name for item in items if item.identifier != "DEFAULT"}
        if languages:
            return languages
    except (AttributeError, TypeError, KeyError):
        pass

    try:
        available = bpy.app.translations.available_translations
        if available:
            return available
    except (AttributeError, TypeError):
        pass

    return {
        "en_US": "English",
        "zh_CN": "简体中文",
        "zh_HANS": "简体中文",
        "ja_JP": "日本語",
        "ko_KR": "한국어",
        "de_DE": "Deutsch",
        "fr_FR": "Français",
        "es_ES": "Español",
        "pt_BR": "Português (Brasil)",
        "ru_RU": "Русский",
    }


def _installed_bilingual_language_codes() -> set[str]:
    codes = {"zh_en", "en_zh"}
    manifest_path = user_data_path("bilingual_manifest.json")
    if not manifest_path.exists():
        return codes
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return codes
    if not isinstance(manifest, dict):
        return codes
    installed_codes = manifest.get("installed_language_codes", [])
    if isinstance(installed_codes, list):
        codes.update(code for code in installed_codes if isinstance(code, str))
    return codes


def _available_base_languages():
    excluded = _installed_bilingual_language_codes()
    return {
        code: name
        for code, name in _available_languages().items()
        if code not in excluded
    }


def _manifest_summary(path: Path) -> str:
    if not path.exists():
        return tr("Installed manifest: not found")
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return tr("Installed manifest: unreadable")
    if not isinstance(manifest, dict):
        return tr("Installed manifest: unreadable")
    version = manifest.get("scope_blender_version") or manifest.get("blender_version", "unknown")
    count = manifest.get("scope_keyword_count", 0)
    return tr("Installed manifest: Blender {version}, {count} keywords").format(version=version, count=count)


def cleanup_bilingual_pack() -> None:
    locale_root = _get_locale_root()
    languages_path = locale_root / "languages"
    manifest_path = user_data_path("bilingual_manifest.json")
    if manifest_path.exists():
        _switch_from_installed_bilingual_language(manifest_path)
        uninstall_from_manifest(locale_root, languages_path, manifest_path)
        manifest_path.unlink()
    else:
        emergency_cleanup(locale_root, manifest_path)


def _switch_from_installed_bilingual_language(manifest_path: Path) -> None:
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return
    if not isinstance(manifest, dict):
        return
    codes = manifest.get("installed_language_codes", [])
    if not isinstance(codes, list):
        return
    installed_codes = {code for code in codes if isinstance(code, str)}
    if not installed_codes:
        return
    try:
        view = bpy.context.preferences.view
    except AttributeError:
        return
    if view.language in installed_codes:
        view.language = "en_US"


def _switch_from_marker_bilingual_language(locale_root: Path) -> None:
    languages_path = locale_root / "languages"
    if not languages_path.exists():
        return
    try:
        marked_codes = _marked_language_codes(languages_path.read_text(encoding="utf-8"))
    except OSError:
        return
    if not marked_codes:
        return
    try:
        view = bpy.context.preferences.view
    except AttributeError:
        return
    if view.language in marked_codes:
        view.language = "en_US"


def _switch_from_bilingual_language_for_emergency_cleanup(locale_root: Path, manifest_path: Path) -> None:
    if manifest_path.exists():
        _switch_from_installed_bilingual_language(manifest_path)
    try:
        view = bpy.context.preferences.view
    except AttributeError:
        return
    if view.language != "en_US":
        _switch_from_marker_bilingual_language(locale_root)


def cleanup_bilingual_pack_on_unregister() -> None:
    try:
        cleanup_bilingual_pack()
    except Exception:
        try:
            emergency_cleanup(_get_locale_root(), user_data_path("bilingual_manifest.json"))
        except Exception:
            pass


def _section_icon(is_open: bool) -> str:
    return 'TRIA_DOWN' if is_open else 'TRIA_RIGHT'

class LANGUAGE_SWITCHER_UL_favorites(UIList):
    bl_idname = "LANGUAGE_SWITCHER_UL_favorites"
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            if item:
                layout.label(text=f"{item.name} ({item.code})", icon='WORLD')
            else:
                layout.label(text=tr("Unknown language"), icon='ERROR')
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            if item:
                layout.label(text="", icon='WORLD')
            else:
                layout.label(text="", icon='ERROR')

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
        prefs = context.preferences.addons[ADDON_PACKAGE].preferences
        
        # Validate input
        if not self.language_code or not self.language_name:
            self.report({'ERROR'}, tr("Choose a language before adding it."))
            return {'CANCELLED'}
        
        # Check if already exists
        for lang in prefs.favorites:
            if lang.code == self.language_code:
                self.report({'WARNING'}, tr("Language is already in favorites: {code}").format(code=self.language_code))
                return {'CANCELLED'}
        
        # Add new language
        new_lang = prefs.favorites.add()
        new_lang.code = self.language_code
        new_lang.name = self.language_name
        
        # Save to JSON
        self._save_to_json(context)
        
        self.report({'INFO'}, tr("Added language: {name}").format(name=self.language_name))
        return {'FINISHED'}
    
    def _save_to_json(self, context):
        manager = LanguageManager(str(user_data_path("languages.json")), str(data_path("languages.json")))
        
        prefs = context.preferences.addons[ADDON_PACKAGE].preferences
        favorites = [{"code": lang.code, "name": lang.name} for lang in prefs.favorites]
        manager.update_favorites(favorites)

class LANGUAGE_SWITCHER_OT_show_add_language_menu(Operator):
    """Show a popup menu to add a language to favorites"""
    bl_idname = "language_switcher.show_add_language_menu"
    bl_label = "Add Language"
    bl_description = tr("Add a language to the top-bar switcher")
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        return context.window_manager.invoke_popup(self)
    
    def draw(self, context):
        layout = self.layout
        layout.label(text=tr("Select a language to add:"))
        layout.separator()
        
        # Get available languages from Blender API
        available_languages = self.get_available_languages()
        
        # Get current favorites to filter them out
        prefs = context.preferences.addons[ADDON_PACKAGE].preferences
        favorite_codes = {lang.code for lang in prefs.favorites}
        
        # Show available languages that aren't already favorites
        col = layout.column(align=True)
        found_any = False
        for code, name in sorted(available_languages.items()):
            if code not in favorite_codes:
                # Use props method to set operator properties
                props = col.operator("language_switcher.add_language", text=f"{name} ({code})")
                props.language_code = code
                props.language_name = name
                found_any = True
        
        if not found_any:
            layout.label(text=tr("All available languages are already in favorites"), icon='INFO')
    
    def get_available_languages(self):
        """Get all available languages from Blender's API"""
        return _available_languages()

class LANGUAGE_SWITCHER_OT_open_bilingual_language_menu(Operator):
    """Open a popup menu to choose a bilingual pack language"""
    bl_idname = "language_switcher.open_bilingual_language_menu"
    bl_label = "Select Bilingual Language"
    bl_options = {'REGISTER', 'UNDO'}

    target_property: bpy.props.StringProperty()

    def execute(self, context):
        return context.window_manager.invoke_popup(self)

    def draw(self, context):
        layout = self.layout
        label = tr("Language 1") if self.target_property == "bilingual_language_1" else tr("Language 2")
        layout.label(text=label)
        layout.separator()

        col = layout.column(align=True)
        for code, name in sorted(_available_base_languages().items()):
            props = col.operator("language_switcher.set_bilingual_language", text=f"{name} ({code})")
            props.target_property = self.target_property
            props.language_code = code
            props.language_name = name


class LANGUAGE_SWITCHER_OT_set_bilingual_language(Operator):
    """Set one side of the generated bilingual pack language pair"""
    bl_idname = "language_switcher.set_bilingual_language"
    bl_label = "Set Bilingual Language"
    bl_options = {'REGISTER', 'UNDO'}

    target_property: bpy.props.StringProperty()
    language_code: bpy.props.StringProperty()
    language_name: bpy.props.StringProperty()

    def execute(self, context):
        prefs = context.preferences.addons[ADDON_PACKAGE].preferences
        setattr(prefs, self.target_property, self.language_code)
        return {'FINISHED'}

class LANGUAGE_SWITCHER_OT_remove_language(Operator):
    """Remove a language from favorites"""
    bl_idname = "language_switcher.remove_language"
    bl_label = "Remove Language"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        prefs = context.preferences.addons[ADDON_PACKAGE].preferences
        
        if prefs.favorites_index >= len(prefs.favorites):
            self.report({'WARNING'}, tr("Select a language before removing."))
            return {'CANCELLED'}

        lang = prefs.favorites[prefs.favorites_index]
        removed_name = lang.name
        prefs.favorites.remove(prefs.favorites_index)
        
        # Adjust index
        if prefs.favorites_index >= len(prefs.favorites):
            prefs.favorites_index = max(0, len(prefs.favorites) - 1)
        
        # Save to JSON
        self._save_to_json(context)
        
        self.report({'INFO'}, tr("Removed language: {name}").format(name=removed_name))
        return {'FINISHED'}
    
    def _save_to_json(self, context):
        manager = LanguageManager(str(user_data_path("languages.json")), str(data_path("languages.json")))
        
        prefs = context.preferences.addons[ADDON_PACKAGE].preferences
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
        prefs = context.preferences.addons[ADDON_PACKAGE].preferences
        
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
        manager = LanguageManager(str(user_data_path("languages.json")), str(data_path("languages.json")))
        
        prefs = context.preferences.addons[ADDON_PACKAGE].preferences
        favorites = [{"code": lang.code, "name": lang.name} for lang in prefs.favorites]
        manager.update_favorites(favorites)

class LANGUAGE_SWITCHER_OT_install_bilingual_pack(Operator):
    """Bake and install bilingual Blender language packs"""
    bl_idname = "language_switcher.install_bilingual_pack"
    bl_label = "Install Bilingual Language Pack"
    bl_options = {'REGISTER'}

    def execute(self, context):
        root = addon_root()
        locale_root = _get_locale_root()
        prefs = context.preferences.addons[ADDON_PACKAGE].preferences
        current_language = context.preferences.view.language
        scope_keywords, enabled_presets = _install_scope_settings(prefs, bpy)
        try:
            language1_code, language2_code = _bilingual_pair_settings(prefs.bilingual_language_1, prefs.bilingual_language_2)
        except ValueError as exc:
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}
        try:
            output_code = bilingual_language_code(language1_code, language2_code)
            install_bilingual_pair(
                locale_root,
                bpy.app.version_string,
                root,
                language1_code=language1_code,
                language1_name=_language_name(language1_code),
                language2_code=language2_code,
                language2_name=_language_name(language2_code),
                scope_keywords=scope_keywords,
                scope_presets=enabled_presets,
                manifest_path=user_data_path("bilingual_manifest.json"),
            )
            context.preferences.view.language = current_language
        except FileNotFoundError as exc:
            self.report({'ERROR'}, tr("Source language .mo file not found: {path}. The '{lang}' language may not be installed in Blender, or its translation files were removed. Try reinstalling Blender or use the 'Emergency Cleanup' button below, then restart Blender.").format(path=exc, lang=_language_name(language1_code if language1_code != "en_US" else language2_code)))
            return {'CANCELLED'}
        except Exception as exc:
            self.report({'ERROR'}, tr("Could not install bilingual packs: {error}. Check Blender locale folder permissions and try again.").format(error=exc))
            return {'CANCELLED'}
        self.report({'INFO'}, tr("Installed bilingual packs for Blender {version}. Restart Blender, then choose '{code}' in Preferences > Interface > Language.").format(version=bpy.app.version_string, code=output_code))
        return {'FINISHED'}

class LANGUAGE_SWITCHER_OT_uninstall_bilingual_pack(Operator):
    """Uninstall bilingual Blender language packs installed by this add-on"""
    bl_idname = "language_switcher.uninstall_bilingual_pack"
    bl_label = "Uninstall Bilingual Language Pack"
    bl_options = {'REGISTER'}

    def execute(self, context):
        try:
            cleanup_bilingual_pack()
        except Exception as exc:
            self.report({'ERROR'}, tr("Could not uninstall bilingual packs: {error}").format(error=exc))
            return {'CANCELLED'}
        self.report({'INFO'}, tr("Uninstalled bilingual packs. Restart Blender to refresh the language list."))
        return {'FINISHED'}

class LANGUAGE_SWITCHER_OT_emergency_cleanup(Operator):
    """Emergency cleanup: restore locale files to pre-addon state without relying on manifest"""
    bl_idname = "language_switcher.emergency_cleanup"
    bl_label = "Emergency Cleanup"
    bl_description = "Remove this add-on's marked bilingual language entries and generated files"
    bl_options = {'REGISTER'}

    def execute(self, context):
        locale_root = _get_locale_root()
        manifest_path = user_data_path("bilingual_manifest.json")
        try:
            _switch_from_bilingual_language_for_emergency_cleanup(locale_root, manifest_path)
            emergency_cleanup(locale_root, manifest_path)
        except Exception as exc:
            self.report({'ERROR'}, tr("Could not run emergency cleanup: {error}").format(error=exc))
            return {'CANCELLED'}
        self.report({'INFO'}, tr("Emergency cleanup complete. Restart Blender to refresh the language list."))
        return {'FINISHED'}

class QuickLanguageSwitcherPreferences(AddonPreferences):
    bl_idname = ADDON_PACKAGE
    
    show_basic_language_switching: BoolProperty(
        name="Show Basic Language Switching",
        default=True,
    )
    show_advanced_bilingual: BoolProperty(
        name="Show Advanced Bilingual Packs",
        default=False,
    )
    show_experimental_scope: BoolProperty(
        name="Show Experimental Region Scope",
        default=False,
    )
    bilingual_language_1: StringProperty(
        name=tr("Language 1"),
        description="First language in the generated bilingual pack",
        default="zh_HANS",
    )
    bilingual_language_2: StringProperty(
        name=tr("Language 2"),
        description="Second language in the generated bilingual pack",
        default="en_US",
    )
    enable_experimental_scope: BoolProperty(
        name=tr("Enable Experimental Region Scope"),
        description="Use selected regions and custom keywords for the next bilingual pack install",
        default=False,
    )
    
    favorites: CollectionProperty(type=LanguageItem)
    favorites_index: bpy.props.IntProperty()
    bilingual_scope_node_shader_geometry: BoolProperty(
        name=tr("Node / Shader / Geometry Nodes"),
        description="Bilingualize node, shader, and geometry-node related terms",
        default=True,
    )
    bilingual_scope_material_texture: BoolProperty(
        name=tr("Material / Texture"),
        description="Bilingualize material and texture related terms",
        default=False,
    )
    bilingual_scope_animation_rigging: BoolProperty(
        name=tr("Animation / Rigging"),
        description="Bilingualize animation and rigging related terms",
        default=False,
    )
    bilingual_scope_viewport_navigation: BoolProperty(
        name=tr("Viewport / Navigation"),
        description="Bilingualize viewport and navigation related terms",
        default=False,
    )
    bilingual_scope_modeling_mesh: BoolProperty(
        name=tr("Modeling / Mesh"),
        description="Bilingualize common modeling and mesh terms",
        default=False,
    )
    bilingual_scope_sculpt_paint: BoolProperty(
        name=tr("Sculpt / Paint"),
        description="Bilingualize sculpting and painting terms",
        default=False,
    )
    bilingual_scope_compositor_vfx: BoolProperty(
        name=tr("Compositor / VFX"),
        description="Bilingualize compositor and VFX terms",
        default=False,
    )
    bilingual_scope_render_lighting: BoolProperty(
        name=tr("Render / Lighting"),
        description="Bilingualize render and lighting terms",
        default=False,
    )
    bilingual_custom_keywords: StringProperty(
        name=tr("Custom Keywords"),
        description="Comma-separated English keywords to bilingualize during bake",
        default="",
    )
    
    def draw(self, context):
        layout = self.layout
        
        # Clean up empty items from favorites
        self._cleanup_empty_favorites()
        
        # Always sync from JSON to ensure consistency across sessions
        self._sync_from_json()
        
        box = layout.box()
        row = box.row(align=True)
        row.prop(self, "show_basic_language_switching", icon=_section_icon(self.show_basic_language_switching), icon_only=True, emboss=False)
        row.label(text=tr("Basic Language Switching"), icon='PREFERENCES')
        if self.show_basic_language_switching:
            box.label(text=tr("Manage languages shown in the top-bar switcher."), icon='INFO')

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
            col.operator("language_switcher.show_add_language_menu", icon='ADD', text="")
            col.operator("language_switcher.remove_language", icon='REMOVE', text="")
            
            col.separator()
            col.operator("language_switcher.move_language", icon='TRIA_UP', text="").direction = 'UP'
            col.operator("language_switcher.move_language", icon='TRIA_DOWN', text="").direction = 'DOWN'
            
            box.separator()
            try:
                available_languages = bpy.app.translations.available_translations
                if available_languages:
                    favorite_codes = {lang.code for lang in self.favorites}
                    available_count = len([code for code in available_languages if code not in favorite_codes])
                    box.label(text=tr("{count} languages available").format(count=available_count), icon='INFO')
            except (AttributeError, TypeError):
                box.label(text=tr("Click button above to add languages"), icon='INFO')
        else:
            box.label(text=tr("Favorites: {count}").format(count=len(self.favorites)), icon='INFO')

        box = layout.box()
        row = box.row(align=True)
        row.prop(self, "show_advanced_bilingual", icon=_section_icon(self.show_advanced_bilingual), icon_only=True, emboss=False)
        row.label(text=tr("Advanced: Bilingual Language Packs"), icon='WORLD')
        box.label(text=_manifest_summary(user_data_path("bilingual_manifest.json")), icon='FILE_TICK')
        if self.show_advanced_bilingual:
            box.label(text=tr("Installs separate zh_en/en_zh languages into Blender's locale folder."), icon='INFO')
            box.label(text=tr("Backs up the languages file. Restart Blender after install or uninstall."), icon='INFO')
            box.label(text=tr("Generated bilingual packs are removed automatically when this add-on is disabled."), icon='ERROR')
            row = box.row(align=True)
            row.label(text=tr("Language 1"))
            props = row.operator("language_switcher.open_bilingual_language_menu", icon='WORLD', text=f"{_language_name(self.bilingual_language_1)} ({self.bilingual_language_1})")
            props.target_property = "bilingual_language_1"
            row = box.row(align=True)
            row.label(text=tr("Language 2"))
            props = row.operator("language_switcher.open_bilingual_language_menu", icon='WORLD', text=f"{_language_name(self.bilingual_language_2)} ({self.bilingual_language_2})")
            props.target_property = "bilingual_language_2"
            row = box.row(align=True)
            row.operator("language_switcher.install_bilingual_pack", icon='IMPORT', text=tr("Install / Update Bilingual Packs"))
            row.operator("language_switcher.uninstall_bilingual_pack", icon='TRASH', text=tr("Uninstall Bilingual Packs"))

        box = layout.box()
        row = box.row(align=True)
        row.prop(self, "show_experimental_scope", icon=_section_icon(self.show_experimental_scope), icon_only=True, emboss=False)
        row.label(text=tr("Experimental: Region Scope"), icon='FILTER')
        box.label(text=_scope_summary(self), icon='INFO')
        if self.show_experimental_scope:
            box.prop(self, "enable_experimental_scope", text=tr("Enable Experimental Region Scope"))
            box.label(text=tr("When disabled, bilingual pack installation uses the default full scope."), icon='INFO')
            box.label(text=tr("Affects the next bilingual pack install; it does not change the current language immediately."), icon='INFO')
            box.label(text=tr("Uses exact English labels. Same-name UI labels may still be included."), icon='ERROR')
            col = box.column(align=True)
            col.prop(self, "bilingual_scope_node_shader_geometry", text=tr("Node / Shader / Geometry Nodes"))
            col.prop(self, "bilingual_scope_material_texture", text=tr("Material / Texture"))
            col.prop(self, "bilingual_scope_animation_rigging", text=tr("Animation / Rigging"))
            col.prop(self, "bilingual_scope_viewport_navigation", text=tr("Viewport / Navigation"))
            col.prop(self, "bilingual_scope_modeling_mesh", text=tr("Modeling / Mesh"))
            col.prop(self, "bilingual_scope_sculpt_paint", text=tr("Sculpt / Paint"))
            col.prop(self, "bilingual_scope_compositor_vfx", text=tr("Compositor / VFX"))
            col.prop(self, "bilingual_scope_render_lighting", text=tr("Render / Lighting"))
            box.prop(self, "bilingual_custom_keywords", text=tr("Custom Keywords"))
            box.separator()
            box.operator("language_switcher.emergency_cleanup", icon='ERROR', text=tr("Emergency Cleanup: Remove All Bilingual Files"))
    
    def _cleanup_empty_favorites(self):
        """Remove any empty items from favorites collection"""
        # Iterate backwards to avoid index issues when removing items
        for i in range(len(self.favorites) - 1, -1, -1):
            lang = self.favorites[i]
            if not lang.code or not lang.name:
                self.favorites.remove(i)
        self.favorites_index = max(0, min(self.favorites_index, max(0, len(self.favorites) - 1)))
    
    def _load_from_json(self):
        json_path = user_data_path("languages.json")
        
        if json_path.exists():
            manager = LanguageManager(str(json_path), str(data_path("languages.json")))
            favorites = manager.get_favorites()
            self.favorites.clear()
            for lang in favorites:
                new_lang = self.favorites.add()
                new_lang.code = lang["code"]
                new_lang.name = lang["name"]
    
    def _sync_from_json(self):
        """Ensure favorites match the user JSON file state."""
        json_path = user_data_path("languages.json")
        manager = LanguageManager(str(json_path), str(data_path("languages.json")))
        favorites = manager.get_favorites()
        current = [{"code": lang.code, "name": lang.name} for lang in self.favorites if lang.code and lang.name]
        if current != favorites:
            self._load_from_json()

# Registration
classes = (
    LANGUAGE_SWITCHER_UL_favorites,
    LanguageItem,
    LANGUAGE_SWITCHER_OT_add_language,
    LANGUAGE_SWITCHER_OT_remove_language,
    LANGUAGE_SWITCHER_OT_move_language,
    LANGUAGE_SWITCHER_OT_show_add_language_menu,
    LANGUAGE_SWITCHER_OT_open_bilingual_language_menu,
    LANGUAGE_SWITCHER_OT_set_bilingual_language,
    LANGUAGE_SWITCHER_OT_install_bilingual_pack,
    LANGUAGE_SWITCHER_OT_uninstall_bilingual_pack,
    LANGUAGE_SWITCHER_OT_emergency_cleanup,
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
