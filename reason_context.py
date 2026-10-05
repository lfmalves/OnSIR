# -*- coding: utf-8 -*-
r"""Taxon-relative dose classification: the reasoner places a numeric dose relative to the statistics
reported for a taxon, an endpoint and a stage, from the assessment alone. A dose assessment names the
plant structure the dose is applied to (hasSubject), whose taxon is stated with RO:0002162 in taxon
some NCBITaxon class, the endpoint (forEndpoint) and the stage (atStage) its source scored, and the
dose (doseGy). The placement says where the dose lies on the dose axis of that taxon and endpoint.

Eight demonstrations, written to reason_context.json. HermiT runs through owlready2 (HermiT 1.3.8) and,
for (E), (H) and a check of (D), through ROBOT (the OWL API, HermiT 1.4), which is the reference where the
two disagree; ROBOT is found through the ROBOT_JAR environment variable or a robot.jar next to this script.
  (A) one dose for every taxon with windows, each assessed for the endpoint and stage of its window:
      280 Gy lies inside the doses tested by the cowpea, wheat, fenugreek and lablab sources.
  (B) the two sides of each boundary: Nicotiana tabacum at 4, 5, 15 and 16 Gy (both band ends are
      included in the band), and Vigna unguiculata at 150, 151, 249 and 250 Gy, where the observations
      of the source bracket the LD50 between 150 and 250 Gy: the window below the LD50 includes 150 Gy,
      and the doses above it and below 250 Gy fall in no window.
  (C) an encoding conflict, on a constructed taxon. A record codes a favourable band of 250 to 300 Gy
      and an LD50 of 273 Gy for the same endpoint and stage, the pattern of the wheat breeding range of
      Chakraborty et al. 2023, whose recommended 250 to 300 Gy brackets their LD50 estimates of 272.71
      and 278.61 Gy. Classification alone, with no dose recorded, finds the probe class of the band
      unsatisfiable; an assessment inside the overlap makes the ontology inconsistent, and assessments
      outside it do not. The same record with an LD50 of 310 Gy leaves the probe satisfiable.
  (D) the doses the ABox records: every DoseAssessment of OnSIR_abox.owl, placed relative to the
      windows of its taxon, endpoint and stage. The germination doses of Lumorh et al. 2025 (cowpea)
      meet a cowpea window for seedling survival at flowering, and fall in none of them. The positions
      are checked against HermiT through ROBOT.
  (E) the datatype of the literal: one cowpea dose written as xsd:double, xsd:decimal, xsd:integer and
      xsd:float, at 280 Gy and at the window boundary of 250 Gy, under HermiT through ROBOT. The range of
      doseGy and the windows are a union over xsd:decimal and xsd:double; xsd:integer lies in the
      decimal value space, and xsd:float in neither, so a float dose violates the range of doseGy and
      the ontology is inconsistent. HermiT 1.3.8 through owlready2 accepts the float dose and places it
      in no window; that result is recorded as well.
  (F) a subtaxon: an assessment of Vigna unguiculata subsp. unguiculata (NCBITaxon:3920, a subclass of
      NCBITaxon:3917 in NCBITaxon) falls in the windows of the species.
  (G) the endpoint and the stage condition the window: the same cowpea dose assessed for seedling
      survival at the flowering stage, for germination at the germination stage, and for seedling
      survival at the early seedling stage.
  (H) the probes of the release, one for each endpoint and stage of a favourable band, under HermiT
      through ROBOT: all are satisfiable; an LD50 window at or above 10 Gy added for one endpoint and stage
      of the tobacco band makes the probe of that endpoint and stage unsatisfiable and no other, for each
      of the ten; the same window from 16 Gy, above the band, leaves every probe satisfiable.
"""
import ast
import copy
import json
import os
import subprocess
import tempfile

import owlready2 as o2
import rdflib
from rdflib import BNode, Literal, Namespace, OWL, RDF, RDFS, URIRef, XSD

HERE = os.path.dirname(os.path.abspath(__file__))
NSU = "https://w3id.org/onsir/"
N = Namespace(NSU)
OBO = Namespace("http://purl.obolibrary.org/obo/")
IN_TAXON = OBO.RO_0002162
CATS = ["BelowReportedFavourableBand", "WithinReportedFavourableBand", "AboveReportedFavourableBand",
        "BelowReportedLD50", "AtOrAboveReportedLD50"]


def literal(path, name):
    tree = ast.parse(open(path, encoding="utf-8").read())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise KeyError(name)


TW = literal(os.path.join(HERE, "build_ontology.py"), "TAXON_WINDOWS")
TWD = {w["taxon"]: w for w in TW}


def core():
    g = rdflib.Graph(); g.parse(os.path.join(HERE, "OnSIR.owl"))
    return g


def some(g, ind, prop, filler):
    r = BNode()
    g.add((r, RDF.type, OWL.Restriction)); g.add((r, OWL.onProperty, prop))
    g.add((r, OWL.someValuesFrom, filler)); g.add((ind, RDF.type, r))


def assessment(g, name, taxon_iri, endpoint, stage, dose, dtype=XSD.double, lexical=None):
    """A dose assessment with its own subject (in the taxon), endpoint and stage individuals."""
    a, s, e, st = N[name], N[name + "_subject"], N[name + "_endpoint"], N[name + "_stage"]
    for x in (a, s, e, st):
        g.add((x, RDF.type, OWL.NamedIndividual))
    g.add((a, RDF.type, N.DoseAssessment))
    g.add((s, RDF.type, N.PlantSeed)); some(g, s, IN_TAXON, taxon_iri)
    g.add((e, RDF.type, N[endpoint])); g.add((st, RDF.type, N[stage]))
    g.add((a, N.hasSubject, s)); g.add((a, N.forEndpoint, e)); g.add((a, N.atStage, st))
    g.add((a, N.doseGy, Literal(lexical if lexical is not None else float(dose), datatype=dtype)))
    return a


def taxon_iri(taxon):
    return OBO["NCBITaxon_" + TWD[taxon]["ncbi"]]


def reason(graph):
    """Serialize an rdflib graph and run HermiT over it; returns (World, consistent)."""
    tmp = os.path.join(tempfile.mkdtemp(), "onsir_context.owl")
    graph.serialize(tmp, format="xml")
    w = o2.World()
    onto = w.get_ontology("file://" + tmp).load()
    try:
        with onto:
            o2.sync_reasoner_hermit(w, infer_property_values=False, debug=0)
        return w, True
    except o2.OwlReadyInconsistentOntologyError:
        return w, False


def positions(w, name):
    ind = w.get_namespace(NSU)[name]
    return sorted(c.name for c in ind.INDIRECT_is_a if getattr(c, "name", None) in CATS)


def windows(w, name):
    ind = w.get_namespace(NSU)[name]
    return sorted(c.name for c in ind.INDIRECT_is_a if getattr(c, "name", "").endswith("Dose")
                  and "_" in getattr(c, "name", ""))


def unsatisfiable(w):
    return sorted(c.name for c in w.inconsistent_classes() if getattr(c, "name", None))


# ---- HermiT through ROBOT (the OWL API) ----
def robot_jar():
    for cand in (os.environ.get("ROBOT_JAR"), os.path.join(HERE, "robot.jar"),
                 os.path.join(HERE, "..", "tools", "robot.jar")):
        if cand and os.path.exists(cand):
            return cand
    raise SystemExit("ROBOT not found: set ROBOT_JAR to a robot.jar (https://github.com/ontodev/robot/releases)")


def robot_reason(graph, classify=False):
    """Run HermiT through ROBOT over an rdflib graph. Returns (consistent, unsatisfiable named classes,
    the graph with the inferred class assertions, direct and indirect, or None)."""
    d = tempfile.mkdtemp()
    f, o = os.path.join(d, "in.owl"), os.path.join(d, "out.owl")
    graph.serialize(f, format="xml")
    cmd = ["java", "-jar", robot_jar(), "reason", "--reasoner", "HermiT", "--input", f]
    if classify:
        cmd += ["--axiom-generators", "ClassAssertion", "--include-indirect", "true"]
    r = subprocess.run(cmd + ["--output", o], capture_output=True, text=True, timeout=900)
    log = r.stdout + r.stderr
    unsat = sorted(line.split("unsatisfiable:", 1)[1].strip()[len(NSU):] for line in log.splitlines()
                   if "unsatisfiable:" in line and NSU in line)
    consistent = "inconsistent" not in log.lower()
    out = None
    if r.returncode == 0:
        out = rdflib.Graph(); out.parse(o, format="xml")
    else:
        assert unsat or not consistent, log[-800:]
    return consistent, unsat, out


def robot_positions(gi, name):
    return sorted(c for c in CATS if (N[name], RDF.type, N[c]) in gi)


def hermit_versions():
    """The HermiT builds the two routes run: the jar owlready2 ships, and the one inside robot.jar."""
    import glob
    import zipfile
    jar = glob.glob(os.path.join(os.path.dirname(o2.__file__), "hermit", "HermiT.jar"))[0]
    man = zipfile.ZipFile(jar).read("META-INF/MANIFEST.MF").decode()
    v_o2 = next(l.split(":", 1)[1].strip() for l in man.splitlines() if l.startswith("Implementation-Version"))
    pom = zipfile.ZipFile(robot_jar()).read(
        "META-INF/maven/net.sourceforge.owlapi/org.semanticweb.hermit/pom.properties").decode()
    v_r = next(l.split("=", 1)[1].strip() for l in pom.splitlines() if l.startswith("version="))
    return dict(owlready2=v_o2, robot=v_r)


def classify(cases):
    """cases: list of (name, taxon IRI, endpoint, stage, dose). Returns {name: (positions, windows)}."""
    g = core()
    for name, tx, ep, st, d in cases:
        assessment(g, name, tx, ep, st, d)
    w, ok = reason(g)
    assert ok
    return {name: (positions(w, name), windows(w, name)) for name, *_ in cases}


# ---- (C) helpers: a constructed record with its own windows, built as build_ontology.py builds them ----
def rlist(g, items):
    head = BNode(); cur = head
    for i, it in enumerate(items):
        g.add((cur, RDF.first, it))
        if i < len(items) - 1:
            nxt = BNode(); g.add((cur, RDF.rest, nxt)); cur = nxt
        else:
            g.add((cur, RDF.rest, RDF.nil))
    return head


def drange(g, lo, hi, lo_ex, hi_ex, dts=(XSD.decimal, XSD.double)):
    parts = []
    for dt in dts:
        dr = BNode(); g.add((dr, RDF.type, RDFS.Datatype)); g.add((dr, OWL.onDatatype, dt))
        fs = []
        if lo is not None:
            f = BNode(); g.add((f, XSD.minExclusive if lo_ex else XSD.minInclusive, Literal(lo, datatype=dt))); fs.append(f)
        if hi is not None:
            f = BNode(); g.add((f, XSD.maxExclusive if hi_ex else XSD.maxInclusive, Literal(hi, datatype=dt))); fs.append(f)
        g.add((dr, OWL.withRestrictions, rlist(g, fs))); parts.append(dr)
    if len(parts) == 1:
        return parts[0]
    u = BNode(); g.add((u, RDF.type, RDFS.Datatype)); g.add((u, OWL.unionOf, rlist(g, parts)))
    return u


def restriction(g, prop, filler):
    r = BNode(); g.add((r, RDF.type, OWL.Restriction)); g.add((r, OWL.onProperty, prop))
    g.add((r, OWL.someValuesFrom, filler)); return r


def define(g, name, tx, endpoint, stage, rng, parent=None):
    c = N[name]; g.add((c, RDF.type, OWL.Class))
    members = [N.DoseAssessment, restriction(g, N.hasSubject, restriction(g, IN_TAXON, tx)),
               restriction(g, N.forEndpoint, N[endpoint]), restriction(g, N.atStage, N[stage]),
               restriction(g, N.doseGy, rng)]
    eq = BNode(); g.add((c, OWL.equivalentClass, eq)); g.add((eq, RDF.type, OWL.Class))
    g.add((eq, OWL.intersectionOf, rlist(g, members)))
    if parent:
        g.add((c, RDFS.subClassOf, N[parent]))


def conflict_record(ld50):
    """A constructed taxon with a favourable band of 250 to 300 Gy and an LD50, for seedling survival
    in the early seedling stage, with the probe class of its band."""
    g = core()
    tx = N["test_ConflictTaxon"]
    g.add((tx, RDF.type, OWL.Class))
    ep, st = "SeedlingSurvival", "EarlySeedlingStage"
    define(g, "test_Conflict_WithinFavourableBandDose", tx, ep, st, drange(g, 250.0, 300.0, False, False),
           "WithinReportedFavourableBand")
    define(g, "test_Conflict_AtOrAboveLD50Dose", tx, ep, st, drange(g, ld50, None, False, False),
           "AtOrAboveReportedLD50")
    define(g, "test_Conflict_BandUpperEndProbe", tx, ep, st, drange(g, 300.0, 300.0, False, False, (XSD.double,)))
    return g, tx, ep, st


if __name__ == "__main__":
    OUT = {"hermit": hermit_versions()}
    print(f"HermiT through owlready2 {OUT['hermit']['owlready2']}, through ROBOT {OUT['hermit']['robot']}")
    DEMO_A_DOSE = 280.0
    print(f"=== (A) one dose, every taxon with windows: {DEMO_A_DOSE:g} Gy ===")
    cases = [(f"a_{i}", taxon_iri(w["taxon"]), w["endpoints"][0], w["stages"][0], DEMO_A_DOSE)
             for i, w in enumerate(TW)]
    res = classify(cases)
    OUT["A"] = []
    for (name, *_), w in zip(cases, TW):
        pos, win = res[name]
        inside = w["tested"][0] <= DEMO_A_DOSE <= w["tested"][1]
        OUT["A"].append(dict(taxon=w["taxon"], endpoint=w["endpoints"][0], stage=w["stages"][0],
                             dose=DEMO_A_DOSE, classes=pos, windows=win, tested=list(w["tested"]),
                             inside_tested=inside))
        print(f"  {w['taxon']:26s} {w['tag']:20s} -> {pos or ['(none)']}{'' if inside else '  (outside the tested doses)'}")

    print("\n=== (B) the two sides of each boundary ===")
    walk = [("Nicotiana tabacum", 4.0), ("Nicotiana tabacum", 5.0), ("Nicotiana tabacum", 15.0),
            ("Nicotiana tabacum", 16.0), ("Vigna unguiculata", 150.0), ("Vigna unguiculata", 151.0),
            ("Vigna unguiculata", 249.0), ("Vigna unguiculata", 250.0)]
    cases = [(f"b_{i}", taxon_iri(t), TWD[t]["endpoints"][0], TWD[t]["stages"][0], d) for i, (t, d) in enumerate(walk)]
    res = classify(cases)
    OUT["B"] = []
    for (name, *_), (t, d) in zip(cases, walk):
        OUT["B"].append(dict(taxon=t, dose=d, classes=res[name][0]))
        print(f"  {t:26s} @ {d:6.1f} Gy -> {res[name][0] or ['(none)']}")

    print("\n=== (C) a coded favourable band that reaches the coded LD50 ===")
    CONFLICT = dict(band=[250.0, 300.0], ld50=273.0, endpoint="SeedlingSurvival", stage="EarlySeedlingStage")
    g, tx, ep, st = conflict_record(CONFLICT["ld50"])
    w, ok = reason(g)
    CONFLICT["consistent_without_doses"] = ok
    CONFLICT["unsatisfiable_without_doses"] = unsatisfiable(w)
    print(f"  no dose recorded: consistent {ok}; unsatisfiable classes {CONFLICT['unsatisfiable_without_doses']}")
    CONFLICT["runs"] = []
    for dose in (260.0, 280.0, 320.0):
        gg = copy.deepcopy(g)
        assessment(gg, f"test_case_{int(dose)}", tx, ep, st, dose)
        _w, ok = reason(gg)
        CONFLICT["runs"].append(dict(dose=dose, consistent=ok))
        print(f"  assessment at {dose:5.1f} Gy: {'consistent' if ok else 'INCONSISTENT (flagged)'}")
    g2, *_ = conflict_record(310.0)
    w2, ok2 = reason(g2)
    CONFLICT["control_ld50"] = 310.0
    CONFLICT["control_unsatisfiable"] = unsatisfiable(w2)
    print(f"  control, LD50 310 Gy: consistent {ok2}; unsatisfiable classes {CONFLICT['control_unsatisfiable']}")
    OUT["C"] = CONFLICT

    print("\n=== (D) the dose assessments of the ABox ===")
    abox = rdflib.Graph(); abox.parse(os.path.join(HERE, "OnSIR_abox.owl"))
    g = core()
    for t in abox:
        if not (t[1] == OWL.imports or (t[0], RDF.type, OWL.Ontology) in abox):
            g.add(t)
    w, ok = reason(g)
    assert ok
    ok_r, unsat_r, gi_r = robot_reason(g, classify=True)
    assert ok_r and not unsat_r, unsat_r
    found = sorted(abox.subjects(RDF.type, N.DoseAssessment),
                   key=lambda a: (str(a).split("_")[1], float(abox.value(a, N.doseGy))))
    OUT["D"] = []
    for a in found:
        name = str(a)[len(NSU):]
        subj = abox.value(a, N.hasSubject)
        ep_ind, st_ind = abox.value(a, N.forEndpoint), abox.value(a, N.atStage)
        ep_cls = next(str(c)[len(NSU):] for c in abox.objects(ep_ind, RDF.type) if str(c).startswith(NSU))
        st_cls = next(str(c)[len(NSU):] for c in abox.objects(st_ind, RDF.type) if str(c).startswith(NSU))
        row = dict(individual=name, study=name.split("_")[1], taxon=str(abox.value(subj, RDFS.label)),
                   endpoint=ep_cls, stage=st_cls, dose=float(abox.value(a, N.doseGy)),
                   classes=positions(w, name), windows=windows(w, name),
                   classes_robot=robot_positions(gi_r, name))
        OUT["D"].append(row)
        print(f"  {row['study']:18s} {row['taxon']:26s} {row['endpoint']:22s} @ {row['dose']:7.1f} Gy -> "
              f"{row['classes'] or ['(none)']}")

    OUT["D_reasoners_agree"] = all(x["classes"] == x["classes_robot"] for x in OUT["D"])
    print(f"  owlready2 and ROBOT place every assessment alike: {OUT['D_reasoners_agree']}")

    print("\n=== (E) the datatype of the dose literal (HermiT through ROBOT) ===")
    OUT["E"] = []
    OUT["E_owlready2"] = []
    cow = "Vigna unguiculata"
    for dose in (280.0, 250.0):
        for dt in (XSD.double, XSD.decimal, XSD.integer, XSD.float):
            name = str(dt).rsplit("#", 1)[-1]
            lex = str(int(dose)) if dt == XSD.integer else f"{dose:.1f}"
            g = core()
            assessment(g, "datatype_case", taxon_iri(cow), "SeedlingSurvival", "FloweringStage", dose, dt, lex)
            ok, _u, gi = robot_reason(g, classify=True)
            cls = robot_positions(gi, "datatype_case") if ok else None
            OUT["E"].append(dict(dose=dose, datatype=name, consistent=ok, classes=cls))
            print(f"  {dose:5.1f} Gy as xsd:{name:8s} -> {'consistent ' + str(cls) if ok else 'INCONSISTENT'}")
            if dt == XSD.float:
                w, ok2 = reason(g)
                cls2 = positions(w, "datatype_case") if ok2 else None
                OUT["E_owlready2"].append(dict(dose=dose, datatype=name, consistent=ok2, classes=cls2))
                print(f"     owlready2 (HermiT 1.3.8): {'consistent ' + str(cls2) if ok2 else 'INCONSISTENT'}")

    print("\n=== (F) a subtaxon inherits the windows of its species ===")
    g = core()
    sub = OBO.NCBITaxon_3920          # Vigna unguiculata subsp. unguiculata, child of NCBITaxon:3917
    g.add((sub, RDF.type, OWL.Class)); g.add((sub, RDFS.subClassOf, OBO.NCBITaxon_3917))
    g.add((sub, RDFS.label, Literal("Vigna unguiculata subsp. unguiculata")))
    assessment(g, "f_sub", sub, "SeedlingSurvival", "FloweringStage", DEMO_A_DOSE)
    w, ok = reason(g)
    OUT["F"] = dict(taxon="NCBITaxon:3920", parent="NCBITaxon:3917", dose=DEMO_A_DOSE,
                    classes=positions(w, "f_sub"), windows=windows(w, "f_sub"))
    print(f"  NCBITaxon:3920 @ {DEMO_A_DOSE:g} Gy -> {OUT['F']['classes']} {OUT['F']['windows']}")

    print("\n=== (G) one cowpea dose, three endpoint and stage pairs ===")
    pairs = [("SeedlingSurvival", "FloweringStage"), ("GerminationPercentage", "GerminationStage"),
             ("SeedlingSurvival", "EarlySeedlingStage")]
    cases = [(f"g_{i}", taxon_iri(cow), e, s, DEMO_A_DOSE) for i, (e, s) in enumerate(pairs)]
    res = classify(cases)
    OUT["G"] = [dict(endpoint=e, stage=s, dose=DEMO_A_DOSE, classes=res[f"g_{i}"][0])
                for i, (e, s) in enumerate(pairs)]
    for x in OUT["G"]:
        print(f"  {x['endpoint']:22s} {x['stage']:20s} -> {x['classes'] or ['(none)']}")
    print("\n=== (H) the probes of the release: one per endpoint and stage of a favourable band (ROBOT) ===")
    g = core()
    probes = sorted(str(c)[len(NSU):] for c in g.subjects(RDF.type, OWL.Class)
                    if str(c).startswith(NSU) and str(c).endswith("BandUpperEndProbe")
                    and (c, OWL.deprecated, None) not in g)
    ok, unsat, _gi = robot_reason(g)
    H = dict(probes=probes, consistent=ok, unsatisfiable=unsat, ld50=10.0, control_ld50=16.0, runs=[])
    print(f"  {len(probes)} probes; release consistent {ok}; unsatisfiable {unsat}")
    tob = TWD["Nicotiana tabacum"]
    assert tob["band"][0] < H["ld50"] <= tob["band"][1] < H["control_ld50"]
    slug = "Nicotiana_tabacum_" + tob["tag"]
    for ep in tob["endpoints"]:
        for st in tob["stages"]:
            gg = core()
            define(gg, f"test_{ep}_{st}_AtOrAboveLD50Dose", taxon_iri("Nicotiana tabacum"), ep, st,
                   drange(gg, H["ld50"], None, False, False), "AtOrAboveReportedLD50")
            ok, unsat, _gi = robot_reason(gg)
            H["runs"].append(dict(endpoint=ep, stage=st, probe=f"{slug}_{ep}_{st}_BandUpperEndProbe",
                                  consistent=ok, unsatisfiable=unsat))
            print(f"  LD50 from {H['ld50']:g} Gy for {ep} at {st}: unsatisfiable {unsat}")
    gg = core()
    ep0, st0 = tob["endpoints"][0], tob["stages"][0]
    define(gg, "test_control_AtOrAboveLD50Dose", taxon_iri("Nicotiana tabacum"), ep0, st0,
           drange(gg, H["control_ld50"], None, False, False), "AtOrAboveReportedLD50")
    ok, unsat, _gi = robot_reason(gg)
    H["control"] = dict(endpoint=ep0, stage=st0, consistent=ok, unsatisfiable=unsat)
    print(f"  control, LD50 from {H['control_ld50']:g} Gy for {ep0} at {st0}: unsatisfiable {unsat}")
    OUT["H"] = H
    json.dump(OUT, open(os.path.join(HERE, "reason_context.json"), "w"), indent=1)
    print("wrote reason_context.json")
