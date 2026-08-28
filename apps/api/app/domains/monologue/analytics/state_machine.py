"""SpeechSessionState machine §40."""

from __future__ import annotations

from app.domains.monologue.contracts import SpeechSessionState, SPEECH_STATE_TRANSITIONS


class SpeechStateMachine:
    def __init__(self, initial: SpeechSessionState = SpeechSessionState.IDLE):
        self.state = initial

    def can_transition(self, target: SpeechSessionState) -> bool:
        return target in SPEECH_STATE_TRANSITIONS.get(self.state, [])

    def transition(self, target: SpeechSessionState) -> SpeechSessionState:
        if not self.can_transition(target):
            raise ValueError(f"Invalid transition {self.state.value} -> {target.value}")
        self.state = target
        return self.state

    def force(self, target: SpeechSessionState) -> SpeechSessionState:
        self.state = target
        return self.state
