"""Example state implementations for testing state machine infrastructure."""

from typing import Dict, Any, Optional
from ..state import AnalysisState, StateTransition


class ExampleState(AnalysisState):
    """Example state for testing state machine infrastructure."""
    
    POSSIBLE_TRANSITIONS = {
        'next_example': StateTransition(
            target_state='example_2',
            condition='always_proceed',
            description='Always proceed to example state 2'
        ),
        'terminate': StateTransition(
            target_state=None,
            condition='manual_termination',
            description='End workflow manually'
        )
    }
    
    REQUIRED_FIELDS = ['document_data']
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute example analysis."""
        self.validate_input(context)
        
        # Simple example logic
        document_data = context['document_data']
        
        # Simulate analysis
        if isinstance(document_data, list):
            pages_count = len(document_data)
        elif isinstance(document_data, dict) and 'pages' in document_data:
            pages_count = len(document_data['pages'])
        else:
            pages_count = 1
        
        return {
            'analysis_type': 'example_analysis',
            'results': {
                'pages_analyzed': pages_count,
                'example_metric': pages_count * 1.5
            },
            'metadata': {
                'confidence': 0.95,
                'processing_time': 0.1
            },
            'knowledge': {
                'example_pattern': f'Document has {pages_count} pages'
            }
        }
    
    def determine_next_state(self, execution_result: Dict[str, Any], context: Dict[str, Any]) -> Optional[str]:
        """Determine next state based on results."""
        # Simple logic: always proceed to next example state
        return 'example_2'


class Example2State(AnalysisState):
    """Second example state for testing workflows."""
    
    POSSIBLE_TRANSITIONS = {
        'complete': StateTransition(
            target_state=None,
            condition='analysis_complete',
            description='Analysis workflow complete'
        )
    }
    
    REQUIRED_FIELDS = ['document_data', 'workflow_results']
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute second example analysis."""
        self.validate_input(context)
        
        # Access previous results
        previous_results = context['workflow_results'].get('example_1', {})
        previous_pages = previous_results.get('results', {}).get('pages_analyzed', 0)
        
        return {
            'analysis_type': 'example_analysis_2',
            'results': {
                'previous_pages': previous_pages,
                'enhanced_metric': previous_pages * 2.0,
                'workflow_progress': '100%'
            },
            'metadata': {
                'confidence': 0.98,
                'processing_time': 0.05
            },
            'knowledge': {
                'workflow_pattern': 'Two-stage example analysis complete'
            }
        }
    
    def determine_next_state(self, execution_result: Dict[str, Any], context: Dict[str, Any]) -> Optional[str]:
        """Determine next state - terminate workflow."""
        return None  # End workflow