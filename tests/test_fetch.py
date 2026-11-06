"""Keeping DIP's files: only the results, and nothing written when the zip didn't change."""

import io
import json
import zipfile

from izbori_hr import fetch
from izbori_hr.elections import BY_ID


def _zip(files: dict) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, data in files.items():
            z.writestr(name, data)
    return buf.getvalue()


def test_store_keeps_results_only_and_skips_an_unchanged_zip(tmp_path):
    sabor = BY_ID["sabor-2024"]
    blob = _zip({"CSV/02_01_rezultati.csv": b"a;b\n1;2\n", "XLSX/02_01.xlsx": b"x", "CSV/": b""})
    assert fetch.store(sabor, blob, tmp_path, log=lambda m: None)
    raw = tmp_path / "sabor-2024" / "raw"
    assert sorted(p.relative_to(raw).as_posix() for p in raw.rglob("*") if p.is_file()) == ["CSV/02_01_rezultati.csv"]
    meta = json.loads((tmp_path / "sabor-2024" / "meta.json").read_text(encoding="utf-8"))
    assert meta["source"].endswith("/data/parlament/2024/zip/rezultati.zip") and list(meta["files"]) == [
        "CSV/02_01_rezultati.csv"]
    assert not fetch.store(sabor, blob, tmp_path, log=lambda m: None)
    president = BY_ID["predsjednik-2024"]
    assert fetch.kept("rezultati_2024/1_krug/rezultati_bm(1).xlsx", president.keep)
