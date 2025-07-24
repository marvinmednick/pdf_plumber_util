"""Analysis workflow orchestrator with context management."""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from ..config import get_config
from .registry import get_all_states, get_state_class
from .state_map import WorkflowStateMap
from .state import AnalysisState

# Fixed limit to prevent infinite loops (generous but reasonable upper bound)
MAX_TOTAL_STATES = 50


class WorkflowExecutionError(Exception):
    """Raised when workflow execution fails."""
    
    def __init__(self, message: str, state_name: str = None, context: Dict[str, Any] = None):
        super().__init__(message)
        self.state_name = state_name
        self.context = context


class AnalysisOrchestrator:
    """Orchestrates document analysis workflow through state machine."""
    
    def __init__(self, validate_on_init: bool = True):
        """Initialize analysis orchestrator.
        
        Args:
            validate_on_init: Whether to validate state map on initialization
            
        Raises:
            WorkflowExecutionError: If state map validation fails
        """
        self.state_map = WorkflowStateMap.generate_state_map()
        self.states = get_all_states()
        self.config = get_config()
        
        # Validate state map if requested
        if validate_on_init:
            errors = WorkflowStateMap.validate_state_map(self.state_map)
            if errors:
                error_msg = "State map validation failed:\n" + "\n".join(f"  • {error}" for error in errors)
                raise WorkflowExecutionError(error_msg)
    
    def run_workflow(
        self, 
        document_data: Any, 
        initial_state: str = None,
        timeout_seconds: int = None,
        save_context: bool = False,
        output_dir: Optional[Path] = None
    ) -> Dict[str, Any]:
        """Execute complete analysis workflow.
        
        Args:
            document_data: Document data to analyze
            initial_state: Starting state name (auto-detects if None)
            timeout_seconds: Workflow timeout (config default if None)
            save_context: Whether to save context snapshots
            output_dir: Directory for context snapshots
            
        Returns:
            Dictionary containing workflow results and metadata
            
        Raises:
            WorkflowExecutionError: If workflow execution fails
        """
        # Set defaults from config
        if timeout_seconds is None:
            timeout_seconds = getattr(self.config, 'workflow_timeout_seconds', 1800)  # 30 minutes
        
        # Auto-detect initial state if not provided
        if initial_state is None:
            entry_states = WorkflowStateMap.get_entry_states(self.state_map)
            if not entry_states:
                raise WorkflowExecutionError("No entry states found and no initial state specified")
            initial_state = entry_states[0]
        
        # Validate initial state exists
        if initial_state not in self.states:
            raise WorkflowExecutionError(f"Initial state '{initial_state}' not found in registry")
        
        # Initialize workflow context
        context = self._initialize_context(document_data, output_dir)
        start_time = datetime.now()
        
        # Workflow execution
        current_state_name = initial_state
        iteration_count = 0
        
        context['workflow_metadata']['start_time'] = start_time.isoformat()
        context['workflow_metadata']['initial_state'] = initial_state
        
        try:
            while current_state_name and iteration_count < MAX_TOTAL_STATES:
                # Check timeout
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed > timeout_seconds:
                    raise WorkflowExecutionError(
                        f"Workflow timeout after {elapsed:.1f} seconds",
                        state_name=current_state_name,
                        context=context
                    )
                
                # Execute current state
                current_state_name = self._execute_state_iteration(
                    current_state_name, context, iteration_count, save_context
                )
                
                iteration_count += 1
            
            # Check termination reason
            if current_state_name and iteration_count >= MAX_TOTAL_STATES:
                raise WorkflowExecutionError(
                    f"Workflow exceeded maximum total states ({MAX_TOTAL_STATES})",
                    state_name=current_state_name,
                    context=context
                )
            
            # Finalize workflow
            end_time = datetime.now()
            context['workflow_metadata']['end_time'] = end_time.isoformat()
            context['workflow_metadata']['duration_seconds'] = (end_time - start_time).total_seconds()
            context['workflow_metadata']['iteration_count'] = iteration_count
            context['workflow_metadata']['termination_reason'] = 'normal'
            
            return self._finalize_workflow_results(context)
            
        except Exception as e:
            # Record error information
            context['workflow_metadata']['end_time'] = datetime.now().isoformat()
            context['workflow_metadata']['duration_seconds'] = (datetime.now() - start_time).total_seconds()
            context['workflow_metadata']['iteration_count'] = iteration_count
            context['workflow_metadata']['termination_reason'] = 'error'
            context['workflow_metadata']['error'] = str(e)
            
            if save_context:
                self._save_context_snapshot(context, 'error', output_dir)
            
            raise
    
    def _initialize_context(self, document_data: Any, output_dir: Optional[Path]) -> Dict[str, Any]:
        """Initialize workflow context.
        
        Args:
            document_data: Document data to analyze
            output_dir: Output directory for results
            
        Returns:
            Initialized context dictionary
        """
        return {
            'document_data': document_data,
            'config': self.config,
            'workflow_results': {},
            'accumulated_knowledge': {},
            'workflow_metadata': {
                'orchestrator_version': '1.0.0',
                'state_map': self.state_map,
                'total_states': len(self.states),
            },
            'output_dir': output_dir or Path(self.config.output_dir),
        }
    
    def _execute_state_iteration(
        self, 
        state_name: str, 
        context: Dict[str, Any], 
        iteration: int,
        save_context: bool
    ) -> Optional[str]:
        """Execute a single state iteration.
        
        Args:
            state_name: Current state name
            context: Workflow context
            iteration: Current iteration number
            save_context: Whether to save context snapshots
            
        Returns:
            Next state name or None if workflow complete
            
        Raises:
            WorkflowExecutionError: If state execution fails
        """
        try:
            # Get and instantiate state
            state_class = get_state_class(state_name)
            state = state_class()
            
            # Record state execution start
            context['workflow_metadata'][f'iteration_{iteration}'] = {
                'state': state_name,
                'start_time': datetime.now().isoformat()
            }
            
            # Execute state
            execution_result = state.execute(context)
            
            # Store state results
            context['workflow_results'][state_name] = execution_result
            
            # Update accumulated knowledge
            if 'knowledge' in execution_result:
                context['accumulated_knowledge'].update(execution_result['knowledge'])
            
            # Determine next state
            next_state = state.determine_next_state(execution_result, context)
            
            # Validate transition
            if next_state is not None:
                self._validate_transition(state_name, next_state)
            
            # Record state execution completion
            context['workflow_metadata'][f'iteration_{iteration}']['end_time'] = datetime.now().isoformat()
            context['workflow_metadata'][f'iteration_{iteration}']['next_state'] = next_state
            context['workflow_metadata'][f'iteration_{iteration}']['execution_result_summary'] = {
                'analysis_type': execution_result.get('analysis_type'),
                'metadata': execution_result.get('metadata', {})
            }
            
            # Save context snapshot if requested
            if save_context:
                self._save_context_snapshot(context, f'iteration_{iteration}_{state_name}', context['output_dir'])
            
            return next_state
            
        except Exception as e:
            raise WorkflowExecutionError(
                f"State '{state_name}' execution failed: {e}",
                state_name=state_name,
                context=context
            ) from e
    
    def _validate_transition(self, current_state: str, next_state: str) -> None:
        """Validate state transition is allowed.
        
        Args:
            current_state: Current state name
            next_state: Target state name
            
        Raises:
            WorkflowExecutionError: If transition is invalid
        """
        if current_state not in self.state_map:
            raise WorkflowExecutionError(f"Current state '{current_state}' not found in state map")
        
        possible_next = self.state_map[current_state]['possible_next_states']
        
        if next_state not in possible_next:
            raise WorkflowExecutionError(
                f"Invalid transition from '{current_state}' to '{next_state}'. "
                f"Allowed transitions: {possible_next}"
            )
        
        if next_state not in self.states:
            raise WorkflowExecutionError(f"Target state '{next_state}' not found in registry")
    
    def _save_context_snapshot(self, context: Dict[str, Any], label: str, output_dir: Path) -> None:
        """Save context snapshot for debugging.
        
        Args:
            context: Context to save
            label: Snapshot label
            output_dir: Output directory
        """
        try:
            import json
            from ..utils.json_utils import save_json
            
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"workflow_context_{timestamp}_{label}.json"
            filepath = output_dir / filename
            
            # Create serializable version of context (remove non-serializable objects)
            serializable_context = self._make_context_serializable(context)
            
            save_json(serializable_context, filepath)
            
        except Exception as e:
            # Don't fail workflow for snapshot save errors
            print(f"Warning: Failed to save context snapshot: {e}")
    
    def _make_context_serializable(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Make context serializable by converting complex objects.
        
        Args:
            context: Original context
            
        Returns:
            Serializable version of context
        """
        serializable = {}
        
        for key, value in context.items():
            if key == 'config':
                # Convert Pydantic config to dict
                serializable[key] = value.model_dump() if hasattr(value, 'model_dump') else str(value)
            elif key == 'document_data':
                # Include only metadata for document data (can be large)
                if isinstance(value, list):
                    serializable[key] = {'type': 'list', 'length': len(value)}
                elif isinstance(value, dict):
                    serializable[key] = {'type': 'dict', 'keys': list(value.keys())}
                else:
                    serializable[key] = {'type': type(value).__name__, 'repr': str(value)[:100]}
            else:
                serializable[key] = value
        
        return serializable
    
    def _finalize_workflow_results(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Finalize and return workflow results.
        
        Args:
            context: Complete workflow context
            
        Returns:
            Finalized results dictionary
        """
        return {
            'workflow_results': context['workflow_results'],
            'accumulated_knowledge': context['accumulated_knowledge'],
            'workflow_metadata': context['workflow_metadata'],
            'summary': self._generate_workflow_summary(context)
        }
    
    def _generate_workflow_summary(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate workflow execution summary.
        
        Args:
            context: Workflow context
            
        Returns:
            Summary dictionary
        """
        metadata = context['workflow_metadata']
        results = context['workflow_results']
        
        # Calculate execution path
        execution_path = []
        for i in range(metadata['iteration_count']):
            iter_key = f'iteration_{i}'
            if iter_key in metadata:
                execution_path.append(metadata[iter_key]['state'])
        
        # Collect analysis types performed
        analysis_types = []
        for result in results.values():
            if 'analysis_type' in result:
                analysis_types.append(result['analysis_type'])
        
        return {
            'execution_path': execution_path,
            'total_iterations': metadata['iteration_count'],
            'duration_seconds': metadata.get('duration_seconds', 0),
            'analysis_types_performed': analysis_types,
            'termination_reason': metadata.get('termination_reason', 'unknown'),
            'states_executed': len(results),
            'knowledge_items': len(context['accumulated_knowledge'])
        }
    
    def get_state_map(self) -> Dict[str, Any]:
        """Get current state map.
        
        Returns:
            State map dictionary
        """
        return self.state_map.copy()
    
    def validate_workflow(self) -> List[str]:
        """Validate current workflow configuration.
        
        Returns:
            List of validation errors (empty if valid)
        """
        return WorkflowStateMap.validate_state_map(self.state_map)
    
    def print_workflow_info(self) -> None:
        """Print workflow information for debugging."""
        print("=== WORKFLOW ORCHESTRATOR INFO ===\n")
        print(f"Total registered states: {len(self.states)}")
        print(f"State map valid: {'✅' if not self.validate_workflow() else '❌'}")
        print()
        
        WorkflowStateMap.print_state_map(self.state_map)