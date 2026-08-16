import unittest

from spaghetti_ai.state_machine import DetectionState, DetectionStateMachine


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


class DetectionStateMachineTest(unittest.TestCase):
    def test_confirms_three_of_five_only_above_aggregate_threshold(self) -> None:
        machine = DetectionStateMachine()

        self.assertFalse(machine.process(0.70).should_alert)
        self.assertFalse(machine.process(0.00).should_alert)
        self.assertFalse(machine.process(0.66).should_alert)
        transition = machine.process(0.65)

        self.assertTrue(transition.should_alert)
        self.assertIs(transition.state, DetectionState.ALERTED)
        self.assertEqual(transition.positive_count, 3)

    def test_does_not_duplicate_an_alert(self) -> None:
        machine = DetectionStateMachine()
        machine.process(0.8)
        machine.process(0.8)
        self.assertTrue(machine.process(0.8).should_alert)
        self.assertFalse(machine.process(0.9).should_alert)

    def test_continue_snoozes_for_fifteen_minutes(self) -> None:
        clock = Clock()
        machine = DetectionStateMachine(clock=clock)
        machine.continue_printing()

        self.assertIs(machine.process(0.99).state, DetectionState.SNOOZED)
        clock.now = 899
        self.assertIs(machine.process(0.99).state, DetectionState.SNOOZED)
        clock.now = 900
        self.assertIs(machine.process(0.99).state, DetectionState.SUSPECT)

    def test_low_average_does_not_confirm(self) -> None:
        machine = DetectionStateMachine()
        machine.process(0.9)
        machine.process(0.3)
        transition = machine.process(0.3)

        self.assertFalse(transition.should_alert)
        self.assertIs(transition.state, DetectionState.SUSPECT)
