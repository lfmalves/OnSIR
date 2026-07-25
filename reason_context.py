# -*- coding: utf-8 -*-
r"""Context-dependent dose classification: the reasoner places a NUMERIC dose relative to the
values reported for a taxon, from the dose and the taxon rather than from an asserted label. The
placement is evidence-relative: it says where the dose falls, not what it does.

Three demonstrations:
  (A) the SAME dose (100 Gy) classifies differently for three taxa, because each taxon carries
      its own literature-derived dose windows;
  (B) the same taxon classifies differently across doses;
  (C) an ENCODING conflict is detected: when a taxon's reported optimum exceeds its reported LD50
      (Triticum aestivum), the two statistics cannot both bound one dose ordering, and the record is
      flagged. This is a data-quality check on the encoding, not a claim that the observations are
      biologically contradictory.
"""
import owlready2 as o2

ONT = "file://" + o2.os.path.abspath("OnSIR.owl")
NSU = "https://w3id.org/onsir/"

TAXA = {"Nicotiana tabacum": "taxon_Nicotiana_tabacum",
        "Vigna unguiculata": "taxon_Vigna_unguiculata",
        "Trigonella foenum-graecum": "taxon_Trigonella_foenum_graecum"}
CATS = ["AtOrBelowReportedOptimum", "AboveReportedOptimum", "AtOrAboveReportedLD50"]


def classify(cases):
    """cases: list of (name, taxon_individual, dose_Gy). Returns {name: (categories, responses)}."""
    onto = o2.get_ontology(ONT).load()
    NS = onto.get_namespace(NSU)
    made = {}
    with onto:
        for name, tax, dose in cases:
            a = NS["DoseAssessment"](name)
            a.forTaxon = [NS[tax]]
            a.doseGy = float(dose)          # functional -> single value
            made[name] = a
    with onto:
        o2.sync_reasoner_hermit(infer_property_values=True)
    out = {}
    for name, a in made.items():
        cats = [c.name for c in a.INDIRECT_is_a if getattr(c, "name", None) in CATS]
        resp = []
        for c in a.INDIRECT_is_a:
            # expected response comes through the subClassOf some-restriction
            r = getattr(c, "value", None)
            if getattr(r, "name", None):
                resp.append(r.name)
        out[name] = (cats, sorted(set(resp)))
    return out


if __name__ == "__main__":
    print("=== (A) ONE dose, THREE taxa: 100 Gy ===")
    cases = [(f"a_{i}", t, 100.0) for i, t in enumerate(TAXA.values())]
    res = classify(cases)
    for (name, tax, dose), lbl in zip(cases, TAXA.keys()):
        cats, resp = res[name]
        print(f"  {lbl:28s} @ {dose:6.1f} Gy -> {cats if cats else ['(none)']}")

    print("\n=== (B) ONE taxon (Nicotiana tabacum), FOUR doses ===")
    doses = [5.0, 12.0, 20.0, 40.0]
    cases = [(f"b_{i}", TAXA["Nicotiana tabacum"], d) for i, d in enumerate(doses)]
    res = classify(cases)
    for (name, _, d) in cases:
        cats, resp = res[name]
        print(f"  {d:6.1f} Gy -> {cats if cats else ['(none)']}")

    print("\n=== (C) contradiction detection: a reported optimum ABOVE the reported LD50 ===")
    print("  Triticum aestivum is reported with optimum 250-300 Gy but LD50 273-279 Gy")
    print("  (Chauhan et al. 2023), so the at-or-below-optimum and at-or-above-LD50 windows would overlap.")
    onto = o2.get_ontology(ONT).load()
    NS = onto.get_namespace(NSU)
    import rdflib
    # build the overlapping encoding directly in RDF, then reason
    g = rdflib.Graph(); g.parse("OnSIR.owl")
    from rdflib import URIRef, BNode, Literal, RDF, RDFS, OWL, XSD, Namespace
    N = Namespace(NSU); OBO = "http://purl.obolibrary.org/obo/NCBITaxon_"
    tri = N["taxon_Triticum_aestivum"]
    g.add((tri, RDF.type, OWL.NamedIndividual)); g.add((tri, RDF.type, URIRef(OBO+"4565")))

    def rlist(items):
        head = BNode(); cur = head
        for i, it in enumerate(items):
            g.add((cur, RDF.first, it))
            if i < len(items)-1:
                nxt = BNode(); g.add((cur, RDF.rest, nxt)); cur = nxt
            else: g.add((cur, RDF.rest, RDF.nil))
        return head
    def drange(lo, hi, lo_ex=True, hi_ex=False):
        dr = BNode(); g.add((dr, RDF.type, RDFS.Datatype)); g.add((dr, OWL.onDatatype, XSD.double))
        fs = []
        if lo is not None:
            f = BNode(); g.add((f, XSD.minExclusive if lo_ex else XSD.minInclusive,
                                Literal(lo, datatype=XSD.double))); fs.append(f)
        if hi is not None:
            f = BNode(); g.add((f, XSD.maxExclusive if hi_ex else XSD.maxInclusive,
                                Literal(hi, datatype=XSD.double))); fs.append(f)
        g.add((dr, OWL.withRestrictions, rlist(fs))); return dr
    def defc(name, lo, hi, parent, lo_ex=True, hi_ex=False):
        c = N[name]; g.add((c, RDF.type, OWL.Class))
        hv = BNode(); g.add((hv, RDF.type, OWL.Restriction))
        g.add((hv, OWL.onProperty, N["forTaxon"])); g.add((hv, OWL.hasValue, tri))
        sv = BNode(); g.add((sv, RDF.type, OWL.Restriction))
        g.add((sv, OWL.onProperty, N["doseGy"])); g.add((sv, OWL.someValuesFrom, drange(lo, hi, lo_ex, hi_ex)))
        eq = BNode(); g.add((c, OWL.equivalentClass, eq)); g.add((eq, RDF.type, OWL.Class))
        g.add((eq, OWL.intersectionOf, rlist([N["DoseAssessment"], hv, sv])))
        g.add((c, RDFS.subClassOf, N[parent]))
    defc("Triticum_aestivum_AtOrBelowOptimumDose", 0.0, 300.0, "AtOrBelowReportedOptimum")
    defc("Triticum_aestivum_AtOrAboveLD50Dose", 273.0, None, "AtOrAboveReportedLD50", lo_ex=False)
    bad = N["triticum_overlap_case"]
    g.add((bad, RDF.type, OWL.NamedIndividual)); g.add((bad, RDF.type, N["DoseAssessment"]))
    g.add((bad, N["forTaxon"], tri))
    g.add((bad, N["doseGy"], Literal(280.0, datatype=XSD.double)))
    g.serialize("/tmp/onsir_overlap.owl", format="xml")

    onto2 = o2.get_ontology("file:///tmp/onsir_overlap.owl").load()
    try:
        with onto2:
            o2.sync_reasoner_hermit()
        print("  result: CONSISTENT  (unexpected -- the overlap was not detected)")
    except o2.OwlReadyInconsistentOntologyError:
        print("  result: INCONSISTENT as expected -> 280 Gy would fall BOTH at-or-below the")
        print("          reported optimum AND at-or-above the reported LD50 for this taxon.")
        print("          The two reported statistics therefore cannot both bound a single")
        print("          dose ordering as encoded, so the RECORD is flagged for review.")
        print("          NOTE: this is a data-quality signal about the encoding, NOT a proof")
        print("          that the underlying observations are biologically contradictory --")
        print("          they may concern different endpoints, stages, or the surviving")
        print("          subpopulation, in which case both can be simultaneously true.")
