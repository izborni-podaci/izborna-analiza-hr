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


# The seats of every parliament, by the first party each list names (as DIP writes it in each constituency): the
# official results, coalitions and all. 2000's file holds constituencies I–X only (140 of 151 seats).
OFFICIAL_SEATS = {
    "sabor-2020": {"HRVATSKA DEMOKRATSKA ZAJEDNICA": 66, "SOCIJALDEMOKRATSKA PARTIJA HRVATSKE": 41,
                   "DOMOVINSKI POKRET MIROSLAVA ŠKORE": 16, "MOST NEZAVISNIH LISTA": 8, "MOŽEMO!": 7,
                   "STRANKA S IMENOM I PREZIMENOM": 3, "HRVATSKA NARODNA STRANKA": 1, "NARODNA STRANKA": 1,
                   "minorities": 8},
    "sabor-2016": {"HRVATSKA DEMOKRATSKA ZAJEDNICA": 61, "SOCIJALDEMOKRATSKA PARTIJA HRVATSKE": 54,
                   "MOST NEZAVISNIH LISTA": 13, "ŽIVI ZID": 8, "ISTARSKI DEMOKRATSKI SABOR": 3,
                   '"BANDIĆ MILAN 365': 2, "HRVATSKI DEMOKRATSKI SAVEZ SLAVONIJE I BARANJE": 1, "NEOVISNA LISTA": 1,
                   "minorities": 8},
    "sabor-2015": {"HRVATSKA DEMOKRATSKA ZAJEDNICA": 59, "SOCIJALDEMOKRATSKA PARTIJA HRVATSKE": 56,
                   "MOST NEZAVISNIH LISTA": 19, "ISTARSKI DEMOKRATSKI SABOR": 3, '"BANDIĆ MILAN 365': 2,
                   "HRVATSKI DEMOKRATSKI SAVEZ SLAVONIJE I BARANJE": 2, "NARODNA STRANKA": 1, "ŽIVI ZID": 1,
                   "minorities": 8},
    "sabor-2011": {"SOCIJALDEMOKRATSKA PARTIJA HRVATSKE": 80, "HRVATSKA DEMOKRATSKA ZAJEDNICA": 47,
                   "HRVATSKI DEMOKRATSKI SAVEZ SLAVONIJE I BARANJE": 6, "HRVATSKI LABURISTI-STRANKA RADA": 6,
                   "NEOVISNA LISTA": 2, "HRVATSKA SELJAČKA STRANKA": 1, "HRVATSKA STRANKA PRAVA DR.ANTE STARČEVIĆ": 1,
                   "minorities": 8},
    "sabor-2007": {"HRVATSKA DEMOKRATSKA ZAJEDNICA": 66, "SOCIJALDEMOKRATSKA PARTIJA HRVATSKE": 56,
                   "HRVATSKA NARODNA STRANKA-LIBERALNI DEMOKRATI": 7, "HRVATSKA SELJAČKA STRANKA": 7,
                   "HRVATSKI DEMOKRATSKI SAVEZ SLAVONIJE I BARANJE": 3, "ISTARSKI DEMOKRATSKI SABOR": 3,
                   "HRVATSKA SOCIJALNO LIBERALNA STRANKA": 1, "HRVATSKA STRANKA PRAVA": 1,
                   "HRVATSKA STRANKA UMIROVLJENIKA": 1, "minorities": 8},
    "sabor-2003": {"HRVATSKA DEMOKRATSKA ZAJEDNICA": 66, "SOCIJALDEMOKRATSKA PARTIJA HRVATSKE": 43,
                   "HRVATSKA NARODNA STRANKA": 11, "HRVATSKA SELJAČKA STRANKA": 9, "HRVATSKA STRANKA PRAVA": 8,
                   "HRVATSKA SOCIJALNO LIBERALNA STRANKA": 3, "HRVATSKA STRANKA UMIROVLJENIKA": 3,
                   "HRVATSKA DEMOKRATSKA SELJAČKA STRANKA": 1, "minorities": 8},
    "sabor-2000": {"SOCIJALDEMOKRATSKA PARTIJA HRVATSKE": 49, "HRVATSKA SOCIJALNO LIBERALNA STRANKA": 22,
                   "HRVATSKA DEMOKRATSKA ZAJEDNICA": 40, "HRVATSKA SELJAČKA STRANKA": 19,
                   "ISTARSKI DEMOKRATSKI SABOR": 5, "HRVATSKA STRANKA PRAVA": 5},
}


@pytest.mark.parametrize("round_id", sorted(OFFICIAL_SEATS))
def test_seats_every_parliament(round_id):
    rnd = load(round_id, DATA)
    won = defaultdict(int)
    for contest in rnd.contests.values():
        for c, n in zip(contest.contestants, allocate(contest, rnd.stations)):
            if n:
                won["minorities" if contest.minority else c.name.split(",")[0].split(" - ")[0].strip()] += n
    assert dict(won) == OFFICIAL_SEATS[round_id]


def test_older_totals_equal_dips_own_rows():
    """2007 ends each constituency's file with its total, 2003 with a grand total; 2011's municipalities add up to
    its regular stations."""
    expected = {"sabor-2007": {"I": (240_716, 2_764), "XI": (89_653, 749), "XII-1": (25_062, 679)},
                "sabor-2003": {"I": (250_408, 3_730), "XI": (69_727, 800), "XII-1": (46_126, 1_484)}}
    for round_id, contests in expected.items():
        rnd = load(round_id, DATA)
        for cid, numbers in contests.items():
            assert (_sum(rnd.of(cid), "valid"), _sum(rnd.of(cid), "invalid")) == numbers, (round_id, cid)
    regular = [s for s in load("sabor-2011", DATA).of("I") if s.kind == "domestic"]
    assert (_sum(regular, "valid"), _sum(regular, "invalid")) == (232_778, 3_581)


# The two leading candidates of every presidential round: DIP's grand totals (2005, 2009) and official results.
PRESIDENTS = {
    "predsjednik-2019-2": [(1_034_170, "ZORAN MILANOVIĆ"), (929_707, "KOLINDA GRABAR-KITAROVIĆ")],
    "predsjednik-2014-2": [(1_114_945, "KOLINDA GRABAR-KITAROVIĆ"), (1_082_436, "IVO JOSIPOVIĆ")],
    "predsjednik-2009-2": [(1_339_385, "prof.dr.sc. IVO JOSIPOVIĆ"), (883_222, "MILAN BANDIĆ")],
    "predsjednik-2005-2": [(1_454_451, "Stjepan Mesić, dipl.iur."), (751_692, "Jadranka Kosor, dipl.iur.")],
    "predsjednik-2005-1": [(1_089_398, "Stjepan Mesić, dipl.iur."), (452_218, "Jadranka Kosor, dipl.iur.")],
    "predsjednik-2000-2": [(1_425_342, "Stjepan Mesić"), (1_120_641, "Dražen Budiša")],
}


@pytest.mark.parametrize("round_id", sorted(PRESIDENTS))
def test_presidents(round_id):
    rnd = load(round_id, DATA)
    votes, _ = totals(rnd.contests["RH"], rnd.stations)
    names = [c.name for c in rnd.contests["RH"].contestants]
    assert sorted(zip(votes, names), reverse=True)[:2] == PRESIDENTS[round_id]


def test_what_older_files_lack():
    assert load("predsjednik-2009-1", DATA).notes == ("ballots_derived",)
    assert load("predsjednik-2005-1", DATA).notes == ("voted_from_ballots",)
    assert load("predsjednik-2000-1", DATA).notes == ("ballots_derived", "abroad_by_country")
    assert load("sabor-2003", DATA).notes == ("voted_from_ballots",)
    assert load("sabor-2000", DATA).notes == ("no_xi_xii", "ballots_derived")
    assert load("sabor-2011", DATA).notes == ()
