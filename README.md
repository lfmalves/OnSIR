# OnSIR: Ontology for Seed Irradiation and Plant Radiobiology

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

**Canonical IRI:** `https://w3id.org/onsir` · **Version:** 1.7.0 · **License:** CC BY 4.0

OnSIR is an OWL 2 DL ontology of seed-irradiation treatments and their dose-dependent effects across
crop and model plants. It models radiation types and isotopic sources, doses, dose ranges and
dose-rate categories, life-cycle stages, endpoints, responses, and the `TreatmentOutcome` that links a
treatment to its subject, context and response.

## What is in this release (v1.7.0)

- **118 named classes, 24 object properties, 11 datatype properties**, each with a definition
  (IAO:0000115), and 10 obsolete classes and properties of release 1.6.0 kept with their replacements
  (see `CHANGELOG.md`). The three outcome-named dose categories (`HormeticDose`, `MutagenicDose`,
  `SterilizationDose`) stay active, with definitions that discourage them for new annotation, because
  their axioms take part in inference.
- **Taxon dose windows conditioned on endpoint and stage.** A `DoseAssessment` records one absorbed
  dose (`doseGy`) applied to a plant structure (`hasSubject`), whose taxon is stated with RO:0002162
  *in taxon* some NCBITaxon class, for one endpoint (`forEndpoint`) and one stage (`atStage`), both
  functional properties. Each window class is defined over the taxon, the endpoint and the stage its
  source scored and an OWL 2 datatype facet on the dose, so a reasoner places an assessment from these values alone, and an
  assessment of a subspecies or cultivar whose NCBITaxon class sits below the species falls in the
  species' windows. Fifteen windows for eight taxa take each bound from their source as a reported
  estimate or bracket, a bracket set by the source's observations, or a lower bound at the highest dose
  tested, and carry the source, the passage of the source the bound rests on (`sourceStatement`), how
  the source supports the bound (`boundQualifier`) and the doses tested:
  - *Nicotiana tabacum*: a favourable band of approximately 5 to 15 Gy for germination and early
    seedling growth (Alves et al. 2027);
  - *Vigna unguiculata*: seedling survival at flowering, with the LD50 bracketed between 150 and
    250 Gy by the observations of Gnankambary et al. (2019), the window below it including 150 Gy;
  - *Trigonella foenum-graecum*: seedling survival, with 350 Gy, which the window below the LD50
    includes, a lower bound on the LD50 (Patel et al. 2017);
  - *Magnolia champaca*: germination, LD50 between 30 and 40 Gy (Zanzibar and Sudrajat 2016);
  - *Lablab purpureus*: germination, LD50 between 263.1 Gy (30 kR, the LD50 the source adopts) and
    304.1 Gy (the higher of its probit estimates) (Mahesha et al. 2023);
  - *Plukenetia volubilis*: seedling survival, LD50 618.78 Gy (Corazon-Guivin et al. 2023);
  - *Solanum lycopersicum*: seedling survival, with 120 Gy, which the window below the LD50 includes,
    a lower bound on the LD50 (Indrayanti et al. 2024);
  - *Triticum aestivum*: seedling survival, probit LD50s of 272.71 and 278.61 Gy (Chakraborty et al.
    2023).

  The generic positions are `BelowReportedFavourableBand`, `WithinReportedFavourableBand`,
  `AboveReportedFavourableBand`, `BelowReportedLD50` and `AtOrAboveReportedLD50`. Each favourable band
  carries one probe class for each endpoint and stage it covers, ten for the tobacco band; a probe
  becomes unsatisfiable when the band reaches an LD50 reported for its taxon, endpoint and stage, so
  classification flags such a record with no dose recorded. All ten are satisfiable, since no tobacco
  LD50 is encoded. `reason_context.py` runs the reasoning cases: one dose across the taxa, the
  boundaries, a constructed conflict, the doses the ABox records, the literal datatypes, a subtaxon,
  one dose under three endpoint and stage pairs, and the ten probes, each made unsatisfiable by an LD50
  of its own endpoint and stage and by no other.
- **ABox: 55 studies, 372 declared individuals**, shipped as Turtle and RDF/XML with an OASIS
  catalogue, built from the coded corpus in `corpus/` (selection rule and codebook in
  `corpus/README.md`). Each study is a treatment, with its radiation type, source isotope and
  dose-rate category as class assertions, its highest dose as the maximum of a dose range and its
  reported dose rate, and an outcome, with its subject (a seed, bulb, tuber, callus or other plant
  part, in its NCBITaxon taxon), its endpoint category and its source. The irradiated doses of seven
  studies are dose assessments for the endpoint and stage each source scored: 53 assessments, which
  the reasoner places relative to the windows.
- **Examples:** `OnSIR_examples.ttl` / `.owl` hold illustrative individuals (outcomes with their
  treatments, typed dose categories and endpoints, a response with no detectable effect and a
  Brain-Cousens model). Their values are invented for illustration; the core ships none of them.
  HermiT classifies one outcome as a `MutagenicOutcome` from its dose category and another as a
  `NoDetectedResponseOutcome`.
- Alignments with IRIs and labels checked on the EBI Ontology Lookup Service to BFO, IAO, OBI, RO,
  the Plant Ontology, NCBITaxon, ChEBI, GO, PATO, the Plant Experimental Conditions Ontology and the
  Plant Trait Ontology, and typed units in QUDT. `rbo_gap.py` and `rbo_recheck.py` compare the release
  term by term with the OBO Radiation Biology Ontology.
- `verify_release.py` checks the release in one command: every numeric row of the metrics table,
  byte-identical regeneration of the generated files, HermiT consistency of the merged graph with no
  unsatisfiable class, the OWL 2 DL profile of every file (ROBOT), no undeclared IRI in a logical
  position, a definition on every term, the obsolete terms, property characteristics, the header
  metadata and the versioned imports, the owlready2 load recipe and the version recorded across the
  files.

## Files

| File | Description |
|---|---|
| `OnSIR.owl` / `OnSIR.ttl` | the ontology (RDF/XML and Turtle) |
| `OnSIR_abox.owl` / `OnSIR_abox.ttl` | ABox of 55 studies (imports the versioned core) |
| `OnSIR_examples.owl` / `OnSIR_examples.ttl` | illustrative individuals with invented values (imports the versioned core) |
| `corpus/onsir_corpus.csv` | the coded corpus the ABox is built from |
| `corpus/codebook.csv` | the meaning of every column and code of the corpus |
| `corpus/dose_series.json` | the irradiated doses coded as dose assessments, with endpoint and stage |
| `corpus/README.md` | the selection rule and the coding of the corpus |
| `docs/index.html` | human-readable documentation (generated by `make_docs.py`) |
| `CHANGELOG.md` | changes by release |
| `build_ontology.py` | reproducible construction of the ontology and the examples |
| `reason.py` | HermiT consistency and dose-to-effect classification |
| `reason_context.py` | numeric dose positioning by taxon, endpoint and stage, and conflict detection |
| `abox_cq.py` | ABox construction and SPARQL competency questions |
| `check_taxa.py` | the NCBITaxon identifiers of the corpus, checked on the EBI Ontology Lookup Service |
| `make_metrics.py`, `make_docs.py` | metrics table and documentation from the ontology |
| `rbo_gap.py`, `rbo_recheck.py` | term-level comparison with the OBO Radiation Biology Ontology |
| `registry_search.py` | search of the OBO Foundry registry and the EBI Ontology Lookup Service |

## Reuse

```turtle
@prefix onsir: <https://w3id.org/onsir/> .
```

Load `OnSIR.ttl` in Protégé or any OWL API, rdflib or owlready2 pipeline. HermiT needs Java;
`verify_release.py` and `reason_context.py` also need ROBOT (set `ROBOT_JAR` to a `robot.jar` from
https://github.com/ontodev/robot/releases).

Write a dose (`doseGy`) as `xsd:decimal`, `xsd:double` or `xsd:integer`. The range of `doseGy` is the
union of `xsd:decimal` and `xsd:double`, whose value spaces OWL 2 keeps disjoint, so a dose typed
`xsd:float` violates it: HermiT 1.4.5 through ROBOT and the OWL API reports the ontology
inconsistent, while HermiT 1.3.8 as shipped with owlready2 accepts the dose and places it in no
window.

### Loading the ABox

`OnSIR_abox.owl` imports the versioned IRI `https://w3id.org/onsir/1.7.0`. The shipped OASIS
catalogue `catalog-v001.xml` maps it to the `OnSIR.owl` of this directory for Protégé and the OWL API.
owlready2 implements no catalogue, so to load exactly this release, register the core under the
versioned IRI in the same `World` first:

```python
import os
import owlready2 as o2
w = o2.World()
core = w.get_ontology("https://w3id.org/onsir/1.7.0")
core.load(only_local=False, fileobj=open("OnSIR.owl", "rb"))
abox = w.get_ontology("file://" + os.path.abspath("OnSIR_abox.owl")).load()
# 200 classes, 375 individuals
```

`verify_release.py` runs exactly this. For rdflib, parse the two files and merge them.

## Persistent identifier

Term IRIs use the namespace `https://w3id.org/onsir/`, registered with w3id.org. For an RDF client
the unversioned IRI redirects to the Turtle or RDF/XML file on the main branch, and
`https://w3id.org/onsir/<x.y.z>` to the file of the matching release tag.

## How to cite

See `CITATION.cff`.
