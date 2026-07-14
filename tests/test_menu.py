from pathlib import Path
import importlib.util
import json
import sys
import types


class _DummyBase:
    pass


class _FakeTopbarLayout:
    def __init__(self, calls):
        self.calls = calls

    def separator(self):
        self.calls.append(("separator",))

    def menu(self, menu_id, **kwargs):
        self.calls.append(("menu", menu_id, kwargs))


class _FakeMenuLayout:
    def __init__(self):
        self.operators = []

    def operator(self, operator_id, **kwargs):
        props = types.SimpleNamespace()
        self.operators.append((operator_id, kwargs, props))
        return props

    def separator(self):
        pass


class _FakeTopbarMenuType:
    def __init__(self):
        self.appended = []
        self.removed = []

    def append(self, callback):
        self.appended.append(callback)

    def remove(self, callback):
        self.removed.append(callback)


def _load_menu_module():
    package_name = "Quickly_switch_languages"
    package = types.ModuleType(package_name)
    root = Path(__file__).resolve().parents[1]
    package.__path__ = [str(root)]
    sys.modules[package_name] = package

    bpy = types.ModuleType("bpy")
    bpy.types = types.SimpleNamespace(
        Menu=_DummyBase,
        Operator=_DummyBase,
        TOPBAR_MT_editor_menus=_FakeTopbarMenuType(),
    )
    bpy.props = types.SimpleNamespace(StringProperty=lambda **kwargs: None)
    bpy.utils = types.SimpleNamespace(
        register_class=lambda cls: None,
        unregister_class=lambda cls: None,
    )
    sys.modules["bpy"] = bpy
    sys.modules["bpy.types"] = bpy.types
    sys.modules["bpy.utils"] = bpy.utils

    ui_package = types.ModuleType(f"{package_name}.ui")
    ui_package.__path__ = [str(root / "ui")]
    sys.modules[f"{package_name}.ui"] = ui_package

    module_path = root / "ui" / "menu.py"
    spec = importlib.util.spec_from_file_location(f"{package_name}.ui.menu", module_path)
    menu = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = menu
    spec.loader.exec_module(menu)
    return menu, bpy


def test_open_preferences_shows_addon_preferences():
    menu, bpy = _load_menu_module()
    calls = []

    def addon_show(module):
        calls.append(module)
        return {'FINISHED'}

    bpy.ops = types.SimpleNamespace(
        preferences=types.SimpleNamespace(addon_show=addon_show)
    )
    context = types.SimpleNamespace()

    result = menu.LANGUAGE_SWITCHER_OT_open_preferences().execute(context)

    assert result == {'FINISHED'}
    assert calls == ["Quickly_switch_languages"]


def test_add_default_languages_uses_three_language_default():
    menu, _bpy = _load_menu_module()
    updated = []

    class FakeLanguageManager:
        def __init__(self, path, default_path=None):
            self.path = path
            self.default_path = default_path

        def update_favorites(self, favorites):
            updated.append(favorites)

    menu.LanguageManager = FakeLanguageManager
    menu.data_path = lambda filename: filename
    menu.user_data_path = lambda filename: f"user/{filename}"
    operator = menu.LANGUAGE_SWITCHER_OT_add_default_languages()
    operator.report = lambda _level, _message: None

    result = operator.execute(types.SimpleNamespace())

    assert result == {'FINISHED'}
    assert updated == [[
        {"code": "en_US", "name": "English"},
        {"code": "zh_HANS", "name": "简体中文"},
        {"code": "ja_JP", "name": "日本語"},
    ]]


def test_shipped_languages_json_uses_three_language_default():
    root = Path(__file__).resolve().parents[1]
    data = json.loads((root / "data" / "languages.json").read_text(encoding="utf-8"))

    assert data["favorites"] == [
        {"code": "en_US", "name": "English"},
        {"code": "zh_HANS", "name": "简体中文"},
        {"code": "ja_JP", "name": "日本語"},
    ]


def test_register_adds_menu_to_editor_menus():
    menu, bpy = _load_menu_module()

    menu.register()

    assert bpy.types.TOPBAR_MT_editor_menus.appended == [menu.draw_menu]


def test_unregister_removes_menu_from_editor_menus():
    menu, bpy = _load_menu_module()

    menu.unregister()

    assert bpy.types.TOPBAR_MT_editor_menus.removed == [menu.draw_menu]


def test_switch_language_normalizes_zh_CN_to_zh_HANS():
    menu, bpy = _load_menu_module()
    operator = menu.LANGUAGE_SWITCHER_OT_switch_language()
    operator.language_code = "zh_CN"
    operator.language_name = "简体中文"
    operator.report = lambda _level, _message: None

    context = types.SimpleNamespace(
        preferences=types.SimpleNamespace(view=types.SimpleNamespace(language=""))
    )
    result = operator.execute(context)
    assert result == {'FINISHED'}
    assert context.preferences.view.language == "zh_HANS"


def test_switch_language_passes_through_valid_code():
    menu, bpy = _load_menu_module()
    operator = menu.LANGUAGE_SWITCHER_OT_switch_language()
    operator.language_code = "ja_JP"
    operator.language_name = "日本語"
    operator.report = lambda _level, _message: None

    context = types.SimpleNamespace(
        preferences=types.SimpleNamespace(view=types.SimpleNamespace(language=""))
    )
    result = operator.execute(context)
    assert result == {'FINISHED'}
    assert context.preferences.view.language == "ja_JP"


def test_switch_language_reports_unavailable_language_code():
    menu, bpy = _load_menu_module()
    operator = menu.LANGUAGE_SWITCHER_OT_switch_language()
    operator.language_code = "zh_en"
    operator.language_name = "简体中文 + English"
    reports = []
    operator.report = lambda level, message: reports.append((level, message))

    class View:
        language = "en_US"

        def __setattr__(self, name, value):
            if name == "language" and value == "zh_en":
                raise TypeError("enum item not found")
            object.__setattr__(self, name, value)

    context = types.SimpleNamespace(preferences=types.SimpleNamespace(view=View()))

    result = operator.execute(context)

    assert result == {'CANCELLED'}
    assert context.preferences.view.language == "en_US"
    assert reports and reports[0][0] == {'ERROR'}


def test_menu_draw_uses_addon_preferences_favorites_before_json_cache():
    menu, _bpy = _load_menu_module()
    menu._favorites_cache = (0, [
        {"code": "en_US", "name": "English"},
        {"code": "zh_en", "name": "简体中文 + English"},
    ])

    favorites = [
        types.SimpleNamespace(code="en_US", name="English"),
        types.SimpleNamespace(code="zh_HANS", name="简体中文"),
        types.SimpleNamespace(code="ja_JP", name="日本語"),
    ]
    context = types.SimpleNamespace(
        preferences=types.SimpleNamespace(
            addons={menu.ADDON_PACKAGE: types.SimpleNamespace(preferences=types.SimpleNamespace(favorites=favorites))}
        )
    )
    instance = menu.LANGUAGE_SWITCHER_MT_menu()
    instance.layout = _FakeMenuLayout()

    instance.draw(context)

    codes = [props.language_code for operator_id, _kwargs, props in instance.layout.operators if operator_id == "language_switcher.switch_language"]
    assert codes == ["en_US", "zh_HANS", "ja_JP"]


def test_draw_menu_renders_without_region_alignment_filter():
    menu, _bpy = _load_menu_module()
    calls = []
    self = types.SimpleNamespace(layout=_FakeTopbarLayout(calls))
    context = types.SimpleNamespace(region=types.SimpleNamespace(alignment='RIGHT'))

    menu.draw_menu(self, context)

    assert ("separator",) in calls
    assert ("menu", "LANGUAGE_SWITCHER_MT_menu", {"icon": "WORLD"}) in calls
