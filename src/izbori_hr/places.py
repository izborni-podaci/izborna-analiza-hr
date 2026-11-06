"""Municipalities and polling places followed through every archived election.

**Municipalities.** A round keys its municipalities by county and name (`Station.mun_key`), and names drift: "SV.
FILIP I JAKOV" in 2000, "SVETI FILIP I JAKOV" later; Funtana became "FUNTANA - FONTANE"; the parliament splits
Zagreb into parts by constituency (2015–2024) or by districts (2003–2011), while the president counts the City of
Zagreb whole. `MunicipalityKeys` gives every round's municipality the key of its newest name, and every part of
Zagreb the City's.

**Places.** Regular polling stations at home (abroad and special stations are institutions or groups of voters, not
places) are joined going forward in time, within their municipality, as the Serbian archive does:

1. by address (street and number), since 2011;
2. by the building (DIP's "lokacija");
3. by the settlement or area it serves (DIP's "naziv");
4. by number, never where the addresses or buildings clearly differ, nor where one register is more than twice
   the other (an area redrawn under an old number; of the stations joined by address, 1.6% change that much), and
   only within one numbering: Zagreb's parts of the parliamentary
   files number their stations from 1, apart from the City's numbers.

Stations that share an address or a name are paired with the places last seen there (not those that ended
earlier), by equal number first; then, at one address, by the nearest number (a school that gained a station keeps
its old one), and under one name in number order only when as many are left on each side. Names are compared by
their telling words ("Osnovna škola" tells nothing; the street does).
Because matching runs forward, a new election never changes how the earlier ones were joined.
"""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field

from izbori_hr.results import RoundResults, Station, slug

GENERIC = {
    "DOM", "DOMA", "DRUSTVENI", "DRUSTVENOG", "DRUSTVENA", "SKOLA", "SKOLE", "OSNOVNA", "OSNOVNE", "PODRUCNA",
    "PODRUCNE", "SREDNJA", "PROSTORIJE", "PROSTORIJA", "PROSTOR", "MJESTO", "BIRACKO", "BIRALISTE", "VATROGASNI",
    "VATROGASNOG", "DVD", "KUCA", "KUCI", "MJESNOG", "MJESNI", "MJESNA", "ODBORA", "ODBOR", "ZAJEDNICE",
    "ZAJEDNICA", "ZGRADA", "ZGRADI", "KULTURE", "OPCINE", "OPCINSKA", "GRADSKA", "GRADSKE", "DJECJI", "DJECJEG",
    "VRTIC", "VRTICA", "CENTAR", "DVORANA", "DVORANE", "UCIONICA", "VIJECNICA", "PRIVATNA", "PRIVATNI", "BIVSE",
    "BIVSA", "PRIZEMLJE", "KAT", "ULAZ", "ULICA", "TRG", "CESTA", "BROJ",
}
HOW = ("address", "location", "name", "number")

# names as the older files write them → the newest name's slug
RENAMED = {
    "sveta-nedjelja": "sveta-nedelja", "skabrnje": "skabrnja", "murter": "murter-kornati",
    "funtana": "funtana-fontane", "tar-vabriga": "tar-vabriga-torre-abrega",
    "kastelir-labinci-castelliere-s-d": "kastelir-labinci-castelliere-s-domenica", "zagreb": "grad-zagreb",
    "barilovici": "barilovic", "donji-martijanec": "martijanec", "otok-vinkovci": "otok",
}
ZAGREB = "21-grad-zagreb"


def _fold(text: str) -> str:
    s = (text or "").upper().replace("Đ", "DJ")
    return "".join(ch for ch in unicodedata.normalize("NFD", s) if not unicodedata.combining(ch))


def words(text: str) -> frozenset[str]:
    """The words that tell one place from another: names of three letters or more, and house numbers."""
    s = _fold(text)
    found = set(re.findall(r"[A-Z]{3,}", s)) | set(re.findall(r"\b\d+[A-Z]?\b", s))
    return frozenset(found - GENERIC)


def _order(number: str) -> tuple[int, str]:
    return (int(number), "") if number.isdigit() else (10 ** 9, number)


def zagreb_part(s: Station) -> bool:
    """A part of Zagreb in the parliamentary files ("ZAGREB - I. IZBORNA JEDINICA", "ZAGREB-CENTAR,ZAPAD")."""
    return s.county_no == "21" and slug(s.municipality) not in ("grad-zagreb", "zagreb")


class MunicipalityKeys:
    """One key per municipality across every round: the county and the newest name. Istria's municipalities have
    had bilingual names since 2011 ("NOVIGRAD - CITTANOVA"); the older files write the Croatian one."""

    def __init__(self, rounds: list[RoundResults]):
        """rounds: oldest first."""
        counties: dict[str, set[str]] = defaultdict(set)
        self.bilingual: dict[tuple[str, str], str] = {}  # (county, the Croatian name) → the newest name
        for rnd in rounds:
            for s in rnd.stations:
                if s.kind != "abroad" and s.county_no and not zagreb_part(s):
                    counties[self._name(s.municipality)].add(s.county_no)
                    if " - " in s.municipality:
                        self.bilingual[(s.county_no, slug(s.municipality.split(" - ")[0]))] = slug(s.municipality)
        # name slug → county number, for rows that name the municipality only; never a name two municipalities
        # share (Otok, Privlaka, Novigrad)
        self.known = {name: next(iter(c)) for name, c in counties.items() if len(c) == 1}

    @staticmethod
    def _name(municipality: str) -> str:
        key = slug(municipality)
        return RENAMED.get(key, key)

    def __call__(self, s: Station) -> str:
        if s.kind == "abroad":
            return s.mun_key
        if zagreb_part(s) or (s.county_no in ("", "21") and slug(s.municipality) == "zagreb"):
            return ZAGREB
        name = self._name(s.municipality)
        if name.startswith("sv-"):  # "SV. FILIP I JAKOV", "SV. KRIŽ ZAČRETJE"
            name = next((n for n in (f"sveti-{name[3:]}", f"sveta-{name[3:]}", f"sveto-{name[3:]}")
                         if n in self.known), name)
        county = s.county_no or self.known.get(name, "")
        name = self.bilingual.get((county, name), name)
        return f"{county}-{name}" if county else name

    @staticmethod
    def placed(code: str) -> bool:
        """A municipality at home or a country abroad: not 2003's mixed stations, displaced persons, the diaspora
        voting at home, nor a special station whose name two municipalities share."""
        return code[:1].isdigit() or code.startswith("ino-")


@dataclass
class Place:
    code: str  # municipality key across rounds
    rounds: list[str] = field(default_factory=list)  # round ids, newest first
    stations: dict[str, Station] = field(default_factory=dict)
    how: dict[str, str] = field(default_factory=dict)  # round id → how it was joined to the earlier ones
    id: str = ""
    number: str = ""
    scope: str = ""  # the numbering the latest number belongs to
    addr: frozenset = frozenset()
    location: frozenset = frozenset()
    name: frozenset = frozenset()
    registered: int = 0
    nearest: int = -1

    @property
    def newest(self) -> Station:
        return self.stations[self.rounds[0]]

    @property
    def former_numbers(self) -> list[str]:
        now = self.newest.number
        return list(dict.fromkeys(self.stations[r].number for r in self.rounds[1:]
                                  if self.stations[r].number != now))

    def add(self, rid: str, s: Station, how: str, position: int, scope: str) -> None:
        self.rounds.insert(0, rid)
        self.stations[rid] = s
        self.how[rid] = how
        self.number, self.scope, self.nearest, self.registered = s.number, scope, position, s.registered
        self.addr = words(s.address) or self.addr
        self.location = words(s.location) or self.location
        self.name = words(s.name) or self.name


@dataclass
class Places:
    places: list[Place]
    at: dict[tuple[str, str], Place]  # (round id, station key) → place

    def of(self, rid: str, key: str) -> Place | None:
        return self.at.get((rid, key))

    def in_municipality(self, code: str) -> list[Place]:
        return [p for p in self.places if p.code == code]


def _differ(a: frozenset, b: frozenset) -> bool:
    return bool(a and b and not a & b)


SIZE = 2.0  # a number never joins stations where one register is more than twice the other


def _resized(a: int, b: int) -> bool:
    return bool(a and b and max(a, b) > SIZE * min(a, b))


def _pair(places: list[Place], stations: list[tuple[Station, str]], how: str) -> list[tuple[Place, Station]]:
    """Places and stations sharing an address or a name: the places seen there last, equal numbers in one numbering
    first. Then at one address the nearest numbers, and under one name the rest in number order, only when as many
    are left on each side (a renumbered building, not one name for many)."""
    latest = max(p.nearest for p in places)
    places = [p for p in places if p.nearest == latest]
    out, rest_p, rest_s = [], sorted(places, key=lambda p: (_order(p.number), -p.nearest)), []
    for s, scope in sorted(stations, key=lambda x: _order(x[0].number)):
        p = next((p for p in rest_p if p.number == s.number and p.scope == scope), None)
        if p is None:
            rest_s.append(s)
        else:
            rest_p.remove(p)
            out.append((p, s))
    if how == "address":
        pairs = sorted(((abs(_order(p.number)[0] - _order(s.number)[0]), _order(s.number), i, j)
                        for i, p in enumerate(rest_p) for j, s in enumerate(rest_s)), key=lambda x: x[:2])
        used_p, used_s = set(), set()
        for _, _, i, j in pairs:
            if i not in used_p and j not in used_s:
                used_p.add(i)
                used_s.add(j)
                out.append((rest_p[i], rest_s[j]))
    elif len(rest_p) == len(rest_s):
        out.extend(zip(rest_p, rest_s))
    return out


def match(places: list[Place], stations: list[tuple[Station, str]]) -> list[tuple[Place, Station, str]]:
    """Join one round's stations in a municipality (each with its numbering) to the places of earlier rounds."""
    out: list[tuple[Place, Station, str]] = []
    free_p = list(places)
    free_s = list(stations)
    of_s = {"address": lambda s: words(s.address), "location": lambda s: words(s.location),
            "name": lambda s: words(s.name)}
    of_p = {"address": lambda p: p.addr, "location": lambda p: p.location, "name": lambda p: p.name}
    for how in ("address", "location", "name"):
        by_p: dict[frozenset, list[Place]] = defaultdict(list)
        by_s: dict[frozenset, list[tuple[Station, str]]] = defaultdict(list)
        for p in free_p:
            if of_p[how](p):
                by_p[of_p[how](p)].append(p)
        for s, scope in free_s:
            if of_s[how](s):
                by_s[of_s[how](s)].append((s, scope))
        done_p, done_s = set(), set()
        for key in by_p.keys() & by_s.keys():
            for p, s in _pair(by_p[key], by_s[key], how):
                # a name or a building shared by stations whose addresses differ is not one place
                if how != "address" and _differ(p.addr, words(s.address)):
                    continue
                out.append((p, s, how))
                done_p.add(id(p))
                done_s.add(id(s))
        free_p = [p for p in free_p if id(p) not in done_p]
        free_s = [(s, scope) for s, scope in free_s if id(s) not in done_s]
    for s, scope in sorted(free_s, key=lambda x: _order(x[0].number)):
        candidates = [p for p in free_p if p.number == s.number and p.scope == scope
                      and not _differ(p.addr, words(s.address)) and not _differ(p.location, words(s.location))
                      and not _resized(p.registered, s.registered)]
        if candidates:
            p = max(candidates, key=lambda p: p.nearest)
            free_p.remove(p)
            out.append((p, s, "number"))
    return out


def regular(s: Station) -> bool:
    """The stations followed across elections: at home, in constituencies I–X or the president's, with numbers (DIP
    lists three empty ones, which the round's pages leave out too)."""
    return (s.kind == "domestic" and (s.contest == "RH" or not s.contest.startswith("XI"))
            and bool(s.registered or s.voted or s.ballots))


def follow(rounds: list[RoundResults]) -> tuple[Places, MunicipalityKeys]:
    """rounds: oldest first."""
    keys = MunicipalityKeys(rounds)
    places: list[Place] = []
    open_by_mun: dict[str, list[Place]] = defaultdict(list)
    at: dict[tuple[str, str], Place] = {}
    for position, rnd in enumerate(rounds):
        by_mun: dict[str, list[tuple[Station, str]]] = defaultdict(list)
        for s in rnd.stations:
            if regular(s):
                code = keys(s)
                by_mun[code].append((s, s.mun_key if zagreb_part(s) else code))
        for code, sts in by_mun.items():
            taken = set()
            for p, s, how in match(open_by_mun[code], sts):
                scope = next(sc for st, sc in sts if st is s)
                p.add(rnd.id, s, how, position, scope)
                at[(rnd.id, s.key)] = p
                taken.add(id(s))
            for s, scope in sts:
                if id(s) not in taken:
                    p = Place(code)
                    p.add(rnd.id, s, "", position, scope)
                    places.append(p)
                    open_by_mun[code].append(p)
                    at[(rnd.id, s.key)] = p
    # page names: the newest round's places first, so they keep the plain name
    ordered, seen, taken_ids = [], set(), set()
    for rnd in reversed(rounds):
        for s in rnd.stations:
            p = at.get((rnd.id, s.key))
            if p is not None and p.rounds[0] == rnd.id and id(p) not in seen:
                seen.add(id(p))
                ordered.append(p)
                # Zagreb's parts number their stations apart: their pages are named after the part
                s = p.newest
                base = f"{s.mun_key if zagreb_part(s) else p.code}-{s.number}"
                p.id = base if base not in taken_ids else f"{base}-{rnd.id}"
                n = 2
                while p.id in taken_ids:
                    p.id, n = f"{base}-{rnd.id}-{n}", n + 1
                taken_ids.add(p.id)
    return Places(ordered, at), keys
