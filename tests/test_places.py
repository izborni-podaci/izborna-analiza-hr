"""Municipalities and polling places across elections."""

from pathlib import Path

import pytest

from izbori_hr.elections import ELECTIONS
from izbori_hr.places import Place, follow, match, words
from izbori_hr.results import Station, load

DATA = Path(__file__).resolve().parent.parent / "data"


@pytest.fixture(scope="module")
def rounds():
    return sorted((load(r.id, DATA) for e in ELECTIONS for r in e.rounds), key=lambda r: r.round.date)


@pytest.fixture(scope="module")
def followed(rounds):
    return follow(rounds)


def _station(number, address="", location="", name="", registered=500, municipality="GRAD", county="1"):
    return Station(contest="I", kind="domestic", county_no=county, county="Ž", place_kind="grad",
                   municipality=municipality, number=str(number), name=name, location=location, address=address,
                   registered=registered, voted=300, ballots=300, valid=290, invalid=10, votes=[290])


def test_municipality_names_across_elections(followed):
    places, keys = followed
    assert keys(_station(1, municipality="SV. FILIP I JAKOV", county="13")) == "13-sveti-filip-i-jakov"
    assert keys(_station(1, municipality="MURTER", county="15")) == "15-murter-kornati"
    assert keys(_station(1, municipality="ZAGREB", county="")) == "21-grad-zagreb"
    assert keys(_station(1, municipality="ZAGREB - II. IZBORNA JEDINICA", county="21")) == "21-grad-zagreb"
    assert keys(_station(1, municipality="ZAGREB-ISTOČNI DIO", county="21")) == "21-grad-zagreb"
    # Istria's names are bilingual since 2011, the older files write the Croatian one
    assert keys(_station(1, municipality="NOVIGRAD", county="18")) == "18-novigrad-cittanova"
    assert keys(_station(1, municipality="OTOK (VINKOVCI)", county="16")) == "16-otok"
    # a name two municipalities share gives no county by itself: such a station has no page across elections
    assert keys(_station(1, municipality="PRIVLAKA", county="")) == "privlaka" and not keys.placed("privlaka")


def test_counties_of_shared_names(rounds):
    """Otok, Privlaka, Novigrad and Sveta Nedelja are two municipalities each. The older parliamentary files name
    the municipality only; its constituency says which, or (2003's minorities) the counties DIP lists around it."""
    by_id = {r.round.id: r for r in rounds}

    def counties(rid, contest, name):
        return {s.county_no for s in by_id[rid].stations
                if s.contest == contest and s.municipality == name and s.kind == "domestic"}

    assert counties("sabor-2000", "VIII", "NOVIGRAD") == {"18"} and counties("sabor-2000", "IX", "NOVIGRAD") == {"13"}
    assert counties("sabor-2011", "XII-1", "OTOK") == {"16", "17"}
    assert counties("sabor-2003", "XII-1", "PRIVLAKA") == {"13", "16"}
    assert counties("sabor-2003", "XII-1", "SVETA NEDJELJA") == {"1"}
    assert all(s.county_no for r in rounds for s in r.stations if s.kind == "domestic")


def test_a_place_through_every_election(followed):
    places, _ = followed
    p = next(p for p in places.places if p.id == "14-beli-manastir-3")
    assert p.newest.location == 'ZGRADA "P+8" (LJEPOTICA)'
    # by address since both elections give one, by number before; 2007's station 3 had 270 registered voters to
    # 2009's 925, so it was another area under the same number
    assert p.how["predsjednik-2014-1"] == "address" and p.how["sabor-2011"] == "number"
    assert p.rounds[-1] == "predsjednik-2009-1" and places.of("sabor-2007", "14-beli-manastir/3") is not p
    assert len({p.id for p in places.places}) == len(places.places) and all(p.id for p in places.places)
    # every regular station has its place: no two municipalities share a key (Otok in V and X, 2000–2011)
    assert len({id(p) for p in places.at.values()}) == len(places.places)


def test_zagreb_parts_number_apart(followed):
    """Zagreb's parts of the 2024 parliamentary files each have a station 5; they're three places, and part I's
    numbers are the City's (the president's), joined by address."""
    places, _ = followed
    fives = {places.of("sabor-2024", f"21-zagreb-{part}-izborna-jedinica/5").id for part in ("i", "ii", "vi")}
    assert len(fives) == 3
    p = places.of("sabor-2024", "21-zagreb-i-izborna-jedinica/5")
    assert "predsjednik-2024-1" in p.rounds and p.stations["predsjednik-2024-1"].number == "5"
    # the school at Gundulićeva 23A had one station in 2019 and two since 2020: the old one keeps its history
    six = places.of("sabor-2024", "21-zagreb-i-izborna-jedinica/6")
    assert {"predsjednik-2019-1", "sabor-2020", "predsjednik-2024-1"} <= set(six.rounds)


def test_matching_rules():
    older = Place("1-grad")
    older.add("a", _station(3, "ULICA KRALJA TOMISLAVA 2", "ŠKOLA"), "", 0, "1-grad")
    # the address wins over the number: the station moved to number 7
    got = match([older], [(_station(3, "TRG BANA JELAČIĆA 1", "OSNOVNA ŠKOLA"), "1-grad"),
                          (_station(7, "KRALJA TOMISLAVA 2", "ŠKOLA"), "1-grad")])
    assert [(s.number, how) for _, s, how in got] == [("7", "address")]
    # a number never joins stations whose address differs, whose register is far bigger, or in another numbering
    assert match([older], [(_station(3, "TRG BANA JELAČIĆA 1"), "1-grad")]) == []
    assert match([older], [(_station(3, registered=1001), "1-grad")]) == []
    assert match([older], [(_station(3), "21-zagreb-jugoistok")]) == []
    assert [how for _, _, how in match([older], [(_station(3, registered=1000), "1-grad")])] == ["number"]
    assert words("OSNOVNA ŠKOLA \"DR. FRANJO TUĐMAN\"") == {"DR", "FRANJO", "TUDJMAN"} - {"DR"}
