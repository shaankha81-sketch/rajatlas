# Data sources

| Source | Used for | Licence | Vintage | Status |
|---|---|---|---|---|
| DataMeet, [Districts/Census_2011](https://github.com/datameet/maps/tree/master/Districts/Census_2011) | district boundaries, areas, borders, neighbours | CC BY 2.5 India | Census 2011 layout (33 districts) | in use, checksum recorded in the manifest |
| Wikipedia, [List of districts of Rajasthan](https://en.wikipedia.org/wiki/List_of_districts_of_Rajasthan) | today's district list, divisions, official district websites | CC BY-SA 4.0 | revision 1381020334 (2026-10-19); states 41 districts as of 30 Dec 2024 | in use, list and divisions only |
| Census of India, Primary Census Abstract 2011 | population and demographics | to check | 2011 (last completed census; 2027 enumeration is scheduled for February 2027, no results yet) | planned, phase 2 |
| IMD gridded rainfall and temperature | climate | to check on the raw files | 1901 onward | planned, phase 5 |
| OpenStreetMap | roads, places | ODbL, needs "© OpenStreetMap contributors" | current | planned, phase 4 |
| datameet/railways | rail stations and trains | CC0 | old, to validate | planned, phase 4 |

## What the Wikipedia page is trusted for

The list, the divisions and the district websites. The page states them twice (a main table and a divisions table) and the ingest requires the two to agree.

The page's **area and population columns are not used**. The ingest finds, automatically:

* Ajmer and Beawar have the identical area, 8,481 km².
* Nagaur and Pali have the identical population, 1,605,543.
* The infobox says Dholpur is the smallest district (3,084 km²), but the table lists smaller ones.
* The infobox says Jaisalmer has the lowest population, but the table lists a lower one.
* The infobox gives Jaipur 6,626,178 and the table 6,046,835.
* No source or year is named for either column.

The validator also compares the claimed areas with the areas measured from the boundaries: they differ by more than 2% for 11 of 33 districts (Sawai Madhopur by +109%). These figures reflect mixed vintages and some transcription errors, so they stay out of the site.

## Source-data quality notes

* DataMeet polygons overlap slightly in a few places (largest: Alwar and Dausa, about 5.5 km² out of 342,469). There are no gaps. Reported in the manifest and on the site.
* The measured total, 342,469 km², is within 0.07% of Rajasthan's 342,239 km² in the Census; that Census figure was recalled by the author and should be checked against the Primary Census Abstract.
* The computed Pakistan border, 1,036 km, is about 3% under the commonly quoted figure of roughly 1,070 km; it is a sanity check only.

## Boundary depiction

India's boundary depiction is regulated, and a 2016 draft Geospatial Information Regulation Bill proposed licensing for map publishing. I could not confirm what law applies today. The site draws only Rajasthan and the five neighbouring states and does not draw India's external boundary beyond the Rajasthan outline. Before wider publication, check the current rules.
