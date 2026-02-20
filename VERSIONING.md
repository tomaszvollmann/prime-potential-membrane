# Prime Potential Membrane (PPM) — Versioning

Freeze v1.0 — Tomasz Vollmann — Vienna, Austria — January 2026

---

## 1. Versioning Model

PPM follows **Semantic Versioning**:

```txt
MAJOR.MINOR.PATCH
```

Example:

```txt
1.0.0
1.1.0
1.0.1
```

Version numbers apply to the specification, not to individual deployments.

---

## 2. Version Components

### MAJOR

A MAJOR version increment indicates structural incompatibility.

A MAJOR increment occurs only if:

- The discovery mechanism changes  
- Required endpoints are removed or redefined  
- The encounter decision space (engage / refuse / defer) is altered  
- Core structural invariants are modified in a non-compatible way  

MAJOR versions signal architectural shifts.

---

### MINOR

A MINOR version increment indicates backward-compatible extension.

A MINOR increment may include:

- New optional modules  
- Additional optional fields  
- Clarifications that preserve compatibility  
- Extended descriptive semantics  

Minor revisions within the v1.x line MUST preserve conformance invariants.

---

### PATCH

A PATCH version increment indicates non-structural correction.

A PATCH increment may include:

- Typographical fixes  
- Documentation clarifications  
- Non-normative improvements  
- Editorial adjustments  

PATCH updates MUST NOT alter required behavior.

---

## 3. Compatibility Rule

Artificial entities interpreting PPM MUST treat:

- v1.0.x as compatible  
- v1.1.x as compatible  
- v2.0.x as structurally incompatible  

Compatibility is determined by preserved invariants, not by branding.

---

## 4. Freeze Releases

Freeze releases declare stable architectural baselines.

Freeze v1.0 represents the first canonical release of PPM.

All deployments referencing:

```json
"spec_version": "1.0"
```

are aligned with Freeze v1.0 unless explicitly modified.

---

End of Versioning Model.
