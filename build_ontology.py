# -*- coding: utf-8 -*-
r"""Build the OnSIR ontology: take the class scaffold (OnSIR_base.owl) and assemble the full
OWL 2 DL ontology: persistent IRIs, metadata, disjointness partitions, existential and
cardinality restrictions, dose->effect GCIs and defined classes, object properties for radiation
type and isotope, functional and inverse properties, a covering axiom on the dose categories, a
definition (IAO:0000115) on every class and property, taxon dose windows conditioned on taxon,
endpoint and stage and written as datatype facets, probe classes that flag a favourable band
reaching an LD50 for one of its endpoints and stages, obsolete terms of earlier releases with their replacements, and external
alignments checked against OLS (BFO, IAO, OBI, RO, PO, NCBITaxon, ChEBI, GO, PATO, PECO, TO;
units via QUDT).

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
VANN = Namespace("http://purl.org/vocab/vann/")
OIO = Namespace("http://www.geneontology.org/formats/oboInOwl#")
DEF = OBO.IAO_0000115            # definition
DEF_SRC = OBO.IAO_0000119        # definition source
REPLACED_BY = OBO.IAO_0100001    # term replaced by
IN_TAXON = OBO.RO_0002162        # in taxon

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
               ("qudt", QUDT), ("owl", OWL), ("rdfs", RDFS), ("vann", VANN), ("oboInOwl", OIO)]:
    g.bind(pfx, n)

# ---- ontology header + real metadata ----
g.add((ONT, RDF.type, OWL.Ontology))
# The release version. It appears in the versionIRI, the versionInfo, CITATION.cff and the README;
# verify_release.py asserts that they agree. The ABox and the examples carry versionIRIs of their own
# and import this versioned IRI.
VERSION = "1.7.0"
PRIOR = "1.6.0"
RELEASE_DATE = "2026-10-05"      # the date of this build; set to the publication date at release
VERSIONED = URIRef("https://w3id.org/onsir/" + VERSION)
g.add((ONT, URIRef(str(OWL) + "versionIRI"), VERSIONED))
g.add((ONT, OWL.versionInfo, Literal(VERSION)))
g.add((ONT, URIRef(str(OWL) + "priorVersion"), URIRef("https://w3id.org/onsir/" + PRIOR)))
g.add((ONT, DCT.title, Literal("OnSIR: Ontology for Seed Irradiation and Plant Radiobiology")))
g.add((ONT, DCT.description, Literal(
    "An OWL 2 DL ontology of seed-irradiation treatments and their dose-dependent biological "
    "effects, with dose-to-effect axioms and taxon dose windows, conditioned on endpoint and stage, "
    "for description-logic reasoning. Its classes are aligned, with IRIs checked against the EBI "
    "Ontology Lookup Service, to BFO, IAO, OBI, PO, NCBITaxon, ChEBI, GO, PATO, PECO and TO, taxa are "
    "stated with the RO relation in taxon, and its units are QUDT terms.")))
# Namespace, citation and publication metadata, as the FAIR assessment of ontologies reads them.
g.add((ONT, VANN.preferredNamespacePrefix, Literal("onsir")))
g.add((ONT, VANN.preferredNamespaceUri, Literal(BASE, datatype=XSD.anyURI)))
g.add((ONT, DCT.bibliographicCitation, Literal(
    f"Alves LFM, de Franco Rosa F, Arthur V. OnSIR: Ontology for Seed Irradiation and Plant "
    f"Radiobiology, version {VERSION}. https://w3id.org/onsir/{VERSION}")))
g.add((ONT, DCT.issued, Literal(RELEASE_DATE, datatype=XSD.date)))
# The release is published by its first author through the GitHub repository and the w3id
# namespace he registered.
g.add((ONT, DCT.publisher, URIRef("https://orcid.org/0009-0005-4227-5568")))
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
g.add((ONT, DCT.modified, Literal(RELEASE_DATE, datatype=XSD.date)))
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
# Five kinds of response, pairwise disjoint as kinds of process. They are not exhaustive: a response
# of another kind is a plain Response, and an outcome with no detected response has none.
for _r in ("InhibitoryResponse", "LossOfViability"):
    g.add((C(_r), RDF.type, OWL.Class))
    g.add((C(_r), RDFS.subClassOf, C("Response")))
all_disjoint(["HormeticResponse", "InhibitoryResponse", "LossOfViability", "MutagenicResponse",
              "SterilizationResponse"])
all_disjoint(["Gamma", "XRay", "Neutron", "Proton", "ElectronBeam", "UV_A", "UV_B", "UV_C"])
all_disjoint(["Am241", "Co60", "Cs137", "Ir192", "Xe133"])
# The dose-rate categories are named by their bound (see "dose-rate categories" below); the 1.6.0
# names LowDoseRate and HighDoseRate are obsolete.
for _c in ("DoseRateBelow100GyPerHour", "DoseRateAbove100GyPerHour"):
    g.add((C(_c), RDF.type, OWL.Class))
    g.add((C(_c), RDFS.subClassOf, C("DoseRateCategory")))
all_disjoint(["DoseRateBelow100GyPerHour", "DoseRateAbove100GyPerHour"])

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
# A treatment states its radiation type, and either one dose, a range of doses (a study that
# irradiated several), or, for ultraviolet light, a fluence. A treatment need not induce a response,
# and an outcome need not have one: a dose with no detectable effect is an outcome too.
some(C("SeedIrradiationTreatment"), "hasRadiationType", "RadiationType")
_dose_alt = BNode()
g.add((_dose_alt, RDF.type, OWL.Class))
_l = [some_node("hasDose", "QuantityValue"), some_node("hasDoseRange", "DoseRange"),
      some_node("hasFluence", "QuantityValue")]
_head = BNode(); _cur = _head
for _i, _it in enumerate(_l):
    g.add((_cur, RDF.first, _it))
    if _i < len(_l) - 1:
        _nxt = BNode(); g.add((_cur, RDF.rest, _nxt)); _cur = _nxt
    else:
        g.add((_cur, RDF.rest, RDF.nil))
g.add((_dose_alt, OWL.unionOf, _head))
g.add((C("SeedIrradiationTreatment"), RDFS.subClassOf, _dose_alt))
some(C("DoseRange"), "minDose", "QuantityValue")
some(C("DoseRange"), "maxDose", "QuantityValue")
some(C("TreatmentOutcome"), "hasTreatment", "SeedIrradiationTreatment")

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
    _kind = {"HormeticDose": "hormetic", "MutagenicDose": "mutagenic", "SterilizationDose": "sterilizing"}[_old]
    g.add((C(_old), DEF, Literal(
        f"A dose asserted by a curator to have a {_kind} effect. Discouraged for new annotation: the "
        "category names a biological outcome, and the outcome of one absorbed dose depends on taxon, "
        "endpoint and stage. Retained because data that already carries a dose category reasons "
        "through its axioms. Record the category as an individual typed with this class; the general "
        "class inclusion reads that typing. For new curation, record the numeric dose as a "
        "DoseAssessment with doseGy, hasSubject, forEndpoint and atStage.")))
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
# OBI and IAO. A seed-irradiation treatment is an OBI planned irradiation (OBI:0302889), and a dose
# assessment, a record that relates one dose to a plant structure, an endpoint and a stage, is an IAO
# information content entity (IAO:0000030).
align("SeedIrradiationTreatment", str(OBO)+"OBI_0302889")   # planned irradiation
g.add((C("DoseAssessment"), RDF.type, OWL.Class))
align("DoseAssessment", str(OBO)+"IAO_0000030")             # information content entity
# PO
align("PlantSeed", str(OBO)+"PO_0009010", OWL.equivalentClass)   # seed
align("Seedling", str(OBO)+"PO_0008037", OWL.equivalentClass)    # seedling
align("Plant", str(OBO)+"PO_0000003")                            # whole plant
align("LifecycleStage", str(OBO)+"PO_0009012")                   # plant structure development stage
align("GerminationStage", str(OBO)+"PO_0007057", SKOS.closeMatch)  # seed germination stage
align("EarlySeedlingStage", str(OBO)+"PO_0007131", SKOS.closeMatch)  # seedling development stage
g.add((C("FloweringStage"), RDF.type, OWL.Class))
g.add((C("FloweringStage"), RDFS.subClassOf, C("LifecycleStage")))
align("FloweringStage", str(OBO)+"PO_0007616", SKOS.closeMatch)  # flowering stage
# ChEBI particles: the neutron and proton radiation types are related to the particles they consist of.
align("Neutron", str(OBO)+"CHEBI_30222", SKOS.relatedMatch)    # neutron
align("Proton", str(OBO)+"CHEBI_24636", SKOS.relatedMatch)     # proton
# ChEBI isotopes (verified: Cs-137)
align("Cs137", str(OBO)+"CHEBI_196959", OWL.equivalentClass)
# ChEBI carries caesium-137 as a nuclide but has NO cobalt-60 class: searching it returns only
# radiopharmaceuticals (cobaltous chloride co 60, cyanocobalamin co 60). An earlier build aligned
# Co60 to CHEBI_749374 "cobaltous chloride co 60", reached through that class's "60co" synonym, a
# labelled compound. The target is the element, as a broader term.
align("Co60", str(OBO)+"CHEBI_27638", SKOS.broadMatch)      # cobalt atom (no Co-60 nuclide in ChEBI)
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
# Response carries no covering axiom: a response may be inhibitory, lethal or of a kind no subclass
# names.

# ---- (8) qualified cardinality: an outcome has exactly one treatment ----
# A treatment has at most one dose (hasDose is functional); a study that irradiated several doses is
# recorded with a dose range instead.
def exactly_one(cls, prop, filler):
    r = BNode(); g.add((r, RDF.type, OWL.Restriction)); g.add((r, OWL.onProperty, C(prop)))
    g.add((r, URIRef(str(OWL)+"qualifiedCardinality"), Literal(1, datatype=XSD.nonNegativeInteger)))
    g.add((r, OWL.onClass, C(filler))); g.add((cls, RDFS.subClassOf, r))
exactly_one(C("TreatmentOutcome"), "hasTreatment", "SeedIrradiationTreatment")

# An outcome with no detected response: the class records a dose at which the endpoints measured did
# not differ from the control, with the closure that the outcome has no response.
g.add((C("NoDetectedResponseOutcome"), RDF.type, OWL.Class))
_nr = BNode(); g.add((C("NoDetectedResponseOutcome"), OWL.equivalentClass, _nr))
g.add((_nr, RDF.type, OWL.Class))
_mx = BNode()
g.add((_mx, RDF.type, OWL.Restriction)); g.add((_mx, OWL.onProperty, C("hasResponse")))
g.add((_mx, OWL.maxCardinality, Literal(0, datatype=XSD.nonNegativeInteger)))
_h1 = BNode(); _h2 = BNode()
g.add((_nr, OWL.intersectionOf, _h1))
g.add((_h1, RDF.first, C("TreatmentOutcome"))); g.add((_h1, RDF.rest, _h2))
g.add((_h2, RDF.first, _mx)); g.add((_h2, RDF.rest, RDF.nil))

# ---- (9) inverse object properties, with the domain and range their inverses imply ----
g.add((C("isTreatmentOf"), RDF.type, OWL.ObjectProperty))
g.add((C("isTreatmentOf"), OWL.inverseOf, C("hasTreatment")))
g.add((C("isTreatmentOf"), RDFS.domain, C("SeedIrradiationTreatment")))
g.add((C("isTreatmentOf"), RDFS.range, C("TreatmentOutcome")))
g.add((C("inducedBy"), RDF.type, OWL.ObjectProperty))
g.add((C("inducedBy"), OWL.inverseOf, C("induces")))
g.add((C("inducedBy"), RDFS.domain, C("Response")))
g.add((C("inducedBy"), RDFS.range, C("SeedIrradiationTreatment")))

# ---- (10) additional verified alignments (OLS-checked) ----
# Each target IRI and label was checked on the EBI Ontology Lookup Service on 2026-10-04; the label
# follows each line. A measured endpoint is matched to the trait that TO or GO defines, and is related
# to the chemical entity it measures by skos:relatedMatch at most.
O = str(OBO)
align("PlantPart", O+"PO_0025131")                              # plant anatomical entity
align("ROSBalanceShift", O+"TO_0002657", SKOS.relatedMatch)     # oxidative stress response
align("ROSBalanceShift", O+"CHEBI_26523", SKOS.relatedMatch)    # reactive oxygen species
align("AntioxidantActivity", O+"TO_0001143", SKOS.closeMatch)   # antioxidant activity trait
align("AntioxidantActivity", O+"GO_0016209", SKOS.relatedMatch) # antioxidant activity
align("AntioxidantIncrease", O+"TO_0001143", SKOS.broadMatch)   # antioxidant activity trait
align("EnzymeActivityChange", O+"TO_0000599", SKOS.broadMatch)  # enzyme activity trait
align("ChlorophyllContent", O+"TO_0000495", SKOS.closeMatch)    # chlorophyll content
align("ShootLength", O+"TO_0001158", SKOS.closeMatch)           # shoot axis length
align("PollenSterility", O+"TO_0000437", SKOS.closeMatch)       # plant male sterility
align("SeedSterility", O+"TO_0000485", SKOS.broadMatch)         # plant sterility trait
align("LipidPeroxidation", O+"GO_0034440", SKOS.broadMatch)     # lipid oxidation
align("FreshMass", O+"PATO_0000125", SKOS.broadMatch)           # mass
align("DryMass", O+"PATO_0000125", SKOS.broadMatch)
align("CotyledonFreeing", O+"PO_0007049", SKOS.relatedMatch)    # cotyledon emergence stage
# Context classes: the PECO exposure that varies the same condition.
align("SoilCondition", O+"PECO_0007049", SKOS.closeMatch)       # soil environment exposure
align("Substrate", O+"PECO_0007147", SKOS.closeMatch)           # plant growth medium exposure
align("TemperatureCondition", O+"PECO_0007175", SKOS.closeMatch)  # temperature exposure
align("TemperatureCondition", O+"PATO_0000146", SKOS.relatedMatch)  # temperature
align("LightCondition", O+"PECO_0007224", SKOS.relatedMatch)    # light intensity exposure
align("WaterQuality", O+"PECO_0007383", SKOS.relatedMatch)      # watering exposure

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

# ---- (10a) endpoints and a stage that the dose windows and their sources need ----
for _e in ("GerminationPercentage", "SeedlingSurvival", "HypocotylEmergence"):
    g.add((C(_e), RDF.type, OWL.Class))
    g.add((C(_e), RDFS.subClassOf, C("Endpoint")))
align("GerminationPercentage", O+"TO_0010001", SKOS.closeMatch)        # percent germination
align("SeedlingSurvival", O+"PATO_0000169", SKOS.relatedMatch)         # viability
align("HypocotylEmergence", O+"PO_0007043", SKOS.relatedMatch)         # hypocotyl emergence stage
# Stress resistance is a measured trait: the scaffold placed it under HormeticResponse, which made
# every record of resistance a hormetic response whatever its direction or dose. It sits under
# Endpoint, matched to the TO stress response traits.
for _t in list(g.triples((C("StressResistance"), RDFS.subClassOf, None))):
    g.remove(_t)
g.add((C("StressResistance"), RDFS.subClassOf, C("Endpoint")))
align("StressResistance", O+"TO_0000164", SKOS.closeMatch)             # plant stress response trait
align("AbioticStressResistance", O+"TO_0000168", SKOS.closeMatch)      # abiotic plant stress response trait
align("BioticStressResistance", O+"TO_0000179", SKOS.closeMatch)       # biotic plant stress trait

# ---- (10b2) biochemical changes are measured endpoints ----
# The scaffold placed BiochemicalChange under HormeticResponse and hasBiochemicalChange under induces,
# so every recorded shift in reactive oxygen species or antioxidants classified as a hormetic
# response. A biochemical change is measured, in either direction and at any dose, so it is an
# Endpoint, and the property relates the outcome to the change measured in it.
for _t in list(g.triples((C("BiochemicalChange"), RDFS.subClassOf, None))):
    g.remove(_t)
g.add((C("BiochemicalChange"), RDFS.subClassOf, C("Endpoint")))
for _t in list(g.triples((C("hasBiochemicalChange"), RDFS.subPropertyOf, None))):
    g.remove(_t)
for _t in list(g.triples((C("hasBiochemicalChange"), RDFS.domain, None))):
    g.remove(_t)
g.add((C("hasBiochemicalChange"), RDFS.domain, C("TreatmentOutcome")))

# ---- (10c) subject of an outcome or an assessment: a plant structure ----
# The corpus irradiates seeds and, in eleven studies, bulbs, a tuber, callus, protocorms, shoot
# cultures or cuttings. The subject of an outcome, and of a dose assessment, is therefore a plant
# structure (PlantPart, under PO plant anatomical entity), and a seed, a bulb, a tuber and a callus are
# kinds of it, each equivalent to its Plant Ontology class.
g.add((C("PlantSeed"), RDFS.subClassOf, C("PlantPart")))
for _cls, _po in (("PlantCallus", "PO_0005052"),     # plant callus
                  ("PlantBulb", "PO_0025356"),       # bulb
                  ("PlantTuber", "PO_0004543")):     # shoot axis tuber
    g.add((C(_cls), RDF.type, OWL.Class))
    g.add((C(_cls), RDFS.subClassOf, C("PlantPart")))
    g.add((C(_cls), OWL.equivalentClass, URIRef(O + _po)))
for _t in list(g.triples((C("hasSubject"), RDFS.range, None))):
    g.remove(_t)
g.add((C("hasSubject"), RDFS.range, C("PlantPart")))
# The dose rate belongs to the treatment.
for _t in list(g.triples((C("hasDoseRateCategory"), RDFS.domain, None))):
    g.remove(_t)
g.add((C("hasDoseRateCategory"), RDFS.domain, C("SeedIrradiationTreatment")))
# RO:0002162 in taxon relates a plant structure to the organism taxon it belongs to; OnSIR uses it in
# class expressions (in taxon some NCBITaxon_X), so it is declared as an object property.
g.add((IN_TAXON, RDF.type, OWL.ObjectProperty))
g.add((IN_TAXON, RDFS.label, Literal("in taxon", lang="en")))

# ---- (12) provenance: grounded in the authors' prior work ----
g.add((ONT, DCT.source, URIRef("https://doi.org/10.56238/sevened2025.039-003")))  # book chapter
g.add((ONT, DCT.source, URIRef("https://doi.org/10.22456/2175-2745.146658")))     # RITA ontology
g.add((ONT, DCT.source, URIRef("https://doi.org/10.69547/TSFJB.030203")))         # tobacco hormesis model

# ============================================================================
# (13) CONTEXT-DEPENDENT NUMERIC DOSE CLASSIFICATION
# ----------------------------------------------------------------------------
# One absorbed dose stimulates tobacco seedlings and lies far below the doses studied in cowpea or
# fenugreek, and the germination and the seedling survival of one taxon answer to different doses.
# The classification is therefore reified as a DoseAssessment, a numeric dose applied to a plant
# structure and considered for one endpoint and one stage, and each dose window is conditioned on the
# taxon of the structure, on the endpoint and the stage its source scored, and on the dose:
#
#   Taxon_Tag_PositionDose == DoseAssessment
#       and hasSubject some (RO:0002162 some NCBITaxon_X)     the structure is in the taxon
#       and forEndpoint some E and atStage some S              the source's endpoint and stage
#       and doseGy some <OWL 2 datatype facets>
#
# The taxon enters as an existential over its NCBITaxon class, so an assessment of a subspecies or a
# cultivar whose NCBITaxon class sits below the species falls in the windows of the species.
#
# Each window is bounded by a statistic its source reports or, where the source's own observations
# place that statistic elsewhere, by the doses those observations support:
#   favourable band (lo, hi): the doses in which the source reports its most favourable responses,
#         both ends included in the band;
#   LD50 (low, high): the window below the LD50 ends below `low`, and the window at or above it
#         starts at `high`. A point estimate has low == high. Where the source reports one estimate
#         per genotype or setting, or states a bracket, low and high are its ends. Where the source's
#         own observations contradict its estimate, or the estimate lies outside the doses it tested,
#         the bounds are those its observations support; `low` is then a dose at which the source
#         observed more than half of its plants alive (low_included), and the window below the LD50
#         includes it. With a lower bound only, high is None and only the window below is defined.
#         Doses between low and high fall in no window.
# A window extends past the doses the source tested wherever its statistic leaves it open, and the
# scope note of each window records the tested range.
# ============================================================================
NCBI = "http://purl.obolibrary.org/obo/NCBITaxon_"

# One dict per taxon and endpoint. ncbi: NCBITaxon id (checked on OLS). tag: the endpoint part of the
# window names. endpoints, stages: the classes the source scored (a union when it scored several).
# band: (lo, hi) or None. ld50: (low, high) or None; ld50_kind: "estimate", "estimates",
# "observed bracket" or "lower bound"; low_included: the window below the LD50 includes `low`, a dose at
# which the source observed more than half of its plants alive. tested: lowest and highest irradiated dose, in Gy. scored: how
# the source scored its endpoint. qualifier: the strength of the bound. quote: the sentence of the
# source that states the statistic. defs: the definition of each window, by position.
TAXON_WINDOWS = [
    {
        "taxon": "Nicotiana tabacum", "ncbi": "4097", "tag": "SeedlingPerformance",
        "endpoints": ["GerminationPercentage", "GerminationRate", "HypocotylEmergence", "CotyledonFreeing",
                      "FreshMass"],
        "stages": ["GerminationStage", "EarlySeedlingStage"],
        "band": (5.0, 15.0), "ld50": None, "ld50_kind": None, "tested": (2.5, 20.0),
        "scored": "germination, hypocotyl emergence and cotyledon liberation from 3 to 9 days after "
                  "sowing, and seedling fresh weight at two and four weeks, in three varieties",
        "qualifier": "Both band ends are approximate: the source places the most favourable responses "
                     "broadly between approximately 5 and 15 Gy across its endpoints, with the apparent "
                     "maximum depending on variety, endpoint and sampling time.",
        "quote": "Across endpoints, the most favorable responses were concentrated broadly between "
                 "approximately 5 and 15 Gy. The exact position of the apparent maximum depended on "
                 "variety, endpoint, and sampling time, indicating that no single universal optimum "
                 "should be assumed for all tobacco genotypes.",
        "source": "Alves et al. 2027, Radiat. Phys. Chem. 250:114279, doi:10.1016/j.radphyschem.2026.114279",
        "defs": {
            "BelowFavourableBand": "A dose assessment of Nicotiana tabacum for germination or early "
                "seedling growth, at a dose below the favourable band of approximately 5 to 15 Gy that "
                "Alves et al. (2027) report.",
            "WithinFavourableBand": "A dose assessment of Nicotiana tabacum for germination or early "
                "seedling growth, at a dose within the favourable band of approximately 5 to 15 Gy that "
                "Alves et al. (2027) report, both ends included.",
            "AboveFavourableBand": "A dose assessment of Nicotiana tabacum for germination or early "
                "seedling growth, at a dose above the favourable band of approximately 5 to 15 Gy that "
                "Alves et al. (2027) report.",
        },
    },
    {
        "taxon": "Vigna unguiculata", "ncbi": "3917", "tag": "SeedlingSurvival",
        "endpoints": ["SeedlingSurvival"], "stages": ["FloweringStage"],
        "band": None, "ld50": (150.0, 250.0), "ld50_kind": "observed bracket", "low_included": True,
        "tested": (150.0, 300.0),
        "scored": "plants alive at 50 % flowering, relative to the unirradiated control, in three genotypes",
        "qualifier": "The source fits a straight line to survival against dose for each of three "
                     "genotypes and reports LD50s of 129.8, 132.0 and 150.2 Gy, two of them below the "
                     "lowest dose tested. Its observations bracket the LD50 of every genotype between 150 "
                     "and 250 Gy: survival at 150 Gy, the lowest dose, was 56 to 71 %, and at 250 Gy it "
                     "was zero in all three genotypes; at 200 Gy it was zero in two genotypes, and for the "
                     "third the table prints 75.86 % in both the lethality and the survival column. The "
                     "window below the LD50 runs up to 150 Gy and includes it, and the window at or above it "
                     "starts at 250 Gy; doses above 150 Gy and below 250 Gy fall in no window.",
        "quote": "Plant survival was recorded at 50% flowering. [...] The (LD50%) for each genotype was "
                 "estimated through the simple linear regression model considering 100% of seed "
                 "germination and survival rate of the control.",
        "source": "Gnankambary et al. 2019, Int. J. Genet. Mol. Biol. 11(2):29-33, doi:10.5897/IJGMB2019.0174",
        "defs": {
            "BelowLD50": "A dose assessment of Vigna unguiculata for seedling survival scored at the "
                "flowering stage, at a dose of 150 Gy or less; at 150 Gy, the lowest dose of Gnankambary et "
                "al. (2019), more than half of the plants of every genotype they tested survived.",
            "AtOrAboveLD50": "A dose assessment of Vigna unguiculata for seedling survival scored at the "
                "flowering stage, at a dose of 250 Gy or more, at which Gnankambary et al. (2019) "
                "observed no survival in any genotype they tested.",
        },
    },
    {
        "taxon": "Trigonella foenum-graecum", "ncbi": "78534", "tag": "SeedlingSurvival",
        "endpoints": ["SeedlingSurvival"], "stages": ["EarlySeedlingStage"],
        "band": None, "ld50": (350.0, None), "ld50_kind": "lower bound", "low_included": True,
        "tested": (150.0, 350.0),
        "scored": "plants alive 30 days after sowing in Petri dishes, as a percentage of the seeds sown",
        "qualifier": "The source states that the LD50 is close to 350 Gy, its highest dose, at which 64 % "
                     "of seeds germinated and 56 % of seedlings survived, against 96 % and 90 % in the "
                     "control. Survival above half at 350 Gy makes 350 Gy a lower bound on the LD50, so "
                     "only the window below the LD50 is defined, and it includes 350 Gy.",
        "quote": "The LD50 was closed to 350 on which 64 percent seed germination, 56% seedlings survival "
                 "and a considerable reduction in seedlings growth were recorded.",
        "source": "Patel et al. 2017, J. AgriSearch 4(4):237-241, doi:10.21921/jas.v4i04.10200",
        "defs": {
            "BelowLD50": "A dose assessment of Trigonella foenum-graecum for seedling survival in the "
                "early seedling stage, at a dose of 350 Gy or less; at 350 Gy, the highest dose of Patel "
                "et al. (2017), 56 % of seedlings survived.",
        },
    },
    {
        "taxon": "Magnolia champaca", "ncbi": "86757", "tag": "Germination",
        "endpoints": ["GerminationPercentage"], "stages": ["GerminationStage"],
        "band": None, "ld50": (30.0, 40.0), "ld50_kind": "estimates", "tested": (5.0, 100.0),
        "scored": "germination percentage of fresh seeds in a germination test, as lethality relative to "
                  "the control",
        "qualifier": "The source estimates the LD50 by regression of germination lethality relative to "
                     "the control and places it above 30 Gy and below 40 Gy. Its observations agree: "
                     "germination at 20 Gy was 65 % of the control and at 40 Gy 24 %.",
        "quote": "Irradiation at dose higher than 30 Gy and below 40 Gy is considered being the lethal "
                 "dosage (LD50) for M. champaca seeds",
        "source": "Zanzibar and Sudrajat 2016, Indones. J. For. Res. 3(2):95-106, doi:10.20886/ijfr.2016.3.2.95-106",
        "defs": {
            "BelowLD50": "A dose assessment of Magnolia champaca for germination, at a dose below 30 Gy, "
                "below the LD50 that Zanzibar and Sudrajat (2016) place between 30 and 40 Gy.",
            "AtOrAboveLD50": "A dose assessment of Magnolia champaca for germination, at a dose of 40 Gy "
                "or more, at or above the LD50 that Zanzibar and Sudrajat (2016) place between 30 and "
                "40 Gy.",
        },
    },
    {
        "taxon": "Lablab purpureus", "ncbi": "35936", "tag": "Germination",
        "endpoints": ["GerminationPercentage"], "stages": ["GerminationStage"],
        "band": None, "ld50": (263.1, 304.1), "ld50_kind": "estimates", "tested": (87.7, 526.2),
        "scored": "germination seven days after sowing, in Petri plates and in polybags",
        "qualifier": "The source reports probit estimates of 34.67 kR in Petri plates and 33.11 kR in "
                     "polybags and adopts 30 kR as the LD50 in its abstract and methods; at 8.77 mGy per "
                     "roentgen (air kerma) these are 304.1, 290.4 and 263.1 Gy. The window below the LD50 "
                     "ends below 263.1 Gy and the window at or above it starts at 304.1 Gy; doses between "
                     "them fall in no window.",
        "quote": "Probit analysis revealed that the LD50 value was 30kR. [...] Based on the percentage of "
                 "germination both in petri plates and polybags, the LD50 value was calculated using probit "
                 "analysis, which observed probit values being 34.67kR and 33.11kR, respectively",
        "source": "Mahesha et al. 2023, Environ. Ecol. 41(4C):2838-2844, doi:10.60151/envec/EFHD5757",
        "defs": {
            "BelowLD50": "A dose assessment of Lablab purpureus for germination, at a dose below 263.1 "
                "Gy (30 kR), the LD50 that Mahesha et al. (2023) adopt, and below both of their probit "
                "estimates.",
            "AtOrAboveLD50": "A dose assessment of Lablab purpureus for germination, at a dose of 304.1 Gy "
                "or more, at or above both probit estimates of the LD50 of Mahesha et al. (2023) and the "
                "30 kR they adopt.",
        },
    },
    {
        "taxon": "Plukenetia volubilis", "ncbi": "316893", "tag": "SeedlingSurvival",
        "endpoints": ["SeedlingSurvival"], "stages": ["EarlySeedlingStage"],
        "band": None, "ld50": (618.78, 618.78), "ld50_kind": "estimate", "tested": (500.0, 900.0),
        "scored": "surviving plants per irradiated seed in a greenhouse sowing, with growth recorded 30 "
                  "days after emergence",
        "qualifier": "A logistic regression of mortality on dose (a generalized linear model) gives 618.78 "
                     "Gy, inside the tested range of 500 to 900 Gy.",
        "quote": "A logistic regression between radiation doses and mortality was calculated to estimate "
                 "the optimum LD50 using a generalized linear model. [...] the LD50 of the dosimetry "
                 "assay was 618.78 Gy.",
        "source": "Corazon-Guivin et al. 2023, Adv. Agric. 2023:9737125, doi:10.1155/2023/9737125",
        "defs": {
            "BelowLD50": "A dose assessment of Plukenetia volubilis for seedling survival in the early "
                "seedling stage, at a dose below the LD50 of 618.78 Gy that Corazon-Guivin et al. (2023) "
                "estimate.",
            "AtOrAboveLD50": "A dose assessment of Plukenetia volubilis for seedling survival in the early "
                "seedling stage, at a dose at or above the LD50 of 618.78 Gy that Corazon-Guivin et al. "
                "(2023) estimate.",
        },
    },
    {
        "taxon": "Solanum lycopersicum", "ncbi": "4081", "tag": "SeedlingSurvival",
        "endpoints": ["SeedlingSurvival"], "stages": ["EarlySeedlingStage"],
        "band": None, "ld50": (120.0, None), "ld50_kind": "lower bound", "low_included": True,
        "tested": (50.0, 120.0),
        "scored": "seedlings alive four weeks after germination, relative to the unirradiated control",
        "qualifier": "The source fits a quadratic to the number of seedlings alive four weeks after "
                     "germination, relative to the control, and reports 132.49 Gy, above its highest dose "
                     "of 120 Gy, at which 59 % of seedlings relative to the control were alive. 120 Gy is "
                     "encoded as a lower bound on the LD50, so only the window below the LD50 is defined, "
                     "and it includes 120 Gy.",
        "quote": "The analysis of the lethal dose showed a 50% reduction in plant growth of tomato cv. "
                 "'Timothy' F1 was obtained at 132.49 Gy.",
        "source": "Indrayanti et al. 2024, Pak. J. Phytopathol. 36(2):267-280, doi:10.33866/phytopathol.036.02.1047",
        "defs": {
            "BelowLD50": "A dose assessment of Solanum lycopersicum for seedling survival in the early "
                "seedling stage, at a dose of 120 Gy or less; at 120 Gy, the highest dose of Indrayanti et "
                "al. (2024), 59 % of seedlings relative to the control were alive.",
        },
    },
    {
        "taxon": "Triticum aestivum", "ncbi": "4565", "tag": "SeedlingSurvival",
        "endpoints": ["SeedlingSurvival"], "stages": ["EarlySeedlingStage"],
        "band": None, "ld50": (272.71, 278.61), "ld50_kind": "estimates", "tested": (200.0, 450.0),
        "scored": "viable seedlings 7 days after sowing, in two varieties",
        "qualifier": "Probit estimates on survival for two varieties, 272.71 Gy (DBW 187) and 278.61 Gy "
                     "(K 1006), inside the tested range of 200 to 450 Gy; the window below the LD50 ends "
                     "below the lower estimate and the window at or above it starts at the higher.",
        "quote": "The median lethal dose was recorded to be 272.71 Gy and 278.61 Gy in DBW 187 and K 1006 "
                 "respectively.",
        "source": "Chakraborty et al. 2023, Braz. Arch. Biol. Technol. 66:e23220294, doi:10.1590/1678-4324-2023220294",
        "defs": {
            "BelowLD50": "A dose assessment of Triticum aestivum for seedling survival in the early "
                "seedling stage, at a dose below 272.71 Gy, below the LD50 of both varieties that "
                "Chakraborty et al. (2023) estimate.",
            "AtOrAboveLD50": "A dose assessment of Triticum aestivum for seedling survival in the early "
                "seedling stage, at a dose of 278.61 Gy or more, at or above the LD50 of both varieties "
                "that Chakraborty et al. (2023) estimate.",
        },
    },
]

# The 1.6.0 windows were conditioned on the taxon alone. Each is obsolete and replaced by the window
# of the same position conditioned on its source's endpoint and stage.
OBSOLETE_WINDOWS = {
    "Nicotiana_tabacum_BelowFavourableBandDose": "Nicotiana_tabacum_SeedlingPerformance_BelowFavourableBandDose",
    "Nicotiana_tabacum_WithinFavourableBandDose": "Nicotiana_tabacum_SeedlingPerformance_WithinFavourableBandDose",
    "Nicotiana_tabacum_AboveFavourableBandDose": "Nicotiana_tabacum_SeedlingPerformance_AboveFavourableBandDose",
    "Vigna_unguiculata_BelowLD50Dose": "Vigna_unguiculata_SeedlingSurvival_BelowLD50Dose",
    "Vigna_unguiculata_AtOrAboveLD50Dose": "Vigna_unguiculata_SeedlingSurvival_AtOrAboveLD50Dose",
    "Trigonella_foenum_graecum_BelowLD50Dose": "Trigonella_foenum_graecum_SeedlingSurvival_BelowLD50Dose",
}

# --- classes and properties for the assessment context ---
# The classes name the position of a dose relative to the reported statistics, and the response
# classes stay separate. A favourable band records where a source saw its most favourable responses;
# an LD50 is a lethality statistic for one endpoint and scoring time.
GENERIC = [
    ("DoseAssessment",
     "A record of one absorbed dose applied to a plant structure and considered for one endpoint and one "
     "life-cycle stage, which a reasoner places relative to the statistics reported for the taxon of the "
     "structure."),
    ("BelowReportedFavourableBand",
     "A dose assessment whose dose is below the lower end of the favourable band reported for its "
     "taxon, endpoint and stage."),
    ("WithinReportedFavourableBand",
     "A dose assessment whose dose lies within the favourable band reported for its taxon, endpoint "
     "and stage, both ends included: the band of doses in which the source reports its most favourable "
     "responses."),
    ("AboveReportedFavourableBand",
     "A dose assessment whose dose exceeds the upper end of the favourable band reported for its "
     "taxon, endpoint and stage."),
    ("BelowReportedLD50",
     "A dose assessment whose dose is below the LD50 reported for its taxon, endpoint and stage: below "
     "the reported estimate, below every estimate where the source reports one per genotype or "
     "setting, or at most a dose that the source's own observations place below the LD50."),
    ("AtOrAboveReportedLD50",
     "A dose assessment whose dose reaches or exceeds the LD50 reported for its taxon, endpoint and "
     "stage: the reported estimate, every estimate where the source reports one per genotype or "
     "setting, or an upper bound that the source's observations place on the LD50. An LD50 is a 50 % "
     "lethality statistic for one endpoint and scoring time."),
]
for cls, com in GENERIC:
    g.add((C(cls), RDF.type, OWL.Class)); g.add((C(cls), DEF, Literal(com)))
    if cls != "DoseAssessment":
        g.add((C(cls), RDFS.subClassOf, C("DoseAssessment")))
# Positions on the two sides of a statistic are disjoint intervals of the dose axis.
all_disjoint(["BelowReportedFavourableBand", "WithinReportedFavourableBand",
              "AboveReportedFavourableBand"])
all_disjoint(["BelowReportedLD50", "AtOrAboveReportedLD50"])
# Assumption: a favourable band lies below the LD50 reported for the same taxon, endpoint and stage. A
# record that codes a band reaching that LD50 makes these two axioms fire: the probe class of the band for
# that endpoint and stage becomes unsatisfiable, and an assessment inside the overlap makes the ontology
# inconsistent, so the record goes to a curator.
for _pos in ("BelowReportedFavourableBand", "WithinReportedFavourableBand"):
    g.add((C(_pos), OWL.disjointWith, C("AtOrAboveReportedLD50")))
g.add((C("WithinReportedFavourableBand"), SKOS.note, Literal(
    "Declared disjoint from AtOrAboveReportedLD50, as is BelowReportedFavourableBand, on the "
    "assumption that a favourable band lies below the LD50 reported for the same taxon, endpoint and "
    "stage. A record coding a band that reaches that LD50 makes the probe class of the band for that "
    "endpoint and stage unsatisfiable, and is sent to a curator.")))
g.add((C("boundQualifier"), RDF.type, OWL.AnnotationProperty))
g.add((C("boundQualifier"), DEF, Literal(
    "How the source of a dose window supports the bound of the window: an approximate band end, a "
    "regression estimate, one estimate per genotype or setting, a bracket the source states, a bracket "
    "set by the source's observations or a lower bound at the highest dose tested.")))
g.add((C("sourceStatement"), RDF.type, OWL.AnnotationProperty))
g.add((C("sourceStatement"), DEF, Literal(
    "A passage quoted verbatim from the source of a dose window, on which the bound of the window "
    "rests.")))

g.add((C("forEndpoint"), RDF.type, OWL.ObjectProperty))
# Two rdfs:domain axioms are read conjunctively, and an endpoint or a subject can be named on a
# DoseAssessment or on a TreatmentOutcome, so the single domain of each is their union.
def _union_domain(prop):
    for _t in list(g.triples((C(prop), RDFS.domain, None))):
        g.remove(_t)
    _dom = BNode()
    g.add((_dom, RDF.type, OWL.Class))
    g.add((_dom, OWL.unionOf, _rdf_list([C("DoseAssessment"), C("TreatmentOutcome")])))
    g.add((C(prop), RDFS.domain, _dom))
g.add((C("forEndpoint"), RDFS.range, C("Endpoint")))
# ---- endpoint categories (the review corpus's EP axis) ----
# The coded corpus records endpoints in six categories, coarser than OnSIR's Endpoint classes, so the
# axis is represented separately from the Endpoint tree and each outcome carries the category its
# source records.
g.add((C("EndpointCategory"), RDF.type, OWL.Class))
g.add((C("EndpointCategory"), DEF, Literal(
    "A coarse grouping of measured endpoints, as recorded by the coding scheme of a study corpus. "
    "Distinct from Endpoint, which names an individual measurable characteristic.")))
EP_CATS = [
    ("EmergenceAndEarlyVigor", "The endpoint category of seed germination, seedling emergence and early "
                               "seedling vigour (code EP1 of the coded corpus)."),
    ("BiochemicalEndpointCategory", "The endpoint category of biochemical measurements, such as enzyme "
                                    "activities, metabolite contents and antioxidant capacity (EP2)."),
    ("GeneticEndpointCategory", "The endpoint category of genetic measurements, such as mutation "
                                "frequency, chromosomal aberrations and molecular markers (EP3)."),
    ("MorphologicalEndpointCategory", "The endpoint category of morphological and anatomical "
                                      "measurements of plants and organs (EP4)."),
    ("PlantHealthEndpointCategory", "The endpoint category of plant health, such as disease incidence "
                                    "or resistance to a pathogen or pest (EP5)."),
    ("OtherPhysiologicalEndpointCategory", "The endpoint category of physiological measurements other "
                                           "than germination and early vigour, such as growth, yield "
                                           "and photosynthetic traits (EP6)."),
]
for nm, dfn in EP_CATS:
    g.add((C(nm), RDF.type, OWL.Class))
    g.add((C(nm), RDFS.subClassOf, C("EndpointCategory")))
    g.add((C(nm), DEF, Literal(dfn)))
all_disjoint([nm for nm, _ in EP_CATS])
g.add((C("hasEndpointCategory"), RDF.type, OWL.ObjectProperty))
g.add((C("hasEndpointCategory"), RDFS.domain, C("TreatmentOutcome")))
g.add((C("hasEndpointCategory"), RDFS.range, C("EndpointCategory")))

g.add((C("atStage"), RDF.type, OWL.ObjectProperty))
g.add((C("atStage"), RDFS.domain, C("DoseAssessment")))
g.add((C("atStage"), RDFS.range, C("LifecycleStage")))
g.add((C("doseGy"), RDF.type, OWL.DatatypeProperty))
g.add((C("doseGy"), RDF.type, OWL.FunctionalProperty))
# A dose assessment, or an outcome, concerns one endpoint, and an assessment one stage. Declaring the two
# properties functional left every window, probe and reasoning case of reason_context.py as it was
# (checked under HermiT through owlready2 and through ROBOT when they were added, 2026-10-04).
for _fp in ("forEndpoint", "atStage"):
    g.add((C(_fp), RDF.type, OWL.FunctionalProperty))
g.add((C("doseGy"), RDFS.domain, C("DoseAssessment")))

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

_union_domain("forEndpoint")
_union_domain("hasSubject")

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

def some_data(prop, drange):
    r = BNode(); g.add((r, RDF.type, OWL.Restriction))
    g.add((r, OWL.onProperty, C(prop))); g.add((r, OWL.someValuesFrom, drange))
    return r

def some_expr(prop, filler):
    r = BNode(); g.add((r, RDF.type, OWL.Restriction))
    g.add((r, OWL.onProperty, prop if isinstance(prop, URIRef) else C(prop)))
    g.add((r, OWL.someValuesFrom, filler))
    return r

def class_union(names):
    if len(names) == 1:
        return C(names[0])
    u = BNode(); g.add((u, RDF.type, OWL.Class))
    g.add((u, OWL.unionOf, _rdf_list([C(n) for n in names])))
    return u

def defined_intersection(name, members):
    g.add((C(name), RDF.type, OWL.Class))
    eq = BNode(); g.add((C(name), OWL.equivalentClass, eq))
    g.add((eq, RDF.type, OWL.Class))
    g.add((eq, OWL.intersectionOf, _rdf_list(members)))

def context(w):
    """The class expressions that condition every window of one taxon and endpoint."""
    return [C("DoseAssessment"),
            some_expr("hasSubject", some_expr(IN_TAXON, URIRef(NCBI + w["ncbi"]))),
            some_expr("forEndpoint", class_union(w["endpoints"])),
            some_expr("atStage", class_union(w["stages"]))]

# --- per-taxon window classes; the reasoner infers the generic position ---
def taxon_windows(w):
    """The windows of one taxon and endpoint: (position, data range, generic parent). A favourable
    band gives three windows and an LD50 one or two; each statistic gives its own windows."""
    band, ld = w["band"], w["ld50"]
    assert band is not None or ld is not None, w["taxon"]
    out = []
    if band is not None:
        lo, hi = band
        assert 0 < lo < hi and (ld is None or hi < ld[0]), w["taxon"]
        out.append(("BelowFavourableBand", dose_range(0.0, lo, hi_exclusive=True), "BelowReportedFavourableBand"))
        out.append(("WithinFavourableBand", dose_range(lo, hi, lo_exclusive=False, hi_exclusive=False),
                    "WithinReportedFavourableBand"))
        out.append(("AboveFavourableBand", dose_range(hi, None), "AboveReportedFavourableBand"))
    if ld is not None:
        low, high = ld
        assert (w["ld50_kind"] == "lower bound") == (high is None), w["taxon"]
        assert high is None or low <= high and (w["ld50_kind"] != "estimate" or low == high), w["taxon"]
        assert not w.get("low_included") or w["ld50_kind"] in ("observed bracket", "lower bound"), w["taxon"]
        out.append(("BelowLD50", dose_range(0.0, low, hi_exclusive=not w.get("low_included", False)),
                    "BelowReportedLD50"))
        if high is not None:
            out.append(("AtOrAboveLD50", dose_range(high, None, lo_exclusive=False), "AtOrAboveReportedLD50"))
    assert sorted(w["defs"]) == sorted(p for p, _r, _g in out), w["taxon"]
    return out


def _words(local):
    """GerminationPercentage -> germination percentage."""
    import re as _r
    return _r.sub(r"(?<=[a-z])(?=[A-Z])", " ", local).lower()


WINDOW_NAMES, PROBE_NAMES = [], []
for w in TAXON_WINDOWS:
    label = w["taxon"]
    slug = label.replace(" ", "_").replace("-", "_")
    for pos, rng, parent in taxon_windows(w):
        cname = f"{slug}_{w['tag']}_{pos}Dose"
        WINDOW_NAMES.append(cname)
        defined_intersection(cname, context(w) + [some_data("doseGy", rng)])
        g.add((C(cname), RDFS.subClassOf, C(parent)))
        g.add((C(cname), DEF, Literal(w["defs"][pos])))
        g.add((C(cname), DCT.source, Literal(w["source"])))
        g.add((C(cname), C("boundQualifier"), Literal(w["qualifier"])))
        g.add((C(cname), C("sourceStatement"), Literal(w["quote"])))
        g.add((C(cname), SKOS.scopeNote, Literal(
            f"The source irradiated doses from {w['tested'][0]:g} to {w['tested'][1]:g} Gy and scored "
            f"{w['scored']}; where the window extends past the tested doses, the position is "
            f"arithmetic only.")))
    if w["band"] is not None:
        # The probes: one per endpoint and stage the band covers, each a dose assessment of the taxon for
        # that endpoint at that stage, at the upper end of the band. A probe is unsatisfiable exactly when
        # that dose lies in a window at or above an LD50 for the same taxon, endpoint and stage, so
        # classification flags a band that reaches its LD50 without any dose being recorded. A single
        # probe over the whole band (the union of its endpoints and stages) would stay satisfiable when
        # an LD50 is reported for one endpoint and stage of a band that covers several.
        # The probe's dose is an xsd:double. Over the decimal-and-double union of the windows, HermiT
        # 1.3.8, as shipped with owlready2, does not find a single xsd:decimal value at the closed end of
        # another xsd:decimal interval to lie inside that interval, and so misses the conflict; over
        # xsd:double alone it finds it. HermiT 1.4 through ROBOT finds it over xsd:decimal, the union and
        # xsd:double alike (tested 2026-10-04: band 250 to 300 Gy against an LD50 of 273 or 300 Gy), so
        # the xsd:double probe serves both.
        hi = w["band"][1]
        for ep in w["endpoints"]:
            for st in w["stages"]:
                pname = f"{slug}_{w['tag']}_{ep}_{st}_BandUpperEndProbe"
                PROBE_NAMES.append(pname)
                defined_intersection(pname, [
                    C("DoseAssessment"),
                    some_expr("hasSubject", some_expr(IN_TAXON, URIRef(NCBI + w["ncbi"]))),
                    some_expr("forEndpoint", C(ep)), some_expr("atStage", C(st)),
                    some_data("doseGy", _facet_range(XSD.double, hi, hi, False, False))])
                g.add((C(pname), DEF, Literal(
                    f"A dose assessment of {label} for {_words(ep)} at the {_words(st)}, at the upper end "
                    f"of the favourable band reported for that taxon, {hi:g} Gy. The class is "
                    f"unsatisfiable when that dose also lies at or above an LD50 reported for the same "
                    f"taxon, endpoint and stage, which flags a band that reaches its LD50 for a curator.")))

# --- a dose position is compatible with a response type ---
# The relation is a non-entailing annotation: the reported statistics bound a dose axis, and the
# response for a given endpoint and stage needs evidence of its own. Only the favourable band is
# linked, because only a favourable band reports a response.
g.add((C("consistentWithResponse"), RDF.type, OWL.AnnotationProperty))
g.add((C("consistentWithResponse"), DEF, Literal(
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

# ---- obsolete terms of release 1.6.0 ----
# Release 1.6.0 is public, so the terms it published and this release retires keep their IRIs as
# obsolete terms: owl:deprecated, a label prefixed "obsolete", a definition prefixed "OBSOLETE.", the
# replacement (IAO:0100001 term replaced by) or a term to consider (oboInOwl:consider), and no logical
# axiom.
def obsolete(term, definition, replaced_by=None, consider=(), kind=OWL.Class):
    for _t in list(g.triples((term, None, None))):
        g.remove(_t)
    for _t in list(g.triples((None, None, term))):
        if _t[1] not in (REPLACED_BY, OIO.consider):
            g.remove(_t)
    g.add((term, RDF.type, kind))
    g.add((term, OWL.deprecated, Literal(True)))
    g.add((term, DEF, Literal("OBSOLETE. " + definition)))
    if replaced_by is not None:
        g.add((term, REPLACED_BY, replaced_by))
    for c in consider:
        g.add((term, OIO.consider, c))


# The label of an obsolete term is written with the others, from its local name, prefixed "obsolete".
for _old, _new in OBSOLETE_WINDOWS.items():
    _taxon = "Trigonella foenum-graecum" if _old.startswith("Trigonella") else " ".join(_old.split("_")[:2])
    obsolete(C(_old), f"A dose window of release 1.6.0 for {_taxon}, conditioned on the taxon "
             f"alone. Replaced by a window that is also conditioned on the endpoint and the stage its "
             f"source scored.", replaced_by=C(_new))
for _old, _new, _side in (("LowDoseRate", "DoseRateBelow100GyPerHour", "below"),
                          ("HighDoseRate", "DoseRateAbove100GyPerHour", "above")):
    obsolete(C(_old), f"A reported dose rate {_side} 100 Gy per hour. Renamed after the bound "
             f"that defines it.", replaced_by=C(_new))
obsolete(C("forTaxon"),
         "Related a dose assessment to an individual standing for a taxon. A dose assessment now names "
         "the plant structure the dose is applied to with hasSubject, and the structure states its taxon "
         "with RO:0002162 in taxon some NCBITaxon class.", consider=(C("hasSubject"), IN_TAXON),
         kind=OWL.ObjectProperty)
obsolete(C("hasTaxon"),
         "Related a plant structure to an individual standing for its taxon. A plant structure now states "
         "its taxon with RO:0002162 in taxon some NCBITaxon class.", replaced_by=IN_TAXON,
         kind=OWL.ObjectProperty)
# The three taxon individuals of 1.6.0 were typed with NCBITaxon classes, whose instances are organisms.
for _sp, _id in (("Nicotiana tabacum", "4097"), ("Vigna unguiculata", "3917"),
                 ("Trigonella foenum-graecum", "78534")):
    _ind = NS["taxon_" + _sp.replace(" ", "_").replace("-", "_")]
    for _t in list(g.triples((_ind, None, None))):
        g.remove(_t)
    g.add((_ind, RDF.type, OWL.NamedIndividual))
    g.add((_ind, OWL.deprecated, Literal(True)))
    g.add((_ind, RDFS.label, Literal(f"obsolete {_sp}")))
    g.add((_ind, RDFS.comment, Literal(
        f"OBSOLETE. Release 1.6.0 typed this individual with the class NCBITaxon_{_id} and used it as the "
        f"value of forTaxon. The taxon is now stated on the plant structure, with RO:0002162 in taxon "
        f"some NCBITaxon_{_id}.")))
    g.add((_ind, OIO.consider, URIRef(NCBI + _id)))

# ---- (14) a definition on every class and property ----
# Every OnSIR class and property carries one definition as IAO:0000115, written to say what the term
# denotes; where the meaning comes from a source, the source is given as IAO:0000119. The definitions
# that the sections above wrote (the generic positions, the windows, the endpoint categories, the
# discouraged dose categories, the obsolete terms) are kept; this table defines the rest. The comments
# the scaffold carried are replaced by these definitions.
PO_SRC = "Plant Ontology (Cooper et al. 2013), checked on the EBI Ontology Lookup Service"
# The note on the dose-rate categories states the gap the bound sits in, read from the coded corpus.
import csv as _csv
_rates = [float(r["dose_rate_gy_per_h"]) for r in _csv.DictReader(open("corpus/onsir_corpus.csv", encoding="utf-8"))
          if r["dose_rate_gy_per_h"]]
_lo_max, _hi_min = max(x for x in _rates if x < 100), min(x for x in _rates if x > 100)
RATE_NOTE = (f"The bound of 100 Gy per hour lies between the two groups of rates reported in the coded "
             f"corpus, at most {_lo_max:g} and at least {_hi_min:g} Gy per hour.")
DEFS = {
    # treatment, outcome and response
    "SeedTreatment": "A planned process applied to seeds or other plant propagules before sowing or planting.",
    "SeedIrradiationTreatment": "A planned process in which seeds or other plant propagules (bulbs, tubers, "
        "cuttings, shoot cultures, callus) are exposed to radiation of a stated type and source, at a stated "
        "dose or dose range and, where reported, a stated dose rate.",
    "TreatmentOutcome": "What was observed in a plant structure after a seed-irradiation treatment, recorded "
        "with the treatment, the subject and the response, endpoint or endpoint category observed.",
    "StimulatoryOutcome": "A treatment outcome that has a hormetic response.",
    "MutagenicOutcome": "A treatment outcome that has a mutagenic response.",
    "NoDetectedResponseOutcome": "A treatment outcome with no response: the endpoints measured did not differ "
        "from the unirradiated control.",
    "Response": "A biological process in an irradiated plant structure, or in the plant grown from it, "
        "observed as a difference from the unirradiated control in one or more endpoints.",
    "HormeticResponse": "A response observed as a biphasic dose-response: an endpoint exceeds its value in "
        "the unirradiated control over a range of low doses and falls below it at higher doses.",
    "InhibitoryResponse": "A response in which an endpoint falls below its value in the unirradiated "
        "control, such as reduced germination, growth or seedling survival.",
    "LossOfViability": "A response in which the irradiated propagule, or the plant grown from it, dies or "
        "fails to germinate or emerge.",
    "MutagenicResponse": "A response in which irradiation induces heritable changes in the genetic "
        "material of the irradiated propagule, observed as mutations or chromosomal aberrations in the plant "
        "or its progeny.",
    "SterilizationResponse": "A response in which irradiation reduces or abolishes the capacity of the plant "
        "grown from the irradiated propagule to produce viable gametes or seed.",
    # dose and dose rate
    "DoseCategory": "A qualitative classification of an irradiation dose by the biological effect a curator "
        "asserts for it.",
    "DoseRange": "The range of absorbed doses irradiated in a study, from its minimum to its maximum dose.",
    "QuantityValue": "A measured quantity with a numeric value and a unit given as a QUDT unit (absorbed dose "
        "in gray, dose rate in gray per hour or per minute, fluence in joule per square metre).",
    "DoseRateCategory": "A category of absorbed-dose rate, named by the bound that delimits it.",
    "DoseRateBelow100GyPerHour": "An absorbed-dose rate below 100 Gy per hour.",
    "DoseRateAbove100GyPerHour": "An absorbed-dose rate above 100 Gy per hour.",
    # radiation
    "RadiationType": "A kind of radiation by which a seed-irradiation treatment is delivered.",
    "Gamma": "Electromagnetic radiation emitted by an atomic nucleus in radioactive decay, such as the photons "
        "of cobalt-60 and caesium-137.",
    "XRay": "Electromagnetic radiation of wavelength from about 5 pm to 10 nm produced outside the nucleus, as "
        "by an X-ray tube.",
    "Neutron": "Radiation consisting of free neutrons.",
    "Proton": "Radiation consisting of accelerated protons.",
    "ElectronBeam": "Radiation consisting of a beam of accelerated electrons.",
    "UV_A": "Ultraviolet radiation of wavelength from 315 to 400 nm.",
    "UV_B": "Ultraviolet radiation of wavelength from 280 to 315 nm.",
    "UV_C": "Ultraviolet radiation of wavelength from 100 to 280 nm.",
    "Isotope": "A radionuclide used as the source of a seed-irradiation treatment.",
    "Am241": "The radionuclide americium-241.",
    "Co60": "The radionuclide cobalt-60, whose decay emits gamma photons of 1.17 and 1.33 MeV.",
    "Cs137": "The radionuclide caesium-137, whose decay emits gamma photons of 0.662 MeV through its daughter "
        "barium-137m.",
    "Ir192": "The radionuclide iridium-192.",
    "Xe133": "The radionuclide xenon-133.",
    # endpoints
    "Endpoint": "A measurable characteristic of an irradiated plant structure, or of the plant grown from it, "
        "used to quantify the outcome of a treatment, such as germination, root length or mutation frequency.",
    "GerminationPercentage": "The percentage of sown seeds that germinate within the period of a germination "
        "test.",
    "GerminationRate": "The speed of germination of a seed lot, measured as the time to a stated germination "
        "percentage or as a germination index.",
    "SeedlingSurvival": "The percentage of irradiated propagules, or of the seedlings raised from them, alive "
        "at a stated time after sowing, often relative to the unirradiated control.",
    "HypocotylEmergence": "The percentage of seeds whose hypocotyl has emerged at a stated time after sowing.",
    "CotyledonFreeing": "The percentage of seedlings whose cotyledons are free of the seed coat at a stated "
        "time after sowing.",
    "SeedlingVigorIndex": "An index of seedling vigour that combines germination with seedling growth, such as "
        "germination percentage multiplied by seedling length or dry mass.",
    "RootLength": "The length of the primary root or of the root system of a seedling or plant.",
    "ShootLength": "The length of the shoot of a seedling or plant.",
    "FreshMass": "The mass of a seedling, plant or organ weighed fresh.",
    "DryMass": "The mass of a seedling, plant or organ after drying.",
    "ChlorophyllContent": "The amount of chlorophyll in leaf or seedling tissue, per unit mass or area.",
    "AntioxidantActivity": "The capacity of a tissue extract to scavenge free radicals or reactive oxygen "
        "species, measured in an assay such as DPPH radical scavenging.",
    "LipidPeroxidation": "The extent of oxidative degradation of membrane lipids, usually measured as "
        "malondialdehyde content.",
    "MutationFrequency": "The frequency of mutants, or of mutations, among the plants or progeny raised from "
        "irradiated propagules.",
    "PollenSterility": "The percentage of pollen grains that are not viable in a viability test.",
    "SeedSterility": "The percentage of flowers or spikelets that fail to set seed.",
    "BiochemicalChange": "A biochemical characteristic measured after irradiation, such as the balance of "
        "reactive oxygen species, antioxidant content or an enzyme activity; the direction of the change is "
        "a result.",
    "AntioxidantIncrease": "An increase in antioxidant content or antioxidant enzyme activity measured after "
        "irradiation, relative to the unirradiated control.",
    "EnzymeActivityChange": "A change in the activity of an enzyme measured after irradiation, relative to the "
        "unirradiated control.",
    "ROSBalanceShift": "A change in the level of reactive oxygen species, or in the balance between their "
        "production and removal, measured after irradiation relative to the unirradiated control.",
    "StressResistance": "The capacity of a plant raised from an irradiated propagule to grow under a biotic or "
        "abiotic stress, measured against the unirradiated control.",
    "AbioticStressResistance": "Stress resistance under an abiotic stress, such as salinity, drought or an "
        "extreme temperature.",
    "BioticStressResistance": "Stress resistance under a biotic stress, such as a pathogen or a pest.",
    # life-cycle stages
    "LifecycleStage": "A stage in the life cycle of a plant at which an endpoint is scored.",
    "SeedStage": "The stage at which the propagule is a quiescent seed, before imbibition.",
    "GerminationStage": "The stage from the imbibition of a seed to the emergence of the radicle or of the "
        "seedling, over which germination is scored.",
    "EarlySeedlingStage": "The stage from seedling emergence through the first weeks of growth, over which "
        "seedling survival and growth are scored, in the studies coded here from 7 days to about six weeks "
        "after sowing.",
    "FloweringStage": "The stage at which the plant flowers. Radiosensitivity tests often score survival when "
        "half of the plants have flowered.",
    # plant structures
    "Plant": "A whole plant.",
    "PlantPart": "A material plant structure that can be irradiated and observed: an organ, a tissue, or a "
        "propagule such as a seed, bulb, tuber, cutting or callus.",
    "PlantSeed": "A seed: the propagule of a seed plant, which generally develops from an ovule after "
        "fertilization.",
    "PlantBulb": "A bulb: a short underground shoot whose fleshy leaves or leaf bases store reserves, as in "
        "onion, shallot and tuberose. A garlic clove is a bulblet.",
    "PlantTuber": "A shoot axis tuber: a swollen stem that stores reserves, as in the potato.",
    "PlantCallus": "A plant callus: a mass of mostly parenchyma cells, formed on wounding or in tissue "
        "culture, irradiated as the propagule in in vitro mutagenesis.",
    "Seedling": "A young plant derived from a newly germinated seed, up to the development of its first true "
        "leaf.",
    # context
    "Context": "An experimental or environmental condition under which an outcome was observed.",
    "LightCondition": "The light under which seeds were germinated or plants grown: its intensity, quality or "
        "photoperiod.",
    "SoilCondition": "The soil in which plants were grown, or a property of it.",
    "Substrate": "The medium on which seeds were germinated or plants grown, such as filter paper, agar, rock "
        "wool or a soil mix.",
    "TemperatureCondition": "The temperature at which seeds were germinated or plants grown.",
    "WaterQuality": "The water supplied to seeds or plants and its properties, such as its source, its salinity "
        "or the watering regime.",
    # dose-response models
    "DoseResponseModel": "A parametric model of how an endpoint varies with dose.",
    "BrainCousensModel": "The dose-response model of Brain and Cousens: an equation for dose responses with "
        "stimulation at low doses, which contains the common sigmoidal (log-logistic) curve as a special "
        "case.",
    # object properties
    "hasTreatment": "Relates a treatment outcome to the seed-irradiation treatment that produced it.",
    "isTreatmentOf": "Relates a seed-irradiation treatment to an outcome it produced; the inverse of has "
        "treatment.",
    "hasSubject": "Relates a treatment outcome or a dose assessment to the plant structure that was irradiated "
        "or observed.",
    "hasResponse": "Relates a treatment outcome to a response observed in it.",
    "induces": "Relates a seed-irradiation treatment to a response it induced.",
    "inducedBy": "Relates a response to the seed-irradiation treatment that induced it; the inverse of "
        "induces.",
    "hasDose": "Relates a seed-irradiation treatment to the single absorbed dose it delivered.",
    "hasDoseRange": "Relates a seed-irradiation treatment that delivered several doses to their range.",
    "minDose": "Relates a dose range to its lowest dose.",
    "maxDose": "Relates a dose range to its highest dose.",
    "hasDoseRate": "Relates a seed-irradiation treatment to the absorbed-dose rate at which it was delivered.",
    "hasDoseRateCategory": "Relates a seed-irradiation treatment to the category of its dose rate.",
    "hasDoseCategory": "Relates a treatment outcome to the dose category a curator asserts for its dose.",
    "hasExposureTime": "Relates a seed-irradiation treatment to the duration of the exposure.",
    "hasFluence": "Relates a seed-irradiation treatment to its fluence, the radiant exposure in joule per "
        "square metre by which ultraviolet treatments are dosed.",
    "hasWavelength": "Relates a seed-irradiation treatment to the wavelength of the radiation, for "
        "ultraviolet treatments.",
    "hasRadiationType": "Relates a seed-irradiation treatment to the kind of radiation that delivered it.",
    "hasSourceIsotope": "Relates a seed-irradiation treatment to the radionuclide of its source.",
    "hasContext": "Relates a treatment outcome to a condition under which it was observed.",
    "hasModel": "Relates a treatment outcome to a dose-response model fitted to it.",
    "hasBiochemicalChange": "Relates a treatment outcome to a biochemical change measured in it.",
    "hasEndpointCategory": "Relates a treatment outcome to the endpoint category its source corpus records "
        "for it.",
    "forEndpoint": "Relates a dose assessment or a treatment outcome to the endpoint it concerns.",
    "atStage": "Relates a dose assessment to the life-cycle stage at which its endpoint is scored.",
    # datatype properties
    "numericValue": "The numeric value of a quantity value, in the unit given by its qudt:hasUnit link.",
    "doseGy": "The absorbed dose of a dose assessment, in gray.",
    "bc_b": "The slope parameter b of a Brain-Cousens model, which sets the steepness of the decline.",
    "bc_c": "The lower limit c of a Brain-Cousens model, the response at very high doses.",
    "bc_d": "The upper limit d of a Brain-Cousens model, the response in the unirradiated control.",
    "bc_e": "The dose parameter e of a Brain-Cousens model, which locates the decline on the dose axis.",
    "bc_f": "The stimulation parameter f of a Brain-Cousens model, the rate of increase of the response at "
        "low doses.",
    "germinationRateIncrease": "The increase in germination relative to the control in a hormetic response, as "
        "a fraction.",
    "rootGrowthStimulus": "The increase in root growth relative to the control in a hormetic response, as a "
        "fraction.",
    "mutationFrequency": "The frequency of mutants or mutations in a mutagenic response, as a fraction.",
    "sterilityRate": "The fraction of sterile plants or gametes in a sterilization response.",
}
DEF_SOURCES = {
    "HormeticResponse": "Calabrese EJ, Baldwin LA (2002). Defining hormesis. Human & Experimental Toxicology "
        "21:91-97, doi:10.1191/0960327102ht217oa: hormesis is characterized by biphasic dose responses.",
    "BrainCousensModel": "Brain P, Cousens R (1989). An equation to describe dose responses where there is "
        "stimulation of growth at low doses. Weed Research 29:93-96, doi:10.1111/j.1365-3180.1989.tb00845.x",
    "PlantSeed": PO_SRC + ", PO:0009010 seed",
    "PlantBulb": PO_SRC + ", PO:0025356 bulb",
    "PlantTuber": PO_SRC + ", PO:0004543 shoot axis tuber",
    "PlantCallus": PO_SRC + ", PO:0005052 plant callus",
    "Seedling": PO_SRC + ", PO:0008037 seedling",
    "Plant": PO_SRC + ", PO:0000003 whole plant",
    "GerminationPercentage": "Plant Trait Ontology, TO:0010001 percent germination",
    "UV_A": "CIE ultraviolet spectral bands: UV-A 315-400 nm",
    "UV_B": "CIE ultraviolet spectral bands: UV-B 280-315 nm",
    "UV_C": "CIE ultraviolet spectral bands: UV-C 100-280 nm",
    "XRay": "Plant Experimental Conditions Ontology, PECO:0007628 X-ray exposure (5 pm to 10 nm)",
}
# Comments kept with the definitions: conventions a curator needs.
COMMENTS = {
    "SeedIrradiationTreatment": "In the OnSIR ABox one treatment individual records the irradiations of one "
        "study: a study that irradiated several doses carries a DoseRange from its lowest to its highest "
        "dose, and a treatment at a single dose records that dose with hasDose.",
    "NoDetectedResponseOutcome": "An outcome enters this class when it is asserted to have no response "
        "(hasResponse max 0). An outcome that records no response without that assertion stays "
        "unclassified, because OWL does not infer the absence of an unrecorded value.",
    "DoseRateBelow100GyPerHour": RATE_NOTE,
    "DoseRateAbove100GyPerHour": RATE_NOTE,
    "QuantityValue": "Dose and dose-rate values carry a typed qudt:hasUnit link; absorbed dose is in gray.",
    "EarlySeedlingStage": "Matched to PO:0007131 seedling development stage by skos:closeMatch: the Plant "
        "Ontology seedling stage ends with the first true leaf, and radiosensitivity tests also score "
        "seedlings after it.",
}

for _x in sorted({s for s in g.subjects() if isinstance(s, URIRef) and str(s).startswith(str(NS))}):
    if (_x, OWL.deprecated, Literal(True)) in g:
        continue
    for _t in list(g.triples((_x, RDFS.comment, None))):
        g.remove(_t)
    for _t in list(g.triples((_x, SKOS.definition, None))):
        g.remove(_t)
        if (_x, DEF, None) not in g:
            g.add((_x, DEF, _t[2]))
for _name, _d in DEFS.items():
    assert (C(_name), DEF, None) not in g, _name
    g.add((C(_name), DEF, Literal(_d)))
for _name, _s in DEF_SOURCES.items():
    g.add((C(_name), DEF_SRC, Literal(_s)))
for _name, _c in COMMENTS.items():
    g.add((C(_name), RDFS.comment, Literal(_c)))
for _p in [p for p in g.subjects(RDF.type, OWL.Class) if str(p).endswith("BandUpperEndProbe")]:
    g.add((_p, RDFS.comment, Literal(
        "A probe for the reasoner, one for each endpoint and stage of a favourable band: it is satisfiable "
        "while the band lies below every LD50 reported for the same taxon, endpoint and stage.")))
# Every class and property of the OnSIR namespace has exactly one definition.
_terms = {x for t in (OWL.Class, OWL.ObjectProperty, OWL.DatatypeProperty, OWL.AnnotationProperty)
          for x in g.subjects(RDF.type, t) if isinstance(x, URIRef) and str(x).startswith(str(NS))}
_missing = sorted(str(x)[len(str(NS)):] for x in _terms if len(list(g.objects(x, DEF))) != 1)
assert not _missing, f"terms without exactly one definition: {_missing}"
# The definition is mirrored as skos:definition, the property that SKOS-based tools and the FOOPS! FAIR
# assessment read (FOOPS! counts no IAO:0000115 as a description).
for _x in sorted(_terms):
    g.add((_x, SKOS.definition, g.value(_x, DEF)))
print(f"  definitions: {len(_terms)} terms, each with one IAO:0000115 mirrored as skos:definition")

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
    "DoseRateBelow100GyPerHour": "dose rate below 100 Gy per hour",
    "DoseRateAbove100GyPerHour": "dose rate above 100 Gy per hour",
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
        _lab = _label(str(_x)[len(str(NS)):])
        if (_x, OWL.deprecated, Literal(True)) in g:
            _lab = "obsolete " + _lab           # OBO convention for an obsolete term
        g.add((_x, RDFS.label, Literal(_lab, lang="en")))
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
# A treatment states one dose, a dose range or, for ultraviolet light, a fluence. The UV-C example is
# dosed by its fluence, the radiant exposure in J m-2, and the Co-60 example by its single dose; the
# scaffold had given the Co-60 example a dose range as well, which a single treatment does not have.
_co = C("Treat_Co60_Gamma_50Gy")
for _rng in list(eg.objects(_co, C("hasDoseRange"))):
    eg.remove((_co, C("hasDoseRange"), _rng))
    for _q in list(eg.objects(_rng, None)):
        for _t in list(eg.triples((_q, None, None))):
            eg.remove(_t)
    for _t in list(eg.triples((_rng, None, None))):
        eg.remove(_t)


def _assert_some(graph, ind, prop, cls):
    """A class assertion ind : (prop some cls), so that no class IRI stands as an individual."""
    r = BNode()
    graph.add((r, RDF.type, OWL.Restriction)); graph.add((r, OWL.onProperty, C(prop)))
    graph.add((r, OWL.someValuesFrom, C(cls))); graph.add((ind, RDF.type, r))


_assert_some(eg, _co, "hasRadiationType", "Gamma")
_assert_some(eg, _co, "hasSourceIsotope", "Co60")
_assert_some(eg, C("Treat_XRay_150Gy"), "hasRadiationType", "XRay")
_assert_some(eg, C("Treat_UVC_254nm_1200Jm2"), "hasRadiationType", "UV_C")
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
# A second outcome of the Co-60 treatment, for root length, records that no response was detected:
# it is asserted to have no response, and a reasoner classifies it as a NoDetectedResponseOutcome.
_ne = C("Outcome_Co60_RootLengthNoResponse")
eg.add((_ne, RDF.type, C("TreatmentOutcome")))
eg.add((_ne, C("hasTreatment"), _co))
eg.add((_ne, C("hasSubject"), NS["example_seed_Co60_GerminationHormesis"]))
eg.add((NS["example_endpoint_Co60_RootLength"], RDF.type, C("RootLength")))
eg.add((_ne, C("forEndpoint"), NS["example_endpoint_Co60_RootLength"]))
_mx0 = BNode()
eg.add((_mx0, RDF.type, OWL.Restriction)); eg.add((_mx0, OWL.onProperty, C("hasResponse")))
eg.add((_mx0, OWL.maxCardinality, Literal(0, datatype=XSD.nonNegativeInteger)))
eg.add((_ne, RDF.type, _mx0))
EXAMPLES_ONT = URIRef("https://w3id.org/onsir/examples")
eg.add((EXAMPLES_ONT, RDF.type, OWL.Ontology))
eg.add((EXAMPLES_ONT, URIRef(str(OWL) + "versionIRI"), URIRef(f"https://w3id.org/onsir/examples/{VERSION}")))
eg.add((EXAMPLES_ONT, OWL.imports, VERSIONED))
eg.add((EXAMPLES_ONT, OWL.versionInfo, Literal(VERSION)))
eg.add((EXAMPLES_ONT, DCT.license, URIRef("https://creativecommons.org/licenses/by/4.0/")))
eg.add((EXAMPLES_ONT, DCT.title, Literal("OnSIR illustrative individuals")))
eg.add((EXAMPLES_ONT, RDFS.comment, Literal(
    "Illustrative individuals showing how a treatment, its outcomes, their responses and a "
    "dose-response model are modelled in OnSIR. Every numeric value in this file is invented for "
    "illustration and is taken from no study. Outcome_XRay_Mutagenesis carries a dose category and no "
    "response, and a reasoner classifies it as a MutagenicOutcome; Outcome_Co60_RootLengthNoResponse is "
    "asserted to have no response, and a reasoner classifies it as a NoDetectedResponseOutcome.")))
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
ANNOTATION_NS = (str(DCT), str(SKOS), str(VANN), str(OIO))
ANNOTATION_IRIS = {DEF, DEF_SRC, REPLACED_BY}


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
    ann = sorted({p_ for p_ in graph.predicates() if str(p_).startswith(ANNOTATION_NS) or p_ in ANNOTATION_IRIS})
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
