"""Checks of one polling station's numbers. The same rules for every list and candidate: none is named here.

A flag is a question, not a verdict ("unusual, check the record"), and comes only from the numbers DIP published.
The rules are those of the Serbian archive (izborna-analiza), so the two can be read side by side:

- paper: the station's own numbers don't add up (ballots, signatures, votes, preferences);
- unusual: lopsided or repeated results; often legitimate, so they weigh least.

Stations abroad and special stations (care homes, prisons, ships) vote apart: their register is the voters who came,
so turnout means nothing there, and only their arithmetic is checked. The national minorities' voters may vote at
any station, so the same holds for constituency XII.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from statistics import median

from izbori_hr.results import RoundResults, Station


@dataclass(frozen=True)
class Check:
    code: str
    group: str
    weight: int


CHECKS = [
    Check("sum_mismatch", "paper", 3),
    Check("ballot_mismatch", "paper", 3),
    Check("ballots_over_signed", "paper", 3),
    Check("signed_over_ballots", "paper", 1),
    Check("signed_over_registered", "paper", 3),
    Check("full_turnout_typo", "paper", 2),
    Check("prefs_over_list", "paper", 2),
    Check("near_unanimity", "unusual", 2),
    Check("invalid_spike", "unusual", 2),
    Check("high_turnout", "unusual", 1),
    Check("identical_results", "unusual", 2),
]
BY_CODE = {c.code: c for c in CHECKS}
GROUPS = ["paper", "unusual"]

RULES = {
    "signed_over_ballots_min": 3,  # a voter walking out with a ballot is common; 3 or more is worth a look
    "typo_min_registered": 10,
    "typo_median_below": 0.80,
    "min_registered": 50,
    "high_turnout": 0.90,
    "near_share": 0.80,
    "invalid_abs_share": 0.08,
    "invalid_abs_min_voted": 100,
    "invalid_rel_factor": 3.0,
    "invalid_rel_min": 10,
    "invalid_rel_share": 0.04,
    "identical_min_votes": 50,  # with a few lists and this many votes, two stations rarely match by chance
    "identical_min_lists": 3,  # two contestants with votes match by chance too often (a two-way race)
}


@dataclass
class Flag:
    station: str  # Station.key
    contest: str
    code: str
    data: dict = field(default_factory=dict)

    @property
    def check(self) -> Check:
        return BY_CODE[self.code]


def regular(s: Station) -> bool:
    """A station whose register is its own voters': at home, and not in constituency XII."""
    return s.kind == "domestic" and not s.contest.startswith("XII")


def _invalid_share(s: Station) -> float | None:
    return s.invalid / s.ballots if s.ballots else None


def paper_flags(s: Station, per_voter: int, mun_turnouts: list[float]) -> list[Flag]:
    out = []
    total = sum(s.votes)
    if (total != s.valid) if per_voter == 1 else not (s.valid <= total <= per_voter * s.valid):
        out.append(Flag(s.key, s.contest, "sum_mismatch", {"sum": total, "valid": s.valid}))
    if s.valid + s.invalid != s.ballots:
        out.append(Flag(s.key, s.contest, "ballot_mismatch", {"valid": s.valid, "invalid": s.invalid,
                                                              "ballots": s.ballots}))
    if s.ballots > s.voted:
        out.append(Flag(s.key, s.contest, "ballots_over_signed",
                        {"ballots": s.ballots, "voted": s.voted, "diff": s.ballots - s.voted}))
    elif s.voted - s.ballots >= RULES["signed_over_ballots_min"]:
        out.append(Flag(s.key, s.contest, "signed_over_ballots",
                        {"voted": s.voted, "ballots": s.ballots, "diff": s.voted - s.ballots}))
    if regular(s):
        if s.voted > s.registered:
            out.append(Flag(s.key, s.contest, "signed_over_registered",
                            {"voted": s.voted, "registered": s.registered, "diff": s.voted - s.registered}))
        elif s.registered >= RULES["typo_min_registered"] and s.voted == s.registered and mun_turnouts:
            med = median(mun_turnouts)
            if med < RULES["typo_median_below"]:
                out.append(Flag(s.key, s.contest, "full_turnout_typo",
                                {"registered": s.registered, "voted": s.voted, "median": med}))
    over = [i + 1 for i, (v, prefs) in enumerate(zip(s.votes, s.prefs)) if prefs and (sum(prefs) > v or max(prefs) > v)]
    if over:
        out.append(Flag(s.key, s.contest, "prefs_over_list", {"lists": over}))
    return out


def unusual_flags(s: Station, mun_peers: list[Station], addr_peers: list[Station], typo: bool) -> list[Flag]:
    out = []
    t = s.turnout
    if not typo and t is not None and s.registered >= RULES["min_registered"] and t >= RULES["high_turnout"]:
        top = max(range(len(s.votes)), key=lambda i: s.votes[i]) if s.votes else None
        share = s.votes[top] / s.valid if top is not None and s.valid else 0
        if share >= RULES["near_share"]:
            out.append(Flag(s.key, s.contest, "near_unanimity",
                            {"turnout": t, "contestant": top + 1, "share": share, "registered": s.registered}))
        else:
            out.append(Flag(s.key, s.contest, "high_turnout", {"turnout": t, "registered": s.registered}))
    share = _invalid_share(s)
    if share is not None:
        if s.voted >= RULES["invalid_abs_min_voted"] and share >= RULES["invalid_abs_share"]:
            out.append(Flag(s.key, s.contest, "invalid_spike", {"invalid": s.invalid, "share": share,
                                                                "basis": "absolute"}))
        elif s.invalid >= RULES["invalid_rel_min"] and share >= RULES["invalid_rel_share"]:
            peers, basis = [p for p in addr_peers if p is not s], "address"
            if not peers:
                peers, basis = [p for p in mun_peers if p is not s], "municipality"
            shares = [x for p in peers if (x := _invalid_share(p)) is not None]
            if shares:
                med = median(shares)
                if share >= RULES["invalid_rel_factor"] * max(med, 0.005):
                    out.append(Flag(s.key, s.contest, "invalid_spike",
                                    {"invalid": s.invalid, "share": share, "median": med, "basis": basis}))
    return out


def identical_flags(groups: dict[tuple, list[Station]]) -> list[Flag]:
    """Stations of one municipality and contest where every contestant got the same votes. Once a few contestants
    have votes, a chance match is rare; a copied record, or a slip when the numbers were entered, gives one."""
    out = []
    for stations in groups.values():
        same: dict[tuple, list[Station]] = defaultdict(list)
        for s in stations:
            votes = tuple(s.votes)
            if sum(votes) >= RULES["identical_min_votes"] and sum(1 for v in votes if v) >= RULES["identical_min_lists"]:
                same[votes].append(s)
        for group in same.values():
            if len(group) > 1:
                out.extend(Flag(s.key, s.contest, "identical_results",
                                {"twins": [t.number for t in group if t is not s], "votes": sum(s.votes)})
                           for s in group)
    return out


def station_flags(rnd: RoundResults) -> list[Flag]:
    """Every flag of the round. The same rules for every contestant: swapping two lists' votes everywhere changes
    nothing here (tests/test_checks.py)."""
    by_mun: dict[str, list[Station]] = defaultdict(list)
    by_addr: dict[tuple, list[Station]] = defaultdict(list)
    by_contest_mun: dict[tuple, list[Station]] = defaultdict(list)
    for s in rnd.stations:
        if regular(s):
            by_mun[s.mun_key].append(s)
            by_addr[(s.mun_key, s.location.upper(), s.address.upper())].append(s)
            by_contest_mun[(s.contest, s.mun_key)].append(s)
    flags: list[Flag] = []
    for s in rnd.stations:
        if not (s.ballots or s.voted or s.valid or s.registered):
            continue  # a station nobody voted at (most of XII's)
        contest = rnd.contests[s.contest]
        peers = [t for p in by_mun.get(s.mun_key, []) if p is not s
                 and p.registered >= RULES["typo_min_registered"] and (t := p.turnout) is not None]
        paper = paper_flags(s, contest.votes_per_voter, peers if regular(s) else [])
        flags.extend(paper)
        if regular(s):
            typo = any(f.code == "full_turnout_typo" for f in paper)
            flags.extend(unusual_flags(s, by_mun[s.mun_key], by_addr[(s.mun_key, s.location.upper(),
                                                                       s.address.upper())], typo))
    flags.extend(identical_flags(by_contest_mun))
    return flags
