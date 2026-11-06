# AGENTS.md

How to work on this repository, what must not change, and the architecture decisions with their reasons. It is
written for coding agents and for people. **Keep it current:** when a decision is made or changed, update this file
in the same commit. README.md describes the project for its users; this file is for those who change it.

## How to work here

- **Commit straight to `main`.** No feature branches or pull requests (as in the Serbian archive).
- **Run the whole test suite before every push:** `uv run pytest -q` (about 30 seconds). The **test** workflow runs
  it again on every push; a red run is fixed before anything else.
- **Explain why in commit messages.** Say what changed for the site or the data, and the reason.
- **Update README.md with every feature:** what the site shows, the archive layout, the commands, the workflows and
  the modules, as they apply.
- **Ask DIP little.** Its archive is final: the **data** workflow runs by hand, when an election is added.
- **Only one pending run per workflow.** Each workflow has a concurrency group; queue at most one run at a time.
- **Talk to the maintainer in Serbian** (Latin script), briefly and to the point. Code, comments and docs are in
  English; the site is in Croatian and English.

## Principles

These are the project's promises to its readers, the same as the Serbian archive's. Never change them without the
maintainer.

1. **The same rules for every contestant.** No party is hardcoded. A test reverses every contest's lists or
   candidates, votes and all, and checks that the flags don't change (`tests/test_checks.py`).
2. **A flag is a question, not a verdict.** The site says "unusual, check the record", never "fraud".
3. **Flags come from primary sources only:** the numbers DIP published. Statistics are never station flags.
4. **No personally identifying data; link to DIP instead.** The only names in the archive are those of lists and
   candidates, as DIP publishes them. Nothing about polling board members, observers or commission members is ever
   recorded, logged or printed.
5. **Nothing from third parties on the pages:** no analytics scripts, cookies, external fonts or scripts
   (`tests/test_site.py`).

## Architecture decisions

### Archive and data

- **Git is the archive.** `data/<election>/raw/` holds the files of DIP's zip that carry results by polling station
  (the parliament's CSV, whose XLSX repeat them; the president's XLSX), and `meta.json` the source, the time and the
  digests. A file is committed only when the zip changed.
- **Stations are keyed `municipality/number` within a contest.** The municipality is the county's number (without
  DIP's leading zero) and the name, or `ino-<country>` abroad; numbers lose DIP's leading zeros.
  - The parliament numbers its special stations apart from the regular ones (`p<number>`), and its minorities'
    special stations have a row for each constituency their voters live in (`p<number>-<constituency>`).
  - The president numbers special stations from 901 within the municipality, among the regular ones.
  - Zagreb is three municipalities in the parliament's files ("ZAGREB - I. IZBORNA JEDINICA", II, VI), each
    numbering its stations from 1, and one ("GRAD ZAGREB") in the president's. Pages are per round, so nothing
    joins them yet.
- **Which parliamentary column is a list is computed, not written:** DIP's CSV has fifteen columns of the station,
  then each list followed by its candidates' preferential votes, with no marker. `results.group_columns` finds the
  grouping in which no candidate, nor all of a list's together, has more votes than the list and the lists add up
  to the valid ballots. A station or two that don't add up are tolerated (a flag, not another grouping).

### Rules from the law

- **Seats:** Act on the Election of Representatives to the Croatian Parliament (NN 98/19): D'Hondt (Art. 40) among
  lists with 5% of the valid votes (Art. 41), 14 seats in I–X and 3 in XI; the minorities' candidates with most
  votes, 3 for the Serb minority and 1 for each other group (Art. 16, 17, 46). The Serb minority's voters may vote
  for up to three candidates, so its votes may add up to three times its valid ballots. The 2024 allocation equals
  DIP's result (`tests/test_results.py`).
- **President:** a majority of all voters who voted (Constitution, Art. 94). The site's first column of shares is of
  the voters who voted (DIP's own first-round tables use it), the second of the valid ballots (as the result was
  reported: 74.68% in the 2025 second round, 71.92% of those who voted).

### Checks and statistics

- **The checks are the Serbian archive's,** with its thresholds (`checks.RULES`), so the two sites can be compared.
  `prefs_over_list` is Croatia's own: a candidate's preferential votes, or all of a list's together, above the
  list's.
- **Only regular stations get the checks that need a register:** stations at home in I–X and the president's at
  home. Abroad and at special stations the register is the voters who came; in XII the minorities' voters may vote
  at any station.
- **Statistics use the same regular stations,** with 100 or more registered. In a runoff the two candidates' shares
  are one test, not two (one is near a whole percent when the other is).

### Site

- **Static pages in Croatian (the root) and English (`en/`).** No JavaScript framework; `static/site.js` filters
  and sorts, and the pages work without it. Charts are SVG drawn when the site is built.
- **Pages:** home, about, and for each round its results, its checks, every municipality (with a section per
  constituency its stations voted in: its own first, then voters from elsewhere at its special stations, then the
  minorities) and, for the parliament, every constituency.
- **Look:** the Serbian site's stylesheet and fonts (IBM Plex Sans, Source Serif 4; Latin subsets only).
- **Hosting:** GitHub Pages through Actions (`pages.yml`), about 60 MB and 3,600 files, at
  https://izborni-podaci.github.io/izborna-analiza-hr/. Pages must be set to "Source: GitHub Actions" in the
  repository's settings (the maintainer did it on 6 Nov 2026); without it the deploy job fails with a 404.

### Workflows

| Workflow | When | What |
|---|---|---|
| data | by hand | fetch DIP's zips, commit what changed, start **pages** |
| pages | on push to `main`, by hand | build and publish the site |
| test | on push | the whole test suite |

## Known issues and open decisions

- **Elections before 2024** are in DIP's archive in the same form (the parliament back to 2000); they are not added
  yet.
- **Pages across elections** (a municipality or a station over time) need Zagreb's parts and renamed
  municipalities joined; not started.
- **Preferential votes:** who of a list takes its seats is not computed.

## Decisions log

- **6 Nov 2026:** the maintainer asked for the Serbian archive's approach for Croatia, starting with the 2024
  parliamentary and presidential elections, from the zips DIP offers as "Preuzmite sve datoteke". The checks,
  statistics and principles are the Serbian archive's; the site is in Croatian and English.
