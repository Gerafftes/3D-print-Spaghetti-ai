from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from enum import StrEnum
import time
from typing import Callable


class DetectionState(StrEnum):
    NORMAL = "normal"
    SUSPECT = "suspect"
    ALERTED = "alerted"
    SNOOZED = "snoozed"


@dataclass(frozen=True)
class FrameAssessment:
    positive: bool
    confidence: float


@dataclass(frozen=True)
class Transition:
    state: DetectionState
    should_alert: bool
    aggregate_confidence: float
    positive_count: int


class DetectionStateMachine:
    def __init__(
        self,
        *,
        window_size: int = 5,
        positives_required: int = 3,
        aggregate_threshold: float = 0.65,
        snooze_seconds: int = 900,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if positives_required > window_size:
            raise ValueError("positives_required cannot exceed window_size")
        self._frames: deque[FrameAssessment] = deque(maxlen=window_size)
        self._positives_required = positives_required
        self._aggregate_threshold = aggregate_threshold
        self._snooze_seconds = snooze_seconds
        self._clock = clock
        self._state = DetectionState.NORMAL
        self._snooze_until = 0.0

    @property
    def state(self) -> DetectionState:
        if self._state is DetectionState.SNOOZED and self._clock() >= self._snooze_until:
            self._state = DetectionState.NORMAL
            self._frames.clear()
        return self._state

    def process(self, confidence: float) -> Transition:
        current_state = self.state
        if current_state is DetectionState.SNOOZED:
            return Transition(current_state, False, 0.0, 0)

        self._frames.append(FrameAssessment(confidence > 0, confidence))
        positives = [frame.confidence for frame in self._frames if frame.positive]
        aggregate = sum(positives) / len(positives) if positives else 0.0
        confirmed = (
            len(positives) >= self._positives_required
            and aggregate >= self._aggregate_threshold
        )

        if confirmed and current_state not in {DetectionState.ALERTED, DetectionState.SNOOZED}:
            self._state = DetectionState.ALERTED
            return Transition(self._state, True, aggregate, len(positives))
        if current_state is DetectionState.ALERTED:
            return Transition(current_state, False, aggregate, len(positives))

        self._state = DetectionState.SUSPECT if positives else DetectionState.NORMAL
        return Transition(self._state, False, aggregate, len(positives))

    def continue_printing(self) -> None:
        self._state = DetectionState.SNOOZED
        self._snooze_until = self._clock() + self._snooze_seconds
        self._frames.clear()

    def acknowledge_pause(self) -> None:
        self._state = DetectionState.ALERTED
