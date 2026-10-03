# -*- coding: utf-8 -*-
r"""Populate OnSIR with an ABox from the 28-study coded corpus (corpus/eiccam_table_body.tex) and
the studies coded in addition to it (corpus/added_studies.json), then answer competency questions as
SPARQL and report coverage. Species are aligned to NCBITaxon by exact-label OLS lookup. Each study
is coded with the highest dose it irradiated, as the maximum of a dose range, and with its source as
a DOI checked on Crossref or, where the source has no DOI, a bibliographic citation. Builds
OnSIR_abox.ttl and OnSIR_abox.owl, which import the core."""
import os, re, json, urllib.request, urllib.parse
import rdflib
from rdflib import Graph, Namespace, URIRef, Literal, BNode, RDF, RDFS, OWL, XSD

# The coded corpus travels WITH the release. Reading it from a path outside the repository would
# make every ABox number in the paper unreproducible by anyone else.
TEX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "corpus", "eiccam_table_body.tex")
ADDED = os.path.join(os.path.dirname(os.path.abspath(__file__)), "corpus", "added_studies.json")
NS = Namespace("https://w3id.org/onsir/")
OBO = Namespace("http://purl.obolibrary.org/obo/")
DCT = Namespace("http://purl.org/dc/terms/")
VERSION = "1.6.0"
# The corpus's DR1-DR4 axis codes the shape of the dose-response curve, so the dose-rate category is
# derived from the rate each study reports, where it reports one. The reported rates fall into two
# groups an order of magnitude apart, 37.4 to 78 Gy/h and 303 to 6645.7 Gy/h, and the cut lies in the
# gap. Every reported rate delivers the study's highest dose in at most about four hours, an acute
# exposure.
RATE_CUT_GY_PER_H = 100.0

def parse_rate(s):
    """Reported dose rate in Gy/h, or None. Handles Gy/kGy/mGy per h/min/s and the Portuguese
    decimal comma used by the corpus."""
    s = (s or "").replace(",", ".").strip()
    m = re.match(r"([\d.]+)\s*(kGy|Gy|mGy)\s*/\s*(h|hr|hora|min|s)\s*$", s, re.I)
    if not m:
        return None
    v = float(m.group(1)) * {"kgy": 1000.0, "gy": 1.0, "mgy": 1e-3}[m.group(2).lower()]
    return v * {"h": 1, "hr": 1, "hora": 1, "min": 60, "s": 3600}[m.group(3).lower()]

def parse_dose(s):
    s = s.strip().replace(",", ".")
    m = re.match(r"([\d.]+)\s*(kGy|Gy|kR|R)", s)
    if not m: return None
    v = float(m.group(1)); u = m.group(2)
    # Exposure in roentgens is converted at 8.77 mGy per roentgen, the air kerma that one roentgen
    # of exposure corresponds to, taken as the dose to the seed. At the 1.25 MeV of cobalt-60, water
    # absorbs 1.11 times the energy per unit mass that air does (NIST mass energy-absorption
    # coefficients), so the converted doses are lower estimates of the dose to water. Two of the 28
    # studies report in roentgens (1.5 kR -> 13.2 Gy and 60 kR -> 526.2 Gy), and the second counts
    # towards CQ2 with either factor.
    return {"kGy": v*1000, "Gy": v, "kR": v*8.77, "R": v*0.00877}[u]

# The corpus codes endpoints on a six-value axis (EP): EP1 emergence and early vigour, EP2
# biochemistry, EP3 genetics, EP4 morphology and anatomy, EP5 plant health, EP6 other physiological.
# Each code names a category of measurements, so the codes map to EndpointCategory classes.
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
        key = re.search(r"\\citealp\{(\w+)\}", cells[-1]).group(1)
        rows.append(dict(key=key, species=sp, year=cells[1], country=cells[2], ff=cells[4].strip(),
                         dr=cells[5], rate=parse_rate(cells[9]),
                         source=cells[7].strip(), dose=parse_dose(cells[8]), ep=cells[10].strip(),
                         doses=None))
    for st in json.load(open(ADDED, encoding="utf-8"))["studies"]:
        rows.append(dict(key=st["key"], species=st["species"], year=st["year"], country=st["country"],
                         ff=st["ff"], dr=None, rate=parse_rate(st["dose_rate"]), source=st["source"],
                         dose=float(max(st["doses_gy"])), ep=st["ep"],
                         doses=[float(d) for d in st["doses_gy"]]))
    return rows


# Source of each study: (first-author family name, DOI) where the source has a DOI, each resolved on
# Crossref with that first author and year; (first-author family name, None, citation) otherwise.
STUDY_SOURCES = {
    "kikakedimau2014": ("Kikakedimau Nakweti", "10.9734/AJEA/2014/8631"),
    "kainthura2015": ("Kainthura", "10.4038/tar.v26i4.8135"),
    "zanzibar2016": ("Zanzibar", "10.20886/ijfr.2016.3.2.95-106"),
    "abdelrahman2016": ("Abd El-Rahman", "10.21608/jbes.2016.369618"),
    "benslimani2019": ("Benslimani", "10.14719/pst.2019.6.4.634"),
    "geng2019": ("Geng", "10.3390/f10050406"),
    "thisawech2020": ("Thisawech", None,
                      "Thisawech M, Saritnum O, Sarapirom S, Prakrajang K, Phakham W (2020). Effects "
                      "of plasma technique and gamma irradiation on seed germination and seedling "
                      "growth of chili pepper. Chiang Mai Journal of Science 47(1):73-82."),
    "kazakova2020": ("Kazakova", "10.31367/2079-8725-2020-68-2-23-28"),
    "bhuiyan2021": ("Bhuiyan", None,
                    "Bhuiyan MSH, Emon RM, Khatun MK, Malek MA, Khan NA (2021). Evaluation of induced "
                    "genetic variability in gamma ray irradiated rapeseed mutants. Bangladesh Journal "
                    "of Nuclear Agriculture 35:1-8."),
    "boonsua2021": ("Boonsua", "10.1088/1742-6596/1719/1/012076"),
    "zanzibar2021": ("Zanzibar", "10.1080/21580103.2021.1924872"),
    "roy2021": ("Roy", None,
                "Roy S, Alim SMA, Ghosh SR, Akondo MRI, Chowhan S, Ali MKJ (2021). Binamash-2, a gamma "
                "ray induced high yielding blackgram mutant variety. Bangladesh Journal of Nuclear "
                "Agriculture 35:63-70."),
    "nelka2022": ("Nelka", "10.53552/ijmfmap.8.1.2022.40-46"),
    "jabbar2022": ("Jabbar", "10.53730/ijhs.v6nS3.7675"),
    "sudrajat2022": ("Sudrajat", "10.13057/biodiv/d231014"),
    "hase2023": ("Hase", "10.3389/fpls.2023.1149083"),
    "zanzibar2023": ("Zanzibar", "10.4308/hjb.30.2.336-346"),
    "mahesha2023": ("Mahesha", "10.60151/envec/EFHD5757"),
    "islam2023": ("Islam", "10.3329/bjnag.v37i2.71778"),
    "corazonguivin2023": ("Corazon-Guivin", "10.1155/2023/9737125"),
    "ajijah2023": ("Ajijah", "10.1051/e3sconf/202346701021"),
    "obok2023": ("Obok", "10.14720/aas.2023.119.3.13423"),
    "nelka2024": ("Nelka", None,
                  "Nelka SAP, Vidanapathirana NP, Silva TD, Subasinghe S, Dahanayake N (2024). Effect "
                  "of gamma irradiation on seed germination of Catharanthus roseus (Madagascar "
                  "periwinkle). Proceedings of the 5th National Symposium on Agro-Technology and "
                  "Rural Sciences (NSATRS), Colombo, p. 31."),
    "pandey2024": ("Pandey", "10.36253/caryologia-2820"),
    "indrayanti2024": ("Indrayanti", "10.33866/phytopathol.036.02.1047"),
    "ahmed2025": ("Ahmed", "10.1007/s44372-025-00375-1"),
    "kotsyubinskaya2025": ("Kotsyubinskaya", "10.18619/2072-9146-2025-1-37-44"),
    "haque2025": ("Haque", "10.3329/bjnag.v39i1.83341"),
    "lumorh2025": ("Lumorh", "10.3329/ijarit.v15i1.82798"),
}

# Species that exact label matching leaves unresolved, with what NCBITaxon holds (OLS, 2026-07-24).
# All three are present under other labels: one disambiguated, two reclassified. Accepting them is a
# curator's call, so the candidates are recorded and left unasserted.
NEAR_MISSES = {
    "Ficus variegata":          ("NCBITaxon:100579",  "Ficus variegata (in: eudicots)",
                                 "homonym disambiguator in the label"),
    "Phyllanthus odontadenius": ("NCBITaxon:2708486", "Moeroris odontadenia",
                                 "reclassified; current name differs"),
    "Polianthes tuberosa":      ("NCBITaxon:82206",   "Agave amica",
                                 "reclassified; current name differs"),
}


def slug(species):
    return re.sub(r"[^A-Za-z0-9]+", "_", species).strip("_")


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
    g = Graph(); g.bind("onsir", NS); g.bind("obo", OBO); g.bind("dct", DCT)
    AB = URIRef("https://w3id.org/onsir/abox")
    g.add((AB, RDF.type, OWL.Ontology))
    g.add((AB, OWL.imports, URIRef("https://w3id.org/onsir")))
    g.add((AB, OWL.versionInfo, Literal(VERSION)))
    g.add((AB, DCT.license, URIRef("https://creativecommons.org/licenses/by/4.0/")))
    g.add((AB, DCT.description, Literal(
        "ABox of OnSIR: gamma-irradiation studies of seeds and other propagules, each coded as a "
        "treatment with its source isotope, the highest dose it irradiated and its dose rate where "
        "reported, and an outcome with its subject, endpoint category and source; and the irradiated "
        "doses of one cowpea study as dose assessments.")))
    for _p in (DCT.license, DCT.description, DCT.source):
        g.add((_p, RDF.type, OWL.AnnotationProperty))
    # verify distinct species once
    species = sorted(set(r["species"] for r in rows))
    taxon = {sp: ols_ncbitaxon(sp) for sp in species}
    iso = {"Co-60": "Co60", "Cs-137": "Cs137"}
    GRAY = URIRef("http://qudt.org/vocab/unit/GRAY")
    HAS_UNIT = URIRef("http://qudt.org/schema/qudt/hasUnit")

    def quantity(iri, value, unit):
        g.add((iri, RDF.type, NS.QuantityValue))
        g.add((iri, NS.numericValue, Literal(round(value, 2), datatype=XSD.double)))
        g.add((iri, HAS_UNIT, unit))
        return iri

    for i, r in enumerate(rows):
        t = NS[f"treat_{i:02d}"]; o = NS[f"outcome_{i:02d}"]
        seed = NS[f"{'callus' if r['ff'] == 'FF4' else 'seed'}_{i:02d}"]
        g.add((t, RDF.type, NS.SeedIrradiationTreatment))
        if r["source"] in iso:
            g.add((t, NS.hasSourceIsotope, NS[iso[r["source"]]]))
        if r["dose"] is not None:
            # The corpus records the highest dose each study irradiated, so it is coded as the maximum
            # of the study's dose range; a study irradiates several doses, and hasDose is functional.
            dr = NS[f"doserange_{i:02d}"]; g.add((dr, RDF.type, NS.DoseRange))
            g.add((dr, NS.maxDose, quantity(NS[f"dose_{i:02d}"], r["dose"], GRAY)))
            if r["doses"]:
                g.add((dr, NS.minDose, quantity(NS[f"dosemin_{i:02d}"], min(r["doses"]), GRAY)))
            g.add((t, NS.hasDoseRange, dr))
        if r["rate"] is not None:
            # The category is asserted on the treatment, which is what has a dose rate, and the rate
            # itself is carried as a named quantity, so the assignment can be checked against it.
            g.add((t, NS.hasDoseRateCategory,
                   NS["HighDoseRate" if r["rate"] > RATE_CUT_GY_PER_H else "LowDoseRate"]))
            g.add((t, NS.hasDoseRate, quantity(NS[f"doserate_{i:02d}"], r["rate"],
                                               URIRef("http://qudt.org/vocab/unit/GRAY-PER-HR"))))
        if EP_MAP.get(r["ep"]):
            g.add((o, NS.hasEndpointCategory, NS[EP_MAP[r["ep"]]]))
        # FF4 marks vegetative tissue or an in vitro culture; in this corpus it is rice callus.
        g.add((seed, RDF.type, NS.PlantCallus if r["ff"] == "FF4" else NS.PlantSeed))
        g.add((seed, RDFS.label, Literal(r["species"])))
        if taxon.get(r["species"]):
            # The subject has a taxon: a taxon individual typed with the NCBITaxon class.
            tind = NS["taxon_" + slug(r["species"])]
            g.add((tind, RDF.type, URIRef(taxon[r["species"]])))
            g.add((tind, RDFS.label, Literal(r["species"])))
            g.add((seed, NS.hasTaxon, tind))
        g.add((o, RDF.type, NS.TreatmentOutcome))
        g.add((o, NS.hasTreatment, t)); g.add((o, NS.hasSubject, seed))
        src = STUDY_SOURCES[r["key"]]
        g.add((o, DCT.source, URIRef("https://doi.org/" + src[1]) if src[1] else Literal(src[2])))
        g.add((o, RDFS.label, Literal(f"{r['species']} / {r['source']} / highest dose "
                                      f"{r['dose']:g} Gy ({r['year']})" if r["dose"] is not None
                                      else f"{r['species']} / {r['source']} ({r['year']})")))
        # Each irradiated dose of an added study becomes a DoseAssessment for its taxon, which the
        # reasoner places relative to the windows of that taxon.
        if r["doses"]:
            # the source scored germination; the assessments record that endpoint
            ep = NS[f"endpoint_{r['key']}_germination"]
            g.add((ep, RDF.type, NS.GerminationRate))
            g.add((ep, RDFS.label, Literal(f"germination scored by {r['key']}")))
        for d in r["doses"] or []:
            tind = NS["taxon_" + slug(r["species"])]
            a = NS[f"assessment_{r['key']}_{d:g}Gy"]
            g.add((a, RDF.type, NS.DoseAssessment))
            g.add((a, NS.forTaxon, tind))
            g.add((a, NS.doseGy, Literal(d, datatype=XSD.double)))
            g.add((a, NS.forEndpoint, ep))
            g.add((a, DCT.source, URIRef("https://doi.org/" + src[1])))
            g.add((a, RDFS.label, Literal(f"{r['species']} at {d:g} Gy ({r['key']})")))
    # Every ABox individual is declared owl:NamedIndividual, for tools that read declarations only.
    # An individual is any OnSIR-namespace subject asserted to be of an OnSIR class or of an
    # external class.
    named = set()
    for s_, p_, o_ in g.triples((None, RDF.type, None)):
        if (isinstance(s_, URIRef) and str(s_).startswith(NS) and "#" not in str(s_)
                and isinstance(o_, URIRef) and o_ != OWL.NamedIndividual
                and not str(o_).startswith(str(OWL))):
            named.add(s_)
    for ind in sorted(named):
        g.add((ind, RDF.type, OWL.NamedIndividual))
    print(f"  declared {len(named)} owl:NamedIndividual")

    # ---- stub declarations for the external classes used in logical positions ----
    # The NCBITaxon IRIs type the taxon individuals, a logical position, and NCBITaxon is not
    # imported, so each gets a bare owl:Class declaration and nothing more. Built-in vocabulary
    # and XML Schema datatypes are excluded.
    _LOGICAL = (RDFS.subClassOf, OWL.equivalentClass, OWL.someValuesFrom, OWL.allValuesFrom,
                OWL.onClass, RDFS.domain, RDFS.range)
    _declared = set()
    for _t in (OWL.Class, OWL.ObjectProperty, OWL.DatatypeProperty, OWL.AnnotationProperty,
               OWL.NamedIndividual, RDFS.Datatype):
        _declared |= set(g.subjects(RDF.type, _t))
    _ext = set()
    for _s, _p, _o in g:
        _cands = (_s, _o) if _p in _LOGICAL else ((_o,) if _p == RDF.type else ())
        for _term in _cands:
            if (isinstance(_term, URIRef) and _term not in _declared
                    and not str(_term).startswith((str(NS), str(OWL), str(RDF), str(RDFS), str(XSD)))):
                _ext.add(_term)
    for _e in sorted(_ext):
        g.add((_e, RDF.type, OWL.Class))
    print(f"  external stub declarations emitted: {len(_ext)}")

    g.serialize("OnSIR_abox.ttl", format="turtle")
    # owlready2 does not parse Turtle, so the ABox ships in RDF/XML as well.
    g.serialize("OnSIR_abox.owl", format="xml")
    return g, rows, taxon

def run_cqs(g, rows, taxon):
    Q = lambda s: list(g.query(s, initNs={"onsir": NS, "obo": OBO, "rdfs": RDFS}))
    print("=== ABox coverage ===")
    n = len(rows)
    print(f"  studies: {n};  treatments: {len(set(g.subjects(RDF.type, NS.SeedIrradiationTreatment)))};"
          f"  outcomes: {len(set(g.subjects(RDF.type, NS.TreatmentOutcome)))}")
    aligned = sum(1 for v in taxon.values() if v)
    print(f"  distinct species: {len(taxon)};  NCBITaxon-aligned (exact label): {aligned}")
    print(f"  highest dose populated: {sum(1 for r in rows if r['dose'] is not None)}/{n}")
    print(f"  endpoint category: {sum(1 for r in rows if EP_MAP.get(r['ep']))}/{n}")
    print(f"  source isotope: {sum(1 for r in rows if r['source'] in ('Co-60','Cs-137'))}/{n}")
    print(f"  dose-rate category: {sum(1 for r in rows if r['rate'] is not None)}/{n} "
          f"(only where a numeric rate is reported)")
    windowed = {"Nicotiana tabacum", "Vigna unguiculata", "Trigonella foenum-graecum"}
    hit = sorted({r["key"] for r in rows if r["species"] in windowed})
    print(f"  studies whose taxon carries dose windows: {len(hit)}/{n} {hit}")
    unres = sorted(sp for sp, iri in taxon.items() if not iri)
    print(f"  species not resolved by exact-label matching: {len(unres)}")
    for sp in unres:
        nm = NEAR_MISSES.get(sp)
        print(f"    {sp:26s} -> " + (f"{nm[0]} {nm[1]!r} ({nm[2]})" if nm else "no candidate found"))

    print("\n=== competency questions (SPARQL) ===")
    print("CQ1 sources used:")
    for r in Q("SELECT ?iso (COUNT(?t) AS ?n) WHERE {?t onsir:hasSourceIsotope ?iso} GROUP BY ?iso ORDER BY DESC(?n)"):
        print(f"   {str(r[0]).split('/')[-1]}: {r[1]}")
    MAXD = "?t onsir:hasDoseRange ?r . ?r onsir:maxDose ?q . ?q onsir:numericValue ?v"
    print("CQ2 studies whose highest dose exceeds 500 Gy:")
    r = Q("SELECT (COUNT(?o) AS ?n) WHERE {?o onsir:hasTreatment ?t . " + MAXD + " FILTER(?v > 500)}")
    print(f"   {r[0][0]}")
    print("CQ3 range of the highest dose per study (Gy):")
    r = Q("SELECT (MIN(?v) AS ?lo) (MAX(?v) AS ?hi) (AVG(?v) AS ?mu) WHERE {" + MAXD + "}")
    print(f"   min={float(r[0][0]):.1f}, max={float(r[0][1]):.1f}, mean={float(r[0][2]):.1f}")
    print("CQ4 dose-rate category distribution:")
    for r in Q("SELECT ?c (COUNT(?t) AS ?n) WHERE {?t onsir:hasDoseRateCategory ?c} GROUP BY ?c"):
        print(f"   {str(r[0]).split('/')[-1]}: {r[1]}")
    print("CQ5 subjects linked to an NCBITaxon class via hasTaxon:")
    r = Q("SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE {?s onsir:hasTaxon ?t. ?t a ?tax. "
          "FILTER(STRSTARTS(STR(?tax),'http://purl.obolibrary.org/obo/NCBITaxon_'))}")
    print(f"   {r[0][0]} subjects carry a resolved taxon")
    print("CQ6 mean highest dose by isotope:")
    for r in Q("SELECT ?iso (AVG(?v) AS ?mu) (COUNT(?t) AS ?n) WHERE {?t onsir:hasSourceIsotope ?iso . " + MAXD + "} GROUP BY ?iso"):
        print(f"   {str(r[0]).split('/')[-1]}: mean {float(r[1]):.0f} Gy (n={r[2]})")

if __name__ == "__main__":
    g, rows, taxon = build()
    run_cqs(g, rows, taxon)
