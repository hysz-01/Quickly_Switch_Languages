import json
import os
import tempfile
import pytest
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
from Quickly_switch_languages.core.language_manager import LanguageManager

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

def test_get_favorites_filters_empty_languages():
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump({
            "favorites": [
                {"code": "en_US", "name": "English"},
                {"code": "", "name": ""},
                {"code": "zh_CN", "name": ""},
                {"code": "", "name": "简体中文"},
            ]
        }, f)
        temp_path = f.name

    try:
        manager = LanguageManager(temp_path)
        languages = manager.get_favorites()
        assert languages == [{"code": "en_US", "name": "English"}]
    finally:
        os.unlink(temp_path)

def test_missing_file_is_created_with_empty_favorites():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = os.path.join(temp_dir, "languages.json")
        manager = LanguageManager(temp_path)
        assert manager.get_favorites() == []

        with open(temp_path, 'r', encoding='utf-8') as f:
            assert json.load(f) == {"favorites": [], "defaults_migrated": True}

def test_missing_user_file_is_seeded_from_default_favorites():
    with tempfile.TemporaryDirectory() as temp_dir:
        default_path = os.path.join(temp_dir, "default_languages.json")
        user_path = os.path.join(temp_dir, "user", "languages.json")
        defaults = {"favorites": [{"code": "en_US", "name": "English"}]}

        with open(default_path, 'w', encoding='utf-8') as f:
            json.dump(defaults, f)

        manager = LanguageManager(user_path, default_path)

        assert manager.get_favorites() == defaults["favorites"]
        with open(default_path, 'r', encoding='utf-8') as f:
            assert json.load(f) == defaults
        with open(user_path, 'r', encoding='utf-8') as f:
            assert json.load(f) == {"favorites": defaults["favorites"], "defaults_migrated": True}

def test_add_empty_language_raises_error():
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump({"favorites": []}, f)
        temp_path = f.name

    try:
        manager = LanguageManager(temp_path)
        with pytest.raises(ValueError, match="cannot be empty"):
            manager.add_favorite({"code": "", "name": ""})
    finally:
        os.unlink(temp_path)


def test_broken_user_file_falls_back_to_default_favorites():
    with tempfile.TemporaryDirectory() as temp_dir:
        default_path = os.path.join(temp_dir, "default_languages.json")
        user_path = os.path.join(temp_dir, "user", "languages.json")
        defaults = {"favorites": [{"code": "en_US", "name": "English"}]}

        os.makedirs(os.path.dirname(user_path), exist_ok=True)
        with open(default_path, 'w', encoding='utf-8') as f:
            json.dump(defaults, f)
        with open(user_path, 'w', encoding='utf-8') as f:
            f.write('{broken json')

        manager = LanguageManager(user_path, default_path)

        assert manager.get_favorites() == defaults["favorites"]
        with open(user_path, 'r', encoding='utf-8') as f:
            assert json.load(f) == {"favorites": defaults["favorites"], "defaults_migrated": True}


def test_existing_user_file_keeps_missing_default_favorites():
    with tempfile.TemporaryDirectory() as temp_dir:
        default_path = os.path.join(temp_dir, "default_languages.json")
        user_path = os.path.join(temp_dir, "user", "languages.json")
        defaults = {"favorites": [
            {"code": "en_US", "name": "English"},
            {"code": "zh_HANS", "name": "简体中文"},
            {"code": "ja_JP", "name": "日本語"},
        ]}
        existing = {"favorites": [
            {"code": "en_US", "name": "English"},
            {"code": "zh_en", "name": "简体中文 + English"},
        ]}

        os.makedirs(os.path.dirname(user_path), exist_ok=True)
        with open(default_path, 'w', encoding='utf-8') as f:
            json.dump(defaults, f)
        with open(user_path, 'w', encoding='utf-8') as f:
            json.dump(existing, f)

        manager = LanguageManager(user_path, default_path)

        assert manager.get_favorites() == [
            {"code": "en_US", "name": "English"},
            {"code": "zh_HANS", "name": "简体中文"},
            {"code": "ja_JP", "name": "日本語"},
            {"code": "zh_en", "name": "简体中文 + English"},
        ]


def test_default_favorites_are_not_readded_after_initial_migration():
    with tempfile.TemporaryDirectory() as temp_dir:
        default_path = os.path.join(temp_dir, "default_languages.json")
        user_path = os.path.join(temp_dir, "user", "languages.json")
        defaults = {"favorites": [
            {"code": "en_US", "name": "English"},
            {"code": "zh_HANS", "name": "简体中文"},
            {"code": "ja_JP", "name": "日本語"},
        ]}
        migrated = {
            "favorites": [{"code": "en_US", "name": "English"}],
            "defaults_migrated": True,
        }

        os.makedirs(os.path.dirname(user_path), exist_ok=True)
        with open(default_path, 'w', encoding='utf-8') as f:
            json.dump(defaults, f)
        with open(user_path, 'w', encoding='utf-8') as f:
            json.dump(migrated, f)

        manager = LanguageManager(user_path, default_path)

        assert manager.get_favorites() == [{"code": "en_US", "name": "English"}]


def test_complete_existing_user_file_gets_migration_marker():
    with tempfile.TemporaryDirectory() as temp_dir:
        default_path = os.path.join(temp_dir, "default_languages.json")
        user_path = os.path.join(temp_dir, "user", "languages.json")
        defaults = {"favorites": [
            {"code": "en_US", "name": "English"},
            {"code": "zh_HANS", "name": "简体中文"},
        ]}

        os.makedirs(os.path.dirname(user_path), exist_ok=True)
        with open(default_path, 'w', encoding='utf-8') as f:
            json.dump(defaults, f)
        with open(user_path, 'w', encoding='utf-8') as f:
            json.dump(defaults, f)

        manager = LanguageManager(user_path, default_path)
        assert manager.get_favorites() == defaults["favorites"]
        with open(user_path, 'r', encoding='utf-8') as f:
            assert json.load(f)["defaults_migrated"] is True
