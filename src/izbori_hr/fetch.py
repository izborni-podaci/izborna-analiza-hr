"""Download an election's zip from DIP's archive and keep its files as published.

The archive is final, so a download changes nothing unless DIP republishes: files are written, and meta.json
updated, only when the zip's content changed. Run on GitHub's runners (the `data` workflow): the development
sandbox may not reach izbori.hr.
"""

from __future__ import annotations

import fnmatch
import hashlib
import io
import json
import time
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from izbori_hr.elections import Election

USER_AGENT = "izborna-analiza-hr (+https://github.com/izborni-podaci/izborna-analiza-hr)"


def download(url: str, tries: int = 4) -> bytes:
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except OSError:
            if attempt == tries - 1:
                raise
            time.sleep(5 * (attempt + 1))
    raise AssertionError("unreachable")


def entry_name(info: zipfile.ZipInfo, encoding: str) -> str:
    """A file's name in the zip. Without the UTF-8 flag Python reads names as cp437; older zips are DOS Latin 2."""
    if info.flag_bits & 0x800 or encoding == "cp437":
        return info.filename
    return info.filename.encode("cp437").decode(encoding)


def kept(name: str, patterns: tuple[str, ...]) -> bool:
    return not name.endswith("/") and any(fnmatch.fnmatch(name, p) for p in patterns)


def store(election: Election, blob: bytes, data_dir: Path, log=print) -> bool:
    """Keep the zip's files that hold results; True when anything changed."""
    out = data_dir / election.id
    meta_path = out / "meta.json"
    digest = hashlib.sha256(blob).hexdigest()
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    if meta.get("sha256") == digest and meta.get("keep") == list(election.keep):
        log(f"{election.id}: unchanged")
        return False
    files = {}
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        for info in z.infolist():
            name = entry_name(info, election.names)
            if not kept(name, election.keep):
                continue
            data = z.read(info)
            path = out / "raw" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            files[name] = hashlib.sha256(data).hexdigest()
    meta = {"source": election.zip_url, "page": election.page_url,
            "fetched": datetime.now(timezone.utc).isoformat(timespec="seconds"), "sha256": digest,
            "keep": list(election.keep), "files": dict(sorted(files.items()))}
    out.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    log(f"{election.id}: {len(files)} files kept from {len(blob) / 1e6:.1f} MB")
    return True


def fetch(election: Election, data_dir: Path, log=print) -> bool:
    return store(election, download(election.zip_url), data_dir, log)
