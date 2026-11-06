# izborna-analiza-hr

An archive of Croatian election results by polling station, as the State Electoral Commission (Državno izborno
povjerenstvo, DIP) published them, with checks of the numbers that are the same for every list and candidate. It
follows the Serbian archive, [izborna-analiza](https://github.com/izborni-podaci/izborna-analiza), with the same
checks, so the two countries can be read side by side.

**Site:** https://izborni-podaci.github.io/izborna-analiza-hr/ (Croatian; English under `en/`)

A flag is a question, not a verdict: "unusual, check the record", never "fraud".

## Elections

| Election | Rounds | DIP's page |
|---|---|---|
| Parliament (Hrvatski sabor) 2024 | 17 April 2024 | [parlament-2024](https://www.izbori.hr/arhiva-izbora/#/app/parlament-2024) |
| President 2024–25 | 29 December 2024, 12 January 2025 | [predsjednik-2024](https://www.izbori.hr/arhiva-izbora/#/app/predsjednik-2024) |

An election is added in `src/izbori_hr/elections.py` (its folder in DIP's archive, its rounds and the files that
hold them), then fetched with the **data** workflow.

## What the site shows

- **Results and seats** for each round. The parliament's seats are computed from the votes by polling station as the
  law allocates them (D'Hondt among lists with 5% of the valid votes in constituencies I–XI; the minorities'
  candidates with most votes in XII) and equal DIP's official result. Lists are added up nationally by the first
  party each names. Who of a list takes its seats (preferential votes) is not computed.
- **Checks** of every polling station, in two groups:
  - *the numbers don't add up*: votes against valid ballots, valid and invalid against the ballots, ballots against
    signatures, voters against the register, 100% turnout where the municipality's is far lower, a candidate's
    preferential votes above the list's;
  - *unusual*: high turnout with a near-unanimous result, many invalid ballots, turnout of 90% or more, the same
    votes as another station of the municipality.

  Stations abroad, special stations (care homes, hospitals, prisons, ships) and constituency XII (the national
  minorities, whose voters may vote anywhere) get the arithmetic checks only.
- **Every municipality and city**, with its stations, in each constituency they voted in.
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
uv run izbori-hr site --out _site       # build the site (about 15 s)
uv run pytest -q                        # every test (about 30 s)
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
| `results.py` | read the parliament's CSV and the president's XLSX into stations and contests |
| `seats.py` | D'Hondt and the minorities' seats |
| `checks.py` | the station checks and their thresholds |
| `stats.py` | last digits, round percentages, per-municipality tests |
| `site.py`, `templates/`, `static/` | the static site |
| `i18n.py` | the site's text in Croatian and English, number and name formats |
| `svg.py` | the charts, drawn when the site is built |

## Licence

Code: MIT. The data are DIP's, published in its election archive.
