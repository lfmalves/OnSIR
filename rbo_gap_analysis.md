# Term-level gap analysis: OBO Radiation Biology Ontology (RBO) vs. OnSIR

Generated 2026-10-02 by `rbo_gap.py` (rdflib 7.6.0, Python 3.12.3). All figures are produced by that script from the two source files and can be regenerated with the commands in section 11.


## 1. Methods

RBO was retrieved on 2026-10-02 from the OBO Foundry PURL `http://purl.obolibrary.org/obo/rbo/releases/2026-07-16/rbo.owl`, which redirects to `https://raw.githubusercontent.com/Radiobiology-Informatics-Consortium/RBO/v2026-07-23/rbo.owl` (29260285 bytes, SHA-256 `ab2ff2f575e8857cabb3f5cd5ebefbd6fd02b4568949a4dae2cde356a4eb0c37`). The release analysed carries `owl:versionInfo` **2026-07-16** and `owl:versionIRI` `http://purl.obolibrary.org/obo/rbo/releases/2026-07-16/rbo.owl`, and is distributed under `http://creativecommons.org/licenses/by/3.0/`. RBO was parsed as RDF/XML and OnSIR (`OnSIR.ttl`, namespace `https://w3id.org/onsir/`) as Turtle, both with rdflib; no reasoner was invoked, so every count below is asserted rather than inferred.

For each named `owl:Class` in both ontologies a set of surface forms was harvested: `rdfs:label`, the oboInOwl exact/broad/narrow/related synonym properties, `IAO_0000118` (alternative term), `IAO_0000111` (editor preferred term), and `skos:prefLabel`/`skos:altLabel`. For OnSIR the IRI local name was added as well, since OnSIR local names are informative (`GerminationRate`, `HormeticDose`) and two OnSIR classes carry no label at all. Each surface form was normalised by splitting camelCase and letter-digit boundaries, lowercasing, replacing every non-alphanumeric character, dashes and `_` included, with a single space, and collapsing whitespace; so `onsir:Co60` yields `co 60` and `Dose–Response Model` yields `dose response model`. An EXACT match is equality of two normalised forms. A NEAR match is `difflib.SequenceMatcher(None, a, b).ratio() >= 0.85` for a pair that is not already exact; the token Jaccard index of the same pair is reported beside the ratio, because a high character ratio with Jaccard 0 (*plant*/*planet*, *neutron*/*neuron*) is an orthographic coincidence.

Two properties of the RBO release govern how the results must be read. First, the distributed `rbo.owl` is a fully merged artifact with no `owl:imports`: it inlines 8775 classes from GO, UBERON, ChEBI, ENVO, UO, CL, NCBITaxon, PATO, OBI, PO and other ontologies alongside RBO's own 446 `obo:RBO_*` classes. A term found in the file is therefore not necessarily an RBO term, so every comparison is reported twice: against **RBO-native** classes and against **all** classes in the file. Second, 41 of the 446 RBO-native classes are flagged `owl:deprecated true` (they form retired/replacement pairs such as `RBO_010014`/`RBO_00010014` 'organ dose'), leaving 405 active RBO-native classes; deprecated hits are flagged where they occur.

The concept probes in section 7 distinguish three situations that a naive keyword search would conflate: (i) a class whose label or synonym *denotes* the concept; (ii) the concept absent from all labels but a related or broader label present; and (iii) the phrase occurring only inside free-text annotation (`IAO_0000115` textual definition, `rdfs:comment`, `skos:definition`, editor notes; 10567 strings scanned), which is prose and not ontological coverage. Regular expressions use word boundaries; the `seed` indicator uses a word-start boundary so that *seedling* and *seed coat* count while *proceed* does not.

## 2. RBO release and parse statistics

| Quantity | Value |
|---|---|
| Ontology IRI | `http://purl.obolibrary.org/obo/rbo.owl` |
| `owl:versionIRI` | `http://purl.obolibrary.org/obo/rbo/releases/2026-07-16/rbo.owl` |
| `owl:versionInfo` | **2026-07-16** |
| `dcterms:license` | `http://creativecommons.org/licenses/by/3.0/` (CC BY 3.0) |
| `dc:title` | Radiation Biology Ontology |
| `dc:description` | RBO is an ontology for the effects of radiation on biota in terrestrial and space environments. |
| `owl:imports` in file | none -- fully merged release |
| File size | 29260285 bytes (27.9 MiB) |
| SHA-256 | `ab2ff2f575e8857cabb3f5cd5ebefbd6fd02b4568949a4dae2cde356a4eb0c37` |
| Total RDF triples | **354548** |
| Named `owl:Class` declarations | **9221** |
| Named classes with `rdfs:label` | 9219 |
| Named classes `owl:deprecated true` | 47 |
| Anonymous class expressions (blank nodes typed `owl:Class`) | 6096 |
| **RBO-native classes** (`obo:RBO_*`) | **446** (405 active, 41 deprecated) |
| Named individuals (`owl:NamedIndividual`) | **1085** |
| of which RBO-native IRIs | 134 |
| Named individuals also typed `owl:Class` (punning; the inlined UO unit terms) | 276 |
| Individuals not also typed as classes | **809** |
| `owl:ObjectProperty` | 313 |
| `owl:DatatypeProperty` | 6 |
| `owl:AnnotationProperty` | 256 |
| Reified `owl:Axiom` annotation nodes | 25456 |
| Distinct normalised label/synonym strings, all classes | 27989 |
| Surface forms harvested, all classes / RBO-native | 28693 / 545 |
| RBO-native labels shared by more than one class | 22 |

### 2.1 Provenance of the classes in the merged file

| Source prefix | Named classes | Share |
|---|---|---|
| GO | 3357 | 36.4% |
| UBERON | 2033 | 22.0% |
| CHEBI | 724 | 7.9% |
| ENVO | 631 | 6.8% |
| UO | 530 | 5.7% |
| CL | 469 | 5.1% |
| RBO | 446 | 4.8% |
| NCBITaxon | 356 | 3.9% |
| PATO | 168 | 1.8% |
| OBI | 102 | 1.1% |
| DOID | 81 | 0.9% |
| PR | 74 | 0.8% |
| https://www.commoncoreontologies.org | 48 | 0.5% |
| PO | 34 | 0.4% |
| IAO | 32 | 0.3% |
| http://www.ebi.ac.uk/efo | 29 | 0.3% |
| BFO | 24 | 0.3% |
| SLSO | 17 | 0.2% |
| COB | 11 | 0.1% |
| OBIB | 9 | 0.1% |
| CARO | 8 | 0.1% |
| PCO | 7 | 0.1% |
| NBO | 7 | 0.1% |
| OBCS | 5 | 0.1% |
| CHMO | 4 | 0.0% |
| HANCESTRO | 3 | 0.0% |
| SO | 3 | 0.0% |
| APOLLO | 2 | 0.0% |
| OMRSE | 2 | 0.0% |
| GENO | 1 | 0.0% |
| http://www.w3.org/2002/07 | 1 | 0.0% |
| http://www.geneontology.org/formats | 1 | 0.0% |
| RO | 1 | 0.0% |
| OGMS | 1 | 0.0% |
| **total** | **9221** | 100% |

RBO's own terms are 4.8% of the classes in the file it distributes; the Plant Ontology fragment is 34 classes (0.37%). Two of the 9221 entries are technical rather than domain terms -- `owl:Thing` (redundantly typed `owl:Class`, the only unlabelled entry besides `NCBITaxon_Union_0000030`) and `oboInOwl:ObsoleteClass` -- so the domain-class total is 9219.

## 3. OnSIR terms compared

OnSIR (`OnSIR.ttl`, 1006 triples) declares **90** named `owl:Class` entities in the `https://w3id.org/onsir/` namespace, plus 27 object properties and 12 datatype properties. These 90 classes are the comparison set.

Two counting notes, so the figures can be reconciled with other descriptions of OnSIR. (i) The file contains 103 named `owl:Class` declarations in total; the extra one is `qudt:QuantityValue`, re-declared locally but not an OnSIR term. (ii) A count of `owl:Class`-typed nodes that does not filter blank nodes returns 117, because 14 anonymous class expressions (the intersections and restrictions used in the equivalence axioms) are also typed `owl:Class`; that 117 counts syntactic nodes. The figure for OnSIR's own named classes is **90**.

| # | OnSIR class | `rdfs:label` |
|---|---|---|
| 1 | `onsir:AbioticStressResistance` | abiotic stress resistance |
| 2 | `onsir:AboveReportedFavourableBand` | above reported favourable band |
| 3 | `onsir:Am241` | americium-241 |
| 4 | `onsir:AntioxidantActivity` | antioxidant activity |
| 5 | `onsir:AntioxidantIncrease` | antioxidant increase |
| 6 | `onsir:AtOrAboveReportedLD50` | at or above reported LD50 |
| 7 | `onsir:BelowReportedFavourableBand` | below reported favourable band |
| 8 | `onsir:BelowReportedLD50` | below reported LD50 |
| 9 | `onsir:BiochemicalChange` | biochemical change |
| 10 | `onsir:BiochemicalEndpointCategory` | biochemical endpoint category |
| 11 | `onsir:BioticStressResistance` | biotic stress resistance |
| 12 | `onsir:BrainCousensModel` | Brain–Cousens model |
| 13 | `onsir:ChlorophyllContent` | chlorophyll content |
| 14 | `onsir:Co60` | cobalt-60 |
| 15 | `onsir:Context` | context |
| 16 | `onsir:CotyledonFreeing` | cotyledon freeing |
| 17 | `onsir:Cs137` | caesium-137 |
| 18 | `onsir:DoseAssessment` | dose assessment |
| 19 | `onsir:DoseCategory` | dose category |
| 20 | `onsir:DoseRange` | dose range |
| 21 | `onsir:DoseRateCategory` | dose-rate category |
| 22 | `onsir:DoseResponseModel` | dose–response model |
| 23 | `onsir:DryMass` | dry mass |
| 24 | `onsir:EarlySeedlingStage` | early seedling stage |
| 25 | `onsir:ElectronBeam` | electron beam |
| 26 | `onsir:EmergenceAndEarlyVigor` | emergence and early vigour |
| 27 | `onsir:Endpoint` | endpoint |
| 28 | `onsir:EndpointCategory` | endpoint category |
| 29 | `onsir:EnzymeActivityChange` | enzyme activity change |
| 30 | `onsir:FreshMass` | fresh mass |
| 31 | `onsir:Gamma` | gamma |
| 32 | `onsir:GeneticEndpointCategory` | genetic endpoint category |
| 33 | `onsir:GerminationRate` | germination rate |
| 34 | `onsir:GerminationStage` | germination stage |
| 35 | `onsir:HighDoseRate` | high dose rate |
| 36 | `onsir:HormeticDose` | hormetic dose |
| 37 | `onsir:HormeticResponse` | hormetic response |
| 38 | `onsir:Ir192` | iridium-192 |
| 39 | `onsir:Isotope` | radioisotope |
| 40 | `onsir:LifecycleStage` | life-cycle stage |
| 41 | `onsir:LightCondition` | light condition |
| 42 | `onsir:LipidPeroxidation` | lipid peroxidation |
| 43 | `onsir:LowDoseRate` | low dose rate |
| 44 | `onsir:MorphologicalEndpointCategory` | morphological endpoint category |
| 45 | `onsir:MutagenicDose` | mutagenic dose |
| 46 | `onsir:MutagenicOutcome` | mutagenic outcome |
| 47 | `onsir:MutagenicResponse` | mutagenic response |
| 48 | `onsir:MutationFrequency` | mutation frequency |
| 49 | `onsir:Neutron` | neutron |
| 50 | `onsir:Nicotiana_tabacum_AboveFavourableBandDose` | Nicotiana tabacum above favourable band dose |
| 51 | `onsir:Nicotiana_tabacum_BelowFavourableBandDose` | Nicotiana tabacum below favourable band dose |
| 52 | `onsir:Nicotiana_tabacum_WithinFavourableBandDose` | Nicotiana tabacum within favourable band dose |
| 53 | `onsir:OtherPhysiologicalEndpointCategory` | other physiological endpoint category |
| 54 | `onsir:Plant` | plant |
| 55 | `onsir:PlantCallus` | plant callus |
| 56 | `onsir:PlantHealthEndpointCategory` | plant health endpoint category |
| 57 | `onsir:PlantPart` | plant part |
| 58 | `onsir:PlantSeed` | plant seed |
| 59 | `onsir:PollenSterility` | pollen sterility |
| 60 | `onsir:Proton` | proton |
| 61 | `onsir:QuantityValue` | quantity value |
| 62 | `onsir:ROSBalanceShift` | ROS balance shift |
| 63 | `onsir:RadiationType` | radiation type |
| 64 | `onsir:Response` | response |
| 65 | `onsir:RootLength` | root length |
| 66 | `onsir:SeedIrradiationTreatment` | seed irradiation treatment |
| 67 | `onsir:SeedStage` | seed stage |
| 68 | `onsir:SeedSterility` | seed sterility |
| 69 | `onsir:SeedTreatment` | seed treatment |
| 70 | `onsir:Seedling` | seedling |
| 71 | `onsir:SeedlingVigorIndex` | seedling vigour index |
| 72 | `onsir:ShootLength` | shoot length |
| 73 | `onsir:SoilCondition` | soil condition |
| 74 | `onsir:SterilizationDose` | sterilization dose |
| 75 | `onsir:SterilizationResponse` | sterilization response |
| 76 | `onsir:StimulatoryOutcome` | stimulatory outcome |
| 77 | `onsir:StressResistance` | stress resistance |
| 78 | `onsir:Substrate` | substrate |
| 79 | `onsir:TemperatureCondition` | temperature condition |
| 80 | `onsir:TreatmentOutcome` | treatment outcome |
| 81 | `onsir:Trigonella_foenum_graecum_BelowLD50Dose` | Trigonella foenum-graecum below LD50 dose |
| 82 | `onsir:UV_A` | UV-A |
| 83 | `onsir:UV_B` | UV-B |
| 84 | `onsir:UV_C` | UV-C |
| 85 | `onsir:Vigna_unguiculata_AtOrAboveLD50Dose` | Vigna unguiculata at or above LD50 dose |
| 86 | `onsir:Vigna_unguiculata_BelowLD50Dose` | Vigna unguiculata below LD50 dose |
| 87 | `onsir:WaterQuality` | water quality |
| 88 | `onsir:WithinReportedFavourableBand` | within reported favourable band |
| 89 | `onsir:XRay` | X-ray |
| 90 | `onsir:Xe133` | xenon-133 |

## 4. (a) EXACT label matches

### 4.1 Against RBO-native classes

| OnSIR class | OnSIR IRI | normalised string matched | RBO class | RBO IRI |
|---|---|---|---|---|
| cobalt-60 | `https://w3id.org/onsir/Co60` | `co 60` | cobalt-60 gamma radiation | `http://purl.obolibrary.org/obo/RBO_00000052` |
| caesium-137 | `https://w3id.org/onsir/Cs137` | `cs 137` | cesium-137 gamma radiation | `http://purl.obolibrary.org/obo/RBO_00000051` |
| X-ray | `https://w3id.org/onsir/XRay` | `x ray` | x-ray radiation | `http://purl.obolibrary.org/obo/RBO_00005013` |

**3 of 90 OnSIR classes (3.3%) have an exact label/synonym match among the 446 RBO-native classes.** All three are radionuclide or radiation-quality terms; the match is to RBO's *radiation* class (e.g. `onsir:Co60` to 'cobalt-60 gamma radiation'), which is a related but not identical concept -- OnSIR's `Co60` is the isotope, RBO's is the radiation emitted by it.

### 4.2 Against all 9221 classes in the merged rbo.owl file

| OnSIR class | OnSIR IRI | string matched | matched class | IRI | source |
|---|---|---|---|---|---|
| cobalt-60 | `https://w3id.org/onsir/Co60` | `co 60` | cobalt-60 gamma radiation | `http://purl.obolibrary.org/obo/RBO_00000052` | RBO |
| caesium-137 | `https://w3id.org/onsir/Cs137` | `cs 137` | cesium-137 gamma radiation | `http://purl.obolibrary.org/obo/RBO_00000051` | RBO |
| gamma | `https://w3id.org/onsir/Gamma` | `gamma` | photon | `http://purl.obolibrary.org/obo/CHEBI_30212` | CHEBI |
| life-cycle stage | `https://w3id.org/onsir/LifecycleStage` | `life cycle stage` | life cycle stage | `http://purl.obolibrary.org/obo/UBERON_0000105` | UBERON |
| life-cycle stage | `https://w3id.org/onsir/LifecycleStage` | `life cycle stage` | developmental stage | `http://www.ebi.ac.uk/efo/EFO_0000399` | http://www.ebi.ac.uk/efo |
| neutron | `https://w3id.org/onsir/Neutron` | `neutron` | neutron | `http://purl.obolibrary.org/obo/CHEBI_30222` | CHEBI |
| plant | `https://w3id.org/onsir/Plant` | `plant` | plant-associated environment | `http://purl.obolibrary.org/obo/ENVO_01001001` | ENVO |
| proton | `https://w3id.org/onsir/Proton` | `proton` | proton | `http://purl.obolibrary.org/obo/CHEBI_24636` | CHEBI |
| X-ray | `https://w3id.org/onsir/XRay` | `x ray` | x-ray radiation | `http://purl.obolibrary.org/obo/RBO_00005013` | RBO |

**8 of 90 OnSIR classes (8.9%) have an exact match somewhere in the merged file.** Note that `onsir:Plant` matches ENVO's 'plant-associated environment' through a synonym rather than a plant class, and `onsir:Gamma` matches ChEBI's 'photon' through the synonym 'gamma'; neither is a usable alignment.

## 5. (b) NEAR matches (SequenceMatcher ratio >= 0.85)

Rows are ordered by token Jaccard first, then ratio. Jaccard 0.000 means the two strings share no whole token and the similarity is orthographic only.

### 5.1 Against RBO-native classes

**None.** No OnSIR class reaches ratio >= 0.85 against any RBO-native class, so the exact matches in section 4.1 are the entire overlap.

### 5.2 Against all classes in the merged file

| OnSIR class | OnSIR form | matched class | IRI | source | ratio | Jaccard |
|---|---|---|---|---|---|---|
| context | `context` | composition | `http://purl.obolibrary.org/obo/PATO_0000025` | PATO | 0.857 | 0.000 |
| neutron | `neutron` | neuron | `http://purl.obolibrary.org/obo/CL_0000540` | CL | 0.923 | 0.000 |
| plant | `plant` | Viridiplantae | `http://purl.obolibrary.org/obo/NCBITaxon_33090` | NCBITaxon | 0.909 | 0.000 |
| plant | `plant` | Embryophyta | `http://purl.obolibrary.org/obo/NCBITaxon_3193` | NCBITaxon | 0.909 | 0.000 |
| plant | `plant` | planet | `http://purl.obolibrary.org/obo/ENVO_01000800` | ENVO | 0.909 | 0.000 |
| plant | `plant` | plan | `http://purl.obolibrary.org/obo/OBI_0000260` | OBI | 0.889 | 0.000 |
| UV-A | `uv a` | microampere | `http://purl.obolibrary.org/obo/UO_0000038` | UO | 0.857 | 0.333 |

4 OnSIR classes have at least one near match in the merged file, but only 1 share any token with their match (UV-A); the remainder are orthographic coincidences.

## 6. (c) OnSIR classes with no RBO counterpart

Against **RBO-native** classes, **87 of 90** OnSIR classes (96.7%) have neither an exact nor a near (>= 0.85) counterpart. Groups are the top-level class reached by following `rdfs:subClassOf` upwards inside the OnSIR namespace.

| OnSIR top-level group | unmatched | members |
|---|---|---|
| Endpoint | 17 | `AntioxidantActivity`, `AntioxidantIncrease`, `BiochemicalChange`, `ChlorophyllContent`, `CotyledonFreeing`, `DryMass`, `EnzymeActivityChange`, `FreshMass`, `GerminationRate`, `LipidPeroxidation`, `MutationFrequency`, `PollenSterility`, `ROSBalanceShift`, `RootLength`, `SeedSterility`, `SeedlingVigorIndex`, `ShootLength` |
| OnSIR root class, no asserted superclass | 14 | `Context`, `DoseAssessment`, `DoseCategory`, `DoseRange`, `DoseRateCategory`, `DoseResponseModel`, `EndpointCategory`, `Isotope`, `LifecycleStage`, `MutagenicOutcome`, `QuantityValue`, `RadiationType`, `StimulatoryOutcome`, `TreatmentOutcome` |
| DoseAssessment | 11 | `AboveReportedFavourableBand`, `AtOrAboveReportedLD50`, `BelowReportedFavourableBand`, `BelowReportedLD50`, `Nicotiana_tabacum_AboveFavourableBandDose`, `Nicotiana_tabacum_BelowFavourableBandDose`, `Nicotiana_tabacum_WithinFavourableBandDose`, `Trigonella_foenum_graecum_BelowLD50Dose`, `Vigna_unguiculata_AtOrAboveLD50Dose`, `Vigna_unguiculata_BelowLD50Dose`, `WithinReportedFavourableBand` |
| RadiationType | 7 | `ElectronBeam`, `Gamma`, `Neutron`, `Proton`, `UV_A`, `UV_B`, `UV_C` |
| EndpointCategory | 6 | `BiochemicalEndpointCategory`, `EmergenceAndEarlyVigor`, `GeneticEndpointCategory`, `MorphologicalEndpointCategory`, `OtherPhysiologicalEndpointCategory`, `PlantHealthEndpointCategory` |
| Response | 6 | `AbioticStressResistance`, `BioticStressResistance`, `HormeticResponse`, `MutagenicResponse`, `SterilizationResponse`, `StressResistance` |
| Context | 5 | `LightCondition`, `SoilCondition`, `Substrate`, `TemperatureCondition`, `WaterQuality` |
| DoseCategory | 3 | `HormeticDose`, `MutagenicDose`, `SterilizationDose` |
| Isotope | 3 | `Am241`, `Ir192`, `Xe133` |
| LifecycleStage | 3 | `EarlySeedlingStage`, `GerminationStage`, `SeedStage` |
| DoseRateCategory | 2 | `HighDoseRate`, `LowDoseRate` |
| OnSIR root class, parent outside OnSIR: BFO_0000015 | 2 | `Response`, `SeedTreatment` |
| OnSIR root class, parent outside OnSIR: BFO_0000040 | 2 | `Plant`, `Seedling` |
| PlantPart | 2 | `PlantCallus`, `PlantSeed` |
| DoseResponseModel | 1 | `BrainCousensModel` |
| OnSIR root class, parent outside OnSIR: BFO_0000019 | 1 | `Endpoint` |
| OnSIR root class, parent outside OnSIR: BFO_0000040, PO_0025131 | 1 | `PlantPart` |
| SeedTreatment | 1 | `SeedIrradiationTreatment` |


**Endpoint** (17)

- `onsir:AntioxidantActivity` -- antioxidant activity
- `onsir:AntioxidantIncrease` -- antioxidant increase
- `onsir:BiochemicalChange` -- biochemical change
- `onsir:ChlorophyllContent` -- chlorophyll content
- `onsir:CotyledonFreeing` -- cotyledon freeing
- `onsir:DryMass` -- dry mass
- `onsir:EnzymeActivityChange` -- enzyme activity change
- `onsir:FreshMass` -- fresh mass
- `onsir:GerminationRate` -- germination rate
- `onsir:LipidPeroxidation` -- lipid peroxidation
- `onsir:MutationFrequency` -- mutation frequency
- `onsir:PollenSterility` -- pollen sterility
- `onsir:ROSBalanceShift` -- ROS balance shift
- `onsir:RootLength` -- root length
- `onsir:SeedSterility` -- seed sterility
- `onsir:SeedlingVigorIndex` -- seedling vigour index
- `onsir:ShootLength` -- shoot length

**OnSIR root class, no asserted superclass** (14)

- `onsir:Context` -- context
- `onsir:DoseAssessment` -- dose assessment
- `onsir:DoseCategory` -- dose category
- `onsir:DoseRange` -- dose range
- `onsir:DoseRateCategory` -- dose-rate category
- `onsir:DoseResponseModel` -- dose–response model
- `onsir:EndpointCategory` -- endpoint category
- `onsir:Isotope` -- radioisotope
- `onsir:LifecycleStage` -- life-cycle stage
- `onsir:MutagenicOutcome` -- mutagenic outcome
- `onsir:QuantityValue` -- quantity value
- `onsir:RadiationType` -- radiation type
- `onsir:StimulatoryOutcome` -- stimulatory outcome
- `onsir:TreatmentOutcome` -- treatment outcome

**DoseAssessment** (11)

- `onsir:AboveReportedFavourableBand` -- above reported favourable band
- `onsir:AtOrAboveReportedLD50` -- at or above reported LD50
- `onsir:BelowReportedFavourableBand` -- below reported favourable band
- `onsir:BelowReportedLD50` -- below reported LD50
- `onsir:Nicotiana_tabacum_AboveFavourableBandDose` -- Nicotiana tabacum above favourable band dose
- `onsir:Nicotiana_tabacum_BelowFavourableBandDose` -- Nicotiana tabacum below favourable band dose
- `onsir:Nicotiana_tabacum_WithinFavourableBandDose` -- Nicotiana tabacum within favourable band dose
- `onsir:Trigonella_foenum_graecum_BelowLD50Dose` -- Trigonella foenum-graecum below LD50 dose
- `onsir:Vigna_unguiculata_AtOrAboveLD50Dose` -- Vigna unguiculata at or above LD50 dose
- `onsir:Vigna_unguiculata_BelowLD50Dose` -- Vigna unguiculata below LD50 dose
- `onsir:WithinReportedFavourableBand` -- within reported favourable band

**RadiationType** (7)

- `onsir:ElectronBeam` -- electron beam
- `onsir:Gamma` -- gamma
- `onsir:Neutron` -- neutron
- `onsir:Proton` -- proton
- `onsir:UV_A` -- UV-A
- `onsir:UV_B` -- UV-B
- `onsir:UV_C` -- UV-C

**EndpointCategory** (6)

- `onsir:BiochemicalEndpointCategory` -- biochemical endpoint category
- `onsir:EmergenceAndEarlyVigor` -- emergence and early vigour
- `onsir:GeneticEndpointCategory` -- genetic endpoint category
- `onsir:MorphologicalEndpointCategory` -- morphological endpoint category
- `onsir:OtherPhysiologicalEndpointCategory` -- other physiological endpoint category
- `onsir:PlantHealthEndpointCategory` -- plant health endpoint category

**Response** (6)

- `onsir:AbioticStressResistance` -- abiotic stress resistance
- `onsir:BioticStressResistance` -- biotic stress resistance
- `onsir:HormeticResponse` -- hormetic response
- `onsir:MutagenicResponse` -- mutagenic response
- `onsir:SterilizationResponse` -- sterilization response
- `onsir:StressResistance` -- stress resistance

**Context** (5)

- `onsir:LightCondition` -- light condition
- `onsir:SoilCondition` -- soil condition
- `onsir:Substrate` -- substrate
- `onsir:TemperatureCondition` -- temperature condition
- `onsir:WaterQuality` -- water quality

**DoseCategory** (3)

- `onsir:HormeticDose` -- hormetic dose
- `onsir:MutagenicDose` -- mutagenic dose
- `onsir:SterilizationDose` -- sterilization dose

**Isotope** (3)

- `onsir:Am241` -- americium-241
- `onsir:Ir192` -- iridium-192
- `onsir:Xe133` -- xenon-133

**LifecycleStage** (3)

- `onsir:EarlySeedlingStage` -- early seedling stage
- `onsir:GerminationStage` -- germination stage
- `onsir:SeedStage` -- seed stage

**DoseRateCategory** (2)

- `onsir:HighDoseRate` -- high dose rate
- `onsir:LowDoseRate` -- low dose rate

**OnSIR root class, parent outside OnSIR: BFO_0000015** (2)

- `onsir:Response` -- response
- `onsir:SeedTreatment` -- seed treatment

**OnSIR root class, parent outside OnSIR: BFO_0000040** (2)

- `onsir:Plant` -- plant
- `onsir:Seedling` -- seedling

**PlantPart** (2)

- `onsir:PlantCallus` -- plant callus
- `onsir:PlantSeed` -- plant seed

**DoseResponseModel** (1)

- `onsir:BrainCousensModel` -- Brain–Cousens model

**OnSIR root class, parent outside OnSIR: BFO_0000019** (1)

- `onsir:Endpoint` -- endpoint

**OnSIR root class, parent outside OnSIR: BFO_0000040, PO_0025131** (1)

- `onsir:PlantPart` -- plant part

**SeedTreatment** (1)

- `onsir:SeedIrradiationTreatment` -- seed irradiation treatment

Against **all** classes in the merged file, 80 of 90 OnSIR classes (88.9%) remain unmatched: `AbioticStressResistance`, `AboveReportedFavourableBand`, `Am241`, `AntioxidantActivity`, `AntioxidantIncrease`, `AtOrAboveReportedLD50`, `BelowReportedFavourableBand`, `BelowReportedLD50`, `BiochemicalChange`, `BiochemicalEndpointCategory`, `BioticStressResistance`, `BrainCousensModel`, `ChlorophyllContent`, `CotyledonFreeing`, `DoseAssessment`, `DoseCategory`, `DoseRange`, `DoseRateCategory`, `DoseResponseModel`, `DryMass`, `EarlySeedlingStage`, `ElectronBeam`, `EmergenceAndEarlyVigor`, `Endpoint`, `EndpointCategory`, `EnzymeActivityChange`, `FreshMass`, `GeneticEndpointCategory`, `GerminationRate`, `GerminationStage`, `HighDoseRate`, `HormeticDose`, `HormeticResponse`, `Ir192`, `Isotope`, `LightCondition`, `LipidPeroxidation`, `LowDoseRate`, `MorphologicalEndpointCategory`, `MutagenicDose`, `MutagenicOutcome`, `MutagenicResponse`, `MutationFrequency`, `Nicotiana_tabacum_AboveFavourableBandDose`, `Nicotiana_tabacum_BelowFavourableBandDose`, `Nicotiana_tabacum_WithinFavourableBandDose`, `OtherPhysiologicalEndpointCategory`, `PlantCallus`, `PlantHealthEndpointCategory`, `PlantPart`, `PlantSeed`, `PollenSterility`, `QuantityValue`, `ROSBalanceShift`, `RadiationType`, `Response`, `RootLength`, `SeedIrradiationTreatment`, `SeedStage`, `SeedSterility`, `SeedTreatment`, `Seedling`, `SeedlingVigorIndex`, `ShootLength`, `SoilCondition`, `SterilizationDose`, `SterilizationResponse`, `StimulatoryOutcome`, `StressResistance`, `Substrate`, `TemperatureCondition`, `TreatmentOutcome`, `Trigonella_foenum_graecum_BelowLD50Dose`, `UV_B`, `UV_C`, `Vigna_unguiculata_AtOrAboveLD50Dose`, `Vigna_unguiculata_BelowLD50Dose`, `WaterQuality`, `WithinReportedFavourableBand`, `Xe133`.

## 7. (d) Targeted probe for seed-irradiation dose-effect concepts

Column meanings. **Denoted in RBO-native**: an `obo:RBO_*` class whose `rdfs:label` or synonym denotes the concept. **Anywhere in file**: the same test over all 9221 named classes, with the contributing ontology named. **As individual**: named individuals whose label denotes the concept (RBO uses individuals for cohorts, facilities and instrument records). **Related RBO-native label**: the nearest broader or adjacent RBO term when the concept itself is absent, so that a gap is not claimed where RBO merely uses different wording. **Prose only**: entities that mention the phrase in free-text annotation while no entity denotes it by a label, which is coverage in prose only (10567 annotation strings over 10030 entities scanned).

| Concept | Denoted in RBO-native? | RBO-native IRIs | Anywhere in file? | As individual | Related RBO-native label | Prose only |
|---|---|---|---|---|---|---|
| **seed** | **NO** | -- | yes (1: NCBITaxon=1) | 0 | -- | 6 |
| **seed irradiation** | **NO** | -- | **NO** | 0 | radiation exposure; accidental radiation exposure; planned radiation exposure; medical diagnostic radiation exposure; +21 | 0 |
| **hormesis / radiohormesis** | **NO** | -- | **NO** | 0 | low dose radiation study type; optically stimulated luminescence dosimeter | 0 |
| **mutation breeding** | **NO** | -- | **NO** | 0 | mutagenesis study | 0 |
| **sterilization** | **NO** | -- | **NO** | 0 | -- | 0 |
| **dose rate** | **YES** (4) | `RBO_00000029` dose rate; `RBO_00005011` absorbed radiation dose rate; `RBO_00005038` average fractionated dose rate; `RBO_00015045` high dose rate irradiation | yes (4: RBO=4) | 2 | dose rate; absorbed radiation dose rate; average fractionated dose rate; high dose rate irradiation | 9 |
| **gray** | **YES** (1) | `RBO_00005066` miligray per second *(deprecated)* | yes (14: UO=13, RBO=1) | 11 | miligray per second | 3 |
| **absorbed dose** | **YES** (2) | `RBO_00005010` absorbed radiation dose; `RBO_00005011` absorbed radiation dose rate | yes (3: RBO=2, UO=1) | 0 | effective dose; equivalent dose; dose fraction; dose rate; +11 | 29 |
| **germination** | **NO** | -- | **NO** | 0 | -- | 0 |
| **dose-response** | **NO** | -- | **NO** | 0 | radiation response modifier; peptide radiation response modifier; small molecule radiation response modifier; adaptive radiation response study; +3 | 3 |
| **hormetic dose** | **NO** | -- | **NO** | 0 | effective dose; equivalent dose; dose fraction; dose rate; +11 | 0 |
| **plant** | **NO** | -- | yes (37: ENVO=15, PO=14, NCBITaxon=5, PATO=2) | 0 | -- | 65 |

### 7.1 Concept-by-concept detail


**seed**

- Denoted by an RBO-native class: **no**
- Denoted anywhere in the merged file: NCBITaxon=1
  - `http://purl.obolibrary.org/obo/NCBITaxon_58024` -- Spermatophyta [NCBITaxon]
- Nearest related RBO-native labels: none
- Phrase present only in free-text annotation of 6 entities (6 classes, 0 individuals): `GO_0007020` (microtubule nucleation), `GO_0009790` (embryo development), `GO_0048598` (embryonic morphogenesis), `PO_0005029` (root primordium), `PO_0025433` (root anlagen), `UBERON_0000922` (embryo)

**seed irradiation**

- Denoted by an RBO-native class: **no**
- Denoted anywhere in the merged file: **no**
- Nearest related RBO-native labels: radiation exposure (`RBO_00002000`), accidental radiation exposure (`RBO_00002001`), planned radiation exposure (`RBO_00002002`), medical diagnostic radiation exposure (`RBO_00002003`), exposure to naturally ocurring radioactive material (`RBO_00002004`), medical therapeutic radiation exposure (`RBO_00002005`), irradiation (`RBO_00002117`), unplanned irradiation (`RBO_00002119`), unplanned anthropogenic irradiation (`RBO_00002120`), sham irradiation (`RBO_00005015`)

**hormesis / radiohormesis**

- Denoted by an RBO-native class: **no**
- Denoted anywhere in the merged file: **no**
- Nearest related RBO-native labels: low dose radiation study type (`RBO_00010056`), optically stimulated luminescence dosimeter (`RBO_00015048`)

**mutation breeding**

- Denoted by an RBO-native class: **no**
- Denoted anywhere in the merged file: **no**
- Nearest related RBO-native labels: mutagenesis study (`RBO_00002092`)

**sterilization**

- Denoted by an RBO-native class: **no**
- Denoted anywhere in the merged file: **no**
- Nearest related RBO-native labels: none

**dose rate**

- Denoted by an RBO-native class: `RBO_00000029` = dose rate, `RBO_00005011` = absorbed radiation dose rate, `RBO_00005038` = average fractionated dose rate, `RBO_00015045` = high dose rate irradiation
- Denoted anywhere in the merged file: RBO=4
  - `http://purl.obolibrary.org/obo/RBO_00000029` -- dose rate [RBO]
  - `http://purl.obolibrary.org/obo/RBO_00005011` -- absorbed radiation dose rate [RBO]
  - `http://purl.obolibrary.org/obo/RBO_00005038` -- average fractionated dose rate [RBO]
  - `http://purl.obolibrary.org/obo/RBO_00015045` -- high dose rate irradiation [RBO]
- Denoted by named individuals: `RBO_00120016` (Low dose rate facility for animal), `RBO_00120017` (Low dose and low dose rate facility for cells)
- Nearest related RBO-native labels: dose rate (`RBO_00000029`), absorbed radiation dose rate (`RBO_00005011`), average fractionated dose rate (`RBO_00005038`), high dose rate irradiation (`RBO_00015045`)
- Phrase present only in free-text annotation of 9 entities (1 classes, 8 individuals): `RBO_00005037` (adaptive radiation response study), `RBO_00120001` (FAXITRON X-rays generator), `RBO_00120005` (Mixed beams facility), `RBO_00120007` (Gammacell40 Exactor), `RBO_00120014` (LIBIS), `RBO_00120018` (UNIPI-AmBe); +3 more

**gray**

- Denoted by an RBO-native class: `RBO_00005066` = miligray per second *(deprecated)*
- Denoted anywhere in the merged file: UO=13, RBO=1
  - `http://purl.obolibrary.org/obo/RBO_00005066` -- miligray per second [RBO] *(deprecated)*
  - `http://purl.obolibrary.org/obo/UO_0000134` -- gray [UO]
  - `http://purl.obolibrary.org/obo/UO_0000141` -- microgray [UO]
  - `http://purl.obolibrary.org/obo/UO_0000142` -- milligray [UO]
  - `http://purl.obolibrary.org/obo/UO_0000143` -- nanogray [UO]
  - `http://purl.obolibrary.org/obo/UO_0010055` -- centigray [UO]
  - `http://purl.obolibrary.org/obo/UO_0010060` -- gray per minute [UO]
  - `http://purl.obolibrary.org/obo/UO_0010061` -- centigray per minute [UO]
  - `http://purl.obolibrary.org/obo/UO_0010062` -- milligray per minute [UO]
  - `http://purl.obolibrary.org/obo/UO_0010063` -- milligray per day [UO]
  - `http://purl.obolibrary.org/obo/UO_0010064` -- milligray per hour [UO]
  - `http://purl.obolibrary.org/obo/UO_0010065` -- milligray per second [UO]
  - `http://purl.obolibrary.org/obo/UO_1000134` -- gray based unit [UO]
  - `http://purl.obolibrary.org/obo/UO_1010060` -- gray per minute based unit [UO]
- Denoted by named individuals: `UO_0000134` (gray), `UO_0000141` (microgray), `UO_0000142` (milligray), `UO_0000143` (nanogray), `UO_0010055` (centigray), `UO_0010060` (gray per minute)
- Nearest related RBO-native labels: miligray per second (`RBO_00005066`)
- Phrase present only in free-text annotation of 3 entities (3 classes, 0 individuals): `RBO_00010016` (radiation dose), `RBO_010016` (radiation dose), `UO_0000135` (rad)

**absorbed dose**

- Denoted by an RBO-native class: `RBO_00005010` = absorbed radiation dose, `RBO_00005011` = absorbed radiation dose rate
- Denoted anywhere in the merged file: RBO=2, UO=1
  - `http://purl.obolibrary.org/obo/RBO_00005010` -- absorbed radiation dose [RBO]
  - `http://purl.obolibrary.org/obo/RBO_00005011` -- absorbed radiation dose rate [RBO]
  - `http://purl.obolibrary.org/obo/UO_0000129` -- absorbed dose unit [UO]
- Nearest related RBO-native labels: effective dose (`RBO_00000014`), equivalent dose (`RBO_00000023`), dose fraction (`RBO_00000024`), dose rate (`RBO_00000029`), absorbed radiation dose (`RBO_00005010`), absorbed radiation dose rate (`RBO_00005011`), average fractionated dose rate (`RBO_00005038`), dose equivalent (`RBO_00010007`), organ dose (`RBO_00010014`), radiation dose (`RBO_00010016`)
- Phrase present only in free-text annotation of 29 entities (29 classes, 0 individuals): `PATO_0001739` (radiation quality), `RBO_00000022` (millirad), `RBO_00000023` (equivalent dose), `RBO_00000024` (dose fraction), `RBO_00005001` (heavy ion radiation), `RBO_00005066` (miligray per second); +23 more

**germination**

- Denoted by an RBO-native class: **no**
- Denoted anywhere in the merged file: **no**
- Nearest related RBO-native labels: none

**dose-response**

- Denoted by an RBO-native class: **no**
- Denoted anywhere in the merged file: **no**
- Nearest related RBO-native labels: radiation response modifier (`RBO_00000073`), peptide radiation response modifier (`RBO_00000074`), small molecule radiation response modifier (`RBO_00000075`), adaptive radiation response study (`RBO_00005037`), indirect cellular response to stimulus (`RBO_00005067`), indirect cellular response to radiation (`RBO_00005068`), indirect cellular response to ionising radiation (`RBO_00005069`)
- Phrase present only in free-text annotation of 3 entities (0 classes, 3 individuals): `RBO_00120047` (FREDERICA), `RBO_00120058` (The German uranium miners cohort study (WISMUT cohort)), `RBO_00120095` (LDRadStatsNet - Network of statisticians interested in low dose IR research)

**hormetic dose**

- Denoted by an RBO-native class: **no**
- Denoted anywhere in the merged file: **no**
- Nearest related RBO-native labels: effective dose (`RBO_00000014`), equivalent dose (`RBO_00000023`), dose fraction (`RBO_00000024`), dose rate (`RBO_00000029`), absorbed radiation dose (`RBO_00005010`), absorbed radiation dose rate (`RBO_00005011`), average fractionated dose rate (`RBO_00005038`), dose equivalent (`RBO_00010007`), organ dose (`RBO_00010014`), radiation dose (`RBO_00010016`)

**plant**

- Denoted by an RBO-native class: **no**
- Denoted anywhere in the merged file: ENVO=15, PO=14, NCBITaxon=5, PATO=2, CHEBI=1
  - `http://purl.obolibrary.org/obo/CHEBI_76924` -- plant metabolite [CHEBI]
  - `http://purl.obolibrary.org/obo/ENVO_00002214` -- power plant [ENVO]
  - `http://purl.obolibrary.org/obo/ENVO_00002215` -- geothermal power plant [ENVO]
  - `http://purl.obolibrary.org/obo/ENVO_00002271` -- nuclear power plant [ENVO]
  - `http://purl.obolibrary.org/obo/ENVO_01000413` -- old plant [ENVO]
  - `http://purl.obolibrary.org/obo/ENVO_01000414` -- young plant [ENVO]
  - `http://purl.obolibrary.org/obo/ENVO_01000536` -- factory [ENVO]
  - `http://purl.obolibrary.org/obo/ENVO_01000628` -- plant litter [ENVO]
  - `http://purl.obolibrary.org/obo/ENVO_01001001` -- plant-associated environment [ENVO]
  - `http://purl.obolibrary.org/obo/ENVO_01001057` -- environment associated with a plant part or small plant [ENVO]
  - `http://purl.obolibrary.org/obo/ENVO_01001121` -- plant matter [ENVO]
  - `http://purl.obolibrary.org/obo/ENVO_02000109` -- dust from plant parts [ENVO]
  - `http://purl.obolibrary.org/obo/ENVO_2000037` -- fossil fuel power plant [ENVO]
  - `http://purl.obolibrary.org/obo/ENVO_2000038` -- coal power plant [ENVO]
  - `http://purl.obolibrary.org/obo/ENVO_2000042` -- ocean thermal power station [ENVO]
  - `http://purl.obolibrary.org/obo/ENVO_2000043` -- tidal power plant [ENVO]
  - `http://purl.obolibrary.org/obo/NCBITaxon_3193` -- Embryophyta [NCBITaxon]
  - `http://purl.obolibrary.org/obo/NCBITaxon_33090` -- Viridiplantae [NCBITaxon]
  - `http://purl.obolibrary.org/obo/NCBITaxon_3398` -- Magnoliopsida [NCBITaxon]
  - `http://purl.obolibrary.org/obo/NCBITaxon_58023` -- Tracheophyta [NCBITaxon]
  - `http://purl.obolibrary.org/obo/NCBITaxon_58024` -- Spermatophyta [NCBITaxon]
  - `http://purl.obolibrary.org/obo/PATO_0001731` -- deciduous (plant) [PATO]
  - `http://purl.obolibrary.org/obo/PATO_0001733` -- evergreen (plant) [PATO]
  - `http://purl.obolibrary.org/obo/PO_0000003` -- whole plant [PO]
  - `http://purl.obolibrary.org/obo/PO_0007033` -- whole plant development stage [PO]
  - `http://purl.obolibrary.org/obo/PO_0009002` -- plant cell [PO]
  - `http://purl.obolibrary.org/obo/PO_0009007` -- portion of plant tissue [PO]
  - `http://purl.obolibrary.org/obo/PO_0009008` -- plant organ [PO]
  - `http://purl.obolibrary.org/obo/PO_0009011` -- plant structure [PO]
  - `http://purl.obolibrary.org/obo/PO_0009012` -- plant structure development stage [PO]
  - `http://purl.obolibrary.org/obo/PO_0025004` -- plant axis [PO]
  - `http://purl.obolibrary.org/obo/PO_0025007` -- collective plant organ structure [PO]
  - `http://purl.obolibrary.org/obo/PO_0025131` -- plant anatomical entity [PO]
  - `http://purl.obolibrary.org/obo/PO_0025337` -- life of whole plant stage [PO]
  - `http://purl.obolibrary.org/obo/PO_0025496` -- multi-tissue plant structure [PO]
  - `http://purl.obolibrary.org/obo/PO_0025497` -- collective plant structure [PO]
  - `http://purl.obolibrary.org/obo/PO_0025606` -- native plant cell [PO]
- Nearest related RBO-native labels: none
- Phrase present only in free-text annotation of 65 entities (57 classes, 8 individuals): `CHEBI_22315` (alkaloid), `CHEBI_33287` (fertilizer), `CHEBI_78295` (food component), `CL_0000034` (stem cell), `CL_0000039` (germ line cell), `CL_0010017` (zygote); +59 more

## 8. (e) Plant-related coverage in RBO

| Indicator | Regex | RBO-native classes | All classes in file |
|---|---|---|---|
| plant | `\bplants?\b` | 0 | 37 |
| seed | `\bseed` | 0 | 1 |
| germinat | `germinat` | 0 | 0 |
| crop | `\bcrops?\b` | 0 | 1 |
| cultivar | `\bcultivars?\b` | 0 | 0 |
| **union** | | **0 of 446 (0.00%)** | **38 of 9221 (0.41%)** |

Provenance of the 38 plant-related classes in the merged file:

| Source | Classes |
|---|---|
| ENVO | 16 |
| PO | 14 |
| NCBITaxon | 5 |
| PATO | 2 |
| CHEBI | 1 |

**No RBO-native class mentions plant, seed, germination, crop or cultivar in any label or synonym.** The 38 plant-related classes in the file are entirely contributed by the inlined ENVO, PO, NCBITaxon, PATO and ChEBI fragments, and 8 of the 37 hits on `plant` are ENVO industrial-facility senses (power plant, coal power plant, nuclear power plant, factory) rather than botanical ones.

### 8.1 Do the external classes OnSIR aligns to exist in RBO?

OnSIR asserts `skos:closeMatch`, `skos:exactMatch`, `owl:equivalentClass` or `rdfs:subClassOf` links to 20 classes in the `obo:` namespace. Their presence in the merged rbo.owl file bounds how much of OnSIR could be re-expressed inside RBO's existing import surface.

| External class OnSIR aligns to | Label in rbo.owl | Present in rbo.owl? | Used by OnSIR class |
|---|---|---|---|
| `http://purl.obolibrary.org/obo/BFO_0000015` | process | yes | `Response`, `SeedIrradiationTreatment`, `SeedTreatment` |
| `http://purl.obolibrary.org/obo/BFO_0000019` | quality | yes | `Endpoint` |
| `http://purl.obolibrary.org/obo/BFO_0000040` | material entity | yes | `Plant`, `PlantPart`, `PlantSeed`, `Seedling` |
| `http://purl.obolibrary.org/obo/CHEBI_15377` | water | yes | `WaterQuality` |
| `http://purl.obolibrary.org/obo/CHEBI_196959` | _n/a_ | **no** | `Cs137` |
| `http://purl.obolibrary.org/obo/CHEBI_22586` | antioxidant | yes | `AntioxidantActivity`, `AntioxidantIncrease` |
| `http://purl.obolibrary.org/obo/CHEBI_26523` | _n/a_ | **no** | `ROSBalanceShift` |
| `http://purl.obolibrary.org/obo/CHEBI_28966` | _n/a_ | **no** | `ChlorophyllContent` |
| `http://purl.obolibrary.org/obo/ENVO_00001998` | soil | yes | `SoilCondition` |
| `http://purl.obolibrary.org/obo/PATO_0000125` | mass | yes | `DryMass`, `FreshMass` |
| `http://purl.obolibrary.org/obo/PATO_0000146` | temperature | yes | `TemperatureCondition` |
| `http://purl.obolibrary.org/obo/PO_0005052` | _n/a_ | **no** | `PlantCallus` |
| `http://purl.obolibrary.org/obo/PO_0007057` | _n/a_ | **no** | `GerminationStage` |
| `http://purl.obolibrary.org/obo/PO_0008037` | _n/a_ | **no** | `Seedling` |
| `http://purl.obolibrary.org/obo/PO_0009010` | _n/a_ | **no** | `PlantSeed` |
| `http://purl.obolibrary.org/obo/PO_0020030` | _n/a_ | **no** | `CotyledonFreeing` |
| `http://purl.obolibrary.org/obo/PO_0025131` | plant anatomical entity | yes | `PlantPart` |
| `http://purl.obolibrary.org/obo/TO_0000227` | _n/a_ | **no** | `RootLength` |
| `http://purl.obolibrary.org/obo/TO_0000280` | _n/a_ | **no** | `SeedlingVigorIndex` |
| `http://purl.obolibrary.org/obo/TO_0000430` | _n/a_ | **no** | `GerminationRate` |

**9 of 20** external alignment targets are present in rbo.owl; **11 are absent**. The absent ones are precisely the plant- and redox-specific anchors: the PO seed, seedling, germination-stage and cotyledon classes, and the ChEBI classes for the Co-60 and Cs-137 nuclides, chlorophyll and reactive oxygen species.

## 9. Factual summary

RBO release 2026-07-16 is a single merged file of 27.9 MiB containing 354548 RDF triples, 9221 named `owl:Class` declarations and 1085 named individuals, of which only 446 classes (4.8%) carry RBO-native `obo:RBO_*` IRIs -- 405 active and 41 deprecated -- while the other 8775 are inlined from GO, UBERON, ChEBI, ENVO, UO, CL, NCBITaxon, PATO, OBI and PO. The RBO-native layer is a vocabulary of radiation physics, dosimetry, exposure environments and epidemiological study design: ion species and cosmic, accelerator and reactor sources, active and passive dosimeters, absorbed, equivalent, effective and organ dose, dose rate and dose fractionation, spaceflight habitats and cohort study types, which is why the physical side of a seed-irradiation protocol maps cleanly -- *dose rate* and *absorbed dose* are denoted by RBO-native classes (`RBO_00000029` dose rate, `RBO_00005010` absorbed radiation dose, `RBO_00010014` organ dose), while the *gray* itself is not an RBO term at all and resolves instead to the inlined UO unit fragment (`UO_0000134` gray, `UO_0010060` gray per minute, plus centigray and milligray variants), RBO's only native gray-derived class being the deprecated and misspelled `RBO_00005066` 'miligray per second'. The biological-effect side has no representation whatsoever: the substrings *hormes*, *hormetic*, *germinat*, *steriliz*, *mutation breeding*, *cultivar* occur nowhere in the file -- zero matches for each by independent `grep`, in labels, synonyms and prose alike -- and *dose-response* (or *dose-effect*) appears only inside the free-text definitions of 3 RBO named individuals recording epidemiology and effects-database resources (`RBO_00120047` FREDERICA; `RBO_00120058` The German uranium miners cohort study (WISMUT cohort); `RBO_00120095` LDRadStatsNet - Network of statisticians interested in low dose IR research), with no class or individual denoting the concept. Plant biology is likewise absent from RBO proper -- 0 of 446 RBO-native classes mention plant, seed, germination, crop or cultivar, the 38 plant-related classes in the file all come from the inlined ENVO, PO, NCBITaxon, PATO and ChEBI fragments, and 11 of the 20 external classes OnSIR aligns to (the PO seed, seedling, germination-stage and cotyledon terms, and the ChEBI Co-60, Cs-137, chlorophyll and ROS terms) are not in the file at all. Consequently 87 of OnSIR's 90 classes (96.7%) have no exact or near counterpart among RBO-native classes and 80 (88.9%) have none anywhere in the merged release, the residue being concentrated in the dose-category, response, endpoint, dose-response-model and experimental-context branches that carry the dose-effect semantics of the domain.

## 10. Limitations

- Matching is lexical. A concept present in RBO under a label that shares no token with OnSIR's would be scored as a gap; the section 7 probes and the `related RBO-native label` column are the safeguard against that, and for the six strings verified absent by independent `grep` (hormesis, hormetic, germinat, steriliz, mutation breeding, cultivar) there is nothing to miss because the substring count in the raw file is zero.
- No reasoner was run over RBO, so subsumption-based coverage (a superclass subsuming an OnSIR term without a lexically similar label) is not tested.
- The comparison is against the merged release as published. RBO's upstream import modules could in principle be extended with PO or GO terms that would change the second column of every table without any change to RBO's own 446 classes.
- The 446 RBO-native classes include 41 deprecated ones; percentages taken over the 405 active classes instead are marginally different and are reported alongside in section 2.

## 11. Cross-validation

The structural counts were reproduced with owlready2, an independent OWL parser, which returns the same 9221 classes and the same 446 `obo:RBO_*` classes, and confirms zero class labels containing *hormes*, *germinat*, *steriliz*, *cultivar* or *mutation breeding*, exactly one label equal to *gray* (`UO_0000134`) and four labels containing *dose rate*. owlready2 reports 808 individuals against rdflib's 1085 because it assigns the 276 punned UO entities -- declared both `owl:Class` and `owl:NamedIndividual` -- to the class side; 809 is the rdflib figure for individuals that are not also classes. The six absent substrings were additionally checked with `grep -ic` over the raw RDF/XML, which returns 0 for each, so their absence does not depend on either parser or on the label/synonym predicate list.

## 12. Reproduction

```sh
curl -sSL -o rbo.owl https://raw.githubusercontent.com/Radiobiology-Informatics-Consortium/RBO/v2026-07-23/rbo.owl
python rbo_gap.py
```

`rbo.owl` SHA-256 `ab2ff2f575e8857cabb3f5cd5ebefbd6fd02b4568949a4dae2cde356a4eb0c37`. If that digest differs, the RBO release has changed and the counts above will differ with it.
