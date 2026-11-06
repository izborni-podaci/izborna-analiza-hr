"""The checks: the same rules for every list and candidate, and what each one catches."""

import copy
from pathlib import Path

import pytest

from izbori_hr.checks import BY_CODE, CHECKS, station_flags
from izbori_hr.elections import ROUNDS
from izbori_hr.results import Contest, Contestant, RoundResults, Station, load

DATA = Path(__file__).resolve().parent.parent / "data"


def _key(flags):
    return sorted((f.station, f.contest, f.code) for f in flags)


@pytest.mark.parametrize("round_id", ["sabor-2024", "predsjednik-2024-2"])
def test_swapping_contestants_changes_no_flag(round_id):
    """Principle 1: reversing the order of every contest's lists or candidates, votes and all, flags the same
    stations for the same reasons."""
    rnd = load(round_id, DATA)
    before = _key(station_flags(rnd))
    swapped = copy.deepcopy(rnd)
    for s in swapped.stations:
        s.votes = s.votes[::-1]
        s.prefs = s.prefs[::-1]
    for c in swapped.contests.values():
        c.contestants = c.contestants[::-1]
    assert _key(station_flags(swapped)) == before
    assert before  # something to compare


def _station(number, votes, registered=500, voted=None, ballots=None, invalid=5, kind="domestic", prefs=None,
             contest="I", municipality="GRAD", address="ULICA 1"):
    voted = sum(votes) + invalid if voted is None else voted
    ballots = voted if ballots is None else ballots
    return Station(contest=contest, kind=kind, county_no="1", county="ŽUPANIJA", place_kind="grad",
                   municipality=municipality, number=str(number), name=f"BM {number}", location=f"ŠKOLA {number}",
                   address=address, registered=registered, voted=voted, ballots=ballots, valid=sum(votes),
                   invalid=invalid, votes=votes, prefs=prefs or [])


def _round(stations, per_voter=1):
    contest = Contest("I", {"hr": "I", "en": "I"}, 14, [Contestant(x) for x in "ABCD"], per_voter)
    election, round_ = ROUNDS["sabor-2024"]
    return RoundResults(election, round_, {"I": contest}, stations)


def _codes(stations, per_voter=1):
    flags = station_flags(_round(stations, per_voter))
    return {s.number: sorted(f.code for f in flags if f.station == s.key) for s in stations}


def test_each_check():
    normal = [_station(n, [100 + n, 80, 60, 20], address=f"ULICA {n}") for n in range(10, 20)]
    typo = _station(4, [150, 80, 40, 20], registered=300, invalid=10)
    odd = [
        _station(1, [100, 80, 60, 21], voted=265, invalid=9, ballots=270),  # 5 ballots more than signatures
        _station(2, [100, 80, 60, 22], voted=274, ballots=267),  # 7 signatures more than ballots
        _station(3, [100, 80, 60, 23], registered=200),  # 268 voted of 200 registered
        typo,  # every voter voted, where the others' median is far lower
        _station(5, [100, 80, 60, 25], prefs=[[120] + [0] * 13, [], [], []]),  # a candidate above the list
        _station(6, [300, 2, 2, 1], registered=330, invalid=0),  # 305 of 330, 98% for one list
        _station(7, [100, 80, 60, 27], invalid=40),  # 40 of 307 invalid
        _station(8, [200, 100, 100, 50], registered=470, invalid=0),  # 96% turnout, the votes spread
    ]
    bad_sum = _station(9, [100, 80, 60, 29])
    bad_sum.valid = 250  # the lists add up to 269
    codes = _codes(normal + odd + [bad_sum])
    assert codes["1"] == ["ballots_over_signed"]
    assert codes["2"] == ["signed_over_ballots"]
    assert codes["3"] == ["high_turnout", "signed_over_registered"]
    assert codes["4"] == ["full_turnout_typo"]
    assert codes["5"] == ["prefs_over_list"]
    assert codes["6"] == ["near_unanimity"]
    assert codes["7"] == ["invalid_spike"]
    assert codes["8"] == ["high_turnout"]
    assert codes["9"] == ["ballot_mismatch", "sum_mismatch"]
    assert all(not codes[str(n)] for n in range(10, 20))
    assert {c for v in codes.values() for c in v} == {c.code for c in CHECKS} - {"identical_results"}


def test_identical_results_and_who_is_left_out():
    same = [_station(n, [120, 80, 60, 20], address=f"ULICA {n}") for n in (1, 2)]
    assert _codes(same + [_station(3, [121, 80, 60, 20])]) == {
        "1": ["identical_results"], "2": ["identical_results"], "3": []}
    # two contestants with votes match by chance too often
    assert _codes([_station(n, [120, 80, 0, 0], address=f"ULICA {n}") for n in (1, 2)]) == {"1": [], "2": []}
    # abroad and special stations: their register is who came, so only their arithmetic is checked
    away = [_station(1, [100, 2, 2, 1], registered=100, invalid=0, kind="abroad"),
            _station(2, [100, 80, 60, 20], registered=10, kind="special")]
    assert _codes(away) == {"1": [], "2": []}


def test_minority_votes():
    """The Serb minority's voters may give up to three votes: the votes may add up to three times the ballots."""
    s = _station(1, [100, 80, 60, 20], voted=105)
    s.valid = 100
    assert _codes([s], per_voter=3)["1"] == []
    assert _codes([s], per_voter=1)["1"] == ["sum_mismatch"]
    s.valid, s.voted, s.ballots = 80, 85, 85  # 260 votes from 80 ballots is more than three each
    assert _codes([s], per_voter=3)["1"] == ["sum_mismatch"]
    assert BY_CODE["sum_mismatch"].group == "paper"
