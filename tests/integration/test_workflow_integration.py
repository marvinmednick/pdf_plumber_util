"""Integration tests for complete workflow execution."""

import pytest
import tempfile
import json
from pathlib import Path
from typing import Dict, Any, Optional

from pdf_plumb.workflow import AnalysisOrchestrator, WorkflowStateMap
from pdf_plumb.workflow.state import AnalysisState, StateTransition
from pdf_plumb.workflow.registry import register_state, get_all_states
from pdf_plumb.workflow.orchestrator import WorkflowExecutionError


# Simple Test State Implementations for Integration Testing

class StateA(AnalysisState):
    """Entry state for basic workflow testing."""
    
    POSSIBLE_TRANSITIONS = {
        'proceed': StateTransition('state_b', 'success', 'Normal progression to state B'),
        'skip': StateTransition('state_c', 'skip_condition', 'Skip directly to state C')
    }
    
    REQUIRED_FIELDS = ['document_data']
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        self.validate_input(context)
        
        test_data = context['document_data']
        should_skip = test_data.get('skip_to_c', False)
        
        return {
            'analysis_type': 'state_a_analysis',
            'results': {
                'processed': True,
                'skip_requested': should_skip,
                'data_count': len(test_data) if isinstance(test_data, (list, dict)) else 1
            },
            'metadata': {
                'confidence': 0.9,
                'processing_time': 0.1
            },
            'knowledge': {
                'state_a_executed': True,
                'skip_condition': should_skip
            }
        }
    
    def determine_next_state(self, execution_result: Dict[str, Any], context: Dict[str, Any]) -> Optional[str]:
        skip_requested = execution_result['results']['skip_requested']
        return 'state_c' if skip_requested else 'state_b'


class StateB(AnalysisState):
    """Middle state for linear workflow testing."""
    
    POSSIBLE_TRANSITIONS = {
        'continue': StateTransition('state_c', 'normal', 'Continue to state C'),
        'terminate': StateTransition(None, 'early_exit', 'Terminate workflow early')
    }
    
    REQUIRED_FIELDS = ['document_data']
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        self.validate_input(context)
        
        # Access previous results
        previous_results = context.get('workflow_results', {})
        state_a_results = previous_results.get('state_a', {})
        
        test_data = context['document_data']
        should_terminate = test_data.get('early_exit', False)
        
        return {
            'analysis_type': 'state_b_analysis',
            'results': {
                'enhanced_data': True,
                'previous_confidence': state_a_results.get('metadata', {}).get('confidence', 0),
                'terminate_requested': should_terminate
            },
            'metadata': {
                'confidence': 0.8,
                'processing_time': 0.2
            },
            'knowledge': {
                'state_b_executed': True,
                'enhanced_analysis': True
            }
        }
    
    def determine_next_state(self, execution_result: Dict[str, Any], context: Dict[str, Any]) -> Optional[str]:
        results = execution_result['results']
        if results['terminate_requested']:
            return None
        else:
            return 'state_c'


class StateC(AnalysisState):
    """Terminal state for workflow completion."""
    
    POSSIBLE_TRANSITIONS = {
        'complete': StateTransition(None, 'workflow_complete', 'Workflow finished successfully')
    }
    
    REQUIRED_FIELDS = ['document_data']
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        self.validate_input(context)
        
        # Compile results from all previous states
        all_results = context.get('workflow_results', {})
        knowledge = context.get('accumulated_knowledge', {})
        
        return {
            'analysis_type': 'state_c_final',
            'results': {
                'final_report': True,
                'states_executed': list(all_results.keys()),
                'total_knowledge': len(knowledge),
                'workflow_complete': True
            },
            'metadata': {
                'confidence': 1.0,
                'processing_time': 0.05
            },
            'knowledge': {
                'state_c_executed': True,
                'workflow_completed': True
            }
        }
    
    def determine_next_state(self, execution_result: Dict[str, Any], context: Dict[str, Any]) -> Optional[str]:
        return None  # Always terminal


class BrokenTransitionState(AnalysisState):
    """State with invalid transition for error testing."""
    
    POSSIBLE_TRANSITIONS = {
        'invalid': StateTransition('nonexistent_state', 'always', 'Points to non-existent state')
    }
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'analysis_type': 'broken_state',
            'results': {'will_fail': True},
            'metadata': {'confidence': 0.5}
        }
    
    def determine_next_state(self, execution_result: Dict[str, Any], context: Dict[str, Any]) -> Optional[str]:
        return 'nonexistent_state'


# Test Fixtures

@pytest.fixture
def integration_registry():
    """Set up integration test state registry."""
    from pdf_plumb.workflow.registry import STATE_REGISTRY
    original_registry = STATE_REGISTRY.copy()
    
    # Clear and register integration test states
    STATE_REGISTRY.clear()
    STATE_REGISTRY.update({
        'state_a': StateA,
        'state_b': StateB,
        'state_c': StateC,
        'broken_transition': BrokenTransitionState,
    })
    
    yield
    
    # Restore original registry
    STATE_REGISTRY.clear()
    STATE_REGISTRY.update(original_registry)


@pytest.fixture
def temp_output_dir():
    """Create temporary output directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def basic_test_data():
    """Create basic test data."""
    return {
        'test_value': 'basic_workflow',
        'items': ['item1', 'item2', 'item3']
    }


@pytest.fixture
def skip_test_data():
    """Create test data that triggers skip condition."""
    return {
        'test_value': 'skip_workflow',
        'skip_to_c': True
    }


# Integration Tests

@pytest.mark.integration
class TestWorkflowIntegration:
    """Integration tests for complete workflow execution."""
    
    def test_basic_linear_workflow(self, integration_registry, basic_test_data, temp_output_dir):
        """Test the AnalysisOrchestrator's ability to execute a complete multi-state workflow.
        
        Test setup:
        - Uses integration test registry with predefined states (state_a → state_b → state_c)
        - Provides basic test data without skip conditions to ensure linear progression
        - Creates temporary output directory for workflow context snapshots

        What it verifies:
        - Workflow completes normally without errors or early termination
        - All three states execute in correct sequence (state_a → state_b → state_c)
        - Each state produces results and contributes to accumulated knowledge
        - Workflow metadata correctly tracks execution path and iteration count
        - Knowledge accumulation works across state transitions

        Test limitation:
        - Uses simplified test states, not real PDF analysis states
        - Validation disabled for orchestrator to allow test state registration
        - Doesn't test error conditions or complex branching logic

        Key insight: Validates that the workflow orchestrator can coordinate multi-state execution and properly accumulate results across state transitions.
        """
        orchestrator = AnalysisOrchestrator(validate_on_init=False)
        
        results = orchestrator.run_workflow(
            document_data=basic_test_data,
            initial_state='state_a',
            output_dir=temp_output_dir
        )
        
        # Verify workflow completion
        assert results['summary']['termination_reason'] == 'normal'
        assert results['summary']['states_executed'] == 3
        
        # Verify execution path
        execution_path = results['summary']['execution_path']
        assert execution_path == ['state_a', 'state_b', 'state_c']
        
        # Verify all states executed
        workflow_results = results['workflow_results']
        assert 'state_a' in workflow_results
        assert 'state_b' in workflow_results
        assert 'state_c' in workflow_results
        
        # Verify knowledge accumulation
        knowledge = results['accumulated_knowledge']
        assert knowledge['state_a_executed'] == True
        assert knowledge['state_b_executed'] == True
        assert knowledge['state_c_executed'] == True
        assert knowledge['workflow_completed'] == True
    
    def test_conditional_skip_workflow(self, integration_registry, skip_test_data, temp_output_dir):
        """Test the orchestrator's ability to handle conditional state skipping based on execution results.
        
        Test setup:
        - Uses skip_test_data which triggers state_a to request skipping state_b
        - State A detects skip condition and transitions directly to state_c
        - This tests workflow branching where intermediate states can be bypassed
        - Uses same three-state setup but with different execution path
        
        What it verifies:
        - Workflow completes normally despite skipping intermediate state
        - Only 2 states execute instead of the full 3-state sequence
        - Execution path correctly shows state_a → state_c (no state_b)
        - State_b results are not present in workflow_results
        - Skip condition detection works (skip_requested=True in state_a results)
        
        Test limitation:
        - Uses artificial skip condition rather than realistic PDF analysis branching
        - Doesn't test complex multi-branch scenarios or nested conditions
        - Skip logic is hardcoded in test states, not configurable
        
        Key insight: Validates that workflows can dynamically branch and skip states based on intermediate analysis results.
        """
        orchestrator = AnalysisOrchestrator(validate_on_init=False)
        
        results = orchestrator.run_workflow(
            document_data=skip_test_data,
            initial_state='state_a',
            output_dir=temp_output_dir
        )
        
        # Verify workflow completion
        assert results['summary']['termination_reason'] == 'normal'
        assert results['summary']['states_executed'] == 2
        
        # Verify execution path skipped state_b
        execution_path = results['summary']['execution_path']
        assert execution_path == ['state_a', 'state_c']
        
        # Verify only state_a and state_c executed
        workflow_results = results['workflow_results']
        assert 'state_a' in workflow_results
        assert 'state_b' not in workflow_results
        assert 'state_c' in workflow_results
        
        # Verify skip condition was detected
        state_a_results = workflow_results['state_a']
        assert state_a_results['results']['skip_requested'] == True
    
    def test_invalid_transition_error(self, integration_registry, basic_test_data):
        """Test the orchestrator's error handling when a state requests transition to nonexistent target state."""
        orchestrator = AnalysisOrchestrator(validate_on_init=False)
        
        with pytest.raises(WorkflowExecutionError, match="Target state.*not found"):
            orchestrator.run_workflow(
                document_data=basic_test_data,
                initial_state='broken_transition'
            )
    
    def test_max_states_limit_with_cycle(self, integration_registry, basic_test_data):
        """Test the orchestrator's cycle detection using MAX_TOTAL_STATES limit in integration environment.
        
        Test setup:
        - Creates temporary CycleStateA and CycleStateB that infinitely transition between each other
        - Registers these states in the integration test registry
        - Attempts to run workflow starting from cycle_a state
        - This simulates real-world infinite loop scenarios that could hang the system
        
        What it verifies:
        - Orchestrator detects when MAX_TOTAL_STATES (50) limit is exceeded
        - WorkflowExecutionError is raised before system hangs
        - Cycle detection works in full integration environment (not just unit tests)
        - Error handling prevents infinite execution that would consume resources
        
        Test limitation:
        - Uses artificially simple 2-state cycle rather than complex real-world cycles
        - Requires temporary modification of registry for test scenario
        - Doesn't test near-limit scenarios or complex cycle patterns
        
        Key insight: Ensures the orchestrator has robust cycle protection that works in realistic deployment scenarios.
        """
        # Create a temporary A->B->A cycle for testing
        from pdf_plumb.workflow.registry import STATE_REGISTRY
        
        class CycleStateA(AnalysisState):
            POSSIBLE_TRANSITIONS = {'to_b': StateTransition('cycle_b', 'always', 'To cycle B')}
            def execute(self, context): return {'analysis_type': 'cycle_a'}
            def determine_next_state(self, result, context): return 'cycle_b'
        
        class CycleStateB(AnalysisState):
            POSSIBLE_TRANSITIONS = {'to_a': StateTransition('cycle_a', 'always', 'To cycle A')}
            def execute(self, context): return {'analysis_type': 'cycle_b'}
            def determine_next_state(self, result, context): return 'cycle_a'
        
        # Temporarily register cycle states (bypassing validation)
        original_validate = AnalysisState.validate_transitions
        AnalysisState.validate_transitions = classmethod(lambda cls: None)  # Disable validation
        
        try:
            STATE_REGISTRY['cycle_a'] = CycleStateA
            STATE_REGISTRY['cycle_b'] = CycleStateB
            
            orchestrator = AnalysisOrchestrator(validate_on_init=False)
            
            with pytest.raises(WorkflowExecutionError, match="exceeded maximum total states"):
                orchestrator.run_workflow(
                    document_data=basic_test_data,
                    initial_state='cycle_a'
                )
        finally:
            # Restore validation and clean up temporary states
            AnalysisState.validate_transitions = original_validate
            STATE_REGISTRY.pop('cycle_a', None)
            STATE_REGISTRY.pop('cycle_b', None)
    
    def test_invalid_initial_state(self, integration_registry, basic_test_data):
        """Test orchestrator error handling when requested initial state doesn't exist in registry."""
        orchestrator = AnalysisOrchestrator(validate_on_init=False)
        
        with pytest.raises(WorkflowExecutionError, match="Initial state 'invalid' not found"):
            orchestrator.run_workflow(
                document_data=basic_test_data,
                initial_state='invalid'
            )
    
    def test_state_map_generation(self, integration_registry):
        """Test WorkflowStateMap.generate_state_map() produces complete representation of registered integration states."""
        state_map = WorkflowStateMap.generate_state_map()
        
        # Verify all integration states present
        expected_states = ['state_a', 'state_b', 'state_c', 'broken_transition']
        
        for state_name in expected_states:
            assert state_name in state_map
            assert 'transitions' in state_map[state_name]
            assert 'class' in state_map[state_name]
        
        # Verify workflow validation
        errors = WorkflowStateMap.validate_state_map(state_map)
        # Should have one error for broken_transition state
        assert len(errors) == 1
        assert 'nonexistent_state' in errors[0]
        
        # Verify entry and terminal states
        entry_states = WorkflowStateMap.get_entry_states(state_map)
        terminal_states = WorkflowStateMap.get_terminal_states(state_map)
        
        # state_a and broken_transition should be entry states (no incoming transitions)
        assert 'state_a' in entry_states
        assert 'broken_transition' in entry_states
        # state_c should be terminal state
        assert 'state_c' in terminal_states
    
    def test_workflow_paths_discovery(self, integration_registry):
        """Test WorkflowStateMap.find_workflow_paths() discovers all possible execution routes including conditional branches."""
        paths = WorkflowStateMap.find_workflow_paths(start_state='state_a')
        
        # Should find multiple paths due to branching logic
        assert len(paths) >= 2
        
        # Verify main path exists: state_a -> state_b -> state_c
        main_paths = [path for path in paths if 'state_b' in path and 'state_c' in path]
        assert len(main_paths) > 0
        
        # Verify skip path exists: state_a -> state_c
        skip_paths = [path for path in paths if len(path) == 2 and path == ['state_a', 'state_c']]
        assert len(skip_paths) > 0
    
    def test_context_and_metadata_tracking(self, integration_registry, basic_test_data):
        """Test the orchestrator's ability to track detailed execution metadata and timing information throughout workflow execution.
        
        Test setup:
        - Uses basic_test_data to run complete linear workflow (state_a → state_b → state_c)
        - Orchestrator automatically captures timing and execution metadata
        - Each iteration (state execution) is tracked with individual timing
        - Tests comprehensive metadata collection in realistic execution environment
        
        What it verifies:
        - Workflow metadata contains all required timing fields (start_time, end_time, duration)
        - Execution metadata includes iteration count and termination reason
        - Per-iteration metadata tracks individual state execution details
        - Duration calculations are valid (duration_seconds >= 0)
        - Initial state and termination reason are correctly recorded
        
        Test limitation:
        - Uses simple test states with predictable execution patterns
        - Doesn't test metadata tracking under error conditions
        - Timing validation is basic (only checks non-negative values)
        
        Key insight: Validates that the orchestrator provides comprehensive execution tracking for debugging and performance analysis.
        """
        orchestrator = AnalysisOrchestrator(validate_on_init=False)
        
        results = orchestrator.run_workflow(
            document_data=basic_test_data,
            initial_state='state_a'
        )
        
        metadata = results['workflow_metadata']
        
        # Verify metadata structure
        assert 'start_time' in metadata
        assert 'end_time' in metadata
        assert 'duration_seconds' in metadata
        assert 'iteration_count' in metadata
        assert 'initial_state' in metadata
        assert 'termination_reason' in metadata
        
        # Verify metadata values
        assert metadata['initial_state'] == 'state_a'
        assert metadata['termination_reason'] == 'normal'
        assert metadata['iteration_count'] == 3  # A -> B -> C
        assert metadata['duration_seconds'] >= 0
        
        # Verify per-iteration metadata
        for i in range(metadata['iteration_count']):
            iter_key = f'iteration_{i}'
            assert iter_key in metadata
            assert 'state' in metadata[iter_key]
            assert 'start_time' in metadata[iter_key]