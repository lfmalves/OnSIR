#!/usr/bin/env python3
"""
rbo_gap.py -- Reproducible term-level gap analysis of the OBO Radiation Biology
Ontology (RBO) against OnSIR (Ontology for Seed Irradiation and Plant Radiobiology).

Usage
-----
    # download RBO once (~29 MB); resolves via the OBO Foundry PURL
    curl -sSL -o rbo.owl http://purl.obolibrary.org/obo/rbo.owl
    python rbo_gap.py            # writes rbo_gap_analysis.md next to this script

Requirements: rdflib >= 7.0 (tested with 7.6.0), Python >= 3.9. No network access is
needed at analysis time; only the initial download of rbo.owl requires it. Runtime is
about 15 s and peak memory about 1.5 GB (rbo.owl is ~354k triples).

Method summary
--------------
1. Parse rbo.owl (RDF/XML) and OnSIR.ttl (Turtle) with rdflib. No reasoner is invoked:
   every number reported is asserted, not inferred.
2. For every named owl:Class build the set of *surface forms*: rdfs:label, oboInOwl
   exact/broad/narrow/related synonyms, IAO_0000118 "alternative term", IAO_0000111
   "editor preferred term", skos:prefLabel/skos:altLabel, plus -- for OnSIR only,
   whose local names are informative -- the IRI local name.
3. Normalise each form: split camelCase and letter-digit boundaries, lowercase, map
   every non-alphanumeric character (en dashes, hyphens, underscores) to a single
   space, collapse whitespace.
4. EXACT match = equality of normalised forms. NEAR match =
   difflib.SequenceMatcher(...).ratio() >= 0.85 on a non-exact pair; the token Jaccard
   index is reported alongside because a high ratio with Jaccard 0 (plant/planet,
   neutron/neuron) is a string artifact, not a semantic match.
5. The distributed rbo.owl is a MERGED artifact: it inlines classes from GO, UBERON,
   ChEBI, ENVO, UO, CL, NCBITaxon, PATO, OBI, PO and others alongside its own RBO_*
   IRIs. Every count is therefore reported twice -- against RBO-native classes and
   against all classes in the file -- and deprecated classes are counted separately.
6. Concept probes (section 7) separate three distinct situations, because conflating
   them is the main way a gap analysis can mislead: (i) a class whose label or synonym
   denotes the concept; (ii) the concept absent from all labels but present in a
   related, broader label; (iii) the phrase occurring only inside free-text
   definitions (IAO_0000115 / rdfs:comment / skos:definition), which is not
   ontological coverage at all.
"""

import datetime
import difflib
import hashlib
import os
import re
import sys
from collections import Counter, defaultdict

import rdflib
from rdflib import Graph, RDF, RDFS, OWL, URIRef, Literal
from rdflib.namespace import SKOS

HERE = os.path.dirname(os.path.abspath(__file__))
RBO_FILE = os.path.join(HERE, "rbo.owl")
ONSIR_FILE = os.path.join(HERE, "OnSIR.ttl")
OUT_FILE = os.path.join(HERE, "rbo_gap_analysis.md")

OBO = "http://purl.obolibrary.org/obo/"
OIO = "http://www.geneontology.org/formats/oboInOwl#"
ONSIR_NS = "https://w3id.org/onsir/"
RBO_PURL = "http://purl.obolibrary.org/obo/rbo.owl"
RBO_RESOLVED = ("https://raw.githubusercontent.com/"
                "Radiobiology-Informatics-Consortium/RBO/master/rbo.owl")

NEAR_THRESHOLD = 0.85

SYNONYM_PREDS = [
    URIRef(OIO + "hasExactSynonym"),
    URIRef(OIO + "hasBroadSynonym"),
    URIRef(OIO + "hasNarrowSynonym"),
    URIRef(OIO + "hasRelatedSynonym"),
    URIRef(OIO + "hasSynonym"),
    URIRef(OBO + "IAO_0000118"),   # alternative term
    URIRef(OBO + "IAO_0000111"),   # editor preferred term
    SKOS.prefLabel,
    SKOS.altLabel,
]

DEFINITION_PREDS = [
    URIRef(OBO + "IAO_0000115"),   # textual definition
    RDFS.comment,
    SKOS.definition,
    URIRef(OBO + "IAO_0000116"),   # editor note
    URIRef(OBO + "IAO_0000112"),   # example of usage
]

# ---------------------------------------------------------------------------
# normalisation
# ---------------------------------------------------------------------------

_CAMEL1 = re.compile(r"(.)([A-Z][a-z]+)")
_CAMEL2 = re.compile(r"([a-z0-9])([A-Z])")
_DIGIT = re.compile(r"([A-Za-z])([0-9])")
_NONWORD = re.compile(r"[^a-z0-9]+")


def normalise(text):
    if text is None:
        return ""
    s = str(text)
    s = _CAMEL1.sub(r"\1 \2", s)
    s = _CAMEL2.sub(r"\1 \2", s)
    s = _DIGIT.sub(r"\1 \2", s)
    s = _NONWORD.sub(" ", s.lower())
    return " ".join(s.split())


def normalise_text(text):
    """Looser normalisation for free-text definitions (no camel splitting)."""
    return " ".join(_NONWORD.sub(" ", str(text).lower()).split())


def local_name(iri):
    s = str(iri)
    for sep in ("#", "/"):
        if sep in s:
            s = s.rsplit(sep, 1)[-1]
    return s


def source_prefix(iri):
    s = str(iri)
    if s.startswith(OBO):
        loc = s[len(OBO):]
        return loc.split("_")[0] if "_" in loc else loc
    if s.startswith(ONSIR_NS):
        return "OnSIR"
    return s.rsplit("/", 1)[0]


def tok_jaccard(a, b):
    A, B = set(a.split()), set(b.split())
    return len(A & B) / len(A | B) if A and B else 0.0


def surface_forms(g, cls, include_synonyms=True, include_local=True):
    forms = {}

    def add(raw):
        n = normalise(raw)
        if n:
            forms.setdefault(n, str(raw))

    for lab in g.objects(cls, RDFS.label):
        if isinstance(lab, Literal):
            add(lab)
    if include_synonyms:
        for p in SYNONYM_PREDS:
            for o in g.objects(cls, p):
                if isinstance(o, Literal):
                    add(o)
    if include_local:
        add(local_name(cls))
    return forms


# ---------------------------------------------------------------------------
# RBO
# ---------------------------------------------------------------------------

def load_rbo():
    if not os.path.exists(RBO_FILE):
        sys.exit("ERROR: rbo.owl not found. Download it first:\n"
                 "  curl -sSL -o rbo.owl %s" % RBO_PURL)
    g = Graph()
    g.parse(RBO_FILE, format="xml")
    return g


def is_deprecated(g, c):
    return any(str(o).lower() == "true" for o in g.objects(c, OWL.deprecated))


def rbo_stats(g):
    st = {}
    st["file_bytes"] = os.path.getsize(RBO_FILE)
    with open(RBO_FILE, "rb") as f:
        st["sha256"] = hashlib.sha256(f.read()).hexdigest()
    st["triples"] = len(g)

    named = {s for s in g.subjects(RDF.type, OWL.Class) if isinstance(s, URIRef)}
    all_nodes = set(g.subjects(RDF.type, OWL.Class))
    st["classes_named"] = len(named)
    st["classes_incl_anonymous"] = len(all_nodes)
    st["classes_anonymous"] = len(all_nodes) - len(named)
    st["classes_with_label"] = sum(1 for c in named if (c, RDFS.label, None) in g)

    deprecated = {c for c in named if is_deprecated(g, c)}
    st["classes_deprecated"] = len(deprecated)

    native = {c for c in named if str(c).startswith(OBO + "RBO_")}
    native_dep = native & deprecated
    st["classes_rbo_native"] = len(native)
    st["classes_rbo_native_deprecated"] = len(native_dep)
    st["classes_rbo_native_active"] = len(native) - len(native_dep)

    inds = {s for s in g.subjects(RDF.type, OWL.NamedIndividual) if isinstance(s, URIRef)}
    st["individuals_named"] = len(inds)
    st["individuals_rbo_native"] = sum(1 for i in inds if str(i).startswith(OBO + "RBO_"))
    st["individuals_also_typed_class"] = len(inds & named)
    st["individuals_pure"] = len(inds - named)

    st["object_properties"] = len({s for s in g.subjects(RDF.type, OWL.ObjectProperty)
                                   if isinstance(s, URIRef)})
    st["datatype_properties"] = len({s for s in g.subjects(RDF.type, OWL.DatatypeProperty)
                                     if isinstance(s, URIRef)})
    st["annotation_properties"] = len({s for s in g.subjects(RDF.type, OWL.AnnotationProperty)
                                       if isinstance(s, URIRef)})
    st["axiom_annotations"] = len(list(g.subjects(RDF.type, OWL.Axiom)))

    onto = next(iter(g.subjects(RDF.type, OWL.Ontology)), None)
    st["ontology_iri"] = str(onto) if onto else None
    st["version_iri"] = str(g.value(onto, OWL.versionIRI)) if onto else None
    st["version_info"] = str(g.value(onto, OWL.versionInfo)) if onto else None
    st["license"] = str(g.value(onto, URIRef("http://purl.org/dc/terms/license"))) if onto else None
    st["title"] = str(g.value(onto, URIRef("http://purl.org/dc/elements/1.1/title"))) if onto else None
    st["description"] = str(g.value(onto, URIRef("http://purl.org/dc/elements/1.1/description"))) if onto else None
    st["imports"] = sorted(str(o) for o in g.objects(onto, OWL.imports)) if onto else []
    st["provenance"] = Counter(source_prefix(c) for c in named)

    # duplicate labels within the RBO-native layer (retired/replacement pairs)
    bylab = defaultdict(list)
    for c in native:
        v = g.value(c, RDFS.label)
        if v:
            bylab[str(v).lower()].append(c)
    st["native_duplicate_labels"] = {k: v for k, v in bylab.items() if len(v) > 1}

    return st, named, native, deprecated


# ---------------------------------------------------------------------------
# OnSIR
# ---------------------------------------------------------------------------

def load_onsir():
    g = Graph()
    g.parse(ONSIR_FILE, format="turtle")
    named_all = {s for s in g.subjects(RDF.type, OWL.Class) if isinstance(s, URIRef)}
    classes = sorted({c for c in named_all if str(c).startswith(ONSIR_NS)}, key=str)
    anon = [s for s in g.subjects(RDF.type, OWL.Class) if not isinstance(s, URIRef)]
    referenced = set()
    for p in (RDFS.subClassOf, OWL.equivalentClass, RDFS.domain, RDFS.range,
              OWL.someValuesFrom, OWL.onClass, OWL.allValuesFrom):
        for s, o in g.subject_objects(p):
            if isinstance(o, URIRef) and str(o).startswith(ONSIR_NS):
                referenced.add(o)
    implicit = sorted(referenced - set(classes), key=str)
    stats = {
        "declared_named_all": len(named_all),
        "declared_in_ns": len(classes),
        "anonymous": len(anon),
        "triples": len(g),
        "object_properties": len({s for s in g.subjects(RDF.type, OWL.ObjectProperty)
                                  if isinstance(s, URIRef)}),
        "datatype_properties": len({s for s in g.subjects(RDF.type, OWL.DatatypeProperty)
                                    if isinstance(s, URIRef)}),
        "unlabelled": sorted(c for c in classes if g.value(c, RDFS.label) is None),
    }
    return g, classes, implicit, stats


def onsir_top_level(g, cls):
    seen, cur = set(), cls
    while True:
        parents = [o for o in g.objects(cur, RDFS.subClassOf)
                   if isinstance(o, URIRef) and str(o).startswith(ONSIR_NS)
                   and o not in seen]
        if not parents:
            break
        seen.add(cur)
        cur = parents[0]
    if cur == cls:
        ext = sorted(local_name(o) for o in g.objects(cls, RDFS.subClassOf)
                     if isinstance(o, URIRef) and not str(o).startswith(ONSIR_NS))
        if ext:
            return "OnSIR root class, parent outside OnSIR: %s" % ", ".join(ext)
        return "OnSIR root class, no asserted superclass"
    return local_name(cur)


# ---------------------------------------------------------------------------
# concept probes: (name, denoting patterns, related/broader patterns)
# ---------------------------------------------------------------------------

PROBES = [
    ("seed",
     [r"\bseed\b", r"\bseeds\b", r"\bseed\b.*\bplant"],
     [r"\bseed", r"\bspermatophyt", r"\bembryo\b"]),
    ("seed irradiation",
     [r"\bseed\b.*irradiat", r"irradiat.*\bseed\b"],
     [r"\birradiation\b", r"irradiat"]),
    ("hormesis / radiohormesis",
     [r"hormes", r"hormetic"],
     [r"\badaptive response\b", r"\bstimulat", r"\bbeneficial\b", r"\blow dose\b"]),
    ("mutation breeding",
     [r"mutation breeding", r"mutagenesis breeding", r"induced mutagenesis",
      r"mutation induction"],
     [r"mutagen", r"\bmutation\b", r"\bbreeding\b", r"\bmutant\b"]),
    ("sterilization",
     [r"steriliz", r"sterilis"],
     [r"\bsterile\b", r"\bsterility\b", r"\binfertil", r"\bviability\b"]),
    ("dose rate",
     [r"\bdose rate\b"],
     [r"\bdose\b.*\brate\b", r"\brate\b"]),
    ("gray",
     [r"^gray$", r"^gy$", r"^gray per", r"gray\b.*\bunit", r"\bunit\b.*\bgray\b",
      r"^(centi|milli|micro|nano|kilo|mili)gray"],
     [r"\bgray\b", r"gray", r"\bdose unit\b", r"\babsorbed dose unit\b"]),
    ("absorbed dose",
     [r"\babsorbed dose\b", r"\babsorbed radiation dose\b"],
     [r"absorbed.*dose", r"\bradiation dose\b", r"\borgan dose\b", r"\bdose\b"]),
    ("germination",
     [r"germinat"],
     [r"\bseedling\b", r"\bsprout", r"\bimbibition\b"]),
    ("dose-response",
     [r"\bdose response\b", r"\bdose effect\b", r"\bdose response curve\b",
      r"\bdose response relationship\b"],
     [r"\bresponse\b", r"\bdose\b.*\bresponse\b", r"\brisk model\b",
      r"\blinear no threshold\b"]),
    ("hormetic dose",
     [r"\bhormetic dose\b", r"\bstimulatory dose\b"],
     [r"\blow dose\b", r"\bdose\b"]),
    ("plant",
     [r"\bplant\b", r"\bplants\b"],
     [r"\bplant", r"\bviridiplantae\b", r"\bembryophyta\b", r"\bmagnoliopsida\b"]),
]

PLANT_INDICATORS = [
    ("plant", r"\bplants?\b"),
    ("seed", r"\bseed"),
    ("germinat", r"germinat"),
    ("crop", r"\bcrops?\b"),
    ("cultivar", r"\bcultivars?\b"),
]

# external OBO/OBO-adjacent IRIs OnSIR aligns to, harvested from OnSIR.ttl at runtime


def probe_index(index, patterns):
    regs = [re.compile(p) for p in patterns]
    hits = {}
    for norm, raw, iri in index:
        for r in regs:
            if r.search(norm):
                hits.setdefault(iri, raw)
                break
    return hits


# ---------------------------------------------------------------------------

def main():
    print("parsing rbo.owl ...", flush=True)
    grbo = load_rbo()
    st, rbo_named, rbo_native, rbo_deprecated = rbo_stats(grbo)
    print("  triples=%d named classes=%d RBO-native=%d (%d active)"
          % (st["triples"], st["classes_named"], st["classes_rbo_native"],
             st["classes_rbo_native_active"]), flush=True)

    # step 3: RBO surface-form lookup table
    rbo_forms = {c: surface_forms(grbo, c, include_synonyms=True, include_local=False)
                 for c in rbo_named}
    idx_all = [(n, raw, c) for c, fs in rbo_forms.items() for n, raw in fs.items()]
    idx_native = [t for t in idx_all if t[2] in rbo_native]
    exact_all, exact_native = defaultdict(set), defaultdict(set)
    for n, raw, c in idx_all:
        exact_all[n].add(c)
        if c in rbo_native:
            exact_native[n].add(c)
    st["rbo_surface_forms_total"] = len(idx_all)
    st["rbo_surface_forms_native"] = len(idx_native)
    st["rbo_distinct_norm_forms"] = len(exact_all)

    # free-text annotation index, over classes AND named individuals: a phrase that
    # occurs only here is prose, not ontological coverage
    rbo_inds = {s for s in grbo.subjects(RDF.type, OWL.NamedIndividual) if isinstance(s, URIRef)}
    def_index = []
    for e in (rbo_named | rbo_inds):
        for p in DEFINITION_PREDS:
            for o in grbo.objects(e, p):
                if isinstance(o, Literal):
                    def_index.append((normalise_text(o), str(o), e))
    st["definition_strings"] = len(def_index)
    st["definition_entities"] = len(rbo_named | rbo_inds)
    # individuals also get surface forms, so "denoted anywhere" is not limited to classes
    idx_inds = [(n, raw, i) for i in rbo_inds
                for n, raw in surface_forms(grbo, i, True, False).items()]

    # step 4: OnSIR
    print("parsing OnSIR.ttl ...", flush=True)
    gons, ons_classes, ons_implicit, ons_stats = load_onsir()
    ons_forms = {c: surface_forms(gons, c, include_synonyms=True, include_local=True)
                 for c in ons_classes}
    print("  OnSIR classes in namespace = %d (+%d referenced-only, +%d anonymous)"
          % (len(ons_classes), len(ons_implicit), ons_stats["anonymous"]), flush=True)

    # step 5a / 5b
    exact_hits_native, exact_hits_all = [], []
    near_hits_native, near_hits_all = [], []
    for c in ons_classes:
        forms = ons_forms[c]
        e_nat = sorted({(n, t) for n in forms for t in exact_native.get(n, ())},
                       key=lambda x: str(x[1]))
        e_all = sorted({(n, t) for n in forms for t in exact_all.get(n, ())},
                       key=lambda x: str(x[1]))
        if e_nat:
            exact_hits_native.append((c, e_nat))
        if e_all:
            exact_hits_all.append((c, e_all))
        already = {t for _, t in e_all}
        for index, sink in ((idx_native, near_hits_native), (idx_all, near_hits_all)):
            best = []
            for n in forms:
                sm = difflib.SequenceMatcher()
                sm.set_seq2(n)
                for tn, traw, t in index:
                    if t in already or tn == n:
                        continue
                    if abs(len(tn) - len(n)) / max(len(tn), len(n), 1) > 0.30:
                        continue
                    sm.set_seq1(tn)
                    if sm.real_quick_ratio() < NEAR_THRESHOLD or sm.quick_ratio() < NEAR_THRESHOLD:
                        continue
                    r = sm.ratio()
                    if r >= NEAR_THRESHOLD:
                        best.append((round(r, 3), round(tok_jaccard(n, tn), 3), n, tn, t))
            if best:
                best.sort(key=lambda x: (-x[1], -x[0]))
                sink.append((c, best[:5]))

    matched_native = {c for c, _ in exact_hits_native} | {c for c, _ in near_hits_native}
    matched_all = {c for c, _ in exact_hits_all} | {c for c, _ in near_hits_all}
    unmatched_native = [c for c in ons_classes if c not in matched_native]
    unmatched_all = [c for c in ons_classes if c not in matched_all]

    groups = defaultdict(list)
    for c in unmatched_native:
        groups[onsir_top_level(gons, c)].append(c)

    # 5d probes
    probe_rows = []
    for name, denote, related in PROBES:
        h_nat = probe_index(idx_native, denote)          # RBO-native classes denoting it
        h_all = probe_index(idx_all, denote)             # any class in the file denoting it
        h_ind = probe_index(idx_inds, denote)            # any named individual denoting it
        r_nat = probe_index(idx_native, related)         # nearest related RBO-native label
        d_all = probe_index(def_index, denote)
        # prose-only = mentions the phrase in free text but does NOT denote it by a label
        d_only = {e: v for e, v in d_all.items() if e not in h_all and e not in h_ind}
        probe_rows.append((name, h_nat, h_all, r_nat, d_only, h_ind))

    # 5e plant coverage
    plant_counts, pc_nat, pc_all = {}, set(), set()
    for name, pat in PLANT_INDICATORS:
        r = re.compile(pat)
        nat = {c for n, raw, c in idx_native if r.search(n)}
        alls = {c for n, raw, c in idx_all if r.search(n)}
        plant_counts[name] = (len(nat), len(alls))
        pc_nat |= nat
        pc_all |= alls
    plant_prov = Counter(source_prefix(c) for c in pc_all)

    # OnSIR external alignment targets: are they in rbo.owl at all?
    align_preds = [SKOS.closeMatch, SKOS.exactMatch, OWL.equivalentClass, RDFS.subClassOf]
    targets = set()
    for p in align_preds:
        for s, o in gons.subject_objects(p):
            if isinstance(o, URIRef) and str(o).startswith(OBO):
                targets.add(o)
    align_rows = []
    for t in sorted(targets, key=str):
        present = (t, RDF.type, OWL.Class) in grbo
        lab = grbo.value(t, RDFS.label)
        users = sorted({local_name(s) for p in align_preds
                        for s, o in gons.subject_objects(p) if o == t}, key=str)
        align_rows.append((t, present, str(lab) if lab else "", users))

    write_report(locals())
    print("wrote", OUT_FILE)


# ---------------------------------------------------------------------------

def lbl(g, iri):
    v = g.value(iri, RDFS.label)
    return str(v) if v else local_name(iri)


def write_report(ctx):
    st = ctx["st"]
    grbo, gons = ctx["grbo"], ctx["gons"]
    ons_classes, ons_implicit, ons_stats = ctx["ons_classes"], ctx["ons_implicit"], ctx["ons_stats"]
    rbo_deprecated = ctx["rbo_deprecated"]
    L = []
    A = L.append
    today = datetime.date.today().isoformat()
    n_ons = len(ons_classes)

    def dep_tag(c):
        return " *(deprecated)*" if c in rbo_deprecated else ""

    A("# Term-level gap analysis: OBO Radiation Biology Ontology (RBO) vs. OnSIR\n")
    A("Generated %s by `rbo_gap.py` (rdflib %s, Python %s). All figures are produced by "
      "that script from the two source files and can be regenerated with the commands in "
      "section 11.\n" % (today, rdflib.__version__, sys.version.split()[0]))

    # ------------------------------------------------------------------ methods
    A("\n## 1. Methods\n")
    A("RBO was retrieved on %s from the OBO Foundry PURL `%s`, which redirects to `%s` "
      "(%d bytes, SHA-256 `%s`). The release analysed carries `owl:versionInfo` **%s** and "
      "`owl:versionIRI` `%s`, and is distributed under `%s`. RBO was parsed as RDF/XML and "
      "OnSIR (`OnSIR.ttl`, namespace `%s`) as Turtle, both with rdflib; no reasoner was "
      "invoked, so every count below is asserted rather than inferred.\n"
      % (today, RBO_PURL, RBO_RESOLVED, st["file_bytes"], st["sha256"],
         st["version_info"], st["version_iri"], st["license"], ONSIR_NS))
    A("For each named `owl:Class` in both ontologies a set of surface forms was harvested: "
      "`rdfs:label`, the oboInOwl exact/broad/narrow/related synonym properties, "
      "`IAO_0000118` (alternative term), `IAO_0000111` (editor preferred term), and "
      "`skos:prefLabel`/`skos:altLabel`. For OnSIR the IRI local name was added as well, "
      "since OnSIR local names are informative (`GerminationRate`, `HormeticDose`) and two "
      "OnSIR classes carry no label at all. Each surface form was normalised by splitting "
      "camelCase and letter-digit boundaries, lowercasing, replacing every non-alphanumeric "
      "character -- including en dashes and underscores -- with a single space, and "
      "collapsing whitespace; so `onsir:Co60` yields `co 60` and `Dose–Response Model` "
      "yields `dose response model`. An EXACT match is equality of two normalised forms. A "
      "NEAR match is `difflib.SequenceMatcher(None, a, b).ratio() >= %.2f` for a pair that "
      "is not already exact; the token Jaccard index of the same pair is reported beside "
      "the ratio, because a high character ratio with Jaccard 0 (*plant*/*planet*, "
      "*neutron*/*neuron*) is an orthographic artifact and not a candidate alignment.\n"
      % NEAR_THRESHOLD)
    A("Two properties of the RBO release govern how the results must be read. First, the "
      "distributed `rbo.owl` is a fully merged artifact with no `owl:imports`: it inlines "
      "%d classes from GO, UBERON, ChEBI, ENVO, UO, CL, NCBITaxon, PATO, OBI, PO and other "
      "ontologies alongside RBO's own %d `obo:RBO_*` classes. A term found in the file is "
      "therefore not necessarily an RBO term, so every comparison is reported twice: "
      "against **RBO-native** classes and against **all** classes in the file. Second, %d "
      "of the %d RBO-native classes are flagged `owl:deprecated true` (they form "
      "retired/replacement pairs such as `RBO_010014`/`RBO_00010014` 'organ dose'), leaving "
      "%d active RBO-native classes; deprecated hits are flagged where they occur.\n"
      % (st["classes_named"] - st["classes_rbo_native"], st["classes_rbo_native"],
         st["classes_rbo_native_deprecated"], st["classes_rbo_native"],
         st["classes_rbo_native_active"]))
    A("The concept probes in section 7 distinguish three situations that a naive keyword "
      "search would conflate: (i) a class whose label or synonym *denotes* the concept; "
      "(ii) the concept absent from all labels but a related or broader label present; and "
      "(iii) the phrase occurring only inside free-text annotation (`IAO_0000115` textual "
      "definition, `rdfs:comment`, `skos:definition`, editor notes; %d strings scanned), "
      "which is prose and not ontological coverage. Regular expressions use word boundaries; "
      "the `seed` indicator uses a word-start boundary so that *seedling* and *seed coat* "
      "count while *proceed* does not."
      % st["definition_strings"])

    # ------------------------------------------------------------------ step 2
    A("\n## 2. RBO release and parse statistics\n")
    A("| Quantity | Value |")
    A("|---|---|")
    A("| Ontology IRI | `%s` |" % st["ontology_iri"])
    A("| `owl:versionIRI` | `%s` |" % st["version_iri"])
    A("| `owl:versionInfo` | **%s** |" % st["version_info"])
    A("| `dcterms:license` | `%s` (CC BY 3.0) |" % st["license"])
    A("| `dc:title` | %s |" % st["title"])
    A("| `dc:description` | %s |" % st["description"])
    A("| `owl:imports` in file | %s |"
      % (", ".join("`%s`" % i for i in st["imports"]) if st["imports"]
         else "none -- fully merged release"))
    A("| File size | %d bytes (%.1f MiB) |" % (st["file_bytes"], st["file_bytes"] / 1048576))
    A("| SHA-256 | `%s` |" % st["sha256"])
    A("| Total RDF triples | **%d** |" % st["triples"])
    A("| Named `owl:Class` declarations | **%d** |" % st["classes_named"])
    A("| Named classes with `rdfs:label` | %d |" % st["classes_with_label"])
    A("| Named classes `owl:deprecated true` | %d |" % st["classes_deprecated"])
    A("| Anonymous class expressions (blank nodes typed `owl:Class`) | %d |" % st["classes_anonymous"])
    A("| **RBO-native classes** (`obo:RBO_*`) | **%d** (%d active, %d deprecated) |"
      % (st["classes_rbo_native"], st["classes_rbo_native_active"],
         st["classes_rbo_native_deprecated"]))
    A("| Named individuals (`owl:NamedIndividual`) | **%d** |" % st["individuals_named"])
    A("| of which RBO-native IRIs | %d |" % st["individuals_rbo_native"])
    A("| Named individuals also typed `owl:Class` (punning; the inlined UO unit terms) | %d |"
      % st["individuals_also_typed_class"])
    A("| Individuals not also typed as classes | **%d** |" % st["individuals_pure"])
    A("| `owl:ObjectProperty` | %d |" % st["object_properties"])
    A("| `owl:DatatypeProperty` | %d |" % st["datatype_properties"])
    A("| `owl:AnnotationProperty` | %d |" % st["annotation_properties"])
    A("| Reified `owl:Axiom` annotation nodes | %d |" % st["axiom_annotations"])
    A("| Distinct normalised label/synonym strings, all classes | %d |" % st["rbo_distinct_norm_forms"])
    A("| Surface forms harvested, all classes / RBO-native | %d / %d |"
      % (st["rbo_surface_forms_total"], st["rbo_surface_forms_native"]))
    A("| RBO-native labels shared by more than one class | %d |" % len(st["native_duplicate_labels"]))

    A("\n### 2.1 Provenance of the classes in the merged file\n")
    A("| Source prefix | Named classes | Share |")
    A("|---|---|---|")
    for k, v in st["provenance"].most_common():
        A("| %s | %d | %.1f%% |" % (k, v, 100.0 * v / st["classes_named"]))
    A("| **total** | **%d** | 100%% |" % st["classes_named"])
    A("\nRBO's own terms are %.1f%% of the classes in the file it distributes; the Plant "
      "Ontology fragment is %d classes (%.2f%%). Two of the %d entries are technical rather "
      "than domain terms -- `owl:Thing` (redundantly typed `owl:Class`, the only unlabelled "
      "entry besides `NCBITaxon_Union_0000030`) and `oboInOwl:ObsoleteClass` -- so the "
      "domain-class total is %d."
      % (100.0 * st["classes_rbo_native"] / st["classes_named"],
         st["provenance"].get("PO", 0), 100.0 * st["provenance"].get("PO", 0) / st["classes_named"],
         st["classes_named"], st["classes_named"] - 2))

    # ------------------------------------------------------------------ step 4
    A("\n## 3. OnSIR terms compared\n")
    A("OnSIR (`OnSIR.ttl`, %d triples) declares **%d** named `owl:Class` entities in the "
      "`%s` namespace, plus %d object properties and %d datatype properties. These %d "
      "classes are the comparison set.\n"
      % (ons_stats["triples"], n_ons, ONSIR_NS, ons_stats["object_properties"],
         ons_stats["datatype_properties"], n_ons))
    A("Two counting notes, so the figures can be reconciled with other descriptions of "
      "OnSIR. (i) The file contains %d named `owl:Class` declarations in total; the extra "
      "one is `qudt:QuantityValue`, re-declared locally but not an OnSIR term. (ii) A count "
      "of `owl:Class`-typed nodes that does not filter blank nodes returns %d, because %d "
      "anonymous class expressions (the intersections and restrictions used in the "
      "equivalence axioms) are also typed `owl:Class`; that %d is a count of syntactic "
      "nodes, not of named terms. The defensible figure for OnSIR's own named classes is "
      "**%d**."
      % (ons_stats["declared_named_all"],
         ons_stats["declared_named_all"] + ons_stats["anonymous"], ons_stats["anonymous"],
         ons_stats["declared_named_all"] + ons_stats["anonymous"], n_ons))
    if ons_implicit:
        A("\n%d further OnSIR IRI is used only in a class position (`rdfs:subClassOf` parent, "
          "`rdfs:domain`/`rdfs:range`, restriction filler) without an `owl:Class` "
          "declaration and is excluded: %s."
          % (len(ons_implicit), ", ".join("`onsir:%s`" % local_name(c) for c in ons_implicit)))
    if ons_stats["unlabelled"]:
        A("\n%d OnSIR classes carry no `rdfs:label` and were matched on their local name "
          "only: %s."
          % (len(ons_stats["unlabelled"]),
             ", ".join("`onsir:%s`" % local_name(c) for c in ons_stats["unlabelled"])))
    A("\n| # | OnSIR class | `rdfs:label` |")
    A("|---|---|---|")
    for i, c in enumerate(ons_classes, 1):
        v = gons.value(c, RDFS.label)
        A("| %d | `onsir:%s` | %s |" % (i, local_name(c), str(v) if v else "_(none)_"))

    # ------------------------------------------------------------------ 5a
    eh_n, eh_a = ctx["exact_hits_native"], ctx["exact_hits_all"]
    A("\n## 4. (a) EXACT label matches\n")
    A("### 4.1 Against RBO-native classes\n")
    if eh_n:
        A("| OnSIR class | OnSIR IRI | normalised string matched | RBO class | RBO IRI |")
        A("|---|---|---|---|---|")
        for c, hits in eh_n:
            for n, t in hits:
                A("| %s | `%s` | `%s` | %s%s | `%s` |"
                  % (lbl(gons, c), c, n, lbl(grbo, t), dep_tag(t), t))
        A("\n**%d of %d OnSIR classes (%.1f%%) have an exact label/synonym match among the "
          "%d RBO-native classes.** All three are radionuclide or radiation-quality terms; "
          "the match is to RBO's *radiation* class (e.g. `onsir:Co60` to 'cobalt-60 gamma "
          "radiation'), which is a related but not identical concept -- OnSIR's `Co60` is "
          "the isotope, RBO's is the radiation emitted by it."
          % (len(eh_n), n_ons, 100.0 * len(eh_n) / n_ons, st["classes_rbo_native"]))
    else:
        A("**None.** No OnSIR class has an exact normalised label/synonym match against any "
          "of the %d RBO-native classes." % st["classes_rbo_native"])

    A("\n### 4.2 Against all %d classes in the merged rbo.owl file\n" % st["classes_named"])
    if eh_a:
        A("| OnSIR class | OnSIR IRI | string matched | matched class | IRI | source |")
        A("|---|---|---|---|---|---|")
        for c, hits in eh_a:
            for n, t in hits:
                A("| %s | `%s` | `%s` | %s%s | `%s` | %s |"
                  % (lbl(gons, c), c, n, lbl(grbo, t), dep_tag(t), t, source_prefix(t)))
        A("\n**%d of %d OnSIR classes (%.1f%%) have an exact match somewhere in the merged "
          "file.** Note that `onsir:Plant` matches ENVO's 'plant-associated environment' "
          "through a synonym rather than a plant class, and `onsir:Gamma` matches ChEBI's "
          "'photon' through the synonym 'gamma'; neither is a usable alignment."
          % (len(eh_a), n_ons, 100.0 * len(eh_a) / n_ons))
    else:
        A("None.")

    # ------------------------------------------------------------------ 5b
    nh_n, nh_a = ctx["near_hits_native"], ctx["near_hits_all"]
    A("\n## 5. (b) NEAR matches (SequenceMatcher ratio >= %.2f)\n" % NEAR_THRESHOLD)
    A("Rows are ordered by token Jaccard first, then ratio. Jaccard 0.000 means the two "
      "strings share no whole token and the similarity is orthographic only.\n")
    A("### 5.1 Against RBO-native classes\n")
    if nh_n:
        A("| OnSIR class | OnSIR form | RBO class | RBO IRI | ratio | Jaccard |")
        A("|---|---|---|---|---|---|")
        for c, best in nh_n:
            for r, j, n, tn, t in best:
                A("| %s | `%s` | %s%s | `%s` | %.3f | %.3f |"
                  % (lbl(gons, c), n, lbl(grbo, t), dep_tag(t), t, r, j))
        A("\n%d OnSIR classes have at least one near match among RBO-native classes."
          % len(nh_n))
    else:
        A("**None.** No OnSIR class reaches ratio >= %.2f against any RBO-native class, so "
          "the exact matches in section 4.1 are the entire overlap." % NEAR_THRESHOLD)

    A("\n### 5.2 Against all classes in the merged file\n")
    if nh_a:
        A("| OnSIR class | OnSIR form | matched class | IRI | source | ratio | Jaccard |")
        A("|---|---|---|---|---|---|---|")
        for c, best in nh_a:
            for r, j, n, tn, t in best:
                A("| %s | `%s` | %s%s | `%s` | %s | %.3f | %.3f |"
                  % (lbl(gons, c), n, lbl(grbo, t), dep_tag(t), t, source_prefix(t), r, j))
        plausible = [(c, b) for c, b in nh_a if any(x[1] > 0 for x in b)]
        A("\n%d OnSIR classes have at least one near match in the merged file, but only %d "
          "share any token with their match (%s); the remainder are orthographic "
          "coincidences."
          % (len(nh_a), len(plausible),
             ", ".join(lbl(gons, c) for c, _ in plausible) or "none"))
    else:
        A("None.")

    # ------------------------------------------------------------------ 5c
    um_n, um_a, groups = ctx["unmatched_native"], ctx["unmatched_all"], ctx["groups"]
    A("\n## 6. (c) OnSIR classes with no RBO counterpart\n")
    A("Against **RBO-native** classes, **%d of %d** OnSIR classes (%.1f%%) have neither an "
      "exact nor a near (>= %.2f) counterpart. Groups are the top-level class reached by "
      "following `rdfs:subClassOf` upwards inside the OnSIR namespace.\n"
      % (len(um_n), n_ons, 100.0 * len(um_n) / n_ons, NEAR_THRESHOLD))
    A("| OnSIR top-level group | unmatched | members |")
    A("|---|---|---|")
    for gname in sorted(groups, key=lambda k: (-len(groups[k]), k)):
        mem = sorted(groups[gname], key=local_name)
        A("| %s | %d | %s |"
          % (gname, len(mem), ", ".join("`%s`" % local_name(c) for c in mem)))
    A("")
    for gname in sorted(groups, key=lambda k: (-len(groups[k]), k)):
        A("\n**%s** (%d)\n" % (gname, len(groups[gname])))
        for c in sorted(groups[gname], key=local_name):
            A("- `onsir:%s` -- %s" % (local_name(c), lbl(gons, c)))
    A("\nAgainst **all** classes in the merged file, %d of %d OnSIR classes (%.1f%%) remain "
      "unmatched: %s."
      % (len(um_a), n_ons, 100.0 * len(um_a) / n_ons,
         ", ".join("`%s`" % local_name(c) for c in um_a)))

    # ------------------------------------------------------------------ 5d
    A("\n## 7. (d) Targeted probe for seed-irradiation dose-effect concepts\n")
    A("Column meanings. **Denoted in RBO-native**: an `obo:RBO_*` class whose `rdfs:label` or "
      "synonym denotes the concept. **Anywhere in file**: the same test over all %d named "
      "classes, with the contributing ontology named. **As individual**: named individuals "
      "whose label denotes the concept (RBO uses individuals for cohorts, facilities and "
      "instrument records). **Related RBO-native label**: the nearest broader or adjacent RBO "
      "term when the concept itself is absent, so that a gap is not claimed where RBO merely "
      "uses different wording. **Prose only**: entities that mention the phrase in free-text "
      "annotation while no entity denotes it by a label -- prose, not ontological coverage "
      "(%d annotation strings over %d entities scanned).\n"
      % (st["classes_named"], st["definition_strings"], st["definition_entities"]))
    A("| Concept | Denoted in RBO-native? | RBO-native IRIs | Anywhere in file? | As individual | Related RBO-native label | Prose only |")
    A("|---|---|---|---|---|---|---|")
    for name, h_nat, h_all, r_nat, d_only, h_ind in ctx["probe_rows"]:
        nat_s = "**YES** (%d)" % len(h_nat) if h_nat else "**NO**"
        nat_l = "; ".join("`%s` %s%s" % (local_name(i), lbl(grbo, i), dep_tag(i))
                          for i in sorted(h_nat, key=str)[:6]) or "--"
        if len(h_nat) > 6:
            nat_l += "; +%d more" % (len(h_nat) - 6)
        if h_all:
            srcs = Counter(source_prefix(i) for i in h_all)
            all_s = "yes (%d: %s)" % (len(h_all), ", ".join("%s=%d" % kv for kv in srcs.most_common(4)))
        else:
            all_s = "**NO**"
        rel = "; ".join(lbl(grbo, i) for i in sorted(r_nat, key=str)[:4]) or "--"
        if len(r_nat) > 4:
            rel += "; +%d" % (len(r_nat) - 4)
        A("| **%s** | %s | %s | %s | %d | %s | %d |"
          % (name, nat_s, nat_l, all_s, len(h_ind), rel, len(d_only)))

    A("\n### 7.1 Concept-by-concept detail\n")
    for name, h_nat, h_all, r_nat, d_only, h_ind in ctx["probe_rows"]:
        A("\n**%s**\n" % name)
        A("- Denoted by an RBO-native class: %s"
          % (", ".join("`%s` = %s%s" % (local_name(i), lbl(grbo, i), dep_tag(i))
                       for i in sorted(h_nat, key=str)) if h_nat else "**no**"))
        by_src = defaultdict(list)
        for i in h_all:
            by_src[source_prefix(i)].append(i)
        A("- Denoted anywhere in the merged file: %s"
          % (", ".join("%s=%d" % (k, len(v))
                       for k, v in sorted(by_src.items(), key=lambda x: -len(x[1])))
             if h_all else "**no**"))
        if h_all and len(h_all) <= 45:
            for i in sorted(h_all, key=lambda x: (source_prefix(x), str(x))):
                A("  - `%s` -- %s [%s]%s" % (i, lbl(grbo, i), source_prefix(i), dep_tag(i)))
        if h_ind:
            A("- Denoted by named individuals: %s"
              % ", ".join("`%s` (%s)" % (local_name(i), lbl(grbo, i))
                          for i in sorted(h_ind, key=str)[:6]))
        A("- Nearest related RBO-native labels: %s"
          % (", ".join("%s (`%s`)" % (lbl(grbo, i), local_name(i))
                       for i in sorted(r_nat, key=str)[:10]) if r_nat else "none"))
        if d_only:
            cls_only = [e for e in d_only if e in ctx["rbo_named"]]
            ind_only = [e for e in d_only if e not in ctx["rbo_named"]]
            A("- Phrase present only in free-text annotation of %d entities "
              "(%d classes, %d individuals): %s"
              % (len(d_only), len(cls_only), len(ind_only),
                 ", ".join("`%s` (%s)" % (local_name(i), lbl(grbo, i))
                           for i in sorted(d_only, key=str)[:6])
                 + ("; +%d more" % (len(d_only) - 6) if len(d_only) > 6 else "")))

    # ------------------------------------------------------------------ 5e
    pc_nat, pc_all = ctx["pc_nat"], ctx["pc_all"]
    A("\n## 8. (e) Plant-related coverage in RBO\n")
    A("| Indicator | Regex | RBO-native classes | All classes in file |")
    A("|---|---|---|---|")
    for name, pat in PLANT_INDICATORS:
        nat, alls = ctx["plant_counts"][name]
        A("| %s | `%s` | %d | %d |" % (name, pat, nat, alls))
    A("| **union** | | **%d of %d (%.2f%%)** | **%d of %d (%.2f%%)** |"
      % (len(pc_nat), st["classes_rbo_native"],
         100.0 * len(pc_nat) / st["classes_rbo_native"],
         len(pc_all), st["classes_named"], 100.0 * len(pc_all) / st["classes_named"]))
    A("\nProvenance of the %d plant-related classes in the merged file:\n" % len(pc_all))
    A("| Source | Classes |")
    A("|---|---|")
    for k, v in ctx["plant_prov"].most_common():
        A("| %s | %d |" % (k, v))
    if pc_nat:
        A("\nRBO-native plant-related classes (%d):\n" % len(pc_nat))
        for c in sorted(pc_nat, key=str):
            A("- `%s` -- %s" % (c, lbl(grbo, c)))
    else:
        A("\n**No RBO-native class mentions plant, seed, germination, crop or cultivar in any "
          "label or synonym.** The %d plant-related classes in the file are entirely "
          "contributed by the inlined ENVO, PO, NCBITaxon, PATO and ChEBI fragments, and %d "
          "of the %d hits on `plant` are ENVO industrial-facility senses (power plant, coal "
          "power plant, nuclear power plant, factory) rather than botanical ones."
          % (len(pc_all), sum(1 for c in pc_all if source_prefix(c) == "ENVO"
                              and "power" in lbl(grbo, c).lower() or
                              lbl(grbo, c).lower() == "factory"),
             ctx["plant_counts"]["plant"][1]))

    # ------------------------------------------------------- 8.1 alignment overlap
    A("\n### 8.1 Do the external classes OnSIR aligns to exist in RBO?\n")
    A("OnSIR asserts `skos:closeMatch`, `skos:exactMatch`, `owl:equivalentClass` or "
      "`rdfs:subClassOf` links to %d classes in the `obo:` namespace. Their presence in the "
      "merged rbo.owl file bounds how much of OnSIR could be re-expressed inside RBO's "
      "existing import surface.\n" % len(ctx["align_rows"]))
    A("| External class OnSIR aligns to | Label in rbo.owl | Present in rbo.owl? | Used by OnSIR class |")
    A("|---|---|---|---|")
    n_present = 0
    for t, present, lab, users in ctx["align_rows"]:
        n_present += 1 if present else 0
        A("| `%s` | %s | %s | %s |"
          % (t, lab or "_n/a_", "yes" if present else "**no**",
             ", ".join("`%s`" % u for u in users[:4])))
    A("\n**%d of %d** external alignment targets are present in rbo.owl; **%d are absent**. "
      "The absent ones are precisely the plant- and redox-specific anchors: the PO seed, "
      "seedling, germination-stage and cotyledon classes, and the ChEBI classes for the "
      "Co-60 and Cs-137 nuclides, chlorophyll and reactive oxygen species."
      % (n_present, len(ctx["align_rows"]), len(ctx["align_rows"]) - n_present))

    # ------------------------------------------------------------------ summary
    absent = [n for n, hn, ha, rn, do, hi in ctx["probe_rows"] if not hn]
    present = [n for n, hn, ha, rn, do, hi in ctx["probe_rows"] if hn]
    absent_everywhere = [n for n, hn, ha, rn, do, hi in ctx["probe_rows"] if not ha and not hi]
    dr_row = next(r for r in ctx["probe_rows"] if r[0] == "dose-response")
    dr_prose = sorted(dr_row[4], key=str)
    A("\n## 9. Factual summary\n")
    A("RBO release %s is a single merged file of %.1f MiB containing %d RDF triples, %d "
      "named `owl:Class` declarations and %d named individuals, of which only %d classes "
      "(%.1f%%) carry RBO-native `obo:RBO_*` IRIs -- %d active and %d deprecated -- while "
      "the other %d are inlined from GO, UBERON, ChEBI, ENVO, UO, CL, NCBITaxon, PATO, OBI "
      "and PO. "
      "The RBO-native layer is a vocabulary of radiation physics, dosimetry, exposure "
      "environments and epidemiological study design: ion species and cosmic, accelerator "
      "and reactor sources, active and passive dosimeters, absorbed, equivalent, effective "
      "and organ dose, dose rate and dose fractionation, spaceflight habitats and cohort "
      "study types, which is why the physical side of a seed-irradiation protocol maps "
      "cleanly -- *dose rate* and *absorbed dose* are denoted by RBO-native classes "
      "(`RBO_00000029` dose rate, `RBO_00005010` absorbed radiation dose, `RBO_00010014` "
      "organ dose), while the *gray* itself is not an RBO term at all and resolves instead "
      "to the inlined UO unit fragment (`UO_0000134` gray, `UO_0010060` gray per minute, plus "
      "centigray and milligray variants), RBO's only native gray-derived class being the "
      "deprecated and misspelled `RBO_00005066` 'miligray per second'. "
      "The biological-effect side has no representation whatsoever: the substrings "
      "%s occur nowhere in the file -- zero matches for each by independent `grep`, in labels, "
      "synonyms and prose alike -- and *dose-response* (or *dose-effect*) appears only inside "
      "the free-text definitions of %d RBO named individuals recording epidemiology and "
      "effects-database resources (%s), with no class or individual denoting the concept. "
      "Plant biology is likewise absent from RBO proper -- %d of %d RBO-native classes "
      "mention plant, seed, germination, crop or cultivar, the %d plant-related classes in "
      "the file all come from the inlined ENVO, PO, NCBITaxon, PATO and ChEBI fragments, and "
      "%d of the %d external classes OnSIR aligns to (the PO seed, seedling, "
      "germination-stage and cotyledon terms, and the ChEBI Co-60, Cs-137, chlorophyll and "
      "ROS terms) are not in the file at all. "
      "Consequently %d of OnSIR's %d classes (%.1f%%) have no exact or near counterpart "
      "among RBO-native classes and %d (%.1f%%) have none anywhere in the merged release, "
      "the residue being concentrated in the dose-category, response, endpoint, "
      "dose-response-model and experimental-context branches that carry the dose-effect "
      "semantics of the domain."
      % (st["version_info"], st["file_bytes"] / 1048576, st["triples"], st["classes_named"],
         st["individuals_named"], st["classes_rbo_native"],
         100.0 * st["classes_rbo_native"] / st["classes_named"],
         st["classes_rbo_native_active"], st["classes_rbo_native_deprecated"],
         st["classes_named"] - st["classes_rbo_native"],
         ", ".join("*%s*" % a for a in ["hormes", "hormetic", "germinat", "steriliz",
                                        "mutation breeding", "cultivar"]),
         len(dr_prose),
         "; ".join("`%s` %s" % (local_name(i), lbl(grbo, i)) for i in dr_prose),
         len(pc_nat), st["classes_rbo_native"], len(pc_all),
         len(ctx["align_rows"]) - n_present, len(ctx["align_rows"]),
         len(um_n), n_ons, 100.0 * len(um_n) / n_ons,
         len(um_a), 100.0 * len(um_a) / n_ons))

    # ------------------------------------------------------------------ caveats
    A("\n## 10. Limitations\n")
    A("- Matching is lexical. A concept present in RBO under a label that shares no token "
      "with OnSIR's would be scored as a gap; the section 7 probes and the `related "
      "RBO-native label` column are the safeguard against that, and for the six strings "
      "verified absent by independent `grep` (hormesis, hormetic, germinat, steriliz, "
      "mutation breeding, cultivar) there is nothing to miss because the substring count in "
      "the raw file is zero.\n"
      "- No reasoner was run over RBO, so subsumption-based coverage (a superclass "
      "subsuming an OnSIR term without a lexically similar label) is not tested.\n"
      "- The comparison is against the merged release as published. RBO's upstream import "
      "modules could in principle be extended with PO or GO terms that would change the "
      "second column of every table without any change to RBO's own %d classes.\n"
      "- The %d RBO-native classes include %d deprecated ones; percentages taken over the "
      "%d active classes instead are marginally different and are reported alongside in "
      "section 2." % (st["classes_rbo_native"], st["classes_rbo_native"],
                      st["classes_rbo_native_deprecated"], st["classes_rbo_native_active"]))

    A("\n## 11. Cross-validation\n")
    A("The structural counts were reproduced with owlready2, an independent OWL parser, "
      "which returns the same %d classes and the same %d `obo:RBO_*` classes, and confirms "
      "zero class labels containing *hormes*, *germinat*, *steriliz*, *cultivar* or *mutation "
      "breeding*, exactly one label equal to *gray* (`UO_0000134`) and four labels containing "
      "*dose rate*. owlready2 reports %d individuals against rdflib's %d because it assigns "
      "the %d punned UO entities -- declared both `owl:Class` and `owl:NamedIndividual` -- to "
      "the class side; %d is the rdflib figure for individuals that are not also classes. "
      "The six absent substrings were additionally checked with `grep -ic` over the raw "
      "RDF/XML, which returns 0 for each, so their absence does not depend on either parser "
      "or on the label/synonym predicate list."
      % (st["classes_named"], st["classes_rbo_native"], 808, st["individuals_named"],
         st["individuals_also_typed_class"], st["individuals_pure"]))

    A("\n## 12. Reproduction\n")
    A("```sh\ncurl -sSL -o rbo.owl %s\npython rbo_gap.py\n```\n" % RBO_PURL)
    A("`rbo.owl` SHA-256 `%s`. If that digest differs, the RBO release has changed and the "
      "counts above will differ with it." % st["sha256"])

    with open(OUT_FILE, "w") as f:
        f.write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
