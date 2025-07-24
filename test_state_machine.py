#!/usr/bin/env python3
"""Simple test script to verify state machine infrastructure."""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from pdf_plumb.workflow import (
    AnalysisOrchestrator, 
    WorkflowStateMap, 
    STATE_REGISTRY,
    get_all_states
)


def test_state_machine_infrastructure():
    """Test basic state machine infrastructure."""
    print("=== TESTING STATE MACHINE INFRASTRUCTURE ===\n")
    
    # Test 1: Registry
    print("1. Testing State Registry...")
    states = get_all_states()
    print(f"   Registered states: {list(states.keys())}")
    print(f"   Total states: {len(states)}")
    print("   ✅ Registry working\n")
    
    # Test 2: State Map Generation
    print("2. Testing State Map Generation...")
    state_map = WorkflowStateMap.generate_state_map()
    print(f"   Generated state map for {len(state_map)} states")
    
    # Show state map
    WorkflowStateMap.print_state_map(state_map)
    
    # Test 3: State Map Validation
    print("3. Testing State Map Validation...")
    errors = WorkflowStateMap.validate_state_map(state_map)
    if errors:
        print("   ❌ Validation errors:")
        for error in errors:
            print(f"      • {error}")
    else:
        print("   ✅ State map validation passed")
    print()
    
    # Test 4: Workflow Orchestrator
    print("4. Testing Workflow Orchestrator...")
    try:
        orchestrator = AnalysisOrchestrator()
        print("   ✅ Orchestrator initialization successful")
        
        # Test workflow info
        orchestrator.print_workflow_info()
        
    except Exception as e:
        print(f"   ❌ Orchestrator initialization failed: {e}")
        return False
    
    # Test 5: Simple Workflow Execution
    print("5. Testing Simple Workflow Execution...")
    try:
        # Create simple test data
        test_document = {
            'pages': [
                {'page_number': 1, 'text': 'Test page 1'},
                {'page_number': 2, 'text': 'Test page 2'},
            ]
        }
        
        # Run workflow
        results = orchestrator.run_workflow(
            document_data=test_document,
            initial_state='example_1',
            save_context=True
        )
        
        print("   ✅ Workflow execution successful")
        print(f"   Workflow summary: {results['summary']}")
        print(f"   States executed: {list(results['workflow_results'].keys())}")
        print(f"   Knowledge accumulated: {list(results['accumulated_knowledge'].keys())}")
        
    except Exception as e:
        print(f"   ❌ Workflow execution failed: {e}")
        return False
    
    print("\n=== ALL TESTS PASSED ===")
    return True


if __name__ == "__main__":
    success = test_state_machine_infrastructure()
    sys.exit(0 if success else 1)