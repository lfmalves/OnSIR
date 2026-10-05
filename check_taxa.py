# -*- coding: utf-8 -*-
r"""Check the NCBITaxon identifier of every species of the coded corpus on the EBI Ontology Lookup
Service: the class must exist, be current, and carry the species name as its label or as one of its
synonyms, as the taxon_match column of corpus/onsir_corpus.csv states. Reads the network only.

Run:  python check_taxa.py     (exit code 0 = every species checks)
"""
import csv
import json
import os
import sys
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))


def term(curie):
    iri = "http://purl.obolibrary.org/obo/" + curie.replace(":", "_")
    url = ("https://www.ebi.ac.uk/ols4/api/ontologies/ncbitaxon/terms/"
           + urllib.parse.quote(urllib.parse.quote(iri, safe=""), safe=""))
    return json.load(urllib.request.urlopen(url, timeout=30))


def main():
    rows = list(csv.DictReader(open(os.path.join(HERE, "corpus", "onsir_corpus.csv"), encoding="utf-8")))
    seen, bad = {}, []
    for r in rows:
        sp, cur, how = r["species"], r["ncbitaxon"], r["taxon_match"]
        if sp in seen:
            continue
        try:
            d = term(cur)
        except Exception as e:  # noqa: BLE001
            bad.append(f"{sp}: {cur} {e}")
            continue
        label, syn = d.get("label", ""), [s.lower() for s in (d.get("synonyms") or [])]
        if how == "exact label":
            good = label.lower() == sp.lower()
        else:
            good = sp.lower() in syn and how.endswith(label)
        seen[sp] = (cur, label, good)
        print(f"  [{'ok  ' if good and not d.get('is_obsolete') else 'FAIL'}] {sp:28s} {cur:20s} {label}")
        if not good or d.get("is_obsolete"):
            bad.append(sp)
    print(f"{len(seen)} species checked, {len(bad)} failed" + (f": {bad}" if bad else ""))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
