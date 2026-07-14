from pathlib import Path

try:
    import bpy
except Exception:
    bpy = None


def addon_root() -> Path:
    return Path(__file__).resolve().parents[1]


def data_path(filename: str) -> Path:
    return addon_root() / "data" / filename


def user_data_path(filename: str) -> Path:
    if bpy is not None:
        try:
            return Path(bpy.utils.user_resource('CONFIG', path="quick_language_switcher", create=True)) / filename
        except Exception:
            pass
    return addon_root() / "user_data" / filename
