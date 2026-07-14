from pathlib import Path
import sys
import types


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))


class _DummyBase:
    pass


def _install_fake_bpy():
    bpy = types.ModuleType("bpy")
    bpy.types = types.SimpleNamespace(
        AddonPreferences=_DummyBase,
        Operator=_DummyBase,
        UIList=_DummyBase,
        PropertyGroup=_DummyBase,
    )
    bpy.props = types.SimpleNamespace(
        BoolProperty=lambda **kwargs: None,
        CollectionProperty=lambda **kwargs: None,
        StringProperty=lambda **kwargs: None,
        IntProperty=lambda **kwargs: None,
        EnumProperty=lambda **kwargs: None,
    )
    bpy.utils = types.SimpleNamespace(resource_path=lambda _kind: "")
    bpy.app = types.SimpleNamespace(version_string="5.0.1")
    sys.modules["bpy"] = bpy
    sys.modules["bpy.props"] = bpy.props
    sys.modules["bpy.types"] = bpy.types


def _load_preferences():
    _install_fake_bpy()
    sys.modules.pop("Quickly_switch_languages.ui.preferences", None)
    ui_package = sys.modules.get("Quickly_switch_languages.ui")
    if ui_package is not None and hasattr(ui_package, "preferences"):
        delattr(ui_package, "preferences")
    from Quickly_switch_languages.ui import preferences
    return preferences


def test_scope_summary_counts_selected_regions_and_custom_keywords():
    preferences = _load_preferences()

    class Prefs:
        enable_experimental_scope = True
        bilingual_scope_node_shader_geometry = True
        bilingual_scope_material_texture = False
        bilingual_scope_animation_rigging = False
        bilingual_scope_viewport_navigation = False
        bilingual_scope_modeling_mesh = True
        bilingual_scope_sculpt_paint = False
        bilingual_scope_compositor_vfx = False
        bilingual_scope_render_lighting = False
        bilingual_custom_keywords = "Bake, Custom Term"

    assert preferences._scope_summary(Prefs()) == "Selected regions: 2 | Custom keywords: 2"


def test_scope_summary_reports_disabled_when_experimental_scope_is_off():
    preferences = _load_preferences()

    class Prefs:
        enable_experimental_scope = False
        bilingual_scope_node_shader_geometry = True
        bilingual_scope_material_texture = False
        bilingual_scope_animation_rigging = False
        bilingual_scope_viewport_navigation = False
        bilingual_scope_modeling_mesh = False
        bilingual_scope_sculpt_paint = False
        bilingual_scope_compositor_vfx = False
        bilingual_scope_render_lighting = False
        bilingual_custom_keywords = ""

    assert preferences._scope_summary(Prefs()) == "Experimental scope: disabled"


def test_manifest_summary_reports_installed_version(tmp_path):
    preferences = _load_preferences()
    manifest = tmp_path / "bilingual_manifest.json"
    manifest.write_text('{"scope_blender_version":"5.0.1","scope_keyword_count":538}', encoding="utf-8")

    assert preferences._manifest_summary(manifest) == "Installed manifest: Blender 5.0.1, 538 keywords"


def test_manifest_summary_handles_broken_manifest(tmp_path):
    preferences = _load_preferences()
    manifest = tmp_path / "bilingual_manifest.json"
    manifest.write_text('{not valid json', encoding="utf-8")

    assert preferences._manifest_summary(manifest) == "Installed manifest: unreadable"


def test_installed_bilingual_language_codes_reads_user_manifest(tmp_path):
    preferences = _load_preferences()
    manifest = tmp_path / "bilingual_manifest.json"
    manifest.write_text('{"installed_language_codes":["en_de"]}', encoding="utf-8")
    preferences.user_data_path = lambda filename: manifest

    assert "en_de" in preferences._installed_bilingual_language_codes()


def test_section_icon_matches_open_state():
    preferences = _load_preferences()

    assert preferences._section_icon(True) == "TRIA_DOWN"
    assert preferences._section_icon(False) == "TRIA_RIGHT"


def test_install_scope_settings_falls_back_to_default_when_experimental_disabled():
    preferences = _load_preferences()

    class Prefs:
        enable_experimental_scope = False
        bilingual_scope_node_shader_geometry = True
        bilingual_scope_material_texture = False
        bilingual_scope_animation_rigging = False
        bilingual_scope_viewport_navigation = False
        bilingual_scope_modeling_mesh = True
        bilingual_scope_sculpt_paint = False
        bilingual_scope_compositor_vfx = False
        bilingual_scope_render_lighting = False
        bilingual_custom_keywords = "Node, Custom"

    scope_keywords, scope_presets = preferences._install_scope_settings(Prefs(), preferences.bpy)

    assert scope_keywords is None
    assert scope_presets == []


def test_install_scope_settings_uses_presets_when_experimental_enabled():
    preferences = _load_preferences()

    class Prefs:
        enable_experimental_scope = True
        bilingual_scope_node_shader_geometry = True
        bilingual_scope_material_texture = False
        bilingual_scope_animation_rigging = False
        bilingual_scope_viewport_navigation = False
        bilingual_scope_modeling_mesh = True
        bilingual_scope_sculpt_paint = False
        bilingual_scope_compositor_vfx = False
        bilingual_scope_render_lighting = False
        bilingual_custom_keywords = "Custom"

    scope_keywords, scope_presets = preferences._install_scope_settings(Prefs(), preferences.bpy)

    assert "node_shader_geometry" in scope_presets
    assert "modeling_mesh" in scope_presets
    assert "Custom" in scope_keywords


def test_bilingual_pair_requires_exactly_one_english_language():
    preferences = _load_preferences()

    assert preferences._bilingual_pair_settings("zh_HANS", "en_US") == ("zh_HANS", "en_US")
    assert preferences._bilingual_pair_settings("en_US", "ja_JP") == ("en_US", "ja_JP")

    for language1, language2 in (("zh_HANS", "ja_JP"), ("en_US", "en_US")):
        try:
            preferences._bilingual_pair_settings(language1, language2)
        except ValueError:
            pass
        else:
            raise AssertionError("Expected non English/custom pair validation to fail")


class _FakeFavorites:
    def __init__(self):
        self._items = [types.SimpleNamespace(code="en_US", name="English")]

    def __bool__(self):
        return bool(self._items)

    def __len__(self):
        return len(self._items)

    def __iter__(self):
        return iter(self._items)

    def __getitem__(self, index):
        return self._items[index]

    def remove(self, index):
        self._items.pop(index)

    def clear(self):
        self._items.clear()

    def add(self):
        item = types.SimpleNamespace(code="", name="")
        self._items.append(item)
        return item


class _FakeLayout:
    def __init__(self, calls=None):
        self.calls = calls if calls is not None else []

    def box(self):
        return _FakeLayout(self.calls)

    def row(self, align=False):
        self.calls.append(("row", align))
        return _FakeLayout(self.calls)

    def column(self, align=False):
        self.calls.append(("column", align))
        return _FakeLayout(self.calls)

    def prop(self, data, property_name, **kwargs):
        self.calls.append(("prop", property_name, kwargs))

    def label(self, text="", **kwargs):
        self.calls.append(("label", text, kwargs))

    def operator(self, operator_id, **kwargs):
        self.calls.append(("operator", operator_id, kwargs))
        return _FakeOperatorProps(kwargs)

    def separator(self):
        self.calls.append(("separator",))

    def template_list(self, *args, **kwargs):
        self.calls.append(("template_list", args, kwargs))


class _FakeOperatorProps:
    def __init__(self, kwargs):
        object.__setattr__(self, "_kwargs", kwargs)

    def __setattr__(self, name, value):
        self._kwargs[name] = value


def _draw_basic_preferences(preferences):
    prefs = preferences.QuickLanguageSwitcherPreferences()
    prefs.layout = _FakeLayout()
    prefs.favorites = _FakeFavorites()
    prefs.favorites_index = 0
    prefs.show_basic_language_switching = True
    prefs.show_advanced_bilingual = False
    prefs.show_experimental_scope = False
    prefs.enable_experimental_scope = False
    prefs.bilingual_scope_node_shader_geometry = True
    prefs.bilingual_scope_material_texture = False
    prefs.bilingual_scope_animation_rigging = False
    prefs.bilingual_scope_viewport_navigation = False
    prefs.bilingual_scope_modeling_mesh = False
    prefs.bilingual_scope_sculpt_paint = False
    prefs.bilingual_scope_compositor_vfx = False
    prefs.bilingual_scope_render_lighting = False
    prefs.bilingual_custom_keywords = ""
    prefs.draw(types.SimpleNamespace())
    return prefs.layout.calls


def test_basic_preferences_do_not_show_save_after_switch_control():
    preferences = _load_preferences()

    calls = _draw_basic_preferences(preferences)

    assert ("prop", "save_after_switch", {}) not in calls
    assert not any(call[0] == "label" and "Save after switch" in call[1] for call in calls)


def test_add_language_button_uses_right_side_icon_button():
    preferences = _load_preferences()

    calls = _draw_basic_preferences(preferences)
    add_buttons = [
        call for call in calls
        if call[0] == "operator" and call[1] == "language_switcher.show_add_language_menu"
    ]

    assert len(add_buttons) == 1
    assert add_buttons[0][2]["icon"] == "ADD"
    assert add_buttons[0][2]["text"] == ""
    assert not any(call[0] == "label" and call[1] == "Add from available languages:" for call in calls)


def test_experimental_section_draws_enable_checkbox_when_expanded():
    preferences = _load_preferences()
    preferences.tr = lambda text: f"T:{text}"
    prefs = preferences.QuickLanguageSwitcherPreferences()
    prefs.layout = _FakeLayout()
    prefs.favorites = _FakeFavorites()
    prefs.favorites_index = 0
    prefs.show_basic_language_switching = False
    prefs.show_advanced_bilingual = False
    prefs.show_experimental_scope = True
    prefs.enable_experimental_scope = False
    prefs.bilingual_scope_node_shader_geometry = True
    prefs.bilingual_scope_material_texture = False
    prefs.bilingual_scope_animation_rigging = False
    prefs.bilingual_scope_viewport_navigation = False
    prefs.bilingual_scope_modeling_mesh = False
    prefs.bilingual_scope_sculpt_paint = False
    prefs.bilingual_scope_compositor_vfx = False
    prefs.bilingual_scope_render_lighting = False
    prefs.bilingual_custom_keywords = ""

    prefs.draw(types.SimpleNamespace())

    expected_dynamic_labels = {
        "enable_experimental_scope": "T:Enable Experimental Region Scope",
        "bilingual_scope_node_shader_geometry": "T:Node / Shader / Geometry Nodes",
        "bilingual_scope_material_texture": "T:Material / Texture",
        "bilingual_scope_animation_rigging": "T:Animation / Rigging",
        "bilingual_scope_viewport_navigation": "T:Viewport / Navigation",
        "bilingual_scope_modeling_mesh": "T:Modeling / Mesh",
        "bilingual_scope_sculpt_paint": "T:Sculpt / Paint",
        "bilingual_scope_compositor_vfx": "T:Compositor / VFX",
        "bilingual_scope_render_lighting": "T:Render / Lighting",
        "bilingual_custom_keywords": "T:Custom Keywords",
    }
    props = {call[1]: call[2] for call in prefs.layout.calls if call[0] == "prop"}
    for property_name, label in expected_dynamic_labels.items():
        assert props[property_name]["text"] == label


def test_advanced_section_draws_bilingual_language_pair_fields_when_expanded():
    preferences = _load_preferences()
    prefs = preferences.QuickLanguageSwitcherPreferences()
    prefs.layout = _FakeLayout()
    prefs.favorites = _FakeFavorites()
    prefs.favorites_index = 0
    prefs.show_basic_language_switching = False
    prefs.show_advanced_bilingual = True
    prefs.show_experimental_scope = False
    prefs.enable_experimental_scope = False
    prefs.bilingual_language_1 = "zh_HANS"
    prefs.bilingual_language_2 = "en_US"
    prefs.bilingual_scope_node_shader_geometry = True
    prefs.bilingual_scope_material_texture = False
    prefs.bilingual_scope_animation_rigging = False
    prefs.bilingual_scope_viewport_navigation = False
    prefs.bilingual_scope_modeling_mesh = False
    prefs.bilingual_scope_sculpt_paint = False
    prefs.bilingual_scope_compositor_vfx = False
    prefs.bilingual_scope_render_lighting = False
    prefs.bilingual_custom_keywords = ""

    prefs.draw(types.SimpleNamespace())

    language_buttons = [
        call for call in prefs.layout.calls
        if call[0] == "operator" and call[1] == "language_switcher.open_bilingual_language_menu"
    ]

    assert len(language_buttons) == 2
    assert language_buttons[0][2]["text"] == "简体中文 (zh_HANS)"
    assert language_buttons[0][2]["target_property"] == "bilingual_language_1"
    assert language_buttons[1][2]["text"] == "English (en_US)"
    assert language_buttons[1][2]["target_property"] == "bilingual_language_2"
    assert not any(call[0] == "prop" and call[1] in {"bilingual_language_1", "bilingual_language_2"} for call in prefs.layout.calls)


def test_advanced_section_warns_generated_packs_are_removed_on_disable():
    preferences = _load_preferences()
    preferences.tr = lambda text: text
    prefs = preferences.QuickLanguageSwitcherPreferences()
    prefs.layout = _FakeLayout()
    prefs.favorites = _FakeFavorites()
    prefs.favorites_index = 0
    prefs.show_basic_language_switching = False
    prefs.show_advanced_bilingual = True
    prefs.show_experimental_scope = False
    prefs.enable_experimental_scope = False
    prefs.bilingual_language_1 = "zh_HANS"
    prefs.bilingual_language_2 = "en_US"
    prefs.bilingual_scope_node_shader_geometry = True
    prefs.bilingual_scope_material_texture = False
    prefs.bilingual_scope_animation_rigging = False
    prefs.bilingual_scope_viewport_navigation = False
    prefs.bilingual_scope_modeling_mesh = False
    prefs.bilingual_scope_sculpt_paint = False
    prefs.bilingual_scope_compositor_vfx = False
    prefs.bilingual_scope_render_lighting = False
    prefs.bilingual_custom_keywords = ""

    prefs.draw(types.SimpleNamespace())

    assert any(
        call[0] == "label" and call[1] == "Generated bilingual packs are removed automatically when this add-on is disabled."
        for call in prefs.layout.calls
    )


def test_emergency_cleanup_description_matches_marker_based_cleanup():
    preferences = _load_preferences()

    assert preferences.LANGUAGE_SWITCHER_OT_emergency_cleanup.bl_description == (
        "Remove this add-on's marked bilingual language entries and generated files"
    )


def test_select_bilingual_language_updates_target_property():
    preferences = _load_preferences()
    prefs = types.SimpleNamespace(bilingual_language_1="zh_HANS", bilingual_language_2="en_US")
    context = types.SimpleNamespace(
        preferences=types.SimpleNamespace(addons={preferences.ADDON_PACKAGE: types.SimpleNamespace(preferences=prefs)})
    )
    operator = preferences.LANGUAGE_SWITCHER_OT_set_bilingual_language()
    operator.target_property = "bilingual_language_1"
    operator.language_code = "ja_JP"
    operator.language_name = "日本語"

    result = operator.execute(context)

    assert result == {'FINISHED'}
    assert prefs.bilingual_language_1 == "ja_JP"
    assert prefs.bilingual_language_2 == "en_US"


def test_bilingual_language_menu_excludes_generated_languages(tmp_path):
    preferences = _load_preferences()
    manifest = tmp_path / "bilingual_manifest.json"
    manifest.write_text('{"installed_language_codes":["en_ja"]}', encoding="utf-8")
    preferences.user_data_path = lambda _filename: manifest
    preferences.bpy.app.translations = types.SimpleNamespace(available_translations={
        "en_US": "English",
        "zh_HANS": "简体中文",
        "ja_JP": "日本語",
        "zh_en": "Chinese + English",
        "en_zh": "English + Chinese",
        "en_ja": "English + Japanese",
    })

    languages = preferences._available_base_languages()

    assert languages == {
        "en_US": "English",
        "zh_HANS": "简体中文",
        "ja_JP": "日本語",
    }


def test_install_bilingual_pack_restores_current_ui_language(monkeypatch):
    preferences = _load_preferences()

    class Prefs:
        bilingual_language_1 = "en_US"
        bilingual_language_2 = "ja_JP"
        enable_experimental_scope = False

    view = types.SimpleNamespace(language="zh_HANS")
    context = types.SimpleNamespace(
        preferences=types.SimpleNamespace(
            view=view,
            addons={preferences.ADDON_PACKAGE: types.SimpleNamespace(preferences=Prefs())},
        )
    )

    def fake_install_bilingual_pair(*_args, **_kwargs):
        view.language = "en_ja"
        return {}

    monkeypatch.setattr(preferences, "_get_locale_root", lambda: Path("/locale"))
    monkeypatch.setattr(preferences, "addon_root", lambda: Path("/addon"))
    monkeypatch.setattr(preferences.bpy.app, "version_string", "5.1.2")
    monkeypatch.setattr(preferences, "install_bilingual_pair", fake_install_bilingual_pair)

    operator = preferences.LANGUAGE_SWITCHER_OT_install_bilingual_pack()
    operator.report = lambda _level, _message: None

    result = operator.execute(context)

    assert result == {'FINISHED'}
    assert view.language == "zh_HANS"


def test_cleanup_bilingual_pack_uninstalls_from_manifest(monkeypatch, tmp_path):
    preferences = _load_preferences()
    manifest = tmp_path / "bilingual_manifest.json"
    manifest.write_text('{"installed_files":[]}', encoding="utf-8")
    calls = []

    monkeypatch.setattr(preferences, "_get_locale_root", lambda: tmp_path / "locale")
    monkeypatch.setattr(preferences, "user_data_path", lambda _filename: manifest)
    monkeypatch.setattr(
        preferences,
        "uninstall_from_manifest",
        lambda locale_root, languages_path, manifest_path: calls.append((locale_root, languages_path, manifest_path)),
    )

    preferences.cleanup_bilingual_pack()

    assert calls == [(tmp_path / "locale", tmp_path / "locale" / "languages", manifest)]
    assert not manifest.exists()


def test_cleanup_bilingual_pack_uses_emergency_cleanup_without_manifest(monkeypatch, tmp_path):
    preferences = _load_preferences()
    manifest = tmp_path / "missing.json"
    calls = []

    monkeypatch.setattr(preferences, "_get_locale_root", lambda: tmp_path / "locale")
    monkeypatch.setattr(preferences, "user_data_path", lambda _filename: manifest)
    monkeypatch.setattr(
        preferences,
        "emergency_cleanup",
        lambda locale_root, manifest_path: calls.append((locale_root, manifest_path)),
    )

    preferences.cleanup_bilingual_pack()

    assert calls == [(tmp_path / "locale", manifest)]


def test_cleanup_bilingual_pack_on_unregister_swallows_cleanup_errors(monkeypatch):
    preferences = _load_preferences()

    def fail_cleanup():
        raise PermissionError("locked locale")

    monkeypatch.setattr(preferences, "cleanup_bilingual_pack", fail_cleanup)

    preferences.cleanup_bilingual_pack_on_unregister()


def test_cleanup_bilingual_pack_on_unregister_falls_back_to_marker_cleanup(monkeypatch, tmp_path):
    preferences = _load_preferences()
    manifest = tmp_path / "bilingual_manifest.json"
    manifest.write_text("{broken", encoding="utf-8")
    calls = []

    def strict_cleanup():
        raise ValueError("broken manifest")

    monkeypatch.setattr(preferences, "cleanup_bilingual_pack", strict_cleanup)
    monkeypatch.setattr(preferences, "_get_locale_root", lambda: tmp_path / "locale")
    monkeypatch.setattr(preferences, "user_data_path", lambda _filename: manifest)
    monkeypatch.setattr(
        preferences,
        "emergency_cleanup",
        lambda locale_root, manifest_path: calls.append((locale_root, manifest_path)),
    )

    preferences.cleanup_bilingual_pack_on_unregister()

    assert calls == [(tmp_path / "locale", manifest)]


def test_cleanup_bilingual_pack_switches_from_generated_language_before_uninstall(monkeypatch, tmp_path):
    preferences = _load_preferences()
    manifest = tmp_path / "bilingual_manifest.json"
    manifest.write_text('{"installed_language_codes":["en_ja"],"installed_files":[]}', encoding="utf-8")
    view = types.SimpleNamespace(language="en_ja")
    preferences.bpy.context = types.SimpleNamespace(preferences=types.SimpleNamespace(view=view))

    monkeypatch.setattr(preferences, "_get_locale_root", lambda: tmp_path / "locale")
    monkeypatch.setattr(preferences, "user_data_path", lambda _filename: manifest)
    monkeypatch.setattr(preferences, "uninstall_from_manifest", lambda *_args: None)

    preferences.cleanup_bilingual_pack()

    assert view.language == "en_US"


def test_emergency_cleanup_operator_switches_from_generated_language(monkeypatch, tmp_path):
    preferences = _load_preferences()
    manifest = tmp_path / "bilingual_manifest.json"
    manifest.write_text('{"installed_language_codes":["en_ja"],"installed_files":[]}', encoding="utf-8")
    view = types.SimpleNamespace(language="en_ja")
    preferences.bpy.context = types.SimpleNamespace(preferences=types.SimpleNamespace(view=view))
    calls = []

    monkeypatch.setattr(preferences, "_get_locale_root", lambda: tmp_path / "locale")
    monkeypatch.setattr(preferences, "user_data_path", lambda _filename: manifest)
    monkeypatch.setattr(preferences, "emergency_cleanup", lambda *_args: calls.append("cleanup"))

    operator = preferences.LANGUAGE_SWITCHER_OT_emergency_cleanup()
    operator.report = lambda _level, _message: None

    result = operator.execute(types.SimpleNamespace())

    assert result == {'FINISHED'}
    assert calls == ["cleanup"]
    assert view.language == "en_US"


def test_switch_from_installed_bilingual_language_ignores_broken_manifest(tmp_path):
    preferences = _load_preferences()
    manifest = tmp_path / "bilingual_manifest.json"
    manifest.write_text("{broken", encoding="utf-8")

    preferences._switch_from_installed_bilingual_language(manifest)


def test_emergency_cleanup_operator_runs_cleanup_with_broken_manifest(monkeypatch, tmp_path):
    preferences = _load_preferences()
    manifest = tmp_path / "bilingual_manifest.json"
    manifest.write_text("{broken", encoding="utf-8")
    calls = []

    monkeypatch.setattr(preferences, "_get_locale_root", lambda: tmp_path / "locale")
    monkeypatch.setattr(preferences, "user_data_path", lambda _filename: manifest)
    monkeypatch.setattr(preferences, "emergency_cleanup", lambda *_args: calls.append("cleanup"))

    operator = preferences.LANGUAGE_SWITCHER_OT_emergency_cleanup()
    operator.report = lambda _level, _message: None

    result = operator.execute(types.SimpleNamespace())

    assert result == {'FINISHED'}
    assert calls == ["cleanup"]


def test_emergency_cleanup_operator_switches_from_marker_language_without_manifest(monkeypatch, tmp_path):
    preferences = _load_preferences()
    locale_root = tmp_path / "locale"
    locale_root.mkdir()
    (locale_root / "languages").write_text(
        "1:English (US):en_US:100%\n"
        "# BEGIN Quick Language Switcher bilingual languages\n"
        "9821:English + Japanese:en_ja:100%\n"
        "# END Quick Language Switcher bilingual languages\n",
        encoding="utf-8",
    )
    manifest = tmp_path / "missing.json"
    view = types.SimpleNamespace(language="en_ja")
    preferences.bpy.context = types.SimpleNamespace(preferences=types.SimpleNamespace(view=view))
    calls = []

    monkeypatch.setattr(preferences, "_get_locale_root", lambda: locale_root)
    monkeypatch.setattr(preferences, "user_data_path", lambda _filename: manifest)
    monkeypatch.setattr(preferences, "emergency_cleanup", lambda *_args: calls.append("cleanup"))

    operator = preferences.LANGUAGE_SWITCHER_OT_emergency_cleanup()
    operator.report = lambda _level, _message: None

    result = operator.execute(types.SimpleNamespace())

    assert result == {'FINISHED'}
    assert calls == ["cleanup"]
    assert view.language == "en_US"


def test_emergency_cleanup_operator_switches_from_marker_language_with_broken_manifest(monkeypatch, tmp_path):
    preferences = _load_preferences()
    locale_root = tmp_path / "locale"
    locale_root.mkdir()
    (locale_root / "languages").write_text(
        "1:English (US):en_US:100%\n"
        "# BEGIN Quick Language Switcher bilingual languages\n"
        "9821:English + Japanese:en_ja:100%\n"
        "# END Quick Language Switcher bilingual languages\n",
        encoding="utf-8",
    )
    manifest = tmp_path / "manifest.json"
    manifest.write_text("{broken", encoding="utf-8")
    view = types.SimpleNamespace(language="en_ja")
    preferences.bpy.context = types.SimpleNamespace(preferences=types.SimpleNamespace(view=view))
    calls = []

    monkeypatch.setattr(preferences, "_get_locale_root", lambda: locale_root)
    monkeypatch.setattr(preferences, "user_data_path", lambda _filename: manifest)
    monkeypatch.setattr(preferences, "emergency_cleanup", lambda *_args: calls.append("cleanup"))

    operator = preferences.LANGUAGE_SWITCHER_OT_emergency_cleanup()
    operator.report = lambda _level, _message: None

    result = operator.execute(types.SimpleNamespace())

    assert result == {'FINISHED'}
    assert calls == ["cleanup"]
    assert view.language == "en_US"


def test_manifest_helpers_ignore_non_dict_manifest(tmp_path):
    preferences = _load_preferences()
    manifest = tmp_path / "bilingual_manifest.json"
    manifest.write_text("[]", encoding="utf-8")
    preferences.user_data_path = lambda _filename: manifest

    assert preferences._installed_bilingual_language_codes() == {"zh_en", "en_zh"}
    assert preferences._manifest_summary(manifest) == "Installed manifest: unreadable"
    preferences._switch_from_installed_bilingual_language(manifest)


def test_addon_unregister_runs_bilingual_cleanup(monkeypatch):
    _install_fake_bpy()
    sys.modules.pop("Quickly_switch_languages", None)
    import Quickly_switch_languages as addon
    calls = []

    monkeypatch.setattr(addon, "_has_blender_ui", True)
    monkeypatch.setattr(addon, "keymap", types.SimpleNamespace(unregister=lambda: calls.append("keymap")))
    monkeypatch.setattr(addon, "menu", types.SimpleNamespace(unregister=lambda: calls.append("menu")))
    monkeypatch.setattr(addon, "preferences", types.SimpleNamespace(
        cleanup_bilingual_pack_on_unregister=lambda: calls.append("cleanup_best_effort"),
        unregister=lambda: calls.append("preferences"),
    ))

    addon.unregister()

    assert calls == ["cleanup_best_effort", "keymap", "menu", "preferences"]


def test_preferences_sync_rebuilds_collection_from_json_when_different(monkeypatch):
    preferences = _load_preferences()
    prefs = preferences.QuickLanguageSwitcherPreferences()
    prefs.favorites = _FakeFavorites()
    prefs.favorites_index = 0

    class FakeManager:
        def __init__(self, _path, _default_path=None):
            pass

        def get_favorites(self):
            return [
                {"code": "en_US", "name": "English"},
                {"code": "zh_en", "name": "简体中文 + English"},
            ]

    monkeypatch.setattr(preferences, "LanguageManager", FakeManager)

    prefs._sync_from_json()

    assert [(item.code, item.name) for item in prefs.favorites] == [
        ("en_US", "English"),
        ("zh_en", "简体中文 + English"),
    ]
