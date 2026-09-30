# Information limits are enforced in the Briefing, not in RUE rules

RUE rules may read any fact, including ground-truth game state such as every agent's inventory. What an agent is allowed to know is enforced solely by what goes into its Briefing: its own game view, the public game state, and a templated rendering of its own private store, never another agent's store or hidden ground truth. Whether a given judgment rule reads ground truth or only what an agent observed is a per-rule authoring choice, which matters for how judgments diverge between agents.
