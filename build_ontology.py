# -*- coding: utf-8 -*-
r"""Build the OnSIR ontology: take the class scaffold (OnSIR_base.owl) and assemble the full
OWL 2 DL ontology: persistent IRIs, metadata, disjointness partitions, existential and
cardinality restrictions, dose->effect GCIs and defined classes, object properties for radiation
type and isotope, functional and inverse properties, covering axioms, SKOS definitions, taxon dose
windows as datatype facets, and external alignments checked against OLS (BFO, PO, NCBITaxon,
ChEBI, PATO, ENVO, PECO, TO; units via QUDT).

Outputs OnSIR.ttl / OnSIR.owl (the ontology) and OnSIR_examples.ttl / OnSIR_examples.owl (the
illustrative individuals of the scaffold, whose values are invented, kept apart from the core).
"""
import rdflib
from rdflib import Graph, Namespace, URIRef, Literal, BNode, RDF, RDFS, OWL, XSD

SRC = "OnSIR_base.owl"
OLD = "http://example.org/SeedIrradCore#"
BASE = "https://w3id.org/onsir/"
ONT = URIRef("https://w3id.org/onsir")
NS = Namespace(BASE)
DCT = Namespace("http://purl.org/dc/terms/")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
OBO = Namespace("http://purl.obolibrary.org/obo/")
QUDT = Namespace("http://qudt.org/schema/qudt/")

def C(n): return NS[n]

# ---- load the class scaffold and rebase example.org -> w3id.org/onsir ----
g0 = Graph(); g0.parse(SRC)
g = Graph()
for s, p, o in g0:
    def rb(x):
        if isinstance(x, URIRef) and str(x).startswith(OLD):
            return NS[str(x)[len(OLD):]]
        return x
    g.add((rb(s), rb(p), rb(o)))
# drop old ontology header triples (rebased) — we rewrite metadata below
for s in list(g.subjects(RDF.type, OWL.Ontology)):
    for t in list(g.triples((s, None, None))): g.remove(t)
    for t in list(g.triples((None, None, s))): g.remove(t)

for pfx, n in [("", NS), ("onsir", NS), ("dct", DCT), ("skos", SKOS), ("obo", OBO),
               ("qudt", QUDT), ("owl", OWL), ("rdfs", RDFS)]:
    g.bind(pfx, n)

# ---- ontology header + real metadata ----
g.add((ONT, RDF.type, OWL.Ontology))
# The release version. It appears in the versionIRI, the versionInfo, CITATION.cff and the README;
# verify_release.py asserts that they agree.
VERSION = "1.6.0"
g.add((ONT, URIRef(str(OWL) + "versionIRI"), URIRef("https://w3id.org/onsir/" + VERSION)))
g.add((ONT, OWL.versionInfo, Literal(VERSION)))
g.add((ONT, URIRef(str(OWL) + "priorVersion"), URIRef("https://w3id.org/onsir/1.5.0")))
g.add((ONT, DCT.title, Literal("OnSIR: Ontology for Seed Irradiation and Plant Radiobiology")))
g.add((ONT, DCT.description, Literal(
    "An OWL 2 DL ontology of seed-irradiation treatments and their dose-dependent "
    "biological effects, aligned to BFO, PO, NCBITaxon, ChEBI, PATO, ENVO, PECO and TO with IRIs "
    "checked against the EBI Ontology Lookup Service and to QUDT for units, with dose-to-effect "
    "axioms and taxon dose windows for description-logic reasoning.")))
# Every creator is emitted as a resolvable ORCID agent IRI, which identifies a person where a name
# string can be shared. Each ORCID below was dereferenced against pub.orcid.org and its registered
# name checked against the name here.
for name, orcid in [("Luis Felipe Medeiro Alves", "0009-0005-4227-5568"),
                    ("Ferrucio de Franco Rosa", "0000-0001-9504-496X"),
                    ("Valter Arthur", "0000-0003-3521-9136")]:
    who = URIRef("https://orcid.org/" + orcid)
    g.add((ONT, DCT.creator, who))
    g.add((who, RDF.type, URIRef("http://xmlns.com/foaf/0.1/Person")))
    g.add((who, RDFS.label, Literal(name)))
g.add((ONT, DCT.license, URIRef("https://creativecommons.org/licenses/by/4.0/")))
g.add((ONT, DCT.created, Literal("2025-09-21", datatype=XSD.date)))
g.add((ONT, DCT.modified, Literal("2026-10-02", datatype=XSD.date)))
g.add((ONT, RDFS.comment, Literal("Canonical IRI https://w3id.org/onsir; source at "
                                  "https://github.com/lfmalves/OnSIR")))

# ---- helper: existential restriction (C subClassOf p some D) ----
def some(cls, prop, filler):
    r = BNode()
    g.add((r, RDF.type, OWL.Restriction)); g.add((r, OWL.onProperty, C(prop)))
    g.add((r, OWL.someValuesFrom, C(filler)))
    g.add((cls, RDFS.subClassOf, r))
    return r

def some_node(prop, filler):
    r = BNode()
    g.add((r, RDF.type, OWL.Restriction)); g.add((r, OWL.onProperty, C(prop)))
    g.add((r, OWL.someValuesFrom, C(filler)))
    return r

def all_disjoint(members):
    node = BNode()
    g.add((node, RDF.type, OWL.AllDisjointClasses))
    lst = BNode(); g.add((node, OWL.members, lst))
    items = [C(m) for m in members]
    cur = lst
    for i, it in enumerate(items):
        g.add((cur, RDF.first, it))
        if i < len(items) - 1:
            nxt = BNode(); g.add((cur, RDF.rest, nxt)); cur = nxt
        else:
            g.add((cur, RDF.rest, RDF.nil))

# ---- (1) disjointness partitions ----
all_disjoint(["HormeticDose", "MutagenicDose", "SterilizationDose"])
all_disjoint(["HormeticResponse", "MutagenicResponse", "SterilizationResponse"])
all_disjoint(["Gamma", "XRay", "Neutron", "Proton", "ElectronBeam", "UV_A", "UV_B", "UV_C"])
all_disjoint(["Am241", "Co60", "Cs137", "Ir192", "Xe133"])
all_disjoint(["LowDoseRate", "HighDoseRate"])

# ---- (2) radiation type and source isotope as object properties into the class trees ----
for op, rng in [("hasRadiationType", "RadiationType"), ("hasSourceIsotope", "Isotope")]:
    g.add((C(op), RDF.type, OWL.ObjectProperty))
    g.add((C(op), RDFS.domain, C("SeedIrradiationTreatment")))
    g.add((C(op), RDFS.range, C(rng)))
# remove redundant string datatype properties in favour of the typed object properties
for dp in ["radiationType", "sourceIsotope"]:
    for t in list(g.triples((C(dp), None, None))): g.remove(t)
    for t in list(g.triples((None, None, C(dp)))): g.remove(t)
    # ...and where they are used as predicates on the carried-over exemplar instances, so that no
    # free-text radiation type survives.
    for t in list(g.triples((None, C(dp), None))): g.remove(t)

# ---- (3) existential restrictions (structural constraints) ----
some(C("SeedIrradiationTreatment"), "hasDose", "QuantityValue")
some(C("SeedIrradiationTreatment"), "hasRadiationType", "RadiationType")
some(C("SeedIrradiationTreatment"), "induces", "Response")
some(C("DoseRange"), "minDose", "QuantityValue")
some(C("DoseRange"), "maxDose", "QuantityValue")
some(C("TreatmentOutcome"), "hasTreatment", "SeedIrradiationTreatment")
some(C("TreatmentOutcome"), "hasResponse", "Response")

# ---- (4) dose->effect: GCIs and defined classes (drive reasoner classification) ----
# GCI: an outcome at a hormetic dose necessarily exhibits a hormetic response (and likewise
# mutagenic, sterilizing). Encoded as (TreatmentOutcome and hasDoseCategory some X) subClassOf
# (hasResponse some Y).
def gci_dose_effect(dosecat, resp):
    lhs = BNode()
    g.add((lhs, RDF.type, OWL.Class))
    inter = BNode(); items = [C("TreatmentOutcome"), some_node("hasDoseCategory", dosecat)]
    # intersectionOf list
    lst = BNode(); g.add((lhs, OWL.intersectionOf, lst)); cur = lst
    for i, it in enumerate(items):
        g.add((cur, RDF.first, it))
        if i < len(items)-1:
            nxt = BNode(); g.add((cur, RDF.rest, nxt)); cur = nxt
        else:
            g.add((cur, RDF.rest, RDF.nil))
    g.add((lhs, RDFS.subClassOf, some_node("hasResponse", resp)))
gci_dose_effect("HormeticDose", "HormeticResponse")
gci_dose_effect("MutagenicDose", "MutagenicResponse")
gci_dose_effect("SterilizationDose", "SterilizationResponse")

# defined class: StimulatoryOutcome == TreatmentOutcome and hasResponse some HormeticResponse
def defined_class(name, prop, filler, base="TreatmentOutcome"):
    g.add((C(name), RDF.type, OWL.Class))
    eq = BNode(); g.add((C(name), OWL.equivalentClass, eq))
    g.add((eq, RDF.type, OWL.Class))
    lst = BNode(); g.add((eq, OWL.intersectionOf, lst))
    g.add((lst, RDF.first, C(base)))
    n2 = BNode(); g.add((lst, RDF.rest, n2))
    g.add((n2, RDF.first, some_node(prop, filler))); g.add((n2, RDF.rest, RDF.nil))
defined_class("StimulatoryOutcome", "hasResponse", "HormeticResponse")
defined_class("MutagenicOutcome", "hasResponse", "MutagenicResponse")

# ---- strip editorial notes carried over from the source skeleton ----
# The hand-authored base file contains "Integration touchpoint..." notes to the author. They are
# rdfs:comments, so the generated documentation publishes them as if they were class definitions.
# They are drafting notes and are removed.
_removed = 0
for _s, _p, _o in list(g.triples((None, RDFS.comment, None))):
    if "Integration touchpoint" in str(_o):
        g.remove((_s, _p, _o)); _removed += 1
print(f"  removed {_removed} editorial note(s) carried over from the source skeleton")

# ---- the dose classes that name a biological outcome: retained, annotated as discouraged ----
# A class called "HormeticDose" records a context-dependent empirical outcome as if it were a
# property of the dose. The three outcome-named categories stay active: they are subclasses of
# DoseCategory, members of a disjointness axiom, disjuncts of the DoseCategory covering axiom and
# antecedents of the dose->effect GCIs, and OBO obsoletion requires an obsolete term to carry no
# logical axioms. Each carries a definition and a note that steer new curation to a DoseAssessment
# with a numeric dose and a taxon, which the reasoner then places relative to the statistics reported
# for that taxon. The generated documentation renders the definition, so the guidance sits there.
DISCOURAGED = ["HormeticDose", "MutagenicDose", "SterilizationDose"]
for _old in DISCOURAGED:
    for _t in list(g.triples((C(_old), SKOS.definition, None))):
        g.remove(_t)
    g.add((C(_old), SKOS.definition, Literal(
        "A dose asserted by a curator to belong to this category. Discouraged for new annotation: the "
        "category names a biological outcome, and the outcome of one absorbed dose depends on taxon, "
        "endpoint and stage. Retained because data that already carries a dose category reasons "
        "through its axioms. Record the category as an individual typed with this class; the general "
        "class inclusion reads that typing. For new curation, record the numeric dose as a "
        "DoseAssessment with doseGy and forTaxon.")))
    g.add((C(_old), SKOS.note, Literal(
        "Kept active: an obsolete OBO term carries no logical axioms, and this class is the "
        "antecedent of a general class inclusion. DoseAssessment records where a numeric dose lies "
        "relative to the statistics reported for its taxon.")))
    g.add((C(_old), SKOS.related, C("DoseAssessment")))

# ---- (5) declarations that the class expressions above depend on ----
# QuantityValue appears in four class expressions (dose and dose-bound restrictions) and was never
# declared, while qudt:QuantityValue was declared and used as the range of the same properties. An
# IRI in a logical position must be declared in OWL 2 DL, so it is declared and its identity stated.
g.add((C("QuantityValue"), RDF.type, OWL.Class))
g.add((C("QuantityValue"), RDFS.label, Literal("Quantity value", lang="en")))
g.add((C("QuantityValue"), OWL.equivalentClass, QUDT.QuantityValue))
g.add((QUDT.QuantityValue, RDF.type, OWL.Class))
# qudt:hasUnit and qudt:numericValue are used in property assertions on the exemplar
# quantity individuals, so they need declarations for OWL 2 DL. The source skeleton
# used qudt:unit, which QUDT retired in favour of qudt:hasUnit and which no longer
# dereferences; the unit IRIs unit/Gray and unit/Gy-PER-MIN do not exist either
# (QUDT spells them GRAY and GRAY-PER-MIN). All four were checked by dereferencing.
g.add((QUDT.hasUnit, RDF.type, OWL.ObjectProperty))
g.add((QUDT.numericValue, RDF.type, OWL.DatatypeProperty))
# numericValue was typed only as FunctionalProperty, a characteristic with no property declaration.
g.add((C("numericValue"), RDF.type, OWL.DatatypeProperty))
g.add((C("numericValue"), RDFS.domain, C("QuantityValue")))
g.add((C("numericValue"), RDFS.range, XSD.double))
g.add((C("numericValue"), RDFS.label, Literal("numeric value", lang="en")))

# ---- functional / characteristics ----
for fp in ["hasDose", "hasDoseRate", "minDose", "maxDose", "numericValue"]:
    g.add((C(fp), RDF.type, OWL.FunctionalProperty))
# dose-bound datatype properties (functional)
for dp, com in [("doseLowerGy", "lower dose bound in gray"), ("doseUpperGy", "upper dose bound in gray")]:
    g.add((C(dp), RDF.type, OWL.DatatypeProperty)); g.add((C(dp), RDF.type, OWL.FunctionalProperty))
    g.add((C(dp), RDFS.domain, C("DoseRange"))); g.add((C(dp), RDFS.range, XSD.double))
    g.add((C(dp), RDFS.comment, Literal(com)))

# ---- (6) VERIFIED external alignments (OLS-checked IRIs) ----
def align(local, iri, rel=RDFS.subClassOf):
    g.add((C(local), rel, URIRef(iri)))
# BFO upper level
align("SeedIrradiationTreatment", str(OBO)+"BFO_0000015")   # process
align("SeedTreatment", str(OBO)+"BFO_0000015")
for m in ["Plant", "PlantSeed", "PlantPart", "Seedling"]:
    align(m, str(OBO)+"BFO_0000040")                        # material entity
# BFO placement. A Response unfolds in time, so it is a process; an Endpoint is the measurable
# characteristic being scored, which is a quality.
align("Response", str(OBO)+"BFO_0000015", RDFS.subClassOf)      # process
for q in ["Endpoint"]:
    align(q, str(OBO)+"BFO_0000019")                        # quality
# PO
align("PlantSeed", str(OBO)+"PO_0009010", OWL.equivalentClass)   # seed
align("Seedling", str(OBO)+"PO_0008037", OWL.equivalentClass)    # seedling
align("GerminationStage", str(OBO)+"PO_0007057", SKOS.closeMatch)  # (germination-related stage)
# ChEBI isotopes (verified: Cs-137)
align("Cs137", str(OBO)+"CHEBI_196959", OWL.equivalentClass)
# ChEBI carries caesium-137 as a nuclide but has NO cobalt-60 class: searching it returns only
# radiopharmaceuticals (cobaltous chloride co 60, cyanocobalamin co 60). An earlier build aligned
# Co60 to CHEBI_749374 "cobaltous chloride co 60", reached through that class's "60co" synonym, a
# labelled compound. The target is the element, as a broader term.
align("Co60", str(OBO)+"CHEBI_27638", SKOS.broadMatch)      # cobalt atom (no Co-60 nuclide in ChEBI)
# dose units, as typed QUDT links on the quantity restrictions
g.add((C("QuantityValue"), RDFS.comment, Literal(
    "dose values carry a typed qudt:hasUnit link; absorbed dose is in gray")))
align("TemperatureCondition", str(OBO)+"PATO_0000146", SKOS.closeMatch)  # temperature (PATO)
# RBO gap note (Radiobiology Ontology has no seed-irradiation dose-effect classes -> OnSIR extends)
g.add((ONT, RDFS.seeAlso, URIRef("http://purl.obolibrary.org/obo/rbo.owl")))

# ---- (7) covering axioms: the categories are exhaustive ----
def union_equiv(cls, members):
    u = BNode(); g.add((C(cls), OWL.equivalentClass, u)); g.add((u, RDF.type, OWL.Class))
    lst = BNode(); g.add((u, OWL.unionOf, lst)); cur = lst
    for i, m in enumerate(members):
        g.add((cur, RDF.first, C(m)))
        if i < len(members)-1:
            nxt = BNode(); g.add((cur, RDF.rest, nxt)); cur = nxt
        else:
            g.add((cur, RDF.rest, RDF.nil))
union_equiv("DoseCategory", ["HormeticDose", "MutagenicDose", "SterilizationDose"])
union_equiv("Response", ["HormeticResponse", "MutagenicResponse", "SterilizationResponse"])

# ---- (8) qualified cardinality: a treatment has exactly one dose; an outcome one treatment ----
def exactly_one(cls, prop, filler):
    r = BNode(); g.add((r, RDF.type, OWL.Restriction)); g.add((r, OWL.onProperty, C(prop)))
    g.add((r, URIRef(str(OWL)+"qualifiedCardinality"), Literal(1, datatype=XSD.nonNegativeInteger)))
    g.add((r, OWL.onClass, C(filler))); g.add((cls, RDFS.subClassOf, r))
exactly_one(C("SeedIrradiationTreatment"), "hasDose", "QuantityValue")
exactly_one(C("TreatmentOutcome"), "hasTreatment", "SeedIrradiationTreatment")

# ---- (9) inverse object properties ----
g.add((C("isTreatmentOf"), RDF.type, OWL.ObjectProperty))
g.add((C("isTreatmentOf"), OWL.inverseOf, C("hasTreatment")))
g.add((C("inducedBy"), RDF.type, OWL.ObjectProperty))
g.add((C("inducedBy"), OWL.inverseOf, C("induces")))

# ---- (10) additional verified alignments (OLS-checked) ----
O = str(OBO)
align("PlantPart", O+"PO_0025131")                              # plant anatomical entity
align("ROSBalanceShift", O+"CHEBI_26523", SKOS.closeMatch)      # reactive oxygen species
align("AntioxidantActivity", O+"CHEBI_22586", SKOS.closeMatch)  # antioxidant
align("AntioxidantIncrease", O+"CHEBI_22586", SKOS.closeMatch)
align("ChlorophyllContent", O+"CHEBI_28966", SKOS.closeMatch)   # chlorophyll
align("SoilCondition", O+"ENVO_00001998", SKOS.closeMatch)      # soil
align("WaterQuality", O+"CHEBI_15377", SKOS.closeMatch)         # water
align("FreshMass", O+"PATO_0000125", SKOS.closeMatch)           # mass
align("DryMass", O+"PATO_0000125", SKOS.closeMatch)
align("CotyledonFreeing", O+"PO_0020030", SKOS.closeMatch)      # cotyledon
g.add((C("QuantityValue"), RDFS.comment, Literal(
    "dose rate values carry a typed qudt:hasUnit link; the unit asserted is gray per hour")))

# ---- (10b) exposure and trait vocabularies: PECO and TO (IRIs and labels checked on OLS) ----
# PECO names plant exposures by radiation quality; OnSIR's radiation types are kinds of radiation,
# so they are related to the exposure terms by skos:relatedMatch. A seed-irradiation treatment is a
# narrower case of PECO's radiation exposure. The endpoint classes name the traits TO defines.
align("SeedIrradiationTreatment", O+"PECO_0007151", SKOS.broadMatch)   # radiation exposure
align("Gamma", O+"PECO_0001022", SKOS.relatedMatch)                    # gamma radiation exposure
align("XRay", O+"PECO_0007628", SKOS.relatedMatch)                     # X-ray exposure
for _uv in ("UV_A", "UV_B", "UV_C"):
    align(_uv, O+"PECO_0007222", SKOS.relatedMatch)                    # ultraviolet light exposure
align("GerminationRate", O+"TO_0000430", SKOS.closeMatch)              # germination rate
align("SeedlingVigorIndex", O+"TO_0000280", SKOS.closeMatch)           # seedling vigor
align("RootLength", O+"TO_0000227", SKOS.closeMatch)                   # root length
align("Response", O+"TO_0000161", SKOS.relatedMatch)                   # radiation response trait

# ---- (10b2) biochemical changes are measured endpoints ----
# The scaffold placed BiochemicalChange under HormeticResponse and hasBiochemicalChange under induces,
# so every recorded shift in reactive oxygen species or antioxidants classified as a hormetic
# response. A biochemical change is measured, in either direction and at any dose, so it is an
# Endpoint, and the property relates a treatment to the change measured after it.
for _t in list(g.triples((C("BiochemicalChange"), RDFS.subClassOf, None))):
    g.remove(_t)
g.add((C("BiochemicalChange"), RDFS.subClassOf, C("Endpoint")))
g.add((C("BiochemicalChange"), SKOS.definition, Literal(
    "A biochemical characteristic measured after irradiation, such as the balance of reactive oxygen "
    "species, antioxidant content or an enzyme activity; the direction of the change is a result.")))
for _t in list(g.triples((C("hasBiochemicalChange"), RDFS.subPropertyOf, None))):
    g.remove(_t)
# ---- dose-rate categories ----
for _cat, _side in (("LowDoseRate", "below"), ("HighDoseRate", "above")):
    g.add((C(_cat), SKOS.definition, Literal(
        f"A reported dose rate {_side} 100 Gy h-1, the cut placed in the gap between the corpus rates "
        "of 78 and 303 Gy h-1; every rate in the corpus is an acute exposure.")))

# ---- (10c) subject of an outcome: a plant structure, seed or other ----
# The corpus irradiates seeds and, in one study, rice callus (PO plant callus). The subject of an outcome and the bearer
# of a taxon are therefore plant structures (PlantPart, under PO plant anatomical entity), and a seed
# is one of them, as in the Plant Ontology.
g.add((C("PlantSeed"), RDFS.subClassOf, C("PlantPart")))
g.add((C("PlantCallus"), RDF.type, OWL.Class))
g.add((C("PlantCallus"), RDFS.subClassOf, C("PlantPart")))
g.add((C("PlantCallus"), OWL.equivalentClass, URIRef(str(OBO) + "PO_0005052")))   # plant callus
g.add((C("PlantCallus"), SKOS.definition, Literal(
    "A callus irradiated as the propagule, as in in vitro mutagenesis of tissue culture.")))
for _t in list(g.triples((C("hasSubject"), RDFS.range, None))):
    g.remove(_t)
g.add((C("hasSubject"), RDFS.range, C("PlantPart")))
# The dose rate belongs to the treatment.
for _t in list(g.triples((C("hasDoseRateCategory"), RDFS.domain, None))):
    g.remove(_t)
g.add((C("hasDoseRateCategory"), RDFS.domain, C("SeedIrradiationTreatment")))

# ---- (11) SKOS definitions for core classes ----
DEFS = {
 "SeedIrradiationTreatment": "A treatment process in which seeds or other propagules are exposed to radiation of a specified type, source, dose and dose rate.",
 "TreatmentOutcome": "The observed result of a seed-irradiation treatment on a subject plant structure under a context, recorded with its response, endpoint or endpoint category.",
 "HormeticResponse": "A beneficial, stimulatory response to low-dose irradiation (e.g., enhanced germination, vigour, or stress resistance).",
 "DoseCategory": "A qualitative classification of an irradiation dose by its predominant biological effect.",
 "QuantityValue": "A measured quantity with a numeric value and a typed unit (absorbed dose in gray, dose rate in gray per hour or per minute).",
 "Endpoint": "A measurable characteristic used to quantify an irradiation outcome (e.g., germination rate, root length, mutation frequency).",
 "DoseResponseModel": "A parametric model describing how an endpoint varies with dose (e.g., the Brain-Cousens hormetic model).",
}
for name, d in DEFS.items():
    g.add((C(name), SKOS.definition, Literal(d)))

# ---- (12) provenance: grounded in the authors' prior work ----
g.add((ONT, DCT.source, URIRef("https://doi.org/10.56238/sevened2025.039-003")))  # book chapter
g.add((ONT, DCT.source, URIRef("https://doi.org/10.22456/2175-2745.146658")))     # RITA ontology
g.add((ONT, DCT.source, URIRef("https://doi.org/10.69547/TSFJB.030203")))         # tobacco hormesis model

# ============================================================================
# (13) CONTEXT-DEPENDENT NUMERIC DOSE CLASSIFICATION
# ----------------------------------------------------------------------------
# One absorbed dose stimulates tobacco seedlings and lies far below the doses studied in cowpea or
# fenugreek. The classification is therefore reified as a DoseAssessment (a numeric dose considered
# for a taxon) and each taxon carries its own dose windows as OWL 2 datatype facets, so that a
# reasoner derives the position of a dose from the numeric value together with the taxon.
#
# Each window is bounded by a statistic the cited source reports, at the strength the source states:
#   favourable band [lo, hi]: the doses in which the source reports the most favourable responses
#   LD50: a median-lethality estimate, or a lower bound when the source's highest dose left more
#         than half of the population alive
# A window extends past the doses the source tested wherever the statistic leaves it open, and the
# scope note of each window records the tested range.
# ============================================================================
NCBI = "http://purl.obolibrary.org/obo/NCBITaxon_"

# One dict per taxon. band: (lower end, upper end) of the reported favourable band, or None.
# ld50: the reported LD50, or None; ld50_kind: "estimate" or "lower bound". tested: the lowest and
# highest irradiated dose of the source, in Gy. NCBITaxon ids checked on OLS.
TAXON_WINDOWS = [
    {
        "taxon": 'Nicotiana tabacum',
        "ncbi": '4097',
        "band": (5.0, 15.0),
        "ld50": None,
        "ld50_kind": None,
        "tested": (2.5, 20.0),
        "qualifier": 'Both band ends are approximate: the source places the most favourable '
            'responses broadly between approximately 5 and 15 Gy, with the apparent maximum '
            'depending on variety, endpoint and sampling time.',
        "source": 'Alves et al. 2027, Radiat. Phys. Chem. 250:114279, '
            'doi:10.1016/j.radphyschem.2026.114279',
    },
    {
        "taxon": 'Vigna unguiculata',
        "ncbi": '3917',
        "band": None,
        "ld50": 132.0,
        "ld50_kind": 'estimate',
        "tested": (150.0, 300.0),
        "qualifier": 'Median of three genotype survival LD50s (129.8, 132.0, 150.2 Gy), each from a '
            'straight line fitted to survival at 50 % flowering relative to the control; observed '
            'survival at 150 Gy, the lowest dose tested, was 56 to 71 % and at 250 Gy zero, so the '
            'observations place two of the LD50s between 150 and 200 Gy and the third, whose 200 Gy row '
            'prints 75.86 % in both the lethality and the survival column, between 150 and 250 Gy.',
        "source": 'Gnankambary et al. 2019, Int. J. Genet. Mol. Biol. 11(2):29-33, '
            'doi:10.5897/IJGMB2019.0174',
    },
    {
        "taxon": 'Trigonella foenum-graecum',
        "ncbi": '78534',
        "band": None,
        "ld50": 350.0,
        "ld50_kind": 'lower bound',
        "tested": (150.0, 350.0),
        "qualifier": 'The source states that the LD50 is close to 350 Gy, its highest dose, at which '
            '64 % of seeds germinated and 56 % of seedlings survived, against 96 % and 90 % '
            'in the control. 350 Gy is encoded as a lower bound on the LD50, so only the '
            'window below it is defined.',
        "source": 'Patel et al. 2017, J. AgriSearch 4(4):237-241, doi:10.21921/jas.v4i04.10200',
    },
]

# --- classes and properties for the assessment context ---
# The classes name the position of a dose relative to the reported statistics, and the response
# classes stay separate. A favourable band records where a source saw its most favourable responses;
# an LD50 is a lethality statistic for one endpoint and scoring time.
GENERIC = [
    ("DoseAssessment",
     "A numeric absorbed dose considered for a given taxon, endpoint and stage; the unit of "
     "taxon-relative dose positioning."),
    ("BelowReportedFavourableBand",
     "A DoseAssessment whose dose is below the lower end of the favourable band reported for its "
     "taxon."),
    ("WithinReportedFavourableBand",
     "A DoseAssessment whose dose lies within the favourable band reported for its taxon, both ends "
     "included: the band of doses in which the source reports its most favourable responses. The "
     "position is evidence compatible with a stimulatory response."),
    ("AboveReportedFavourableBand",
     "A DoseAssessment whose dose exceeds the upper end of the favourable band reported for its "
     "taxon."),
    ("BelowReportedLD50",
     "A DoseAssessment whose dose is below the LD50 reported for its taxon, or below a reported lower "
     "bound on that LD50."),
    ("AtOrAboveReportedLD50",
     "A DoseAssessment whose dose reaches or exceeds the LD50 reported for its taxon. The LD50 is a "
     "50 % lethality statistic for one endpoint and scoring time."),
]
for cls, com in GENERIC:
    g.add((C(cls), RDF.type, OWL.Class)); g.add((C(cls), SKOS.definition, Literal(com)))
    if cls != "DoseAssessment":
        g.add((C(cls), RDFS.subClassOf, C("DoseAssessment")))
# Positions on the two sides of a statistic are disjoint intervals of the dose axis.
all_disjoint(["BelowReportedFavourableBand", "WithinReportedFavourableBand",
              "AboveReportedFavourableBand"])
all_disjoint(["BelowReportedLD50", "AtOrAboveReportedLD50"])
# Assumption: a taxon's favourable band lies below its LD50. A record that codes a band reaching the
# LD50 makes these two axioms fire, the ontology becomes inconsistent, and the record goes to a
# curator; the encoding check of reason_context.py rests on them.
for _pos in ("BelowReportedFavourableBand", "WithinReportedFavourableBand"):
    g.add((C(_pos), OWL.disjointWith, C("AtOrAboveReportedLD50")))
g.add((C("WithinReportedFavourableBand"), SKOS.note, Literal(
    "Declared disjoint from AtOrAboveReportedLD50, as is BelowReportedFavourableBand, on the "
    "assumption that a taxon's favourable band lies below its LD50. A record coding a band that "
    "reaches its LD50 makes the ontology inconsistent and is sent to a curator.")))
g.add((C("boundQualifier"), RDF.type, OWL.AnnotationProperty))
g.add((C("boundQualifier"), RDFS.label, Literal("bound qualifier", lang="en")))
g.add((C("boundQualifier"), SKOS.definition, Literal(
    "The strength at which the source of a dose window states the statistic that bounds it: an "
    "approximate band end, a regression estimate or a lower bound.")))

g.add((C("forTaxon"), RDF.type, OWL.ObjectProperty))
g.add((C("forTaxon"), RDFS.domain, C("DoseAssessment")))
g.add((C("forTaxon"), RDFS.comment, Literal("the taxon the assessment is relative to")))
g.add((C("forEndpoint"), RDF.type, OWL.ObjectProperty))
# Two rdfs:domain axioms are read conjunctively, and an endpoint can be named on a DoseAssessment or
# on a TreatmentOutcome, so the single domain is their union.
for _t in list(g.triples((C("forEndpoint"), RDFS.domain, None))):
    g.remove(_t)
_fe_dom = BNode()
g.add((_fe_dom, RDF.type, OWL.Class))
_l1 = BNode(); _l2 = BNode()
g.add((_fe_dom, OWL.unionOf, _l1))
g.add((_l1, RDF.first, C("DoseAssessment"))); g.add((_l1, RDF.rest, _l2))
g.add((_l2, RDF.first, C("TreatmentOutcome"))); g.add((_l2, RDF.rest, RDF.nil))
g.add((C("forEndpoint"), RDFS.domain, _fe_dom))
g.add((C("forEndpoint"), RDFS.range, C("Endpoint")))
# ---- endpoint categories (the review corpus's EP axis) ----
# The coded corpus records endpoints in six categories, coarser than OnSIR's Endpoint classes, so the
# axis is represented separately from the Endpoint tree and each outcome carries the category its
# source records.
g.add((C("EndpointCategory"), RDF.type, OWL.Class))
g.add((C("EndpointCategory"), SKOS.definition, Literal(
    "A coarse grouping of measured endpoints, as recorded by the coding scheme of a study corpus. "
    "Distinct from Endpoint, which names an individual measurable characteristic.")))
EP_CATS = [
    ("EmergenceAndEarlyVigor", "Emergence and early vigour."),
    ("BiochemicalEndpointCategory", "Biochemical endpoints."),
    ("GeneticEndpointCategory", "Genetic endpoints."),
    ("MorphologicalEndpointCategory", "Morphological and anatomical endpoints."),
    ("PlantHealthEndpointCategory", "Plant-health (phytosanitary) endpoints."),
    ("OtherPhysiologicalEndpointCategory", "Other physiological endpoints."),
]
for nm, dfn in EP_CATS:
    g.add((C(nm), RDF.type, OWL.Class))
    g.add((C(nm), RDFS.subClassOf, C("EndpointCategory")))
    g.add((C(nm), SKOS.definition, Literal(dfn)))
all_disjoint([nm for nm, _ in EP_CATS])
g.add((C("hasEndpointCategory"), RDF.type, OWL.ObjectProperty))
g.add((C("hasEndpointCategory"), RDFS.domain, C("TreatmentOutcome")))
g.add((C("hasEndpointCategory"), RDFS.range, C("EndpointCategory")))
g.add((C("hasEndpointCategory"), RDFS.comment, Literal(
    "relates an outcome to the coarse endpoint category recorded for it in the source corpus")))

g.add((C("atStage"), RDF.type, OWL.ObjectProperty))
g.add((C("atStage"), RDFS.domain, C("DoseAssessment")))
g.add((C("atStage"), RDFS.range, C("LifecycleStage")))
g.add((C("doseGy"), RDF.type, OWL.DatatypeProperty))
g.add((C("doseGy"), RDF.type, OWL.FunctionalProperty))
g.add((C("doseGy"), RDFS.domain, C("DoseAssessment")))
g.add((C("doseGy"), SKOS.definition, Literal("absorbed dose, expressed in gray")))
# a plant structure has a taxon
g.add((C("hasTaxon"), RDF.type, OWL.ObjectProperty))
g.add((C("hasTaxon"), RDFS.domain, C("PlantPart")))
g.add((C("hasTaxon"), RDFS.comment, Literal(
    "relates a plant structure to its taxon, an individual typed with an NCBITaxon class; the "
    "structure has the taxon as a property, and PlantSeed stays an anatomical class")))
g.add((C("expectedResponse"), RDF.type, OWL.ObjectProperty))
g.add((C("expectedResponse"), RDFS.domain, C("DoseAssessment")))
g.add((C("expectedResponse"), RDFS.range, C("Response")))

# --- helpers: OWL 2 datatype facet range, hasValue restriction, intersection ---
def _rdf_list(items):
    head = BNode(); cur = head
    for i, it in enumerate(items):
        g.add((cur, RDF.first, it))
        if i < len(items) - 1:
            nxt = BNode(); g.add((cur, RDF.rest, nxt)); cur = nxt
        else:
            g.add((cur, RDF.rest, RDF.nil))
    return head

NUMERIC_TYPES = (XSD.decimal, XSD.double)   # OWL 2 treats these as DISJOINT value spaces

def _facet_range(dt, lo, hi, lo_exclusive, hi_exclusive):
    dr = BNode()
    g.add((dr, RDF.type, RDFS.Datatype)); g.add((dr, OWL.onDatatype, dt))
    facets = []
    if lo is not None:
        f = BNode()
        g.add((f, XSD.minExclusive if lo_exclusive else XSD.minInclusive,
               Literal(lo, datatype=dt)))
        facets.append(f)
    if hi is not None:
        f = BNode()
        g.add((f, XSD.maxExclusive if hi_exclusive else XSD.maxInclusive,
               Literal(hi, datatype=dt)))
        facets.append(f)
    g.add((dr, OWL.withRestrictions, _rdf_list(facets)))
    return dr

def dose_range(lo=None, hi=None, lo_exclusive=True, hi_exclusive=False):
    """A dose window as a faceted data range.

    OWL 2 gives xsd:decimal and xsd:double disjoint value spaces, and different tools serialize
    a plain numeric literal differently (rdflib emits xsd:double, owlready2 emits xsd:decimal).
    A window declared on only one of them silently fails to classify literals written by the
    other. We therefore build the window as a DataUnionOf over both, so classification is
    independent of which serializer produced the ABox.
    """
    parts = [_facet_range(dt, lo, hi, lo_exclusive, hi_exclusive) for dt in NUMERIC_TYPES]
    u = BNode()
    g.add((u, RDF.type, RDFS.Datatype)); g.add((u, OWL.unionOf, _rdf_list(parts)))
    return u

def numeric_union():
    """xsd:decimal union xsd:double, for use as a property range."""
    u = BNode(); g.add((u, RDF.type, RDFS.Datatype))
    g.add((u, OWL.unionOf, _rdf_list(list(NUMERIC_TYPES))))
    return u

# doseGy accepts either numeric serialization (see dose_range docstring)
g.add((C("doseGy"), RDFS.range, numeric_union()))

def has_value(prop, ind):
    r = BNode(); g.add((r, RDF.type, OWL.Restriction))
    g.add((r, OWL.onProperty, C(prop))); g.add((r, OWL.hasValue, ind))
    return r

def some_data(prop, drange):
    r = BNode(); g.add((r, RDF.type, OWL.Restriction))
    g.add((r, OWL.onProperty, C(prop))); g.add((r, OWL.someValuesFrom, drange))
    return r

def defined_intersection(name, members):
    g.add((C(name), RDF.type, OWL.Class))
    eq = BNode(); g.add((C(name), OWL.equivalentClass, eq))
    g.add((eq, RDF.type, OWL.Class))
    g.add((eq, OWL.intersectionOf, _rdf_list(members)))

# --- per-taxon window classes; the reasoner infers the generic position ---
def taxon_windows(w):
    """The windows of one taxon: (name, data range, generic parents). The windows of a taxon
    partition the doses its statistics speak to; with an LD50 lower bound, doses at or above the
    bound are left unclassified."""
    band, ld50, kind = w["band"], w["ld50"], w["ld50_kind"]
    assert band is not None or ld50 is not None, w["taxon"]
    below_ld50 = ["BelowReportedLD50"] if ld50 is not None else []
    out = []
    if band is not None:
        lo, hi = band
        assert 0 < lo < hi and (ld50 is None or hi < ld50), w["taxon"]
        out.append(("BelowFavourableBand", dose_range(0.0, lo, hi_exclusive=True),
                    ["BelowReportedFavourableBand"] + below_ld50))
        out.append(("WithinFavourableBand", dose_range(lo, hi, lo_exclusive=False, hi_exclusive=False),
                    ["WithinReportedFavourableBand"] + below_ld50))
        out.append(("AboveFavourableBand",
                    dose_range(hi, ld50 if kind == "estimate" else None, hi_exclusive=True),
                    ["AboveReportedFavourableBand"] + below_ld50))
    else:
        out.append(("BelowLD50", dose_range(0.0, ld50, hi_exclusive=True), ["BelowReportedLD50"]))
    if ld50 is not None and kind == "estimate":
        out.append(("AtOrAboveLD50", dose_range(ld50, None, lo_exclusive=False),
                    ["AtOrAboveReportedLD50"] + (["AboveReportedFavourableBand"] if band else [])))
    return out


for w in TAXON_WINDOWS:
    label = w["taxon"]
    slug = label.replace(" ", "_").replace("-", "_")
    ind = NS["taxon_" + slug]
    g.add((ind, RDF.type, OWL.NamedIndividual))
    g.add((ind, RDF.type, URIRef(NCBI + w["ncbi"])))      # typed with the NCBITaxon class
    g.add((ind, RDFS.label, Literal(label)))
    for cat, rng, parents in taxon_windows(w):
        cname = f"{slug}_{cat}Dose"
        defined_intersection(cname, [C("DoseAssessment"), has_value("forTaxon", ind),
                                     some_data("doseGy", rng)])
        for parent in parents:
            g.add((C(cname), RDFS.subClassOf, C(parent)))
        g.add((C(cname), RDFS.comment, Literal(
            f"Dose window for {label}, bounded by the statistics its source reports.")))
        g.add((C(cname), DCT.source, Literal(w["source"])))
        g.add((C(cname), C("boundQualifier"), Literal(w["qualifier"])))
        g.add((C(cname), SKOS.scopeNote, Literal(
            f"The source irradiated doses from {w['tested'][0]:g} to {w['tested'][1]:g} Gy; where "
            f"the window extends past them, the position is arithmetic only.")))

# --- a dose position is compatible with a response type ---
# The relation is a non-entailing annotation: the reported statistics bound a dose axis, and the
# response for a given endpoint and stage needs evidence of its own. Only the favourable band is
# linked, because only a favourable band reports a response.
g.add((C("consistentWithResponse"), RDF.type, OWL.AnnotationProperty))
g.add((C("consistentWithResponse"), RDFS.comment, Literal(
    "Relates a dose-position class to the response type its sources report within that position.")))
g.add((C("WithinReportedFavourableBand"), C("consistentWithResponse"), C("HormeticResponse")))

# ---- remove declared-but-unused terms ----
# expectedResponse is left over from a design in which a dose category implied a response.
# doseLowerGy and doseUpperGy duplicate the bounds that the datatype facets of the windows carry.
# BeneficialDoseRange, MutagenicDoseRange and SterilizationDoseRange carry a subClassOf DoseRange and
# a disjointness axiom, with no restriction, no instance and no role in any inference.
for _dead in ("expectedResponse", "doseLowerGy", "doseUpperGy",
              "BeneficialDoseRange", "MutagenicDoseRange", "SterilizationDoseRange"):
    for _t in list(g.triples((C(_dead), None, None))):
        g.remove(_t)
    for _t in list(g.triples((None, None, C(_dead)))):
        g.remove(_t)
    for _t in list(g.triples((None, C(_dead), None))):
        g.remove(_t)

# ---- labels: one convention for every term ----
# Every OnSIR class and property gets an English label in lower case, words separated by spaces,
# with British spelling, acronyms (LD50, ROS, UV) and taxon binomials kept as written. The scaffold's
# labels mixed camel case, title case and lower case, so all are rewritten from the local name.
import re as _re
LABELS = {
    "Am241": "americium-241", "Co60": "cobalt-60", "Cs137": "caesium-137", "Ir192": "iridium-192",
    "Xe133": "xenon-133", "UV_A": "UV-A", "UV_B": "UV-B", "UV_C": "UV-C", "XRay": "X-ray",
    "Isotope": "radioisotope", "BrainCousensModel": "Brain\u2013Cousens model",
    "DoseResponseModel": "dose\u2013response model", "DoseRateCategory": "dose-rate category",
    "HighDoseRate": "high dose rate", "LowDoseRate": "low dose rate", "LifecycleStage": "life-cycle stage",
    "hasDose": "has absorbed dose", "hasDoseRateCategory": "has dose-rate category",
    "doseGy": "dose in gray", "maxDose": "maximum dose", "minDose": "minimum dose",
    "bc_b": "Brain\u2013Cousens parameter b", "bc_c": "Brain\u2013Cousens parameter c",
    "bc_d": "Brain\u2013Cousens parameter d", "bc_e": "Brain\u2013Cousens parameter e",
    "bc_f": "Brain\u2013Cousens parameter f",
}
ACRONYMS = {"ld50": "LD50", "ros": "ROS", "uv": "UV"}
BRITISH = {"vigor": "vigour", "favorable": "favourable"}
TAXON_SLUGS = {w["taxon"].replace(" ", "_").replace("-", "_"): w["taxon"] for w in TAXON_WINDOWS}


def _label(local):
    if local in LABELS:
        return LABELS[local]
    head = ""
    for slug, binomial in TAXON_SLUGS.items():
        if local.startswith(slug + "_"):
            head, local = binomial + " ", local[len(slug) + 1:]
    t = local.replace("_", " ")
    t = _re.sub(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", " ", t)
    words = [ACRONYMS.get(w.lower(), BRITISH.get(w.lower(), w.lower())) for w in t.split()]
    return head + " ".join(words)


_relabelled = 0
for _t in (OWL.Class, OWL.ObjectProperty, OWL.DatatypeProperty, OWL.AnnotationProperty):
    for _x in sorted(set(g.subjects(RDF.type, _t))):
        if not isinstance(_x, URIRef) or not str(_x).startswith(str(NS)):
            continue
        for _old in list(g.triples((_x, RDFS.label, None))):
            g.remove(_old)
        g.add((_x, RDFS.label, Literal(_label(str(_x)[len(str(NS)):]), lang="en")))
        _relabelled += 1
print(f"  labels written: {_relabelled}")


# ---- the scaffold's illustrative individuals move to their own file ----
# OnSIR_base.owl carries ten worked individuals (three outcomes, their treatments and responses, and a
# Brain-Cousens model). Their numbers (a 50 Gy Co-60 treatment coded as a hormetic dose, Brain-Cousens
# parameters, response magnitudes, a 150 Gy X-ray treatment, a 1200 J m-2 UV-C treatment) come from
# no study. The core ships none of them; OnSIR_examples imports the core and carries them with a
# header that states the values are invented for illustration.
EXAMPLES = ["Model_BC_Germination", "Outcome_Co60_GerminationHormesis", "Outcome_UVC_Sterilization",
            "Outcome_XRay_Mutagenesis", "Resp_GerminationHormesis", "Resp_Mutagenesis", "Resp_Sterility",
            "Treat_Co60_Gamma_50Gy", "Treat_UVC_254nm_1200Jm2", "Treat_XRay_150Gy"]
eg = Graph()
for pfx, n in [("onsir", NS), ("dct", DCT), ("qudt", QUDT), ("owl", OWL), ("rdfs", RDFS)]:
    eg.bind(pfx, n)


def _move(node):
    for t in list(g.triples((node, None, None))):
        g.remove(t)
        eg.add(t)
        if isinstance(t[2], BNode):
            _move(t[2])


for _x in EXAMPLES:
    assert (C(_x), RDF.type, OWL.NamedIndividual) in g or any(g.triples((C(_x), RDF.type, None))), _x
    _move(C(_x))
# The scaffold wrote quantities as qudt:QuantityValue with qudt:numericValue, while the ABox and the
# axioms use onsir:QuantityValue and onsir:numericValue; the examples follow the ABox.
for _s, _p, _o in list(eg):
    if _p == QUDT.numericValue:
        eg.remove((_s, _p, _o)); eg.add((_s, C("numericValue"), Literal(float(_o), datatype=XSD.double)))
    if _p == RDF.type and _o == QUDT.QuantityValue:
        eg.remove((_s, _p, _o)); eg.add((_s, RDF.type, C("QuantityValue")))
# The scaffold used the class PlantSeed itself as the subject of each outcome; each outcome now has a
# seed individual of its own.
for _o in [C(x) for x in EXAMPLES if x.startswith("Outcome_")]:
    if (_o, C("hasSubject"), C("PlantSeed")) in eg:
        eg.remove((_o, C("hasSubject"), C("PlantSeed")))
        _seed = NS["example_seed_" + str(_o)[len(str(NS)) + len("Outcome_"):]]
        eg.add((_seed, RDF.type, OWL.NamedIndividual)); eg.add((_seed, RDF.type, C("PlantSeed")))
        eg.add((_o, C("hasSubject"), _seed))
# A treatment has exactly one dose. For the UV-C example that dose is its fluence, the radiant
# exposure in J m-2 by which ultraviolet treatments are dosed.
_uv = C("Treat_UVC_254nm_1200Jm2")
eg.add((_uv, C("hasDose"), eg.value(_uv, C("hasFluence"))))
# The scaffold named classes where individuals belong: hasDoseCategory onsir:HormeticDose and
# forEndpoint onsir:GerminationRate. A class IRI in that position is a punned individual with no type,
# so the dose-to-effect inclusion never fires. Each outcome gets a dose-category individual and an
# endpoint individual typed with those classes.
for _p, _prefix in (("hasDoseCategory", "example_dose_"), ("forEndpoint", "example_endpoint_")):
    for _o, _cls in list(eg.subject_objects(C(_p))):
        if str(_cls).startswith(str(NS)) and (_cls, RDF.type, OWL.NamedIndividual) not in eg:
            _ind = NS[_prefix + str(_o)[len(str(NS)) + len("Outcome_"):]]
            eg.remove((_o, C(_p), _cls))
            eg.add((_ind, RDF.type, _cls)); eg.add((_o, C(_p), _ind))
# One outcome is left without an asserted response, so the file shows the inference: HermiT
# classifies Outcome_XRay_Mutagenesis as a MutagenicOutcome from its typed dose category alone.
eg.remove((C("Outcome_XRay_Mutagenesis"), C("hasResponse"), C("Resp_Mutagenesis")))
for _t in list(eg.triples((C("Resp_Mutagenesis"), None, None))):
    eg.remove(_t)
EXAMPLES_ONT = URIRef("https://w3id.org/onsir/examples")
eg.add((EXAMPLES_ONT, RDF.type, OWL.Ontology))
eg.add((EXAMPLES_ONT, OWL.imports, ONT))
eg.add((EXAMPLES_ONT, OWL.versionInfo, Literal(VERSION)))
eg.add((EXAMPLES_ONT, DCT.license, URIRef("https://creativecommons.org/licenses/by/4.0/")))
eg.add((EXAMPLES_ONT, RDFS.comment, Literal(
    "Illustrative individuals showing how a treatment, its outcome, its response and a dose-response "
    "model are modelled in OnSIR. Every numeric value in this file is invented for illustration and "
    "is taken from no study. Outcome_XRay_Mutagenesis carries a dose category and no response, and "
    "a reasoner classifies it as a MutagenicOutcome.")))
for _x in sorted(set(eg.subjects(RDF.type, None))):
    if isinstance(_x, URIRef) and str(_x).startswith(str(NS)) and _x != EXAMPLES_ONT:
        eg.add((_x, RDF.type, OWL.NamedIndividual))
        eg.add((_x, RDFS.comment, Literal("Illustrative individual; its values are invented.")))

# ---- stub declarations for the external classes used in logical positions ----
# OWL 2 DL requires every IRI in a logical position to be declared somewhere in the imports closure.
# OnSIR does not import BFO, PO, ChEBI, PATO, ENVO or NCBITaxon (NCBITaxon alone would add millions
# of axioms), so each external target of an alignment axiom gets a MIREOT-style stub: the IRI is
# declared owl:Class and nothing else is asserted about it. Built-in vocabulary is excluded, and so
# is XML Schema: xsd:double is the range of numericValue, a datatype, and declaring it a class takes
# the file out of the profile.
BUILTIN = (str(OWL), str(RDFS), str(RDF), str(XSD))
# Annotation properties from Dublin Core and SKOS are used on the ontology header and on terms;
# OWL 2 DL requires each to be declared.
ANNOTATION_NS = (str(DCT), str(SKOS))


def declare(graph):
    logical = (RDFS.subClassOf, OWL.equivalentClass, OWL.someValuesFrom, OWL.allValuesFrom,
               OWL.onClass, OWL.complementOf, RDFS.domain, RDFS.range)
    declared = set()
    for t in (OWL.Class, OWL.ObjectProperty, OWL.DatatypeProperty, OWL.AnnotationProperty,
              OWL.NamedIndividual, RDFS.Datatype):
        declared |= set(graph.subjects(RDF.type, t))
    ext = set()
    for s_, p_, o_ in graph:
        if p_ in logical:
            terms = (s_, o_)
        elif p_ == RDF.type:
            terms = (o_,)
        else:
            terms = ()
        for term in terms:
            if (isinstance(term, URIRef) and term not in declared and not str(term).startswith(str(NS))
                    and not str(term).startswith(BUILTIN)):
                ext.add(term)
    for e in sorted(ext):
        graph.add((e, RDF.type, OWL.Class))
    ann = sorted({p_ for p_ in graph.predicates() if str(p_).startswith(ANNOTATION_NS)})
    for a_ in ann:
        graph.add((a_, RDF.type, OWL.AnnotationProperty))
    return len(ext), len(ann)


_n_ext, _n_ann = declare(g)
print(f"  external stub declarations emitted: {_n_ext}; annotation properties declared: {_n_ann}")
declare(eg)

# ---- every individual is declared owl:NamedIndividual ----
# OWL API tools list an individual from its class assertion as well, so the declaration is a
# convenience for tools that read declarations only; the build emits it for every individual.
_named_cls = {c for c in g.subjects(RDF.type, OWL.Class)
              if isinstance(c, URIRef) and str(c).startswith(str(NS))}
_indiv = {s for s, _p, o in g.triples((None, RDF.type, None))
          if isinstance(s, URIRef) and str(s).startswith(str(NS)) and o in _named_cls}
_added_ni = 0
for _i in sorted(_indiv):
    if (_i, RDF.type, OWL.NamedIndividual) not in g:
        g.add((_i, RDF.type, OWL.NamedIndividual)); _added_ni += 1
print(f"  owl:NamedIndividual declarations added: {_added_ni} "
      f"(individuals in the core file: {len(set(g.subjects(RDF.type, OWL.NamedIndividual)))})")

eg.serialize("OnSIR_examples.ttl", format="turtle")
eg.serialize("OnSIR_examples.owl", format="xml")
g.serialize("OnSIR.ttl", format="turtle")
g.serialize("OnSIR.owl", format="xml")

# ---- report ----
from rdflib import RDF as R
print("OnSIR ontology built.")
print("  triples:", len(g))
# count NAMED classes in the OnSIR namespace only: counting all owl:Class subjects also counts
# anonymous class expressions, which would inflate the reported class count.
print("  classes (named, onsir namespace):",
      len([c for c in set(g.subjects(R.type, OWL.Class))
           if isinstance(c, URIRef) and str(c).startswith(str(NS))]))
print("  object properties:", len(set(g.subjects(R.type, OWL.ObjectProperty))))
print("  restrictions:", len(set(g.subjects(R.type, OWL.Restriction))))
print("  AllDisjointClasses:", len(set(g.subjects(R.type, OWL.AllDisjointClasses))))
print("  equivalentClass:", len(list(g.triples((None, OWL.equivalentClass, None)))))
print("  external alignments (obo/*):",
      len([o for o in g.objects(None, None) if str(o).startswith(str(OBO))]))
print("  functional properties:", len(set(g.subjects(R.type, OWL.FunctionalProperty))))
