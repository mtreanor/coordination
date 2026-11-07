# Briefings show the agent's RUE state; social menus are RUE's top five, with reasons

Decided Nov 7, 2026 (Mike). Builds on ADR 0003 (information limits at the Briefing) and ADR 0006 (work events).

## Context

RUE ranks social actions and judgement actions, but the agent chooses (`docs/framework.md`). Showing RUE's scores, or ordering a menu by them, hands the agent RUE's ranking and interferes with its strategy. Still, the agent should know *why* an option is on its menu: the social world is meant to inform the choice. And the agent's Briefing should give it the social world it has lived through, not just the work.

## Decision

**A round, as the agent sees it.**

1. **Work move.** The Briefing holds the work state, the raw history of choices (descriptive, public and relevant information only, no interpretation), and the agent's full RUE state. The agent chooses a work move freely; the work moves forward.
2. **The work reports** each event to RUE as an external action (ADR 0006).
3. **Three RUE stages**, each a decision per binding (work judgement and social judgement: one per occurrence the agent knows of; social actions: one per agent):
   - the stage's priming rules run (`social-priming`, fresh);
   - the menu is RUE's **top five** options by utility, shown in random order (seeded by the Run), ties broken at random;
   - each option comes with its **reasons**: the provenance of its utility, the priming rules that fired and the facts on their left-hand side, rendered as text by RUE (each predicate's `toString`), never by an LLM. No number about the ranking appears: no utility, no impulse value, no rule weight. Facts keep their own values ("You like bob 3 out of 10") or tiers. Reasons that pull against an option are shown too. An option can have no reasons;
   - the agent chooses freely.

**What a social decision's Briefing holds:** the agent's RUE state, the available options, and their reasons. Not the work Briefing.

**The agent's RUE state** is everything in RUE the agent knows: its private store, the public facts, and the occurrences it witnessed, including a raw list of the social events it took part in or heard (what it was told, who confronted it, what it called things). It never includes what the agent didn't witness (ADR 0003).

**Doing nothing is a RUE choice.** Every stage has an option to stay out of it ("no real opinion", "say nothing"), with utility from `impulse-reserved`, which priming rules raise from the agent's state. It is not forced onto the menu: it appears when it ranks in the top five.

## Status (Nov 7)

Built: the top-five menu with random ties, the occurrence's text in each judgement decision, social decisions' Briefings without the work, and reasons. RUE renders reasons (`engine.reasonsFor`, served on every candidate as `reasons`; RUE's docs/actions.md#reasons): the premise facts of the rules that set the numerics a utility reads, through each predicate's `briefing` template, marked for or against, each once. A template's `{text[N]}` shows an occurrence's text. A test fails when a priming rule reads a predicate with no `briefing` template. Not yet: the agent's full RUE state (text templates for every predicate an agent can know, filtered to what it witnessed).

Observed: a reason belongs to the impulse, not the option, so an impulse about the agent alone (charitable, reserved) brings facts about other people to every option that reads it; and recent label verdicts make lists long.

## Consequences

- The menu's cut to five is the one place RUE's ranking shapes a choice: it decides what the agent considers, not what it picks.
- Every predicate an agent can know needs a `toString` template, and every priming rule's premises need to be renderable, before Briefings are complete.
- Reasons tie a choice to the facts and rules behind it, so a Run's log can say why an option was offered as well as which was chosen.
