"""Base classes for analysis states and transitions."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class StateTransition:
    """Represents a possible state transition."""
    target_state: str
    condition: str
    description: str
    
    def __str__(self) -> str:
        return f"{self.condition} → {self.target_state}"


class AnalysisState(ABC):
    """Base class for document analysis states."""
    
    # Subclasses declare their possible transitions
    POSSIBLE_TRANSITIONS: Dict[str, StateTransition] = {}
    
    # Subclasses can declare required input fields
    REQUIRED_FIELDS: list = []
    
    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute state logic (programmatic and/or LLM calls).
        
        Args:
            context: Standardized JSON-like data structure containing:
                - document_data: Original document data
                - config: System configuration
                - workflow_results: Results from completed states
                - accumulated_knowledge: Growing knowledge base
                
        Returns:
            State execution results in standardized format:
                - analysis_type: Type of analysis performed
                - results: Analysis findings
                - metadata: Analysis metadata (confidence, pages analyzed, etc.)
                - knowledge: Extracted patterns for context accumulation
        """
        pass
    
    @abstractmethod
    def determine_next_state(self, execution_result: Dict[str, Any], context: Dict[str, Any]) -> Optional[str]:
        """Determine next state based on results and confidence.
        
        Args:
            execution_result: Output from execute() method
            context: Current analysis context
            
        Returns:
            Next state name or None if workflow complete
        """
        pass
    
    def validate_input(self, context: Dict[str, Any]) -> None:
        """Validate required input context.
        
        Args:
            context: Analysis context to validate
            
        Raises:
            ValueError: If required fields are missing
        """
        required_fields = getattr(self, 'REQUIRED_FIELDS', [])
        for field in required_fields:
            if field not in context:
                raise ValueError(f"Missing required field '{field}' for state {self.__class__.__name__}")
    
    @classmethod
    def validate_transitions(cls) -> None:
        """Validate state transitions for correctness.
        
        Raises:
            ValueError: If transitions are invalid (e.g., self-transitions)
        """
        state_name = cls.__name__.lower().replace('state', '')
        
        for transition_key, transition in cls.POSSIBLE_TRANSITIONS.items():
            if transition.target_state == state_name:
                raise ValueError(
                    f"Self-transition not allowed: {cls.__name__} cannot transition to itself "
                    f"(transition '{transition_key}' -> '{transition.target_state}')"
                )
            
            # Could add other validation rules here in the future
            # e.g., check transition naming conventions, etc.
    
    def get_possible_transitions(self) -> Dict[str, StateTransition]:
        """Get all possible transitions from this state."""
        return self.POSSIBLE_TRANSITIONS.copy()
    
    def get_transition_targets(self) -> list:
        """Get list of possible target state names."""
        return [transition.target_state for transition in self.POSSIBLE_TRANSITIONS.values()]
    
    def __str__(self) -> str:
        return self.__class__.__name__
    
    def __repr__(self) -> str:
        transitions = list(self.POSSIBLE_TRANSITIONS.keys())
        return f"{self.__class__.__name__}(transitions={transitions})"