# -*- coding: utf-8 -*-
r"""Populate OnSIR with a real ABox from the EICCAM 28-study systematic-review corpus, then
answer competency questions as SPARQL and report coverage. Species are aligned to NCBITaxon by
verified OLS lookup (no fabricated IRIs). Builds OnSIR_abox.ttl (imports the enriched core)."""
import os, re, json, urllib.request, urllib.parse
import rdflib
from rdflib import Graph, Namespace, URIRef, Literal, BNode, RDF, RDFS, OWL, XSD

# The coded corpus travels WITH the release. Reading it from a path outside the repository would
# make every ABox number in the paper unreproducible by anyone else.
TEX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "corpus", "eiccam_table_body.tex")
NS = Namespace("https://w3id.org/onsir/")
OBO = Namespace("http://purl.obolibrary.org/obo/")
DR_MAP = {"DR1": "LowDoseRate", "DR2": "LowDoseRate", "DR3": "HighDoseRate", "DR4": "HighDoseRate"}

def parse_dose(s):
    s = s.strip().replace(",", ".")
    m = re.match(r"([\d.]+)\s*(kGy|Gy|kR|R)", s)
    if not m: return None
    v = float(m.group(1)); u = m.group(2)
    # The roentgen factors are an air-kerma-to-absorbed-dose approximation (1 R ~ 8.77 mGy in air),
    # not a measured conversion. Two of the 28 studies report in roentgens, and one of them
    # (60 kR -> 526 Gy) crosses the 500 Gy threshold used by CQ2, so that answer depends on this
    # factor. The manuscript states it.
    return {"kGy": v*1000, "Gy": v, "kR": v*8.77, "R": v*0.00877}[u]

# The corpus codes endpoints on a six-value axis (EICCAM axis EP): EP1 emergence and early vigour,
# EP2 biochemistry, EP3 genetics, EP4 morphology/anatomy, EP5 plant health, EP6 other physiological.
# These are categories, not individual measurements, so they map to EndpointCategory classes.
EP_MAP = {"EP1": "EmergenceAndEarlyVigor",
          "EP2": "BiochemicalEndpointCategory",
          "EP3": "GeneticEndpointCategory",
          "EP4": "MorphologicalEndpointCategory",
          "EP5": "PlantHealthEndpointCategory",
          "EP6": "OtherPhysiologicalEndpointCategory"}

def parse_rows():
    rows = []
    for line in open(TEX, encoding="utf-8"):
        if "&" not in line: continue
        cells = [c.strip() for c in line.split("&")]
        if len(cells) < 12: continue
        sp = re.sub(r"\\textit\{(.+?)\}", r"\1", cells[0]).strip()
        rows.append(dict(species=sp, year=cells[1], country=cells[2], dr=cells[5],
                         source=cells[7].strip(), dose=parse_dose(cells[8]), ep=cells[10].strip()))
    return rows

# Species we could not resolve by EXACT label match, with what NCBITaxon actually holds. Checked
# against OLS on 2026-07-24. All three are present; none is reachable by exact label. Resolving them
# means accepting a disambiguated label or a taxonomic reclassification, which is a curator's call,
# so we record the candidates rather than assert them.
NEAR_MISSES = {
    "Ficus variegata":          ("NCBITaxon:100579",  "Ficus variegata (in: eudicots)",
                                 "homonym disambiguator in the label"),
    "Phyllanthus odontadenius": ("NCBITaxon:2708486", "Moeroris odontadenia",
                                 "reclassified; current name differs"),
    "Polianthes tuberosa":      ("NCBITaxon:82206",   "Agave amica",
                                 "reclassified; current name differs"),
}


def ols_ncbitaxon(species):
    try:
        url = ("https://www.ebi.ac.uk/ols4/api/search?q=" + urllib.parse.quote(species) +
               "&ontology=ncbitaxon&exact=true&rows=1")
        d = json.load(urllib.request.urlopen(url, timeout=12))
        docs = d["response"]["docs"]
        return docs[0]["iri"] if docs and docs[0]["label"].lower() == species.lower() else None
    except Exception:
        return None

def build():
    rows = parse_rows()
    g = Graph(); g.bind("onsir", NS); g.bind("obo", OBO)
    g.add((URIRef("https://w3id.org/onsir/abox"), RDF.type, OWL.Ontology))
    g.add((URIRef("https://w3id.org/onsir/abox"), OWL.imports, URIRef("https://w3id.org/onsir")))
    # verify distinct species once
    species = sorted(set(r["species"] for r in rows))
    taxon = {sp: ols_ncbitaxon(sp) for sp in species}
    iso = {"Co-60": "Co60", "Cs-137": "Cs137"}
    for i, r in enumerate(rows):
        t = NS[f"treat_{i:02d}"]; o = NS[f"outcome_{i:02d}"]; seed = NS[f"seed_{i:02d}"]
        g.add((t, RDF.type, NS.SeedIrradiationTreatment))
        if r["source"] in iso:
            g.add((t, NS.hasSourceIsotope, NS[iso[r["source"]]]))
        if r["dose"] is not None:
            qv = NS[f"dose_{i:02d}"]; g.add((qv, RDF.type, NS.QuantityValue))
            g.add((qv, NS.numericValue, Literal(round(r["dose"], 2), datatype=XSD.double)))
            # a typed unit link, not a string. The comment form referenced UO, which the
            # ontology does not align to, and contradicted the abstract's own correction.
            g.add((qv, URIRef("http://qudt.org/schema/qudt/unit"),
                   URIRef("http://qudt.org/vocab/unit/Gray")))
            g.add((t, NS.hasDose, qv))
        if DR_MAP.get(r["dr"]):
            g.add((o, NS.hasDoseRateCategory, NS[DR_MAP[r["dr"]]]))
        if EP_MAP.get(r["ep"]):
            g.add((o, NS.hasEndpointCategory, NS[EP_MAP[r["ep"]]]))
        g.add((seed, RDF.type, NS.PlantSeed))
        g.add((seed, RDFS.label, Literal(r["species"])))
        if taxon.get(r["species"]):
            # A taxon is NOT an anatomical type: the seed HAS a taxon, it is not a subclass /
            # instance of one. We therefore link via onsir:hasTaxon to a taxon individual that
            # is itself typed with the (verified) NCBITaxon class.
            tind = NS[f"taxon_{r['species'].replace(' ', '_').replace('-', '_')}"]
            g.add((tind, RDF.type, URIRef(taxon[r["species"]])))
            g.add((tind, RDFS.label, Literal(r["species"])))
            g.add((seed, NS.hasTaxon, tind))
        g.add((o, RDF.type, NS.TreatmentOutcome))
        g.add((o, NS.hasTreatment, t)); g.add((o, NS.hasSubject, seed))
        g.add((o, RDFS.label, Literal(f"{r['species']} / {r['source']} / {r['dose']} Gy ({r['year']})")))
    # Declare every ABox individual as owl:NamedIndividual before serializing. Without the
    # declaration the graph is not a legal OWL 2 DL ontology, and an OWL API or owlready2 pipeline
    # loads the file and reports ZERO individuals -- the assertions are silently invisible.
    named = set()
    for s_, p_, o_ in g:
        for term in (s_, o_):
            if isinstance(term, URIRef) and str(term).startswith(NS) and "#" not in str(term):
                local = str(term)[len(str(NS)):]
                if local.split("_")[0] in ("treat", "outcome", "seed", "dose", "taxon"):
                    named.add(term)
    for ind in sorted(named):
        g.add((ind, RDF.type, OWL.NamedIndividual))
    print(f"  declared {len(named)} owl:NamedIndividual")

    g.serialize("OnSIR_abox.ttl", format="turtle")
    # owlready2 does not parse Turtle, so a Turtle-only ABox cannot be loaded in an owlready2
    # pipeline. Ship RDF/XML alongside it.
    g.serialize("OnSIR_abox.owl", format="xml")
    return g, rows, taxon

def run_cqs(g, rows, taxon):
    Q = lambda s: list(g.query(s, initNs={"onsir": NS, "obo": OBO, "rdfs": RDFS}))
    print("=== ABox coverage ===")
    n = len(rows)
    print(f"  studies: {n};  treatments: {len(set(g.subjects(RDF.type, NS.SeedIrradiationTreatment)))};"
          f"  outcomes: {len(set(g.subjects(RDF.type, NS.TreatmentOutcome)))}")
    aligned = sum(1 for v in taxon.values() if v)
    print(f"  distinct species: {len(taxon)};  NCBITaxon-aligned (verified): {aligned}")
    print(f"  dose populated: {sum(1 for r in rows if r['dose'] is not None)}/{n}")
    print(f"  endpoint category: {sum(1 for r in rows if EP_MAP.get(r['ep']))}/{n}")
    print(f"  source isotope: {sum(1 for r in rows if r['source'] in ('Co-60','Cs-137'))}/{n}")
    print(f"  dose-rate category: {sum(1 for r in rows if DR_MAP.get(r['dr']))}/{n}")
    # Applicability of the taxon-specific dose windows (Section 7) to this corpus. Reported because
    # it is currently zero, and a reader should learn that here rather than discover it.
    windowed = {"Nicotiana tabacum", "Vigna unguiculata", "Trigonella foenum-graecum",
                "Capsicum annuum"}
    hit = sorted({r["species"] for r in rows if r["species"] in windowed})
    print(f"  studies whose taxon carries encoded dose windows: {len(hit)}/{n} {hit or '(none)'}")
    unres = sorted(sp for sp, iri in taxon.items() if not iri)
    print(f"  species not resolved by exact-label matching: {len(unres)}")
    for sp in unres:
        nm = NEAR_MISSES.get(sp)
        print(f"    {sp:26s} -> " + (f"{nm[0]} {nm[1]!r} ({nm[2]})" if nm else "no candidate found"))
    print("    -> all three ARE in NCBITaxon; the limitation is the exact-label rule, not the")
    print("       resource. Accepting them requires a curator decision on taxonomic synonymy.")
    print("    -> the numeric-dose classification needs BOTH a reported optimum and a reported")
    print("       LD50 for the taxon; the four taxa that have both do not appear in this corpus,")
    print("       so the two reasoning contributions currently apply to disjoint data.")

    print("\n=== competency questions (SPARQL) ===")
    print("CQ1 sources used:")
    for r in Q("SELECT ?iso (COUNT(?t) AS ?n) WHERE {?t onsir:hasSourceIsotope ?iso} GROUP BY ?iso ORDER BY DESC(?n)"):
        print(f"   {str(r[0]).split('/')[-1]}: {r[1]}")
    print("CQ2 studies with dose > 500 Gy (high/sterilizing range):")
    r = Q("SELECT (COUNT(?o) AS ?n) WHERE {?o onsir:hasTreatment ?t. ?t onsir:hasDose ?q. ?q onsir:numericValue ?v. FILTER(?v > 500)}")
    print(f"   {r[0][0]}")
    print("CQ3 dose range (Gy):")
    r = Q("SELECT (MIN(?v) AS ?lo) (MAX(?v) AS ?hi) (AVG(?v) AS ?mu) WHERE {?q onsir:numericValue ?v}")
    print(f"   min={float(r[0][0]):.1f}, max={float(r[0][1]):.1f}, mean={float(r[0][2]):.1f}")
    print("CQ4 dose-rate category distribution:")
    for r in Q("SELECT ?c (COUNT(?o) AS ?n) WHERE {?o onsir:hasDoseRateCategory ?c} GROUP BY ?c"):
        print(f"   {str(r[0]).split('/')[-1]}: {r[1]}")
    print("CQ5 seeds linked to an NCBITaxon class via hasTaxon (species interoperability):")
    r = Q("SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE {?s onsir:hasTaxon ?t. ?t a ?tax. "
          "FILTER(STRSTARTS(STR(?tax),'http://purl.obolibrary.org/obo/NCBITaxon_'))}")
    print(f"   {r[0][0]} seeds carry a resolved taxon")
    print("CQ6 mean dose by isotope:")
    for r in Q("SELECT ?iso (AVG(?v) AS ?mu) (COUNT(?t) AS ?n) WHERE {?t onsir:hasSourceIsotope ?iso; onsir:hasDose ?q. ?q onsir:numericValue ?v} GROUP BY ?iso"):
        print(f"   {str(r[0]).split('/')[-1]}: mean {float(r[1]):.0f} Gy (n={r[2]})")

if __name__ == "__main__":
    g, rows, taxon = build()
    run_cqs(g, rows, taxon)
