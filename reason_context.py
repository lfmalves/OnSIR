# -*- coding: utf-8 -*-
r"""Taxon-relative dose classification: the reasoner places a numeric dose relative to the
statistics reported for a taxon, from the dose and the taxon alone. The placement says where the dose
lies on the dose axis of that taxon.

Five demonstrations, written to reason_context.json:
  (A) one dose (200 Gy) for the three taxa with windows: Nicotiana tabacum carries a favourable band,
      Vigna unguiculata an LD50 estimate and Trigonella foenum-graecum a lower bound on its LD50.
  (B) the two sides of each boundary: Nicotiana tabacum at 4, 5, 15 and 16 Gy (both band ends are
      included in the band) and Vigna unguiculata at 131 and 132 Gy (the LD50 is included in the
      window at or above it).
  (C) an encoding conflict. A constructed record codes a breeding dose range, 250 to 300 Gy, as a
      favourable band, beside an LD50 of 273 Gy inside it: the pattern of the wheat breeding range
      of Chakraborty et al. 2023, whose recommended 250 to 300 Gy brackets their LD50 estimates of
      272.71 and 278.61 Gy. The windows overlap, and the disjointness of the band from the doses at
      or above the LD50 makes an assessment inside the overlap inconsistent, so the record is
      flagged for a curator.
  (D) the doses of a study the windows were not built from: the twelve doses of Lumorh et al. 2025
      (cowpea, 100 to 1200 Gy), read from the ABox and placed relative to the cowpea LD50.
  (E) the datatype of the literal: one cowpea dose written as xsd:double, xsd:decimal, xsd:integer
      and xsd:float. The windows are a union over xsd:decimal and xsd:double; xsd:integer lies in the
      decimal value space and xsd:float in neither.
"""
import copy
import json
import os
import tempfile

import owlready2 as o2
import rdflib
from rdflib import BNode, Literal, Namespace, OWL, RDF, RDFS, URIRef, XSD

ONT = "file://" + o2.os.path.abspath("OnSIR.owl")
NSU = "https://w3id.org/onsir/"
N = Namespace(NSU)

TAXA = {"Nicotiana tabacum": "taxon_Nicotiana_tabacum",
        "Vigna unguiculata": "taxon_Vigna_unguiculata",
        "Trigonella foenum-graecum": "taxon_Trigonella_foenum_graecum"}
CATS = ["BelowReportedFavourableBand", "WithinReportedFavourableBand", "AboveReportedFavourableBand",
        "BelowReportedLD50", "AtOrAboveReportedLD50"]


def positions(ind):
    return sorted(c.name for c in ind.INDIRECT_is_a if getattr(c, "name", None) in CATS)


def classify(cases):
    """cases: list of (name, taxon_individual, dose_Gy). Returns {name: positions}."""
    w = o2.World()
    onto = w.get_ontology(ONT).load()
    NS = onto.get_namespace(NSU)
    made = {}
    with onto:
        for name, tax, dose in cases:
            a = NS["DoseAssessment"](name)
            a.forTaxon = [NS[tax]]
            a.doseGy = float(dose)          # functional -> single value
            made[name] = a
    with onto:
        o2.sync_reasoner_hermit(w, infer_property_values=True)
    return {name: positions(a) for name, a in made.items()}


def reason_file(graph):
    """Serialize an rdflib graph and run HermiT over it; returns (World, consistent)."""
    tmp = os.path.join(tempfile.mkdtemp(), "onsir_context.owl")
    graph.serialize(tmp, format="xml")
    w = o2.World()
    onto = w.get_ontology("file://" + tmp).load()
    try:
        with onto:
            o2.sync_reasoner_hermit(w)
        return w, True
    except o2.OwlReadyInconsistentOntologyError:
        return w, False


if __name__ == "__main__":
    OUT = {}
    DEMO_A_DOSE = 200.0
    print(f"=== (A) one dose, three taxa: {DEMO_A_DOSE:.0f} Gy ===")
    cases = [(f"a_{i}", t, DEMO_A_DOSE) for i, t in enumerate(TAXA.values())]
    res = classify(cases)
    OUT["A"] = []
    for (name, tax, dose), lbl in zip(cases, TAXA.keys()):
        OUT["A"].append(dict(taxon=lbl, dose=dose, classes=res[name]))
        print(f"  {lbl:28s} @ {dose:6.1f} Gy -> {res[name] or ['(none)']}")

    print("\n=== (B) the two sides of each boundary ===")
    walk = [("Nicotiana tabacum", 4.0), ("Nicotiana tabacum", 5.0), ("Nicotiana tabacum", 15.0),
            ("Nicotiana tabacum", 16.0), ("Vigna unguiculata", 131.0), ("Vigna unguiculata", 132.0)]
    cases = [(f"b_{i}", TAXA[lbl], d) for i, (lbl, d) in enumerate(walk)]
    res = classify(cases)
    OUT["B"] = []
    for (name, _, d), (lbl, _) in zip(cases, walk):
        OUT["B"].append(dict(taxon=lbl, dose=d, classes=res[name]))
        print(f"  {lbl:28s} @ {d:6.1f} Gy -> {res[name] or ['(none)']}")

    print("\n=== (C) a coded favourable band that reaches the coded LD50 ===")
    g = rdflib.Graph(); g.parse("OnSIR.owl")
    tri = N["taxon_conflict_test"]
    g.add((tri, RDF.type, OWL.NamedIndividual))
    g.add((tri, RDF.type, URIRef("http://purl.obolibrary.org/obo/NCBITaxon_4565")))

    def rlist(items):
        head = BNode(); cur = head
        for i, it in enumerate(items):
            g.add((cur, RDF.first, it))
            if i < len(items) - 1:
                nxt = BNode(); g.add((cur, RDF.rest, nxt)); cur = nxt
            else:
                g.add((cur, RDF.rest, RDF.nil))
        return head

    def drange(lo, hi, lo_ex, hi_ex):
        dr = BNode(); g.add((dr, RDF.type, RDFS.Datatype)); g.add((dr, OWL.onDatatype, XSD.double))
        fs = []
        if lo is not None:
            f = BNode(); g.add((f, XSD.minExclusive if lo_ex else XSD.minInclusive,
                                Literal(lo, datatype=XSD.double))); fs.append(f)
        if hi is not None:
            f = BNode(); g.add((f, XSD.maxExclusive if hi_ex else XSD.maxInclusive,
                                Literal(hi, datatype=XSD.double))); fs.append(f)
        g.add((dr, OWL.withRestrictions, rlist(fs))); return dr

    def defc(name, lo, hi, parent, lo_ex, hi_ex):
        c = N[name]; g.add((c, RDF.type, OWL.Class))
        hv = BNode(); g.add((hv, RDF.type, OWL.Restriction))
        g.add((hv, OWL.onProperty, N["forTaxon"])); g.add((hv, OWL.hasValue, tri))
        sv = BNode(); g.add((sv, RDF.type, OWL.Restriction))
        g.add((sv, OWL.onProperty, N["doseGy"]))
        g.add((sv, OWL.someValuesFrom, drange(lo, hi, lo_ex, hi_ex)))
        eq = BNode(); g.add((c, OWL.equivalentClass, eq)); g.add((eq, RDF.type, OWL.Class))
        g.add((eq, OWL.intersectionOf, rlist([N["DoseAssessment"], hv, sv])))
        g.add((c, RDFS.subClassOf, N[parent]))

    CONFLICT = dict(band=[250.0, 300.0], ld50=273.0, dose=280.0)
    defc("conflict_test_WithinFavourableBandDose", 250.0, 300.0, "WithinReportedFavourableBand",
         lo_ex=False, hi_ex=False)
    defc("conflict_test_AtOrAboveLD50Dose", CONFLICT["ld50"], None, "AtOrAboveReportedLD50",
         lo_ex=False, hi_ex=False)
    base = copy.deepcopy(g)
    CONFLICT["runs"] = []
    for dose in (260.0, CONFLICT["dose"], 320.0):
        gg = copy.deepcopy(base)
        case = N[f"conflict_test_case_{int(dose)}"]
        gg.add((case, RDF.type, OWL.NamedIndividual)); gg.add((case, RDF.type, N["DoseAssessment"]))
        gg.add((case, N["forTaxon"], tri))
        gg.add((case, N["doseGy"], Literal(dose, datatype=XSD.double)))
        _w, ok = reason_file(gg)
        CONFLICT["runs"].append(dict(dose=dose, consistent=ok))
        print(f"  assessment at {dose:5.1f} Gy: {'consistent' if ok else 'INCONSISTENT (flagged)'}")
    OUT["C"] = CONFLICT

    print("\n=== (D) the doses of Lumorh et al. 2025 from the ABox ===")
    abox = rdflib.Graph(); abox.parse("OnSIR_abox.owl")
    g = rdflib.Graph(); g.parse("OnSIR.owl")
    found = sorted(abox.subjects(RDF.type, N["DoseAssessment"]), key=lambda a: float(abox.value(a, N["doseGy"])))
    for a in found:
        for t in abox.triples((a, None, None)):
            g.add(t)
    w, ok = reason_file(g)
    assert ok
    ns = w.get_namespace(NSU)
    OUT["D"] = []
    for a in found:
        ind = ns[str(a)[len(NSU):]]
        row = dict(individual=str(a)[len(NSU):], taxon=str(abox.value(abox.value(a, N["forTaxon"]), RDFS.label)),
                   dose=float(abox.value(a, N["doseGy"])), source=str(abox.value(a, URIRef("http://purl.org/dc/terms/source"))),
                   classes=positions(ind))
        OUT["D"].append(row)
        print(f"  {row['taxon']:20s} @ {row['dose']:7.1f} Gy -> {row['classes'] or ['(none)']}")

    print("\n=== (E) the datatype of the dose literal ===")
    OUT["E"] = []
    for dt, lex in ((XSD.double, "200.0"), (XSD.decimal, "200.0"), (XSD.integer, "200"), (XSD.float, "200.0")):
        g = rdflib.Graph(); g.parse("OnSIR.owl")
        case = N["datatype_case"]
        g.add((case, RDF.type, OWL.NamedIndividual)); g.add((case, RDF.type, N["DoseAssessment"]))
        g.add((case, N["forTaxon"], N["taxon_Vigna_unguiculata"]))
        g.add((case, N["doseGy"], Literal(lex, datatype=dt)))
        w, ok = reason_file(g)
        cls = positions(w.get_namespace(NSU)["datatype_case"]) if ok else None
        OUT["E"].append(dict(datatype=str(dt).rsplit("#", 1)[-1], consistent=ok, classes=cls))
        print(f"  xsd:{str(dt).rsplit('#', 1)[-1]:8s} -> {cls}")
    json.dump(OUT, open("reason_context.json", "w"), indent=1)
    print("wrote reason_context.json")
