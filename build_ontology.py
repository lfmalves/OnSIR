# -*- coding: utf-8 -*-
r"""Build the OnSIR ontology: take the class scaffold (OnSIR_base.owl) and assemble the full
OWL 2 DL ontology -- persistent IRIs, metadata, disjointness partitions, existential and
cardinality restrictions, dose->effect GCIs and defined classes, object properties for radiation
type / isotope, functional and inverse properties, covering axioms, SKOS definitions, and VERIFIED
external alignments (BFO, PO, NCBITaxon, ChEBI, PATO, ENVO; units via QUDT).
Outputs OnSIR.ttl / OnSIR.owl.
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
g.add((ONT, URIRef(str(OWL) + "versionIRI"), URIRef("https://w3id.org/onsir/1.3.0")))
g.add((ONT, OWL.versionInfo, Literal("1.3.0")))
g.add((ONT, DCT.title, Literal("OnSIR: Ontology for Seed Irradiation and Plant Radiobiology")))
g.add((ONT, DCT.description, Literal(
    "A FAIR OWL 2 DL ontology of seed-irradiation treatments and their dose-dependent "
    "biological effects, aligned to BFO, PO, NCBITaxon, ChEBI, PATO and ENVO with verified IRIs "
    "and to QUDT for units, with dose-to-effect axioms supporting DL reasoning.")))
for name, orcid in [("Luis Felipe Medeiro Alves", "0009-0005-4227-5568"),
                    ("Ferrucio de Franco Rosa", None),
                    ("Valter Arthur", "0000-0003-3521-9136")]:
    if orcid:
        # emit the ORCID as a resolvable agent IRI, not only as a name string
        who = URIRef("https://orcid.org/" + orcid)
        g.add((ONT, DCT.creator, who))
        g.add((who, RDF.type, URIRef("http://xmlns.com/foaf/0.1/Person")))
        g.add((who, RDFS.label, Literal(name)))
    else:
        g.add((ONT, DCT.creator, Literal(name)))
g.add((ONT, DCT.license, URIRef("https://creativecommons.org/licenses/by/4.0/")))
g.add((ONT, DCT.created, Literal("2025-09-21", datatype=XSD.date)))
g.add((ONT, DCT.modified, Literal("2026-07-24", datatype=XSD.date)))
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
all_disjoint(["BeneficialDoseRange", "MutagenicDoseRange", "SterilizationDoseRange"])
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
    # ...and where they are USED as predicates on the carried-over exemplar instances. Removing
    # only the declaration left `Treat_... radiationType "gamma"` in the release, which is exactly
    # the free-text modelling the paper says it eliminates.
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
# They are drafting notes, not content, and do not belong in a release.
_removed = 0
for _s, _p, _o in list(g.triples((None, RDFS.comment, None))):
    if "Integration touchpoint" in str(_o):
        g.remove((_s, _p, _o)); _removed += 1
print(f"  removed {_removed} editorial note(s) carried over from the source skeleton")

# ---- deprecate the dose classes that name a biological outcome ----
# Section 5 argues that a class called "HormeticDose" reifies a context-dependent empirical outcome
# as an intrinsic property of a dose. Keeping such classes while arguing against them is
# indefensible; deleting them would break any user of an earlier release. We deprecate them the OBO
# way: the IRI survives, is marked obsolete, and points at the evidence-relative replacement.
LEGACY = {
    "HormeticDose": "AtOrBelowReportedOptimum",
    "MutagenicDose": "AboveReportedOptimum",
    "SterilizationDose": "AtOrAboveReportedLD50",
}
for _old, _new in LEGACY.items():
    g.add((C(_old), OWL.deprecated, Literal(True)))
    g.add((C(_old), RDFS.comment, Literal(
        "DEPRECATED. This class names a biological outcome as if it were a property of the dose, "
        "which is context-dependent: the same absorbed dose falls in different windows for "
        "different taxa. Use " + _new + ", which records where a dose falls relative to the values "
        "reported for a given taxon and asserts nothing about the outcome.")))
    g.add((C(_old), URIRef("http://purl.obolibrary.org/obo/IAO_0100001"), C(_new)))

# ---- (5) declarations that the class expressions above depend on ----
# QuantityValue appears in four class expressions (dose and dose-bound restrictions) and was never
# declared, while qudt:QuantityValue was declared and used as the range of the same properties. An
# undeclared IRI in a logical position is not legal OWL 2 DL, so declare it and state the identity.
g.add((C("QuantityValue"), RDF.type, OWL.Class))
g.add((C("QuantityValue"), RDFS.label, Literal("Quantity value", lang="en")))
g.add((C("QuantityValue"), OWL.equivalentClass, QUDT.QuantityValue))
g.add((QUDT.QuantityValue, RDF.type, OWL.Class))
# numericValue was typed only as FunctionalProperty -- a characteristic with no property declaration.
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
# BFO placement. A Response is something that HAPPENS -- it unfolds in time -- so it is a process,
# not a quality. An Endpoint is the measurable characteristic being scored, which is a quality.
# Asserting both as qualities (an earlier build did) is a category error a BFO-aware referee catches.
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
# Co60 to CHEBI_749374 "cobaltous chloride co 60", reached through that class's "60co" synonym --
# a labelled compound, not the source nuclide. The honest target is the element, as a BROADER term.
align("Co60", str(OBO)+"CHEBI_27638", SKOS.broadMatch)      # cobalt atom (no Co-60 nuclide in ChEBI)
# dose units, as typed QUDT links on the quantity restrictions
g.add((C("QuantityValue"), RDFS.comment, Literal(
    "dose values carry a typed qudt:unit link; absorbed dose is in gray")))
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
    "dose rate values carry a typed qudt:unit link; the unit asserted is gray per hour")))

# ---- (11) SKOS definitions for core classes ----
DEFS = {
 "SeedIrradiationTreatment": "A treatment process in which seeds are exposed to ionizing radiation of a specified type, source, dose and dose rate.",
 "TreatmentOutcome": "The observed result of a seed-irradiation treatment on a subject seed under a context, characterized by a dose category and a biological response for a given endpoint.",
 "HormeticDose": "A dose in the range that elicits a stimulatory (hormetic) biological response.",
 "MutagenicDose": "A dose in the range that elicits induced genetic variability (mutagenesis) without predominant sterilization.",
 "SterilizationDose": "A dose high enough to cause predominant loss of viability or reproductive capacity.",
 "HormeticResponse": "A beneficial, stimulatory response to low-dose irradiation (e.g., enhanced germination, vigour, or stress resistance).",
 "DoseCategory": "A qualitative classification of an irradiation dose by its predominant biological effect.",
 "QuantityValue": "A measured quantity with a numeric value and a unit (dose in gray, dose rate in gray per minute).",
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
# A dose is not hormetic in itself: 10 Gy stimulates tobacco but is far below the
# stimulatory range of cowpea or fenugreek. We therefore reify the classification as a
# DoseAssessment (a numeric dose applied to a taxon for an endpoint) and give each taxon its
# own dose windows using OWL 2 datatype facets, so that a reasoner DERIVES the dose category
# from the numeric value together with the taxon, instead of it being asserted.
#
# Window convention, using only literature-reported bounds per taxon:
#   stimulatory  : 0 < dose <= D*_upper      (reported stimulation optimum, upper value)
#   mutagenic    : D*_upper < dose < LD50    (between optimum and early-viability LD50)
#   sterilizing  : dose >= LD50
# These are operational, provenanced bounds, not universal thresholds.
# ============================================================================
NCBI = "http://purl.obolibrary.org/obo/NCBITaxon_"

# (taxon label, NCBITaxon id [OLS-verified], D*_upper Gy, LD50 Gy, provenance)
TAXON_WINDOWS = [
    ("Nicotiana tabacum",        "4097",  15.0,  25.0, "Alves & Arthur 2025, TSF J. Biol. 3(2):26-51"),
    ("Vigna unguiculata",        "3917",  80.0, 132.0, "Gnankambary et al. 2019, Int. J. Genet. Mol. Biol. 11(2):29-33"),
    ("Trigonella foenum-graecum","78534", 150.0, 350.0, "Latha et al. 2017, J. AgriSearch 4(1):28-33"),
    ("Capsicum annuum",          "4072",  50.0, 200.0, "Esmaiel et al. 2025, J. Agric. Biol. Res. 11(1):44-55"),
]

# --- classes and properties for the assessment context ---
# NOTE ON NAMING. The reported statistics are a stimulation OPTIMUM and an early-viability LD50.
# Neither licenses a biological category name: the optimum is where stimulation is maximal, not
# where it ends, so doses just above it may still be stimulatory; and an LD50 is 50% lethality
# under some endpoint and time definition, which is NOT sterility -- a population at its LD50 may
# retain substantial reproductive capacity. We therefore name these classes by the dose's POSITION
# RELATIVE TO THE REPORTED STATISTICS, which is exactly what the evidence supports, and keep the
# biological response classes separate.
for cls, com in [("DoseAssessment",
                  "A numeric absorbed dose considered for a given taxon, endpoint and stage; the "
                  "unit of context-dependent dose positioning."),
                 ("AtOrBelowReportedOptimum",
                  "A DoseAssessment whose dose is at or below the stimulation optimum reported for "
                  "its taxon. Being at or below the reported optimum is evidence consistent with a "
                  "stimulatory response; it does not entail one, and stimulation may also occur "
                  "above the optimum."),
                 ("AboveReportedOptimum",
                  "A DoseAssessment whose dose exceeds the reported stimulation optimum but is "
                  "below the reported early-viability LD50. This is not by itself evidence of "
                  "mutagenesis: mutation induction may begin below the optimum and continue above "
                  "the LD50, and depends on the endpoint."),
                 ("AtOrAboveReportedLD50",
                  "A DoseAssessment whose dose reaches or exceeds the early-viability LD50 reported "
                  "for its taxon. LD50 is a 50% lethality statistic, NOT a sterilization threshold; "
                  "inferring sterility requires reproductive evidence, which this class does not "
                  "assert.")]:
    g.add((C(cls), RDF.type, OWL.Class)); g.add((C(cls), SKOS.definition, Literal(com)))
for sub in ["AtOrBelowReportedOptimum", "AboveReportedOptimum", "AtOrAboveReportedLD50"]:
    g.add((C(sub), RDFS.subClassOf, C("DoseAssessment")))
# These three are disjoint as ARITHMETIC intervals of the dose axis -- a fact about the numbers,
# not a biological claim about incompatible responses.
all_disjoint(["AtOrBelowReportedOptimum", "AboveReportedOptimum", "AtOrAboveReportedLD50"])

g.add((C("forTaxon"), RDF.type, OWL.ObjectProperty))
g.add((C("forTaxon"), RDFS.domain, C("DoseAssessment")))
g.add((C("forTaxon"), RDFS.comment, Literal("the taxon the assessment is relative to")))
g.add((C("forEndpoint"), RDF.type, OWL.ObjectProperty))
g.add((C("forEndpoint"), RDFS.domain, C("DoseAssessment")))
g.add((C("forEndpoint"), RDFS.range, C("Endpoint")))
# ---- endpoint categories (the review corpus's EP axis) ----
# The coded corpus records endpoints at a coarser granularity than OnSIR's Endpoint classes: six
# categories, not thirteen measurements. Asserting e.g. SeedlingVigorIndex from the code "EP1"
# would invent a measurement that the source does not report, so the axis is represented
# separately and left unrelated to the fine-grained Endpoint tree.
g.add((C("EndpointCategory"), RDF.type, OWL.Class))
g.add((C("EndpointCategory"), SKOS.definition, Literal(
    "A coarse grouping of measured endpoints, as recorded by a systematic review's coding scheme. "
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
# a seed HAS a taxon; it is not a subclass of one
g.add((C("hasTaxon"), RDF.type, OWL.ObjectProperty))
g.add((C("hasTaxon"), RDFS.domain, C("PlantSeed")))
g.add((C("hasTaxon"), RDFS.comment, Literal(
    "relates a plant structure to its taxon; taxonomic identity is not an anatomical type, so "
    "PlantSeed is never asserted to be a subclass of an NCBITaxon class")))
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

# --- per-taxon window classes; the reasoner infers the generic category ---
for label, tid, dstar_hi, ld50, prov in TAXON_WINDOWS:
    slug = label.replace(" ", "_").replace("-", "_")
    ind = NS["taxon_" + slug]
    g.add((ind, RDF.type, OWL.NamedIndividual))
    g.add((ind, RDF.type, URIRef(NCBI + tid)))        # typed with the NCBITaxon class
    g.add((ind, RDFS.label, Literal(label)))
    for cat, rng, parent in [
        ("AtOrBelowOptimum", dose_range(0.0, dstar_hi), "AtOrBelowReportedOptimum"),
        ("AboveOptimum",     dose_range(dstar_hi, ld50, lo_exclusive=True, hi_exclusive=True),
         "AboveReportedOptimum"),
        ("AtOrAboveLD50",    dose_range(ld50, None, lo_exclusive=False), "AtOrAboveReportedLD50"),
    ]:
        cname = f"{slug}_{cat}Dose"
        defined_intersection(cname, [C("DoseAssessment"), has_value("forTaxon", ind),
                                     some_data("doseGy", rng)])
        g.add((C(cname), RDFS.subClassOf, C(parent)))
        g.add((C(cname), RDFS.comment, Literal(
            f"dose interval '{cat}' for {label}, relative to the reported statistics; "
            f"bounds from {prov}")))
        g.add((C(cname), DCT.source, Literal(prov)))

# --- dose position is CONSISTENT WITH a response; it does not entail one ---
# An earlier version made the dose interval a subclass of "has expected response R", i.e. it
# ENTAILED the biology from the arithmetic. That is stronger than the evidence: the reported
# statistics bound a dose axis, they do not determine the response for an arbitrary endpoint and
# stage. We therefore record the relation as a non-entailing annotation.
g.add((C("consistentWithResponse"), RDF.type, OWL.AnnotationProperty))
g.add((C("consistentWithResponse"), RDFS.comment, Literal(
    "Relates a dose-position class to the response type it is evidentially compatible with. This is "
    "an annotation, deliberately NOT a subclass axiom: no biological response is entailed by the "
    "position of a dose relative to a reported statistic.")))
for acls, resp in [("AtOrBelowReportedOptimum", "HormeticResponse"),
                   ("AboveReportedOptimum", "MutagenicResponse"),
                   ("AtOrAboveReportedLD50", "SterilizationResponse")]:
    g.add((C(acls), C("consistentWithResponse"), C(resp)))

# ---- remove declared-but-unused terms ----
# expectedResponse is a leftover from the pre-correction design, in which a dose category implied a
# response. doseLowerGy and doseUpperGy were an alternative to expressing bounds as datatype facets;
# the facets are what the ontology actually uses, and the manuscript's contribution rests on them.
# A term declared and never used is dead weight that a reader has to rule out.
for _dead in ("expectedResponse", "doseLowerGy", "doseUpperGy"):
    for _t in list(g.triples((C(_dead), None, None))):
        g.remove(_t)
    for _t in list(g.triples((None, None, C(_dead)))):
        g.remove(_t)
    for _t in list(g.triples((None, C(_dead), None))):
        g.remove(_t)

# ---- every named class must carry a label: OBO practice, and the generated documentation renders
# ---- bare IRIs without one. Derive from the local name where no explicit label was set.
import re as _re
def _human(local):
    t = _re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", local.replace("_", " "))
    t = _re.sub(r"\s+", " ", t).strip()
    # keep established acronyms and binomials readable
    for a, b in [("Ld50", "LD50"), ("L D50", "LD50"), ("Ros", "ROS"), ("Uv", "UV"),
                 ("Xray", "X-ray"), ("X Ray", "X-ray")]:
        t = t.replace(a, b)
    return t[:1].upper() + t[1:]

_missing = 0
for _c in sorted(set(g.subjects(RDF.type, OWL.Class))):
    if not isinstance(_c, URIRef) or not str(_c).startswith(str(NS)):
        continue
    if g.value(_c, RDFS.label) is None:
        g.add((_c, RDFS.label, Literal(_human(str(_c)[len(str(NS)):]), lang="en")))
        _missing += 1
for _p in sorted(set(g.subjects(RDF.type, OWL.ObjectProperty))
                 | set(g.subjects(RDF.type, OWL.DatatypeProperty))):
    if not isinstance(_p, URIRef) or not str(_p).startswith(str(NS)):
        continue
    if g.value(_p, RDFS.label) is None:
        g.add((_p, RDFS.label, Literal(_human(str(_p)[len(str(NS)):]), lang="en")))
        _missing += 1
print(f"  labels added where missing: {_missing}")


g.serialize("OnSIR.ttl", format="turtle")
g.serialize("OnSIR.owl", format="xml")

# ---- report ----
from rdflib import RDF as R
print("OnSIR ontology built.")
print("  triples:", len(g))
# count NAMED classes in the OnSIR namespace only: counting all owl:Class subjects also counts
# anonymous class expressions, which is how an inflated class count got into an earlier draft.
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
