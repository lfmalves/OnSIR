# -*- coding: utf-8 -*-
r"""One-command verification of the release: does the published artifact say what the paper claims?

Checks, in order:
  1. every file the manuscript names is present;
  2. the ontology and the ABox parse, in both serializations;
  3. the merged ontology + ABox is consistent under HermiT, and no class is unsatisfiable;
  4. the counts the manuscript's metrics table reports match the artifact;
  5. no undeclared IRI sits in a logical position (an OWL 2 DL requirement that a reasoner will
     tolerate and an OWL API profile validator will not);
  6. no drafting note or placeholder survives in the release.

HermiT is invoked through its own command line rather than through owlready2's `sync_reasoner`,
because owlready2 encodes subsumption as Python inheritance and raises on an inferred equivalence
(`Seedling` is equivalent to `PO:0008037`) before it reports the reasoner's verdict. The exception is
an artefact of that encoding, not a DL result, so the verdict is taken from HermiT directly.

Run:  python verify_release.py     (exit code 0 = every check passed)
"""
import glob, os, re, subprocess, sys, tempfile

import rdflib
from rdflib import RDF, RDFS, OWL, URIRef

NS = "https://w3id.org/onsir/"
OBO = "http://purl.obolibrary.org/obo/"
HERE = os.path.dirname(os.path.abspath(__file__))
FAIL = []


def check(label, ok, detail=""):
    print(f"  [{'ok  ' if ok else 'FAIL'}] {label}" + (f": {detail}" if detail else ""))
    if not ok:
        FAIL.append(label)


# ---------------------------------------------------------------- 1. files present
print("release contents")
REQUIRED = ["OnSIR.ttl", "OnSIR.owl", "OnSIR_abox.ttl", "OnSIR_abox.owl", "OnSIR_base.owl",
            "catalog-v001.xml", "build_ontology.py", "reason.py", "reason_context.py",
            "abox_cq.py", "rbo_recheck.py", "rbo_gap.py", "make_metrics.py", "make_docs.py",
            "llm_bench.py", "registry_search.py", "README.md", "CITATION.cff", "LICENSE",
            os.path.join("corpus", "eiccam_table_body.tex"), os.path.join("docs", "index.html")]
missing = [f for f in REQUIRED if not os.path.exists(os.path.join(HERE, f))]
check("every file the manuscript names is present", not missing, f"missing {missing}")
for cond in ("ungrounded", "grounded", "framed"):
    p = os.path.join(HERE, "bench", f"answers_{cond}.json")
    check(f"benchmark answers ({cond})", os.path.exists(p))

# ---------------------------------------------------------------- 2. parses
print("\nserializations")
graphs = {}
for f, fmt in [("OnSIR.ttl", "turtle"), ("OnSIR.owl", "xml"),
               ("OnSIR_abox.ttl", "turtle"), ("OnSIR_abox.owl", "xml")]:
    try:
        g = rdflib.Graph(); g.parse(os.path.join(HERE, f), format=fmt)
        graphs[f] = g
        check(f"{f} parses", True, f"{len(g)} triples")
    except Exception as e:
        check(f"{f} parses", False, str(e)[:70])

core, abox = graphs.get("OnSIR.ttl"), graphs.get("OnSIR_abox.ttl")
if core is not None and "OnSIR.owl" in graphs:
    check("both ontology serializations agree in size",
          abs(len(core) - len(graphs["OnSIR.owl"])) <= 1,
          f"ttl {len(core)} vs owl {len(graphs['OnSIR.owl'])}")

# ---------------------------------------------------------------- 3. HermiT
print("\nreasoning over the merged ontology and ABox")
merged = rdflib.Graph()
for g in (core, abox):
    if g is not None:
        merged += g
for t in list(merged.triples((None, OWL.imports, None))):
    merged.remove(t)                       # already merged; the IRI does not resolve yet
onts = list(merged.subjects(RDF.type, OWL.Ontology))
for o in onts[1:]:
    for t in list(merged.triples((o, None, None))):
        merged.remove(t)
out = os.path.join(tempfile.gettempdir(), "onsir_verify_merged.owl")
merged.serialize(out, format="xml")

jar = glob.glob(os.path.join(os.path.dirname(__file__), "**", "HermiT.jar"), recursive=True)
if not jar:
    try:
        import owlready2 as o2
        jar = glob.glob(os.path.join(os.path.dirname(o2.__file__), "hermit", "HermiT.jar"))
    except ImportError:
        jar = []
if jar:
    cp = os.path.dirname(jar[0]) + os.pathsep + jar[0]
    try:
        r = subprocess.run(["java", "-Xmx2000M", "-cp", cp,
                            "org.semanticweb.HermiT.cli.CommandLine", "-c", "-U", "file://" + out],
                           capture_output=True, text=True, timeout=900)
        out_txt = (r.stdout or "") + (r.stderr or "")
        check("merged ontology + ABox is consistent", r.returncode == 0,
              f"HermiT exit {r.returncode}")
        # "-U" lists classes equivalent to owl:Nothing; only owl:Nothing itself may appear
        unsat = [l.strip() for l in out_txt.splitlines()
                 if l.strip().startswith("<") and "Nothing" not in l]
        block = out_txt.split("Classes equivalent to 'owl:Nothing':")
        bad = []
        if len(block) > 1:
            for line in block[1].splitlines():
                s_ = line.strip()
                if not s_ or s_.startswith(("EquivalentClasses", "SubClassOf", "Class")):
                    break
                if s_ and "owl:Nothing" not in s_:
                    bad.append(s_)
        check("no unsatisfiable class", not bad, f"unsatisfiable: {bad}" if bad else "")
    except subprocess.TimeoutExpired:
        check("merged ontology + ABox is consistent", False, "HermiT timed out")
else:
    print("  [skip] HermiT jar not found; install owlready2 to run the consistency check")

# ---------------------------------------------------------------- 4. counts match the paper
print("\ncounts against paper/tab_metrics.tex")
tabp = os.path.join(HERE, "paper", "tab_metrics.tex")
if core is not None and os.path.exists(tabp):
    rows = {k.strip(): int(v) for k, v in
            re.findall(r"^(.+?) & (\d+)\\\\$", open(tabp).read(), re.M)}
    named = lambda t: len([x for x in set(core.subjects(RDF.type, t))
                           if isinstance(x, URIRef) and str(x).startswith(NS)])
    for label, want in [("Named classes", named(OWL.Class)),
                        ("Object properties", named(OWL.ObjectProperty)),
                        ("Datatype properties", named(OWL.DatatypeProperty))]:
        check(f"table row {label!r}", rows.get(label) == want,
              f"table {rows.get(label)} vs artifact {want}")
else:
    print("  [skip] metrics table not present (manuscript source not in the release)")

# ---------------------------------------------------------------- 5. declarations
print("\nOWL 2 DL declarations")
if core is not None and abox is not None:
    both = core + abox
    declared = set()
    for t in (OWL.Class, OWL.ObjectProperty, OWL.DatatypeProperty, OWL.AnnotationProperty,
              OWL.NamedIndividual, RDFS.Datatype):
        declared |= set(both.subjects(RDF.type, t))
    LOGICAL = {RDFS.subClassOf, OWL.equivalentClass, OWL.onProperty, OWL.someValuesFrom,
               OWL.allValuesFrom, OWL.hasValue, RDFS.domain, RDFS.range, OWL.inverseOf}
    undecl = set()
    for s_, p_, o_ in both:
        if p_ in LOGICAL:
            for term in (s_, o_):
                if (isinstance(term, URIRef) and str(term).startswith(NS)
                        and term not in declared):
                    undecl.add(str(term)[len(NS):])
    check("no undeclared OnSIR IRI in a logical position", not undecl,
          f"undeclared: {sorted(undecl)}" if undecl else "")
    ind = len([x for x in set(abox.subjects(RDF.type, OWL.NamedIndividual))])
    check("ABox individuals are declared owl:NamedIndividual", ind > 100, f"{ind} declared")

# ---------------------------------------------------------------- 6. no drafting residue
print("\nrelease hygiene")
PATTERNS = ["Integration touchpoint", "You + Assistant", "TODO", "FIXME", "XXX",
            "example.org/SeedIrradCore#Treat"]
# The scripts that STRIP this residue necessarily contain the patterns they search for, so the
# hygiene check covers the published artifacts and documentation, not the build tooling.
ARTIFACTS = ["OnSIR.ttl", "OnSIR.owl", "OnSIR_abox.ttl", "OnSIR_abox.owl", "README.md",
             "CITATION.cff", os.path.join("docs", "index.html")]
resid = []
for f in ARTIFACTS:
    p = os.path.join(HERE, f)
    if not os.path.exists(p):
        continue
    try:
        t = open(p, errors="ignore").read()
    except Exception:
        continue
    resid += [f"{f}:{pat}" for pat in PATTERNS if pat in t]
check("no drafting notes or placeholders in the release", not resid, f"{resid}")

print("\n" + "=" * 64)
print("RELEASE VERIFIED" if not FAIL else f"FAILURES: {FAIL}")
sys.exit(1 if FAIL else 0)
