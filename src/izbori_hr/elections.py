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

    @property
    def zip_url(self) -> str:
        return f"{ARCHIVE}data/{self.path}/zip/rezultati.zip"

    @property
    def page_url(self) -> str:
        return f"{ARCHIVE}#/app/{self.page}"


ELECTIONS = (
    Election(
        id="sabor-2024", kind="parliament", path="parlament/2024", page="parlament-2024",
        title={"hr": "Izbori za zastupnike u Hrvatski sabor 2024.", "en": "Croatian parliamentary election 2024"},
        rounds=(Round("sabor-2024", 1, "2024-04-17", ("CSV/*.csv",)),),
        keep=("CSV/*.csv",),  # the XLSX files hold the same numbers
    ),
    Election(
        id="predsjednik-2024", kind="president", path="predsjednik/2024", page="predsjednik-2024",
        title={"hr": "Izbori za predsjednika Republike Hrvatske 2024./2025.",
               "en": "Croatian presidential election 2024–25"},
        rounds=(Round("predsjednik-2024-1", 1, "2024-12-29", ("*/1_krug/*.xlsx",)),
                Round("predsjednik-2024-2", 2, "2025-01-12", ("*/2_krug/*.xlsx",))),
        keep=("*.xlsx",),
    ),
)

BY_ID = {e.id: e for e in ELECTIONS}
ROUNDS = {r.id: (e, r) for e in ELECTIONS for r in e.rounds}
