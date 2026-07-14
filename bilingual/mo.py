import os
import struct
from dataclasses import dataclass
from pathlib import Path


_MO_MAGIC_LE = 0x950412DE
_MO_MAGIC_BE = 0xDE120495


@dataclass(frozen=True)
class MoCatalog:
    entries: dict[str, str]


def read_mo(path: str | os.PathLike) -> MoCatalog:
    data = Path(path).read_bytes()
    magic = struct.unpack("<I", data[:4])[0]
    if magic == _MO_MAGIC_LE:
        endian = "<"
    elif magic == _MO_MAGIC_BE:
        endian = ">"
    else:
        raise ValueError("Invalid .mo magic number")

    _magic, _revision, count, original_offset, translated_offset, _hash_size, _hash_offset = struct.unpack(
        endian + "7I", data[:28]
    )
    entries = {}
    for index in range(count):
        orig_len, orig_pos = struct.unpack(
            endian + "2I",
            data[original_offset + index * 8:original_offset + (index + 1) * 8],
        )
        trans_len, trans_pos = struct.unpack(
            endian + "2I",
            data[translated_offset + index * 8:translated_offset + (index + 1) * 8],
        )
        original = data[orig_pos:orig_pos + orig_len].decode("utf-8")
        translated = data[trans_pos:trans_pos + trans_len].decode("utf-8")
        entries[original] = translated
    return MoCatalog(entries)


def write_mo(path: str | os.PathLike, catalog: MoCatalog) -> None:
    items = sorted(catalog.entries.items(), key=lambda item: item[0])
    ids = [key.encode("utf-8") for key, _value in items]
    strs = [value.encode("utf-8") for _key, value in items]

    count = len(items)
    header_size = 28
    original_table_offset = header_size
    translated_table_offset = original_table_offset + count * 8
    string_offset = translated_table_offset + count * 8

    original_table = []
    translated_table = []
    string_data = bytearray()

    for msgid in ids:
        original_table.append((len(msgid), string_offset + len(string_data)))
        string_data.extend(msgid + b"\0")

    for msgstr in strs:
        translated_table.append((len(msgstr), string_offset + len(string_data)))
        string_data.extend(msgstr + b"\0")

    output = bytearray()
    output.extend(struct.pack("<7I", _MO_MAGIC_LE, 0, count, original_table_offset, translated_table_offset, 0, 0))
    for length, offset in original_table:
        output.extend(struct.pack("<2I", length, offset))
    for length, offset in translated_table:
        output.extend(struct.pack("<2I", length, offset))
    output.extend(string_data)

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(output)
