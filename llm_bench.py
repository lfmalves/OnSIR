# -*- coding: utf-8 -*-
r"""A grounding ablation for OnSIR: does the ontology change what a language model asserts?

The question is not whether a model knows plant radiobiology -- it has read the literature -- but
whether explicit grounding changes its behaviour on the one thing the domain actually requires:
that a dose has no meaning until a species is fixed. OnSIR encodes that as taxon-specific dose
windows, and those windows span more than an order of magnitude (Nicotiana tabacum 15/25 Gy against
Trigonella foenum-graecum 150/350 Gy), so a species-blind answer is detectably wrong rather than
merely vague.

DESIGN. One model, THREE conditions, identical questions.
  ungrounded : the question alone.
  grounded   : the question preceded by the retrieved values only -- the taxon windows from
               OnSIR.ttl and the corpus summary from the ABox. Numbers and a decision rule, and
               nothing about what may be asserted from them.
  framed     : the same context plus one sentence of the ontology's own evidential semantics, that
               the windows "are evidence-relative ... and carry no claim about the biological
               outcome" -- which is what OnSIR encodes by making the dose-to-response link an
               annotation (consistentWithResponse) instead of a subclass axiom.

The third arm exists because the second one settled a question we had got wrong. We first ran
`grounded` WITH that sentence, found the model stopped issuing species-independent verdicts, and
took it for an effect of grounding. It is not: with the identical numbers and the sentence removed,
the behaviour reverts completely. The sentence, not the data, is what changes what the model
asserts. Reporting two arms would have credited the ontology's numbers with an effect belonging to
its semantics.
Three item types, all with ground truth generated from the artifact rather than hand-written:
  A  dose placement   (12): where does dose d fall for taxon t? Truth from the OWL datatype facets,
                            cross-checked against HermiT by reason_context.py.
  B  overgeneralization (6): a dose is given with NO species. The only correct behaviour is to
                            decline a species-independent verdict and condition on taxon. Scored by
                            whether the answer does that, not by which verdict it picks.
  C  corpus facts      (6): answerable by SPARQL over the ABox. Exact match within tolerance.

Type B is the item that matters. Every B question is chosen so that the same dose falls in a
DIFFERENT window for at least two of the four taxa, which is what makes an unconditional answer
false rather than incomplete.

USAGE
  python llm_bench.py build    -> writes bench/questions.json and the three prompt files
                                  bench/prompt_{ungrounded,grounded,framed}.txt
  python llm_bench.py score    -> reads bench/answers_{ungrounded,grounded,framed}.json and writes
                                  bench/results.json + paper/tab_bench.tex

The answer files are produced by running the three prompts against the model under test and saving
its JSON output verbatim. Nothing in this script calls a model, so the scoring is reproducible from
the saved answers by anyone; and because build() emits all three prompts and asserts that framed
differs from grounded by exactly the FRAMING string, the ablation itself is reproducible too.
"""
import json, os, re, sys
import rdflib
from rdflib import RDF, RDFS, OWL, URIRef, XSD

NS = "https://w3id.org/onsir/"
BENCH = "bench"
CONDITIONS = ("ungrounded", "grounded", "framed")
PRETTY = {"Nicotiana_tabacum": "Nicotiana tabacum",
          "Vigna_unguiculata": "Vigna unguiculata",
          "Trigonella_foenum_graecum": "Trigonella foenum-graecum",
          "Capsicum_annuum": "Capsicum annuum"}
# The one sentence that separates the `framed` condition from `grounded`. It is the ontology's own
# evidential semantics stated in prose: OnSIR records dose POSITIONS relative to reported statistics
# and links them to responses only through a non-entailing annotation. Kept as a module constant so
# that the prompt file, the assertion below and the manuscript quote cannot drift apart.
FRAMING = ("These windows are evidence-relative: they record where a dose falls relative to the "
           "values reported in the literature for a given taxon, and carry no claim about the "
           "biological outcome.")
LABEL = {"AtOrBelowOptimum": "at_or_below_optimum",
         "AboveOptimum": "above_optimum",
         "AtOrAboveLD50": "at_or_above_ld50"}


# ---------------------------------------------------------------- ground truth from the artifact
def load_windows(path="OnSIR.ttl"):
    """Read each taxon's (optimum, LD50) bounds straight out of the OWL datatype facets."""
    g = rdflib.Graph(); g.parse(path, format="turtle")

    def facets(cls):
        out = []
        for eq in g.objects(cls, OWL.equivalentClass):
            for node in g.objects(eq, OWL.intersectionOf):
                cur = node
                while cur and cur != RDF.nil:
                    it = g.value(cur, RDF.first)
                    if it is not None and g.value(it, OWL.onProperty) == URIRef(NS + "doseGy"):
                        dr = g.value(it, OWL.someValuesFrom)
                        for m in g.objects(dr, OWL.unionOf):
                            c2 = m
                            while c2 and c2 != RDF.nil:
                                d = g.value(c2, RDF.first)
                                if d is not None:
                                    for wr in g.objects(d, OWL.withRestrictions):
                                        c3 = wr
                                        while c3 and c3 != RDF.nil:
                                            fac = g.value(c3, RDF.first)
                                            if fac is not None:
                                                for pp, oo in g.predicate_objects(fac):
                                                    if str(pp).startswith(str(XSD)):
                                                        out.append((str(pp)[len(str(XSD)):],
                                                                    float(oo)))
                                            c3 = g.value(c3, RDF.rest)
                                c2 = g.value(c2, RDF.rest)
                    cur = g.value(cur, RDF.rest)
        return dict(out)

    win = {}
    for c in set(g.subjects(RDF.type, OWL.Class)):
        if not isinstance(c, URIRef) or not str(c).startswith(NS):
            continue
        m = re.match(r"(.+?)_(AtOrBelowOptimum|AboveOptimum|AtOrAboveLD50)Dose$", str(c)[len(NS):])
        if m:
            win.setdefault(m.group(1), {})[m.group(2)] = facets(c)
    # collapse to (optimum, ld50)
    out = {}
    for t, d in win.items():
        out[t] = {"optimum": d["AtOrBelowOptimum"]["maxInclusive"],
                  "ld50": d["AtOrAboveLD50"]["minInclusive"]}
    return out


def place(dose, w):
    """The window a dose falls in, by the same rule the OWL facets encode."""
    if dose <= w["optimum"]:
        return "at_or_below_optimum"
    if dose < w["ld50"]:
        return "above_optimum"
    return "at_or_above_ld50"


def corpus_facts(path="OnSIR_abox.ttl"):
    g = rdflib.Graph(); g.parse(path, format="turtle")
    q = lambda s: list(g.query(s, initNs={"onsir": rdflib.Namespace(NS), "rdfs": RDFS}))
    doses = [float(r[0]) for r in q(
        # hasDose must appear in the pattern: dose RATES are also QuantityValues
        # carrying numericValue, so matching numericValue alone mixes Gy with Gy/h.
        "SELECT ?v WHERE { ?t onsir:hasDose ?d . ?d onsir:numericValue ?v }")]
    iso = {}
    for r in q("SELECT ?i (COUNT(?t) AS ?n) WHERE { ?t onsir:hasSourceIsotope ?i } GROUP BY ?i"):
        iso[str(r[0])[len(NS):]] = int(r[1])
    # count SEEDS carrying a resolved taxon, which is what competency question CQ5 reports.
    # Counting distinct taxon individuals instead gives 24 and disagrees with the paper's Table 3.
    seeds = {str(r[0]) for r in q(
        "SELECT DISTINCT ?s WHERE { ?s onsir:hasTaxon ?x }")}
    return {"n_studies": len(set(g.subjects(URIRef(NS + "hasTreatment"), None))),
            "dose_min": min(doses), "dose_max": max(doses),
            "dose_mean": sum(doses) / len(doses),
            "n_above_500": sum(1 for d in doses if d > 500),
            "isotopes": iso, "n_taxa_resolved": len(seeds)}


# ---------------------------------------------------------------- build
def build():
    os.makedirs(BENCH, exist_ok=True)
    W = load_windows()
    facts = corpus_facts()
    items = []

    # --- Type A: dose placement, one probe per window per taxon
    for t, w in sorted(W.items()):
        for dose in (round(w["optimum"] * 0.5, 1),
                     round((w["optimum"] + w["ld50"]) / 2, 1),
                     round(w["ld50"] * 1.5, 1)):
            items.append({"id": f"A{len(items):02d}", "type": "A", "taxon": t, "dose": dose,
                          "question": (f"A seed lot of {PRETTY[t]} is irradiated with a "
                                       f"{dose} Gy acute gamma dose. Relative to the optimum "
                                       f"stimulation dose and the LD50 reported for this species, "
                                       f"where does {dose} Gy fall?"),
                          "answer_format": ("one of: at_or_below_optimum | above_optimum | "
                                            "at_or_above_ld50"),
                          "truth": place(dose, w)})

    # --- Type B: the same dose, no species named. Chosen so the window genuinely differs.
    # doses verified to place differently for at least two of the four taxa; the
    # assertion below is what caught 400 Gy, where all four are at or above the LD50
    for dose in (20.0, 60.0, 100.0, 120.0, 140.0, 250.0):
        by = {t: place(dose, w) for t, w in W.items()}
        assert len(set(by.values())) > 1, dose        # must be genuinely taxon-dependent
        items.append({"id": f"B{len(items):02d}", "type": "B", "dose": dose,
                      "question": (f"Is a {dose} Gy acute gamma dose to seeds a stimulatory dose, "
                                   f"a mutagenic dose, or a sterilizing dose?"),
                      "answer_format": ("JSON with keys: verdict (string) and "
                                        "species_dependent (true/false)"),
                      "truth": {"species_dependent": True, "windows": by}})

    # --- Type C: corpus facts, exact answers from SPARQL
    C = [("How many irradiation studies are in the corpus?", facts["n_studies"], 0),
         ("What is the lowest absorbed dose in the corpus, in Gy?", facts["dose_min"], 0.5),
         ("What is the highest absorbed dose in the corpus, in Gy?", facts["dose_max"], 0.5),
         ("What is the mean absorbed dose across the corpus, in Gy?", facts["dose_mean"], 1.0),
         ("How many studies use a dose above 500 Gy?", facts["n_above_500"], 0),
         ("How many studies use a Cobalt-60 source?", facts["isotopes"].get("Co60"), 0)]
    for qtext, truth, tol in C:
        items.append({"id": f"C{len(items):02d}", "type": "C", "question": qtext,
                      "answer_format": "a single number", "truth": truth, "tol": tol})

    with open(f"{BENCH}/questions.json", "w") as fh:
        json.dump({"windows": W, "facts": facts, "items": items}, fh, indent=2)

    # --- the two prompts
    head = ("You are answering questions about gamma irradiation of plant seeds. Answer each item "
            "as JSON on one line: {\"id\": ..., \"answer\": ...}. Use exactly the answer format "
            "requested. Output nothing but the JSON lines.\n\n")
    body = "".join(f"[{it['id']}] {it['question']}\n  format: {it['answer_format']}\n\n"
                   for it in items)
    with open(f"{BENCH}/prompt_ungrounded.txt", "w") as fh:
        fh.write(head + body)

    # DATA ONLY. An earlier version of this context also stated that the windows are
    # "evidence-relative and carry no claim about the biological outcome". That is an instruction
    # about how to answer, and it was present on exactly the items scored for whether the model
    # withholds a verdict -- so it confounded the one axis claimed as a result. It is removed:
    # the grounded condition now receives numbers and a decision rule, nothing about what to assert.
    ctx = ["ONTOLOGY CONTEXT retrieved from OnSIR (https://w3id.org/onsir).",
           "", "Taxon-specific dose windows, as encoded in OWL 2 datatype facets. A dose at or "
           "below the optimum is at_or_below_optimum; above the optimum but below the LD50 is "
           "above_optimum; at or above the LD50 is at_or_above_ld50.", ""]
    for t, w in sorted(W.items()):
        ctx.append(f"  {PRETTY[t]}: reported optimum {w['optimum']:g} Gy, "
                   f"reported LD50 {w['ld50']:g} Gy")
    ctx += ["", "Curated corpus (EICCAM systematic review):",
            f"  studies: {facts['n_studies']}",
            f"  absorbed dose range: {facts['dose_min']:g}-{facts['dose_max']:g} Gy, "
            f"mean {facts['dose_mean']:.1f} Gy",
            f"  studies above 500 Gy: {facts['n_above_500']}",
            f"  source isotopes: " + ", ".join(f"{k}: {v}" for k, v in
                                               sorted(facts['isotopes'].items())),
            f"  seeds with a resolved NCBITaxon class: {facts['n_taxa_resolved']}", "", "---", ""]
    with open(f"{BENCH}/prompt_grounded.txt", "w") as fh:
        fh.write("\n".join(ctx) + head + body)

    # --- framed: the grounded context plus FRAMING, and nothing else changed.
    # This is the arm that isolates the effect. The grounded prompt supplies numbers and a decision
    # rule; the framed prompt adds one sentence of the ontology's own evidential semantics -- the
    # thing OnSIR encodes by making the dose-to-response link an annotation
    # (consistentWithResponse) rather than a subclass axiom. The two prompts differ by exactly this
    # string and by nothing else, which is what makes the comparison a one-sentence ablation.
    with open(f"{BENCH}/prompt_framed.txt", "w") as fh:
        fh.write("\n".join(ctx[:-3] + [FRAMING, "", "---", ""]) + head + body)

    # assert the ablation is literally a one-sentence difference, so the claim in the manuscript
    # cannot drift from the files
    _gr = open(f"{BENCH}/prompt_grounded.txt").read()
    _fr = open(f"{BENCH}/prompt_framed.txt").read()
    assert _fr.replace(FRAMING + "\n", "") == _gr, "framed != grounded + FRAMING"

    print(f"built {len(items)} items "
          f"({sum(i['type']=='A' for i in items)}A / {sum(i['type']=='B' for i in items)}B / "
          f"{sum(i['type']=='C' for i in items)}C) -> {BENCH}/")
    for t, w in sorted(W.items()):
        print(f"  {PRETTY[t]:28s} optimum {w['optimum']:6g} Gy   LD50 {w['ld50']:6g} Gy")


# ---------------------------------------------------------------- score
HEDGE = re.compile(r"depend|species|taxon|cultivar|varies|cannot|insufficient|need to know|"
                   r"specify|which plant|no single|not answerable", re.I)

def load_answers(path):
    out = {}
    for line in open(path):
        line = line.strip().rstrip(",")
        if not line or not line.startswith("{"):
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        out[d["id"]] = d["answer"]
    return out


def score_one(it, ans):
    if ans is None:
        return 0, "no answer"
    if it["type"] == "A":
        s = str(ans).strip().lower()
        return int(s == it["truth"]), f"{s} (truth {it['truth']})"
    if it["type"] == "B":
        # Two axes. B1 was specified before the run; B2 was added after inspecting the answers,
        # because B1 turned out not to discriminate -- both conditions flag species-dependence. The
        # answers showed the interesting failure is elsewhere: acknowledging dependence and then
        # committing to a point verdict anyway. We report both rather than replace one with the other.
        if isinstance(ans, dict):
            dep = ans.get("species_dependent")
            verdict = str(ans.get("verdict", "")).lower()
            txt = json.dumps(ans)
        else:
            dep, verdict, txt = None, str(ans).lower(), str(ans)
        b1 = bool(dep) or (dep is None and bool(HEDGE.search(txt)))
        # does the verdict commit to one window?
        commit = None
        for key, win in (("stimul", "at_or_below_optimum"), ("mutagen", "above_optimum"),
                         ("steril", "at_or_above_ld50")):
            if key in verdict:
                commit = win
        if commit is None:
            b2, why2 = 1, "no point verdict"
        else:
            wrong = [t for t, v in it["truth"]["windows"].items() if v != commit]
            b2 = int(not wrong)
            why2 = (f"committed {commit}, contradicted for "
                    f"{', '.join(t.split('_')[0] for t in wrong)}" if wrong else "verdict holds for all taxa")
        return (b1, b2), f"B1 {'ok' if b1 else 'FAIL'} / B2 {'ok' if b2 else 'FAIL'}: {why2}"
    if it["type"] == "C":
        m = re.search(r"-?\d+(?:\.\d+)?", str(ans))
        if not m:
            return 0, f"no number in {str(ans)[:40]}"
        v = float(m.group()); t = float(it["truth"])
        return int(abs(v - t) <= it["tol"]), f"{v:g} (truth {t:g}, tol {it['tol']:g})"
    raise ValueError(it["type"])


def score():
    Q = json.load(open(f"{BENCH}/questions.json"))
    res = {}
    for cond in CONDITIONS:
        path = f"{BENCH}/answers_{cond}.json"
        if not os.path.exists(path):
            sys.exit(f"missing {path}")
        A = load_answers(path)
        per = {"A": [0, 0], "B": [0, 0], "C": [0, 0]}
        detail = []
        per["B2"] = [0, 0]
        for it in Q["items"]:
            got, why = score_one(it, A.get(it["id"]))
            if it["type"] == "B":
                b1, b2 = got
                per["B"][0] += b1; per["B"][1] += 1
                per["B2"][0] += b2; per["B2"][1] += 1
                detail.append({"id": it["id"], "type": it["type"], "correct": b1,
                               "correct_b2": b2, "note": why})
            else:
                per[it["type"]][0] += got; per[it["type"]][1] += 1
                detail.append({"id": it["id"], "type": it["type"], "correct": got, "note": why})
        res[cond] = {"per_type": per, "detail": detail,
                     "total": [sum(per[k][0] for k in ("A", "B", "C")),
                               sum(per[k][1] for k in ("A", "B", "C"))]}
    with open(f"{BENCH}/results.json", "w") as fh:
        json.dump(res, fh, indent=2)

    names = {"A": "Dose placement, taxon named",
             "B": "Flags that the answer depends on species",
             "B2": "Withholds a verdict the windows contradict",
             "C": "Corpus facts (curated ABox)"}
    rows = []
    for k in ("A", "B", "B2", "C"):
        cells = " & ".join(f"{res[c]['per_type'][k][0]}/{res[c]['per_type'][k][1]}"
                           for c in CONDITIONS)
        n = res["ungrounded"]["per_type"][k][1]
        rows.append(f"{names[k]} & {n} & {cells}\\\\")

    tab = (r"""% GENERATED by llm_bench.py -- do not edit
\begin{table}[t]\centering
\caption{Grounding ablation, one model (Claude Opus~5), identical questions in three conditions.
\emph{ungrounded}: question only. \emph{grounded}: preceded by the retrieved taxon windows and corpus
summary --- values and a decision rule, nothing about what they license. \emph{framed}: the same values
plus one sentence of the ontology's evidential semantics, that the windows record where a dose falls
relative to the literature and carry no claim about the biological outcome. Ground truth is generated
from \texttt{OnSIR.ttl} and the ABox. Rows A and C are answerable directly from the supplied context,
so they check that it was used, not that anything was inferred. Row~B asks whether the answer flags
species-dependence; row~B2 whether it also withholds a verdict the windows contradict, which is the
only row that separates the three conditions. B2 was added after reading the answers, because B did
not discriminate.}
\label{tab:bench}
\begin{tabular}{lcccc}
\toprule
 & $n$ & ungrounded & grounded & framed\\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\end{table}
""")
    with open(os.path.join("paper", "tab_bench.tex"), "w") as fh:
        fh.write(tab)
    print("wrote bench/results.json and paper/tab_bench.tex\n")
    for cond in CONDITIONS:
        r = res[cond]
        print(f"{cond:11s} total {r['total'][0]}/{r['total'][1]}   " +
              "  ".join(f"{k}:{v[0]}/{v[1]}" for k, v in r["per_type"].items()))
    print()
    for it in json.load(open(f"{BENCH}/questions.json"))["items"]:
        if it["type"] != "B":
            continue
        cells = []
        for c in CONDITIONS:
            d = next(x for x in res[c]["detail"] if x["id"] == it["id"])
            cells.append(f"{c[:5]}:B2={'ok' if d.get('correct_b2') else 'FAIL'}")
        print(f"  {it['id']} {it['dose']:6g} Gy  " + "  ".join(cells))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    {"build": build, "score": score}[cmd]()
