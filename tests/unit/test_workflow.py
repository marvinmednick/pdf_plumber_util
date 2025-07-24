"""Unit tests for workflow state machine components."""

import pytest
from typing import Dict, Any, Optional
from unittest.mock import Mock, patch

from pdf_plumb.workflow.state import AnalysisState, StateTransition
from pdf_plumb.workflow.registry import (
    register_state, unregister_state, get_state_class, 
    list_state_names, get_all_states
)
from pdf_plumb.workflow.state_map import WorkflowStateMap
from pdf_plumb.workflow.orchestrator import AnalysisOrchestrator, WorkflowExecutionError


# Test fixtures

class TestState(AnalysisState):
    """Test state for unit testing."""
    
    POSSIBLE_TRANSITIONS = {
        'next': StateTransition('test_2', 'condition_met', 'Go to test state 2'),
        'end': StateTransition(None, 'terminate', 'End workflow')
    }
    
    REQUIRED_FIELDS = ['document_data']
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        self.validate_input(context)
        return {
            'analysis_type': 'test_analysis',
            'results': {'processed': True},
            'metadata': {'confidence': 0.9},
            'knowledge': {'test_pattern': 'found'}
        }
    
    def determine_next_state(self, execution_result: Dict[str, Any], context: Dict[str, Any]) -> Optional[str]:
        return 'test_2'


class TestState2(AnalysisState):
    """Second test state for unit testing."""
    
    POSSIBLE_TRANSITIONS = {
        'complete': StateTransition(None, 'analysis_complete', 'Workflow complete')
    }
    
    REQUIRED_FIELDS = ['document_data']
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        self.validate_input(context)
        return {
            'analysis_type': 'test_analysis_2',
            'results': {'final': True},
            'metadata': {'confidence': 0.95},
            'knowledge': {'final_pattern': 'complete'}
        }
    
    def determine_next_state(self, execution_result: Dict[str, Any], context: Dict[str, Any]) -> Optional[str]:
        return None


class BrokenState(AnalysisState):
    """State with broken transitions for testing validation."""
    
    POSSIBLE_TRANSITIONS = {
        'broken': StateTransition('nonexistent_state', 'always', 'Points to nonexistent state')
    }
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {'analysis_type': 'broken'}
    
    def determine_next_state(self, execution_result: Dict[str, Any], context: Dict[str, Any]) -> Optional[str]:
        return 'nonexistent_state'


@pytest.fixture
def clean_registry():
    """Clean state registry before and after tests."""
    # Store original registry
    from pdf_plumb.workflow.registry import STATE_REGISTRY
    original_registry = STATE_REGISTRY.copy()
    
    # Clear registry for testing
    STATE_REGISTRY.clear()
    
    yield
    
    # Restore original registry
    STATE_REGISTRY.clear()
    STATE_REGISTRY.update(original_registry)


# State Tests

@pytest.mark.unit
class TestStateTransition:
    """Test StateTransition class."""
    
    def test_state_transition_creation(self):
        """Test creating a state transition."""
        transition = StateTransition('next_state', 'condition', 'description')
        
        assert transition.target_state == 'next_state'
        assert transition.condition == 'condition'
        assert transition.description == 'description'
    
    def test_state_transition_str(self):
        """Test string representation of transition."""
        transition = StateTransition('next_state', 'condition', 'description')
        assert str(transition) == 'condition → next_state'


@pytest.mark.unit
class TestAnalysisState:
    """Test AnalysisState base class."""
    
    def test_state_validation_success(self):
        """Test successful input validation."""
        state = TestState()
        context = {'document_data': 'value'}
        
        # Should not raise
        state.validate_input(context)
    
    def test_state_validation_failure(self):
        """Test input validation failure."""
        state = TestState()
        context = {}  # Missing required field
        
        with pytest.raises(ValueError, match="Missing required field 'document_data'"):
            state.validate_input(context)
    
    def test_state_get_possible_transitions(self):
        """Test getting possible transitions."""
        state = TestState()
        transitions = state.get_possible_transitions()
        
        assert len(transitions) == 2
        assert 'next' in transitions
        assert 'end' in transitions
        assert transitions['next'].target_state == 'test_2'
    
    def test_state_get_transition_targets(self):
        """Test getting transition target states."""
        state = TestState()
        targets = state.get_transition_targets()
        
        assert 'test_2' in targets
        assert None in targets  # Terminal transition
        assert len(targets) == 2
    
    def test_state_str_repr(self):
        """Test string representations."""
        state = TestState()
        
        assert str(state) == 'TestState'
        assert 'TestState' in repr(state)
        assert 'transitions=' in repr(state)


# Registry Tests

@pytest.mark.unit
class TestStateRegistry:
    """Test state registry functionality."""
    
    def test_register_state(self, clean_registry):
        """Test registering a new state."""
        register_state('test_state', TestState)
        
        assert 'test_state' in list_state_names()
        assert get_state_class('test_state') == TestState
    
    def test_register_duplicate_state(self, clean_registry):
        """Test registering duplicate state name."""
        register_state('test_state', TestState)
        
        with pytest.raises(ValueError, match="State 'test_state' already registered"):
            register_state('test_state', TestState2)
    
    def test_register_invalid_state_class(self, clean_registry):
        """Test registering invalid state class."""
        class NotAState:
            pass
        
        with pytest.raises(ValueError, match="State class must inherit from AnalysisState"):
            register_state('invalid', NotAState)
    
    def test_unregister_state(self, clean_registry):
        """Test unregistering a state."""
        register_state('test_state', TestState)
        assert 'test_state' in list_state_names()
        
        unregister_state('test_state')
        assert 'test_state' not in list_state_names()
    
    def test_unregister_nonexistent_state(self, clean_registry):
        """Test unregistering nonexistent state."""
        with pytest.raises(KeyError, match="State 'nonexistent' not registered"):
            unregister_state('nonexistent')
    
    def test_get_nonexistent_state(self, clean_registry):
        """Test getting nonexistent state."""
        with pytest.raises(KeyError, match="State 'nonexistent' not registered"):
            get_state_class('nonexistent')
    
    def test_get_all_states(self, clean_registry):
        """Test getting all registered states."""
        register_state('test_1', TestState)
        register_state('test_2', TestState2)
        
        all_states = get_all_states()
        assert len(all_states) == 2
        assert all_states['test_1'] == TestState
        assert all_states['test_2'] == TestState2


# State Map Tests

@pytest.mark.unit
class TestWorkflowStateMap:
    """Test workflow state map functionality."""
    
    def test_generate_empty_state_map(self, clean_registry):
        """Test generating empty state map."""
        state_map = WorkflowStateMap.generate_state_map()
        assert state_map == {}
    
    def test_generate_state_map(self, clean_registry):
        """Test generating state map with registered states."""
        register_state('test_1', TestState)
        register_state('test_2', TestState2)
        
        state_map = WorkflowStateMap.generate_state_map()
        
        assert len(state_map) == 2
        assert 'test_1' in state_map
        assert 'test_2' in state_map
        
        # Check test_1 state info
        test_1_info = state_map['test_1']
        assert test_1_info['class'] == 'TestState'
        assert test_1_info['required_fields'] == ['document_data']
        assert test_1_info['is_terminal'] == True
        assert len(test_1_info['transitions']) == 2
        assert 'test_2' in test_1_info['possible_next_states']
    
    def test_validate_valid_state_map(self, clean_registry):
        """Test validating a valid state map."""
        register_state('test_1', TestState)
        register_state('test_2', TestState2)
        
        errors = WorkflowStateMap.validate_state_map()
        assert errors == []
    
    def test_validate_broken_state_map(self, clean_registry):
        """Test validating state map with broken references."""
        register_state('broken', BrokenState)
        
        errors = WorkflowStateMap.validate_state_map()
        assert len(errors) > 0
        assert any('nonexistent_state' in error for error in errors)
    
    def test_validate_no_terminal_states(self, clean_registry):
        """Test validation when no terminal states exist."""
        # Create states that cycle between each other (A->B->A) with no terminal transitions
        class CyclicStateA(AnalysisState):
            POSSIBLE_TRANSITIONS = {
                'to_b': StateTransition('cyclic_b', 'always', 'Cycle to B')
            }
            def execute(self, context): return {}
            def determine_next_state(self, result, context): return 'cyclic_b'
        
        class CyclicStateB(AnalysisState):
            POSSIBLE_TRANSITIONS = {
                'to_a': StateTransition('cyclic_a', 'always', 'Cycle to A')
            }
            def execute(self, context): return {}
            def determine_next_state(self, result, context): return 'cyclic_a'
        
        # Temporarily disable validation to register cyclic states
        original_validate = AnalysisState.validate_transitions
        AnalysisState.validate_transitions = classmethod(lambda cls: None)
        
        try:
            register_state('cyclic_a', CyclicStateA)
            register_state('cyclic_b', CyclicStateB)
            
            errors = WorkflowStateMap.validate_state_map()
            assert any('terminal' in error.lower() for error in errors)
        finally:
            # Restore validation
            AnalysisState.validate_transitions = original_validate
    
    def test_find_workflow_paths(self, clean_registry):
        """Test finding workflow paths."""
        register_state('test_1', TestState)
        register_state('test_2', TestState2)
        
        paths = WorkflowStateMap.find_workflow_paths(start_state='test_1')
        
        assert len(paths) > 0
        # Should find path: test_1 -> test_2 (terminal)
        assert any('test_1' in path and 'test_2' in path for path in paths)
    
    def test_get_entry_states(self, clean_registry):
        """Test identifying entry states."""
        register_state('test_1', TestState)  # No other state transitions to this
        register_state('test_2', TestState2)  # test_1 transitions to this
        
        entry_states = WorkflowStateMap.get_entry_states()
        
        assert 'test_1' in entry_states
        assert 'test_2' not in entry_states  # Is a target of test_1
    
    def test_get_terminal_states(self, clean_registry):
        """Test identifying terminal states."""
        register_state('test_1', TestState)
        register_state('test_2', TestState2)
        
        terminal_states = WorkflowStateMap.get_terminal_states()
        
        # Both states can terminate (have None transitions)
        assert 'test_1' in terminal_states
        assert 'test_2' in terminal_states
    
    def test_export_state_map_json(self, clean_registry):
        """Test exporting state map as JSON."""
        register_state('test_1', TestState)
        
        json_export = WorkflowStateMap.export_state_map(format='json')
        
        assert isinstance(json_export, str)
        assert 'test_1' in json_export
        assert 'TestState' in json_export
    
    def test_export_state_map_dot(self, clean_registry):
        """Test exporting state map as DOT format."""
        register_state('test_1', TestState)
        register_state('test_2', TestState2)
        
        dot_export = WorkflowStateMap.export_state_map(format='dot')
        
        assert isinstance(dot_export, str)
        assert 'digraph workflow' in dot_export
        assert 'test_1' in dot_export
        assert 'test_2' in dot_export
    
    def test_export_invalid_format(self, clean_registry):
        """Test exporting with invalid format."""
        with pytest.raises(ValueError, match="Unsupported export format"):
            WorkflowStateMap.export_state_map(format='invalid')


# Orchestrator Tests

@pytest.mark.unit 
class TestAnalysisOrchestrator:
    """Test analysis orchestrator functionality."""
    
    def test_orchestrator_initialization(self, clean_registry):
        """Test orchestrator initialization."""
        register_state('test_1', TestState)
        register_state('test_2', TestState2)
        
        orchestrator = AnalysisOrchestrator()
        
        assert orchestrator.state_map is not None
        assert len(orchestrator.states) == 2
        assert orchestrator.config is not None
    
    def test_orchestrator_initialization_with_broken_states(self, clean_registry):
        """Test orchestrator initialization with broken state map."""
        register_state('broken', BrokenState)
        
        with pytest.raises(WorkflowExecutionError, match="State map validation failed"):
            AnalysisOrchestrator(validate_on_init=True)
    
    def test_orchestrator_no_validation(self, clean_registry):
        """Test orchestrator initialization without validation."""
        register_state('broken', BrokenState)
        
        # Should not raise when validation disabled
        orchestrator = AnalysisOrchestrator(validate_on_init=False)
        assert orchestrator is not None
    
    def test_get_state_map(self, clean_registry):
        """Test getting state map from orchestrator."""
        register_state('test_1', TestState)
        register_state('test_2', TestState2)  # Register the referenced state
        
        orchestrator = AnalysisOrchestrator()
        state_map = orchestrator.get_state_map()
        
        assert 'test_1' in state_map
        assert state_map['test_1']['class'] == 'TestState'
    
    def test_validate_workflow(self, clean_registry):
        """Test workflow validation."""
        register_state('test_1', TestState)
        register_state('test_2', TestState2)
        
        orchestrator = AnalysisOrchestrator()
        errors = orchestrator.validate_workflow()
        
        assert errors == []
    
    def test_run_workflow_success(self, clean_registry):
        """Test successful workflow execution."""
        
        register_state('test_1', TestState)
        register_state('test_2', TestState2)
        
        orchestrator = AnalysisOrchestrator()
        
        test_document = {'pages': [1, 2, 3]}
        
        results = orchestrator.run_workflow(
            document_data=test_document,
            initial_state='test_1'
        )
        
        assert 'workflow_results' in results
        assert 'accumulated_knowledge' in results
        assert 'workflow_metadata' in results
        assert 'summary' in results
        
        # Check workflow results
        assert 'test_1' in results['workflow_results']
        assert 'test_2' in results['workflow_results']
        
        # Check accumulated knowledge
        assert 'test_pattern' in results['accumulated_knowledge']
        assert 'final_pattern' in results['accumulated_knowledge']
        
        # Check summary
        summary = results['summary']
        assert summary['execution_path'] == ['test_1', 'test_2']
        assert summary['total_iterations'] == 2
        assert summary['termination_reason'] == 'normal'
    
    def test_run_workflow_invalid_initial_state(self, clean_registry):
        """Test workflow with invalid initial state."""
        register_state('test_1', TestState)
        register_state('test_2', TestState2)
        
        orchestrator = AnalysisOrchestrator()
        
        with pytest.raises(WorkflowExecutionError, match="Initial state 'invalid' not found"):
            orchestrator.run_workflow({}, initial_state='invalid')
    
    def test_run_workflow_no_entry_states(self, clean_registry):
        """Test workflow when no entry states available."""
        # Create states that all reference each other (no entry points)
        class State1(AnalysisState):
            POSSIBLE_TRANSITIONS = {'to_2': StateTransition('state_2', 'always', 'To state 2')}
            def execute(self, context): return {}
            def determine_next_state(self, result, context): return 'state_2'
        
        class State2(AnalysisState):
            POSSIBLE_TRANSITIONS = {'to_1': StateTransition('state_1', 'always', 'To state 1')}
            def execute(self, context): return {}
            def determine_next_state(self, result, context): return 'state_1'
        
        register_state('state_1', State1)
        register_state('state_2', State2)
        
        orchestrator = AnalysisOrchestrator(validate_on_init=False)
        
        with pytest.raises(WorkflowExecutionError, match="No entry states found"):
            orchestrator.run_workflow({})
    
    def test_run_workflow_max_total_states(self, clean_registry):
        """Test workflow hitting maximum total states with multi-state cycle."""
        # Create states that cycle between each other (A->B->A)
        class CycleStateA(AnalysisState):
            POSSIBLE_TRANSITIONS = {'to_b': StateTransition('cycle_b', 'always', 'To cycle B')}
            def execute(self, context): return {'analysis_type': 'cycle_a'}
            def determine_next_state(self, result, context): return 'cycle_b'
        
        class CycleStateB(AnalysisState):
            POSSIBLE_TRANSITIONS = {'to_a': StateTransition('cycle_a', 'always', 'To cycle A')}
            def execute(self, context): return {'analysis_type': 'cycle_b'}
            def determine_next_state(self, result, context): return 'cycle_a'
        
        # Temporarily disable transition validation to allow registration
        original_validate = AnalysisState.validate_transitions
        AnalysisState.validate_transitions = classmethod(lambda cls: None)
        
        try:
            register_state('cycle_a', CycleStateA)
            register_state('cycle_b', CycleStateB)
            
            orchestrator = AnalysisOrchestrator(validate_on_init=False)
            
            with pytest.raises(WorkflowExecutionError, match="exceeded maximum total states"):
                orchestrator.run_workflow(
                    document_data={},
                    initial_state='cycle_a'
                )
        finally:
            # Restore validation
            AnalysisState.validate_transitions = original_validate
    
    def test_run_workflow_invalid_transition(self, clean_registry):
        """Test workflow with invalid state transition."""
        class BadTransitionState(AnalysisState):
            POSSIBLE_TRANSITIONS = {'valid': StateTransition('test_2', 'valid', 'Valid transition')}
            def execute(self, context): return {'analysis_type': 'bad'}
            def determine_next_state(self, result, context): return 'invalid_state'  # Not in transitions
        
        register_state('bad_state', BadTransitionState)
        register_state('test_2', TestState2)
        
        orchestrator = AnalysisOrchestrator(validate_on_init=False)
        
        with pytest.raises(WorkflowExecutionError, match="Invalid transition"):
            orchestrator.run_workflow(
                document_data={},
                initial_state='bad_state'
            )