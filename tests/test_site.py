"""The built site: every page in both languages, every link and anchor resolves, nothing loads from elsewhere."""

import json
import re
from pathlib import Path
from urllib.parse import urldefrag

import pytest

from izbori_hr.site import build

DATA = Path(__file__).resolve().parent.parent / "data"
HREF = re.compile(r'(?:href|src)="([^"]*)"')
ALLOWED = ("https://www.izbori.hr/", "https://github.com/izborni-podaci/", "https://izborni-podaci.github.io/")


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    out = tmp_path_factory.mktemp("site")
    build(DATA, out)
    return out


def test_pages_in_both_languages(site):
    for prefix in ("", "en/"):
        for page in ("index.html", "about.html", "r/sabor-2024/index.html", "r/sabor-2024/check.html",
                     "r/sabor-2024/j/IV.html", "r/sabor-2024/j/XII-1.html", "r/sabor-2024/m/14-beli-manastir.html",
                     "r/predsjednik-2024-2/index.html",
                     "r/predsjednik-2024-1/m/21-grad-zagreb.html"):
            assert (site / prefix / page).is_file(), prefix + page
    for prefix in ("", "en/"):
        for page in ("elections.html", "municipalities.html", "repeat.html", "m/14-beli-manastir.html",
                     "m/21-grad-zagreb.html"):
            assert (site / prefix / page).is_file(), prefix + page
    # the places' pages are Croatian only (size budget); both languages link to them
    assert (site / "s/14-beli-manastir-3.html").is_file() and not (site / "en/s").exists()
    assert 'href="../../s/14-beli-manastir-3.html"' in (site / "en/m/14-beli-manastir.html").read_text(encoding="utf-8")
    index = json.loads((site / "search.json").read_text(encoding="utf-8"))
    municipalities = {m[1] for m in index["m"]}
    assert "21-grad-zagreb" in municipalities and all(index["m"][s[0]][1] in municipalities for s in index["s"])
    assert all((site / f"s/{s[3]}.html").is_file() for s in index["s"][:200])
    assert "table.history td.l-turnout" in (site / "static/labels.css").read_text(encoding="utf-8")
    assert (site / "api/r/sabor-2024/flags.csv").read_text(encoding="utf-8").startswith("round,contest,")
    home = (site / "index.html").read_text(encoding="utf-8")
    assert 'lang="hr"' in home and "data-search" in home and "Odakle krenuti" in home
    assert "Izbori u arhivi" in (site / "elections.html").read_text(encoding="utf-8")
    assert "Elections in the archive" in (site / "en/elections.html").read_text(encoding="utf-8")


def test_results_on_the_pages(site):
    sabor = (site / "r/sabor-2024/index.html").read_text(encoding="utf-8")
    assert re.search(r"HRVATSKA DEMOKRATSKA ZAJEDNICA - HDZ</td><td [^>]*><strong>61</strong>", sabor)
    second = (site / "en/r/predsjednik-2024-2/index.html").read_text(encoding="utf-8")
    assert "ZORAN MILANOVIĆ: 71.92% of the votes of those who voted" in second
    assert "74.68%" in second  # of the valid ballots, as the result was reported
    first = (site / "r/predsjednik-2024-1/index.html").read_text(encoding="utf-8")
    assert "U drugi krug idu ZORAN MILANOVIĆ i DRAGAN PRIMORAC" in first


def test_links_and_anchors_resolve(site):
    pages = sorted(site.rglob("*.html"))
    ids: dict[Path, set] = {}
    missing, external = [], set()
    for page in pages:
        text = page.read_text(encoding="utf-8")
        for href in HREF.findall(text):
            if href.startswith(("http://", "https://")):
                if not href.startswith(ALLOWED):
                    external.add(href)
                continue
            if page.name == "404.html" or href.startswith(("mailto:", "#")) or not href:
                continue
            path, fragment = urldefrag(href)
            target = (page.parent / path).resolve()
            if not target.is_file():
                missing.append((page.relative_to(site), href))
                continue
            if fragment and target.suffix == ".html" and target.parent.name == "m":
                if target not in ids:
                    ids[target] = set(re.findall(r'id="([^"]+)"', target.read_text(encoding="utf-8")))
                if fragment not in ids[target]:
                    missing.append((page.relative_to(site), href))
    assert not missing, missing[:10]
    assert not external, sorted(external)[:10]


def test_nothing_from_third_parties(site):
    """Principle 5: no script, style or font from anywhere else."""
    for page in [site / "index.html", site / "en/r/sabor-2024/check.html"]:
        text = page.read_text(encoding="utf-8")
        assert not re.search(r'<(?:script|link)[^>]+(?:src|href)="https?://', text)
    assert "url(http" not in (site / "static/fonts.css").read_text(encoding="utf-8")
