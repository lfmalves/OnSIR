# -*- coding: utf-8 -*-
r"""Generate the manuscript's ontology-metrics table directly from OnSIR.ttl.

A hand-maintained table can silently disagree with the release it describes -- a stale
disjointness or restriction count looks perfectly plausible. Counting here removes the possibility.

Counting rules, stated because every one of them is a choice:
  * named classes / properties: IRIs in the OnSIR namespace only, so anonymous class expressions
    and imported terms are excluded;
  * disjointness axioms: owl:AllDisjointClasses nodes plus owl:disjointWith pairs;
  * restrictions: owl:Restriction nodes, split by the operator they carry, since "existential and
    cardinality" is narrower than "all restrictions";
  * external alignments: triples whose subject is an OnSIR IRI and whose object is an external
    class IRI, counted as triples and as distinct targets, which are different numbers.

Writes: paper/tab_metrics.tex
Run:    python make_metrics.py
"""
import os
from collections import Counter
import rdflib
from rdflib import RDF, RDFS, OWL, URIRef, XSD

NS = "https://w3id.org/onsir/"
OBO = "http://purl.obolibrary.org/obo/"
QUDT_UNIT = "http://qudt.org/vocab/unit/"

g = rdflib.Graph()
g.parse("OnSIR.ttl", format="turtle")


def named(t):
    return sorted(x for x in set(g.subjects(RDF.type, t))
                  if isinstance(x, URIRef) and str(x).startswith(NS))


R = set(g.subjects(RDF.type, OWL.Restriction))
sv = [r for r in R if (r, OWL.someValuesFrom, None) in g]
hv = [r for r in R if (r, OWL.hasValue, None) in g]
qc = [r for r in R if (r, OWL.qualifiedCardinality, None) in g
      or (r, OWL.minQualifiedCardinality, None) in g]

disj = len(set(g.subjects(RDF.type, OWL.AllDisjointClasses))) + \
    len(set(g.subject_objects(OWL.disjointWith)))

align = set()
for s_, p_, o_ in g:
    if (isinstance(s_, URIRef) and str(s_).startswith(NS)
            and isinstance(o_, URIRef) and (str(o_).startswith(OBO) or str(o_).startswith(QUDT_UNIT))
            and not str(o_).endswith("rbo.owl")):
        # the SUBJECT belongs in the key. Dropping it counted distinct (predicate, object) pairs and
        # reported 21 where there are 28 triples -- and made the triple count coincide exactly with
        # the distinct-target count, which the caption says should differ.
        align.add((str(s_), str(p_), str(o_)))
targets = {t[2] for t in align}
fams = Counter()
for o in targets:
    fams[o[len(OBO):].split("_")[0] if o.startswith(OBO) else "QUDT"] += 1

# The equivalence count mixes two different things: internal defined/covering classes and external
# alignments asserted as equivalences. Reporting them together mislabels three of them.
# "external" means the target is outside the OnSIR namespace, not merely that it is an OBO IRI.
# Testing for the OBO prefix alone counted :QuantityValue == qudt:QuantityValue as an INTERNAL
# defined class, so the row label "covering, defined and dose-window classes" was false for one of
# its members.
_eq = list(g.subject_objects(OWL.equivalentClass))
n_eq_external = len([1 for _s, _o in _eq
                     if isinstance(_o, URIRef) and not str(_o).startswith(NS)])
n_eq_internal = len(_eq) - n_eq_external

# The description-logic name is DERIVED from the axioms present, not typed in. It used to be a
# hard-coded string and was wrong: OnSIR carries a role hierarchy
# (hasBiochemicalChange subPropertyOf induces), which contributes H, and no owl:complementOf --
# negation enters through the disjointness axioms, which ALC already provides.
_letters = ["ALC"]
if list(g.subject_objects(RDFS.subPropertyOf)):
    _letters.append("H")                        # role hierarchy
if hv:
    _letters.append("O")                        # nominals, via owl:hasValue
if list(g.triples((None, OWL.inverseOf, None))):
    _letters.append("I")                        # inverse roles
if qc:
    _letters.append("Q")                        # qualified cardinality
_dl = "".join(_letters)
_has_dtype = bool(list(g.triples((None, OWL.withRestrictions, None)))) or bool(
    [1 for _s, _o in g.subject_objects(RDFS.range) if str(_o).startswith(str(XSD))])
expr = r"$\mathcal{%s}%s$" % (_dl, r"(\mathcal{D})" if _has_dtype else "")

# BFO reach. The paper says OnSIR builds on BFO; how much of it actually hangs off BFO is a fact
# about the artifact, so it is counted rather than characterised. Transitive closure over
# rdfs:subClassOf and owl:equivalentClass, since an equivalence to a PO class inherits PO's own BFO
# placement only if that class is imported -- which it is not, so equivalences count only when the
# chain reaches BFO inside this file.
_BFO = "http://purl.obolibrary.org/obo/BFO_"
_up = {}
for _s, _o in list(g.subject_objects(RDFS.subClassOf)) + list(g.subject_objects(OWL.equivalentClass)):
    if isinstance(_s, URIRef) and isinstance(_o, URIRef):
        _up.setdefault(_s, set()).add(_o)


def _has_bfo(c, seen=None):
    seen = seen or set()
    if c in seen:
        return False
    seen.add(c)
    for par in _up.get(c, ()):
        if str(par).startswith(_BFO) or _has_bfo(par, seen):
            return True
    return False


n_bfo = len([c for c in named(OWL.Class) if _has_bfo(c)])

rows = [
    ("Named classes", len(named(OWL.Class))),
    ("Object properties", len(named(OWL.ObjectProperty))),
    ("Datatype properties", len(named(OWL.DatatypeProperty))),
    ("Functional properties", len([x for x in set(g.subjects(RDF.type, OWL.FunctionalProperty))
                                   if str(x).startswith(NS)])),
    ("Disjointness axioms", disj),
    ("Existential and cardinality restrictions", len(sv) + len(qc)),
    (r"Nominal (\texttt{hasValue}) restrictions", len(hv)),
    ("Equivalences: covering, defined and dose-window classes", n_eq_internal),
    ("Equivalences: external alignments", n_eq_external),
    ("External alignment triples", len(align)),
    ("Named classes with a BFO ancestor", n_bfo),
    ("Distinct external terms aligned to", len(targets)),
]

body = "\n".join(f"{k} & {v}\\\\" for k, v in rows)
tab = r"""% GENERATED by make_metrics.py -- do not edit
\begin{table}[t]\centering
\caption{Size and expressivity of the release, counted from \texttt{OnSIR.ttl} by
\texttt{make\_metrics.py}. Counts cover the OnSIR namespace only, so imported terms and anonymous
class expressions are excluded. Alignment triples and distinct external terms are reported
separately because one external term can be the target of more than one triple.}
\label{tab:metrics}
\begin{tabular}{lr}
\toprule
@@BODY@@
DL expressivity & @@EXPR@@\\
Reasoner-checked (HermiT) & yes\\
\bottomrule
\end{tabular}
\end{table}
""".replace("@@BODY@@", body).replace("@@EXPR@@", expr)

with open(os.path.join("paper", "tab_metrics.tex"), "w") as fh:
    fh.write(tab)
print("wrote paper/tab_metrics.tex")
for k, v in rows:
    print(f"  {k:56s} {v}")
print(f"  expressivity: {expr}")
print(f"  external families: {dict(sorted(fams.items()))}")
