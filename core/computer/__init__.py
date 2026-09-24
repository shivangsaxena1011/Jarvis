"""
SHIVANI Phase 17: Advanced Computer Autonomy & GUI Reasoning Package.
"""

from core.computer.agent import ComputerAutonomyAgent
from core.computer.checkpoint_engine import CheckpointEngine
from core.computer.execution_engine import ExecutionEngine
from core.computer.expectation_engine import ExpectationEngine
from core.computer.models import (
    ActionExecutionResult,
    ActionType,
    ApplicationContext,
    ApplicationState,
    CommandRisk,
    ComputerAction,
    DesktopObservation,
    ElementSource,
    ElementType,
    ErrorType,
    MonitorLayout,
    RectBounds,
    StateDifference,
    TaskCheckpoint,
    UIElement,
)
from core.computer.observation_engine import ObservationEngine
from core.computer.recovery_engine import ComputerRecoveryEngine, LoopDetector
from core.computer.resource_lock import ActionPriority, ResourceLockManager
from core.computer.semantic_graph import UIGraphNode, UISemanticGraph
from core.computer.spatial_engine import SpatialEngine
from core.computer.synthetic import SyntheticGUIEnvironment
from core.computer.terminal_controller import TerminalController, TerminalExecutionResult
from core.computer.uia_engine import UIAEngine
from core.computer.visual_grounding import GroundingResult, MultiSourceGrounder

__all__ = [
    "ComputerAutonomyAgent",
    "ObservationEngine",
    "ExecutionEngine",
    "ExpectationEngine",
    "ComputerRecoveryEngine",
    "LoopDetector",
    "CheckpointEngine",
    "ResourceLockManager",
    "ActionPriority",
    "TerminalController",
    "TerminalExecutionResult",
    "UIAEngine",
    "UISemanticGraph",
    "UIGraphNode",
    "SpatialEngine",
    "MultiSourceGrounder",
    "GroundingResult",
    "SyntheticGUIEnvironment",
    "DesktopObservation",
    "UIElement",
    "ElementType",
    "ElementSource",
    "ApplicationContext",
    "ApplicationState",
    "ComputerAction",
    "ActionType",
    "StateDifference",
    "ActionExecutionResult",
    "TaskCheckpoint",
    "ErrorType",
    "CommandRisk",
    "RectBounds",
    "MonitorLayout",
]
