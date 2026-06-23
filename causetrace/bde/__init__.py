"""Behavior Design Engine interfaces.

BDE is an opt-in scenario design layer. It defines behavior-generation metadata
only; it does not execute agents or modify runtime behavior.
"""

from .behavior_generator import BehaviorGenerator, BehaviorScenario, PromptVariant
from .failure_injection import FailureInjection
from .multi_agent_simulator import MultiAgentSimulation
from .task_distribution import TaskDistribution

__all__ = [
    "BehaviorGenerator",
    "BehaviorScenario",
    "FailureInjection",
    "MultiAgentSimulation",
    "PromptVariant",
    "TaskDistribution",
]
