# MTG Lab Architecture

Purpose

MTG Lab is designed as a modular research platform for Magic: The Gathering. The architecture emphasizes correctness, extensibility, reproducibility, and maintainability over short-term implementation speed.

The system is designed so that support for new Magic products can be added primarily by importing new product data rather than rewriting application logic.

## Core Design Principles

### 1. Data-Driven Design

No product-specific logic should exist in the simulation engine.

Products define themselves through structured data.

Examples include:

- Products
- Cards
- Printings
- Pack definitions
- Slot definitions
- Probability tables

The engine interprets the data rather than containing special-case rules for individual products.

### 2. Modular Architecture

Each major system has a single responsibility.

Major modules include:

- Database
- Import Pipeline
- Validation Engine
- Simulation Engine
- Analytics Engine
- Collection Manager
- Market Intelligence
- API
- Web Interface

Each module should remain independently testable.

### 3. Reproducible Results

Every simulation should be reproducible.

Each simulation records:

- Product
- Simulator version
- Database version
- Random seed
- Timestamp
- Configuration

Running the same simulation with identical inputs should produce identical outputs.

### 4. Verification First

Before simulations are trusted, imported data should be validated.

Validation includes:

- Missing cards
- Duplicate identifiers
- Invalid references
- Broken probability tables
- Slot consistency
- Product integrity

The goal is to ensure statistical analyses are built on verified data.

## High-Level Architecture

```text
                User
                  │
                  ▼
            Web Interface
                 │
          Command Line Interface
                 │
                 ▼
             REST API Layer
                 │
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
 Simulation Engine   Analytics Engine
        │                 │
        └────────┬────────┘
                 ▼
          Database Layer
                 │
      ┌──────────┴──────────┐
      ▼                     ▼
 Import Pipeline      Market Data
```

## Engineering Philosophy

MTG Lab favors correctness over convenience, reproducibility over randomness, documentation alongside implementation, modular components over tightly coupled systems, and evidence-based analysis over assumptions.