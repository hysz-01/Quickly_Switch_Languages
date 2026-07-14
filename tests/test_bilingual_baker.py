from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
from Quickly_switch_languages.bilingual import scope as bilingual_scope
from Quickly_switch_languages.bilingual.baker import bake_bilingual_catalogs, bake_bilingual_pair_catalog, bilingual_language_code
from Quickly_switch_languages.bilingual.mo import MoCatalog


def test_bake_generates_chinese_first_and_english_first_catalogs():
    source = MoCatalog({
        "": "Content-Type: text/plain; charset=UTF-8\n",
        "File": "文件",
        "Save As": "另存为",
    })

    result = bake_bilingual_catalogs(source)

    assert result["zh_en"].entries[""] == source.entries[""]
    assert result["zh_en"].entries["File"] == "文件 (File)"
    assert result["en_zh"].entries["File"] == "File (文件)"


def test_bilingual_language_code_uses_short_codes_in_order():
    assert bilingual_language_code("zh_HANS", "en_US") == "zh_en"
    assert bilingual_language_code("en_US", "ja_JP") == "en_ja"


def test_bake_bilingual_pair_catalog_uses_selected_order():
    source = MoCatalog({
        "": "Content-Type: text/plain; charset=UTF-8\n",
        "File": "文件",
    })

    chinese_first = bake_bilingual_pair_catalog(source, english_first=False)
    english_first = bake_bilingual_pair_catalog(source, english_first=True)

    assert chinese_first.entries["File"] == "文件 (File)"
    assert english_first.entries["File"] == "File (文件)"


def test_bake_only_combines_matching_scope_keywords():
    source = MoCatalog({
        "Node": "节点",
        "Save": "保存",
    })

    result = bake_bilingual_catalogs(source, scope_keywords={"Node"})

    assert result["zh_en"].entries["Node"] == "节点 (Node)"
    assert result["zh_en"].entries["Save"] == "保存"


def test_bake_scope_matches_node_terms_exactly_without_sentence_bleed():
    source = MoCatalog({
        "Mix": "混合",
        "Noise Texture": "噪波纹理",
        "Input devices are disabled": "输入设备已禁用",
    })

    result = bake_bilingual_catalogs(source, scope_keywords={"Mix", "Noise Texture", "Input"})

    assert result["zh_en"].entries["Mix"] == "混合 (Mix)"
    assert result["zh_en"].entries["Noise Texture"] == "噪波纹理 (Noise Texture)"
    assert result["zh_en"].entries["Input devices are disabled"] == "输入设备已禁用"


def test_bake_uses_msgid_part_for_scoped_gettext_context_entries():
    source = MoCatalog({
        "NodeTree\x04Mix": "混合",
        "WindowManager\x04Shift": "Shift",
    })

    result = bake_bilingual_catalogs(source, scope_keywords={"Mix", "Shift"})

    assert result["zh_en"].entries["NodeTree\x04Mix"] == "混合 (Mix)"
    assert result["en_zh"].entries["NodeTree\x04Mix"] == "Mix (混合)"
    assert result["zh_en"].entries["WindowManager\x04Shift"] == "Shift"


def test_bake_scope_rejects_generic_terms_in_non_node_contexts():
    source = MoCatalog({
        "WindowManager\x04Input": "输入",
        "UI_Event_KeyMaps\x04Color": "颜色",
    })

    result = bake_bilingual_catalogs(source, scope_keywords={"Input", "Color"})

    assert result["zh_en"].entries["WindowManager\x04Input"] == "输入"
    assert result["zh_en"].entries["UI_Event_KeyMaps\x04Color"] == "颜色"


def test_bake_full_scope_rejects_high_risk_gettext_contexts():
    source = MoCatalog({
        "WindowManager\x04Input": "输入",
        "UI_Event_KeyMaps\x04Color": "颜色",
    })

    result = bake_bilingual_catalogs(source)

    assert result["zh_en"].entries["WindowManager\x04Input"] == "输入"
    assert result["zh_en"].entries["UI_Event_KeyMaps\x04Color"] == "颜色"


def test_bake_does_not_duplicate_positional_printf_placeholders():
    source = MoCatalog({
        "%1$s contains %2$d item(s)": "%1$s 包含 %2$d 个项目",
    })

    result = bake_bilingual_catalogs(source)

    assert result["zh_en"].entries["%1$s contains %2$d item(s)"] == "%1$s 包含 %2$d 个项目"


def test_get_scope_keywords_combines_presets_and_custom_keywords():
    keywords = bilingual_scope.get_scope_keywords(["node_shader_geometry"], "Bake, Custom Term")

    assert "Node" in keywords
    assert "Shader" in keywords
    assert "Bake" in keywords
    assert "Custom Term" in keywords


def test_collect_blender_node_keywords_reads_node_rna_names():
    class FakeRna:
        def __init__(self, name):
            self.name = name

    class FakeTypes:
        ShaderNodeMix = type("ShaderNodeMix", (), {"bl_rna": FakeRna("Mix")})
        GeometryNodeNoiseTexture = type("GeometryNodeNoiseTexture", (), {"bl_rna": FakeRna("Noise Texture")})
        ObjectModifier = type("ObjectModifier", (), {"bl_rna": FakeRna("Modifier")})

        @classmethod
        def __dir__(cls):
            return ["ShaderNodeMix", "GeometryNodeNoiseTexture", "ObjectModifier"]

    class FakeBpy:
        types = FakeTypes

    keywords = bilingual_scope.collect_blender_node_keywords(FakeBpy)

    assert keywords == {"Mix", "Noise Texture"}


def test_get_scope_keywords_includes_blender_node_names_for_node_preset():
    class FakeRna:
        def __init__(self, name):
            self.name = name

    class FakeNode:
        @classmethod
        def __subclasses__(cls):
            return [type("MixNode", (), {"bl_rna": FakeRna("Mix")})]

    class FakeTypes:
        ShaderNodeMix = type("ShaderNodeMix", (), {"bl_rna": FakeRna("Mix")})

        @classmethod
        def __dir__(cls):
            return ["ShaderNodeMix"]

    class FakeBpy:
        types = FakeTypes

    keywords = bilingual_scope.get_scope_keywords(["node_shader_geometry"], bpy_module=FakeBpy)

    assert "Mix" in keywords


def test_get_scope_keywords_accepts_version_for_runtime_collection():
    class FakeRna:
        def __init__(self, name):
            self.name = name

    class FakeTypes:
        ShaderNodeMix = type("ShaderNodeMix", (), {"bl_rna": FakeRna("Mix")})

        @classmethod
        def __dir__(cls):
            return ["ShaderNodeMix"]

    class FakeBpy:
        types = FakeTypes

    keywords = bilingual_scope.get_scope_keywords(
        ["node_shader_geometry"],
        bpy_module=FakeBpy,
        blender_version="5.0.1",
    )

    assert "Mix" in keywords


def test_common_region_presets_include_expected_terms():
    presets = bilingual_scope.SCOPE_PRESETS

    assert "modeling_mesh" in presets
    assert presets["sculpt_paint"]["label"] == "Sculpt / Paint"
    assert "Bevel" in presets["modeling_mesh"]["keywords"]
    assert "Brush" in presets["sculpt_paint"]["keywords"]
    assert "Color Balance" in presets["compositor_vfx"]["keywords"]
    assert "Cycles" in presets["render_lighting"]["keywords"]


def test_get_scope_keywords_combines_multiple_common_regions():
    keywords = bilingual_scope.get_scope_keywords(["modeling_mesh", "render_lighting"])

    assert "Bevel" in keywords
    assert "Extrude" in keywords
    assert "Render" in keywords
    assert "Light" in keywords


def test_bake_preserves_empty_identical_and_placeholder_mismatch_entries():
    source = MoCatalog({
        "": "Content-Type: text/plain; charset=UTF-8\n",
        "Untranslated": "",
        "Same": "Same",
        "Value: %s": "值：%d",
        "Name: %s": "名称：%s",
    })

    result = bake_bilingual_catalogs(source)

    assert result["zh_en"].entries["Untranslated"] == ""
    assert result["zh_en"].entries["Same"] == "Same"
    assert result["zh_en"].entries["Value: %s"] == "值：%d"
    assert result["zh_en"].entries["Name: %s"] == "名称：%s"


def test_bake_does_not_duplicate_printf_placeholders():
    source = MoCatalog({
        "%d file(s) saved": "已保存 %d 个文件",
        "Scale: %.2f": "缩放：%.2f",
    })

    result = bake_bilingual_catalogs(source)

    assert result["zh_en"].entries["%d file(s) saved"] == "已保存 %d 个文件"
    assert result["en_zh"].entries["Scale: %.2f"] == "缩放：%.2f"


def test_bake_does_not_duplicate_fmt_replacement_fields():
    source = MoCatalog({
        "Compiling shaders ({} remaining)": "正在编译着色器 (剩余 {})",
        "Add-on '{name}' not found": "未找到 '{name}' 插件",
    })

    result = bake_bilingual_catalogs(source)

    assert result["zh_en"].entries["Compiling shaders ({} remaining)"] == "正在编译着色器 (剩余 {})"
    assert result["en_zh"].entries["Add-on '{name}' not found"] == "未找到 '{name}' 插件"


def test_bake_preserves_gettext_context_entries():
    source = MoCatalog({
        "WindowManager\x04Shift": "Shift",
        "UI_Event_KeyMaps\x04F3": "F3",
    })

    result = bake_bilingual_catalogs(source)

    assert result["zh_en"].entries["WindowManager\x04Shift"] == "Shift"
    assert result["zh_en"].entries["UI_Event_KeyMaps\x04F3"] == "F3"


def test_bake_preserves_entries_when_combined_text_is_too_long():
    source = MoCatalog({
        "This is a long tooltip that should not be combined because it can make Blender UI labels too large": "这是一段很长的工具提示文本，合成双语后可能导致 Blender UI 标签过长，因此应该保持原翻译",
    })

    result = bake_bilingual_catalogs(source)

    assert result["zh_en"].entries[next(iter(source.entries))] == next(iter(source.entries.values()))


def test_bake_preserves_entries_when_either_output_order_is_too_long():
    source = MoCatalog({
        "Short": "这是一段非常长的中文翻译文本，会让英文在前的双语形式超过长度上限，并且继续增加长度以触发保护规则",
    })

    result = bake_bilingual_catalogs(source)

    assert result["zh_en"].entries["Short"] == source.entries["Short"]
    assert result["en_zh"].entries["Short"] == source.entries["Short"]
