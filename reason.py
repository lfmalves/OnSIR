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
print("  outcome_hormetic inferred response:", [r.name for r in o_h.hasResponse]
      or "(via some-restriction; see class membership)")
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
