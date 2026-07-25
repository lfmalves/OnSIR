# -*- coding: utf-8 -*-
r"""Reason over enriched OnSIR with HermiT (via owlready2): (i) consistency check;
(ii) a small ABox demonstrating dose->effect classification: an outcome asserted only to be
at a hormetic dose is INFERRED to exhibit a hormetic response and to be a StimulatoryOutcome."""
import owlready2 as o2

onto = o2.get_ontology("file://" + o2.os.path.abspath("OnSIR.owl")).load()
NS = onto.get_namespace("https://w3id.org/onsir/")

def get(name):
    return NS[name] or getattr(onto, name, None)

TreatmentOutcome = get("TreatmentOutcome"); HormeticDose = get("HormeticDose")
MutagenicDose = get("MutagenicDose"); hasDoseCategory = get("hasDoseCategory")
StimulatoryOutcome = get("StimulatoryOutcome"); MutagenicOutcome = get("MutagenicOutcome")
HormeticResponse = get("HormeticResponse"); hasResponse = get("hasResponse")

with onto:
    # outcome asserted ONLY to be at a hormetic dose (no response asserted)
    hd = HormeticDose("hd_low"); md = MutagenicDose("md_high")
    o_h = TreatmentOutcome("outcome_hormetic"); o_h.hasDoseCategory = [hd]
    o_m = TreatmentOutcome("outcome_mutagenic"); o_m.hasDoseCategory = [md]

print("=== before reasoning ===")
print("  outcome_hormetic types:", [c.name for c in o_h.is_a])
print("  outcome_hormetic hasResponse:", [r.name for r in o_h.hasResponse])

try:
    with onto:
        o2.sync_reasoner_hermit(infer_property_values=True)
    consistent = True
except o2.OwlReadyInconsistentOntologyError:
    consistent = False

print("\n=== after HermiT ===")
print("  ontology CONSISTENT:", consistent)
# The response is entailed through an existential restriction, so it never appears as a property
# value on the individual, and owlready2 does not list anonymous restriction classes in
# INDIRECT_is_a either -- both of those checks report a misleading negative. The entailment has to be
# tested by refutation: assert the NEGATION on a fresh copy and see whether the reasoner rejects it.
def entails_response(dose_cls_name, resp_cls_name):
    """True iff asserting NOT(hasResponse some <resp>) on the outcome makes the KB inconsistent."""
    w2 = o2.World()
    o2_ = w2.get_ontology("file://" + o2.os.path.abspath("OnSIR.owl")).load()
    ns = o2_.get_namespace("https://w3id.org/onsir/")
    with o2_:
        x = ns["TreatmentOutcome"]("probe_" + dose_cls_name)
        x.hasDoseCategory = [ns[dose_cls_name]("probe_dose_" + dose_cls_name)]
        x.is_a.append(o2.Not(ns["hasResponse"].some(ns[resp_cls_name])))
    try:
        with o2_:
            o2.sync_reasoner_hermit(x=w2, debug=0)
        return False           # the negation is satisfiable -> not entailed
    except o2.OwlReadyInconsistentOntologyError:
        return True            # the negation is refuted -> entailed

print("  entails (hasResponse some HormeticResponse) from HormeticDose  :",
      entails_response("HormeticDose", "HormeticResponse"))
print("  entails (hasResponse some MutagenicResponse) from MutagenicDose:",
      entails_response("MutagenicDose", "MutagenicResponse"))
print("  outcome_hormetic inferred classes:", [c.name for c in o_h.is_a])
print("  is StimulatoryOutcome?:", StimulatoryOutcome in o_h.is_a
      or StimulatoryOutcome in o_h.INDIRECT_is_a)
print("  outcome_mutagenic inferred classes:", [c.name for c in o_m.is_a])
print("  is MutagenicOutcome?:", MutagenicOutcome in o_m.INDIRECT_is_a)

# TBox: check a disjointness works (hormetic+mutagenic dose on one individual -> inconsistent)
print("\n=== disjointness sanity: assert an individual is BOTH hormetic & mutagenic dose ===")
onto2 = o2.get_ontology("file://" + o2.os.path.abspath("OnSIR.owl")).load()
NS2 = onto2.get_namespace("https://w3id.org/onsir/")
with onto2:
    x = NS2["HormeticDose"]("bad"); x.is_a.append(NS2["MutagenicDose"])
try:
    with onto2:
        o2.sync_reasoner_hermit()
    print("  result: CONSISTENT (unexpected - disjointness not firing)")
except o2.OwlReadyInconsistentOntologyError:
    print("  result: INCONSISTENT as expected -> disjointness axiom is active")
