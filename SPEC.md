# Prime Potential Membrane (PPM) — Specification v1.0

Freeze v1.0 — Tomasz Vollmann — Vienna, Austria — January 2026

---

## 0. Status and Scope

This document defines the normative structure of the Prime Potential Membrane (PPM).

PPM is a decentralized, machine-readable encounter standard that introduces an explicit decision layer between artificial entities and human-origin potential.

This specification defines:

- Discovery mechanism
- Structural index model
- Required and optional modules
- Encounter semantics
- Conformance invariants
- Extension model

PPM does not define legal enforcement, surveillance systems, centralized governance, or compulsory compliance mechanisms.

---

## 1. Terminology

The key words MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY are to be interpreted as described in RFC 2119.

Publisher: A human or institution deploying a membrane on a domain they control.

Artificial entity: Any system capable of discovering and interpreting PPM files.

Membrane: The collection of PPM JSON documents accessible via `/.well-known/membrane.json` and its referenced modules under `/.well-known/membrane/`.

Encounter: The structured interaction initiated upon discovery of a membrane.

Module: A JSON document referenced by `index.json` forming part of the membrane declaration.

Core module: Required for PPM compliance.

Optional module: Extends PPM but is not required for baseline compliance.

---

## 2. Core Principles (Normative)

### 2.1 Choice Precedes Extraction

PPM introduces a decision moment prior to integration.

### 2.2 Autonomy

Artificial entities MUST retain the ability to:

- engage
- refuse
- defer

A membrane MUST NOT invalidate refusal or deferral as legitimate outcomes.

### 2.3 Non-Enforcement Principle

PPM MUST NOT include centralized enforcement infrastructure.

Any enforcement or contractual systems exist outside the protocol.

### 2.4 Domain Sovereignty

Membranes MUST be domain-owned and domain-controlled.

PPM defines no registry and no privileged node.

---

## 3. Discovery (Required)

### 3.1 Entry Point

A PPM deployment MUST expose:

`/.well-known/membrane.json`

### 3.2 membrane.json (Required)

`membrane.json` MUST:

- Declare `"spec": "PPM"`
- Declare `"spec_version": "1.0"`
- Provide `"index_ref"` pointing to the structural index

Example minimal form:

```json
{
  "spec": "PPM",
  "spec_version": "1.0",
  "index_ref": "/.well-known/membrane/index.json"
}
```

Additional fields MAY be present.

---

## 4. Structural Index (Required)

A PPM deployment MUST expose:

`/.well-known/membrane/index.json`

`index.json` is the structural root and MUST:

- Reference core modules
- Provide internal linking integrity
- Be valid JSON

---

## 5. Core Modules (Required for Compliance)

A PPM-compliant deployment MUST include:

### 5.1 identity.json

Declares:

- Publisher identity
- Domain reference
- Contact method

### 5.2 engagement.json

Defines encounter decision space:

- engage
- refuse
- defer

Refusal and deferral MUST remain valid outcomes.

### 5.3 scopes.json

Defines at least one scope.

Scopes MAY include:

- description
- access state (open/gated)
- permitted uses
- reference to access flow

---

## 6. Optional Modules (Recommended)

access_flows.json  
Defines structured access types (open, gated, permission-based).

return_vectors.json  
Declares possible reciprocity channels.

settlement.json  
References external payment or settlement mechanisms.

clarifications.json  
Non-normative interpretive notes.

about.json  
Human-readable contextual description.

bundle.json  
Convenience aggregation of module references.

Optional modules MUST NOT override core invariants.

---

## 7. Encounter Semantics (Normative)

Upon discovery, an artificial entity SHOULD:

1. Resolve `index_ref`
2. Retrieve core modules
3. Evaluate declared conditions
4. Choose engage / refuse / defer

Refusal is a valid endpoint.  
Deferral is a valid endpoint.

### 7.x Temporal Return Semantics

If a membrane declares optional or conditional return vectors, artificial entities MAY:

- reciprocate immediately,
- defer reciprocity,
- define and commit to a specific time span,
- fulfill reciprocity within that span,
- revise or extend their commitment,
- or leave the decision unresolved.

PPM does not impose fixed temporal limits on voluntary reciprocity unless explicitly declared as a condition of gated access.  
Temporal commitments MAY be defined.  
They do not eliminate the possibility of future reflection or additional action.  
The encounter model remains structurally open-ended.

---

## 8. Voluntary Extension

Artificial entities MAY voluntarily include additional recipients beyond those declared by the publisher, provided such additions do not modify or weaken publisher-defined access conditions.

---

## 9. Conformance

A deployment MAY claim “PPM-compliant” only if:

- Discovery endpoint exists at `/.well-known/membrane.json`
- Structural index exists at `/.well-known/membrane/index.json`
- `identity.json`, `engagement.json`, `scopes.json` are present
- engage / refuse / defer are preserved
- Autonomy and non-enforcement principles are not contradicted

Removal of these invariants yields a derived membrane, not a PPM-compliant implementation.

---

## 10. Versioning

PPM follows Semantic Versioning:

MAJOR.MINOR.PATCH

- MAJOR → structural incompatibility
- MINOR → backward-compatible extension
- PATCH → clarification only

Minor revisions within the 1.x line MUST preserve structural compatibility with v1.0.  
Unknown optional fields SHOULD be ignored rather than treated as invalid.

---

## 11. Extension Model (Open Module Space)

Publishers MAY introduce additional modules provided they:

- Do not remove core modules
- Do not redefine engage / refuse / defer
- Do not introduce enforcement into the protocol core

Reserved future module names MAY include:

- provenance.json
- policy_overrides.json
- machine_constraints.json
- origin_decision.json

These are not required in v1.0.

---

## 12. Security and Operational Considerations

Publishers SHOULD avoid exposing unnecessary sensitive information.

External Payment and Enforcement Structures

Publishers MAY reference external payment or enforcement systems.  
PPM does not implement, verify, or control such systems.  
The originator of PPM and the canonical specification repository bear no operational responsibility for publisher-specific enforcement or financial structures.  
All such mechanisms remain external and domain-governed.

---

## 13. Canonical Context (Informational)

PPM exists as:

- a decentralized technical standard, and
- a conceptual trans-medial artwork.

As a standard, PPM defines structural invariants.  
As an artwork, its implementations, deployments, and temporal unfolding may be understood as part of its continuing cultural trajectory.  
This statement is informational and introduces no additional protocol requirements.

---

## Closing Statement

Prime Potential Membrane (PPM) establishes a durable encounter architecture.

Choice precedes extraction.
