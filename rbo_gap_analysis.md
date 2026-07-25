# Term-level gap analysis: OnSIR against the OBO Radiation Biology Ontology (RBO)

This file is the **verbatim output of `rbo_recheck.py`**, which is the script whose numbers the
manuscript quotes. Regenerate with:

    python rbo_gap.py       # downloads rbo.owl (~29 MB, CC BY 3.0; not redistributed here)
    python rbo_recheck.py > rbo_gap_analysis.md

MATCHING RULE. An OnSIR class name is split at camel-case boundaries, lowercased and stripped of
non-alphanumerics; an RBO label is normalised the same way; a match is equality of the two normalised
strings. Synonyms are **not** consulted for the match counts. They *are* consulted in the concept
probe, which is the claim that matters, and there the search is over the raw serialisation so
synonyms and definitions are included.

A looser rule that also consults synonyms and allows substring containment reports a few more hits --
an earlier version of this document did exactly that and reported three -- so the rule has to be
stated with the number. Both rules agree on the finding: RBO carries the dosimetric vocabulary and
none of the seed-irradiation dose-effect vocabulary.

---

```
RBO release            : http://purl.obolibrary.org/obo/rbo/releases/2026-07-16/rbo.owl
RBO named classes      : 9221  (URIRef only; blank-node class expressions excluded)
  RBO-native (RBO_*)   : 446   (with rdfs:label: 424)
OnSIR named classes    : 96

STRICT LABEL MATCHING (synonyms not consulted)
  exact match to an RBO-native label   : 0 []
  exact match anywhere in the release  : 3 ['LifecycleStage', 'Neutron', 'Proton']
  near match (>=0.85) to RBO-native    : 0 []
  NO RBO-native counterpart            : 96/96 = 100.0%
  NO counterpart anywhere              : 93/96 = 96.9%

CONCEPT PROBE (raw text of the release, so synonyms and definitions are included)
  hormesis            : 0 occurrence(s)
  radiohormesis       : 0 occurrence(s)
  hormetic dose       : 0 occurrence(s)
  seed irradiation    : 0 occurrence(s)
  germination         : 0 occurrence(s)
  sterilization       : 0 occurrence(s)
  mutation breeding   : 0 occurrence(s)
  dose-response       : 2 occurrence(s)
  seed                : 21 occurrence(s)
  plant               : 480 occurrence(s)
  dose rate           : 30 occurrence(s)
  absorbed dose       : 58 occurrence(s)

PLANT COVERAGE among RBO-native labels
  labels containing ['plant', 'seed', 'germinat', 'crop', 'cultivar']: 0/424 = 0.00%  []
```
