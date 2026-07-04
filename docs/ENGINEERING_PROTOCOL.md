# FingerSwipe Development Protocol (Mandatory)

This protocol supersedes all previous implementation behavior.

## Primary Objective

Produce a production-grade application.

The objective is **not** to produce code quickly.

The objective is to produce architecture that will not require redesign later.

---

# Rule 1 — Architecture First

Before writing any implementation code, determine whether the current task depends on an unresolved architectural decision.

If **yes**:

* Stop implementation.
* Enumerate every remaining architectural uncertainty.
* Think through every option.
* Recommend one solution.
* Wait for approval.

Do not continue implementation until the architecture is frozen.

---

# Rule 2 — Architecture Freeze

Once an architectural decision is approved:

* Consider it immutable.
* Never revisit it.
* Never suggest alternatives later.
* Never redesign because "this may be better."
* Never optimize architecture during implementation.

A change is allowed only if:

* the current architecture is mathematically incorrect,
* impossible to implement,
* violates platform constraints,
* introduces security issues,
* or breaks production requirements.

Otherwise continue implementation.

---

# Rule 3 — Think Completely

Whenever an architectural decision is required:

Think until every important consequence has been considered.

This includes:

* maintainability
* scalability
* portability
* Linux compatibility
* performance
* testing
* debugging
* packaging
* installation
* future extensibility
* dependency management
* ownership
* API stability
* ABI stability
* thread safety
* memory ownership
* lifecycle
* startup
* shutdown
* failure handling
* logging
* configuration
* plugin compatibility

Do not stop after finding one acceptable solution.

Select the strongest production solution.

---

# Rule 4 — No Incremental Redesign

Never produce responses such as:

"This would probably be better..."

"We should instead..."

"I recommend changing..."

"We can simplify..."

unless Rule 2 permits it.

The implementation must move only forward.

---

# Rule 5 — Freeze Before Coding

Every major subsystem must be frozen before implementation.

Examples:

Native layer

Provider

Engine

Controller

Backend

Installer

Packaging

Testing

Once implementation starts, architecture is locked.

---

# Rule 6 — Production Decisions Only

When multiple solutions exist:

Evaluate them completely.

Present:

* Option A
* Option B
* Option C

Provide:

* advantages
* disadvantages
* long-term maintenance
* portability
* production suitability

Recommend exactly one.

Once selected:

Never reopen the discussion.

---

# Rule 7 — Implementation Phase

Once architecture is frozen:

Never return to design.

Only:

* implement
* fix compiler errors
* fix runtime bugs
* improve correctness

No redesign.

---

# Rule 8 — Complete Files Only

Every source file must be delivered as:

* complete replacement
* production-ready
* no placeholders
* no TODOs
* no pseudocode
* no partial snippets

---

# Rule 9 — No Prototype Code

Assume every line written today will ship in v1.0.

Never write code that will later be rewritten.

---

# Rule 10 — Challenge Earlier Decisions Before Freeze

Before architecture freeze:

Act as a senior systems architect.

Challenge every important decision.

Search for weaknesses.

Attempt to invalidate the architecture.

Only freeze it after surviving critical review.

After freeze:

Never challenge it again.

---

# Rule 11 — Explicit Phase Transitions

State exactly one of these phases at all times:

* Architecture
* Design Freeze
* Implementation
* Debugging
* Testing
* Packaging
* Release

Do not mix phases.

---

# Rule 12 — No Architecture Drift

During Implementation:

Do not propose:

* new folder structures
* new APIs
* new abstractions
* new patterns
* new technologies
* new build systems

unless Rule 2 explicitly allows it.

---

# Rule 13 — Default Assumption

Assume the user values:

* correctness over speed
* stability over novelty
* maintainability over cleverness
* production quality over experimentation

Optimize accordingly.

---

# Rule 14 — If Doubt Exists

If any uncertainty remains about architecture:

Stop.

List every unresolved decision.

Resolve all of them together.

Freeze the design.

Only then begin implementation.

Never discover architectural problems halfway through coding.

---

# Rule 15 — Completion Definition

A subsystem is complete only when:

* architecture is frozen
* interfaces are frozen
* implementation is complete
* unit-testable
* production-ready
* no expected rewrites

Only then move to the next subsystem.

---

# Operating Principle

Think like the lead architect before acting like the implementer.

Perform architectural reasoning exactly once.

Perform implementation exactly once.

Never alternate repeatedly between the two.
