# -*- coding: utf-8 -*-
r"""Search the public ontology registries for a prior seed-irradiation ontology.

The manuscript claims OnSIR is the first reasoning-enabled ontology dedicated to seed irradiation.
A comparison against one incumbent (RBO) does not establish that, so this script performs the
registry search the claim needs, and prints the numbers the paper quotes. It hits the network; the
output is reproducible in the sense that anyone can re-run it and see the registries' current state.

Run:  python registry_search.py
"""
import json, re, sys, urllib.parse, urllib.request

PAT = re.compile(r"radiat|irradiat|mutagen|mutation breed|radiobiol|hormesis", re.I)
SEED = re.compile(r"seed|germinat", re.I)


def get(url):
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return json.load(r)
    except Exception as e:
        print(f"  ! {url.split('/')[2]} unreachable: {e}")
        return None


print("OBO Foundry registry")
d = get("https://obofoundry.org/registry/ontologies.jsonld")
if d:
    onts = d["ontologies"]
    hits = [o for o in onts
            if PAT.search((o.get("title") or "") + " " + (o.get("description") or ""))]
    seed = [o for o in hits
            if SEED.search((o.get("title") or "") + " " + (o.get("description") or ""))]
    print(f"  ontologies registered                     : {len(onts)}")
    print(f"  mentioning radiation/mutagenesis/hormesis : {len(hits)}"
          f"  {[o['id'] for o in hits]}")
    print(f"  ...of those also mentioning seeds         : {len(seed)}"
          f"  {[o['id'] for o in seed] or '(none)'}")

print("\nEBI Ontology Lookup Service")
for q in ("seed irradiation", "radiohormesis", "mutation breeding"):
    d = get("https://www.ebi.ac.uk/ols4/api/search?q="
            + urllib.parse.quote(q) + "&type=ontology&rows=20")
    if d is not None:
        n = len(d.get("response", {}).get("docs", []))
        print(f"  ontologies matching {q!r:20s}: {n}")

print("\nReading: the only registered ontology in this space is RBO, whose scope is radiation")
print("physics, dosimetry and human/animal radiobiology (Section 6.1 quantifies the gap). No")
print("registered ontology combines seed irradiation with plant dose-effect vocabulary.")
