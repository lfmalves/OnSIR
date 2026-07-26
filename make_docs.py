# -*- coding: utf-8 -*-
r"""Generate human-readable HTML documentation for OnSIR directly from OnSIR.ttl.

Written in-repo rather than delegated to a generic tool because OnSIR uses OWL 2 constructs
(faceted data ranges and DataUnionOf for the taxon-specific dose windows) that off-the-shelf
documentation generators do not render. Everything below is read from the ontology itself, so the
documentation cannot drift from the artifact.
"""
import html
from collections import defaultdict
import rdflib
from rdflib import RDF, RDFS, OWL, XSD, URIRef, BNode, Literal, Namespace

NS = "https://w3id.org/onsir/"
DCT = Namespace("http://purl.org/dc/terms/")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
OBO = "http://purl.obolibrary.org/obo/"

g = rdflib.Graph(); g.parse("OnSIR.ttl", format="turtle")

def loc(u):
    s = str(u)
    for pre, short in [(NS, ""), (OBO, "obo:"), (str(RDFS), "rdfs:"), (str(OWL), "owl:"),
                       (str(XSD), "xsd:"), (str(SKOS), "skos:"), (str(DCT), "dct:")]:
        if s.startswith(pre):
            return short + s[len(pre):]
    return s

def esc(x): return html.escape(str(x))

def one(s, p):
    v = g.value(s, p)
    return str(v) if v else None

# ---------- ontology metadata ----------
ont = next(iter(g.subjects(RDF.type, OWL.Ontology)))
meta = dict(
    title=one(ont, DCT.title), desc=one(ont, DCT.description),
    version=one(ont, OWL.versionInfo), license=one(ont, DCT.license),
    created=one(ont, DCT.created), modified=one(ont, DCT.modified),
    creators=sorted(str(o) for o in g.objects(ont, DCT.creator)),
    sources=sorted(str(o) for o in g.objects(ont, DCT.source)),
)

named = lambda t: sorted((x for x in set(g.subjects(RDF.type, t))
                          if isinstance(x, URIRef) and str(x).startswith(NS)), key=loc)
classes = named(OWL.Class)
objprops = named(OWL.ObjectProperty)
dataprops = named(OWL.DatatypeProperty)
individuals = named(OWL.NamedIndividual)

# ---------- decode a faceted data range (possibly a union) into readable text ----------
def facets(dr):
    out = []
    for f in g.objects(dr, OWL.withRestrictions):
        node = f
        while node and node != RDF.nil:
            item = g.value(node, RDF.first)
            if item is not None:
                for p, v in g.predicate_objects(item):
                    out.append(f"{loc(p).split(':')[-1]} {v}")
            node = g.value(node, RDF.rest)
    return out

def datarange_text(dr):
    if isinstance(dr, URIRef):
        return loc(dr)
    un = g.value(dr, OWL.unionOf)
    if un is not None:
        parts, node = [], un
        while node and node != RDF.nil:
            parts.append(g.value(node, RDF.first)); node = g.value(node, RDF.rest)
        inner = {" and ".join(facets(p)) for p in parts if facets(p)}
        types = ", ".join(sorted({loc(g.value(p, OWL.onDatatype) or p) for p in parts}))
        body = " and ".join(sorted(inner)[0].split(" and ")) if inner else ""
        return f"{body} ({types})" if body else types
    fs = facets(dr)
    dt = g.value(dr, OWL.onDatatype)
    return (" and ".join(fs) + (f" ({loc(dt)})" if dt else "")) if fs else loc(dr)

def class_expr(x):
    """Readable rendering of a (possibly anonymous) class expression."""
    if isinstance(x, URIRef):
        return f'<a href="#{esc(loc(x))}">{esc(loc(x))}</a>' if str(x).startswith(NS) else esc(loc(x))
    if (x, RDF.type, OWL.Restriction) in g:
        p = g.value(x, OWL.onProperty)
        for pred, word in [(OWL.someValuesFrom, "some"), (OWL.allValuesFrom, "only"),
                           (OWL.hasValue, "value")]:
            v = g.value(x, pred)
            if v is not None:
                if pred == OWL.someValuesFrom and isinstance(v, BNode) and (
                        g.value(v, OWL.onDatatype) or g.value(v, OWL.unionOf)):
                    return f"{esc(loc(p))} <em>some</em> [{esc(datarange_text(v))}]"
                return f"{esc(loc(p))} <em>{word}</em> {class_expr(v)}"
        card = g.value(x, URIRef(str(OWL) + "qualifiedCardinality"))
        if card is not None:
            oc = g.value(x, OWL.onClass)
            return f"{esc(loc(p))} <em>exactly</em> {card} {class_expr(oc)}"
        return "restriction"
    for pred, sep in [(OWL.intersectionOf, " <b>and</b> "), (OWL.unionOf, " <b>or</b> ")]:
        lst = g.value(x, pred)
        if lst is not None:
            items, node = [], lst
            while node and node != RDF.nil:
                items.append(class_expr(g.value(node, RDF.first)))
                node = g.value(node, RDF.rest)
            return "(" + sep.join(items) + ")"
    return "anonymous class"

# ---------- build HTML ----------
P = []
P.append(f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(meta['title'] or 'OnSIR')}</title><style>
:root{{--ink:#1a1a1a;--mut:#666;--line:#e2e2e2;--bg:#fff;--acc:#0b6}}
*{{box-sizing:border-box}}body{{margin:0;font:16px/1.6 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:var(--ink);background:var(--bg)}}
.wrap{{max-width:62rem;margin:0 auto;padding:2.5rem 1.25rem 5rem}}
h1{{font-size:1.9rem;margin:0 0 .3rem}}h2{{font-size:1.3rem;margin:2.5rem 0 .75rem;padding-bottom:.3rem;border-bottom:2px solid var(--line)}}
h3{{font-size:1rem;margin:1.5rem 0 .3rem;font-family:ui-monospace,SFMono-Regular,Menlo,monospace}}
.sub{{color:var(--mut);margin:0 0 1.5rem}}
table{{width:100%;border-collapse:collapse;margin:.75rem 0;font-size:.92rem}}
th,td{{text-align:left;padding:.45rem .6rem;border-bottom:1px solid var(--line);vertical-align:top}}
th{{background:#fafafa;font-weight:600}}
code,.mono{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.9em}}
a{{color:#06c;text-decoration:none}}a:hover{{text-decoration:underline}}
.def{{margin:.2rem 0 .4rem}}.ax{{color:var(--mut);font-size:.9rem}}
.badge{{display:inline-block;background:#eef7f2;color:var(--acc);border:1px solid #cfe9dd;border-radius:.5rem;padding:.05rem .45rem;font-size:.78rem;margin-right:.3rem}}
.toc a{{display:inline-block;margin:.1rem .55rem .1rem 0;font-family:ui-monospace,monospace;font-size:.85rem}}
@media(prefers-color-scheme:dark){{:root{{--ink:#e8e8e8;--mut:#9a9a9a;--line:#333;--bg:#161616}}
th{{background:#1f1f1f}}.badge{{background:#12261d;border-color:#1f4a35}}a{{color:#6ab7ff}}}}
</style></head><body><div class="wrap">""")
P.append(f"<h1>{esc(meta['title'] or 'OnSIR')}</h1>")
P.append(f"<p class='sub'>{esc(meta['desc'] or '')}</p>")
P.append("<table>")
for k, v in [("Namespace", NS), ("Version", meta["version"]), ("License", meta["license"]),
             ("Created", meta["created"]), ("Modified", meta["modified"]),
             ("Authors", "; ".join(meta["creators"])),
             ("Provenance", "<br>".join(esc(s) for s in meta["sources"]) or "&mdash;")]:
    if v: P.append(f"<tr><th style='width:9rem'>{esc(k)}</th><td class='mono'>{v if k=='Provenance' else esc(v)}</td></tr>")
P.append(f"<tr><th>Size</th><td>{len(g)} triples &middot; {len(classes)} named classes &middot; "
         f"{len(objprops)} object properties &middot; {len(dataprops)} datatype properties</td></tr>")
P.append("</table>")

# taxon dose windows — the distinctive content
windows = defaultdict(list)
for c in classes:
    for eq in g.objects(c, OWL.equivalentClass):
        txt = class_expr(eq)
        if "doseGy" in txt:
            windows[loc(c)].append(txt)
if windows:
    P.append("<h2>Taxon-specific dose windows</h2>")
    P.append("<p>Dose categories are <em>not</em> asserted: each taxon carries numeric windows, so a "
             "reasoner derives the category of a dose from its value together with the taxon. "
             "Bounds are literature-derived and provenanced per class.</p><table>"
             "<tr><th>Window class</th><th>Definition</th><th>Source</th></tr>")
    for k in sorted(windows):
        src = one(URIRef(NS + k), DCT.source) or ""
        P.append(f"<tr><td class='mono'><a href='#{esc(k)}'>{esc(k)}</a></td>"
                 f"<td class='ax'>{windows[k][0]}</td><td class='ax'>{esc(src)}</td></tr>")
    P.append("</table>")

def entity_section(title, items, kind):
    P.append(f"<h2>{title} <span class='badge'>{len(items)}</span></h2>")
    P.append("<p class='toc'>" + " ".join(f"<a href='#{esc(loc(i))}'>{esc(loc(i))}</a>" for i in items) + "</p>")
    for i in items:
        P.append(f"<h3 id='{esc(loc(i))}'>{esc(loc(i))}</h3>")
        d = one(i, SKOS.definition) or one(i, RDFS.comment)
        # A term carrying a curation caveat must show it. skos:definition wins over rdfs:comment
        # above, so a caveat recorded only in skos:note or owl:deprecated would be invisible in the
        # rendered documentation -- exactly the drift the manuscript says cannot happen.
        dep = g.value(i, OWL.deprecated)
        if dep is not None and str(dep).lower() in ("true", "1"):
            d = "DEPRECATED. " + (d or "")
        note = one(i, SKOS.note)
        if note:
            d = ((d + " ") if d else "") + "[curation note] " + note
        if d: P.append(f"<p class='def'>{esc(d)}</p>")
        rows = []
        if kind == "class":
            sups = [class_expr(o) for o in g.objects(i, RDFS.subClassOf)]
            eqs = [class_expr(o) for o in g.objects(i, OWL.equivalentClass)]
            if eqs: rows.append(("equivalent to", "<br>".join(eqs)))
            if sups: rows.append(("subclass of", "<br>".join(sups)))
        else:
            dom = [class_expr(o) for o in g.objects(i, RDFS.domain)]
            rng = [datarange_text(o) if kind == "data" else class_expr(o)
                   for o in g.objects(i, RDFS.range)]
            inv = [class_expr(o) for o in g.objects(i, OWL.inverseOf)]
            if dom: rows.append(("domain", ", ".join(dom)))
            if rng: rows.append(("range", ", ".join(esc(r) if kind == "data" else r for r in rng)))
            if inv: rows.append(("inverse of", ", ".join(inv)))
            chars = [loc(t) for t in g.objects(i, RDF.type) if t != OWL.ObjectProperty and t != OWL.DatatypeProperty]
            if chars: rows.append(("characteristics", ", ".join(sorted(esc(c) for c in chars))))
        ext = [esc(loc(o)) for p in (RDFS.subClassOf, OWL.equivalentClass, SKOS.closeMatch)
               for o in g.objects(i, p) if isinstance(o, URIRef) and str(o).startswith(OBO)]
        if ext: rows.append(("external alignment", ", ".join(sorted(set(ext)))))
        if rows:
            P.append("<table>" + "".join(
                f"<tr><th style='width:11rem'>{k}</th><td class='ax'>{v}</td></tr>" for k, v in rows) + "</table>")

entity_section("Classes", classes, "class")
entity_section("Object properties", objprops, "object")
entity_section("Datatype properties", dataprops, "data")
if individuals:
    P.append(f"<h2>Named individuals <span class='badge'>{len(individuals)}</span></h2><table>"
             "<tr><th>Individual</th><th>Types</th></tr>")
    for i in individuals:
        ts = ", ".join(sorted(esc(loc(t)) for t in g.objects(i, RDF.type) if t != OWL.NamedIndividual))
        P.append(f"<tr><td class='mono'>{esc(loc(i))}</td><td class='ax'>{ts}</td></tr>")
    P.append("</table>")
P.append("<h2>Reproducibility</h2><p>This page is generated from <code>OnSIR.ttl</code> by "
         "<code>make_docs.py</code> in the repository, so it cannot drift from the ontology. "
         "The OWL/Turtle files are normative.</p>")
P.append("</div></body></html>")

open("docs/index.html", "w").write("\n".join(P))
print(f"docs/index.html written: {len(''.join(P))} chars, {len(classes)} classes, "
      f"{len(objprops)} object properties, {len(windows)} dose-window classes")
