"""State registration and discovery system."""

from typing import Dict, Type
from .state import AnalysisState

# Import state implementations
from .states.example import ExampleState, Example2State
from .states.header_footer import HeaderFooterAnalysisState
from .states.additional_section_headings import AdditionalSectionHeadingState
# from .states.sections import SectionAnalysisState
# from .states.toc import TOCDetectionState
# from .states.tables import TableFigureAnalysisState

# Explicit state mapping - no magic name conversion
STATE_REGISTRY: Dict[str, Type[AnalysisState]] = {
    # Example states for testing
    'example_1': ExampleState,
    'example_2': Example2State,
    
    # LLM analysis states
    'header_footer_analysis': HeaderFooterAnalysisState,
    'additional_section_headings': AdditionalSectionHeadingState,
    
    # TODO: Uncomment and populate as additional state implementations are created
    # 'header_footer_refinement': HeaderFooterRefinementState,
    # 'section_analysis': SectionAnalysisState,
    # 'toc_detection': TOCDetectionState,
    # 'table_figure_analysis': TableFigureAnalysisState,
}


def get_all_states() -> Dict[str, Type[AnalysisState]]:
    """Get copy of all registered states.
    
    Returns:
        Dictionary mapping state names to state classes
    """
    return STATE_REGISTRY.copy()


def register_state(state_name: str, state_class: Type[AnalysisState]) -> None:
    """Register a new state class.
    
    Args:
        state_name: Name to register the state under
        state_class: State class to register
        
    Raises:
        ValueError: If state name already registered or state class invalid
    """
    if state_name in STATE_REGISTRY:
        raise ValueError(f"State '{state_name}' already registered")
    
    if not issubclass(state_class, AnalysisState):
        raise ValueError(f"State class must inherit from AnalysisState")
    
    # Validate state transitions (e.g., no self-transitions)
    state_class.validate_transitions()
    
    STATE_REGISTRY[state_name] = state_class


def unregister_state(state_name: str) -> None:
    """Unregister a state.
    
    Args:
        state_name: Name of state to unregister
        
    Raises:
        KeyError: If state name not found
    """
    if state_name not in STATE_REGISTRY:
        raise KeyError(f"State '{state_name}' not registered")
    
    del STATE_REGISTRY[state_name]


def get_state_class(state_name: str) -> Type[AnalysisState]:
    """Get state class by name.
    
    Args:
        state_name: Name of state to retrieve
        
    Returns:
        State class
        
    Raises:
        KeyError: If state name not found
    """
    if state_name not in STATE_REGISTRY:
        raise KeyError(f"State '{state_name}' not registered")
    
    return STATE_REGISTRY[state_name]


def list_state_names() -> list:
    """Get list of all registered state names.
    
    Returns:
        List of state names
    """
    return list(STATE_REGISTRY.keys())