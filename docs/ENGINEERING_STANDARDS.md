# ENGINEERING_STANDARDS.md

## MTG Lab Engineering Standards

**Version:** 1.0
**Status:** Accepted

---

# Purpose

This document defines the engineering standards for MTG Lab.

These standards exist to ensure the project remains:

- Maintainable
- Testable
- Reproducible
- Extensible
- Deterministic
- Understandable years into the future

These rules apply to every module, feature, and pull request.

---

# Core Philosophy

MTG Lab is an engineering project—not a prototype.

The project prioritizes:

1. Correctness over speed
2. Simplicity over cleverness
3. Explicitness over implicit behavior
4. Reusable systems over one-off solutions
5. Data-driven design over hardcoded logic

---

# Coding Principles

## Single Responsibility Principle

Every module should have one reason to change.

## Separation of Concerns

Business logic must remain separate from UI, database, API, file I/O, and logging.

## No Magic Numbers

Use named constants or enums instead of unexplained numeric values.

## Self-Documenting Code

Prefer descriptive names over abbreviations.

## Comments

Comments explain why, not what.

---

# Data Standards

- Source data is immutable.
- Persistent objects require stable IDs.
- Relationships use IDs rather than ordering.

---

# Simulation Standards

Simulation must be deterministic when provided identical inputs and RNG seed.

---

# Testing Standards

All major features require unit, integration, and regression tests where appropriate.

---

# Definition of Done

A feature is complete when requirements are met, tests pass, documentation is updated, and the implementation follows these engineering standards.

---

> Build MTG Lab as if it will be maintained for the next decade. Every line of code should make future development easier, not harder.
