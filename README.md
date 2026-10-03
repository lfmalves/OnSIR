# OnSIR: Ontology for Seed Irradiation and Plant Radiobiology

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

**Canonical IRI:** `https://w3id.org/onsir` · **Version:** 1.6.0 · **License:** CC BY 4.0

OnSIR is an OWL 2 DL ontology of seed-irradiation treatments and their dose-dependent effects across
crop and model plants. It models radiation types and isotopic sources, dose and dose-rate
categories, lifecycle stages, endpoints, and the `TreatmentOutcome` that links a treatment to its
subject, context and response.

## What is in this release (v1.6.0)

- **90 named classes, 26 object properties, 11 datatype properties.** The three outcome-named dose
  categories (`HormeticDose`, `MutagenicDose`, `SterilizationDose`) stay active, with definitions
  that discourage them for new annotation, because their axioms take part in inference.
- **Taxon-specific dose windows** written as OWL 2 datatype facets, so that a reasoner derives where
  a numeric dose lies relative to the statistics reported for its taxon. Each taxon carries windows
  for the statistics its source reports, at the strength the source states: *Nicotiana tabacum* the
  favourable band of approximately 5 to 15 Gy (Alves et al. 2027), *Vigna unguiculata* a survival
  LD50 of 132 Gy, the median of three regression estimates (Gnankambary et al. 2019) and *Trigonella foenum-graecum* a lower bound of 350 Gy on
  its LD50 (Patel et al. 2017). The generic positions are `BelowReportedFavourableBand`,
  `WithinReportedFavourableBand`, `AboveReportedFavourableBand`, `BelowReportedLD50` and
  `AtOrAboveReportedLD50`. At 200 Gy the reasoner places tobacco above its favourable band, cowpea at
  or above its LD50 and fenugreek below its LD50 (`reason_context.py`). A window extends past the
  doses its source tested wherever the statistic leaves it open; each window records the tested
  range in a scope note.
- **ABox: 29 studies, 195 declared individuals**, shipped as Turtle and RDF/XML with an OASIS
  catalogue: the 28 studies of the coded corpus, each with the highest dose it irradiated, and the
  cowpea study of Lumorh et al. (2025), whose twelve doses are coded as dose assessments that the
  reasoner places relative to the cowpea window. Every outcome carries its source as `dct:source`, and the
  ABox header carries its licence, version and description.
- **Examples:** `OnSIR_examples.ttl` / `.owl` hold the illustrative individuals of the class
  scaffold (three outcomes with their treatments, typed dose categories and endpoints, and a
  Brain-Cousens model). Their values are invented for illustration; the core ships none of them. One
  outcome has a dose category and no response, and HermiT classifies it as a `MutagenicOutcome`.
- Alignments with IRIs checked on the EBI Ontology Lookup Service to BFO, the Plant Ontology,
  NCBITaxon, ChEBI, PATO, ENVO, the Plant Experimental Conditions Ontology and the Plant Trait
  Ontology, and typed units in QUDT. `rbo_gap.py` and `rbo_recheck.py` compare the release term by
  term with the OBO Radiation Biology Ontology.
- `verify_release.py` checks the release in one command: every numeric row of the metrics table,
  byte-identical regeneration of the generated files, HermiT consistency of the merged graph with no
  unsatisfiable class, the OWL 2 DL profile of every file (ROBOT), no undeclared IRI in a logical
  position, property characteristics, the owlready2 load recipe and the version recorded across the
  files.

### Changes from 1.5.0

The dose windows encode the statistics the cited sources report, at their stated strength:
- *Nicotiana tabacum*: the band of approximately 5 to 15 Gy in which Alves et al. (2027) report the
  most favourable responses, with both ends approximate, giving three windows.
- *Vigna unguiculata*: the median of the three genotype survival LD50s of Gnankambary et al. (2019),
  132 Gy. The cowpea optimum of 1.5.0 is removed; the study irradiated no dose below 150 Gy.
- *Trigonella foenum-graecum*: 350 Gy, the dose at which Patel et al. (2017) place the LD50 and their
  highest dose, encoded as a lower bound, so only the window below it is defined.
- The *Capsicum annuum* window is removed.

The generic positions are renamed after the favourable band, and `BelowReportedLD50` is added.
Biochemical changes are measured endpoints: `BiochemicalChange` sits under `Endpoint`, and
`hasBiochemicalChange` is a property of its own, so a shift in reactive oxygen species classifies as
a measured change in either direction. `PlantCallus` (PO plant callus) types the one callus subject,
the dose-rate categories carry definitions, and every class and property label follows one convention
(lower case, British spelling, acronyms and binomials as written). The
link from a position to a response type (`consistentWithResponse`) is kept for the favourable band
only. The ABox codes each study's highest dose as the maximum of a dose range, types the rice callus
of one study as a plant structure, records each source, and adds Lumorh et al. (2025). Dublin Core
and SKOS annotation properties are declared, the class stubs leave XML Schema datatypes out, and
every file is in the OWL 2 DL profile. `owl:priorVersion` points to 1.5.0. The language-model benchmark
files are no longer part of the release.

## Files

| File | Description |
|---|---|
| `OnSIR.owl` / `OnSIR.ttl` | the ontology (RDF/XML and Turtle) |
| `OnSIR_abox.owl` / `OnSIR_abox.ttl` | ABox of 29 studies (imports the core) |
| `OnSIR_examples.owl` / `OnSIR_examples.ttl` | illustrative individuals with invented values (imports the core) |
| `corpus/eiccam_table_body.tex` | the coded corpus the ABox is built from |
| `corpus/added_studies.json` | the study coded in addition to the corpus, with its doses |
| `docs/index.html` | human-readable documentation (generated by `make_docs.py`) |
| `build_ontology.py` | reproducible construction of the ontology and the examples |
| `reason.py` | HermiT consistency and dose-to-effect classification |
| `reason_context.py` | numeric dose positioning by taxon and conflict detection |
| `abox_cq.py` | ABox construction and SPARQL competency questions |
| `make_metrics.py`, `make_docs.py` | metrics table and documentation from the ontology |
| `rbo_gap.py`, `rbo_recheck.py` | term-level comparison with the OBO Radiation Biology Ontology |
| `registry_search.py` | search of the OBO Foundry registry and the EBI Ontology Lookup Service |

## Reuse

```turtle
@prefix onsir: <https://w3id.org/onsir/> .
```

Load `OnSIR.ttl` in Protégé or any OWL API, rdflib or owlready2 pipeline. HermiT needs Java;
`verify_release.py` also needs ROBOT (set `ROBOT_JAR` to a `robot.jar` from
https://github.com/ontodev/robot/releases).

### Loading the ABox

`OnSIR_abox.owl` imports `https://w3id.org/onsir`. Over the network that IRI resolves to the file on
the main branch; the shipped OASIS catalogue `catalog-v001.xml` maps it to the `OnSIR.owl` of this
directory for Protégé and the OWL API. owlready2 implements no catalogue, so to load exactly this
release, register the core under its canonical IRI in the same `World` first:

```python
import os
import owlready2 as o2
w = o2.World()
core = w.get_ontology("https://w3id.org/onsir")
core.load(only_local=False, fileobj=open("OnSIR.owl", "rb"))
abox = w.get_ontology("file://" + os.path.abspath("OnSIR_abox.owl")).load()
# 128 classes, 198 individuals
```

`verify_release.py` runs exactly this. For rdflib, parse the two files and merge them.

## Persistent identifier

Term IRIs use the namespace `https://w3id.org/onsir/`, registered with w3id.org. For an RDF client
the unversioned IRI redirects to the Turtle or RDF/XML file on the main branch, and
`https://w3id.org/onsir/<x.y.z>` to the file of the matching release tag.

## How to cite

See `CITATION.cff`.
