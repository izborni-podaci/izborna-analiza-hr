"""Seats from votes, as the law allocates them (Zakon o izborima zastupnika u Hrvatski sabor).

Constituencies I–XI: D'Hondt among the lists with at least 5% of the constituency's valid ballots (14 seats each in
I–X, 3 in XI). The national minorities (XII): the candidates with the most votes, by the seats of their group. Who of
a list takes its seats (the preferential votes) is not computed here.
"""

from __future__ import annotations

from fractions import Fraction

from izbori_hr.results import Contest, Station


def dhondt(votes: list[int], seats: int, eligible: list[bool] | None = None) -> list[int]:
    """Seats per list; a tie for the last seat goes to the list with more votes, then to the earlier one."""
    eligible = eligible or [True] * len(votes)
    won = [0] * len(votes)
    for _ in range(seats):
        best = max((i for i in range(len(votes)) if eligible[i] and votes[i] > 0),
                   key=lambda i: (Fraction(votes[i], won[i] + 1), votes[i], -i), default=None)
        if best is None:
            break
        won[best] += 1
    return won


def totals(contest: Contest, stations: list[Station]) -> tuple[list[int], int]:
    """Votes per contestant and valid ballots, over the contest's stations."""
    votes = [0] * len(contest.contestants)
    valid = 0
    for s in stations:
        if s.contest != contest.id:
            continue
        valid += s.valid
        for i, v in enumerate(s.votes):
            votes[i] += v
    return votes, valid


def allocate(contest: Contest, stations: list[Station]) -> list[int]:
    votes, valid = totals(contest, stations)
    if contest.lists:
        return dhondt(votes, contest.seats, [v >= contest.threshold * valid for v in votes])
    order = sorted(range(len(votes)), key=lambda i: (-votes[i], i))
    won = [0] * len(votes)
    for i in order[:contest.seats]:
        won[i] = 1
    return won
