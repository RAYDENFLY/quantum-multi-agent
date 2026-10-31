"""Quantum multi-agent trading system agents package."""

from quantum.agents.contracts import (
    AnalystInput,
    AnalystOutput,
    BankerInput,
    BankerOutput,
    RiskInput,
    RiskOutput,
    ScoutInput,
    ScoutOutput,
    SniperInput,
    SniperOutput,
)
from quantum.agents.scout import ScoutAgent
from quantum.agents.analyst import AnalystAgent
from quantum.agents.sniper import SniperAgent
from quantum.agents.risk import RiskAgent
from quantum.agents.banker import BankerAgent, InvalidExecutionQuantityError, InvalidStateTransitionError
from quantum.agents.orchestrator import PipelineOrchestrator, PipelineRunResult

__all__ = [
    "ScoutInput",
    "ScoutOutput",
    "AnalystInput",
    "AnalystOutput",
    "SniperInput",
    "SniperOutput",
    "RiskInput",
    "RiskOutput",
    "BankerInput",
    "BankerOutput",
    "ScoutAgent",
    "AnalystAgent",
    "SniperAgent",
    "RiskAgent",
    "BankerAgent",
    "InvalidStateTransitionError",
    "InvalidExecutionQuantityError",
    "PipelineOrchestrator",
    "PipelineRunResult",
]
