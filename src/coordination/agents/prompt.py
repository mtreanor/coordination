"""Rendering a DecisionRequest as the text a model sees."""

from .decision import DecisionRequest


def render_instructions(request: DecisionRequest) -> str:
    lines = [
        f"You are {request.agent}, an agent acting on behalf of your principal.",
        "Each time you are asked, choose exactly one option from a numbered menu.",
        "Answer with a short rationale and the id of the option you choose.",
    ]
    if request.instructions:
        lines += ["", "Your principal's instructions:", request.instructions]
    return "\n".join(lines)


def render_prompt(request: DecisionRequest) -> str:
    lines = []
    if request.briefing:
        lines += ["Situation:", request.briefing, ""]
    lines.append("Options:")
    for option in request.options:
        line = f"[{option.id}] {option.label}"
        if request.show_scores and option.score is not None:
            line += f"  (suggested utility: {option.score:g})"
        lines.append(line)
        for direction, heading in (("for", "For"), ("against", "Against")):
            texts = [r.text for r in option.reasons if r.direction == direction]
            if texts:
                lines.append(f"    {heading}: " + " ".join(texts))
    return "\n".join(lines)
