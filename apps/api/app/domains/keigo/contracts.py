"""Keigo contracts — answer candidates, analyses, and provenance."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class HonorificType(str, Enum):
    SONKEIGO = "sonkeigo"
    KENJOUGO_I = "kenjougo_i"
    KENJOUGO_II = "kenjougo_ii"
    TEINEIGO = "teineigo"
    BIKAGO = "bikago"
    NEUTRAL = "neutral"
    CASUAL = "casual"


class Register(str, Enum):
    TAMEGUCHI = "tameguchi"
    POLITE = "polite"
    BUSINESS_POLITE = "business_polite"
    BUSINESS_KEIGO = "business_keigo"
    VERY_FORMAL = "very_formal"


class DoubleKeigoStatus(str, Enum):
    ACCEPTED_ESTABLISHED = "accepted_established"
    GENERALLY_INAPPROPRIATE = "generally_inappropriate"
    CONTEXT_DEPENDENT = "context_dependent"
    NONSTANDARD = "nonstandard"


class KeigoAssessmentDTO(BaseModel):
    role_accuracy: float = Field(ge=0, le=100)
    register_accuracy: float = Field(ge=0, le=100)
    keigo_accuracy: float = Field(ge=0, le=100)
    grammar: float = Field(ge=0, le=100)
    naturalness: float = Field(ge=0, le=100)
    context_fit: float = Field(ge=0, le=100)
    reaction: float = Field(ge=0, le=100)
    independence: float = Field(ge=0, le=100)
    completeness: float = Field(ge=0, le=100)
    overall: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    double_keigo: dict[str, Any] | None = None
    provenance: dict[str, Any] | None = None
