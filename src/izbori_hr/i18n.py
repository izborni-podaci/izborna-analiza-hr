"""The site's text in Croatian and English, and how numbers and names are written in each.

Every string is a pair (hr, en). Numbers of things are written as "label: n", so Croatian needs no plural forms."""

from __future__ import annotations

import re

LANGS = ("hr", "en")

S: dict[str, tuple[str, str]] = {
    # the frame
    "site_name": ("Izborni podaci · Hrvatska", "Election data · Croatia"),
    "tagline": ("Rezultati izbora u Hrvatskoj po biračkim mjestima, s provjerama brojki koje su iste za sve liste i "
                "kandidate.",
                "Croatian election results by polling station, with checks of the numbers that are the same for "
                "every list and candidate."),
    "nav_main": ("Glavna navigacija", "Main navigation"),
    "nav_elections": ("Izbori", "Elections"),
    "nav_about": ("O projektu", "About"),
    "nav_round": ("Ovi izbori", "This election"),
    "menu_label": ("Jezik i izgled", "Language and theme"),
    "theme_dark": ("Tamna tema", "Dark theme"),
    "theme_light": ("Svijetla tema", "Light theme"),
    "crumbs_label": ("Gdje ste", "You are here"),
    "crumbs_home": ("Početna", "Home"),
    "footer_data": ("Podaci: Državno izborno povjerenstvo Republike Hrvatske (DIP), arhiva izbora. Oznake su pitanja, "
                    "ne presude.",
                    "Data: the State Electoral Commission of the Republic of Croatia (DIP), its election archive. "
                    "Flags are questions, not verdicts."),
    "footer_code": ("Izvorni kod i podaci", "Source code and data"),
    "footer_serbia": ("Isti projekt za Srbiju", "The same project for Serbia"),
    "not_found": ("Stranica nije pronađena", "Page not found"),
    "not_found_text": ("Ova stranica ne postoji. Možda pomaže početna stranica.",
                       "This page doesn't exist. The home page may help."),

    # home
    "home_heading": ("Rezultati izbora u Hrvatskoj po biračkim mjestima", "Croatian election results by polling station"),
    "home_lede": ("Brojke svakog biračkog mjesta onako kako ih je objavilo Državno izborno povjerenstvo, s provjerama "
                  "koje traže ono što se ne slaže ili je neuobičajeno. Ista pravila vrijede za sve liste i kandidate.",
                  "Every polling station's numbers as the State Electoral Commission published them, with checks "
                  "that look for what doesn't add up or is unusual. The same rules apply to every list and "
                  "candidate."),
    "principle": ("Oznaka je pitanje, ne presuda: „neuobičajeno, provjerite zapisnik”, nikad „prijevara”.",
                  "A flag is a question, not a verdict: “unusual, check the record”, never “fraud”."),
    "elections_heading": ("Izbori u arhivi", "Elections in the archive"),
    "home_what": ("Što je ovdje", "What is here"),
    "home_what_results": ("Rezultati i mandati po izbornim jedinicama, izračunani iz brojki po biračkim mjestima i "
                          "jednaki službenima.",
                          "Results and seats by constituency, computed from the numbers by polling station and equal "
                          "to the official ones."),
    "home_what_checks": ("Provjere svakog biračkog mjesta: brojke koje se ne slažu i neuobičajeni rezultati.",
                         "Checks of every polling station: numbers that don't add up, and unusual results."),
    "home_what_muns": ("Svaka općina i grad, sa svojim biračkim mjestima.",
                       "Every municipality and city, with its polling stations."),
    "home_what_stats": ("Statistika cijelih izbora i svake općine, s njezinim ograničenjima.",
                        "Statistics for the whole election and each municipality, with their limits."),
    "home_what_data": ("Izvorne datoteke DIP-a u arhivi na GitHubu i oznake u CSV-u.",
                       "DIP's original files in the archive on GitHub, and the flags as CSV."),
    "rounds": ("Krugovi", "Rounds"),
    "round_n": ("{n}. krug", "Round {n}"),
    "election_day": ("Dan izbora", "Election day"),

    # a round
    "kind_parliament": ("Izbori za Hrvatski sabor", "Parliamentary election"),
    "kind_president": ("Izbori za predsjednika Republike", "Presidential election"),
    "results_heading": ("Rezultati", "Results"),
    "check_heading": ("Provjere", "Checks"),
    "nav_check": ("Provjere", "Checks"),
    "municipalities_heading": ("Općine i gradovi", "Municipalities and cities"),
    "stats_heading": ("Statistika", "Statistics"),
    "on_this_page": ("Na ovoj stranici", "On this page"),
    "source": ("Izvor", "Source"),
    "source_page": ("stranica izbora u arhivi DIP-a", "the election's page in DIP's archive"),
    "source_zip": ("sve datoteke (zip)", "every file (zip)"),
    "source_raw": ("datoteke u ovoj arhivi", "the files in this archive"),
    "fetched": ("preuzeto", "fetched"),
    "registered": ("Upisani birači", "Registered voters"),
    "voted": ("Glasovalo", "Voted"),
    "voted_register": ("Glasovalo po popisu", "Voted by the register"),
    "turnout": ("Izlaznost", "Turnout"),
    "ballots": ("Listića u kutiji", "Ballots in the box"),
    "valid": ("Važeći listići", "Valid ballots"),
    "invalid": ("Nevažeći listići", "Invalid ballots"),
    "stations": ("Biračka mjesta", "Polling stations"),
    "station": ("Biračko mjesto", "Polling station"),
    "station_no": ("BM", "No."),
    "flags": ("Oznake", "Flags"),
    "flagged": ("S oznakom", "Flagged"),
    "flagged_share": ("Udio s oznakom", "Share flagged"),
    "no": ("Br.", "No."),
    "list": ("Lista", "List"),
    "candidate": ("Kandidat", "Candidate"),
    "votes": ("Glasovi", "Votes"),
    "seats": ("Mandati", "Seats"),
    "share_valid": ("% važećih", "% of valid"),
    "share_voted": ("% glasovalih", "% of voters"),
    "status": ("Status", "Status"),
    "below_threshold": ("ispod praga", "below the threshold"),
    "elected": ("izabran/a", "elected"),
    "total": ("Ukupno", "Total"),
    "others": ("Ostali", "Others"),
    "county": ("Županija", "County"),
    "municipality": ("Općina ili grad", "Municipality or city"),
    "abroad": ("Inozemstvo", "Abroad"),
    "kind_abroad": ("u inozemstvu", "abroad"),
    "kind_special": ("posebno biračko mjesto", "special polling station"),
    "home_tiles_note": ("Izborne jedinice I–X: birači s prebivalištem u Hrvatskoj, na biračkim mjestima u zemlji, u "
                        "inozemstvu i na posebnim biračkim mjestima. XI. i XII. jedinica broje se zasebno.",
                        "Constituencies I–X: voters resident in Croatia, at polling stations at home, abroad and at "
                        "special stations. Constituencies XI and XII are counted apart."),
    "seats_heading": ("Mandati u Saboru", "Seats in parliament"),
    "seats_national_note": ("Liste su zbrojene po prvoj stranci navedenoj na listi; koalicije se razlikuju od "
                            "jedinice do jedinice.",
                            "Lists are added up by the first party named on each; coalitions differ from one "
                            "constituency to another."),
    "lead_party": ("Prva stranka na listi", "First party on the list"),
    "units_ran": ("Jedinice", "Constituencies"),
    "minorities": ("Nacionalne manjine (XII. jedinica)", "National minorities (constituency XII)"),
    "majority_line": ("većina: {n}", "majority: {n}"),
    "seats_rule": ("Mandati po Zakonu o izborima zastupnika u Hrvatski sabor (danas NN 98/19, ranije kako je tada "
                   "glasio): u jedinicama I–X bira se po 14 zastupnika, u XI. {xi}, D'Hondtovom metodom među listama "
                   "s najmanje 5 % važećih glasova u jedinici (čl. 40. i 41.). Pripadnici nacionalnih manjina u XII. jedinici biraju osam zastupnika: "
                   "izabrani su kandidati s najviše glasova (čl. 16., 17. i 46.). Raspodjela se ovdje računa iz "
                   "glasova po biračkim mjestima i jednaka je službenom rezultatu. Tko s liste dobiva mandat "
                   "(preferencijski glasovi od 2015., čl. 40.) ovdje se ne računa.",
                   "Seats as the Act on the Election of Representatives to the Croatian Parliament (today OG 98/19, "
                   "before as it then stood) allocates them: 14 in each of constituencies I–X and {xi} in XI, by the "
                   "D'Hondt method among the "
                   "lists with at least 5% of the valid votes in the constituency (Art. 40 and 41). The national "
                   "minorities elect eight representatives in constituency XII: the candidates with the most votes "
                   "(Art. 16, 17 and 46). The allocation here is computed from the votes by polling station and "
                   "equals the official result. Who on a list takes its seats (preferential votes since 2015, Art. 40) "
                   "is not computed here."),

    # what a round's files lack
    "note_ballots_derived": ("DIP-ove datoteke ovog kruga ne navode broj listića u kutiji: umjesto njega stoji zbroj "
                             "važećih i nevažećih listića, pa se potpisi uspoređuju s njim, a provjera „važeći i "
                             "nevažeći ne daju broj listića” se ne radi.",
                             "DIP's files for this round don't give the ballots in the box: valid plus invalid "
                             "ballots stand in for them, signatures are compared with that sum, and the check “valid "
                             "and invalid don't make the ballots” isn't made."),
    "note_voted_from_ballots": ("DIP-ove datoteke ovog kruga navode samo broj glasovalih po listićima: on stoji i za "
                                "broj glasovalih po popisu birača, pa se potpisi i listići ne mogu usporediti.",
                                "DIP's files for this round give only the voters counted by the ballots: that number "
                                "stands for the register's count too, so signatures and ballots can't be compared."),
    "note_abroad_by_country": ("Glasovi iz inozemstva u DIP-ovim su datotekama zbrojeni po državama, ne po biračkim "
                               "mjestima.",
                               "DIP's files add up the votes abroad by country, not by polling station."),
    "note_no_xi_xii": ("DIP-ova arhiva za ove izbore ima rezultate po biračkim mjestima samo za jedinice I–X: XI. "
                       "jedinica (birači bez prebivališta u Hrvatskoj) i nacionalne manjine nisu uključeni, pa ni "
                       "njihovi mandati.",
                       "DIP's archive for this election has results by polling station for constituencies I–X "
                       "only: constituency XI (voters living abroad) and the national minorities are not included, "
                       "nor their seats."),
    "units_heading": ("Izborne jedinice", "Constituencies"),
    "unit": ("Izborna jedinica", "Constituency"),
    "unit_seats": ("Raspodjela mandata", "Seats won"),
    "threshold_line": ("Prag od 5 % važećih glasova: {n} glasova.", "The 5% threshold of the valid votes: {n} votes."),
    "serb_note": ("Birači srpske nacionalne manjine mogu glasovati za do tri kandidata, pa postoci važećih listića "
                  "zajedno prelaze 100 %.",
                  "Voters of the Serb national minority may vote for up to three candidates, so the shares of "
                  "valid ballots add up to more than 100%."),
    "minority_note": ("Pripadnici manjine mogu glasovati na bilo kojem biračkom mjestu, pa se njihovi upisani birači "
                      "i izlaznost ovdje ne prikazuju.",
                      "The minority's voters may vote at any polling station, so registered voters and turnout "
                      "aren't shown for them."),
    "pres_rule": ("Predsjednik Republike bira se većinom glasova svih birača koji su glasovali (Ustav, čl. 94.); ako "
                  "je nitko ne dobije, nakon 14 dana održava se drugi krug između dvoje kandidata s najviše glasova. "
                  "Prvi stupac postotaka računa se od birača koji su glasovali, kao i ta većina (i kao u DIP-ovim "
                  "tablicama prvog kruga); drugi od važećih listića.",
                  "The President is elected by a majority of the votes of all voters who voted (Constitution, "
                  "Art. 94); if no one gets it, a second round between the two leading candidates follows 14 days "
                  "later. The first column of shares is of the voters who voted, like that majority (and like DIP's "
                  "first-round tables); the second of the valid ballots."),
    "pres_runoff": ("Nitko nije dobio više od polovice glasova birača koji su glasovali ({needed} glasova). U drugi "
                    "krug idu {a} i {b}.",
                    "No one won more than half of the votes of those who voted ({needed} votes). {a} and {b} go to "
                    "the second round."),
    "pres_elected": ("{name}: {share} glasova birača koji su glasovali, više od polovice potrebne za izbor.",
                     "{name}: {share} of the votes of those who voted, more than the half needed to be elected."),
    "marker_half": ("Crta označava polovicu glasova birača koji su glasovali.",
                    "The line marks half of the votes of those who voted."),
    "marker_threshold": ("Crta označava prag od 5 %.", "The line marks the 5% threshold."),
    "unit_link": ("Rezultati jedinice", "The constituency's results"),
    "unit_muns": ("Općine i gradovi u jedinici", "Municipalities and cities in the constituency"),
    "search_mun": ("Traži općinu ili grad", "Find a municipality or city"),
    "spotlight_rest": ("od {total} biračkih mjesta ima barem jednu oznaku ({share}).",
                       "of {total} polling stations have at least one flag ({share})."),
    "spotlight_contests": ("Biračko mjesto broji se jednom po jedinici u kojoj je glasovalo.",
                           "A polling station counts once for each constituency voted at it."),
    "see_all_flags": ("Sve oznake", "Every flag"),
    "groups_explained": ("Što provjere traže", "What the checks look for"),
    "rules_link": ("Pravila i pragovi", "Rules and thresholds"),

    # checks
    "check_lede": ("Svako biračko mjesto s oznakom, s brojkama koje su je dale. Brojke su DIP-ove; zapisnik biračkog "
                   "odbora je ono što treba provjeriti.",
                   "Every flagged polling station, with the numbers behind the flag. The numbers are DIP's; the "
                   "polling board's record is what to check."),
    "check_count": ("Biračka mjesta s oznakom: {n}", "Flagged polling stations: {n}"),
    "filter_contest": ("Izborna jedinica", "Constituency"),
    "filter_type": ("Vrsta provjere", "Kind of check"),
    "filter_municipality": ("Općina ili grad", "Municipality or city"),
    "filter_search": ("Traži", "Search"),
    "filter_all": ("Sve", "All"),
    "filter_group_all": ("cijela skupina", "the whole group"),
    "filter_shown": ("Prikazano: {n}", "Shown: {n}"),
    "no_flags": ("Nijedno biračko mjesto nema oznaku.", "No polling station is flagged."),
    "what_to_check": ("Što provjeriti", "What to check"),
    "flags_csv": ("Oznake u CSV-u", "The flags as CSV"),
    "group_paper": ("Brojke se ne slažu", "The numbers don't add up"),
    "group_paper_note": ("Brojke samog biračkog mjesta (listići, potpisi, glasovi) ne slažu se međusobno.",
                         "The station's own numbers (ballots, signatures, votes) don't agree with each other."),
    "group_unusual": ("Neuobičajeno", "Unusual"),
    "group_unusual_note": ("Jednostrani ili ponovljeni rezultati; često su zakoniti, pa najmanje teže.",
                           "Lopsided or repeated results; often legitimate, so they weigh least."),

    # municipality
    "stations_heading": ("Biračka mjesta", "Polling stations"),
    "mun_votes_note": ("Udjeli triju lista ili kandidata s najviše glasova u općini; brojevi glasova u opisu ćelije.",
                       "Shares of the three lists or candidates with the most votes in the municipality; the votes "
                       "in each cell's tooltip."),
    "mun_result": ("Rezultat u općini", "Result in the municipality"),
    "special_note": ("Na posebnim biračkim mjestima (domovi za starije, bolnice, zatvori, brodovi) glasuju birači iz "
                     "raznih jedinica; svaka jedinica ima svoj red.",
                     "At special polling stations (care homes, hospitals, prisons, ships) voters of several "
                     "constituencies vote; each constituency has its own row."),

    # statistics
    "stats_note": ("Ovi testovi pokazuju ponašaju li se brojke kako se očekuje na velikom broju biračkih mjesta. Slabi "
                   "su signali i sami ništa ne dokazuju. Broje se samo redovna biračka mjesta u zemlji (u jedinicama "
                   "I–X), sa 100 i više upisanih.",
                   "These tests show whether the numbers behave as expected across many polling stations. They are "
                   "weak signals and prove nothing on their own. Only regular stations at home count (in "
                   "constituencies I–X), with 100 or more registered voters."),
    "hist_heading": ("Izlaznost po biračkim mjestima", "Turnout across polling stations"),
    "hist_note": ("Broj biračkih mjesta po izlaznosti, u koracima od jednog postotnog boda.",
                  "Polling stations by turnout, in steps of one point."),
    "digits_heading": ("Posljednje znamenke", "Last digits"),
    "digits_note": ("Za brojeve glasova od 100 i više svaka bi se posljednja znamenka trebala javiti u oko 10 % "
                    "slučajeva. p je vjerojatnost ovako nejednake raspodjele slučajno.",
                    "For vote counts of 100 or more, each last digit should come up about 10% of the time. p is the "
                    "chance of a spread this uneven by chance."),
    "round_heading": ("Okrugli postoci", "Round percentages"),
    "round_note": ("Biračka mjesta gdje izlaznost ili udio pada na 0,05 boda od cijelog postotka, i koliko bi ih bilo "
                   "slučajno. Očekivani broj ovisi o nazivniku svakog mjesta: od 500 glasova svaki peti broj daje "
                   "cijeli postotak, od 737 svaki deseti. p je vjerojatnost da ih slučajno bude barem ovoliko.",
                   "Stations where turnout or a share lands within 0.05 points of a whole percent, against the number "
                   "expected by chance. The expected number depends on each station's denominator: of 500 votes "
                   "every fifth count is a whole percent, of 737 every tenth. p is the chance of at least this many "
                   "by chance."),
    "measure": ("Mjera", "Measure"),
    "share_of": ("udio: {name}", "share: {name}"),
    "on_whole": ("Na cijelom postotku", "On a whole percent"),
    "expected": ("Očekivano", "Expected"),
    "counts": ("Brojeva", "Counts"),
    "p_adjusted": ("p nakon korekcije", "Corrected p"),
    "local_heading": ("Po općinama", "By municipality"),
    "local_note": ("Isti testovi za svaku općinu s dovoljno podataka. Među toliko testova poneki p slučajno ispadne "
                   "malen, pa se svaki množi brojem testiranih općina (Bonferronijeva korekcija). Ispod 0,05 i nakon "
                   "nje vrijedi pogledati zapisnike; iznad, odstupanje se ne razlikuje od slučaja. Prikazano je pet "
                   "općina s najmanjim p.",
                   "The same tests for each municipality with enough data. Among so many tests some p comes out "
                   "small by chance, so each is multiplied by the number of municipalities tested (the Bonferroni "
                   "correction). Below 0.05 even after it, the records are worth a look; above, the deviation is "
                   "indistinguishable from chance. The five municipalities with the smallest p are shown."),
    "local_round_note": ("Izlaznost i udjeli dviju lista ili kandidata s najviše glasova zajedno, u općinama gdje se "
                         "slučajno očekuje barem 5 pogodaka. Testirano općina: {n}; ispod 0,05: {k}.",
                         "Turnout and the shares of the two leading lists or candidates together, in municipalities "
                         "expecting at least 5 hits by chance. Municipalities tested: {n}; below 0.05: {k}."),
    "local_digits_note": ("Svi brojevi glasova od 100 i više, svih lista i kandidata, u općinama s barem 50 takvih "
                          "brojeva. Testirano općina: {n}; ispod 0,05: {k}.",
                          "Every vote count of 100 or more, of every list and candidate, in municipalities with at "
                          "least 50 of them. Municipalities tested: {n}; below 0.05: {k}."),

    # about
    "about_heading": ("O projektu", "About"),
    "about_lede": ("Arhiva rezultata izbora u Hrvatskoj po biračkim mjestima, s provjerama brojki. Nastala je po "
                   "uzoru na istu arhivu za Srbiju, s istim pravilima, da se dvije zemlje mogu čitati jedna uz drugu.",
                   "An archive of Croatian election results by polling station, with checks of the numbers. It "
                   "follows the same archive for Serbia, with the same rules, so the two countries can be read side "
                   "by side."),
    "principles_heading": ("Načela", "Principles"),
    "pr_same": ("Ista pravila za sve liste i kandidate. Nijedna stranka nije upisana u kod; test zamijeni glasove "
                "lista i provjeri da se oznake ne mijenjaju.",
                "The same rules for every list and candidate. No party is written into the code; a test swaps the "
                "lists' votes and checks that the flags don't change."),
    "pr_question": ("Oznaka je pitanje, ne presuda. Stranica kaže „neuobičajeno, provjerite zapisnik”, nikad "
                    "„prijevara”.",
                    "A flag is a question, not a verdict. The site says “unusual, check the record”, never “fraud”."),
    "pr_primary": ("Oznake dolaze samo iz primarnih izvora: brojki koje je objavio DIP.",
                   "Flags come from primary sources only: the numbers DIP published."),
    "pr_private": ("Bez osobnih podataka. Arhiva ne bilježi ništa o članovima biračkih odbora ni o promatračima; "
                   "imena su samo ona lista i kandidata, kako ih objavljuje DIP. Za sve ostalo poveznica vodi na DIP.",
                   "No personal data. The archive records nothing about polling board members or observers; the "
                   "only names are those of the lists and candidates, as DIP publishes them. For anything else, a "
                   "link leads to DIP."),
    "pr_third": ("Ništa od trećih strana na stranicama: bez analitike, kolačića, vanjskih fontova i skripti.",
                 "Nothing from third parties on the pages: no analytics, cookies, external fonts or scripts."),
    "sources_heading": ("Izvori", "Sources"),
    "sources_text": ("Za svake izbore arhiva preuzima DIP-ov zip s rezultatima po biračkim mjestima („Preuzmite sve "
                     "datoteke”) i čuva ga u gitu, s vremenom preuzimanja i sažetkom (SHA-256) svake datoteke. Datoteka "
                     "se zapisuje samo kad se promijeni, pa je povijest repozitorija zapis onoga što je DIP objavio.",
                     "For each election the archive downloads DIP's zip of results by polling station (“Preuzmite sve "
                     "datoteke”) and keeps it in git, with the time it was fetched and a digest (SHA-256) of every "
                     "file. A file is written only when it changes, so the repository's history is a record of what "
                     "DIP published."),
    "data_heading": ("Kako čitati podatke", "How to read the data"),
    "data_kinds": ("Biračka mjesta u inozemstvu i posebna biračka mjesta (domovi za starije, bolnice, zatvori, "
                   "brodovi) imaju kao upisane birače one koji su došli, pa se za njih provjerava samo aritmetika. Isto "
                   "vrijedi za XII. jedinicu: pripadnici manjina mogu glasovati na bilo kojem biračkom mjestu.",
                   "At stations abroad and at special stations (care homes, hospitals, prisons, ships) the register "
                   "is the voters who came, so only their arithmetic is checked. The same holds for constituency "
                   "XII: the minorities' voters may vote at any station."),
    "data_columns": ("DIP-ove datoteke za Sabor ne kažu koji je stupac lista, a koji preferencijski glasovi njezinih "
                     "kandidata. Lista je stupac iza kojeg nijedan kandidat nema više glasova od nje, a liste zajedno "
                     "daju važeće listiće; postoji samo jedna takva podjela.",
                     "DIP's parliamentary files don't say which column is a list and which its candidates' "
                     "preferential votes. A list is the column after which no candidate has more votes than it, and "
                     "the lists together make the valid ballots; only one such grouping exists."),
    "data_zagreb": ("Zagreb je u datotekama za Sabor podijeljen na dijelove u I., II. i VI. jedinici, svaki sa svojim "
                    "brojevima biračkih mjesta; predsjednički izbori imaju Grad Zagreb u cjelini.",
                    "In the parliamentary files Zagreb is split into its parts in constituencies I, II and VI, each "
                    "numbering its own stations; the presidential election has the City of Zagreb whole."),
    "data_president": ("U predsjedničkim datotekama posebna biračka mjesta imaju brojeve od 901.",
                       "In the presidential files special stations are numbered from 901."),
    "data_older": ("Starije DIP-ove datoteke svaka su na svoj način: 2007. i 2011. izvještaji po jedinicama s "
                   "posebnim biračkim mjestima i onima u inozemstvu, 2003. redovita i „mješovita” biračka mjesta "
                   "(veleposlanstva, klubovi u inozemstvu, prognanici, ustanove), 2000. liste samo pod brojevima. "
                   "Čitaju se po nazivima stupaca, a zbrojevi su jednaki DIP-ovim zbrojevima u istim datotekama. Što "
                   "datoteka nema, ne izmišlja se: stranica kruga to kaže.",
                   "DIP's older files each have their own layout: 2007 and 2011 reports by constituency with special "
                   "stations and those abroad, 2003 regular and “mixed” stations (embassies, clubs abroad, displaced "
                   "persons, institutions), 2000 lists by number only. They are read by their columns' names, and "
                   "the totals equal DIP's own totals in the same files. What a file lacks isn't made up: the "
                   "round's page says so."),
    "data_2000": ("2000., V. jedinica: DIP-ov popis ima 26 lista, a datoteka 25 stupaca koji daju zbroj važećih "
                  "listića. Lista 19 (Nova Hrvatska) nema stupca: stupac 19 ima glasove Partije podunavskih Srba "
                  "(Trpinja, Vukovar, Negoslavci, Borovo), a stupac 22 26,7 % koalicije SDP-a i HSLS-a, čijih pet "
                  "mandata ondje daje njezinih 71 iz službenog rezultata.",
                  "2000, constituency V: DIP's list has 26 lists and the file 25 columns, which make the valid "
                  "ballots. List 19 (Nova Hrvatska) has no column: column 19 holds the votes of the Party of Danube "
                  "Serbs (Trpinja, Vukovar, Negoslavci, Borovo), column 22 the 26.7% of the SDP–HSLS coalition, "
                  "whose five seats there make its 71 of the official result."),
    "checks_heading": ("Provjere i pragovi", "Checks and thresholds"),
    "checks_text": ("Provjere su iste kao u arhivi za Srbiju. Svaka je pitanje o jednom biračkom mjestu; pragovi su "
                    "isti za sve.",
                    "The checks are the Serbian archive's. Each is a question about one polling station; the "
                    "thresholds are the same for all."),
    "rule_signed_over_ballots": ("Više potpisa nego listića: od {n} naviše (birač može otići s listićem).",
                                 "More signatures than ballots: from {n} up (a voter may leave with a ballot)."),
    "rule_typo": ("Izlaznost točno 100 %: barem {n} upisanih, gdje je medijan općine ispod {median}.",
                  "Turnout of exactly 100%: at least {n} registered, where the municipality's median is below "
                  "{median}."),
    "rule_high": ("Izlaznost {turnout} ili viša, uz barem {n} upisanih; s udjelom jedne liste ili kandidata od "
                  "{share} naviše to je gotovo jednoglasan rezultat.",
                  "Turnout of {turnout} or more, with at least {n} registered; with one list or candidate at "
                  "{share} or more it is a near-unanimous result."),
    "rule_invalid": ("Mnogo nevažećih: {abs} listića uz barem {voted} glasovalih, ili barem {min} nevažećih i "
                     "{rel_share} listića, {factor} puta više od medijana na istoj adresi ili u općini.",
                     "Many invalid ballots: {abs} of the ballots with at least {voted} voters, or at least {min} "
                     "invalid and {rel_share} of the ballots, {factor} times the median at the same address or in "
                     "the municipality."),
    "rule_identical": ("Isti glasovi kao na drugom biračkom mjestu iste općine: barem {votes} glasova i {lists} liste "
                       "ili kandidata s glasovima.",
                       "Same votes as another station of the municipality: at least {votes} votes and {lists} lists "
                       "or candidates with votes."),
    "stats_about": ("Statistike (posljednje znamenke, okrugli postoci) nikad nisu oznake biračkih mjesta: test na "
                    "mnogo mjesta ne može reći koje je neobično.",
                    "Statistics (last digits, round percentages) are never station flags: a test over many stations "
                    "can't say which one is unusual."),
}

S.update({
    # home
    "nav_municipalities": ("Općine i gradovi", "Municipalities"),
    "search_field": ("Općina, grad ili biračko mjesto", "Municipality, city or polling station"),
    "search_placeholder": ("npr. Vukovar ili Split 25", "e.g. Vukovar or Split 25"),
    "search_button": ("Traži", "Search"),
    "search_none": ("Ništa nije pronađeno.", "Nothing found."),
    "search_mun_sub": ("općina ili grad · izbora: {n}", "municipality · elections: {n}"),
    "search_flagged": ("s oznakom na {k} od {n} izbora", "flagged in {k} of {n} elections"),
    "search_clean": ("bez oznake · izbora: {n}", "no flag · elections: {n}"),
    "search_former": ("ranije BM {n}", "formerly station {n}"),
    "stats_line": ("Izbora i krugova: {n} ({first}–{last}) · biračkih mjesta kroz izbore: {places} · općina i gradova: "
                   "{muns}",
                   "Elections and rounds: {n} ({first}–{last}) · polling stations across elections: {places} · "
                   "municipalities: {muns}"),
    "intents_heading": ("Odakle krenuti", "Where to start"),
    "intent_check_title": ("Što je neuobičajeno", "What's unusual"),
    "intent_check_body": ("Biračka mjesta s oznakom: {n} od {total}.", "Flagged polling stations: {n} of {total}."),
    "intent_check_cta": ("Provjere", "The checks"),
    "intent_repeat_kicker": ("Svi izbori od 2000.", "Every election since 2000"),
    "intent_repeat_body": ("Biračka mjesta s oznakom na dvoje ili više izbora: {n}.",
                           "Polling stations flagged in two or more elections: {n}."),
    "intent_mun_kicker": ("Kroz izbore", "Across elections"),
    "intent_mun_title": ("Općina ili grad", "A municipality or city"),
    "intent_mun_body": ("Izlaznost, nevažeći listići, tko je dobio najviše glasova i oznake, na svakim izborima.",
                        "Turnout, invalid ballots, who had most votes and the flags, at every election."),
    "intent_elections_kicker": ("Arhiva", "The archive"),
    "intent_elections_title": ("Svi izbori", "Every election"),
    "intent_elections_body": ("Sabor i predsjednik od 2000., svaki krug: rezultati, mandati, provjere, statistika.",
                              "Parliament and president since 2000, every round: results, seats, checks, "
                              "statistics."),
    "intent_data_kicker": ("Podaci", "The data"),
    "intent_data_title": ("Izvori i način rada", "Sources and method"),
    "intent_data_body": ("DIP-ove datoteke u arhivi na GitHubu, oznake u CSV-u, pravila provjera.",
                         "DIP's files in the archive on GitHub, the flags as CSV, the rules of the checks."),
    "read_heading": ("Kako čitati stranice", "How to read the pages"),
    "read1_title": ("Brojke su DIP-ove", "The numbers are DIP's"),
    "read1_body": ("Svaka brojka dolazi iz DIP-ovih datoteka po biračkim mjestima; ništa se ne procjenjuje.",
                   "Every number comes from DIP's files by polling station; nothing is estimated."),
    "read2_title": ("Oznaka je pitanje", "A flag is a question"),
    "read2_body": ("Brojke koje se ne slažu ili neobičan rezultat: često postoji obično objašnjenje.",
                   "Numbers that don't add up, or an unusual result: often there is an ordinary explanation."),
    "read3_title": ("Odgovor je u zapisniku", "The record has the answer"),
    "read3_body": ("Zapisnik biračkog odbora i primjedbe njegovih članova kažu što se dogodilo.",
                   "The polling board's record and its members' remarks say what happened."),
    "trust_source": ("Izvor: DIP, arhiva izbora", "Source: DIP's election archive"),
    "trust_same": ("Ista pravila za sve liste i kandidate", "The same rules for every list and candidate"),
    "trust_code": ("Otvoreni kod i podaci", "Open code and data"),
    "trust_private": ("Bez osobnih podataka, analitike i kolačića", "No personal data, analytics or cookies"),
    "elections_lede": ("Svi izbori u arhivi, s izlaznošću i brojem biračkih mjesta s oznakom.",
                       "Every election in the archive, with turnout and the number of flagged polling stations."),
    "mun_index_lede": ("Svaka općina i grad abecednim redom, s brojem izbora u arhivi i biračkih mjesta na "
                       "posljednjima. Države su na kraju. Biračka mjesta koja DIP-ove datoteke ne smještaju u "
                       "općinu (mješovita 2003., prognanici, dijaspora koja glasuje u Hrvatskoj) su samo na "
                       "stranicama svojih izbora.",
                       "Every municipality and city in alphabetical order, with the number of elections in the "
                       "archive and its polling stations at the latest. Countries come last. Polling stations that "
                       "DIP's files don't place in a municipality (2003's mixed stations, displaced persons, the "
                       "diaspora voting in Croatia) are on their own election's pages only."),
    "mun_index_elections": ("Izbora", "Elections"),
    "mun_index_stations": ("Biračkih mjesta", "Polling stations"),
    "countries": ("Države (birališta u inozemstvu)", "Countries (stations abroad)"),

    # across elections
    "across": ("Kroz sve izbore", "Across all elections"),
    "an_heading": ("Ukratko", "In short"),
    "an_context_mun": ("Brojke posljednjih izbora uz ostale; općina se uspoređuje s cijelom zemljom.",
                       "The latest election's figures beside the others; the municipality is compared with the "
                       "whole country."),
    "an_context_place": ("Brojke posljednjih izbora uz ostale; biračko mjesto se uspoređuje sa svojom općinom.",
                         "The latest election's figures beside the others; the polling station is compared with its "
                         "municipality."),
    "an_note": ("Tekst je napisan iz brojki, istim pravilima za svako mjesto, i ne ocjenjuje ih.",
                "The text is written from the numbers, by the same rules for every place, and doesn't judge them."),
    "an_flags": ("Oznake", "Flags"),
    "an_flagged_latest": ("{title}: s oznakom {n} od {total} biračkih mjesta",
                          "{title}: {n} of {total} polling stations flagged"),
    "an_flagged_elections": ("Izbora s barem jednom oznakom: {k} od {n}", "Elections with at least one flag: {k} of {n}"),
    "an_turnout_vs": ("{title}: {x} ({ref}: {y})", "{title}: {x} ({ref}: {y})"),
    "an_ref_country": ("cijela zemlja", "the whole country"),
    "an_ref_mun": ("općina", "the municipality"),
    "an_turnout_before": ("Prethodni izbori iste vrste ({title}): {y}", "The previous election of the kind ({title}): {y}"),
    "an_most": ("Najviše glasova", "Most votes"),
    "an_lead": ("{title}: {name}, {share}", "{title}: {name}, {share}"),
    "an_lead_country": ("U cijeloj zemlji: {name}, {share}", "In the whole country: {name}, {share}"),
    "an_lead_mun": ("U općini: {name}, {share}", "In the municipality: {name}, {share}"),
    "an_stations": ("{title}: {n}", "{title}: {n}"),
    "an_stations_first": ("{title}: {n}", "{title}: {n}"),
    "an_place_flagged": ("S oznakom na {k} od {n} izbora", "Flagged in {k} of {n} elections"),
    "an_place_flagged_last": ("Posljednji put: {title} ({names})", "Last: {title} ({names})"),
    "an_place": ("Mjesto", "The place"),
    "an_followed": ("Praćeno kroz izbora: {n}, od {title}", "Followed through {n} elections, from {title}"),
    "place_former": ("Ranije BM {numbers}", "Formerly station {numbers}"),
    "trend_label": ("Kroz izbore", "Across elections"),
    "trend_turnout": ("Izlaznost", "Turnout"),
    "trend_invalid": ("Nevažeći listići", "Invalid ballots"),
    "trend_here_mun": ("Općina", "The municipality"),
    "trend_ref_all": ("Cijela zemlja", "The whole country"),
    "trend_here_place": ("Biračko mjesto", "The polling station"),
    "trend_ref_mun": ("Općina", "The municipality"),
    "trend_note": ("Puna točka: Sabor; prazna: krug predsjedničkih izbora. Pokazivač nad stupcem daje izbore i "
                   "brojke.",
                   "Filled dot: parliament; hollow: a presidential round. Hovering over a column gives the election "
                   "and the figures."),
    "mun_across_lede": ("Jedan red za svake izbore na kojima je općina bila; svaki vodi na njezinu stranicu tih "
                        "izbora.",
                        "One row for every election the municipality took part in; each leads to its page of that "
                        "election."),
    "col_election": ("Izbori", "Election"),
    "top_three": ("Najviše glasova", "Most votes"),
    "mun_places_heading": ("Biračka mjesta kroz izbore", "Polling stations across elections"),
    "place_rule": ("Biračka mjesta prate se kroz izbore po adresi, zgradi i nazivu, a gdje toga nema (do 2009.) po "
                   "broju; broj nikad ne spaja mjesta s različitom adresom ili zgradom.",
                   "Polling stations are followed across elections by address, building and name, and where those "
                   "are missing (until 2009) by number; a number never joins places whose address or building "
                   "differs."),
    "zagreb_note": ("Datoteke za Sabor dijele Zagreb na dijelove s vlastitim brojevima biračkih mjesta; ovdje su "
                    "zajedno, a mjesta se kroz izbore spajaju po adresi i, unutar istog dijela, po broju.",
                    "The parliamentary files split Zagreb into parts that number their own stations; here they are "
                    "together, and stations are joined across elections by address and, within one part, by "
                    "number."),
    "col_elections": ("Izbora", "Elections"),
    "col_flagged": ("S oznakom", "Flagged"),
    "joined_address": ("po adresi", "by address"),
    "joined_location": ("po zgradi", "by building"),
    "joined_name": ("po nazivu", "by name"),
    "joined_number": ("po broju", "by number"),
    "place_lede": ("Jedan red za svake izbore na kojima je ovo biračko mjesto postojalo.",
                   "One row for every election this polling station existed at."),
    "address": ("Adresa", "Address"),
    "area": ("Naziv", "Name"),
    "no_flag": ("bez oznake", "no flag"),
    "repeat_title": ("Više puta s oznakom", "Flagged more than once"),
    "repeat_lede": ("Biračka mjesta s oznakom na dvoje ili više izbora, praćena kroz izbore. I ponovljena oznaka je "
                    "pitanje: mjesto s mnogo nevažećih listića može ih imati na svakim izborima.",
                    "Polling stations flagged in two or more elections, followed across elections. A repeated flag "
                    "is still a question: a place with many invalid ballots may have them at every election."),
    "repeat_count": ("Biračka mjesta s oznakom na dvoje ili više izbora: {n}",
                     "Polling stations flagged in two or more elections: {n}"),
    "repeat_k": ("Izbora s oznakom", "Elections flagged"),
    "repeat_checks": ("Provjere", "Checks"),
    "repeat_last": ("Posljednja oznaka", "Last flagged"),
    "see_across": ("Kroz sve izbore", "Across all elections"),
    "places_in_croatian": ("", "The polling stations' pages are in Croatian only, to keep the site within GitHub's "
                               "limit of 1 GB."),
})

# the checks: name, the sentence with its numbers, and what to look at
CHECK_TEXT: dict[str, dict[str, tuple[str, str]]] = {
    "sum_mismatch": {
        "name": ("Glasovi se ne zbrajaju u važeće listiće", "Votes don't add up to the valid ballots"),
        "text": ("Zbroj glasova {sum}, važećih listića {valid}.", "The votes add up to {sum}; valid ballots {valid}."),
        "hint": ("Usporedite zapisnik biračkog odbora s objavljenim brojkama: glasovi lista ili kandidata moraju dati "
                 "broj važećih listića.",
                 "Compare the polling board's record with the published numbers: the votes must add up to the valid "
                 "ballots."),
    },
    "ballot_mismatch": {
        "name": ("Važeći i nevažeći ne daju broj listića", "Valid and invalid don't make the ballots"),
        "text": ("Važećih {valid} i nevažećih {invalid}, a listića u kutiji {ballots}.",
                 "Valid {valid} and invalid {invalid}; ballots in the box {ballots}."),
        "hint": ("U zapisniku važeći i nevažeći listići zajedno moraju dati broj listića u glasačkoj kutiji.",
                 "In the record, valid and invalid ballots together must make the number of ballots in the box."),
    },
    "ballots_over_signed": {
        "name": ("Više listića nego potpisa", "More ballots than signatures"),
        "text": ("Listića u kutiji {ballots}, glasovalo po popisu {voted} (+{diff}).",
                 "Ballots in the box {ballots}, voted by the register {voted} (+{diff})."),
        "hint": ("U kutiji je više listića nego birača zaokruženih u izvodu iz popisa birača: provjerite zapisnik i "
                 "primjedbe članova odbora.",
                 "More ballots in the box than voters marked in the register: check the record and the board "
                 "members' remarks."),
    },
    "signed_over_ballots": {
        "name": ("Više potpisa nego listića", "More signatures than ballots"),
        "text": ("Glasovalo po popisu {voted}, listića u kutiji {ballots} (−{diff}).",
                 "Voted by the register {voted}, ballots in the box {ballots} (−{diff})."),
        "hint": ("Birač može otići s listićem; nekoliko je uobičajeno, više vrijedi provjeriti u zapisniku.",
                 "A voter may leave with the ballot; a few is common, more is worth checking in the record."),
    },
    "signed_over_registered": {
        "name": ("Glasovalo više birača nego je upisano", "More voters than registered"),
        "text": ("Glasovalo {voted}, upisano {registered} (+{diff}).", "Voted {voted}, registered {registered} (+{diff})."),
        "hint": ("Provjerite izvod iz popisa birača i potvrde za glasovanje izvan mjesta prebivališta.",
                 "Check the register and the certificates for voting away from home."),
    },
    "full_turnout_typo": {
        "name": ("Izlaznost točno 100 %", "Turnout of exactly 100%"),
        "text": ("Glasovalo svih {registered} upisanih; medijan općine {median}.",
                 "All {registered} registered voters voted; the municipality's median is {median}."),
        "hint": ("Provjerite je li u zapisnik upisan broj upisanih birača umjesto broja onih koji su glasovali.",
                 "Check whether the number registered was entered as the number who voted."),
    },
    "prefs_over_list": {
        "name": ("Preferencijski glasovi veći od glasova liste", "Preferential votes above the list's votes"),
        "text": ("{lists}.", "{lists}."),
        "hint": ("Kandidat ne može imati više preferencijskih glasova od svoje liste, ni svi kandidati zajedno: "
                 "provjerite zapisnik.",
                 "A candidate can't have more preferential votes than the list, nor all of them together: check "
                 "the record."),
    },
    "near_unanimity": {
        "name": ("Visoka izlaznost i gotovo jednoglasan rezultat", "High turnout and a near-unanimous result"),
        "text": ("Izlaznost {turnout}, {share} za: {name}.", "Turnout {turnout}, {share} for {name}."),
        "hint": ("Može biti zakonito (mala mjesta, jaka lokalna podrška); usporedite sa susjednim biračkim mjestima "
                 "i prethodnim izborima.",
                 "May be legitimate (small places, strong local support); compare with nearby stations and "
                 "earlier elections."),
    },
    "invalid_spike": {
        "name": ("Mnogo nevažećih listića", "Many invalid ballots"),
        "text": ("Nevažećih {invalid} ({share} listića).", "Invalid {invalid} ({share} of the ballots)."),
        "text_rel": ("Nevažećih {invalid} ({share} listića); medijan {basis}: {median}.",
                     "Invalid {invalid} ({share} of the ballots); the median {basis}: {median}."),
        "hint": ("Nevažeći listići mogu biti prosvjed ili zabuna; provjerite zapisnik i primjedbe.",
                 "Invalid ballots may be a protest or a mistake; check the record and the remarks."),
    },
    "high_turnout": {
        "name": ("Izlaznost 90 % ili viša", "Turnout of 90% or more"),
        "text": ("Izlaznost {turnout} od {registered} upisanih.", "Turnout {turnout} of {registered} registered."),
        "hint": ("Visoka izlaznost može biti zakonita; usporedite s općinom i s prethodnim izborima.",
                 "High turnout may be legitimate; compare with the municipality and with earlier elections."),
    },
    "identical_results": {
        "name": ("Isti glasovi kao na drugom biračkom mjestu", "Same votes as another polling station"),
        "text": ("Iste glasove svih lista ili kandidata ima i BM {twins} ({votes} glasova).",
                 "Every list or candidate got the same votes at station {twins} ({votes} votes)."),
        "hint": ("Dva biračka mjesta s istim glasovima rijetko su slučajnost: usporedite oba zapisnika.",
                 "Two stations with the same votes are rarely chance: compare both records."),
    },
}
BASIS = {"address": ("na istoj adresi", "at the same address"), "municipality": ("u općini", "in the municipality")}


def _i(loc: str) -> int:
    return LANGS.index(loc)


def t(key: str, loc: str, **kw) -> str:
    text = S[key][_i(loc)]
    return text.format(**kw) if kw else text


def check_text(code: str, part: str, loc: str) -> str:
    return CHECK_TEXT[code][part][_i(loc)]


def fmt_int(n: int | None, loc: str) -> str:
    if n is None:
        return "—"
    s = f"{n:,}"
    return s if loc == "en" else s.replace(",", ".")


def fmt_num(x: float | None, loc: str, digits: int = 1) -> str:
    if x is None:
        return "—"
    if round(x, digits) == 0:
        x = 0.0  # no "-0.0"
    s = f"{x:,.{digits}f}"
    return s if loc == "en" else s.replace(",", "\0").replace(".", ",").replace("\0", ".")


def fmt_pct(x: float | None, loc: str, digits: int = 1) -> str:
    if x is None:
        return "—"
    return fmt_num(100 * x, loc, digits) + ("%" if loc == "en" else " %")


def fmt_p(p: float, loc: str) -> str:
    if p < 0.001:
        return "< " + fmt_num(0.001, loc, 3)
    return fmt_num(p, loc, 3)


MONTHS = {"en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
                 "November", "December"],
          "hr": ["siječnja", "veljače", "ožujka", "travnja", "svibnja", "lipnja", "srpnja", "kolovoza", "rujna",
                 "listopada", "studenoga", "prosinca"]}


def fmt_date(iso: str, loc: str) -> str:
    y, m, d = (int(x) for x in iso[:10].split("-"))
    if loc == "hr":
        return f"{d}. {MONTHS['hr'][m - 1]} {y}."
    return f"{d} {MONTHS['en'][m - 1]} {y}"


SMALL = {"i", "na", "u", "pri", "kod", "od", "do", "nad", "pod", "za", "sa", "izborna", "jedinica"}
ROMAN = re.compile(r"^[IVX]+\.$")


def nice(name: str) -> str:
    """A place's name as DIP writes it (in capitals), in ordinary case: "SVETI FILIP I JAKOV" → "Sveti Filip i
    Jakov", "BUJE - BUIE" → "Buje - Buie". Counties keep their adjective lower: "Osječko-baranjska županija"."""
    if not name:
        return name
    if name.upper().endswith("ŽUPANIJA"):
        return name[:1].upper() + name[1:].lower()
    words = []
    for i, word in enumerate(name.split(" ")):
        low = word.lower()
        if ROMAN.match(word):
            words.append(word)
        elif i and low in SMALL:
            words.append(low)
        else:  # every part after a hyphen, comma, bracket or full stop: "Zagreb-Centar,Zapad", "U.K. V.Britanije"
            words.append(re.sub(r"(^|[-,(.])(\w)", lambda m: m[1] + m[2].upper(), low))
    return " ".join(words)


ALPHABET = "ABCČĆDĐEFGHIJKLMNOPRSŠTUVZŽ"


def collate(name: str) -> tuple:
    """Croatian alphabetical order (č after c, đ after d, š after s, ž after z)."""
    return tuple(ALPHABET.index(ch) if ch in ALPHABET else 100 + ord(ch) for ch in name.upper())
