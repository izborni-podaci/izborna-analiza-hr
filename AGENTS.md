# AGENTS.md

How to work on this repository, what must not change, and the architecture decisions with their reasons. It is
written for coding agents and for people. **Keep it current:** when a decision is made or changed, update this file
in the same commit. README.md describes the project for its users; this file is for those who change it.

## How to work here

- **Commit straight to `main`.** No feature branches or pull requests (as in the Serbian archive).
- **Run the whole test suite before every push:** `uv run pytest -q` (about 3 minutes; `tests/test_site.py`
  builds the whole site). The **test** workflow runs
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
  - Zagreb is three municipalities in the parliament's files ("ZAGREB - I. IZBORNA JEDINICA", II, VI; by
    districts in 2003–2011), each numbering its stations from 1, and one ("GRAD ZAGREB") in the president's. A
    round's pages keep DIP's division; the pages across elections join them (*Across elections*).
- **Every election since 2000 is archived** (DIP's archive has PDF reports only before that). The layouts:
  - parliament 2015–2024: fifteen columns of the station, then each list and its candidates' preferential votes
    (`results.read_parliament`); 2016 names its files `004_00_rezultati.csv`, the others `02_04_rezultati.csv`;
    2015's special stations name their first columns differently, so only the vote columns must agree;
  - parliament 2007 and 2011: reports by constituency (regular, special, abroad; XI's voters in Croatia), a row
    of ballot numbers under the header and totals at the end; read by the columns' names (`formats.roles`);
  - parliament 2003: regular and "mixed" stations (embassies, clubs abroad, displaced persons, institutions),
    all kept as special stations; one column of voters, counted by the ballots; the zip's file names are DOS
    Latin 2 without the UTF-8 flag (`Election.names`);
  - parliament 2000: constituencies I–X only, lists by number with their names in `ijNN_Stranke.csv` (parties a
    line each, the leader last, not in capitals);
  - president 2014–2024: one sheet a round, as 2024 (`results.read_president`); 2009 and 2005: the country and
    its stations abroad as a county ("INOZEMSTVO"), "Grand Total" rows; 2000: a sheet for Croatia and one for
    abroad by country.
- **What a file lacks is not made up** (`RoundResults.notes`, shown on every page of the round): no ballots in the
  box (president 2000 and 2009, parliament 2000) → valid plus invalid stand in, and signatures are compared with
  them; no register count (parliament 2003, president 2005) → the ballots stand in, so signatures and ballots
  aren't compared; abroad by country (president 2000); I–X only (parliament 2000).
- **2000, constituency V:** DIP's list names 26 lists and the file has 25 columns, which add up to the valid
  ballots. List 19 (Nova Hrvatska) has no column: column 19's votes are where the Party of Danube Serbs (list 20)
  would have them (Trpinja, Vukovar, Negoslavci, Borovo), 21's where SDSS (22) would, and 22 holds SDP–HSLS's
  26.7% (23), whose five seats there make the coalition's 71 of the official result (`formats.NO_COLUMN_2000`).
- **Counties of the older parliamentary files,** which name the municipality only, come from the presidential
  files of 2024, 2019, 2014 and 2009 (`formats.county_lookup`, regular stations only: 2009 lists a special station
  of Karlovac in county 3), the newest first; renamed ones have an alias. Four names belong to two municipalities
  each (Otok, Privlaka, Novigrad, Sveta Nedelja):
  - written apart ("OTOK (VINKOVCI)"), the name says which;
  - otherwise the constituency does, from the parliamentary files of 2015–2020, which name both
    (`formats.constituency_lookup`); the minorities' files of 2007 and 2011 give the constituency of each
    municipality in a column of their own;
  - otherwise (2003's minorities) the stations around it do: DIP lists regular stations county by county, so the
    municipality takes the county of those before and after it when they agree and it is one of the name's
    (`formats._between`);
  - otherwise (a few special stations of 2007, listed alphabetically) it stays without a county.
- **A zip is extracted again when the patterns of what is kept change** (`meta.json` records them), not only when
  DIP republishes.
- **Which parliamentary column is a list is computed, not written:** DIP's CSV has fifteen columns of the station,
  then each list followed by its candidates' preferential votes, with no marker. `results.group_columns` finds the
  grouping in which no candidate, nor all of a list's together, has more votes than the list and the lists add up
  to the valid ballots. A station or two that don't add up are tolerated (a flag, not another grouping).

### Rules from the law

- **Seats:** Act on the Election of Representatives to the Croatian Parliament (NN 98/19): D'Hondt (Art. 40) among
  lists with 5% of the valid votes (Art. 41), 14 seats in I–X and 3 in XI; the minorities' candidates with most
  votes, 3 for the Serb minority and 1 for each other group (Art. 16, 17, 46). The Serb minority's voters may vote
  for up to three candidates, so its votes may add up to three times its valid ballots. XI's seats followed
  turnout before 2011 (2000: 6, 2003: 4, 2007: 5; `Election.xi_seats`). The allocation equals the official
  result of every election since 2000, with the threshold on the valid votes (`tests/test_results.py`).
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
- **Pages:** home (search, where to start), about, every election, every municipality, the stations flagged in two
  or more elections, and for each round its results, its checks, every municipality (with a section per
  constituency its stations voted in: its own first, then voters from elsewhere at its special stations, then the
  minorities) and, for the parliament, every constituency; then every municipality and every polling station
  across elections (*Across elections*).
- **Search** reads `search.json` (municipalities and places, flagged ones first; about 700 kB), in the browser; the
  home page works without it, pointing to the municipalities' index.
- **Look:** the Serbian site's stylesheet and fonts (IBM Plex Sans, Source Serif 4; Latin subsets only).
- **Size:** GitHub Pages publishes up to 1 GB. The places' pages (about 10,600) are in Croatian only, and the
  English pages link to them: in both languages the site passed 1 GB. Pages are written without indentation
  (`site.put`), and the cell labels of the tables on phones are one stylesheet (`static/labels.css`), not
  repeated in every cell. The build runs in parallel processes (`Site.parallel`).
- **Hosting:** GitHub Pages through Actions (`pages.yml`), about 620 MB and 37,000 files with every election
  since 2000, at
  https://izborni-podaci.github.io/izborna-analiza-hr/. Pages must be set to "Source: GitHub Actions" in the
  repository's settings (the maintainer did it on 6 Nov 2026); without it the deploy job fails with a 404.

### Across elections

- **Municipalities** have one key across every round (`places.MunicipalityKeys`): the county and the newest name.
  Renamed ones (`RENAMED`: "SV. FILIP I JAKOV", Murter, Barilovići), Istria's municipalities, whose names are
  bilingual since 2011 ("NOVIGRAD - CITTANOVA"; the older files write the Croatian name), and every part of Zagreb
  (the City's key) join under it. A row that names the municipality only takes the county its name has, never
  one of a name two municipalities share. Stations without a municipality (2003's mixed stations, displaced
  persons, the diaspora voting at home, the special stations of 2007 left without a county) are on their round's
  pages only.
- **Places** are regular stations at home (I–X and the president's), followed forward in time, round by round oldest
  first, so a new election never changes how the earlier ones were joined (`places.follow`): by address, then
  building, then the settlement or area served, then number. A number never joins stations whose addresses or
  buildings clearly differ, whose registers differ more than twice (`SIZE = 2.0`; at 1.5, about 1,500 more places,
  most of them one station split in two; of those joined by address, 1.6% change that much), or that belong to
  another numbering (Zagreb's parts number from 1, the City's numbers are its own). Stations sharing an address or a
  name pair with the places last seen there, the same number first, then the nearest number at one address. 10,612
  places; 3,444 are in all 20 rounds. A place's page is named after its municipality and newest number
  (`s/14-beli-manastir-3.html`; Zagreb's parts after the part); the newest elections' places take the plain names,
  one that ended earlier adds its last round.
- **What the pages say:** rows of numbers for every round and a short text ("Ukratko") that sets the latest
  numbers beside the country's or the municipality's and the earlier elections', computed the same way for
  every place; it states numbers and never judges them (`history.py`).

### Workflows

| Workflow | When | What |
|---|---|---|
| data | by hand | fetch DIP's zips, commit what changed, start **pages** |
| pages | on push to `main`, by hand | build and publish the site |
| test | on push | the whole test suite |

## Known issues and open decisions

- **Elections before 2000** are PDF reports in DIP's archive, not results by polling station; they are not added.
- **Local elections, the European Parliament and referendums** are in DIP's archive too; not added yet.
- **Places are joined by rules, not by DIP's own key:** DIP gives no identifier that lasts from one election to
  the next. A place's page says how each round's station was joined to the earlier ones (address, building,
  settlement or number), so a reader can judge it.
- **Not yet:** an explorer of every station by its numbers, a JSON API by municipality and place, a guide for
  readers, as the Serbian site has.
- **Preferential votes:** who of a list takes its seats is not computed.

## Decisions log

- **6 Nov 2026:** the maintainer asked for the Serbian archive's approach for Croatia, starting with the 2024
  parliamentary and presidential elections, from the zips DIP offers as "Preuzmite sve datoteke". The checks,
  statistics and principles are the Serbian archive's; the site is in Croatian and English.
- **6 Nov 2026, later:** at the maintainer's request, every older parliamentary and presidential election with
  results by polling station (2000–2020) was added. The seats of all seven older parliaments equal the official
  results, the totals equal DIP's own total rows, and the 2000 file's missing column was placed by where its
  parties' votes fall (see *Archive and data*).
- **6 Nov 2026, later:** the maintainer asked to continue the site after the Serbian one ("po uzoru na srpsku
  verziju"): every municipality and every polling station across elections, search on the home page, the
  elections and municipalities indexes, the stations flagged more than once and a home page that starts from
  them. The places' pages are in Croatian only, to stay under GitHub Pages' 1 GB.
