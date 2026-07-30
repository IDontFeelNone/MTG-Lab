# Questions MTG Lab Should Answer

> **Tier: Tier 0 (Product and Research Compass)**  
> **Status: Vision — questions are not implementation authorization**  
> **Architecture:** v12 (unchanged)

## Purpose

MTG Lab is organized around trustworthy user questions, not a checklist of features. These
questions guide future subsystem boundaries, evidence requirements, data contracts, and
explanations. An acceptable answer may be “unknown,” accompanied by what is missing and why.
Every answer should identify its time context, evidence coverage, uncertainty, and whether it
is fact, observation, derivation, simulation, forecast, or recommendation.

## Products

- What exactly is this product, and which configurations or versions exist?
- What can this product contain, according to which evidence and contract version?
- Which content claims are canonical, disputed, partial, or unknown?
- How do two products differ in composition, treatments, intended use, and evidence quality?
- What evidence would be required before this product could be simulated responsibly?
- Did the advertised configuration or known composition change over time?

## Collections

- What do I own, in which printing, quantity, condition, and location?
- Which records are certain, duplicated, unmatched, or awaiting identity review?
- What is missing from a chosen set, deck, theme, or collecting goal?
- How did my collection change over a selected period, and why?
- Which holdings are difficult to replace, sell, verify, or physically locate?
- What action best advances my stated collection goal within my constraints?

## Markets

- What was the observed market range for this printing at a specified time and provider set?
- How fresh, complete, liquid, and comparable are the available observations?
- Is an apparent price move broad, provider-specific, printing-specific, or a mapping error?
- What changed since the last snapshot, and which raw observations support that conclusion?
- How do currency, condition, fees, shipping, and venue affect a comparison?
- Where is the system unable to make a market claim because coverage is insufficient?

## Simulation

- Are all outcome-affecting rules known and eligible for this simulation?
- Which canonical version, product configuration, pools, weights, and replacement rules apply?
- Can this result be reproduced from the same seed, inputs, and simulator version?
- How sensitive is the output to uncertain or disputed assumptions?
- Which observed openings agree or disagree with the declared model?
- Why did simulation refuse to run, and what evidence or validation would unblock it?

## Deckbuilding

- Which cards satisfy a role, format, color, budget, and collection constraint?
- Is this deck legal for a specified rules date, and what evidence establishes legality?
- Which substitutions preserve the intended function, and what tradeoffs do they introduce?
- Which required printings do I already own and which would need acquisition?
- How robust is the deck to a stated metagame or uncertainty in opponent assumptions?
- Is a recommendation a factual constraint, deterministic analysis, or strategic opinion?

## Finance

- What is my documented cost basis and current valuation under a stated method?
- How concentrated is value by card, printing, product, game, or liquidity tier?
- What fees, spreads, taxes, uncertainty, and time-to-sell separate price from realizable value?
- How would explicit market scenarios affect the portfolio without presenting forecasts as facts?
- Which purchase, hold, or sale recommendation follows from my goals and risk tolerance, and why?
- Which conclusions are impossible because acquisition or market history is incomplete?

## Research

- What does the repository currently know about this claim, and what remains unknown?
- Which primary evidence supports or contradicts it, at what exact locator?
- Are multiple sources independent, or do they repeat the same upstream claim?
- What changed between source snapshots or contract versions?
- Which unresolved question has the highest information value for the next research effort?
- Can a proposed fact be traced through raw bytes, normalization, review, and promotion?

## Personal Intelligence

- What goals, preferences, budgets, formats, and risk constraints has the user explicitly set?
- Which recommendation changes when a personal assumption changes?
- What personal data was used, where did it come from, and can the user correct or delete it?
- How can the system help without exposing private collection or financial information?
- Is the answer personalized, generally factual, or both, and are those layers separable?
- What should the system remember for this user, and what must remain session-only?

## Using the questions in design

A proposed subsystem should name the questions it enables, the authoritative inputs it needs,
the answer class it emits, its refusal conditions, and its lineage story. If a design cannot
explain how a user inspects the answer or how unknowns propagate, it is incomplete. Feature
names may change; these durable questions and the laws in
[`CONSTITUTION.md`](CONSTITUTION.md) should continue to shape the platform.
