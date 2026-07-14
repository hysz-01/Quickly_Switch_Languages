import re
from pathlib import Path

from .mo import MoCatalog, read_mo, write_mo


OUTPUT_LANGUAGES = ("zh_en", "en_zh")
MAX_COMBINED_LENGTH = 60
_PLACEHOLDER_RE = re.compile(
    r"%(?:\d+\$)?(?:\([^)]+\))?[#0 +\-]*(?:(?:\d+\$)?\*|\d+)?(?:\.(?:(?:\d+\$)?\*|\d+))?[hlL]?[diouxXeEfFgGcrs%]|\{[^{}]+\}"
)
_BLOCKED_CONTEXTS = {"WindowManager", "UI_Event_KeyMaps"}


def _placeholders(text: str) -> list[str]:
    return _PLACEHOLDER_RE.findall(text)


def _display_width(text: str) -> int:
    return sum(1 if ord(char) < 128 else 2 for char in text)


def _translation_text(msgid: str) -> str:
    return msgid.rsplit("\x04", 1)[-1]


def _context(msgid: str) -> str:
    return msgid.split("\x04", 1)[0] if "\x04" in msgid else ""


def _matches_scope(msgid: str, scope_keywords: set[str] | None) -> bool:
    if _context(msgid) in _BLOCKED_CONTEXTS:
        return False
    if scope_keywords is None:
        return True
    folded = _translation_text(msgid).casefold()
    return any(keyword.casefold() == folded for keyword in scope_keywords)


def _can_combine(msgid: str, msgstr: str) -> bool:
    text = _translation_text(msgid)
    if not text or not msgstr or text == msgstr:
        return False
    if "{" in text or "}" in text or "{" in msgstr or "}" in msgstr:
        return False
    if _placeholders(text) or _placeholders(msgstr):
        return False
    return (
        _display_width(f"{msgstr} ({text})") <= MAX_COMBINED_LENGTH
        and _display_width(f"{text} ({msgstr})") <= MAX_COMBINED_LENGTH
    )


def bake_bilingual_catalogs(source: MoCatalog, scope_keywords: set[str] | None = None) -> dict[str, MoCatalog]:
    zh_en = {}
    en_zh = {}
    for msgid, msgstr in source.entries.items():
        if msgid == "" or not _matches_scope(msgid, scope_keywords) or not _can_combine(msgid, msgstr):
            zh_en[msgid] = msgstr
            en_zh[msgid] = msgstr
            continue
        text = _translation_text(msgid)
        zh_en[msgid] = f"{msgstr} ({text})"
        en_zh[msgid] = f"{text} ({msgstr})"
    return {
        "zh_en": MoCatalog(zh_en),
        "en_zh": MoCatalog(en_zh),
    }


def _short_language_code(language_code: str) -> str:
    if language_code in {"zh_CN", "zh_HANS"}:
        return "zh"
    if language_code == "en_US":
        return "en"
    return language_code.split("_", 1)[0].lower()


def bilingual_language_code(language1_code: str, language2_code: str) -> str:
    return f"{_short_language_code(language1_code)}_{_short_language_code(language2_code)}"


def bake_bilingual_pair_catalog(
    source: MoCatalog,
    english_first: bool,
    scope_keywords: set[str] | None = None,
) -> MoCatalog:
    entries = {}
    for msgid, msgstr in source.entries.items():
        if msgid == "" or not _matches_scope(msgid, scope_keywords) or not _can_combine(msgid, msgstr):
            entries[msgid] = msgstr
            continue
        text = _translation_text(msgid)
        entries[msgid] = f"{text} ({msgstr})" if english_first else f"{msgstr} ({text})"
    return MoCatalog(entries)


def bake_bilingual_files(source_mo: Path, output_root: Path, scope_keywords: set[str] | None = None) -> dict[str, Path]:
    catalogs = bake_bilingual_catalogs(read_mo(source_mo), scope_keywords=scope_keywords)
    outputs = {}
    for lang_code, catalog in catalogs.items():
        output_path = output_root / lang_code / "LC_MESSAGES" / "blender.mo"
        write_mo(output_path, catalog)
        outputs[lang_code] = output_path
    return outputs


def bake_bilingual_pair_file(
    source_mo: Path,
    output_root: Path,
    output_code: str,
    english_first: bool,
    scope_keywords: set[str] | None = None,
) -> Path:
    catalog = bake_bilingual_pair_catalog(read_mo(source_mo), english_first, scope_keywords=scope_keywords)
    output_path = output_root / output_code / "LC_MESSAGES" / "blender.mo"
    write_mo(output_path, catalog)
    return output_path
