"""Shared helpers for tracking LLM token usage and estimating costs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Mapping

MODEL_PRICING: dict[str, Dict[str, float]] = {
    "gpt-5.2": {"input": 1.75, "cached_input": 0.175, "output": 14.0},
    "gpt-5.1": {"input": 1.25, "cached_input": 0.125, "output": 10.0},
    "gpt-5": {"input": 1.25, "cached_input": 0.125, "output": 10.0},
    "gpt-5-mini": {"input": 0.25, "cached_input": 0.025, "output": 2.0},
    "gpt-5-nano": {"input": 0.05, "cached_input": 0.005, "output": 0.40},
}


@dataclass(slots=True)
class TokenUsage:
    input_tokens: int = 0
    cached_input_tokens: int = 0
    output_tokens: int = 0

    def add_mapping(self, usage: Mapping[str, int]) -> None:
        self.input_tokens += int(usage.get("input_tokens", 0) or 0)
        self.cached_input_tokens += int(usage.get("cached_input_tokens", 0) or 0)
        self.output_tokens += int(usage.get("output_tokens", 0) or 0)

    def add_usage(self, other: "TokenUsage") -> None:
        self.input_tokens += other.input_tokens
        self.cached_input_tokens += other.cached_input_tokens
        self.output_tokens += other.output_tokens

    def total_tokens(self) -> int:
        return self.input_tokens + self.cached_input_tokens + self.output_tokens


def record_usage(bucket: dict[str, TokenUsage], model: str, usage: TokenUsage) -> None:
    if usage.input_tokens == 0 and usage.cached_input_tokens == 0 and usage.output_tokens == 0:
        return
    aggregate = bucket.setdefault(model, TokenUsage())
    aggregate.add_usage(usage)


def estimate_model_cost(model: str, usage: TokenUsage) -> float:
    pricing = MODEL_PRICING.get(model)
    if not pricing:
        return 0.0
    billable_input = max(usage.input_tokens - usage.cached_input_tokens, 0)
    cached_input = min(usage.cached_input_tokens, usage.input_tokens)
    # Pricing table is per 1M tokens; convert usage to millions before multiplying.
    input_cost = (billable_input / 1_000_000) * pricing["input"]
    cached_cost = (cached_input / 1_000_000) * pricing["cached_input"]
    output_cost = (usage.output_tokens / 1_000_000) * pricing["output"]
    return input_cost + cached_cost + output_cost
