"""Results by polling station, read from DIP's files as published.

The parliament's CSV files (Windows-1250, ";") come one per contest and kind of station:

- `02_NN_rezultati.csv`: constituency NN (I–X by residence, XI for voters living abroad), its regular stations;
  `_inozemstvo`: the constituency's voters voting abroad; `_posebna`: special stations (care homes, prisons,
  ships, ...).
- `G3_12_*.csv`: the national minorities (constituency XII), group G (1 Serbian, 2 Hungarian, 3 Italian, 4 Czech and
  Slovak, 5 Austrian, Bulgarian, German, Polish, Roma, Romanian, Rusyn, Russian, Turkish, Ukrainian, Vlach, Jewish,
  6 Albanian, Bosniak, Montenegrin, Macedonian, Slovene). Their voters may vote at any station, so a station's
  registered voters say nothing about its turnout there.

Fifteen columns describe the station and its numbers; then each list, followed by its candidates' preferential
votes (none for the minorities, who vote for candidates). Which column is a list isn't written anywhere: it is the
grouping in which a candidate's preferences never exceed the list's votes and the lists add up to the valid ballots
(`group_columns`).

The president's XLSX files hold one round each, every station in one sheet, a column per candidate and its share.
"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from pathlib import Path

from izbori_hr.elections import ROUNDS, Election, Round

ROMAN = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]
MINORITIES = {  # group code in DIP's file names → (seats, votes a voter may give, name by language)
    "13": (3, 3, {"hr": "srpska nacionalna manjina", "en": "Serb national minority"}),
    "23": (1, 1, {"hr": "mađarska nacionalna manjina", "en": "Hungarian national minority"}),
    "33": (1, 1, {"hr": "talijanska nacionalna manjina", "en": "Italian national minority"}),
    "43": (1, 1, {"hr": "češka i slovačka nacionalna manjina", "en": "Czech and Slovak national minorities"}),
    "53": (1, 1, {"hr": "austrijska, bugarska, njemačka, poljska, romska, rumunjska, rusinska, ruska, turska, "
                        "ukrajinska, vlaška i židovska nacionalna manjina",
                  "en": "Austrian, Bulgarian, German, Polish, Roma, Romanian, Rusyn, Russian, Turkish, Ukrainian, "
                        "Vlach and Jewish national minorities"}),
    "63": (1, 1, {"hr": "albanska, bošnjačka, crnogorska, makedonska i slovenska nacionalna manjina",
                  "en": "Albanian, Bosniak, Montenegrin, Macedonian and Slovene national minorities"}),
}
FIXED = 15  # columns that describe the station and its numbers, before the votes
MAX_CANDIDATES = 14  # a list's candidates in a constituency


@dataclass
class Contestant:
    name: str  # as DIP writes it
    candidates: tuple[str, ...] = ()  # a list's candidates, whose preferential votes follow it


@dataclass
class Contest:
    id: str  # "I" … "XI", "XII-1" … "XII-6", or "RH" for the president
    name: dict  # by language
    seats: int
    contestants: list[Contestant]
    votes_per_voter: int = 1  # the Serb minority's voters may vote for up to three
    lists: bool = True  # lists with candidates (the constituencies) or candidates alone
    threshold: float = 0.05  # share of the valid votes a list needs for a seat (the constituencies)

    @property
    def minority(self) -> bool:
        return self.id.startswith("XII")


@dataclass
class Station:
    contest: str
    kind: str  # "domestic", "abroad" or "special"
    county_no: str
    county: str
    place_kind: str  # "grad", "općina" or "država"
    municipality: str  # city, municipality or, abroad, country
    number: str  # the station's number in its municipality (Rbr BM)
    name: str
    location: str
    address: str
    registered: int
    voted: int  # voters who signed the register
    ballots: int  # ballots in the box
    valid: int
    invalid: int
    votes: list[int]
    prefs: list[list[int]] = field(default_factory=list)  # per list, its candidates' preferential votes
    unit: str = ""  # the parliament: the constituency its voters live in ("I" … "XI"); the minorities' special
    # stations have a row for each

    @property
    def mun_key(self) -> str:
        """The municipality across this archive: county and name at home, the country abroad."""
        if self.kind == "abroad":
            return f"ino-{slug(self.municipality)}"
        return f"{self.county_no}-{slug(self.municipality)}" if self.county_no else slug(self.municipality)

    @property
    def key(self) -> str:
        """The station within its contest. The parliament numbers its special stations apart from the regular ones
        ("p"), and gives the minorities' special stations a row per constituency their voters live in; the
        president numbers them from 901. Zagreb's parts of constituencies I, II and VI number their stations each
        from 1, under their own names."""
        if self.kind != "special" or self.contest == "RH":
            return f"{self.mun_key}/{self.number or '-'}"
        key = f"{self.mun_key}/p{self.number}"
        return f"{key}-{self.unit.lower()}" if self.contest.startswith("XII") and self.unit else key

    @property
    def turnout(self) -> float | None:
        return self.voted / self.registered if self.registered else None


@dataclass
class RoundResults:
    election: Election
    round: Round
    contests: dict[str, Contest]
    stations: list[Station]
    notes: tuple[str, ...] = ()  # what DIP's files of this round lack, as keys of the site's texts

    @property
    def id(self) -> str:
        return self.round.id

    def of(self, contest: str) -> list[Station]:
        return [s for s in self.stations if s.contest == contest]


def slug(text: str) -> str:
    table = str.maketrans("ČĆŽŠĐčćžšđ", "CCZSDcczsd")
    return re.sub(r"[^a-z0-9]+", "-", text.translate(table).lower()).strip("-")


def _county(value) -> str:
    """The county's number without DIP's leading zero (the president's files write "01", the parliament's "1")."""
    value = str(value).strip()
    return str(int(value)) if value.isdigit() else value


def _number(value) -> str:
    """The station's number without DIP's leading zeros ("001" in the parliament's files, 1 in the president's)."""
    value = str(value).strip()
    return str(int(value)) if value.isdigit() else value


def _int(value) -> int:
    if value is None or value == "":
        return 0
    return int(float(value)) if isinstance(value, (int, float)) else int(str(value).strip() or 0)


def group_columns(header: list[str], rows: list[list[int]], valid: list[int], tolerance: int = 0) -> list[int]:
    """Which vote columns are lists: the grouping (list, then up to MAX_CANDIDATES candidates) in which no candidate
    has more preferential votes than the list, nor all of them together, and the lists add up to the valid ballots.
    A station or two where DIP's numbers don't add up is allowed (`tolerance`): that is a flag, not another
    grouping. Each list takes as many candidates as fit, fewer only when the sums say so. Raises ValueError when no
    grouping fits."""
    n, m = len(header), len(rows)
    # how many columns after a list can be its candidates (the more, the more stations must hold)
    reach = []
    for start in range(n):
        k, bad, totals = 0, [0] * m, [0] * m
        while k < MAX_CANDIDATES and start + k + 1 < n:
            c = start + k + 1
            fails = 0
            for r in range(m):
                totals[r] += rows[r][c]
                if not bad[r] and (rows[r][c] > rows[r][start] or totals[r] > rows[r][start]):
                    bad[r] = 1
                fails += bad[r]
            if fails > tolerance:
                break
            k += 1
        reach.append(k)

    def search(start: int, lists: list[int], sums: list[int]) -> list[int] | None:
        if start == n:
            return lists if sum(1 for r in range(m) if sums[r] != valid[r]) <= tolerance else None
        sums = [sums[r] + rows[r][start] for r in range(m)]
        if sum(1 for r in range(m) if sums[r] > valid[r]) > tolerance:
            return None
        for k in range(min(reach[start], n - start - 1), -1, -1):
            found = search(start + 1 + k, lists + [start], sums)
            if found is not None:
                return found
        return None

    found = search(0, [], [0] * m)
    if found is None:
        raise ValueError(f"no grouping of {n} columns fits")
    return found


def _read_csv(path: Path) -> list[list[str]]:
    return list(csv.reader(io.StringIO(path.read_bytes().decode("cp1250")), delimiter=";"))


FILE = re.compile(r"(\d{2,3})_(\d\d)_rezultati(?:_(inozemstvo|posebna))?\.csv$")


def contest_of(first: str, second: str) -> str:
    """The contest a file holds, from its name: "02_04" (IV), "13_12" (the Serb minority) since 2020 and in 2015;
    "004_00" (IV), "012_13" (the Serb minority) in 2016."""
    if len(first) == 3:
        unit = int(first)
        return f"XII-{second[0]}" if unit == 12 else ROMAN[unit]
    return f"XII-{first[0]}" if second == "12" else ROMAN[int(second)]


def minority_contest(cid: str, names: list[str]) -> Contest:
    seats, per_voter, mname = MINORITIES[cid.split("-")[1] + "3"]
    return Contest(cid, {lang: f"XII. izborna jedinica – {n}" if lang == "hr" else f"Constituency XII – {n}"
                         for lang, n in mname.items()},
                   seats, [Contestant(clean(x)) for x in names], per_voter, lists=False, threshold=0.0)


def list_contest(cid: str, election: Election, contestants: list[Contestant]) -> Contest:
    return Contest(cid, {"hr": f"{cid}. izborna jedinica", "en": f"Constituency {cid}"},
                   election.xi_seats if cid == "XI" else 14, contestants)


def contest_order(contests: dict[str, Contest]) -> dict[str, Contest]:
    order = {c: i for i, c in enumerate(ROMAN[1:12] + [f"XII-{g}" for g in "123456"])}
    return dict(sorted(contests.items(), key=lambda kv: order[kv[0]]))


def clean(text) -> str:
    """A name as DIP wrote it, without line breaks, padding or a "Kandidat:" label."""
    text = str(text or "").replace("-\n", "-").replace("\n", " ")
    text = re.sub(r"^\s*kandidat:\s*", "", text, flags=re.I)
    return re.sub(r"\s+", " ", text).strip()


def read_parliament(election: Election, round_: Round, raw: Path) -> RoundResults:
    files = sorted((raw / "CSV").glob("*.csv"))
    tables: dict[str, list[tuple[str, list[list[str]]]]] = {}
    for f in files:
        m = FILE.search(f.name)
        if not m:
            continue
        first, second, suffix = m.groups()
        contest = contest_of(first, second)
        kind = {"inozemstvo": "abroad", "posebna": "special"}.get(suffix or "", "domestic")
        tables.setdefault(contest, []).append((kind, _read_csv(f)))
    contests: dict[str, Contest] = {}
    stations: list[Station] = []
    for cid, parts in tables.items():
        header = parts[0][1][0]
        names = header[FIXED:]
        minority = cid.startswith("XII")
        if minority:
            contest = minority_contest(cid, names)
            list_cols = list(range(len(names)))
        else:
            # the grouping comes from the file with the most stations; every file of the contest shares its header
            kind, rows = max(parts, key=lambda p: len(p[1]))
            votes = [[_int(x) for x in r[FIXED:]] for r in rows[1:] if len(r) > FIXED and r[6].strip()]
            valid = [_int(r[13]) for r in rows[1:] if len(r) > FIXED and r[6].strip()]
            list_cols = group_columns(names, votes, valid, tolerance=max(1, len(votes) // 200))
            bounds = list_cols + [len(names)]
            contest = list_contest(cid, election, [Contestant(clean(names[a]), tuple(clean(x) for x in names[a + 1:b]))
                                                   for a, b in zip(bounds, bounds[1:])])
        contests[cid] = contest
        for kind, rows in parts:
            if rows[0][FIXED:] != header[FIXED:]:  # 2015's special stations name their first columns differently
                raise ValueError(f"{cid}: the files name the lists differently")
            for r in rows[1:]:
                if len(r) <= FIXED or not (r[5].strip() or r[6].strip()):
                    continue  # a blank row (XI's special stations: there were none)
                values = [_int(x) for x in r[FIXED:]]
                place_kind = r[4].strip()
                stations.append(Station(
                    contest=cid, kind="abroad" if place_kind == "država" else kind, county_no=_county(r[2]),
                    county=r[3].strip(), place_kind=place_kind, municipality=r[5].strip(), number=_number(r[6]),
                    name=r[7].strip(), location=r[8].strip(), address=r[9].strip(), registered=_int(r[10]),
                    voted=_int(r[11]), ballots=_int(r[12]), valid=_int(r[13]), invalid=_int(r[14]),
                    votes=[values[c] for c in list_cols],
                    prefs=[] if minority else [values[a + 1:b] for a, b in zip(list_cols, list_cols[1:] + [len(values)])],
                    unit=ROMAN[int(r[0])] if r[0].strip().isdigit() else ""))
    return RoundResults(election, round_, contest_order(contests), stations)


def round_file(raw: Path, round_: Round) -> Path:
    """The file holding a round's results, wherever DIP put it in the zip."""
    return next(p for pattern in round_.files for p in sorted(raw.rglob(pattern)))


def read_president(election: Election, round_: Round, raw: Path) -> RoundResults:
    import openpyxl
    path = round_file(raw, round_)
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    rows = list(wb.worksheets[0].iter_rows(values_only=True))
    head = next(i for i, r in enumerate(rows) if r and r[0] == "Rbr.županije")
    header = [str(x or "") for x in rows[head]]
    cand_cols = [i for i, h in enumerate(header) if i >= 13 and h.strip() and h.strip() != "(%)"]
    contest = president_contest([header[i] for i in cand_cols])
    stations = []
    for r in rows[head + 1:]:
        if not r or r[4] in (None, ""):
            continue
        cells = ["" if x is None else x for x in r]
        place_kind = str(cells[2]).strip()
        number = _number(cells[4])
        # special stations (care homes, prisons) are numbered from 901 in their municipality
        kind = "abroad" if place_kind == "država" else "special" if number.isdigit() and int(number) >= 900 else "domestic"
        stations.append(Station(
            contest="RH", kind=kind, county_no=_county(cells[0]),
            county=str(cells[1]).strip(), place_kind=place_kind, municipality=str(cells[3]).strip(),
            number=number, name=str(cells[5]).strip(), location=str(cells[6]).strip(),
            address=str(cells[7]).strip(), registered=_int(cells[8]), voted=_int(cells[9]), ballots=_int(cells[10]),
            valid=_int(cells[11]), invalid=_int(cells[12]), votes=[_int(cells[i]) for i in cand_cols]))
    return RoundResults(election, round_, {"RH": contest}, stations)


def president_contest(names: list[str]) -> Contest:
    return Contest("RH", {"hr": "Republika Hrvatska", "en": "Croatia"}, 1, [Contestant(clean(n)) for n in names],
                   lists=False, threshold=0.0)


def load(round_id: str, data_dir: Path) -> RoundResults:
    """A round as DIP published it. Each era of DIP's files has its own layout (`formats`)."""
    from izbori_hr import formats
    election, round_ = ROUNDS[round_id]
    raw = data_dir / election.id / "raw"
    if election.kind == "parliament":
        if any((raw / "CSV").glob("*_rezultati.csv")):
            return read_parliament(election, round_, raw)
        return formats.read_parliament_old(election, round_, raw)
    if formats.has_row(round_file(raw, round_), "Rbr.županije"):
        return read_president(election, round_, raw)
    return formats.read_president_old(election, round_, raw)
