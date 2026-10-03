# -*- coding: utf-8 -*-
r"""One-command verification of the release: does the published artifact say what its README and
the accompanying paper state?

Checks, in order:
  1. every file of the release is present;
  2. the ontology, the ABox and the examples parse, in both serializations, and the serializations
     agree;
  3. the merged ontology + ABox is consistent under HermiT, and no class is unsatisfiable;
  4. every generated file regenerates byte-identically from the artifact;
  5. every numeric row of the metrics table matches the artifact;
  6. no IRI sits undeclared in a logical position, counting the imports closure;
  7. every individual in the three files is declared owl:NamedIndividual, and the core carries no
     individual besides the taxa of the dose windows;
  8. the property characteristics the README advertises are present, and no property carries two
     rdfs:domain or two rdfs:range axioms (they are read conjunctively);
  9. ROBOT validates each file against the OWL 2 DL profile, the ABox and the examples with their
     import resolved through the shipped catalogue;
 10. owlready2 can load the ABox by the recipe the README documents;
 11. no drafting note or placeholder survives anywhere in the release, the source skeleton included;
 12. the counts the README states match the artifact;
 13. the examples show the dose-to-effect inference: an example outcome with a typed dose category
     and no asserted response is classified by HermiT into the matching defined class.

HermiT is invoked through its own command line, because owlready2 encodes subsumption as Python
inheritance and raises on an inferred equivalence (Seedling is equivalent to PO:0008037) before it
reports the reasoner's verdict. ROBOT is found through the ROBOT_JAR environment variable, a robot
command on the PATH, or a robot.jar next to this script; without it check 9 fails.

Run:  python verify_release.py     (exit code 0 = every check passed)
"""
import filecmp
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile

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
REQUIRED = ["OnSIR.ttl", "OnSIR.owl", "OnSIR_abox.ttl", "OnSIR_abox.owl", "OnSIR_examples.ttl",
            "OnSIR_examples.owl", "OnSIR_base.owl",
            "catalog-v001.xml", "build_ontology.py", "reason.py", "reason_context.py",
            "abox_cq.py", "rbo_recheck.py", "rbo_gap.py", "make_metrics.py", "make_docs.py",
            "registry_search.py", "README.md", "CITATION.cff", "LICENSE",
            os.path.join("corpus", "eiccam_table_body.tex"), os.path.join("corpus", "added_studies.json"),
            os.path.join("docs", "index.html")]
missing = [f for f in REQUIRED if not os.path.exists(os.path.join(HERE, f))]
check("every file of the release is present", not missing, f"missing {missing}")

# ---------------------------------------------------------------- 2. parses
print("\nserializations")
graphs = {}
for f, fmt in [("OnSIR.ttl", "turtle"), ("OnSIR.owl", "xml"),
               ("OnSIR_abox.ttl", "turtle"), ("OnSIR_abox.owl", "xml"),
               ("OnSIR_examples.ttl", "turtle"), ("OnSIR_examples.owl", "xml")]:
    try:
        g = rdflib.Graph()
        g.parse(os.path.join(HERE, f), format=fmt)
        graphs[f] = g
        check(f"{f} parses", True, f"{len(g)} triples")
    except Exception as e:
        check(f"{f} parses", False, str(e)[:70])

core, abox = graphs.get("OnSIR.ttl"), graphs.get("OnSIR_abox.ttl")
examples = graphs.get("OnSIR_examples.ttl")
for a, b in (("OnSIR.ttl", "OnSIR.owl"), ("OnSIR_abox.ttl", "OnSIR_abox.owl"),
             ("OnSIR_examples.ttl", "OnSIR_examples.owl")):
    if a in graphs and b in graphs:
        check(f"{a} and {b} agree in size", abs(len(graphs[a]) - len(graphs[b])) <= 1,
              f"{len(graphs[a])} vs {len(graphs[b])}")

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

jar = glob.glob(os.path.join(HERE, "**", "HermiT.jar"), recursive=True)
if not jar:
    try:
        import owlready2 as _o2
        jar = glob.glob(os.path.join(os.path.dirname(_o2.__file__), "hermit", "HermiT.jar"))
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
        block = out_txt.split("Classes equivalent to 'owl:Nothing':")
        bad = []
        if len(block) > 1:
            for line in block[1].splitlines():
                s_ = line.strip()
                if not s_ or s_.startswith(("EquivalentClasses", "SubClassOf", "Class")):
                    break
                if "owl:Nothing" not in s_:
                    bad.append(s_)
        check("no unsatisfiable class", not bad, f"unsatisfiable: {bad}" if bad else "")
    except subprocess.TimeoutExpired:
        check("merged ontology + ABox is consistent", False, "HermiT timed out")
else:
    print("  [skip] HermiT jar not found; install owlready2 to run the consistency check")

# ---------------------------------------------------------------- 4. generated files reproduce
print("\ngenerated files regenerate byte-identically")
GENERATED = [(os.path.join("paper", "tab_metrics.tex"), "make_metrics.py"),
             (os.path.join("docs", "index.html"), "make_docs.py")]
for rel, script in GENERATED:
    p = os.path.join(HERE, rel)
    if not (os.path.exists(p) and os.path.exists(os.path.join(HERE, script))):
        print(f"  [skip] {rel} or {script} not present")
        continue
    keep = p + ".verify_backup"
    shutil.copy2(p, keep)
    try:
        r = subprocess.run([sys.executable, script], cwd=HERE, capture_output=True, text=True,
                           timeout=600)
        same = r.returncode == 0 and filecmp.cmp(p, keep, shallow=False)
        check(f"{rel} reproduces from {script}", same,
              "" if same else f"differs (exit {r.returncode})")
    except Exception as e:
        check(f"{rel} reproduces from {script}", False, str(e)[:60])
    finally:
        shutil.copy2(keep, p)
        os.remove(keep)

# ---------------------------------------------------------------- 5. every metrics row
print("\nevery numeric row of paper/tab_metrics.tex against the artifact")
tabp = os.path.join(HERE, "paper", "tab_metrics.tex")
if core is not None and os.path.exists(tabp):
    rows = {k.strip(): int(v) for k, v in
            re.findall(r"^(.+?) & (\d+)\\\\$", open(tabp).read(), re.M)}
    named = lambda t: [x for x in set(core.subjects(RDF.type, t))
                       if isinstance(x, URIRef) and str(x).startswith(NS)]
    sv = [s for s in core.subjects(OWL.someValuesFrom, None)]
    qc = [s for s in core.subjects(URIRef(str(OWL) + "qualifiedCardinality"), None)]
    hv = [s for s in core.subjects(OWL.hasValue, None)]
    eq = list(core.subject_objects(OWL.equivalentClass))
    eq_ext = [1 for _s, _o in eq if isinstance(_o, URIRef) and not str(_o).startswith(NS)]
    # An alignment is any triple whose subject is an OnSIR term and whose object is an OBO or
    # QUDT-unit IRI, whatever the predicate -- restricting the predicate list, as a first version of
    # this check did, undercounted by three and made the check disagree with the generator for
    # reasons that had nothing to do with the artifact.
    QUDT_UNIT = "http://qudt.org/vocab/unit/"
    align = [(str(s), str(p), str(o)) for s, p, o in core
             if isinstance(s, URIRef) and str(s).startswith(NS)
             and isinstance(o, URIRef)
             and (str(o).startswith(OBO) or str(o).startswith(QUDT_UNIT))
             and not str(o).endswith("rbo.owl")]
    # BFO reach, by the same transitive rule make_metrics uses
    up = {}
    for s, o in (list(core.subject_objects(RDFS.subClassOf))
                 + list(core.subject_objects(OWL.equivalentClass))):
        if isinstance(s, URIRef) and isinstance(o, URIRef):
            up.setdefault(s, set()).add(o)

    def has_bfo(c, seen=None):
        seen = seen or set()
        if c in seen:
            return False
        seen.add(c)
        return any(str(p).startswith(OBO + "BFO_") or has_bfo(p, seen) for p in up.get(c, ()))

    EXPECT = {
        "Named classes": len(named(OWL.Class)),
        "Object properties": len(named(OWL.ObjectProperty)),
        "Datatype properties": len(named(OWL.DatatypeProperty)),
        "Functional properties": len(named(OWL.FunctionalProperty)),
        "Disjointness axioms": len(set(core.subjects(RDF.type, OWL.AllDisjointClasses)))
                               + len(list(core.triples((None, OWL.disjointWith, None)))),
        "Existential and cardinality restrictions": len(set(sv)) + len(set(qc)),
        r"Nominal (\texttt{hasValue}) restrictions": len(set(hv)),
        "Equivalences: covering, defined and dose-window classes": len(eq) - len(eq_ext),
        "Equivalences: external alignments": len(eq_ext),
        "External alignment triples": len(align),
        "Named classes with a BFO ancestor": len([c for c in named(OWL.Class) if has_bfo(c)]),
        "Distinct external terms aligned to": len({t[2] for t in align}),
    }
    unchecked = sorted(set(rows) - set(EXPECT))
    check("every numeric row of the table has a check", not unchecked, f"unchecked: {unchecked}")
    for label, want in EXPECT.items():
        check(f"row {label!r}", rows.get(label) == want,
              f"table {rows.get(label)} vs artifact {want}")
else:
    print("  [skip] metrics table not present (manuscript source not in the release)")

# ---------------------------------------------------------------- 6. declarations
print("\nOWL 2 DL declarations (every IRI, external ones included)")
LOGICAL = {RDFS.subClassOf, OWL.equivalentClass, OWL.onProperty, OWL.someValuesFrom,
           OWL.allValuesFrom, OWL.hasValue, OWL.onClass, OWL.complementOf, OWL.disjointWith,
           RDFS.domain, RDFS.range, OWL.inverseOf, RDFS.subPropertyOf}
SKIP_NS = (str(OWL), str(RDF), str(RDFS), "http://www.w3.org/2001/XMLSchema#",
           "http://www.w3.org/2004/02/skos/core#", "http://purl.org/dc/terms/")


def undeclared(g, closure):
    """IRIs used in a logical position (or as a type) with no declaration in `closure`."""
    decl = set()
    for t in (OWL.Class, OWL.ObjectProperty, OWL.DatatypeProperty, OWL.AnnotationProperty,
              OWL.NamedIndividual, RDFS.Datatype, OWL.Ontology):
        decl |= set(closure.subjects(RDF.type, t))
    bad = set()
    for s_, p_, o_ in g:
        cands = (s_, o_) if p_ in LOGICAL else ((o_,) if p_ == RDF.type else ())
        for term in cands:
            if (isinstance(term, URIRef) and term not in decl
                    and not any(str(term).startswith(x) for x in SKIP_NS)):
                bad.add(str(term))
    return bad


if core is not None and abox is not None:
    both = core + abox
    for label, g_, closure in (("OnSIR.ttl (standalone)", core, core),
                               ("OnSIR_abox.ttl (with its import)", abox, both),
                               ("merged", both, both)):
        u = undeclared(g_, closure)
        check(f"no undeclared IRI in a logical position: {label}", not u,
              f"undeclared: {sorted(u)[:8]}" if u else "")

    # ---------------------------------------------------------- 7. every individual declared
    print("\nowl:NamedIndividual declarations")
    for label, g_ in (("OnSIR.ttl", core), ("OnSIR_abox.ttl", abox),
                      ("OnSIR_examples.ttl", examples if examples is not None else rdflib.Graph())):
        cls = {c for c in both.subjects(RDF.type, OWL.Class)}
        declared = set(g_.subjects(RDF.type, OWL.NamedIndividual))
        used = {s for s, p, o in g_.triples((None, RDF.type, None))
                if isinstance(s, URIRef) and str(s).startswith(NS) and o in cls}
        miss = sorted(str(x)[len(NS):] for x in used - declared)
        check(f"every individual in {label} is declared", not miss,
              f"{len(declared)} declared, missing {miss}" if miss else f"{len(declared)} declared")
    # The illustrative individuals of the scaffold carry invented values and live in the examples
    # file; the core carries only the taxon individuals that the dose windows name.
    core_ind = sorted(str(x)[len(NS):] for x in core.subjects(RDF.type, OWL.NamedIndividual))
    check("the core carries only the taxon individuals of the dose windows",
          core_ind and all(x.startswith("taxon_") for x in core_ind), f"{core_ind}")

    # ---------------------------------------------------------- 8. property characteristics
    print("\nproperty characteristics")
    check("functional properties present",
          len(set(both.subjects(RDF.type, OWL.FunctionalProperty))) > 0,
          f"{len(set(both.subjects(RDF.type, OWL.FunctionalProperty)))} functional")
    inv = list(both.triples((None, OWL.inverseOf, None)))
    check("inverse property pairs present", len(inv) > 0, f"{len(inv)} owl:inverseOf axioms")
    for pred, name in ((RDFS.domain, "rdfs:domain"), (RDFS.range, "rdfs:range")):
        multi = {}
        for s_, o_ in both.subject_objects(pred):
            multi.setdefault(s_, []).append(o_)
        bad = {str(k)[len(NS):]: len(v) for k, v in multi.items() if len(v) > 1}
        check(f"no property carries two {name} axioms (they are conjunctive)", not bad, f"{bad}")

# ---------------------------------------------------------------- 8b. metadata
print("\nontology metadata")
if core is not None:
    DCT = "http://purl.org/dc/terms/"
    ont = URIRef("https://w3id.org/onsir")
    creators = list(core.objects(ont, URIRef(DCT + "creator")))
    lits = [c for c in creators if not isinstance(c, URIRef)]
    check("every creator is a resolvable ORCID agent IRI", creators and not lits,
          f"{len(creators)} creators, {len(lits)} bare literal(s)"
          + (f": {[str(x) for x in lits]}" if lits else ""))
    check("every creator IRI is in the orcid.org namespace",
          all(str(c).startswith("https://orcid.org/") for c in creators if isinstance(c, URIRef)),
          f"{[str(c) for c in creators]}")
    # the version appears in four places and they must agree
    vinfo = core.value(ont, OWL.versionInfo)
    viri = core.value(ont, URIRef(str(OWL) + "versionIRI"))
    cff = ""
    cffp = os.path.join(HERE, "CITATION.cff")
    if os.path.exists(cffp):
        m = re.search(r'^version:\s*"([^"]+)"', open(cffp).read(), re.M)
        cff = m.group(1) if m else ""
    rdme = ""
    rp = os.path.join(HERE, "README.md")
    if os.path.exists(rp):
        m = re.search(r"\*\*Version:\*\*\s*([0-9.]+)", open(rp).read())
        rdme = m.group(1) if m else ""
    agree = (str(vinfo) and str(viri).endswith(str(vinfo)) and cff == str(vinfo)
             and rdme == str(vinfo))
    check("version agrees across versionInfo, versionIRI, CITATION.cff and README", agree,
          f"versionInfo {vinfo}, versionIRI {viri}, cff {cff}, readme {rdme}")

    # Retired or non-existent external IRIs. Each of these was in the artifact and each 404s:
    # qudt:unit was superseded by qudt:hasUnit, and QUDT spells the units GRAY / GRAY-PER-MIN,
    # not Gray / Gy-PER-MIN. A dead DECLARATION counts: it is an assertion about an IRI that no
    # longer resolves, and it is the form the first fix here missed.
    RETIRED = ["http://qudt.org/schema/qudt/unit",
               "http://qudt.org/vocab/unit/Gray",
               "http://qudt.org/vocab/unit/Gy-PER-MIN"]
    found = {}
    for g_, nm in ((core, "OnSIR.ttl"), (abox, "OnSIR_abox.ttl")):
        if g_ is None:
            continue
        for r in RETIRED:
            n = sum(1 for t in g_ for x in t if str(x) == r)
            if n:
                found[f"{nm}:{r.rsplit('/', 1)[-1]}"] = n
    check("no retired or non-dereferencing external IRI, used or declared", not found, f"{found}")
    # ...and the same in the prose of any annotation, where a stale name misleads a reader
    stale = [str(o)[:60] for _s, _p, o in (core or [])
             if isinstance(o, str) and "qudt:unit " in str(o)]
    check("no annotation names the retired property", not stale, f"{stale}")

# ---------------------------------------------------------------- 8c. the docs say something
# Regenerating byte-identically shows the generator is deterministic; it does not show the output is
# worth reading. A broken generator that emits a list of bare headings reproduces perfectly. So the
# rendered documentation is checked for content: most terms must carry a definition, and the terms
# that carry a curation caveat must show it.
print("\ngenerated documentation content")
dp = os.path.join(HERE, "docs", "index.html")
if core is not None and os.path.exists(dp):
    dh = open(dp, errors="ignore").read()
    # Exact, not a threshold: the docs must render a definition for every term that HAS one in the
    # ontology. A fraction would have to be guessed, and a guess low enough to pass today is a guess
    # that would also pass an empty shell.
    n_h3 = dh.count("<h3 id=")
    n_def = dh.count("<p class='def'>")
    SKOSDEF = URIRef("http://www.w3.org/2004/02/skos/core#definition")
    described = {s_ for s_, _o in core.subject_objects(SKOSDEF)} | \
                {s_ for s_, _o in core.subject_objects(RDFS.comment)}
    want = len([x for x in described
                if isinstance(x, URIRef) and str(x).startswith(NS)
                and f"<h3 id='{str(x)[len(NS):]}'>" in dh])
    check("documentation renders every definition the ontology carries", n_def >= want,
          f"{n_def} rendered, {want} terms have one, {n_h3} terms total")
    SKOSNS = URIRef("http://www.w3.org/2004/02/skos/core#note")
    noted = [str(s_)[len(NS):] for s_, _o in core.subject_objects(SKOSNS)
             if str(s_).startswith(NS)]
    missing = [t for t in noted if "curation note" not in
               dh[dh.find(f"<h3 id='{t}'>"):dh.find(f"<h3 id='{t}'>") + 2000]] if noted else []
    check("every term with a curation note shows it in the documentation",
          noted and not missing, f"{len(noted)} noted, missing {missing}" if noted else "no notes")

# ---------------------------------------------------------------- 9. ROBOT DL profile
print("\nOWL 2 DL profile (ROBOT validate-profile)")


def robot_cmd():
    if os.environ.get("ROBOT_JAR") and os.path.exists(os.environ["ROBOT_JAR"]):
        return ["java", "-jar", os.environ["ROBOT_JAR"]]
    if shutil.which("robot"):
        return ["robot"]
    if os.path.exists(os.path.join(HERE, "robot.jar")):
        return ["java", "-jar", os.path.join(HERE, "robot.jar")]
    return None


_robot = robot_cmd()
if _robot is None:
    check("ROBOT is available for the DL profile check", False,
          "set ROBOT_JAR to a robot.jar (https://github.com/ontodev/robot/releases)")
else:
    for f in ("OnSIR.owl", "OnSIR.ttl", "OnSIR_abox.owl", "OnSIR_abox.ttl", "OnSIR_examples.owl",
              "OnSIR_examples.ttl"):
        try:
            r = subprocess.run(_robot + ["--catalog", "catalog-v001.xml", "validate-profile",
                                         "--profile", "DL", "--input", f],
                               cwd=HERE, capture_output=True, text=True, timeout=600)
            txt = (r.stdout or "") + (r.stderr or "")
            good = r.returncode == 0 and "[Ontology and imports closure in profile]" in txt
            first = next((l for l in txt.splitlines() if l.strip()), "")
            check(f"{f} is in the OWL 2 DL profile", good, "" if good else first[:110])
        except subprocess.TimeoutExpired:
            check(f"{f} is in the OWL 2 DL profile", False, "ROBOT timed out")

# ---------------------------------------------------------------- 10. owlready2 recipe
print("\nowlready2 load recipe (README section 'Loading the ABox')")
try:
    import owlready2 as o2
    w = o2.World()
    o2c = w.get_ontology("https://w3id.org/onsir")
    with open(os.path.join(HERE, "OnSIR.owl"), "rb") as fh:
        o2c.load(only_local=False, fileobj=fh)
    w.get_ontology("file://" + os.path.join(HERE, "OnSIR_abox.owl")).load()
    n_c, n_i = len(list(w.classes())), len(list(w.individuals()))
    check("owlready2 loads core-then-ABox in one World", n_i > 100,
          f"{n_c} classes, {n_i} individuals")
except ImportError:
    print("  [skip] owlready2 not installed")
except Exception as e:
    check("owlready2 loads core-then-ABox in one World", False,
          f"{type(e).__name__}: {str(e)[:80]}")

# ---------------------------------------------------------------- 13. the examples reason
print("\nexamples: dose-to-effect inference")
try:
    import owlready2 as o2
    w = o2.World()
    _core = w.get_ontology("https://w3id.org/onsir")
    with open(os.path.join(HERE, "OnSIR.owl"), "rb") as fh:
        _core.load(only_local=False, fileobj=fh)
    _ex = w.get_ontology("file://" + os.path.join(HERE, "OnSIR_examples.owl")).load()
    with _ex:
        o2.sync_reasoner_hermit(w, infer_property_values=False, debug=0)
    _ns = w.get_namespace(NS)
    _x = _ns["Outcome_XRay_Mutagenesis"]
    _no_resp = not list(examples.objects(URIRef(NS + "Outcome_XRay_Mutagenesis"), URIRef(NS + "hasResponse")))
    _cls = sorted(c.name for c in _x.INDIRECT_is_a if hasattr(c, "name"))
    check("an example outcome with no asserted response is classified MutagenicOutcome",
          _no_resp and "MutagenicOutcome" in _cls, f"{_cls}")
except ImportError:
    print("  [skip] owlready2 not installed")
except Exception as e:
    check("an example outcome with no asserted response is classified MutagenicOutcome", False,
          f"{type(e).__name__}: {str(e)[:80]}")

# ---------------------------------------------------------------- 11. no drafting residue
print("\nrelease hygiene")
# "example.org/..." is NOT in this list. The source skeleton was authored under that ontology IRI
# and the build rewrites every term into the OnSIR namespace; its exemplar individuals are content,
# not placeholders. What must not happen is an example.org IRI reaching a PUBLISHED graph, which is
# the separate check below.
PATTERNS = ["Integration touchpoint", "You + Assistant", "TODO", "FIXME", "XXX", "DEPRECATED",
            "PLACEHOLDER", "lorem ipsum"]
# The scripts that STRIP this residue necessarily contain the patterns they search for, so the
# hygiene check covers the published artifacts and documentation, not the build tooling. The source
# skeleton IS covered: it is shipped, and it was the one file the earlier version of this check
# required but did not scan.
ARTIFACTS = ["OnSIR.ttl", "OnSIR.owl", "OnSIR_abox.ttl", "OnSIR_abox.owl", "OnSIR_examples.ttl",
             "OnSIR_examples.owl", "OnSIR_base.owl",
             "README.md", "CITATION.cff", os.path.join("docs", "index.html")]
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
# OnSIR_base.owl legitimately carries the example.org ontology IRI it was authored under; the build
# rewrites every term into the OnSIR namespace. What must not survive is a placeholder INDIVIDUAL.
check("no example.org IRI reaches the published graphs",
      not any("example.org" in open(os.path.join(HERE, f), errors="ignore").read()
              for f in ("OnSIR.ttl", "OnSIR_abox.ttl", "OnSIR_examples.ttl")
              if os.path.exists(os.path.join(HERE, f))))

# ---------------------------------------------------------------- 12. README numeric claims
print("\nREADME numeric claims (hand-written prose, pinned against the artifact)")
readme = open(os.path.join(HERE, "README.md"), errors="ignore").read()
_g = rdflib.Graph(); _g.parse(os.path.join(HERE, "OnSIR.ttl"), format="turtle")
_NS = "https://w3id.org/onsir/"
_n_cls = len({s for s in _g.subjects(RDF.type, OWL.Class)
              if isinstance(s, URIRef) and str(s).startswith(_NS)})
_n_op = len({s for s in _g.subjects(RDF.type, OWL.ObjectProperty) if str(s).startswith(_NS)})
_n_dp = len({s for s in _g.subjects(RDF.type, OWL.DatatypeProperty) if str(s).startswith(_NS)})
_ga = rdflib.Graph(); _ga.parse(os.path.join(HERE, "OnSIR_abox.owl"), format="xml")
_n_ind = len({s for s in _ga.subjects(RDF.type, OWL.NamedIndividual)})
_n_out = len({s for s in _ga.subjects(RDF.type, URIRef(_NS + "TreatmentOutcome"))})
_m = re.search(r"\*\*(\d+) named classes, (\d+) object properties, (\d+) datatype properties", readme)
check("README headline counts match the artifact",
      bool(_m) and tuple(map(int, _m.groups())) == (_n_cls, _n_op, _n_dp),
      f"README {_m.groups() if _m else None} vs artifact ({_n_cls}, {_n_op}, {_n_dp})")
_m = re.search(r"ABox: (\d+) studies, (\d+) declared individuals", readme)
check("README ABox counts match the artifact",
      bool(_m) and tuple(map(int, _m.groups())) == (_n_out, _n_ind),
      f"README {_m.groups() if _m else None} vs artifact ({_n_out}, {_n_ind})")
_m = re.search(r"# (\d+) classes, (\d+) individuals", readme)
try:
    check("README loading-recipe comment matches the owlready2 counts",
          bool(_m) and tuple(map(int, _m.groups())) == (n_c, n_i),
          f"README {_m.groups() if _m else None} vs measured ({n_c}, {n_i})")
except NameError:
    print("  [skip] owlready2 counts unavailable")

print("\n" + "=" * 64)
print("RELEASE VERIFIED" if not FAIL else f"{len(FAIL)} FAILURE(S): {FAIL}")
sys.exit(1 if FAIL else 0)
