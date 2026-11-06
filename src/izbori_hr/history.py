"""Municipalities and polling places across every archived election: the rows of their pages, the short text on
top ("Ukratko") and the points of their charts. Every row is computed the same way for every place and contestant;
the text states numbers and never judges them."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field

from izbori_hr.checks import Flag
from izbori_hr.i18n import fmt_pct, t
from izbori_hr.places import Place, Places, MunicipalityKeys
from izbori_hr.results import Station


@dataclass
class Top:
    label: str
    full: str
    share: float | None


@dataclass
class Row:
    """One election of a municipality or a place."""
    view: object  # site.RoundView
    stations: list[Station]
    flags: list[Flag] = field(default_factory=list)
    flagged: int = 0  # stations with a flag (a municipality)
    count: int = 0  # polling stations (a municipality)
    registered: int = 0
    voted: int = 0
    turnout: float | None = None
    invalid: int = 0
    invalid_share: float | None = None
    top: list[Top] = field(default_factory=list)
    how: str = ""  # a place: how this election's station was joined to the earlier ones
    links: list[tuple[str, str]] = field(default_factory=list)  # (round's municipality key, its name)

    @property
    def rid(self) -> str:
        return self.view.id


def _share(n: int, d: int) -> float | None:
    return n / d if d else None


def top_three(view, stations: list[Station], short_name) -> list[Top]:
    """The three with most votes: lists by the first party each names (the parliament: one municipality can vote in
    several constituencies), candidates by name; shares of the valid votes, the president's of the voters."""
    votes: Counter = Counter()
    full: dict[str, str] = {}
    for s in stations:
        contest = view.rnd.contests[s.contest]
        for c, v in zip(contest.contestants, s.votes):
            key = c.name.split(", ")[0].strip() if contest.lists else c.name
            votes[key] += v
            full.setdefault(key, c.name)
    if view.kind == "president":
        base = sum(s.voted for s in stations)
    else:
        base = sum(s.valid for s in stations)
    return [Top(short_name(k) if view.kind == "parliament" else k, full[k], _share(v, base))
            for k, v in votes.most_common(3) if v]


def summarize(view, stations: list[Station], short_name) -> Row:
    """A municipality's or a place's numbers in one election. Turnout counts regular stations only (elsewhere the
    register is the voters who came); the minorities' rows repeat voters of the other constituencies, so they're
    left out of the voters."""
    counted = [s for s in stations if not s.contest.startswith("XII")]
    reg = [s for s in counted if s.kind == "domestic"]
    registered, voted_reg = sum(s.registered for s in reg), sum(s.voted for s in reg)
    ballots, invalid = sum(s.ballots for s in counted), sum(s.invalid for s in counted)
    flagged = {(s.contest, s.key) for s in stations if (s.contest, s.key) in view.by_station}
    return Row(view, stations, [f for s in stations for f in view.by_station.get((s.contest, s.key), [])],
               len(flagged), len({(s.kind, s.mun_key, s.number) for s in counted}), registered,
               sum(s.voted for s in counted), _share(voted_reg, registered), invalid, _share(invalid, ballots),
               top_three(view, counted, short_name))


class History:
    def __init__(self, views: list, places: Places, keys: MunicipalityKeys, short_name):
        """views: oldest first."""
        self.views, self.places, self.keys, self.short_name = views, places, keys, short_name
        self.by_mun: dict[str, dict[str, list[Station]]] = defaultdict(lambda: defaultdict(list))
        self.names: dict[str, str] = {}
        self.counties: dict[str, str] = {}
        for view in views:  # oldest first, so the newest name stays
            for s in view.rnd.stations:
                code = keys(s)
                if not keys.placed(code):
                    continue  # on its election's pages only
                self.by_mun[code][view.id].append(s)
                self.names[code] = "GRAD ZAGREB" if code == "21-grad-zagreb" else s.municipality
                if s.county:
                    self.counties[code] = s.county
        self.view_of = {v.id: v for v in views}
        self.national = {v.id: summarize(v, [s for s in v.rnd.stations], short_name) for v in views}
        self._mun_rows: dict[str, list[Row]] = {}

    def municipalities(self) -> list[str]:
        return list(self.by_mun)

    def mun_rows(self, code: str) -> list[Row]:
        """Newest first."""
        if code not in self._mun_rows:
            rows = []
            for view in reversed(self.views):
                stations = self.by_mun[code].get(view.id)
                if stations:
                    row = summarize(view, stations, self.short_name)
                    row.links = sorted({(s.mun_key, s.municipality) for s in stations})
                    rows.append(row)
            self._mun_rows[code] = rows
        return self._mun_rows[code]

    def place_rows(self, p: Place) -> list[Row]:
        rows = []
        for rid in p.rounds:  # newest first
            view, s = self.view_of[rid], p.stations[rid]
            row = summarize(view, [s], self.short_name)
            row.how = p.how.get(rid, "")
            rows.append(row)
        return rows

    def flagged_in(self, p: Place) -> int:
        return sum(1 for rid in p.rounds if (p.stations[rid].contest, p.stations[rid].key)
                   in self.view_of[rid].by_station)

    # ---- the charts -------------------------------------------------------------------------------------------

    def points(self, rows: list[Row], reference: dict[str, Row], measure: str, loc: str) -> list[dict]:
        """Oldest first: this place's value and the reference's (its municipality, or the whole election)."""
        out, last_year = [], None
        for row in reversed(rows):
            view = row.view
            year = view.round.date[:4]
            ref = reference.get(row.rid)
            out.append({"kind": view.kind, "year": year if year != last_year else "", "title": view.short(loc),
                        "v": getattr(row, measure), "r": getattr(ref, measure) if ref else None})
            last_year = year
        return out

    # ---- "Ukratko" --------------------------------------------------------------------------------------------

    def analysis_mun(self, code: str, loc: str) -> list[dict]:
        rows = self.mun_rows(code)
        if not rows:
            return []
        latest = rows[0]
        national = self.national[latest.rid]
        out = []
        with_flags = [r for r in rows if r.flagged]
        lines = [t("an_flagged_latest", loc, n=latest.flagged, total=latest.count, title=latest.view.short(loc))]
        lines.append(t("an_flagged_elections", loc, k=len(with_flags), n=len(rows)))
        out.append({"label": t("an_flags", loc), "lines": lines})
        if latest.turnout is not None:
            out.append({"label": t("turnout", loc), "lines": [
                t("an_turnout_vs", loc, x=fmt_pct(latest.turnout, loc), title=latest.view.short(loc),
                  ref=t("an_ref_country", loc), y=fmt_pct(national.turnout, loc))] + self._turnout_change(rows, loc)})
        if latest.top:
            lead = latest.top[0]
            line2 = []
            if national.top and national.top[0].label != lead.label:
                line2 = [t("an_lead_country", loc, name=national.top[0].label, share=fmt_pct(national.top[0].share, loc))]
            out.append({"label": t("an_most", loc), "lines": [
                t("an_lead", loc, name=lead.label, share=fmt_pct(lead.share, loc), title=latest.view.short(loc))]
                + line2})
        first = rows[-1]
        out.append({"label": t("stations", loc), "lines": [
            t("an_stations", loc, n=latest.count, title=latest.view.short(loc)),
            t("an_stations_first", loc, n=first.count, title=first.view.short(loc))]})
        return out

    def analysis_place(self, p: Place, loc: str) -> list[dict]:
        rows = self.place_rows(p)
        latest = rows[0]
        mun = {r.rid: r for r in self.mun_rows(p.code)}
        out = []
        flagged = [r for r in rows if r.flags]
        lines = [t("an_place_flagged", loc, k=len(flagged), n=len(rows))]
        if flagged:
            r = flagged[0]
            from izbori_hr.i18n import check_text
            names = ", ".join(dict.fromkeys(check_text(f.code, "name", loc) for f in r.flags))
            lines.append(t("an_place_flagged_last", loc, title=r.view.short(loc), names=names))
        out.append({"label": t("an_flags", loc), "lines": lines})
        if latest.turnout is not None and latest.rid in mun:
            out.append({"label": t("turnout", loc), "lines": [
                t("an_turnout_vs", loc, x=fmt_pct(latest.turnout, loc), title=latest.view.short(loc),
                  ref=t("an_ref_mun", loc), y=fmt_pct(mun[latest.rid].turnout, loc))] + self._turnout_change(rows, loc)})
        if latest.top:
            lead = latest.top[0]
            m = mun.get(latest.rid)
            line2 = []
            if m and m.top and m.top[0].label != lead.label:
                line2 = [t("an_lead_mun", loc, name=m.top[0].label, share=fmt_pct(m.top[0].share, loc))]
            out.append({"label": t("an_most", loc), "lines": [
                t("an_lead", loc, name=lead.label, share=fmt_pct(lead.share, loc), title=latest.view.short(loc))]
                + line2})
        former = p.former_numbers
        lines = [t("an_followed", loc, n=len(rows), title=rows[-1].view.short(loc))]
        if former:
            lines.append(t("place_former", loc, numbers=", ".join(former)))
        out.append({"label": t("an_place", loc), "lines": lines})
        return out

    @staticmethod
    def _turnout_change(rows: list[Row], loc: str) -> list[str]:
        """The latest turnout against the last earlier election of the same kind."""
        latest = rows[0]
        same = next((r for r in rows[1:] if r.view.kind == latest.view.kind and r.turnout is not None
                     and r.view.round.number == latest.view.round.number), None)
        if same is None or latest.turnout is None:
            return []
        return [t("an_turnout_before", loc, title=same.view.short(loc), y=fmt_pct(same.turnout, loc))]
