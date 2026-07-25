# -*- coding: utf-8 -*-
r"""Populate OnSIR with a real ABox from the EICCAM 28-study systematic-review corpus, then
answer competency questions as SPARQL and report coverage. Species are aligned to NCBITaxon by
verified OLS lookup (no fabricated IRIs). Builds OnSIR_abox.ttl (imports the enriched core)."""
import re, json, urllib.request, urllib.parse
import rdflib
from rdflib import Graph, Namespace, URIRef, Literal, BNode, RDF, RDFS, OWL, XSD

TEX = "/home/luis-alves/Desktop/papers_to_send/ready_to_go/EICCAM/table_body.tex"
NS = Namespace("https://w3id.org/onsir/")
OBO = Namespace("http://purl.obolibrary.org/obo/")
DR_MAP = {"DR1": "LowDoseRate", "DR2": "LowDoseRate", "DR3": "HighDoseRate", "DR4": "HighDoseRate"}

def parse_dose(s):
    s = s.strip().replace(",", ".")
    m = re.match(r"([\d.]+)\s*(kGy|Gy|kR|R)", s)
    if not m: return None
    v = float(m.group(1)); u = m.group(2)
    return {"kGy": v*1000, "Gy": v, "kR": v*8.77, "R": v*0.00877}[u]   # kR->Gy air-kerma approx

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
    g.serialize("OnSIR_abox.ttl", format="turtle")
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
