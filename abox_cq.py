# -*- coding: utf-8 -*-
r"""Populate OnSIR with an ABox from the coded corpus (corpus/onsir_corpus.csv, 55 studies) and the dose
series of corpus/dose_series.json, then answer competency questions as SPARQL and report coverage.
Builds OnSIR_abox.ttl and OnSIR_abox.owl, which import the versioned core.

Each study is one treatment and one outcome:
  * the treatment records its radiation type, its source isotope and its dose-rate category as class
    assertions (the treatment has some Gamma, some Co60, some DoseRateBelow100GyPerHour), so no class
    IRI stands as an individual; the highest dose the study irradiated is the maximum of a dose range,
    and the reported dose rate a quantity in gray per hour;
  * the outcome records its subject, a plant structure typed with its kind (seed, bulb, tuber, callus or
    another plant part) and with its taxon as RO:0002162 in taxon some NCBITaxon class, its endpoint
    category as a class assertion, and its source as a DOI or, where the source has none, a citation.
For the seven studies of corpus/dose_series.json, each irradiated dose is a DoseAssessment of the
study's subject, for the endpoint and stage the source scored, which the reasoner places relative to the
dose windows of the taxon. The build reads no network; corpus/onsir_corpus.csv carries the NCBITaxon
identifiers, which check_taxa.py verifies on the EBI Ontology Lookup Service."""
import csv
import json
import os

from rdflib import BNode, Graph, Literal, Namespace, OWL, RDF, RDFS, URIRef, XSD

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.join(HERE, "corpus", "onsir_corpus.csv")
SERIES = os.path.join(HERE, "corpus", "dose_series.json")
NS = Namespace("https://w3id.org/onsir/")
OBO = Namespace("http://purl.obolibrary.org/obo/")
DCT = Namespace("http://purl.org/dc/terms/")
VERSION = "1.7.0"
IN_TAXON = OBO.RO_0002162
GRAY = URIRef("http://qudt.org/vocab/unit/GRAY")
GRAY_PER_HR = URIRef("http://qudt.org/vocab/unit/GRAY-PER-HR")
HAS_UNIT = URIRef("http://qudt.org/schema/qudt/hasUnit")
# The reported dose rates fall into two groups an order of magnitude apart, at most 78 and at least 303
# Gy per hour; the categories are named by the bound between them.
RATE_CUT_GY_PER_H = 100.0
ISOTOPE = {"Co-60": "Co60", "Cs-137": "Cs137"}
# The corpus codes endpoints on a six-value axis (EP1 to EP6), and each code names a category of
# measurements, so the codes map to EndpointCategory classes.
EP_MAP = {"EP1": "EmergenceAndEarlyVigor", "EP2": "BiochemicalEndpointCategory",
          "EP3": "GeneticEndpointCategory", "EP4": "MorphologicalEndpointCategory",
          "EP5": "PlantHealthEndpointCategory", "EP6": "OtherPhysiologicalEndpointCategory"}
SUBJECT_CLASS = {"seed": "PlantSeed", "bulb": "PlantBulb", "tuber": "PlantTuber", "callus": "PlantCallus",
                 "protocorm": "PlantPart", "shoot culture": "PlantPart", "cutting": "PlantPart"}
WINDOWED = {"Nicotiana tabacum", "Vigna unguiculata", "Trigonella foenum-graecum", "Magnolia champaca",
            "Lablab purpureus", "Plukenetia volubilis", "Solanum lycopersicum", "Triticum aestivum"}


def rows():
    return list(csv.DictReader(open(CORPUS, encoding="utf-8")))


def build():
    data = rows()
    series = json.load(open(SERIES, encoding="utf-8"))["studies"]
    g = Graph()
    for pfx, n in (("onsir", NS), ("obo", OBO), ("dct", DCT)):
        g.bind(pfx, n)
    AB = URIRef("https://w3id.org/onsir/abox")
    g.add((AB, RDF.type, OWL.Ontology))
    g.add((AB, URIRef(str(OWL) + "versionIRI"), URIRef(f"https://w3id.org/onsir/abox/{VERSION}")))
    g.add((AB, OWL.imports, URIRef(f"https://w3id.org/onsir/{VERSION}")))
    g.add((AB, OWL.versionInfo, Literal(VERSION)))
    g.add((AB, DCT.license, URIRef("https://creativecommons.org/licenses/by/4.0/")))
    g.add((AB, DCT.title, Literal("OnSIR ABox: coded gamma-irradiation studies of plant propagules")))
    g.add((AB, DCT.description, Literal(
        "ABox of OnSIR: the 55 studies of the coded corpus (corpus/onsir_corpus.csv), gamma-irradiation "
        "studies of seeds and other propagules, each coded as a treatment with its radiation type, source "
        "isotope, highest dose and dose rate where reported, and an outcome with its subject, taxon, "
        "endpoint category and source; and the irradiated doses of seven studies as dose assessments for "
        "the endpoint and stage each source scored.")))
    for _p in (DCT.license, DCT.description, DCT.source, DCT.title):
        g.add((_p, RDF.type, OWL.AnnotationProperty))

    def some(ind, prop, cls):
        r = BNode()
        g.add((r, RDF.type, OWL.Restriction)); g.add((r, OWL.onProperty, prop))
        g.add((r, OWL.someValuesFrom, cls)); g.add((ind, RDF.type, r))

    def quantity(iri, value, unit):
        g.add((iri, RDF.type, NS.QuantityValue))
        g.add((iri, NS.numericValue, Literal(round(value, 2), datatype=XSD.double)))
        g.add((iri, HAS_UNIT, unit))
        return iri

    for r in data:
        k = r["key"]
        t, o, s = NS[f"treat_{k}"], NS[f"outcome_{k}"], NS[f"subject_{k}"]
        g.add((t, RDF.type, NS.SeedIrradiationTreatment))
        some(t, NS.hasRadiationType, NS.Gamma)          # the corpus includes gamma sources only
        if r["source"]:
            some(t, NS.hasSourceIsotope, NS[ISOTOPE[r["source"]]])
        dr = NS[f"doserange_{k}"]
        g.add((dr, RDF.type, NS.DoseRange))
        g.add((dr, NS.maxDose, quantity(NS[f"dosemax_{k}"], float(r["highest_dose_gy"]), GRAY)))
        if k in series:
            g.add((dr, NS.minDose, quantity(NS[f"dosemin_{k}"], min(series[k]["doses_gy"]), GRAY)))
        g.add((t, NS.hasDoseRange, dr))
        if r["dose_rate_gy_per_h"]:
            rate = float(r["dose_rate_gy_per_h"])
            assert rate != RATE_CUT_GY_PER_H, k
            some(t, NS.hasDoseRateCategory,
                 NS["DoseRateBelow100GyPerHour" if rate < RATE_CUT_GY_PER_H else "DoseRateAbove100GyPerHour"])
            g.add((t, NS.hasDoseRate, quantity(NS[f"doserate_{k}"], rate, GRAY_PER_HR)))
        g.add((s, RDF.type, NS[SUBJECT_CLASS[r["subject"]]]))
        some(s, IN_TAXON, URIRef(OBO + r["ncbitaxon"].replace(":", "_")))
        g.add((s, RDFS.label, Literal(r["species"])))
        g.add((o, RDF.type, NS.TreatmentOutcome))
        g.add((o, NS.hasTreatment, t)); g.add((o, NS.hasSubject, s))
        some(o, NS.hasEndpointCategory, NS[EP_MAP[r["ep"]]])
        src = URIRef("https://doi.org/" + r["doi"]) if r["doi"] else Literal(r["citation"])
        g.add((o, DCT.source, src))
        g.add((o, RDFS.label, Literal(f"{r['species']} / {r['source'] or 'source not reported'} / highest "
                                      f"dose {float(r['highest_dose_gy']):g} Gy ({r['year']})")))
        if k in series:
            sr = series[k]
            ep, st = NS[f"endpoint_{k}"], NS[f"stage_{k}"]
            g.add((ep, RDF.type, NS[sr["endpoint"]]))
            g.add((ep, RDFS.label, Literal(f"{sr['endpoint']} scored by {k}: {sr['scored']}")))
            g.add((st, RDF.type, NS[sr["stage"]]))
            g.add((st, RDFS.label, Literal(f"{sr['stage']} of {k}")))
            for d in sr["doses_gy"]:
                a = NS[f"assessment_{k}_{d:g}Gy"]
                g.add((a, RDF.type, NS.DoseAssessment))
                g.add((a, NS.hasSubject, s)); g.add((a, NS.forEndpoint, ep)); g.add((a, NS.atStage, st))
                g.add((a, NS.doseGy, Literal(float(d), datatype=XSD.double)))
                g.add((a, DCT.source, src))
                g.add((a, RDFS.label, Literal(f"{r['species']} at {d:g} Gy ({k})")))

    # Every ABox individual is declared owl:NamedIndividual, for tools that read declarations only.
    # The ontology IRI of the ABox is no individual.
    named = {s_ for s_, o_ in g.subject_objects(RDF.type)
             if isinstance(s_, URIRef) and str(s_).startswith(str(NS)) and o_ != OWL.NamedIndividual
             and (s_, RDF.type, OWL.Ontology) not in g}
    for ind in sorted(named):
        g.add((ind, RDF.type, OWL.NamedIndividual))
    print(f"  declared {len(named)} owl:NamedIndividual")

    # ---- stub declarations for the external classes used in logical positions ----
    # The NCBITaxon classes fill the in-taxon restrictions of the subjects, a logical position, and
    # NCBITaxon is not imported, so each gets a bare owl:Class declaration and nothing more.
    _logical = (RDFS.subClassOf, OWL.equivalentClass, OWL.someValuesFrom, OWL.allValuesFrom,
                OWL.onClass, RDFS.domain, RDFS.range)
    _declared = set()
    for _t in (OWL.Class, OWL.ObjectProperty, OWL.DatatypeProperty, OWL.AnnotationProperty,
               OWL.NamedIndividual, RDFS.Datatype):
        _declared |= set(g.subjects(RDF.type, _t))
    _ext = set()
    for _s, _p, _o in g:
        _cands = (_s, _o) if _p in _logical else ((_o,) if _p == RDF.type else ())
        for _term in _cands:
            if (isinstance(_term, URIRef) and _term not in _declared
                    and not str(_term).startswith((str(NS), str(OWL), str(RDF), str(RDFS), str(XSD)))):
                _ext.add(_term)
    for _e in sorted(_ext):
        g.add((_e, RDF.type, OWL.Class))
    print(f"  external stub declarations emitted: {len(_ext)}")

    g.serialize(os.path.join(HERE, "OnSIR_abox.ttl"), format="turtle")
    # owlready2 does not parse Turtle, so the ABox ships in RDF/XML as well.
    g.serialize(os.path.join(HERE, "OnSIR_abox.owl"), format="xml")
    return g, data, series


SOME = "?t a ?_r . ?_r owl:onProperty {p} ; owl:someValuesFrom ?{v} ."


def run_cqs(g, data, series):
    Q = lambda s: list(g.query(s, initNs={"onsir": NS, "obo": OBO, "rdfs": RDFS, "owl": OWL}))
    print("=== ABox coverage ===")
    n = len(data)
    print(f"  studies: {n};  treatments: {len(set(g.subjects(RDF.type, NS.SeedIrradiationTreatment)))};"
          f"  outcomes: {len(set(g.subjects(RDF.type, NS.TreatmentOutcome)))}")
    species = sorted({r["species"] for r in data})
    print(f"  distinct species: {len(species)};  NCBITaxon by exact label: "
          f"{len({r['species'] for r in data if r['taxon_match'] == 'exact label'})}, by synonym: "
          f"{len({r['species'] for r in data if r['taxon_match'] != 'exact label'})}")
    print(f"  source isotope: {sum(1 for r in data if r['source'])}/{n};  dose rate: "
          f"{sum(1 for r in data if r['dose_rate_gy_per_h'])}/{n}")
    print(f"  subjects: " + ", ".join(f"{k} {sum(1 for r in data if r['subject'] == k)}"
                                       for k in sorted({r['subject'] for r in data})))
    hit = sorted(r["key"] for r in data if r["species"] in WINDOWED)
    print(f"  studies whose taxon carries dose windows: {len(hit)}/{n} {hit}")
    print(f"  dose assessments: {len(set(g.subjects(RDF.type, NS.DoseAssessment)))} from {len(series)} studies")

    print("\n=== competency questions (SPARQL) ===")
    print("CQ1 sources used:")
    for r in Q("SELECT ?iso (COUNT(?t) AS ?n) WHERE {" + SOME.format(p="onsir:hasSourceIsotope", v="iso")
               + "} GROUP BY ?iso ORDER BY DESC(?n)"):
        print(f"   {str(r[0]).split('/')[-1]}: {r[1]}")
    MAXD = "?t onsir:hasDoseRange ?r . ?r onsir:maxDose ?q . ?q onsir:numericValue ?v"
    print("CQ2 studies whose highest dose exceeds 500 Gy:")
    r = Q("SELECT (COUNT(?o) AS ?n) WHERE {?o onsir:hasTreatment ?t . " + MAXD + " FILTER(?v > 500)}")
    print(f"   {r[0][0]}")
    print("CQ3 range of the highest dose per study (Gy):")
    r = Q("SELECT (MIN(?v) AS ?lo) (MAX(?v) AS ?hi) (AVG(?v) AS ?mu) WHERE {" + MAXD + "}")
    print(f"   min={float(r[0][0]):.1f}, max={float(r[0][1]):.1f}, mean={float(r[0][2]):.1f}")
    print("CQ4 dose-rate category distribution:")
    for r in Q("SELECT ?c (COUNT(?t) AS ?n) WHERE {" + SOME.format(p="onsir:hasDoseRateCategory", v="c")
               + "} GROUP BY ?c"):
        print(f"   {str(r[0]).split('/')[-1]}: {r[1]}")


if __name__ == "__main__":
    g, data, series = build()
    run_cqs(g, data, series)
