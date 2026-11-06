"""The elections this archive holds, where DIP publishes them, and how their rounds are named.

DIP's archive (https://www.izbori.hr/arhiva-izbora/) offers each election's results by polling station as one zip
("Preuzmite sve datoteke"): CSV and XLSX by constituency for the parliament, XLSX by round for the president.
"""

from __future__ import annotations

from dataclasses import dataclass, field

ARCHIVE = "https://www.izbori.hr/arhiva-izbora/"


@dataclass(frozen=True)
class Round:
    id: str  # the round's id in this archive, e.g. "predsjednik-2024-1"
    number: int
    date: str  # election day, ISO
    files: tuple[str, ...]  # glob patterns of the zip's files that hold this round's results


@dataclass(frozen=True)
class Election:
    id: str  # e.g. "sabor-2024"
    kind: str  # "parliament" or "president"
    path: str  # the election's folder in DIP's archive, e.g. "parlament/2024"
    page: str  # the election's page in DIP's archive app
    title: dict = field(default_factory=dict)  # by language
    rounds: tuple[Round, ...] = ()
    keep: tuple[str, ...] = ()  # glob patterns of the zip's files kept in the archive
    names: str = "cp437"  # how the zip encodes its file names when it doesn't say (2003's: DOS Latin 2)
    published: bool = True  # on the site; False while its files are archived but not yet read
    xi_seats: int = 3  # seats for voters living abroad: fixed at 3 since 2011, set by turnout before

    @property
    def zip_url(self) -> str:
        return f"{ARCHIVE}data/{self.path}/zip/rezultati.zip"

    @property
    def page_url(self) -> str:
        return f"{ARCHIVE}#/app/{self.page}"


def _parliament(year: int, date: str, keep: tuple[str, ...], published: bool = False, names: str = "cp437",
                title_hr: str | None = None, xi_seats: int = 3) -> Election:
    return Election(
        id=f"sabor-{year}", kind="parliament", path=f"parlament/{year}", page=f"parlament-{year}",
        title={"hr": title_hr or f"Izbori za zastupnike u Hrvatski sabor {year}.",
               "en": f"Croatian parliamentary election {year}"},
        rounds=(Round(f"sabor-{year}", 1, date, keep),), keep=keep, names=names, published=published,
        xi_seats=xi_seats)


def _president(year: int, dates: tuple[str, str], files: tuple[str, str], keep: tuple[str, ...],
               published: bool = False) -> Election:
    span = f"{year}./{year + 1}." if dates[0][:4] != dates[1][:4] else f"{year}."
    span_en = f"{year}–{str(year + 1)[2:]}" if dates[0][:4] != dates[1][:4] else f"{year}"
    return Election(
        id=f"predsjednik-{year}", kind="president", path=f"predsjednik/{year}", page=f"predsjednik-{year}",
        title={"hr": f"Izbori za predsjednika Republike Hrvatske {span}",
               "en": f"Croatian presidential election {span_en}"},
        rounds=(Round(f"predsjednik-{year}-1", 1, dates[0], (files[0],)),
                Round(f"predsjednik-{year}-2", 2, dates[1], (files[1],))),
        keep=keep, published=published)


# Newest first. The parliament's files are kept as CSV (the XLSX repeat them); the president's as published. DIP's
# archive has results by polling station from 2000; before that, PDF reports only.
ELECTIONS = (
    _parliament(2024, "2024-04-17", ("CSV/*.csv",), published=True),
    _president(2024, ("2024-12-29", "2025-01-12"), ("*/1_krug/*.xlsx", "*/2_krug/*.xlsx"), ("*.xlsx",),
               published=True),
    _parliament(2020, "2020-07-05", ("CSV/*.csv",)),
    _president(2019, ("2019-12-22", "2020-01-05"), ("*/1_krug/*.xlsx", "*/2_krug/*.xlsx"), ("*.xlsx",)),
    _parliament(2016, "2016-09-11", ("CSV/*.csv",)),
    _parliament(2015, "2015-11-08", ("CSV/*.csv",)),
    _president(2014, ("2014-12-28", "2015-01-11"), ("*/1_krug/*.xlsx", "*/2_krug/*.xlsx"), ("*.xlsx", "*.csv")),
    _parliament(2011, "2011-12-04", ("CSV/*.csv",)),
    _president(2009, ("2009-12-27", "2010-01-10"), ("*/1_krug/*.xlsx", "*/2_krug/*.xlsx"), ("*.xlsx", "*.csv")),
    _parliament(2007, "2007-11-25", ("CSV/*.csv",), xi_seats=5),
    _president(2005, ("2005-01-02", "2005-01-16"), ("*1krug.xlsx", "*2krug.xlsx"), ("*.xlsx", "*.csv")),
    _parliament(2003, "2003-11-23", ("Rezultati po BM redovita+*/CSV/*.csv",), names="cp852", xi_seats=4),
    # 2000: the sheets name the lists in their header, which the CSV only number
    _parliament(2000, "2000-01-03", ("RezultatiPoBM/CSV/*.csv", "RezultatiPoBM/Excel/*.xlsx"), xi_seats=6),
    _president(2000, ("2000-01-24", "2000-02-07"), ("*1. krug*.xlsx", "*2. krug*.xlsx"), ("*.xlsx", "*.csv")),
)
PUBLISHED = tuple(e for e in ELECTIONS if e.published)

BY_ID = {e.id: e for e in ELECTIONS}
ROUNDS = {r.id: (e, r) for e in ELECTIONS for r in e.rounds}
