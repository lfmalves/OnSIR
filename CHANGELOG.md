# Changes

## 1.7.0

**Dose windows conditioned on endpoint and stage.** A dose window now holds for the endpoint and the
stage its source scored, as well as for the taxon: a `DoseAssessment` names the plant structure the dose
is applied to (`hasSubject`), whose taxon is stated with RO:0002162 *in taxon* some NCBITaxon class, its
endpoint (`forEndpoint`) and its stage (`atStage`), both functional properties. Because the taxon is an existential over the
NCBITaxon class, an assessment of a subspecies or cultivar falls in the windows of its species. New
classes `SeedlingSurvival`, `GerminationPercentage` and `HypocotylEmergence` (endpoints) and
`FloweringStage` (stage) carry the endpoints and stages of the sources.

**Windows.** Fifteen windows for eight taxa, each with the passage of its source that its bound rests on
(`sourceStatement`):
- *Nicotiana tabacum* (Alves et al. 2027): the favourable band of approximately 5 to 15 Gy, for
  germination, hypocotyl emergence, cotyledon liberation and seedling fresh weight at the germination
  and early seedling stages.
- *Vigna unguiculata* (Gnankambary et al. 2019): seedling survival at flowering. The median regression
  estimate of 132 Gy lies below the lowest dose tested, at which every genotype kept more than half its
  plants, so the windows encode the bracket that the observations support: up to and including 150 Gy,
  and from 250 Gy.
- *Trigonella foenum-graecum* (Patel et al. 2017): seedling survival, up to and including the lower bound
  of 350 Gy.
- New: *Magnolia champaca* (Zanzibar and Sudrajat 2016, germination), *Lablab purpureus* (Mahesha et
  al. 2023, germination, between the 30 kR the source adopts as its LD50, 263.1 Gy, and the higher of its
  probit estimates, 304.1 Gy), *Plukenetia volubilis* (Corazon-Guivin et al. 2023, seedling survival),
  *Solanum lycopersicum* (Indrayanti et al. 2024, seedling survival, up to and including the lower bound
  of 120 Gy) and *Triticum aestivum* (Chakraborty et al. 2023, seedling survival).

Each statistic gives its own windows. The window below an LD50 ends below the lowest estimate, or
includes a dose at which the source observed more than half of its plants alive (cowpea 150 Gy,
fenugreek 350 Gy, tomato 120 Gy), and the window at or above it starts at the highest estimate, so doses
between them fall in no window. Each favourable band carries one probe class for each endpoint and stage
it covers, ten for the tobacco band; a probe is unsatisfiable when the band reaches an LD50 of its taxon,
endpoint and stage. `reason_context.py` runs the literal datatypes, the probes and a check of the ABox
doses under HermiT 1.4.5 through ROBOT as well as through owlready2.

**Responses.** `InhibitoryResponse` and `LossOfViability` join the response kinds; `Response` carries
no covering axiom, a treatment need not induce a response and an outcome need not have one, and
`NoDetectedResponseOutcome` records an outcome asserted to have none. `StressResistance` and its two
subclasses are measured traits and sit under `Endpoint`.

**Treatments and subjects.** A treatment states one dose, a dose range or, for ultraviolet light, a
fluence; the exactly-one-dose restriction is replaced by this disjunction, since `hasDose` is
functional. `PlantBulb` (PO:0025356) and `PlantTuber` (PO:0004543) join `PlantSeed` and `PlantCallus`
under `PlantPart`, which names organs, tissues and propagules; `Plant` and `Seedling` stay outside it. `hasBiochemicalChange` relates an outcome to the change measured in it, and the
inverse properties carry a domain and a range.

**Alignments.** `SeedIrradiationTreatment` is a subclass of OBI:0302889 (planned irradiation),
`DoseAssessment` of IAO:0000030 (information content entity), `Plant` of PO:0000003 (whole plant) and
`LifecycleStage` of PO:0009012 (plant structure development stage). Endpoints are matched to TO and GO
traits (chlorophyll content, antioxidant activity, shoot axis length, plant male sterility, percent
germination and others) where 1.6.0 pointed at chemical entities, and context classes to the PECO
exposures that vary the same condition. `Neutron` and `Proton` are related to the ChEBI particles.

**Definitions and metadata.** Every class and property carries one definition as IAO:0000115, with its
source as IAO:0000119 where the meaning comes from a source; the definition of `HormeticResponse` is
descriptive. The header carries `vann:preferredNamespacePrefix`, `vann:preferredNamespaceUri`,
`dct:bibliographicCitation`, `dct:issued` and `dct:publisher`. The ABox and the examples carry
versionIRIs of their own and import the versioned core.

**Punning removed.** Isotopes, radiation types, dose-rate categories and endpoint categories enter the
ABox as class assertions (a treatment has some `Co60` source), so no class IRI stands as an individual,
and every individual is declared `owl:NamedIndividual`.

**Corpus.** The ABox is built from the 55 studies of the authors' systematic review
(`corpus/onsir_corpus.csv`, with a codebook and the selection rule in `corpus/README.md`), replacing the
28-study table and the one added study of 1.6.0. The tuberose bulbs and the potato tubers are coded as
vegetative tissue (FF4), the near-miss species resolve to NCBITaxon through its synonyms, and ABox
individual IRIs are keyed by study.

**Obsolete terms** (owl:deprecated, labelled "obsolete", with their replacement):
- `LowDoseRate` and `HighDoseRate`, replaced by `DoseRateBelow100GyPerHour` and
  `DoseRateAbove100GyPerHour`, named after their bound;
- the six 1.6.0 windows (`Nicotiana_tabacum_BelowFavourableBandDose` and the others), replaced by the
  windows of the same position conditioned on endpoint and stage;
- `forTaxon` (consider `hasSubject` with RO:0002162) and `hasTaxon` (replaced by RO:0002162), and the
  three taxon individuals of 1.6.0, which were typed with NCBITaxon classes.

## 1.6.0

The dose windows encode the statistics the cited sources report, at their stated strength: the
*Nicotiana tabacum* favourable band of approximately 5 to 15 Gy (Alves et al. 2027), the median of the
three genotype survival LD50s of Gnankambary et al. (2019) for *Vigna unguiculata*, and 350 Gy as a lower
bound on the LD50 of *Trigonella foenum-graecum* (Patel et al. 2017). The *Capsicum annuum* window and
the cowpea optimum of 1.5.0 are removed. The generic positions are renamed after the favourable band, and
`BelowReportedLD50` is added. `BiochemicalChange` sits under `Endpoint`; `PlantCallus` types the callus
subject; every label follows one convention. The ABox codes each study's highest dose as the maximum of a
dose range, records each source and adds Lumorh et al. (2025). Every file is in the OWL 2 DL profile, and
the illustrative individuals move to `OnSIR_examples`.

## 1.5.0

The unsourced *Nicotiana tabacum* LD50 is removed.
