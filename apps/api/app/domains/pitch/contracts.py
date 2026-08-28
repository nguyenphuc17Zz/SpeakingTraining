"""Pitch domain contracts."""

from enum import Enum

from pydantic import BaseModel, Field


class PitchSubMode(str, Enum):
    MINIMAL_PAIR = "pitch_minimal_pair"
    MORA_LENGTH = "mora_length"
    VOWEL_DEVOICING = "vowel_devoicing"
    PITCH_CONTOUR = "pitch_contour"
    PITCH_RECOGNITION = "pitch_recognition"
