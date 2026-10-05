# The coded corpus of the OnSIR ABox

`onsir_corpus.csv` holds the 55 primary studies from which the ABox is built, one row per study, and
`codebook.csv` gives the meaning of every column and every code. `dose_series.json` lists the
irradiated doses of the seven studies whose doses the ABox codes as dose assessments, with the
endpoint and stage each source scored and the sentence of the source that states the doses. The CSV
uses English country names and decimal points; an empty cell means that the study does not report the
value.

## Selection

The corpus is the set of studies included in a systematic review of gamma irradiation of plant
propagules, run by L. F. M. Alves following the PRISMA 2020 statement and the Kitchenham (2004)
guidelines for systematic reviews.

- **Sources searched:** Scopus, Web of Science, PubMed, SciELO, Google Scholar and open repositories
  (Zenodo, ResearchGate).
- **Query,** on title, abstract and keywords, with no language restriction:
  (gamma irradiation OR radiação gama) AND (seed\* OR seedling\* OR semente\* OR plântula\* OR
  propágulo\*) AND (hormesis OR radiosensitivity).
- **Publication window:** 2014 to 2026.
- **Search dates:** a first round in November 2025, when the window closed in 2025, and a second
  round in July 2026 with the same terms and criteria, which found five studies published in 2026 and
  extended the window to the current year.
- **Records:** 389 from the databases before duplicate removal (Scopus 106, SciELO 99, Web of Science
  89, Google Scholar 46, PubMed 31, open repositories 18) and one from reference tracking, 390 in all.
  Duplicates were detected by DOI and title across databases and, for the full texts obtained, by file
  checksum. Removing duplicates and screening titles and abstracts left 78 records, all read in full
  text; 55 were included and 23 excluded.
- **Inclusion,** at least two of: (i) seeds, seedlings or tissues irradiated by a gamma source
  (cobalt-60 or caesium-137); (ii) a measurable physiological, kinetic or genetic endpoint; (iii) a
  dose reported explicitly in a unit convertible to gray; (iv) extractable data.
- **Exclusion:** (i) post-harvest irradiation for food preservation, shelf life or insect control;
  (ii) nutritional or nutraceutical quality of seeds treated as food and not germinated; (iii) no
  reproducible method or no defined dose. The 23 full texts excluded were narrative reviews without a
  dose (10), food or nutraceutical studies (6), post-harvest or packaging studies (3), sources without
  extractable primary data, an abstract book and a poster (2), a study of pollen irradiation (1) and a
  study outside the window (1).
- **Screening and coding:** titles, abstracts and full texts were screened by L. F. M. Alves, and the
  coding of each included study was checked in a second reading by G. T. Giraldi, with disagreements
  resolved by re-reading the passage of the study that supports each code.

## Coding

Each study is coded on four axes, defined in `codebook.csv`: FF, the phenological phase of the
propagule primarily irradiated; DR, the shape of the reported dose-response curve; MM, the statistical
model used; and EP, the endpoint category. A fifth axis, TE (study type), is kept for audit. The
review coded it and retired it because the endpoint category recovers it in 49 of the 55 studies.
Species, country, year, radiation source, highest dose, dose rate, the number of dose treatments and
whether the study publishes a confidence interval for its threshold dose are recorded as reported.

Two codes differ from the review, each recorded in the `recode_note` column with the sentence of the
source that decides it. Kainthura and Srivastava (2015) irradiated tuberose bulbs and Haque et al.
(2025) potato tubers, so both are coded FF4 (vegetative tissue).

Every species carries an NCBITaxon identifier resolved on the EBI Ontology Lookup Service on
4 October 2026: by exact label for 47 species, and for three by an exact NCBITaxon synonym of the
name the source uses (*Polianthes tuberosa*, a synonym of *Agave amica*; *Phyllanthus odontadenius*,
of *Moeroris odontadenia*; *Ficus variegata*, of *Ficus variegata* (in: eudicots)).
`../check_taxa.py` repeats the lookup. Every DOI resolves on Crossref to the study's title; the
`source_note` column records where the Crossref record differs from the printed byline, year or
status. One source, Valombola et al. (2025), is a preprint.

Doses stated in roentgens (three studies) are converted at 8.77 mGy per roentgen, the air kerma that
one roentgen of exposure corresponds to. At the 1.25 MeV of cobalt-60 the mass energy-absorption
coefficient of water is 1.11 times that of air (Hubbell and Seltzer 1996), so the converted doses are
lower estimates of the dose to water.
