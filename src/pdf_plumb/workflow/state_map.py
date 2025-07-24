"""Workflow state map generation and validation."""

from typing import Dict, Any, List, Set
from .registry import get_all_states
from .state import AnalysisState


class WorkflowStateMap:
    """Generates and validates workflow state maps."""
    
    @staticmethod
    def generate_state_map() -> Dict[str, Any]:
        """Generate complete workflow state map from registered states.
        
        Returns:
            Dictionary containing state map with transitions and metadata
        """
        states = get_all_states()
        state_map = {}
        
        for state_name, state_class in states.items():
            transitions = {}
            
            # Extract transition information
            for trans_key, transition in state_class.POSSIBLE_TRANSITIONS.items():
                transitions[trans_key] = {
                    'target_state': transition.target_state,
                    'condition': transition.condition,
                    'description': transition.description
                }
            
            # Build state entry
            state_map[state_name] = {
                'class': state_class.__name__,
                'module': state_class.__module__,
                'transitions': transitions,
                'possible_next_states': [
                    transition.target_state 
                    for transition in state_class.POSSIBLE_TRANSITIONS.values()
                    if transition.target_state is not None
                ],
                'required_fields': getattr(state_class, 'REQUIRED_FIELDS', []),
                'is_terminal': len([
                    t for t in state_class.POSSIBLE_TRANSITIONS.values() 
                    if t.target_state is None
                ]) > 0
            }
        
        return state_map
    
    @staticmethod
    def validate_state_map(state_map: Dict[str, Any] = None) -> List[str]:
        """Validate state map for consistency.
        
        Args:
            state_map: State map to validate (generates if None)
            
        Returns:
            List of validation errors (empty if valid)
        """
        if state_map is None:
            state_map = WorkflowStateMap.generate_state_map()
        
        errors = []
        all_states = set(state_map.keys())
        
        # Check for broken references
        for state_name, state_info in state_map.items():
            for next_state in state_info['possible_next_states']:
                if next_state and next_state not in all_states:
                    errors.append(f"State '{state_name}' references unknown state '{next_state}'")
        
        # Check for unreachable states (states that no other state transitions to)
        reachable_states = set()
        for state_info in state_map.values():
            reachable_states.update(state_info['possible_next_states'])
        
        # Remove None (terminal transitions)
        reachable_states.discard(None)
        
        # Find unreachable states (excluding potential starting states)
        all_states_set = set(state_map.keys())
        unreachable = all_states_set - reachable_states
        
        # Entry states (unreachable by transitions) are valid as workflow starting points
        # Only report as error if ALL states are unreachable (indicates broken workflow)
        if len(all_states_set) > 1 and unreachable == all_states_set:
            errors.append("All states are unreachable - no valid workflow paths exist")
        # Individual unreachable states are potential entry points, not errors
        
        # Check for terminal workflows (at least one path should lead to termination)
        has_terminal_path = any(state_info['is_terminal'] for state_info in state_map.values())
        if not has_terminal_path and state_map:
            errors.append("No terminal states found - workflow may run indefinitely")
        
        return errors
    
    @staticmethod
    def find_workflow_paths(state_map: Dict[str, Any] = None, start_state: str = None) -> List[List[str]]:
        """Find all possible workflow paths.
        
        Args:
            state_map: State map to analyze (generates if None)
            start_state: Starting state (uses first state if None)
            
        Returns:
            List of workflow paths (each path is list of state names)
        """
        if state_map is None:
            state_map = WorkflowStateMap.generate_state_map()
        
        if not state_map:
            return []
        
        if start_state is None:
            start_state = next(iter(state_map.keys()))
        
        paths = []
        
        def _find_paths(current_state: str, current_path: List[str], visited: Set[str]) -> None:
            """Recursively find all paths from current state."""
            if current_state in visited:
                # Cycle detected - end this path
                paths.append(current_path + [f"{current_state} (cycle)"])
                return
            
            current_path = current_path + [current_state]
            next_states = state_map[current_state]['possible_next_states']
            
            # Check if this state can terminate the workflow
            can_terminate = any(
                trans_info['target_state'] is None 
                for trans_info in state_map[current_state]['transitions'].values()
            )
            
            if can_terminate or not next_states:
                # Terminal state reached
                paths.append(current_path)
                if not next_states:  # No more transitions
                    return
            
            visited_copy = visited.copy()
            visited_copy.add(current_state)
            
            for next_state in next_states:
                if next_state:  # Skip None (terminal) transitions
                    _find_paths(next_state, current_path, visited_copy)
        
        _find_paths(start_state, [], set())
        return paths
    
    @staticmethod
    def print_state_map(state_map: Dict[str, Any] = None) -> None:
        """Pretty print the workflow state map.
        
        Args:
            state_map: State map to print (generates if None)
        """
        if state_map is None:
            state_map = WorkflowStateMap.generate_state_map()
        
        errors = WorkflowStateMap.validate_state_map(state_map)
        
        print("=== WORKFLOW STATE MAP ===\n")
        
        if not state_map:
            print("No states registered.\n")
            return
        
        # Print states
        for state_name, state_info in state_map.items():
            terminal_indicator = " (terminal)" if state_info['is_terminal'] else ""
            print(f"🔵 {state_name}{terminal_indicator}")
            print(f"   Class: {state_info['class']}")
            print(f"   Module: {state_info['module']}")
            
            if state_info['required_fields']:
                print(f"   Required fields: {', '.join(state_info['required_fields'])}")
            
            if state_info['transitions']:
                print("   Transitions:")
                for trans_key, trans_info in state_info['transitions'].items():
                    target = trans_info['target_state'] or 'END'
                    print(f"     • {trans_key} → {target}")
                    print(f"       Condition: {trans_info['condition']}")
                    print(f"       Description: {trans_info['description']}")
            else:
                print("   Transitions: None")
            
            print()
        
        # Print workflow paths
        if len(state_map) > 1:
            print("=== POSSIBLE WORKFLOW PATHS ===\n")
            for i, start_state in enumerate(state_map.keys()):
                paths = WorkflowStateMap.find_workflow_paths(state_map, start_state)
                if paths:
                    print(f"Starting from '{start_state}':")
                    for path in paths[:3]:  # Show first 3 paths to avoid clutter
                        print(f"  {' → '.join(path)}")
                    if len(paths) > 3:
                        print(f"  ... and {len(paths) - 3} more paths")
                    print()
        
        # Print validation results
        if errors:
            print("❌ VALIDATION ERRORS:")
            for error in errors:
                print(f"   • {error}")
        else:
            print("✅ State map validation passed")
        
        print()
    
    @staticmethod
    def export_state_map(state_map: Dict[str, Any] = None, format: str = 'json') -> str:
        """Export state map in specified format.
        
        Args:
            state_map: State map to export (generates if None)
            format: Export format ('json', 'yaml', 'dot')
            
        Returns:
            State map in specified format
            
        Raises:
            ValueError: If format not supported
        """
        if state_map is None:
            state_map = WorkflowStateMap.generate_state_map()
        
        if format == 'json':
            import json
            return json.dumps(state_map, indent=2)
        elif format == 'yaml':
            try:
                import yaml
                return yaml.dump(state_map, default_flow_style=False)
            except ImportError:
                raise ValueError("PyYAML not available for YAML export")
        elif format == 'dot':
            # Generate Graphviz DOT format for visualization
            lines = ['digraph workflow {']
            lines.append('  rankdir=TB;')
            lines.append('  node [shape=box];')
            
            # Add nodes
            for state_name, state_info in state_map.items():
                label = state_name
                if state_info['is_terminal']:
                    label += '\\n(terminal)'
                lines.append(f'  "{state_name}" [label="{label}"];')
            
            # Add edges
            for state_name, state_info in state_map.items():
                for trans_key, trans_info in state_info['transitions'].items():
                    target = trans_info['target_state']
                    if target:
                        condition = trans_info['condition']
                        lines.append(f'  "{state_name}" -> "{target}" [label="{condition}"];')
            
            lines.append('}')
            return '\n'.join(lines)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    @staticmethod
    def get_entry_states(state_map: Dict[str, Any] = None) -> List[str]:
        """Get potential entry states (states with no incoming transitions).
        
        Args:
            state_map: State map to analyze (generates if None)
            
        Returns:
            List of potential entry state names
        """
        if state_map is None:
            state_map = WorkflowStateMap.generate_state_map()
        
        all_states = set(state_map.keys())
        target_states = set()
        
        # Collect all states that are targets of transitions
        for state_info in state_map.values():
            target_states.update(state_info['possible_next_states'])
        
        target_states.discard(None)  # Remove terminal transitions
        
        # Entry states are those not targeted by any transition
        entry_states = all_states - target_states
        return list(entry_states)
    
    @staticmethod
    def get_terminal_states(state_map: Dict[str, Any] = None) -> List[str]:
        """Get terminal states (states that can end the workflow).
        
        Args:
            state_map: State map to analyze (generates if None)
            
        Returns:
            List of terminal state names
        """
        if state_map is None:
            state_map = WorkflowStateMap.generate_state_map()
        
        terminal_states = []
        for state_name, state_info in state_map.items():
            if state_info['is_terminal']:
                terminal_states.append(state_name)
        
        return terminal_states