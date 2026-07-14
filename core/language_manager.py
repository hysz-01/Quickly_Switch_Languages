import json
import os
from typing import List, Dict, Optional

class LanguageManager:
    def __init__(self, json_path: str, default_json_path: str | None = None):
        self.json_path = json_path
        self.default_json_path = default_json_path
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        if not os.path.exists(self.json_path):
            os.makedirs(os.path.dirname(self.json_path), exist_ok=True)
            data = self._default_data()
            data["defaults_migrated"] = True
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    def _default_data(self) -> Dict:
        if self.default_json_path and os.path.exists(self.default_json_path):
            try:
                with open(self.default_json_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (OSError, json.JSONDecodeError, UnicodeDecodeError):
                pass
        return {"favorites": []}
    
    def _load_data(self) -> Dict:
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            data = self._default_data()
            self._save_data(data)
            return data

    def _merge_with_defaults(self, favorites: List[Dict]) -> List[Dict]:
        merged = []
        seen = set()
        for source in (self._default_data().get("favorites", []), favorites):
            for fav in source:
                code = fav.get("code")
                name = fav.get("name")
                if code and name and code not in seen:
                    merged.append({"code": code, "name": name})
                    seen.add(code)
        return merged

    def _needs_default_migration(self, data: Dict) -> bool:
        return self.default_json_path is not None and not data.get("defaults_migrated")
    
    def _save_data(self, data: Dict):
        with open(self.json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def get_favorites(self) -> List[Dict]:
        data = self._load_data()
        had_migration_marker = "defaults_migrated" in data
        favorites = [
            fav for fav in data.get("favorites", [])
            if fav.get("code") and fav.get("name")
        ]
        if self._needs_default_migration(data):
            favorites = self._merge_with_defaults(favorites)
            data["defaults_migrated"] = True
        if favorites != data.get("favorites", []) or ("defaults_migrated" in data and not had_migration_marker):
            data["favorites"] = favorites
            self._save_data(data)
        return favorites
    
    def add_favorite(self, language: Dict) -> bool:
        """Add a language to favorites. Returns True if added, False if already exists."""
        if not all(k in language for k in ("code", "name")):
            raise ValueError("Language must have 'code' and 'name' keys")
        
        # Validate that code and name are not empty
        if not language["code"] or not language["name"]:
            raise ValueError("Language code and name cannot be empty")
        
        data = self._load_data()
        favorites = data.get("favorites", [])
        
        # Check if already exists
        for fav in favorites:
            if fav["code"] == language["code"]:
                return False
        
        favorites.append(language)
        data["favorites"] = favorites
        self._save_data(data)
        return True
    
    def remove_favorite(self, language_code: str) -> bool:
        """Remove a language from favorites. Returns True if removed, False if not found."""
        data = self._load_data()
        favorites = data.get("favorites", [])
        
        original_length = len(favorites)
        favorites = [fav for fav in favorites if fav["code"] != language_code]
        
        if len(favorites) < original_length:
            data["favorites"] = favorites
            self._save_data(data)
            return True
        return False
    
    def update_favorites(self, favorites: List[Dict]):
        """Replace entire favorites list."""
        data = self._load_data()
        data["favorites"] = favorites
        self._save_data(data)
