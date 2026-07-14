from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
from Quickly_switch_languages.bilingual.mo import MoCatalog, read_mo, write_mo


def test_write_then_read_roundtrips_context_and_header(tmp_path):
    path = tmp_path / "blender.mo"
    catalog = MoCatalog({
        "": "Content-Type: text/plain; charset=UTF-8\n",
        "File": "文件",
        "Operator\x04Open": "打开",
    })

    write_mo(path, catalog)
    result = read_mo(path)

    assert result.entries == catalog.entries
