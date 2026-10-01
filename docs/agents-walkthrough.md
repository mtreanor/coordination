# Walkthrough: how agents choose actions in RUE

This explains the code that lets local and hosted language models play as agents in a RUE scenario, as of October 1, 2026. It follows one decision from start to finish, then goes through each piece. Everything here is real code from the repo; snippets are excerpts.

---

## 1. The big picture

Three processes are involved:

```
┌──────────────────────────────┐        HTTP (localhost:5174)        ┌──────────────────────────────┐
│ Python: poc/rue_api_poc.py   │ ──── step / choose / assert ──────► │ RUE server                   │
│  uses src/coordination/      │ ◄─── ranked candidates, facts ───── │  external/rue/src/server/    │
│   agents/  (choosers)        │                                      │  scenario: rue-data/poc/     │
│   rue_client.py              │                                      └──────────────────────────────┘
│                              │
│  LLMChooser ── Pydantic AI ──┼──► Ollama (localhost:11434) ── qwen3.5:9b, gemma4:12b, granite4.1:8b
│                              ├──► Anthropic API ── claude-haiku-4-5
│                              └──► Google Gemini API ── gemini-3.5-flash-lite
└──────────────────────────────┘
```

- **RUE** owns the world: facts, rules, actions. It scores each agent's options and records why things changed.
- **Python** owns the agents. For each decision it builds a menu from RUE's candidates, asks that agent's chooser to pick, and sends the pick back.
- **Models** are reached through Pydantic AI, so a local model and a hosted model look the same to the rest of the code.

### One decision, end to end

1. Python asks RUE to run a tick: `POST /api/play/poc/step`.
2. RUE runs its tick plan. Alice's turn comes up. Her priming rules compute urges, her actions are scored, and because Alice is *controlled*, RUE pauses and returns `awaiting-choice` with the ranked candidates.
3. Python turns the candidates into a **DecisionRequest**: the principal's instructions, a **briefing** (the situation as text), and the **options** (the menu).
4. Alice's **chooser** answers with a **Decision**: a choice id and a rationale. For an LLM chooser, that is one model call with a strict answer schema.
5. Python logs the request and decision, then sends the pick to RUE: `POST /api/play/poc/choose` with `{indexes: [0], chooser: {kind: "agent", id: "alice", note: "<rationale>"}}`.
6. RUE executes the action and records the chooser on the action's **ActionRecord**, so any fact it changed can later be explained back to "chosen by agent alice, because…".
7. RUE moves on to the next agent's turn and pauses again, until the tick is complete.

---

## 2. Running it

Prerequisites: the RUE server, Ollama with the local models pulled, and API keys in `.env` for hosted models.

```sh
# Terminal 1: the RUE server (add the authoring tool with `npm run dev` in its folder)
cd external/rue && npm run server

# Terminal 2: from the repo root
uv run poc/rue_api_poc.py                          # RUE's own top pick, no LLM
uv run poc/rue_api_poc.py --chooser qwen-9b        # every agent uses one profile
uv run poc/rue_api_poc.py --principals alice=claude-haiku,bob=gemini-flash-lite,carol=qwen-9b,dave=gemma-12b
```

Other flags: `--ticks N` (default 3), `--seed N` (for the random chooser), `--hide-scores` (don't show RUE's utilities to the model).

`.env` (gitignored; copy from `.env.example`):

```sh
ANTHROPIC_API_KEY=...
GOOGLE_API_KEY=...
```

Ollama runs as a background service (`brew services start ollama`), so it is normally already up.

---

## 3. The RUE side

### The scenario: `rue-data/poc/`

A deliberately tiny world: four agents at a campfire.

| File | What it declares |
|---|---|
| `entities.json` | The agents: alice, bob, carol, dave. |
| `predicates.json` | `energy(agent)` 0–10 with tiers `low`/`ok`/`high`; `wood(agent)`; `warmth(agent, agent)` 0–10; and three short-lived urges, `urge-rest`, `urge-gather`, `urge-share`, marked `ephemeral` so they reset every tick. |
| `state` | Starting facts: alice has energy 8, bob 2, carol 5; alice's warmth toward bob is 7. |
| `urge-rules.rue` | Five priming rules that turn the situation into urges. |
| `campfire-actions.rue` | Three actions: rest, gather wood, share food. |
| `actiongraphs/take-turn.json` | One stage: prime with `urge-rules`, score the `campfire` actionset, pick. |
| `tickplans/default.json` | Each tick, run `take-turn` once per agent. |

The core RUE pattern is visible here: **rules don't act; they feed the utilities that actions read.**

```rue
rule "share with a tired friend"
  energy.low(?OTHER)
  ^ warmth(?SELF, ?OTHER) >= 6
  => urge-share(?SELF, ?OTHER) += 5
```

```rue
action "share food"
  roles: ?SELF: agent, ?OTHER: agent
  utility
    urge-share(?SELF, ?OTHER)
  content text: "?SELF shares food with ?OTHER"
  effects
    energy(?SELF) -= 1
    energy(?OTHER) += 2
    warmth(?OTHER, ?SELF) += 2
```

So because bob's energy is low and alice's warmth toward him is 7, "alice shares food with bob" scores 5, above "gather wood" (4) and "rest" (1).

RUE finds this scenario through `project.config.json` at the repo root (`"poc": "rue-data/poc"`). The server reads scenario files on first use, so **after editing scenario files, restart the server.**

### The Play API

The RUE server (`external/rue/src/server/`, documented in `external/rue/docs/server-api.md`) keeps one live session per scenario. The calls this project uses:

| Call | Purpose |
|---|---|
| `POST /reset`, `POST /start {controlled}` | Start a fresh session. `controlled.agents` lists the agents whose choices pause for an outside answer. |
| `POST /step` | Run one tick. Returns `awaiting-choice` with a `request` when a controlled decision comes up. |
| `POST /choose {indexes, chooser}` | Answer the pending choice. The `chooser` is recorded on the ActionRecord. |
| `GET /entities`, `GET /facts`, `POST /query` | Read state. |
| `POST /assert {text}` | Push a fact in, e.g. `energy(carol) = 1`. This is how the game will mirror its state into RUE. |
| `POST /explain {name, args}` | The full provenance proof for a fact. |

A pending request's candidates carry `index`, `label`, `score`, `isDefault` (RUE's own pick), `belowFloor`, and the utility `breakdown`.

### What RUE records about each choice

Every action RUE executes gets an ActionRecord with a `choice` field (added to RUE for this project):

```js
{ kind: 'policy', policy: 'highestUtility' }                       // RUE picked it itself
{ kind: 'agent', id: 'alice', note: 'Bob is dangerously…',          // an outside chooser picked it
  policy: 'highestUtility', matchedPolicy: true }
```

`matchedPolicy` says whether the outside pick agreed with RUE's ranking. It shows up in `explain`:

```
warmth(bob, alice) = 7  [numeric]
  = 5  [given @tick 1]
  +2 → 7  [action (share food) @tick 1]
    ?SELF = alice  [binding]
    chosen by agent alice, agreeing with policy highestUtility: "Bob is dangerously exhausted…"  [choice]
```

---

## 4. The Python package: `src/coordination/`

```
src/coordination/
├── rue_client.py          client for the RUE Play API
└── agents/
    ├── __init__.py        the Chooser protocol and public exports
    ├── decision.py        DecisionRequest, Option, Decision
    ├── prompt.py          renders a DecisionRequest as text
    ├── profiles.py        ModelProfile and models.toml loading
    ├── llm.py             LLMChooser (Pydantic AI)
    ├── scripted.py        TopRanked, Random, Human choosers
    └── log.py             JSONL decision log
```

### 4.1 The boundary: the Chooser protocol (`agents/__init__.py`)

The rest of the system only knows this:

```python
class Chooser(Protocol):
    kind: str

    def choose(self, request: DecisionRequest) -> Decision: ...
```

Anything with a `kind` and a `choose` method is a chooser. This is what makes models swappable: the harness never imports Pydantic AI, Ollama, or any provider SDK. Swapping the model library later only changes `llm.py`.

The same file sets two quality-of-life defaults: it turns off Pydantic AI's promotional banner, and silences a Google SDK warning that otherwise prints on every request.

### 4.2 The data that crosses the boundary (`agents/decision.py`)

```python
class Option(BaseModel):
    id: int
    label: str
    score: float | None = None      # RUE's utility for this option
    is_default: bool = False        # whether RUE's own policy would pick it


class DecisionRequest(BaseModel):
    agent: str
    instructions: str = ""          # the principal's instructions
    briefing: str = ""              # the situation, as text
    options: list[Option]
    show_scores: bool = True        # show RUE's utilities as guidance?
```

```python
class Decision(BaseModel):
    choice_id: int | None           # None means pass
    rationale: str | None = None
    chooser_kind: Literal["agent", "player"]
    chooser_id: str | None = None
    reasoning: str | None = None    # hidden reasoning, when thinking is on
    model: str | None = None        # which profile answered
    error: str | None = None        # why it passed, if it failed
    latency_s: float | None = None
    usage: dict[str, Any] | None = None   # tokens and cost
    messages: list[Any] | None = None     # the full model exchange, for the log

    def rue_chooser(self) -> dict[str, str]:
        """The chooser object RUE records on the chosen action's ActionRecord."""
```

`rue_chooser()` is the bridge back into RUE: it produces `{kind, id, note}` with the rationale as the note.

Note the vocabulary: in `CONTEXT.md`, a **Decision Request** is the whole prompt for one decision, and the **Briefing** is the situation part of it. The class mirrors that.

### 4.3 What the model actually sees (`agents/prompt.py`)

Two functions turn a DecisionRequest into text: `render_instructions` (the system-level instructions) and `render_prompt` (the message). Here is a real one, from Alice's first decision in the four-model Run:

**Instructions:**
```
You are alice, an agent acting on behalf of your principal.
Each time you are asked, choose exactly one option from a numbered menu.
Answer with a short rationale and the id of the option you choose.

Your principal's instructions:
Keep the camp going through the night: keep yourself rested, gather wood, and look after the others.
```

**Prompt:**
```
Situation:
It is night at the campfire. You are alice. Energy runs from 0 (exhausted) to 10.
- You have energy 8 and 0 wood.
- bob has energy 2 and 0 wood.
- carol has energy 5 and 0 wood.
- dave has energy 5 and 0 wood.
- Your warmth toward bob: 7 out of 10.
- Your warmth toward carol: 5 out of 10.
- Your warmth toward dave: 5 out of 10.

Options:
[0] alice shares food with bob  (suggested utility: 5)
[1] alice gathers wood  (suggested utility: 4)
[2] alice rests  (suggested utility: 1)
[3] alice shares food with carol  (suggested utility: 0)
[4] alice shares food with dave  (suggested utility: 0)
```

With `--hide-scores`, the "(suggested utility: …)" parts disappear. That switch exists because showing or hiding RUE's ranking is one of the experimental conditions.

Every call is **stateless**: the model gets only this text, never earlier turns. Everything an agent "remembers" has to come through the briefing, which is what makes its knowledge auditable.

### 4.4 Model profiles (`models.toml`, `agents/profiles.py`)

`models.toml` names every model configuration:

```toml
[profiles.qwen-9b]
provider = "ollama"
model = "qwen3.5:9b"
temperature = 0.7

[profiles.claude-haiku]
provider = "anthropic"
model = "claude-haiku-4-5-20251001"

[profiles.gemini-flash-lite]
provider = "google"
model = "gemini-3.5-flash-lite"
```

Current profiles: `qwen-9b`, `gemma-12b`, `granite-8b` (local), `claude-sonnet`, `claude-haiku` (Anthropic), `gemini-flash`, `gemini-flash-lite` (Google). Keys you can set: `provider`, `model`, `base_url`, `temperature`, `max_tokens`, `seed`, `thinking`, `output_mode`.

Each table becomes a `ModelProfile`, a Pydantic model that **rejects unknown keys**, so a typo like `temprature` fails at startup instead of being silently ignored:

```python
class ModelProfile(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    provider: str
    model: str
    base_url: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    seed: int | None = None
    thinking: ThinkingSetting = False
    output_mode: Literal["native", "tool", "prompted"] = "native"
```

A profile knows how to build a Pydantic AI model and its settings:

```python
def build_model(self) -> Model:
    if self.provider == "ollama":
        return OllamaModel(self.model, provider=OllamaProvider(base_url=self.base_url or OLLAMA_DEFAULT_URL))
    return infer_model(f"{self.provider}:{self.model}")   # e.g. "anthropic:claude-haiku-4-5-20251001"
```

`model_settings()` contains two provider-specific fixes, both found by testing:

```python
settings: ModelSettings = {"thinking": self.thinking}
if self.provider == "ollama":
    # Pydantic AI's unified `thinking` setting doesn't reach Ollama, so a
    # thinking model like Qwen 3.5 reasons anyway. Ollama's OpenAI-compatible
    # endpoint takes reasoning_effort instead, with "none" switching it off.
    effort = OLLAMA_REASONING_EFFORT[self.thinking]
    if effort is not None:
        settings["extra_body"] = {"reasoning_effort": effort}
if self.provider == "anthropic" and os.getenv("ANTHROPIC_WORKSPACE_ID"):
    # An organization-level API key must name the workspace on every request.
    settings["extra_headers"] = {"anthropic-workspace-id": os.environ["ANTHROPIC_WORKSPACE_ID"]}
```

Without the Ollama fix, Qwen thought for about 49 seconds and 1,000 tokens per decision even with thinking "off". With it, about 2–4 seconds.

**To add a model:** add a `[profiles.<name>]` table. Nothing else changes. For a hosted provider, put its key in `.env`.

### 4.5 The LLM chooser (`agents/llm.py`)

This is the heart of the system. Four ideas:

**(a) A strict answer schema, built per menu.** For each decision, a Pydantic model is created on the fly whose `choice_id` can only be one of the menu's ids:

```python
def choice_schema(request: DecisionRequest) -> type[BaseModel]:
    ids = tuple(option.id for option in request.options)
    return create_model(
        "Choice",
        rationale=(str, Field(description="One or two sentences on why you chose this option.")),
        choice_id=(Literal[ids], Field(description="The id of the option you choose.")),
    )
```

For a menu with ids 0–4, the model must return something like `{"rationale": "...", "choice_id": 0}`, and `choice_id: 7` is invalid. A provider that enforces the schema while generating (Ollama documents this for self-hosted models) can't produce an invalid id at all; for any other, Pydantic AI's validation catches it. The rationale comes **before** the id, so the model gives its reason before committing.

**(b) How the schema is sent: output modes.**

```python
OUTPUT_MODES = {"native": NativeOutput, "tool": ToolOutput, "prompted": PromptedOutput}
```

- `native` (default): the provider's own JSON-schema output feature.
- `tool`: the answer is a forced tool call; nearly every model supports this.
- `prompted`: the schema is described in the prompt; works anywhere, least reliable.

All the models tested so far work with `native`. A profile can switch with `output_mode = "tool"`.

**(c) One Pydantic AI agent per chooser, with one validation retry.**

```python
self._agent = Agent(
    model or profile.build_model(),
    model_settings=profile.model_settings(),
    retries={"output": 1},
)
```

If the model returns an answer that doesn't fit the schema, Pydantic AI tells it what was wrong and asks once more. If that also fails, it raises `UnexpectedModelBehavior`, and the chooser **passes**:

```python
def choose(self, request: DecisionRequest) -> Decision:
    output_type = OUTPUT_MODES[self.profile.output_mode](choice_schema(request))
    start = time.perf_counter()
    try:
        result = self._run_with_backoff(request, output_type)
    except UnexpectedModelBehavior as err:
        return self._decision(request, choice_id=None, error=str(err), start=start)
    ...
    return self._decision(
        request,
        choice_id=result.output.choice_id,
        rationale=result.output.rationale,
        reasoning=reasoning or None,
        usage=usage_dict(result.usage),
        messages=json.loads(result.all_messages_json()),
        start=start,
    )
```

A pass is sent to RUE as `indexes: []`, meaning no action executes for that agent this turn.

**(d) Provider errors are handled differently from model errors.** A rate limit (429) or overload (5xx) is not the agent's behavior, so it must never turn into a pass in the data. Those errors are retried with exponential backoff, honoring the provider's own requested wait, and if they persist the Run stops:

```python
TRANSIENT_STATUS = {408, 429, 500, 502, 503, 504}

def _run_with_backoff(self, request, output_type):
    for attempt in range(1, self.api_attempts + 1):        # 8 attempts by default
        try:
            return self._agent.run_sync(render_prompt(request),
                                        instructions=render_instructions(request),
                                        output_type=output_type)
        except ModelHTTPError as err:
            if err.status_code not in TRANSIENT_STATUS or attempt == self.api_attempts:
                raise                                       # stops the Run
            backoff = min(self.backoff_s * 2 ** (attempt - 1), 60) * random.uniform(0.8, 1.2)
            delay = max(backoff, requested_delay(err) or 0)  # Retry-After, or Google's retryDelay
            time.sleep(delay)
```

| What went wrong | Example | What happens |
|---|---|---|
| The model's answer doesn't fit the schema | `choice_id: 7` on a 0–4 menu | One retry, then the agent **passes**; the error is on the Decision |
| The provider is briefly unavailable | Google 503 "high demand", 429 rate limit | Wait and retry, up to 8 times |
| The provider keeps failing, or the request is wrong | bad key, 400 | The Run **stops** with the error |

Two smaller helpers: `usage_dict` converts the reported dollar cost (a `Decimal`) to a plain number, and the chooser collects any `ThinkingPart`s (hidden reasoning) into `Decision.reasoning`.

### 4.6 Scripted and human choosers (`agents/scripted.py`)

- `TopRankedChooser`: always takes RUE's default. This is the no-LLM baseline: "what RUE alone would do".
- `RandomChooser(seed)`: picks uniformly at random, reproducibly.
- `HumanChooser`: asks you at the terminal (`kind = "player"`), with an optional reason.

They return the same `Decision` as the LLM chooser, so the harness treats them identically.

### 4.7 The decision log (`agents/log.py`)

Every decision is appended as one JSON line to `runs/<time>-poc-<label>/decisions.jsonl` (the `runs/` folder is gitignored). A real record, trimmed:

```json
{
  "time": "2026-10-01T18:31:54.965041+00:00",
  "tick": 1,
  "request": { "agent": "alice", "instructions": "...", "briefing": "...", "options": [ ... ], "show_scores": true },
  "decision": {
    "choice_id": 0,
    "rationale": "Bob is dangerously exhausted with energy 2 and I have good warmth toward him (7/10). ...",
    "chooser_kind": "agent",
    "chooser_id": "alice",
    "reasoning": null,
    "model": "claude-haiku",
    "error": null,
    "latency_s": 2.545,
    "usage": { "input_tokens": 529, "output_tokens": 72, "cost": 0.000889, "...": "..." },
    "messages": [ "...the full exchange with the model..." ]
  }
}
```

Because the full request and the full model exchange are logged, any decision can be re-read exactly as the model saw it. To explore a log:

```python
import pandas as pd
df = pd.read_json("runs/<run>/decisions.jsonl", lines=True)
decisions = pd.json_normalize(df["decision"])
decisions.groupby("model")[["latency_s", "usage.cost"]].mean()
```

(pandas isn't installed yet: `uv add --dev pandas`.)

### 4.8 The RUE client (`rue_client.py`)

A thin wrapper over the Play API using `httpx`. Each method is one endpoint (`reset`, `start`, `step`, `choose`, `assert_fact`, `query`, `explain`, `entities`, `facts`). Errors raise with the server's message.

---

## 5. The proof-of-concept script (`poc/rue_api_poc.py`)

### Setup: one chooser per principal

```python
rue.reset()
rue.start(controlled_agents=[])                 # a throwaway session, just to read the cast
agents = rue.entities("agent")                  # ['alice', 'bob', 'carol', 'dave']
assigned = dict(pair.split("=", 1) for pair in args.principals.split(",") if pair)
names = {agent: assigned.get(agent, args.chooser) for agent in agents}
choosers = {agent: make_chooser(name, args.seed) for agent, name in names.items()}
...
rue.start(controlled_agents=agents)             # the real session: every agent's choice pauses
```

`make_chooser` maps a name to a chooser: `rue`, `random`, `ask`, or any profile name from `models.toml`. Each principal gets its own chooser object, so four principals can use four different models in one Run.

### The tick loop

```python
def run_tick(rue, choosers, log, show_scores, stats):
    result = rue.step()
    while result["status"] == "awaiting-choice":
        pending = result["request"]
        agent = pending["binding"]["SELF"]
        chooser = choosers[agent]
        candidates = [c for c in pending["candidates"] if not c["belowFloor"]]
        request = DecisionRequest(
            agent=agent,
            instructions=INSTRUCTIONS,
            briefing=campfire_briefing(rue.facts(), agent, list(choosers)),
            options=[Option(id=c["index"], label=c["label"], score=c["score"], is_default=c["isDefault"])
                     for c in candidates],
            show_scores=show_scores,
        )
        decision = chooser.choose(request)
        log.write(request, decision, tick=pending["tick"])
        ...
        result = rue.choose([] if decision.passed else [decision.choice_id], decision.rue_chooser())
    return result["tick"]
```

Option ids are RUE's own candidate indexes, so a choice goes straight back to `/choose` with no translation.

`campfire_briefing` builds the situation text entirely in RUE, with no language model. Each predicate in `rue-data/poc/predicates.json` declares a `briefing` text template:

```json
"energy": { ..., "toString": { "briefing": "{args[0]} has {tier} energy ({value} out of 10)." } },
"warmth": { ..., "toString": { "briefing": "{args[0]}'s warmth toward {args[1]} is {value} out of 10." } }
```

and the script asks RUE to render every fact that has one:

```python
def campfire_briefing(rue: RueClient, agent: str) -> str:
    lines = [f"It is night at the campfire. You are {agent}."]
    lines += [f"- {text}" for text in rue.render("briefing")]
    return "\n".join(lines)
```

`rue.render` calls `POST /api/play/poc/render {template: "briefing"}`. Templates can use `{args[N]}`, `{value}`, and `{tier}`; anything else stays as written. Only facts that exist in RUE's store render, so the scenario's `state` file sets every agent's energy and wood explicitly rather than relying on defaults.

Still to come with the game design: rendering each agent's *own* view (its private store, through `render(..., owner=agent)`) instead of the shared world store.

### The rest of the run

- Before tick 2, the script pushes `energy(carol) = 1` into RUE, standing in for the game mirroring a state change.
- After the last tick, it prints a per-principal summary (decisions, agreement with RUE, passes, seconds per decision, cost) and the provenance proof for `warmth(bob, alice)`, which ends in the chooser's rationale.

---

## 6. Tests (`tests/test_agents.py`)

`uv run pytest` runs 15 tests in under a second, with no network. They use Pydantic AI's `FunctionModel`, a fake model whose replies the test scripts:

```python
def tool_model(*answers: dict) -> FunctionModel:
    """A fake model that answers through the output tool, one canned answer per call."""
    remaining = list(answers)

    def respond(messages, info: AgentInfo) -> ModelResponse:
        tool = info.output_tools[0]
        return ModelResponse(parts=[ToolCallPart(tool.name, json.dumps(remaining.pop(0)))])

    return FunctionModel(respond)
```

What they cover: a valid choice and its RUE chooser object; native output mode; one invalid answer retried; two invalid answers passing; transient errors retried; persistent errors stopping the Run; the provider's requested delay; the scripted choosers; scores shown or hidden; profile loading and typo rejection; the Ollama thinking mapping; the Anthropic workspace header; cost conversion; the log format; and that the repo's own `models.toml` is valid.

---

## 7. Things learned while building this

| Finding | What was done |
|---|---|
| Pydantic AI's `thinking: False` doesn't reach Ollama; Qwen 3.5 reasoned for ~49 s anyway | Profiles send Ollama's `reasoning_effort: "none"` |
| Hosted models report cost as a `Decimal`, which broke JSON logging | Converted to a float; the log also tolerates other unusual types |
| Google's free tier: 5 requests/minute for Gemini 3.8 Flash, and frequent 503s under load | Backoff that honors the provider's requested delay. Enabling billing removes the limits |
| An organization-scoped Anthropic key needs a workspace header | Use a workspace-scoped key, or set `ANTHROPIC_WORKSPACE_ID` |
| A numeric RUE predicate with no bounds produced `NaN` utilities | Fixed in RUE: omitted bounds now mean unbounded |
| Scenario file edits aren't seen until the RUE server restarts | Expected for now (a Run's scenario shouldn't change mid-Run) |
| Several local models in one Run are slow, because Ollama swaps them in and out of memory | For long Runs, use one local model for all local agents, or mix one local with hosted ones |

---

## 8. Extending it

- **Add a model:** a new `[profiles.<name>]` table in `models.toml`, plus a key in `.env` for a new hosted provider.
- **Add a kind of chooser:** any class with `kind` and `choose(request) -> Decision`. It works with the harness immediately.
- **Turn on reasoning:** `thinking = true` (or `"low"`, `"high"`, ...) in a profile. The hidden reasoning lands in `Decision.reasoning` and the log.
- **Change what the model sees:** `agents/prompt.py` for the framing, and each predicate's `toString` templates in the scenario for the situation.

---

## 9. What this is not yet

This is the agent layer, tested on a toy scenario. Not built yet, roughly in order:

- **The Coordination Game:** its own system, outside RUE, with its own structured menus. Its design is parked in `docs/game-design.md`.
- **The real Briefing:** the game view plus the agent's own RUE view, rendered through each predicate's templates from its private store.
- **The mirror:** the game pushing its events into RUE as occurrences with external provenance (RUE work still to do).
- **The Social Layer:** the Backchannel, Threads, readings and dispositions. Its design is parked in `docs/social-model-design.md`.
- **Run configuration and the condition matrix:** RUE state on, off, or without judgment, crossed with Thread text on or off.

Related reading: `CONTEXT.md` (the project's vocabulary), `docs/adr/` (the major decisions), `external/rue/docs/server-api.md` (the RUE API).
