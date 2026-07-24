# -*- coding: utf-8 -*-
r"""Build the OnSIR ontology: take the class scaffold (OnSIR_base.owl) and assemble the full
OWL 2 DL ontology -- persistent IRIs, metadata, disjointness partitions, existential and
cardinality restrictions, dose->effect GCIs and defined classes, object properties for radiation
type / isotope, functional and inverse properties, covering axioms, SKOS definitions, and VERIFIED
external alignments (BFO, PO, NCBITaxon, ChEBI, UO, PATO). Outputs OnSIR.ttl / OnSIR.owl.
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
g.add((ONT, URIRef(str(OWL) + "versionIRI"), URIRef("https://w3id.org/onsir/1.0.0")))
g.add((ONT, OWL.versionInfo, Literal("1.0.0")))
g.add((ONT, DCT.title, Literal("OnSIR: Ontology for Seed Irradiation and Plant Radiobiology")))
g.add((ONT, DCT.description, Literal(
    "A FAIR OWL 2 DL ontology of seed-irradiation treatments and their dose-dependent "
    "biological effects (hormetic, mutagenic, sterilizing), aligned to BFO, PO, NCBITaxon, "
    "ChEBI, UO and PATO, with dose-to-effect axioms supporting DL reasoning.")))
for name, orcid in [("Luis Felipe Medeiro Alves", "0009-0005-4227-5568"),
                    ("Ferrucio de Franco Rosa", None),
                    ("Valter Arthur", "0000-0003-3521-9136")]:
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

# ---- (5) functional / characteristics ----
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
for q in ["Endpoint", "Response"]:
    align(q, str(OBO)+"BFO_0000019")                        # quality
# PO
align("PlantSeed", str(OBO)+"PO_0009010", OWL.equivalentClass)   # seed
align("Seedling", str(OBO)+"PO_0008037", OWL.equivalentClass)    # seedling
align("GerminationStage", str(OBO)+"PO_0007057", SKOS.closeMatch)  # (germination-related stage)
# ChEBI isotopes (verified: Cs-137)
align("Cs137", str(OBO)+"CHEBI_196959", OWL.equivalentClass)
align("Co60", str(OBO)+"CHEBI_749374", SKOS.closeMatch)     # closeMatch (compound, not pure nuclide)
# UO dose unit
g.add((C("QuantityValue"), RDFS.comment, Literal("dose values use unit gray (UO_0000134)")))
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
g.add((C("QuantityValue"), RDFS.comment, Literal("dose rate values use gray per minute (UO_0010060)")))

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

g.serialize("OnSIR.ttl", format="turtle")
g.serialize("OnSIR.owl", format="xml")

# ---- report ----
from rdflib import RDF as R
print("OnSIR ontology built.")
print("  triples:", len(g))
print("  classes:", len(set(g.subjects(R.type, OWL.Class))))
print("  object properties:", len(set(g.subjects(R.type, OWL.ObjectProperty))))
print("  restrictions:", len(set(g.subjects(R.type, OWL.Restriction))))
print("  AllDisjointClasses:", len(set(g.subjects(R.type, OWL.AllDisjointClasses))))
print("  equivalentClass:", len(list(g.triples((None, OWL.equivalentClass, None)))))
print("  external alignments (obo/*):",
      len([o for o in g.objects(None, None) if str(o).startswith(str(OBO))]))
print("  functional properties:", len(set(g.subjects(R.type, OWL.FunctionalProperty))))
