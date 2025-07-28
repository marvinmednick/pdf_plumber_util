# LLM Analysis State Machine Architecture

## Overview

This document details the design of a state machine orchestrator for managing complex, multi-objective analysis workflows. The architecture provides a flexible framework where different analysis tasks can be chained together with conditional logic determining the flow between states.

## Core Concepts

### State Machine Fundamentals

A **state** represents a discrete analysis task that:
- Takes standardized input data (JSON-like context)
- Performs work (programmatic logic, LLM calls, or both)
- Produces standardized output results
- Determines what should happen next

The **orchestrator** manages the overall workflow by:
- Executing states in sequence
- Passing context between states
- Validating state transitions
- Accumulating results across the workflow

### The Execute Function

Each state implements an `execute()` function that follows this pattern:
```python
def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
    # 1. Validate required input data
    self.validate_input(context)
    
    # 2. Perform the actual work (hybrid approach)
    #    - Programmatic logic (data processing, calculations)
    #    - LLM calls (if content understanding needed)
    #    - External API calls
    #    - File operations
    
    # 3. Return standardized results
    return {
        'analysis_type': 'my_analysis',
        'results': processed_data,
        'metadata': analysis_metadata,
        'knowledge': extracted_patterns  # For context accumulation
    }
```

### The Next State Function

Each state implements a `determine_next_state()` function that decides workflow progression:
```python
def determine_next_state(self, execution_result: Dict[str, Any], context: Dict[str, Any]) -> Optional[str]:
    # Examine execution results and current context
    # Apply decision logic (any criteria you want)
    # Return next state name or None to end workflow
    
    if some_condition:
        return 'next_state_name'
    elif other_condition:
        return 'alternative_state_name' 
    else:
        return None  # End workflow
```

The transition logic can be based on:
- Result quality metrics (confidence scores, completeness)
- Data characteristics (document type, size, complexity)
- Resource constraints (time limits, API costs)
- Business rules (required vs optional analysis steps)
- Error conditions (retry logic, fallback strategies)

### Data Passing and Context Growth

The orchestrator maintains a growing context object that accumulates information:
```python
context = {
    'original_input': input_data,           # Initial data
    'config': system_configuration,         # Settings and parameters
    'workflow_results': {                   # Results from completed states
        'state1': state1_results,
        'state2': state2_results,
    },
    'accumulated_knowledge': {              # Cross-state knowledge base
        'patterns': discovered_patterns,
        'metadata': enriched_metadata,
    }
}
```

Each state:
- Receives the full context (but filters what it needs)
- Adds its results to `workflow_results`
- Contributes knowledge to `accumulated_knowledge`
- Can reference previous state results for decision-making

### State Registration and Discovery

States are registered using a hybrid manual approach:
```python
# states/__init__.py
from .task_a import TaskAState
from .task_b import TaskBState, TaskBRefinementState
from .task_c import TaskCState

# Explicit registration - no magic naming
STATE_REGISTRY = {
    'task_a': TaskAState,
    'task_b': TaskBState,
    'task_b_refine': TaskBRefinementState,
    'task_c': TaskCState,
}
```

Benefits:
- **Explicit Control**: You choose exact state names
- **IDE Friendly**: Full import support and refactoring
- **Visible**: All states listed in one place
- **Safe**: Import errors catch missing classes

## Simple Example: Data Processing Pipeline

Consider a data processing workflow with these states:

### State Definitions
```python
class DataValidationState(AnalysisState):
    POSSIBLE_TRANSITIONS = {
        'data_cleaning': StateTransition('data_cleaning', 'validation_passed', 'Data is valid'),
        'error_handling': StateTransition('error_handling', 'validation_failed', 'Data has errors')
    }
    
    def execute(self, context):
        data = context['input_data']
        is_valid = self.validate_data(data)
        return {'valid': is_valid, 'error_count': len(errors)}
    
    def determine_next_state(self, result, context):
        return 'data_cleaning' if result['valid'] else 'error_handling'

class DataCleaningState(AnalysisState):
    POSSIBLE_TRANSITIONS = {
        'analysis': StateTransition('analysis', 'cleaning_complete', 'Data ready for analysis')
    }
    
    def execute(self, context):
        # Clean the data based on validation results
        return {'cleaned_data': cleaned_data, 'records_processed': count}
    
    def determine_next_state(self, result, context):
        return 'analysis'  # Always proceed to analysis
```

### Example Workflow Map
```
🔵 data_validation
   Transitions:
     • data_cleaning → IF validation passes
     • error_handling → IF validation fails

🔵 data_cleaning  
   Transitions:
     • analysis → Always proceed

🔵 error_handling
   Transitions:
     • data_validation → Retry after fixes
     • END → Give up after max attempts

🔵 analysis
   Transitions:
     • END → Workflow complete
```

### Possible Execution Flows
```
# Happy path
data_validation → data_cleaning → analysis → END

# Error path with retry
data_validation → error_handling → data_validation → data_cleaning → analysis → END

# Error path with failure
data_validation → error_handling → END
```

## Architecture Components

### 1. Analysis State (Abstract Base)
```python
class AnalysisState(ABC):
    POSSIBLE_TRANSITIONS: Dict[str, StateTransition] = {}
    
    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute state logic."""
        pass
    
    @abstractmethod
    def determine_next_state(self, execution_result: Dict[str, Any], context: Dict[str, Any]) -> Optional[str]:
        """Determine next state."""
        pass
    
    def validate_input(self, context: Dict[str, Any]) -> None:
        """Validate required input context."""
        pass
```

### 2. State Transition Definition
```python
@dataclass
class StateTransition:
    target_state: str
    condition: str  
    description: str
```

### 3. Workflow State Map
Auto-generated from state definitions:
```python
class WorkflowStateMap:
    @staticmethod
    def generate_state_map() -> Dict[str, Any]:
        """Generate workflow map from registered states."""
        
    @staticmethod
    def validate_state_map(state_map: Dict[str, Any]) -> List[str]:
        """Validate workflow consistency."""
        
    @staticmethod
    def print_state_map():
        """Visualize workflow for debugging."""
```

### 4. Analysis Orchestrator
```python
class AnalysisOrchestrator:
    def run_workflow(self, input_data: Any, initial_state: str) -> Dict[str, Any]:
        context = self._initialize_context(input_data)
        current_state_name = initial_state
        
        while current_state_name:
            state = self.states[current_state_name]
            
            # Execute state
            execution_result = state.execute(context)
            
            # Store results and grow context
            context['workflow_results'][current_state_name] = execution_result
            context['accumulated_knowledge'].update(execution_result.get('knowledge', {}))
            
            # Determine next state
            current_state_name = state.determine_next_state(execution_result, context)
        
        return context['workflow_results']
```

## Quality Assurance

### Validation Mechanisms
- **State Map Validation**: Verify all referenced states exist
- **Transition Validation**: Ensure returned states are in allowed transitions  
- **Context Validation**: Check required fields present for each state
- **Workflow Completeness**: Confirm workflows can reach terminal states

### Error Handling
- **State-Level**: Each state handles its own exceptions with context
- **Workflow-Level**: Orchestrator logs workflow context and re-raises
- **Transition-Level**: Invalid transitions caught by validation

## Loop Prevention and Transition Restrictions

### Self-Transition Prohibition

**Rule**: States cannot transition to themselves.

**Implementation**: The `validate_transitions()` method in `AnalysisState` explicitly checks for and rejects self-transitions:

```python
@classmethod
def validate_transitions(cls) -> None:
    for transition_key, transition in cls.POSSIBLE_TRANSITIONS.items():
        if transition.target_state == state_name:
            raise ValueError(
                f"Self-transition not allowed: {cls.__name__} cannot transition to itself"
            )
```

**Rationale**: 
- Prevents infinite loops at the state level
- Forces explicit workflow design decisions
- Simplifies loop detection and prevention
- Any retry logic must be handled by the orchestrator, not individual states

### Orchestrator-Level Loop Prevention

**Maximum State Limit**: The orchestrator enforces a hard limit of `MAX_TOTAL_STATES = 50` total state executions per workflow.

**Implementation**: 
```python
while current_state_name and iteration_count < MAX_TOTAL_STATES:
    # Execute state
    iteration_count += 1

if current_state_name and iteration_count >= MAX_TOTAL_STATES:
    raise WorkflowExecutionError(f"Workflow exceeded maximum total states ({MAX_TOTAL_STATES})")
```

**Design Philosophy**:
- **Fixed Limit**: No configuration - uses a generous but reasonable upper bound (50 states)
- **Fail-Fast**: Workflows that hit the limit indicate design problems, not configuration issues
- **Explicit Loops**: Any intentional looping (e.g., retry patterns) must be designed into the state machine workflow map

### Workflow Design Implications

**For Retry Patterns**: Instead of state self-transitions, design explicit retry workflows:
```
data_validation → error_handling → data_validation_retry → analysis
```

**For Iterative Processing**: Use multiple related states rather than loops:
```
initial_analysis → refinement_analysis → validation_analysis → complete
```

**For Conditional Processing**: Use branching patterns with clear termination:
```
assessment → branch_a OR branch_b → consolidation → complete
```

### Transition Validation

The orchestrator validates every state transition:
1. **Existence Check**: Target state must be registered in the state registry
2. **Declaration Check**: Target state must be declared in source state's `POSSIBLE_TRANSITIONS`
3. **Self-Transition Check**: Target state cannot be the same as source state

**Validation Failure**: Any validation failure raises `WorkflowExecutionError` with context about the invalid transition.

## Implementation Strategy

### Phase 1: Core Infrastructure
1. Create state base classes and transition definitions
2. Implement state registry and discovery system  
3. Build workflow state map generator and validator
4. Create basic orchestrator framework

### Phase 2: Migration and Testing
1. Convert existing analysis to state-based implementation
2. Add transition logic and validation
3. Test multi-state workflows
4. Validate state map generation and visualization

### Phase 3: Advanced Features
1. Add sophisticated transition logic
2. Implement context accumulation strategies
3. Add workflow debugging and monitoring
4. Performance optimization for complex workflows

## Integration with Existing System

### Backward Compatibility
- Existing analysis methods remain functional
- CLI flags can switch between old and new implementations
- Current result formats maintained

### Configuration Integration
```python
# config.py additions
workflow_timeout_seconds: int = Field(default=1800)
max_iterations_per_state: int = Field(default=3)
state_specific_settings: Dict[str, Any] = Field(default={})
```

This state machine architecture provides a flexible foundation for complex analysis workflows while maintaining simplicity in the core design patterns.