"""Reading DIP's files: the numbers add up to DIP's own totals, and the seats to the official result."""

from collections import Counter, defaultdict
from pathlib import Path

import pytest

from izbori_hr.results import group_columns, load
from izbori_hr.seats import allocate, dhondt, totals

DATA = Path(__file__).resolve().parent.parent / "data"
UNITS = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]


@pytest.fixture(scope="module")
def sabor():
    return load("sabor-2024", DATA)


@pytest.fixture(scope="module")
def president():
    return load("predsjednik-2024-1", DATA), load("predsjednik-2024-2", DATA)


def _sum(stations, field):
    return sum(getattr(s, field) for s in stations)


def test_parliament_totals(sabor):
    assert list(sabor.contests) == UNITS + ["XI"] + [f"XII-{g}" for g in "123456"]
    home = [s for s in sabor.stations if s.contest in UNITS]
    # DIP's totals for constituencies I–X: every station, at home, abroad and special
    assert (_sum(home, "registered"), _sum(home, "voted")) == (3_482_150, 2_140_824)
    assert Counter(s.kind for s in sabor.stations if s.contest == "XI") == {"abroad": 192}
    keys = Counter((s.contest, s.key) for s in sabor.stations)
    assert max(keys.values()) == 1  # the minorities' special stations: a row per constituency, each its own key
    assert all(s.number for s in sabor.stations)


def test_parliament_lists_and_preferences(sabor):
    hdz = [c for c in sabor.contests["I"].contestants if c.name.startswith("HRVATSKA DEMOKRATSKA ZAJEDNICA")]
    assert len(hdz) == 1 and len(hdz[0].candidates) == 14
    for cid in UNITS + ["XI"]:
        stations = sabor.of(cid)
        assert all(len(s.prefs) == len(s.votes) for s in stations)
        bad = sum(1 for s in stations if sum(s.votes) != s.valid)
        assert bad == 0, cid
    serb = sabor.contests["XII-1"]
    assert (serb.seats, serb.votes_per_voter, serb.lists) == (3, 3, False)


def test_seats_match_the_official_result(sabor):
    """The seats DIP declared in 2024, by the first party named on each list."""
    won = defaultdict(int)
    for cid, contest in sabor.contests.items():
        for c, n in zip(contest.contestants, allocate(contest, sabor.stations)):
            if n:
                won["minorities" if contest.minority else c.name.split(",")[0].split(" - ")[0]] += n
    assert dict(won) == {"HRVATSKA DEMOKRATSKA ZAJEDNICA": 61, "SOCIJALDEMOKRATSKA PARTIJA HRVATSKE": 42,
                         "DOMOVINSKI POKRET": 14, "MOST": 11, "MOŽEMO!": 10, "ISTARSKI DEMOKRATSKI SABOR": 2,
                         "NEZAVISNA PLATFORMA SJEVERA": 2, "FOKUS": 1, "minorities": 8}


def test_dhondt():
    assert dhondt([100, 80, 30], 5) == [3, 2, 0]
    assert dhondt([100, 80, 30], 5, [True, True, False]) == [3, 2, 0]
    assert dhondt([60, 60], 3) == [2, 1]  # a tie goes to the earlier list
    assert dhondt([0, 0], 2) == [0, 0]


def test_group_columns():
    """Two lists with two candidates each, and a third without: the only grouping where no candidate tops the list."""
    header = ["A", "a1", "a2", "B", "b1", "b2", "C"]
    rows = [[50, 20, 10, 30, 30, 0, 20], [10, 5, 5, 60, 10, 40, 30]]
    assert group_columns(header, rows, [100, 100]) == [0, 3, 6]
    with pytest.raises(ValueError):
        group_columns(header, rows, [99, 100])


def test_president(president):
    first, second = president
    for rnd in president:
        assert Counter(s.kind for s in rnd.stations) == {"domestic": 6527, "special": 123, "abroad": 105}
        assert all(int(s.number) >= 901 for s in rnd.stations if s.kind == "special")
        assert len({s.key for s in rnd.stations}) == len(rnd.stations)
    def top(rnd):
        votes, _ = totals(rnd.contests["RH"], rnd.stations)
        names = [c.name for c in rnd.contests["RH"].contestants]
        return sorted(zip(votes, names), reverse=True)[:2]
    assert top(first) == [(797_938, "ZORAN MILANOVIĆ"), (314_663, "DRAGAN PRIMORAC")]
    assert top(second) == [(1_122_859, "ZORAN MILANOVIĆ"), (380_752, "DRAGAN PRIMORAC")]
    assert _sum(first.stations, "voted") == 1_625_458
