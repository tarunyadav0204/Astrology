"""Bounded conflict-resolution protocol, shared by the prompt and server."""
from typing import Literal, Optional, Annotated
from datetime import date
from chat.calculator_menu import CalculatorParameters
from pydantic import BaseModel, ConfigDict, Field, model_validator

MAX_ROUNDS = 8

class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

DOUBLE_TRANSIT_CAPABILITY = 'parashari.double_transit'

def conflict_capabilities():
    from chat.verified_chat_pipeline import CAPABILITY_REGISTRY
    return dict(CAPABILITY_REGISTRY)

class DoubleTransitParameters(StrictModel):
    houses: list[Annotated[int, Field(strict=True, ge=1, le=12)]] = Field(min_length=1, max_length=12)
    start_date: date
    end_date: date

    @model_validator(mode='after')
    def valid_range(self):
        if len(self.houses) != len(set(self.houses)):
            raise ValueError('Double-transit houses must be unique')
        if self.end_date <= self.start_date:
            raise ValueError('Double-transit end date must be after start date')
        if self.start_date < date(1800, 1, 1) or self.end_date >= date(2400, 1, 1):
            raise ValueError('Double-transit dates are outside ephemeris coverage')
        if (self.end_date - self.start_date).days > 366 * 120:
            raise ValueError('Double-transit range cannot exceed 120 years')
        return self

class CalculationRequest(StrictModel):
    answer_id: int
    capabilities: list[str] = Field(min_length=1)
    parameters: Optional[CalculatorParameters] = None
    double_transit: Optional[DoubleTransitParameters] = None

    @model_validator(mode='after')
    def valid_parameters(self):
        from chat.calculator_menu import EXTRA_CALCULATORS, validate_parameters
        if self.double_transit is not None and self.parameters is None:
            self.parameters = CalculatorParameters.model_validate(self.double_transit.model_dump(mode='json'))
        for capability in self.capabilities:
            if capability in EXTRA_CALCULATORS:
                validate_parameters(capability, self.parameters.model_dump(mode="json") if self.parameters else None)
        if self.double_transit is not None and DOUBLE_TRANSIT_CAPABILITY not in self.capabilities:
            raise ValueError('Double-transit requests require houses, start_date and end_date; other requests must leave double_transit null')
        return self

class ClaimReview(StrictModel):
    answer_id: int
    claim: str
    assessment: str

class Evidence(StrictModel):
    answer_id: int
    source: str
    finding: str

class Resolution(StrictModel):
    verdict: Literal['contradiction', 'different_contexts', 'insufficient_evidence']
    explanation: str = Field(min_length=1, max_length=6000)
    claims: list[ClaimReview] = Field(min_length=2, max_length=12)
    evidence: list[Evidence] = Field(max_length=20)
    corrected_answer: str = Field(min_length=1, max_length=12000)
    uncertainty: list[str] = Field(max_length=10)

class ConflictTurn(StrictModel):
    action: Literal['calculate', 'clarify', 'resolve']
    question: Optional[str] = Field(default=None, max_length=1200)
    calculations: list[CalculationRequest] = Field(default_factory=list)
    resolution: Optional[Resolution] = None

    @model_validator(mode='after')
    def valid_action(self):
        if self.action == 'calculate' and (not self.calculations or self.question or self.resolution):
            raise ValueError('Calculation round must contain only calculations')
        if self.action == 'clarify' and (not self.question or self.calculations or self.resolution):
            raise ValueError('Clarification round must contain only a question')
        if self.action == 'resolve' and (not self.resolution or self.question or self.calculations):
            raise ValueError('Resolution must contain only the final contract')
        return self


def strictify_schema(schema):
    # Parameter schemas nested in tool definitions must resolve their local $defs.
    def flatten(node, definitions=None):
        if isinstance(node, dict):
            definitions = {**(definitions or {}), **node.get('$defs', {})}
            if '$ref' in node:
                return flatten(definitions[node['$ref'].split('/')[-1]], definitions)
            return {k: flatten(v, definitions) for k,v in node.items() if k != '$defs'}
        if isinstance(node, list): return [flatten(v, definitions) for v in node]
        return node
    schema = flatten(schema)
    def visit(node):
        if isinstance(node, dict):
            if node.get('type') == 'object':
                node.setdefault('properties', {})
                node['additionalProperties'] = False
                node['required'] = list(node.get('properties', {}))
            node.pop('default', None)
            for value in list(node.values()):
                visit(value)
        elif isinstance(node, list):
            for value in node:
                visit(value)
    visit(schema)
    return schema

def strict_schema():
    return strictify_schema(ConflictTurn.model_json_schema())


def validate_turn(raw, answer_ids, rounds, available):
    CAPABILITY_REGISTRY = conflict_capabilities()
    # Final answers sometimes carry stale fields from a previous clarification.
    # They cannot trigger another round; validate the full final contract below.
    if isinstance(raw, dict) and raw.get("action") == "resolve" and raw.get("resolution"):
        raw = {**raw, "question": None, "calculations": []}
    turn = ConflictTurn.model_validate(raw)
    if turn.action != 'resolve' and rounds >= MAX_ROUNDS:
        raise ValueError('The information rounds have been used')
    for request in turn.calculations:
        if request.answer_id not in answer_ids or any(c not in CAPABILITY_REGISTRY for c in request.capabilities):
            raise ValueError('Unknown answer or calculation')
        if len(request.capabilities) != len(set(request.capabilities)):
            raise ValueError('Duplicate calculation')
    if turn.resolution:
        if {c.answer_id for c in turn.resolution.claims} != set(answer_ids):
            raise ValueError('Resolution must assess both selected answers')
        for item in turn.resolution.evidence:
            if item.answer_id not in answer_ids or item.source not in available.get(str(item.answer_id), []):
                raise ValueError('Evidence refers to an unavailable calculation')
    return turn


def resolution_markdown(result, sources):
    # Technical comparisons and source IDs remain in admin metadata, not the chat answer.
    lines = ['## Your answer', result.corrected_answer]
    if result.explanation:
        lines += ['### Why the guidance differed', result.explanation]
    if result.evidence:
        lines += ['### Why this is most likely']
        lines += [f'- {item.finding}' for item in result.evidence]
    if result.uncertainty:
        lines += ['### Keep in mind', result.uncertainty[0]]
    return '\n\n'.join(lines)
