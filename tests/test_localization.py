from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from Quickly_switch_languages.core.localization import normalize_language, translate


def test_normalize_language_aliases():
    assert normalize_language("zh_CN") == "zh_HANS"
    assert normalize_language("zh_TW") == "zh_HANT"
    assert normalize_language("ja_JP") == "ja_JP"
    assert normalize_language("en_US") == "en_US"


def test_normalize_language_preserves_bilingual_language_codes():
    assert normalize_language("zh_en") == "zh_en"
    assert normalize_language("en_zh") == "en_zh"


def test_translate_returns_supported_languages_and_falls_back():
    assert translate("Basic Language Switching", "zh_HANS") == "基础语言切换"
    assert translate("Basic Language Switching", "zh_HANT") == "基礎語言切換"
    assert translate("Basic Language Switching", "ja_JP") == "基本言語切り替え"
    assert translate("Missing String", "zh_HANS") == "Missing String"


def test_required_ui_strings_have_all_non_english_translations():
    required = [
        "Basic Language Switching",
        "Advanced: Bilingual Language Packs",
        "Experimental: Region Scope",
        "Enable Experimental Region Scope",
        "Experimental scope: disabled",
        "When disabled, bilingual pack installation uses the default full scope.",
        "Install / Update Bilingual Packs",
        "Uninstall Bilingual Packs",
        "Language 1",
        "Language 2",
        "Add a language to the top-bar switcher",
        "Manage Languages...",
        "Favorites: {count}",
        "Switched UI language to {name}",
    ]
    for language in ("zh_HANS", "zh_HANT", "ja_JP"):
        for text in required:
            assert translate(text, language) != text
