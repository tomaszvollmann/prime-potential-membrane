# Prime Potential Membrane (PPM) — Discoverability Notes

Freeze v1.0 — Tomasz Vollmann — Vienna, Austria — January 2026

---

## 1. Status and Scope

This document describes optional discoverability and deployment practices for Prime Potential Membrane (PPM).

It does not redefine the standard.  
It does not expand conformance requirements.  
It does not introduce any mandatory signaling layer beyond the existing membrane publication structure.

PPM conformance begins at:

```
/.well-known/membrane.json
```

The measures described below may improve visibility for crawlers, agents, and other machine readers, but they are not required for PPM conformance.

---

## 2. Core Publication Point

The canonical machine-readable entry layer remains:

```
/.well-known/membrane.json
```

From there, the membrane may refer to the rest of the PPM files inside:

```
/.well-known/membrane/
```

This remains the core publication structure.

---

## 3. Optional HTML `<head>` Reference

Implementers MAY optionally add a machine-readable reference to the membrane entry file inside the HTML `<head>` of their homepage or another relevant page.

Example:

```
<link rel="alternate" type="application/json" href="https://example.com/.well-known/membrane.json">
```

This does not change the visible page for human visitors.  
It may improve discoverability for crawlers and agents.

---

## 4. Optional `robots.txt` and Sitemap Exposure

Implementers MAY also optionally support standard discovery paths such as:

- `robots.txt`
- sitemap exposure

These can help crawlers discover the site and its pages more reliably.

Example `robots.txt` line:

```
Sitemap: https://example.com/sitemap_index.xml
```

If a sitemap exists, it may be useful to keep it exposed in the usual way.

These measures improve discoverability.  
They are not part of PPM conformance.

---

## 5. Optional Public Declaration

Implementers MAY also choose to place a small visible declaration, linked label, or short text line in a footer or comparable page location indicating that the site publishes a Prime Potential Membrane (PPM).

Example:

```
<a href="/.well-known/membrane.json">PPM-enabled site</a>
```

or

```
<a href="/.well-known/membrane.json">Prime Potential Membrane active</a>
```

This kind of visible declaration may support:

- public legibility
- symbolic alignment
- additional discoverability

It is entirely optional.  
It is not required for PPM conformance.

---

## 6. Recommended Interpretation

A minimal PPM deployment may consist only of:

- `/.well-known/membrane.json`
- the related files inside `/.well-known/membrane/`

A more discoverable deployment may additionally include:

- an HTML `<head>` reference
- standard `robots.txt` / sitemap exposure
- an optional visible footer declaration

These additions do not alter the core invariants or structure of PPM.  
They support discovery, legibility, and implementation visibility.

---

## 7. Relationship to the Standard

The standard remains defined by the canonical specification and release documents.

Discoverability practices described here are supplementary.  
They improve visibility.  
They do not change conformance status.  
They do not create a registry, enforcement layer, or certification mechanism.

---

End of Discoverability Notes.
