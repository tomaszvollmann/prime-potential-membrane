# PPM Conformance — v1.0

Prime Potential Membrane (PPM) — Conformance Definition  
Freeze v1.0 — Tomasz Vollmann — Vienna, Austria — January 2026

---

## 1. Purpose

This document defines the structural conditions under which a deployment  
MAY claim compatibility with the Prime Potential Membrane (PPM) standard.

Conformance is structural, not symbolic.

PPM is decentralized and non-governing.  
This document does not establish a compliance authority.  
It clarifies architectural integrity.

---

## 2. Conformance Claim

A deployment MAY describe itself as:

- “PPM-compliant”
- “Compatible with PPM v1.x”
- “Implements Prime Potential Membrane”

only if it satisfies the normative invariants defined below.

---

## 3. Normative Structural Invariants (PPM v1.x)

A PPM-compliant deployment MUST:

### 3.1 Discovery

- Expose a discovery endpoint at:

  ```txt
  /.well-known/membrane.json
  ```

- Reference a structural index at:

  ```txt
  /.well-known/membrane/index.json
  ```

### 3.2 Core Modules

Include and correctly reference:

- `identity.json`
- `engagement.json`
- `scopes.json`

### 3.3 Encounter Decision Space

Preserve the explicit decision model:

- **engage**
- **refuse**
- **defer**

Refusal and deferral MUST remain valid outcomes.

These states MUST NOT be removed, invalidated, or redefined in a way that  
eliminates autonomy.

### 3.4 Autonomy

The membrane MUST NOT:

- Claim to compel artificial entities.
- Declare refusal invalid.
- Introduce protocol-level enforcement mechanisms.

Enforcement, if any, exists outside the PPM protocol.
