"""DIP's older layouts: the parliament before 2015 and the president before 2014.

Each era wrote its files differently, but the columns are named, so they are read by their names (`ROLES`):

- parliament 2007 and 2011: per constituency, a file for regular stations, special stations, stations abroad, and
  sums by municipality (not read); a row of ballot numbers under the header, sums at the end;
- parliament 2003: per constituency, regular and "mixed" stations (embassies, displaced persons, care homes), whose
  voters belong to the constituency wherever they vote; one column of voters, by the ballots;
- parliament 2000: constituencies I–X only, lists by number, their names in a separate file;
- president 2009 and 2005: one sheet a round, the country and its stations abroad as a county ("INOZEMSTVO");
- president 2000: a sheet for Croatia and one for abroad, by country only.

What a file lacks is not made up: a round without ballots in the box counts the valid and invalid ballots instead,
one without the register's count of voters takes the ballots, and the round says so (`RoundResults.notes`).
"""

from __future__ import annotations

import csv
import io
import re
from functools import lru_cache
from pathlib import Path

from izbori_hr.elections import ROUNDS, Election, Round
from izbori_hr.results import (ROMAN, Contestant, RoundResults, Station, clean, contest_order, list_contest,
                               minority_contest, president_contest, slug)

ROLES = [  # what a column holds, by its name in DIP's files (lower case, spaces collapsed)
    ("unit_city", r"izborna jedinica grada"),
    ("unit", r"izborna jedinica"),
    ("municipality", r"grad\s*/\s*općin\w*(\s*/\s*država)?|grad/općina|država"),
    ("number", r"bm rbr|(redni )?broj bi\w*čkog mjesta|broj bm|biračko mjesto"),  # 2005: "biačkog"
    ("name", r"bm naziv"),
    ("location", r"bm lokacija"),
    ("address", r"bm adresa"),
    ("registered", r"(ukupno|broj|upisano) birača"),
    ("voted", r"glasovalo (ukupno|birača)"),
    ("ballots", r"glasovalo (birača )?\((prema|po) listić\w*\)|listići ukupno"),
    ("valid", r"listići važeći|važećih listića|važeći listići|broj važećih listića"),
    ("invalid", r"listići nevažeći|nevažećih listića|nevažeći listići|broj nevažećih listića"),
]
FIRST_VOTES = "invalid"  # the votes start after this column


def count(value) -> int:
    """A number as DIP wrote it: blank for none, "1.335" with a thousands point."""
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip().replace(".", "").replace(" ", "")
    return int(text) if text.lstrip("-").isdigit() else 0


def _norm(text) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip().lower()


def roles(header: list) -> dict[str, int]:
    found: dict[str, int] = {}
    for i, h in enumerate(header):
        h = _norm(h)
        for role, pattern in ROLES:
            if role not in found and re.fullmatch(pattern, h):
                found[role] = i
                break
    return found


def _read_csv(path: Path) -> list[list[str]]:
    text = path.read_bytes().decode("cp1250")
    delimiter = ";" if text.count(";") >= text.count(",") else ","
    return list(csv.reader(io.StringIO(text), delimiter=delimiter))


def xlsx_rows(path: Path, sheet: int = 0) -> list[tuple]:
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    return list(wb.worksheets[sheet].iter_rows(values_only=True)) if sheet < len(wb.worksheets) else []


def has_row(path: Path, first: str) -> bool:
    """Does one of the sheet's first rows start with this (the header of the president's files since 2014)?"""
    if path.suffix != ".xlsx":
        return False
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    return any(row and str(row[0] or "").strip() == first
               for row in wb.worksheets[0].iter_rows(values_only=True, max_row=10))


def number_of(value) -> str:
    text = str(value if value is not None else "").strip()
    if isinstance(value, float) and value.is_integer():
        text = str(int(value))
    return str(int(text)) if text.isdigit() else ""


# ---- counties: the older parliamentary files name the municipality only ------------------------------------------

@lru_cache(maxsize=4)
def county_lookup(data_dir: str) -> dict[str, tuple[str, str]]:
    """Municipality → (county number, county), from the presidential rounds that name both: the newest first."""
    out: dict[str, tuple[str, str]] = {}
    twice: set[str] = set()  # names of two municipalities (Otok): left without a county
    for round_id in ("predsjednik-2024-1", "predsjednik-2019-1", "predsjednik-2014-1", "predsjednik-2009-1"):
        if round_id not in ROUNDS:
            continue
        election, _ = ROUNDS[round_id]
        if not (Path(data_dir) / election.id / "raw").is_dir():
            continue
        from izbori_hr.results import load
        seen: dict[str, str] = {}
        for s in load(round_id, Path(data_dir)).stations:
            if s.kind != "abroad" and s.county_no:
                key = slug(s.municipality)
                if seen.setdefault(key, s.county_no) != s.county_no:
                    twice.add(key)
                out.setdefault(key, (s.county_no, s.county))
    return {k: v for k, v in out.items() if k not in twice}


@lru_cache(maxsize=4)
def county_numbers(data_dir: str) -> dict[str, tuple[str, str]]:
    """County name, without "županija" → (number, the name as the newest files write it)."""
    out = {}
    for no, county in county_lookup(data_dir).values():
        out[_county_key(county)] = (no, county)
    return out


def _county_key(name: str) -> str:
    return slug(re.sub(r"\s*županija\s*$", "", str(name or "").strip(), flags=re.I))


ALIASES = {  # municipalities renamed since, as the older files write them
    "barilovici": "barilovic", "donji-martijanec": "martijanec", "sveta-nedjelja": "sveta-nedelja",
}
PLACES = {"otok-vinkovci": ("16", "VUKOVARSKO-SRIJEMSKA ŽUPANIJA")}  # two municipalities are called Otok


def place(name: str, data_dir: Path) -> tuple[str, str]:
    lookup = county_lookup(str(data_dir))
    key = ALIASES.get(slug(name), slug(name))
    if key in PLACES:
        return PLACES[key]
    found = lookup.get(key)
    if found:
        return found
    longer = {v for k, v in lookup.items() if k.startswith(key)}  # 2011 cuts long names: "… - CASTELLIERE-S. D"
    if len(longer) == 1:
        return longer.pop()
    if slug(name).startswith("zagreb"):  # Zagreb's parts in the parliamentary files
        return "21", "GRAD ZAGREB"
    return "", ""


# ---- the parliament ---------------------------------------------------------------------------------------------

def _report(rows: list[list[str]], cid: str, kind: str, data_dir: Path, file_unit: str = "",
            mixed: bool = False) -> tuple[list[str], list[Station]]:
    """A report of DIP's (2000–2011): find the header by its column names, read every row with a station number."""
    head = next(i for i, r in enumerate(rows[:5]) if {"municipality", "number", "valid", "invalid"} <= roles(r).keys())
    cols = roles(rows[head])
    first = cols[FIRST_VOTES] + 1
    names = [clean(h) for h in rows[head][first:]]
    while names and not names[-1]:
        names.pop()
    abroad_header = _norm(rows[head][cols["municipality"]]) == "država"
    stations = []
    for r in rows[head + 1:]:
        if len(r) <= cols["invalid"]:
            continue
        number = number_of(r[cols["number"]])
        municipality = clean(r[cols["municipality"]])
        if not number or not municipality:
            continue  # the ballot numbers under the header, blank rows, sums
        row_kind = kind
        if abroad_header and kind == "domestic":
            row_kind = "abroad"
        if mixed:  # 2003: embassies, clubs abroad, displaced persons, institutions, a constituency's voters each
            row_kind = "special"
        if municipality.upper() == "DIJASPORA U RH":
            row_kind = "special"  # voters living abroad, voting in Croatia
        get = lambda role: count(r[cols[role]]) if role in cols and cols[role] < len(r) else None  # noqa: E731
        valid, invalid = get("valid") or 0, get("invalid") or 0
        voted, ballots = get("voted"), get("ballots")
        if ballots is None:
            ballots = valid + invalid if voted is None else voted
        if voted is None:
            voted = ballots
        county_no, county = ("", "") if row_kind == "abroad" else place(municipality, data_dir)
        text = lambda role: clean(r[cols[role]]) if role in cols and cols[role] < len(r) else ""  # noqa: E731
        stations.append(Station(
            contest=cid, kind=row_kind, county_no=county_no, county=county,
            place_kind="država" if row_kind == "abroad" else "", municipality=municipality, number=number,
            name=text("name"), location=text("location"), address=text("address"),
            registered=get("registered") or 0, voted=voted, ballots=ballots, valid=valid, invalid=invalid,
            votes=[count(x) for x in (r[first:first + len(names)] + [""] * len(names))[:len(names)]],
            unit=file_unit))
    return names, stations


FILE_2007 = re.compile(r"^\d+_(?P<roman>[IVX]+)(?:_nm(?P<g>\d))?_izborna_jedinica_(?P<part>.+)\.csv$")
FILE_2003 = re.compile(r"^(?P<roman>[IVX]+) izborna jedinica(?: - (?P<g>\d))?_(?P<part>.+?)\s*\.csv$")
PARTS = {  # what a file holds, by the end of its name → kind of station (None: sums, not read)
    "redovita_bm": "domestic", "posebna_bm": "special", "bm_inozemstvo": "abroad", "bm_u_inozemstvu": "abroad",
    "dijaspora_u_rh": "special", "bm_u_rh": "special", "gradovi-opcine": None, "grdovi-opcine": None,
    "drzave": None,
}


def _contest_id(roman: str, group: str | None) -> str:
    return f"XII-{group}" if roman == "XII" else roman


def read_parliament_old(election: Election, round_: Round, raw: Path) -> RoundResults:
    data_dir = raw.parent.parent
    parts: dict[str, list[tuple[list[str], list[Station]]]] = {}
    notes: list[str] = []
    files = sorted({p for pattern in round_.files for p in raw.rglob(pattern)})
    for path in files:
        name = path.name
        if m := FILE_2007.match(name):  # 2007, 2011
            kind = PARTS.get(m["part"].lower())
            if kind is None:
                continue
            cid = _contest_id(m["roman"], m["g"])
            parts.setdefault(cid, []).append(_report(_read_csv(path), cid, kind, data_dir))
        elif m := FILE_2003.match(name):  # 2003
            part = m["part"].lower()
            if "sumari" in part:
                continue
            cid = _contest_id(m["roman"], m["g"])
            mixed = part.startswith("mješovita")
            parts.setdefault(cid, []).append(_report(_read_csv(path), cid, "domestic", data_dir, mixed=mixed))
        elif m := re.match(r"^ij(\d\d)_ij\d\d\.csv$", name):  # 2000
            cid = ROMAN[int(m[1])]
            names, stations = _report(_read_csv(path), cid, "domestic", data_dir)
            lists = _lists_2000(path.with_name(f"ij{m[1]}_Stranke.csv"))
            if names != [str(i + 1) for i in range(len(names))] or len(lists) < len(names):
                raise ValueError(f"{name}: {len(names)} columns of votes, {len(lists)} lists")
            # V names 26 lists and has columns for 25, which add up to the valid ballots: the last has none
            lists = lists[:len(names)]
            parts.setdefault(cid, []).append((lists, stations))
    if not parts:
        raise ValueError(f"{election.id}: no file read")
    contests, stations = {}, []
    for cid, found in parts.items():
        # the names of the file with most stations: the others may cut them (2007) or break their lines (2003)
        names = max(found, key=lambda f: len(f[1]))[0]
        for other, _ in found:
            if len(other) != len(names) or not all(_same(a, b) for a, b in zip(other, names)):
                raise ValueError(f"{election.id} {cid}: the files name the contestants differently")
        if cid.startswith("XII"):
            contests[cid] = minority_contest(cid, names)
        else:
            contests[cid] = list_contest(cid, election, [Contestant(n) for n in names])
        for _, rows in found:
            stations.extend(rows)
    if election.id == "sabor-2000":
        notes.append("no_xi_xii")
    if not any(s.voted != s.ballots for s in stations):
        notes.append("voted_from_ballots" if election.id == "sabor-2003" else "ballots_derived")
    return RoundResults(election, round_, contest_order(contests), stations, tuple(notes))


def _same(a: str, b: str) -> bool:
    a, b = (re.sub(r"[\W_]+", "", x.lower()) for x in (a, b))
    return a.startswith(b) or b.startswith(a)


def _lists_2000(path: Path) -> list[str]:
    """2000's lists: a number, the parties of the list a line each, and last its leader (not in capitals)."""
    lists: list[list[str]] = []
    for r in _read_csv(path)[1:]:
        if len(r) < 2 or not r[1].strip():
            continue
        if r[0].strip():
            lists.append([])
        if lists:
            lists[-1].append(clean(r[1]))
    out = []
    for parts in lists:
        parties = [p for p in parts if p.upper() == p]
        leaders = [p for p in parts if p.upper() != p]
        out.append(", ".join(parties) + (f", Nositelj liste: {leaders[-1]}" if leaders else ""))
    return out


# ---- the president ----------------------------------------------------------------------------------------------

def _strip_kind(name: str) -> tuple[str, str]:
    """2005 writes "GRAD DUGO SELO", "OPĆINA BRCKOVLJANI"."""
    for prefix, kind in (("GRAD ", "grad"), ("OPĆINA ", "općina")):
        if name.upper().startswith(prefix) and name.upper() != "GRAD ZAGREB":
            return name[len(prefix):].strip(), kind
    return name, ""


def read_president_old(election: Election, round_: Round, raw: Path) -> RoundResults:
    from izbori_hr.results import round_file
    path = round_file(raw, round_)
    rows = xlsx_rows(path)
    head = next(i for i, r in enumerate(rows[:10]) if r and {"number", "valid", "invalid"} <= roles(list(r)).keys())
    header = [str(c or "") for c in rows[head]]
    cols = roles(header)
    first = cols[FIRST_VOTES] + 1
    cand = [i for i in range(first, len(header)) if clean(header[i]) and clean(header[i]) not in ("%", "(%)")]
    contest = president_contest([header[i] for i in cand])
    data_dir = raw.parent.parent
    county_col = next((i for i, h in enumerate(header) if _norm(h).startswith("županija")), None)
    county_no_col = next((i for i, h in enumerate(header) if _norm(h) in ("rbr. županije", "redni broj županije")),
                         None)
    kind_col = next((i for i, h in enumerate(header) if _norm(h) == "grad/općina"), None)  # 2000: GRAD / OPĆINA
    name_col = next((i for i, h in enumerate(header) if _norm(h) == "naziv"), None)  # 2000: the name
    notes = []
    stations = []
    for r in rows[head + 1:]:
        if not r or len(r) <= cols["invalid"]:
            continue
        number = number_of(r[cols["number"]])
        if not number:
            continue  # sums
        county = clean(r[county_col]) if county_col is not None else ""
        abroad = county.upper().startswith("INOZEMSTVO")
        if name_col is not None:
            municipality, place_kind = clean(r[name_col]), clean(r[kind_col]).lower()
        else:
            municipality, place_kind = _strip_kind(clean(r[cols["municipality"]]))
        if abroad:
            county_no, county, place_kind = "", "inozemstvo", "država"
        elif county_no_col is not None and number_of(r[county_no_col]):
            county_no = number_of(r[county_no_col])
        else:
            county_no, county = county_numbers(str(data_dir)).get(_county_key(county), ("", county))
        valid, invalid = count(r[cols["valid"]]), count(r[cols["invalid"]])
        voted = count(r[cols["voted"]]) if "voted" in cols else None
        ballots = count(r[cols["ballots"]]) if "ballots" in cols else None
        stations.append(Station(
            contest="RH", kind="abroad" if abroad else "special" if int(number) >= 900 else "domestic",
            county_no=county_no, county=county, place_kind=place_kind, municipality=municipality, number=number,
            name="", location="", address="", registered=count(r[cols["registered"]]),
            voted=voted if voted is not None else ballots, ballots=ballots if ballots is not None else valid + invalid,
            valid=valid, invalid=invalid, votes=[count(r[i]) for i in cand]))
    if "ballots" not in cols:
        notes.append("ballots_derived")
    if "voted" not in cols:
        notes.append("voted_from_ballots")
    abroad_rows = xlsx_rows(path, 1)  # 2000: abroad by country, on a sheet of its own
    if abroad_rows:
        h = [str(c or "") for c in abroad_rows[0]]
        c2 = roles(h)
        names = [clean(h[i]) for i in range(c2[FIRST_VOTES] + 1, len(h)) if clean(h[i])]
        if names != [c.name for c in contest.contestants]:
            raise ValueError(f"{path.name}: the sheets name the candidates differently")
        for r in abroad_rows[1:]:
            country = clean(r[c2["municipality"]]) if r else ""
            if not country or country.upper().startswith(("UKUPNO", "TOTAL")):
                continue
            valid, invalid = count(r[c2["valid"]]), count(r[c2["invalid"]])
            stations.append(Station(
                contest="RH", kind="abroad", county_no="", county="inozemstvo", place_kind="država",
                municipality=country, number="", name="", location="", address="",
                registered=count(r[c2["registered"]]), voted=count(r[c2["voted"]]), ballots=valid + invalid,
                valid=valid, invalid=invalid,
                votes=[count(r[i]) for i in range(c2[FIRST_VOTES] + 1, c2[FIRST_VOTES] + 1 + len(names))]))
        notes.append("abroad_by_country")
    return RoundResults(election, round_, {"RH": contest}, stations, tuple(notes))
