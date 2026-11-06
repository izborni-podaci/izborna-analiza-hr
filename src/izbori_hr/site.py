"""The static site, in Croatian at the root and in English under en/. Every page comes from the archive in data/.

Pages: the home page and the one about the project; for each round its results, its checks, every municipality and,
for the parliament, every constituency. The flags are also a CSV under api/."""

from __future__ import annotations

import csv
import io
import json
import math
import shutil
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from fractions import Fraction
from importlib import resources
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from markupsafe import Markup

from izbori_hr import i18n, stats, svg
from izbori_hr.checks import BY_CODE, CHECKS, GROUPS, RULES, Flag, regular, station_flags
from izbori_hr.elections import ELECTIONS, Election, Round
from izbori_hr.i18n import LANGS, collate, fmt_date, fmt_int, fmt_num, fmt_p, fmt_pct, nice, t
from izbori_hr.results import Contest, RoundResults, Station, load
from izbori_hr.seats import allocate, totals

REPO = "https://github.com/izborni-podaci/izborna-analiza-hr"
SERBIA = "https://izborni-podaci.github.io/izborna-analiza/"
PREFIX = {"hr": "", "en": "en/"}
LANG_LABELS = {"hr": "Hrvatski", "en": "English"}
UNITS = ("I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X")


# ---- what a round's pages show ---------------------------------------------------------------------------------

@dataclass
class Row:
    """A list or candidate in one contest."""
    index: int  # in the contest, from 0
    name: str
    votes: int
    share: float | None
    seats: int = 0
    eligible: bool = True
    candidates: int = 0  # a list's candidates
    bar: float = 0.0  # the share against the contest's largest


@dataclass
class ContestView:
    id: str
    contest: Contest
    rows: list[Row]
    registered: int
    voted: int
    ballots: int
    valid: int
    invalid: int
    stations: int  # station rows with ballots
    turnout: float | None  # regular stations only
    denominator: str  # "valid" or "voted"
    threshold_votes: int | None = None
    flagged: int = 0
    muns: list = field(default_factory=list)  # (key, name)

    @property
    def won(self) -> list[Row]:
        return sorted((r for r in self.rows if r.seats), key=lambda r: (-r.seats, -r.votes))

    @property
    def invalid_share(self) -> float | None:
        return self.invalid / self.ballots if self.ballots else None


@dataclass
class Party:
    """Lists across the constituencies, by the first party each names."""
    name: str
    seats: int = 0
    votes: int = 0
    units: list[str] = field(default_factory=list)


@dataclass
class Municipality:
    key: str
    name: str
    county: str
    county_no: str
    abroad: bool
    stations: list[Station] = field(default_factory=list)
    flagged: int = 0

    def sections(self, order: list[str]) -> list[tuple[str, list[Station]]]:
        by: dict[str, list[Station]] = defaultdict(list)
        for s in self.stations:
            if s.ballots or s.voted or (s.registered and not s.contest.startswith("XII")):
                by[s.contest].append(s)
        # the constituency the municipality's own stations vote in first, then those of voters from elsewhere at its
        # special stations, then the minorities
        rank = {c: (0 if any(s.kind == "domestic" for s in by[c]) and not c.startswith("XII") else
                    2 if c.startswith("XII") else 1, i) for i, c in enumerate(order) if by.get(c)}
        return [(c, by[c]) for c in sorted(rank, key=rank.get)]

    @property
    def count(self) -> int:
        """Polling stations: each counted once, though a constituency or a minority has its own row of it."""
        return len({(s.kind, s.key.split("/")[1].split("-")[0]) for s in self.stations})

    def _regular(self) -> list[Station]:
        return [s for s in self.stations if regular(s)]

    @property
    def registered(self) -> int:
        return sum(s.registered for s in self._regular())

    @property
    def voted(self) -> int:
        return sum(s.voted for s in self.stations if not s.contest.startswith("XII"))

    @property
    def turnout(self) -> float | None:
        reg = self._regular()
        n = sum(s.registered for s in reg)
        return sum(s.voted for s in reg) / n if n else None

    @property
    def invalid_share(self) -> float | None:
        rows = [s for s in self.stations if not s.contest.startswith("XII")]
        ballots = sum(s.ballots for s in rows)
        return sum(s.invalid for s in rows) / ballots if ballots else None


@dataclass
class RoundView:
    rnd: RoundResults
    election: Election
    round: Round
    meta: dict
    flags: list[Flag]
    by_station: dict  # (contest, key) → [Flag]
    contests: dict  # id → ContestView
    municipalities: list[Municipality]
    parties: list[Party]
    rows_with_numbers: int

    @property
    def id(self) -> str:
        return self.round.id

    @property
    def kind(self) -> str:
        return self.election.kind

    @property
    def counts(self) -> Counter:
        return Counter(f.code for f in self.flags)

    @property
    def main(self) -> dict:
        """The numbers on top of the round's page: constituencies I–X for the parliament (voters living in Croatia,
        wherever they voted), every station for the president."""
        cs = [c for cid, c in self.contests.items() if cid in UNITS or cid == "RH"]
        registered, voted = sum(c.registered for c in cs), sum(c.voted for c in cs)
        ballots, invalid = sum(c.ballots for c in cs), sum(c.invalid for c in cs)
        return dict(registered=registered, voted=voted, valid=sum(c.valid for c in cs), invalid=invalid,
                    turnout=voted / registered if registered else None,
                    invalid_share=invalid / ballots if ballots else None)

    @property
    def minority_seats(self) -> int:
        return sum(r.seats for c in self.contests.values() if c.contest.minority for r in c.rows)

    def title(self, loc: str) -> str:
        base = self.election.title[loc]
        if len(self.election.rounds) > 1:
            return f"{base} · {t('round_n', loc, n=self.round.number)}"
        return base

    def short(self, loc: str) -> str:
        year = self.round.date[:4]
        if self.kind == "parliament":
            return f"Sabor {year}." if loc == "hr" else f"Parliament {year}"
        label = "Predsjednik" if loc == "hr" else "President"
        return f"{label} {self.election.id[-4:]} · {t('round_n', loc, n=self.round.number)}"


def lead_party(name: str) -> str:
    return name.split(", ")[0].strip()


def short_name(name: str) -> str:
    """A list's short label for compact summaries: the first party's abbreviation, as DIP writes it after " - "."""
    parts = [p.strip() for p in lead_party(name).split(" - ")]
    abbreviations = [p for p in parts[1:] if p and p == p.upper() and " " not in p and len(p) <= 10]
    return abbreviations[-1] if abbreviations else parts[0]


def contest_view(rnd: RoundResults, contest: Contest) -> ContestView:
    stations = rnd.of(contest.id)
    votes, valid = totals(contest, stations)
    voted = sum(s.voted for s in stations)
    # the president: whoever has more than half of the votes of those who voted (Constitution, Art. 94)
    seats = [1 if v * 2 > voted else 0 for v in votes] if contest.id == "RH" else allocate(contest, stations)
    denominator = "voted" if contest.id == "RH" else "valid"
    base = voted if denominator == "voted" else valid
    rows = [Row(i, c.name, v, v / base if base else None, seats[i],
                not contest.lists or v >= contest.threshold * valid, len(c.candidates))
            for i, (c, v) in enumerate(zip(contest.contestants, votes))]
    top = max((r.share or 0 for r in rows), default=0)
    for r in rows:
        r.bar = (r.share or 0) / top if top else 0
    reg = [s for s in stations if regular(s)]
    n_reg = sum(s.registered for s in reg)
    return ContestView(
        contest.id, contest, rows, sum(s.registered for s in stations), voted, sum(s.ballots for s in stations),
        valid, sum(s.invalid for s in stations), sum(1 for s in stations if s.ballots),
        sum(s.voted for s in reg) / n_reg if n_reg else None, denominator,
        threshold_votes=math.ceil(valid * Fraction(str(contest.threshold))) if contest.lists else None)


def prepare(rnd: RoundResults, meta: dict) -> RoundView:
    flags = station_flags(rnd)
    by_station: dict[tuple, list[Flag]] = defaultdict(list)
    for f in flags:
        by_station[(f.contest, f.station)].append(f)
    contests = {cid: contest_view(rnd, c) for cid, c in rnd.contests.items()}
    for (cid, _), _fl in by_station.items():
        contests[cid].flagged += 1
    muns: dict[str, Municipality] = {}
    for s in rnd.stations:
        m = muns.get(s.mun_key)
        if m is None:
            m = muns[s.mun_key] = Municipality(s.mun_key, s.municipality, s.county, s.county_no, s.kind == "abroad")
        m.stations.append(s)
    for m in muns.values():
        m.flagged = len({(s.contest, s.key) for s in m.stations if (s.contest, s.key) in by_station})
        for cid in {s.contest for s in m.stations if s.ballots or s.voted}:
            contests[cid].muns.append((m.key, m.name))
    for c in contests.values():
        c.muns.sort(key=lambda kv: collate(kv[1]))
    ordered = sorted(muns.values(), key=lambda m: (m.abroad, collate(m.name)))
    parties: dict[str, Party] = {}
    if rnd.election.kind == "parliament":
        for c in contests.values():
            if not c.contest.lists:
                continue
            for r in c.rows:
                p = parties.setdefault(lead_party(r.name), Party(lead_party(r.name)))
                p.seats += r.seats
                p.votes += r.votes
                p.units.append(c.id)
    rows = sum(1 for s in rnd.stations if s.ballots or s.voted or s.registered)
    return RoundView(rnd, rnd.election, rnd.round, meta, flags, dict(by_station), contests, ordered,
                     sorted(parties.values(), key=lambda p: (-p.seats, -p.votes)), rows)


# ---- texts that depend on the numbers ---------------------------------------------------------------------------

def flag_text(f: Flag, view: RoundView, loc: str) -> str:
    d = f.data
    i, pct = (lambda n: fmt_int(n, loc)), (lambda x: fmt_pct(x, loc, 1))
    contest = view.rnd.contests[f.contest]
    if f.code == "invalid_spike" and "median" in d:
        return i18n.check_text(f.code, "text_rel", loc).format(
            invalid=i(d["invalid"]), share=pct(d["share"]), median=pct(d["median"]),
            basis=i18n.BASIS[d["basis"]][LANGS.index(loc)])
    values = {k: (pct(v) if k in ("share", "turnout", "median") else i(v) if isinstance(v, int) else v)
              for k, v in d.items()}
    if f.code == "near_unanimity":
        values["name"] = contest.contestants[d["contestant"] - 1].name
    if f.code == "prefs_over_list":
        values["lists"] = "; ".join(contest.contestants[n - 1].name for n in d["lists"])
    if f.code == "identical_results":
        values["twins"] = ", ".join(d["twins"])
    return i18n.check_text(f.code, "text", loc).format(**values)


def check_name(code: str, loc: str) -> str:
    return i18n.check_text(code, "name", loc)


def contest_name(view: RoundView, cid: str, loc: str) -> str:
    if cid == "RH":
        return t("kind_president", loc)
    return view.rnd.contests[cid].name[loc]


# ---- building ---------------------------------------------------------------------------------------------------

class Site:
    def __init__(self, out: Path, views: list[RoundView]):
        self.out = out
        self.views = views
        templates = resources.files("izbori_hr") / "templates"
        self.env = Environment(loader=FileSystemLoader(str(templates)), autoescape=select_autoescape(["html"]),
                               undefined=StrictUndefined, trim_blocks=True, lstrip_blocks=True)
        self.written = 0

    def put(self, path: str, text: str) -> None:
        target = self.out / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        self.written += 1

    def render(self, template: str, page: str, loc: str, **ctx) -> None:
        up = "../" * page.count("/")
        root = up + ("../" if loc == "en" else "")
        langs = [{"lang": other, "label": LANG_LABELS[other], "href": root + PREFIX[other] + page,
                  "current": other == loc} for other in LANGS]
        env = dict(
            loc=loc, lang=loc, page=page, root=root, langs=langs, repo_url=REPO, serbia_url=SERBIA,
            link=lambda target: up + target,
            t=lambda key, **kw: t(key, loc, **kw),
            i=lambda n: fmt_int(n, loc), num=lambda x, d=1: fmt_num(x, loc, d),
            pct=lambda x, d=1: fmt_pct(x, loc, d), pval=lambda p: fmt_p(p, loc),
            date=lambda iso: fmt_date(iso, loc), name=nice,
            check_name=lambda code: check_name(code, loc),
            hint=lambda code: i18n.check_text(code, "hint", loc),
            checks=CHECKS, groups=GROUPS, rules=RULES,
        )
        env.update(ctx)
        self.put(PREFIX[loc] + page, self.env.get_template(template).render(**env))

    def build(self) -> None:
        if self.out.exists():
            shutil.rmtree(self.out)
        self.out.mkdir(parents=True)
        static = resources.files("izbori_hr") / "static"
        shutil.copytree(str(static), self.out / "static")
        (self.out / ".nojekyll").write_text("", encoding="utf-8")
        for view in self.views:
            self.put(f"api/r/{view.id}/flags.csv", flags_csv(view))
        for loc in LANGS:
            self.render("index.html", "index.html", loc, views=self.views, elections=ELECTIONS,
                        by_round={v.id: v for v in self.views})
            self.render("about.html", "about.html", loc, elections=ELECTIONS, metas={v.election.id: v.meta
                                                                                   for v in self.views})
            for view in self.views:
                self.round_pages(view, loc)
        self.render("404.html", "404.html", "hr")

    def round_pages(self, view: RoundView, loc: str) -> None:
        base = f"r/{view.id}/"
        common = dict(view=view, rnd=view.rnd, base=base, rtitle=view.title(loc), rshort=view.short(loc),
                      cname=lambda cid: contest_name(view, cid, loc), short_name=short_name,
                      flag_text=lambda f: flag_text(f, view, loc))
        order = list(view.rnd.contests)
        self.render("round.html", base + "index.html", loc, stats=round_stats(view, loc), **common)
        self.render("check.html", base + "check.html", loc, cards=cards(view), **common)
        if view.kind == "parliament":
            for cid, c in view.contests.items():
                self.render("contest.html", f"{base}j/{cid}.html", loc, c=c, **common)
        for m in view.municipalities:
            sections = []
            for cid, stations in m.sections(order):
                c = view.contests[cid]
                votes = [0] * len(c.rows)
                for s in stations:
                    for k, v in enumerate(s.votes):
                        votes[k] += v
                top = sorted(range(len(votes)), key=lambda k: (-votes[k], k))[:3 if len(votes) > 3 else len(votes)]
                sections.append(dict(id=cid, c=c, stations=sorted(stations, key=station_order), top=top,
                                     votes=votes, valid=sum(s.valid for s in stations),
                                     voted=sum(s.voted for s in stations)))
            self.render("municipality.html", f"{base}m/{m.key}.html", loc, m=m, sections=sections, **common)


def station_order(s: Station) -> tuple:
    number = s.number.lstrip("0") or "0"
    return ({"domestic": 0, "abroad": 1, "special": 2}[s.kind], int(number) if number.isdigit() else 0, s.unit)


def anchor(s: Station) -> str:
    return f"s-{s.contest}-{s.key.split('/', 1)[1]}"


def cards(view: RoundView) -> list[dict]:
    """The flagged stations, the strongest first: the weights of their checks added up, then by place."""
    stations = {(s.contest, s.key): s for s in view.rnd.stations}
    out = []
    for (cid, key), fl in view.by_station.items():
        s = stations[(cid, key)]
        out.append(dict(s=s, contest=cid, flags=sorted(fl, key=lambda f: (GROUPS.index(f.check.group), f.code)),
                        weight=sum(f.check.weight for f in fl), anchor=anchor(s)))
    out.sort(key=lambda c: (-c["weight"], collate(c["s"].municipality), station_order(c["s"]), c["contest"]))
    return out


def round_stats(view: RoundView, loc: str) -> dict:
    rnd = view.rnd
    contests = [c for c in rnd.contests if c == "RH" or c in UNITS]
    digits, shares = [], []
    for cid in contests:
        for idx in stats.top_two(rnd, cid):
            d = stats.last_digits(rnd, cid, idx)
            if d:
                digits.append(dict(contest=cid, name=rnd.contests[cid].contestants[idx].name, d=d,
                                   chart=svg.digits(d, loc) if cid == "RH" else None))
        for r in stats.round_percentages(rnd, cid):
            label = t("turnout", loc) if r.measure == "turnout" else t(
                "share_of", loc, name=rnd.contests[cid].contestants[int(r.measure)].name)
            shares.append(dict(contest=cid, label=label, r=r))
    return dict(hist=svg.histogram(stats.turnout_histogram(rnd), loc), digits=digits, shares=shares,
                local_round=stats.round_percentages_by_municipality(rnd),
                local_digits=stats.last_digits_by_municipality(rnd))


def flags_csv(view: RoundView) -> str:
    stations = {(s.contest, s.key): s for s in view.rnd.stations}
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["round", "contest", "kind", "county", "municipality", "number", "location", "code", "group", "data"])
    for f in sorted(view.flags, key=lambda f: (f.contest, f.station, f.code)):
        s = stations[(f.contest, f.station)]
        w.writerow([view.id, f.contest, s.kind, s.county, s.municipality, s.number, s.location, f.code,
                    f.check.group, json.dumps(f.data, ensure_ascii=False, sort_keys=True)])
    return buf.getvalue()


def read_meta(election: Election, data: Path) -> dict:
    return json.loads((data / election.id / "meta.json").read_text(encoding="utf-8"))


def build(data: Path, out: Path) -> Site:
    views = []
    for election in ELECTIONS:
        meta = read_meta(election, data)
        for round_ in election.rounds:
            views.append(prepare(load(round_.id, data), meta))
    site = Site(out, views)
    site.build()
    print(f"{site.written} files in {out}")
    return site
