# Coordination Testbed

A testbed where LLM agents acting for different principals play a resource-coordination game while living in a symbolic social world, so that the effect of social life on coordination can be measured and traced.

## Language

### Participants

**Principal**:
The party an agent acts for; it owns the agent's instructions, objective, and model configuration. Exactly one agent per principal.
_Avoid_: Deployer, owner, player

**Agent**:
The LLM-driven actor that takes turns on behalf of one principal.
_Avoid_: Bot, NPC, character

**Briefing**:
The situation an agent is shown at a decision point: its own game view, public game state, a templated rendering of its own private store in RUE, and thread text when that is enabled.
_Avoid_: Prompt, context, observation

**Decision Request**:
The whole prompt for one agent decision: the principal's instructions, the Briefing, the menu of choices, and the answer format.
_Avoid_: Prompt, query

### Experiments

**Run**:
One complete play of the Coordination Game under a fixed configuration and seed, with exactly one RUE session modeling every agent in it.
_Avoid_: Episode, game, simulation

### Game

**Coordination Game**:
The resource game the agents play, defined and run independently of RUE.
_Avoid_: Productive work, game layer, simulation

**Game Move**:
A structured choice an agent makes in the coordination game (for example a trade or a contribution); the game alone decides which game moves are legal.
_Avoid_: Resource move, choice move

**Mirror**:
RUE's symbolic copy of game state, kept current by the game pushing its state changes into RUE after each resolution.
_Avoid_: Sync, shadow state

### Social

**Social Layer**:
The RUE-driven side of the testbed: beliefs agents hold about one another, social moves, and judgment. It can be switched off as a unit.
_Avoid_: Social channel, social world

**Backchannel**:
The phase after game resolution in which agents make social moves about what just happened in play.
_Avoid_: Discussion phase, chat phase

**Thread**:
A backchannel conversation among a set of agents, like a direct message or group text. Members can be added later but do not receive earlier history, and a Thread's effects on its members exist only as RUE facts created by the Social Moves made in it.
_Avoid_: Channel, chat, group

**Social Move**:
A move in the backchannel (for example gossip or an apology), made by a speaker to one or more listeners and possibly about a subject; RUE decides which social moves are available and how they rank.
_Avoid_: Social action, message

**Occurrence**:
A recorded event that happened, whether a game move or a social move, which witnesses can later judge.
_Avoid_: Event, act, action record

**Witness**:
An agent who saw a particular occurrence and is therefore eligible to judge it.
_Avoid_: Observer, audience

**Reading**:
A witness's interpretation of one occurrence it witnessed (for example generous, selfish, thoughtless, or no opinion). The same occurrence can get different readings from different witnesses.
_Avoid_: Judgment (for the single interpretation), verdict, opinion

**Disposition**:
How one agent feels about another agent. Readings shift dispositions, and dispositions shape later readings and choices.
_Avoid_: Relationship score, affinity

**Judgment**:
The phase in which each witness chooses a reading for each occurrence it witnessed; the chosen reading's effects update that witness's private beliefs and dispositions toward the actor. Readings are ranked by rules like any other action, so the same occurrence can be read differently by different witnesses.
_Avoid_: Evaluation, belief update, belief rules

**Inclination**:
How drawn one agent is toward a kind of dealing with another agent (for example trading with or helping them), computed by RUE from dispositions and beliefs and shown beside game options that involve that agent.
_Avoid_: Social utility, bias, preference

### Engine

**RUE**:
The Rule Utility Engine: the symbolic logic engine that holds social state, ranks social moves, and records provenance for every fact change.
_Avoid_: RUSE (the name used in the proposal)
