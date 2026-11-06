# izborna-analiza-hr

An archive of Croatian election results by polling station, as the State Electoral Commission (Državno izborno
povjerenstvo, DIP) published them, with checks of the numbers that are the same for every list and candidate. It
follows the Serbian archive, [izborna-analiza](https://github.com/izborni-podaci/izborna-analiza), with the same
checks, so the two countries can be read side by side.

**Site:** https://izborni-podaci.github.io/izborna-analiza-hr/ (Croatian; English under `en/`)

A flag is a question, not a verdict: "unusual, check the record", never "fraud".

## Elections

Every election DIP's archive has by polling station: the archive starts in 2000, and earlier elections are PDF
reports only.

| Parliament (Hrvatski sabor) | President |
|---|---|
| 2024, 2020, 2016, 2015, 2011, 2007, 2003, 2000 | 2024–25, 2019–20, 2014–15, 2009–10, 2005, 2000 (both rounds) |

An election is added in `src/izbori_hr/elections.py` (its folder in DIP's archive, its rounds and the files that
hold them), then fetched with the **data** workflow. It stays off the site (`published=False`) until its files
are read.

Each era of DIP's files has its own layout (`formats.py`); the columns are read by their names. What a file
lacks is not made up, and the round's pages say so: the president's files of 2000 and 2009 and the parliament's of
2000 give no ballots in the box (valid plus invalid ballots stand in), those of 2003 and 2005 only the voters
counted by the ballots, the president's of 2000 the votes abroad by country, and the parliament's of 2000
constituencies I–X only.

## What the site shows

- **Results and seats** for each round. The parliament's seats are computed from the votes by polling station as the
  law allocates them (D'Hondt among lists with 5% of the valid votes in constituencies I–XI; the minorities'
  candidates with most votes in XII) and equal the official result of every election since 2000. Lists are added up nationally by the first
  party each names. Who of a list takes its seats (preferential votes) is not computed.
- **Checks** of every polling station, in two groups:
  - *the numbers don't add up*: votes against valid ballots, valid and invalid against the ballots, ballots against
    signatures, voters against the register, 100% turnout where the municipality's is far lower, a candidate's
    preferential votes above the list's;
  - *unusual*: high turnout with a near-unanimous result, many invalid ballots, turnout of 90% or more, the same
    votes as another station of the municipality.

  Stations abroad, special stations (care homes, hospitals, prisons, ships) and constituency XII (the national
  minorities, whose voters may vote anywhere) get the arithmetic checks only.
- **Every municipality and city**, with its stations, in each constituency they voted in, on each round's pages.
- **Every municipality across elections** (`m/<code>.html`): a row for every round since 2000 (turnout, invalid
  ballots, the three with most votes, flagged stations), charts of turnout and invalid ballots against the whole
  country, and a short text of the latest numbers beside the earlier ones. Renamed municipalities, Istria's
  bilingual names and the parts of Zagreb the parliament counts apart are joined under the newest name.
- **Every polling station across elections** (`s/<id>.html`): regular stations at home are followed from election
  to election by their address, building, settlement or number (`places.py`), the same way for every station.
  These pages are in Croatian only, as both languages would pass GitHub Pages' 1 GB limit; the English pages link
  to them.
- **Search** on the home page for a municipality or a polling station (by number, building or settlement), from one
  file (`search.json`) loaded when the search is first used; **every election** on one page; and the stations
  **flagged in two or more elections**.
- **Statistics**, never station flags: turnout across stations, last digits, round percentages, and the same tests
  per municipality with the Bonferroni correction.
- **Downloads:** the flags as CSV (`api/r/<round>/flags.csv`); DIP's own files are in `data/`.

## Archive layout

```
data/<election>/meta.json   where the zip came from, when it was fetched, SHA-256 of the zip and of each file kept
data/<election>/raw/...     DIP's files as published: the parliament's CSV, the president's XLSX by round
```

A file is written only when DIP's zip changed, so the git history records what DIP published.

## Commands

```
uv sync
uv run izbori-hr fetch [election ...]   # download DIP's zips; writes only what changed
uv run izbori-hr site --out _site       # build the site (about 2 minutes, 620 MB, 37,000 files)
uv run pytest -q                        # every test (about 3 minutes)
```

## Workflows

| Workflow | When | What |
|---|---|---|
| data | by hand | fetch DIP's zips, commit what changed, start **pages** |
| pages | on push to `main`, by hand | build the site and publish it on GitHub Pages |
| test | on push | the whole test suite |

## Modules

| Module | What |
|---|---|
| `elections.py` | the elections, their rounds, DIP's URLs |
| `fetch.py` | download a zip, keep the results files, record `meta.json` |
| `results.py` | stations and contests; reads the parliament's CSV since 2015 and the president's XLSX since 2014 |
| `formats.py` | DIP's older layouts (parliament 2000–2011, president 2000–2009), read by their columns' names |
| `seats.py` | D'Hondt and the minorities' seats |
| `checks.py` | the station checks and their thresholds |
| `stats.py` | last digits, round percentages, per-municipality tests |
| `places.py` | municipalities and polling stations followed through every election |
| `history.py` | the pages across elections: their rows, short texts and charts |
| `site.py`, `templates/`, `static/` | the static site |
| `i18n.py` | the site's text in Croatian and English, number and name formats |
| `svg.py` | the charts, drawn when the site is built |

## Licence

Code: MIT. The data are DIP's, published in its election archive.
