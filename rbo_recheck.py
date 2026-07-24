# -*- coding: utf-8 -*-
r"""Reproducible term-level comparison of OnSIR against the OBO Radiation Biology Ontology.

This is the script whose numbers the manuscript quotes. It is deliberately short and states its
matching rule explicitly, because label-overlap counts are method-dependent: a looser rule that
also consults synonyms and substring containment reports more matches than strict label equality,
and a paper should say which it used.

MATCHING RULE. An OnSIR class name is split at camel-case boundaries, lowercased, and stripped of
non-alphanumerics; an RBO class label is lowercased and stripped the same way. A match is exact
equality of the two normalized strings. Near matches use difflib ratio >= 0.85. Synonyms are NOT
consulted for the match counts (they ARE consulted for the concept probe below, which is the claim
that actually matters).

Run:  python rbo_recheck.py      (expects rbo.owl; fetch with rbo_gap.py if absent)
"""
import re, difflib, sys, os
import rdflib
from rdflib import RDF, RDFS, OWL, URIRef

NS = "https://w3id.org/onsir/"
PROBE = ["hormesis", "radiohormesis", "hormetic dose", "seed irradiation", "germination",
         "sterilization", "mutation breeding", "dose-response", "seed", "plant", "dose rate",
         "absorbed dose"]
PLANT_TOKENS = ["plant", "seed", "germinat", "crop", "cultivar"]


def norm_class(n):
    return re.sub(r"[^a-z0-9]", "", re.sub(r"(?<!^)(?=[A-Z])", " ", n).lower())


def norm_label(l):
    return re.sub(r"[^a-z0-9]", "", str(l).lower())


def main():
    if not os.path.exists("rbo.owl"):
        sys.exit("rbo.owl not present; run rbo_gap.py first to download it.")
    o = rdflib.Graph(); o.parse("OnSIR.ttl", format="turtle")
    onsir = sorted(str(c)[len(NS):] for c in set(o.subjects(RDF.type, OWL.Class))
                   if isinstance(c, URIRef) and str(c).startswith(NS))

    r = rdflib.Graph(); r.parse("rbo.owl")
    ont = next(iter(r.subjects(RDF.type, OWL.Ontology)), None)
    ver = r.value(ont, URIRef(str(OWL) + "versionIRI")) if ont else None
    native_lbl, all_lbl = {}, {}
    n_native_cls = 0
    for c in set(r.subjects(RDF.type, OWL.Class)):
        if not isinstance(c, URIRef):
            continue
        is_native = "/obo/RBO_" in str(c)
        n_native_cls += is_native
        lab = r.value(c, RDFS.label)
        if lab is None:
            continue
        all_lbl[norm_label(lab)] = c
        if is_native:
            native_lbl[norm_label(lab)] = c

    print(f"RBO release            : {ver}")
    named_cls = [x for x in set(r.subjects(RDF.type, OWL.Class)) if isinstance(x, URIRef)]
    print(f"RBO named classes      : {len(named_cls)}  (URIRef only; blank-node class "
          f"expressions excluded)")
    print(f"  RBO-native (RBO_*)   : {n_native_cls}   (with rdfs:label: {len(native_lbl)})")
    print(f"OnSIR named classes    : {len(onsir)}")
    print()

    ex_nat = [n for n in onsir if norm_class(n) in native_lbl]
    ex_any = [n for n in onsir if norm_class(n) in all_lbl]
    near = [n for n in onsir if norm_class(n) not in native_lbl
            and difflib.get_close_matches(norm_class(n), list(native_lbl), 1, 0.85)]
    print("STRICT LABEL MATCHING (synonyms not consulted)")
    print(f"  exact match to an RBO-native label   : {len(ex_nat)} {ex_nat}")
    print(f"  exact match anywhere in the release  : {len(ex_any)} {ex_any}")
    print(f"  near match (>=0.85) to RBO-native    : {len(near)} {near}")
    print(f"  NO RBO-native counterpart            : {len(onsir)-len(ex_nat)}/{len(onsir)}"
          f" = {100*(len(onsir)-len(ex_nat))/len(onsir):.1f}%")
    print(f"  NO counterpart anywhere              : {len(onsir)-len(ex_any)}/{len(onsir)}"
          f" = {100*(len(onsir)-len(ex_any))/len(onsir):.1f}%")
    print()

    # the claim that matters: does RBO carry the seed-irradiation dose-effect vocabulary at all?
    raw = open("rbo.owl", encoding="utf-8", errors="ignore").read().lower()
    print("CONCEPT PROBE (raw text of the release, so synonyms and definitions are included)")
    for t in PROBE:
        print(f"  {t:20s}: {raw.count(t.lower())} occurrence(s)")
    print()
    print("PLANT COVERAGE among RBO-native labels")
    hits = [l for l in native_lbl if any(tok in l for tok in PLANT_TOKENS)]
    print(f"  labels containing {PLANT_TOKENS}: {len(hits)}/{len(native_lbl)}"
          f" = {100*len(hits)/len(native_lbl):.2f}%  {hits}")


if __name__ == "__main__":
    main()
