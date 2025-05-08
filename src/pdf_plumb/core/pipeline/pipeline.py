"""Core pipeline implementation for PDF processing."""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from pathlib import Path
from ..utils.logging import LogManager, DebugManager

@dataclass
class PipelineConfig:
    """Configuration for the processing pipeline."""
    save_intermediate: bool = True
    debug_level: str = 'INFO'
    output_dir: str = 'output'
    base_name: str = 'document'
    gap_rounding: float = 0.5

class ProcessingPipeline:
    """Manages the document processing pipeline stages."""
    
    def __init__(self, config: PipelineConfig):
        self.stages: List['PipelineStage'] = []
        self.config = config
        self.results: Dict[str, Any] = {}
        self.logger = LogManager(config.debug_level)
        self.debugger = DebugManager(config.debug_level)
        
        # Ensure output directory exists
        Path(config.output_dir).mkdir(parents=True, exist_ok=True)
        
    def add_stage(self, stage: 'PipelineStage'):
        """Add a processing stage to the pipeline."""
        self.stages.append(stage)
        self.logger.info(f"Added stage: {stage.name}")
        
    def run(self, input_data: Any) -> Dict:
        """Run the complete pipeline."""
        self.logger.info("Starting pipeline execution")
        current_data = input_data
        
        for stage in self.stages:
            self.logger.info(f"Processing stage: {stage.name}")
            try:
                # Capture pre-stage state
                self.debugger.capture_state(f"{stage.name}_before", current_data)
                
                # Process stage
                current_data = stage.process(current_data)
                
                # Capture post-stage state
                self.debugger.capture_state(f"{stage.name}_after", current_data)
                
                # Store results
                self.results[stage.name] = current_data
                
                # Save intermediate results if configured
                if self.config.save_intermediate:
                    stage.save_results(current_data)
                    
                self.logger.info(f"Completed stage: {stage.name}")
                
            except Exception as e:
                self.logger.error(f"Error in stage {stage.name}: {str(e)}")
                self.debugger.capture_error(stage.name, e)
                raise
                
        self.logger.info("Pipeline execution completed")
        
        # Generate debug report
        self.debugger.generate_debug_report(self.config.output_dir)
        
        return self.results 