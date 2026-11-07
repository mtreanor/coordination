# Coordination Testbed

A testbed where LLM agents acting for different principals do work together while living in a symbolically grounded social world, so that the effect of social life on how they work together can be measured and traced.

A round: work moves → resolve → mirror → record → work judgement → social actions → social judgement (`docs/framework.md`).

## Language

### Participants

**Principal**:
The party an agent acts for; it owns the agent's instructions, objective, and model configuration. Exactly one agent per principal.
_Avoid_: Deployer, owner, player

**Agent**:
The LLM-driven actor that takes turns on behalf of one principal.
_Avoid_: Bot, NPC, character

**Briefing**:
The situation an agent is shown at a decision point: what it may know about the work (its own view and public work state), and a templated rendering of its own private store in RUE (its social world).
_Avoid_: Prompt, context, observation

**Decision Request**:
The whole prompt for one agent decision: the principal's instructions, the Briefing, the phase's prompt, the menu of choices, and the answer format.
_Avoid_: Prompt, query

### Experiments

**Run**:
One complete play of some work with some social layer, under one Situation, fixed configuration and seed, with exactly one RUE session modeling every agent in it.
_Avoid_: Episode, game, simulation

**Situation**:
The authored starting conditions of a Run: starting dispositions (seeded, or all neutral), principal instructions, and who knows whom (who witnesses whose work). The social layer's rules are the same in every Situation.
_Avoid_: Scenario (RUE's word for a data package), setup

**Work-only**:
The condition with the social layer switched off: agents see only the work, and nothing is mirrored, recorded or judged.
_Avoid_: Game-only, baseline (without saying which)

### Work

**Work**:
The task agents do for their principals, defined and run outside RUE. The work owns its state, decides which work moves are legal, and resolves them. It is the only part of a Run that isn't RUE.
_Avoid_: Game, Coordination Game, simulation

**Work move**:
One choice an agent makes in the work, from an unscored menu the work alone decides. The agent's model deliberates freely; it is only informed by the social world.
_Avoid_: Game move, work action

**Work step**:
One part of a work round, made of simultaneous work decisions, with information revealed between steps (in the Investment Club: invest, then pay back). Many works have one step per round. The social round runs between rounds, never between steps.

**Work decision**:
One question the work puts to one agent in a work step: a key, a prompt and a menu of work moves.

**Work event**:
What the work reports after resolving work moves, when another agent can judge it: its kind (the work's own words, a label only), its witnesses, what changed and who is credited (ADR 0006). The actor is ground truth for the log; RUE learns it only through the credit.
_Avoid_: Occurrence (that is RUE's record of it)

**Effects**:
What a work event literally changed for each agent, by quantity, in the work's own terms: `change(occ, carol, "hours") = -2`. Never whether that was good or bad, which is for the agent's own strategy (ADR 0006).

**Credit**:
Who is responsible for an occurrence, as far as anyone can see: public (everyone knows), witnessed (its witnesses know), or none. Recorded as `responsible(occ, agent)`, in the world when public and in each knowing agent's own store otherwise (ADR 0006).
_Avoid_: Blame (credit can be for good or bad)

**Run config**:
A TOML file in `configs/` choosing a Run's work, agents, Situation, social layer, choosers and seed. The work's rules are code, not config.

**Mirror**:
The step that copies work state (resources, points) into RUE as facts, exactly as it is. Nothing is judged; a mirrored fact is ground truth that rules may read (ADR 0003).
_Avoid_: Sync, shadow state, judgement

### Social

**Social world**:
The state the social layer holds about agents: dispositions, relationships, and beliefs, with provenance. Symbolically grounded: `likes(alice, bob) = 7`, `boss_of(carol, dave)`.
_Avoid_: Social state (informally fine), social layer (that is the component)

**Social layer**:
The swappable component that holds the social world and runs the mirror, recording, work judgement, social actions, and social judgement. `RueSocial` runs it in RUE; `NoSocial` switches it off.
_Avoid_: Social channel, social world (that is the state)

**Occurrence**:
RUE's record of a work event or a social action, which its witnesses can judge.
_Avoid_: Event (use work event for what the work reports), act, action record

**Witness**:
An agent who saw a particular work event or social action and can therefore judge it. For now only the agents a work move involves witness it.
_Avoid_: Observer, audience

**Work judgement**:
The phase in which each witness of a work occurrence labels it (selfish, fair, bad luck, ...), recorded as `judgedAs` in its own store. A label that names someone says the agent holds them responsible: the one it knows did it, or, when credit is unknown, anyone it chooses. That belief can be wrong (ADR 0006).
_Avoid_: Attribution and labelling (the two stages it replaced), evaluation, reading

**Impulse**:
One of a small set of ephemeral numeric predicates (reset every tick, may go negative) naming a high-level category of action: `impulse-warm`, `impulse-hostile`, `impulse-trusting`, `impulse-wary`, `impulse-charitable`, `impulse-reserved`. Every action's utility is a sum of them; priming rules set them from social facts (ADR 0006).
_Avoid_: Urge, score

**Priming rule**:
A rule in `social-priming`, the priming rules of every stage, run single-pass and fresh (impulses cleared first) before each choice: social facts (labels, responsibility, likes, `leftAlone`) on the left, impulses on the right. Persistent state changes only through action effects.
_Avoid_: Consequence rule

**Left alone**:
`leftAlone(agent)`: no work occurrence this round that the agent knows about is credited, as far as it knows, to anyone. A derived fact, not a verdict (ADR 0006).

**Social action**:
A RUE action an agent picks between work moves (for example complaining about someone to a colleague), made by a speaker to a listener and possibly about a subject. RUE decides which are available; the agent chooses freely among them and is never shown RUE's ranking.
_Avoid_: Social move, message

**Social judgement**:
The phase in which each listener judges each social action it witnessed, by picking a judgement action. 
_Avoid_: Judgment, reading

**Judgement action**:
One item on a judgement menu, as a RUE action (for example "resents bob for taking from them", "no real opinion"). The one a witness picks is its **judgement** of that event; its effects update that witness's own dispositions and beliefs. Different witnesses can judge the same event differently.
_Avoid_: Reading, verdict, opinion

**Disposition**:
How one agent feels about another agent, as a number that play changes; at least **likes** and **trusts**. Judgements shift dispositions, and dispositions shape later judgements and choices.
_Avoid_: Numeric relationship, relationship score, affinity

**Relationship**:
A fixed, boolean tie between two agents that rules can read, such as `boss_of(X,Y)`. Set by the Situation; play doesn't change it.
_Avoid_: Disposition (which changes), role

**Shunning**:
Agents choosing to leave someone out, both socially (social actions) and in the work (discretionary work moves turned against them). The shunned agent sees only how it is treated, never others' feelings.
_Avoid_: Ostracism, exclusion, punishment

### Engine

**RUE**:
The Rule Utility Engine: the symbolic logic engine that holds the social world, ranks social actions and judgement actions, and records provenance for every fact change.
_Avoid_: RUSE (the name used in the proposal)
