import json
import hashlib
import os
import re
import shutil
from pathlib import Path

from .baker import bake_bilingual_files, bake_bilingual_pair_file, bilingual_language_code


BEGIN_MARKER = "# BEGIN Quick Language Switcher bilingual languages"
END_MARKER = "# END Quick Language Switcher bilingual languages"
LEGACY_LANGUAGE_IDS = {
    "en_zh": 998,
    "zh_en": 999,
}
BILINGUAL_LANGUAGE_ENTRIES = {
    "en_zh": "998:English + Chinese - English (简体中文):en_zh:100%",
    "zh_en": "999:Chinese + English - 简体中文 (English):zh_en:100%",
}


def _language_codes(text: str) -> set[str]:
    codes = set()
    for line in text.splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split(":")
        if len(parts) >= 3:
            codes.add(parts[2])
    return codes


def _language_ids(text: str) -> set[int]:
    ids = set()
    for line in text.splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split(":")
        if len(parts) >= 3:
            try:
                ids.add(int(parts[0]))
            except ValueError:
                pass
    return ids


def _language_entries(text: str) -> dict[str, str]:
    entries = {}
    for line in text.splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split(":")
        if len(parts) >= 3:
            entries[parts[2]] = line
    return entries


def _language_entry_id(language_code: str) -> int:
    if language_code in LEGACY_LANGUAGE_IDS:
        return LEGACY_LANGUAGE_IDS[language_code]
    weighted = sum((index + 1) * ord(char) for index, char in enumerate(language_code))
    return 9000 + weighted % 900


def _available_language_entry_id(language_code: str, languages_text: str) -> int:
    entry_id = _language_entry_id(language_code)
    existing_ids = _language_ids(languages_text)
    if entry_id in existing_ids and language_code in LEGACY_LANGUAGE_IDS:
        weighted = sum((index + 1) * ord(char) for index, char in enumerate(language_code))
        entry_id = 9000 + weighted % 900
    while entry_id in existing_ids and entry_id <= 9999:
        entry_id += 1
    if entry_id > 9999:
        raise ValueError("No available language id for generated locale")
    return entry_id


def _source_mo_path(locale_root: Path, language_code: str) -> Path:
    locale_dirs = [path for path in locale_root.iterdir() if (path / "LC_MESSAGES" / "blender.mo").exists()]
    locale_names = {path.name: path for path in locale_dirs}

    if language_code in locale_names:
        return locale_names[language_code] / "LC_MESSAGES" / "blender.mo"

    if "@" in language_code:
        prefix, modifier = language_code.split("@", 1)
        base = prefix.split("_", 1)[0]
        modified = f"{base}@{modifier}"
        if modified in locale_names:
            return locale_names[modified] / "LC_MESSAGES" / "blender.mo"

    if "_" in language_code:
        base = language_code.split("_", 1)[0]
        if base in locale_names:
            return locale_names[base] / "LC_MESSAGES" / "blender.mo"

    return locale_root / language_code / "LC_MESSAGES" / "blender.mo"


def unpatch_languages_text(text: str) -> str:
    pattern = re.compile(rf"\n?{re.escape(BEGIN_MARKER)}.*?{re.escape(END_MARKER)}\n?", re.DOTALL)
    result = pattern.sub("\n", text)
    while "\n\n\n" in result:
        result = result.replace("\n\n\n", "\n\n")
    return result


def patch_languages_text(text: str, entries: dict[str, str]) -> str:
    old_entries = _language_entries(_addon_language_block(text))
    clean = unpatch_languages_text(text)
    existing_codes = _language_codes(clean)
    existing_ids = _language_ids(clean)
    merged_entries = {**old_entries, **entries}
    for code, entry in merged_entries.items():
        if code in existing_codes:
            raise ValueError(f"Conflicting language code: {code}")
        try:
            entry_id = int(entry.split(":", 1)[0])
        except ValueError:
            continue
        if entry_id in existing_ids:
            raise ValueError(f"Conflicting language id: {entry_id}")
    block = "\n".join([BEGIN_MARKER, *merged_entries.values(), END_MARKER]) + "\n"
    separator = "" if clean.endswith("\n") else "\n"
    return clean + separator + block


def _addon_language_block(text: str) -> str:
    return "\n".join(
        match.group(1)
        for match in re.finditer(rf"{re.escape(BEGIN_MARKER)}(.*?){re.escape(END_MARKER)}", text, re.DOTALL)
    )


def _marked_language_codes(text: str) -> set[str]:
    return _language_codes(_addon_language_block(text))


def write_manifest(path: Path, manifest: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def read_manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _manifest_list(manifest: dict, key: str) -> list:
    if not isinstance(manifest, dict):
        return []
    value = manifest.get(key, [])
    return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []


def _manifest_dict(manifest: dict, key: str) -> dict:
    if not isinstance(manifest, dict):
        return {}
    value = manifest.get(key, {})
    return value if isinstance(value, dict) else {}


def merge_manifest(existing: dict, new: dict) -> dict:
    existing = existing if isinstance(existing, dict) else {}
    merged = dict(existing)
    for key, value in new.items():
        if key not in {"installed_language_codes", "installed_language_ids", "installed_files", "added_language_lines"}:
            merged[key] = value

    language_codes = list(_manifest_list(existing, "installed_language_codes"))
    for code in _manifest_list(new, "installed_language_codes"):
        if code not in language_codes:
            language_codes.append(code)
    merged["installed_language_codes"] = language_codes

    language_ids = dict(_manifest_dict(existing, "installed_language_ids"))
    language_ids.update(_manifest_dict(new, "installed_language_ids"))
    if language_ids:
        merged["installed_language_ids"] = language_ids

    installed_files = list(_manifest_list(existing, "installed_files"))
    for relative in _manifest_list(new, "installed_files"):
        if relative not in installed_files:
            installed_files.append(relative)
    merged["installed_files"] = installed_files

    lines_by_code = _language_entries("\n".join(_manifest_list(existing, "added_language_lines")))
    lines_by_code.update(_language_entries("\n".join(_manifest_list(new, "added_language_lines"))))
    merged["added_language_lines"] = list(lines_by_code.values())
    return merged


def write_merged_manifest(path: Path, manifest: dict) -> dict:
    if path.exists():
        try:
            manifest = merge_manifest(read_manifest(path), manifest)
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            pass
    write_manifest(path, manifest)
    return manifest


def _remove_empty_parents(path: Path, stop_at: Path) -> None:
    current = path
    while current != stop_at and current.exists():
        try:
            current.rmdir()
        except OSError:
            return
        current = current.parent


def _installed_file_path(locale_root: Path, relative: str) -> Path:
    relative_path = Path(relative)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValueError(f"Unsafe installed file path: {relative}")
    target = (locale_root / relative_path).resolve()
    root = locale_root.resolve()
    if target == root or root not in target.parents:
        raise ValueError(f"Unsafe installed file path: {relative}")
    if target.name != "blender.mo" or target.parent.name != "LC_MESSAGES":
        raise ValueError(f"Unsafe installed file path: {relative}")
    return target


def uninstall_from_manifest(locale_root: Path, languages_path: Path, manifest_path: Path) -> None:
    manifest = read_manifest(manifest_path)
    installed_targets = [
        _installed_file_path(locale_root, relative)
        for relative in _manifest_list(manifest, "installed_files")
    ]
    if languages_path.exists():
        original = languages_path.read_text(encoding="utf-8")
        try:
            languages_path.write_text(unpatch_languages_text(original), encoding="utf-8")
        except Exception:
            try:
                languages_path.write_text(original, encoding="utf-8")
            except OSError:
                pass
            raise
    for target in installed_targets:
        if target.exists():
            target.unlink()
        _remove_empty_parents(target.parent, locale_root)


def emergency_cleanup(locale_root: Path, manifest_path: Path) -> None:
    """Restore Blender locale to its pre-addon state WITHOUT relying on a valid manifest.

    This is a safety net — it:
    1. Removes only this add-on's marked language block.
    2. Removes files recorded by the manifest or explicitly named in the marker block.

    Safe to call even when nothing is installed.
    """
    languages_path = locale_root / "languages"

    marked_codes: set[str] = set()
    languages_text = None
    if languages_path.exists():
        languages_text = languages_path.read_text(encoding="utf-8")
        marked_codes = _marked_language_codes(languages_text)

    installed_files = []
    if manifest_path.exists():
        try:
            manifest = read_manifest(manifest_path)
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            manifest = {}
        installed_files = _manifest_list(manifest, "installed_files")
    else:
        installed_files = [f"{code}/LC_MESSAGES/blender.mo" for code in marked_codes]

    if not installed_files and marked_codes:
        installed_files = [f"{code}/LC_MESSAGES/blender.mo" for code in marked_codes]

    installed_targets = [
        _installed_file_path(locale_root, relative)
        for relative in installed_files
    ]

    if languages_text is not None:
        try:
            languages_path.write_text(unpatch_languages_text(languages_text), encoding="utf-8")
        except Exception:
            try:
                languages_path.write_text(languages_text, encoding="utf-8")
            except OSError:
                pass
            raise

    for target in installed_targets:
        if target.exists():
            target.unlink()
        _remove_empty_parents(target.parent, locale_root)

    # Remove manifest if it exists
    if manifest_path.exists():
        try:
            manifest_path.unlink()
        except OSError:
            pass


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _require_writable(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)
    if not os.access(path, os.W_OK):
        raise PermissionError(f"Not writable: {path}")


def _install_and_patch(
    locale_root: Path,
    languages_path: Path,
    mo_files: list[tuple[str, Path]],  # (relative_target, source_path)
    backup_path: Path,
    language_entries: dict[str, str],
) -> tuple[list[str], str]:
    """Copy .mo files and patch languages text, with automatic rollback on failure."""
    if not backup_path.exists():
        shutil.copy2(languages_path, backup_path)

    installed_files: list[str] = []
    original = None
    try:
        for relative, source in mo_files:
            target = locale_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            installed_files.append(relative)

        original = languages_path.read_text(encoding="utf-8")
        languages_path.write_text(patch_languages_text(original, language_entries), encoding="utf-8")
    except Exception:
        if original is not None:
            try:
                languages_path.write_text(original, encoding="utf-8")
            except OSError:
                pass
        for relative in installed_files:
            target = locale_root / relative
            if target.exists():
                target.unlink()
            _remove_empty_parents(target.parent, locale_root)
        raise

    return installed_files, original


def _augment_manifest(base: dict, scope_keywords, scope_presets, blender_version) -> dict:
    if scope_keywords is not None:
        base["scope_keywords"] = sorted(scope_keywords)
        base["scope_blender_version"] = blender_version
        base["scope_keyword_count"] = len(scope_keywords)
    if scope_presets is not None:
        base["scope_presets"] = list(scope_presets)
    return base


def install_bilingual_pack(
    locale_root: Path,
    blender_version: str,
    addon_root: Path,
    scope_keywords: set[str] | None = None,
    scope_presets: list[str] | None = None,
    manifest_path: Path | None = None,
) -> dict:
    languages_path = locale_root / "languages"
    source_mo = _source_mo_path(locale_root, "zh_HANS")
    _require_writable(locale_root)
    _require_writable(languages_path)
    if not source_mo.exists():
        raise FileNotFoundError(source_mo)

    generated_root = addon_root / "generated" / blender_version
    generated = bake_bilingual_files(source_mo, generated_root, scope_keywords=scope_keywords)

    mo_files = [(f"{code}/LC_MESSAGES/blender.mo", source) for code, source in generated.items()]
    installed_files, original_languages = _install_and_patch(
        locale_root,
        languages_path,
        mo_files,
        locale_root / "languages.quick_language_switcher.bak",
        BILINGUAL_LANGUAGE_ENTRIES,
    )

    manifest = _augment_manifest(
        {
            "blender_version": blender_version,
            "locale_root": str(locale_root),
            "source_language": "zh_HANS",
            "source_mo_hash": _sha256(source_mo),
            "languages_hash_before": hashlib.sha256(original_languages.encode("utf-8")).hexdigest(),
            "installed_language_codes": ["zh_en", "en_zh"],
            "installed_files": installed_files,
            "added_language_lines": list(BILINGUAL_LANGUAGE_ENTRIES.values()),
        },
        scope_keywords,
        scope_presets,
        blender_version,
    )
    return write_merged_manifest(manifest_path or addon_root / "data" / "bilingual_manifest.json", manifest)


def install_bilingual_pair(
    locale_root: Path,
    blender_version: str,
    addon_root: Path,
    language1_code: str,
    language1_name: str,
    language2_code: str,
    language2_name: str,
    scope_keywords: set[str] | None = None,
    scope_presets: list[str] | None = None,
    manifest_path: Path | None = None,
) -> dict:
    language_codes = {language1_code, language2_code}
    if "en_US" not in language_codes or len(language_codes) != 2:
        raise ValueError("Bilingual pair must contain English and one non-English language")

    output_code = bilingual_language_code(language1_code, language2_code)
    non_english_code = language2_code if language1_code == "en_US" else language1_code
    languages_path = locale_root / "languages"
    _require_writable(locale_root)
    _require_writable(languages_path)
    languages_text = languages_path.read_text(encoding="utf-8")
    language_entry_id = _available_language_entry_id(output_code, languages_text)
    source_mo = _source_mo_path(locale_root, non_english_code)
    if not source_mo.exists():
        raise FileNotFoundError(source_mo)

    generated_root = addon_root / "generated" / blender_version
    generated = bake_bilingual_pair_file(
        source_mo,
        generated_root,
        output_code,
        english_first=language1_code == "en_US",
        scope_keywords=scope_keywords,
    )

    entry = f"{language_entry_id}:{language1_name} + {language2_name} - {language1_name} ({language2_name}):{output_code}:100%"
    installed_files, original_languages = _install_and_patch(
        locale_root,
        languages_path,
        [(f"{output_code}/LC_MESSAGES/blender.mo", generated)],
        locale_root / "languages.quick_language_switcher.bak",
        {output_code: entry},
    )

    manifest = _augment_manifest(
        {
            "blender_version": blender_version,
            "locale_root": str(locale_root),
            "source_language": non_english_code,
            "source_mo_hash": _sha256(source_mo),
            "languages_hash_before": hashlib.sha256(original_languages.encode("utf-8")).hexdigest(),
            "installed_language_codes": [output_code],
            "installed_language_ids": {output_code: language_entry_id},
            "installed_files": installed_files,
            "added_language_lines": [entry],
            "bilingual_language_1": language1_code,
            "bilingual_language_2": language2_code,
        },
        scope_keywords,
        scope_presets,
        blender_version,
    )
    return write_merged_manifest(manifest_path or addon_root / "data" / "bilingual_manifest.json", manifest)
