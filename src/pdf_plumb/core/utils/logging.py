"""Logging and debugging utilities for the PDF processing pipeline."""

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

class LogManager:
    """Manages logging for the pipeline."""
    
    def __init__(self, level: str = 'INFO'):
        self.logger = logging.getLogger('pdf_plumb')
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        self.logger.addHandler(console_handler)
        
    def info(self, message: str):
        """Log an info message."""
        self.logger.info(message)
        
    def error(self, message: str):
        """Log an error message."""
        self.logger.error(message)
        
    def debug(self, message: str):
        """Log a debug message."""
        self.logger.debug(message)

class DebugManager:
    """Manages debugging capabilities."""
    
    def __init__(self, level: str = 'INFO'):
        self.level = level
        self.debug_data: Dict[str, Any] = {}
        self.errors: Dict[str, Exception] = {}
        
    def capture_state(self, stage: str, data: Any):
        """Capture the state at a particular stage."""
        if self.level == 'DEBUG':
            self.debug_data[stage] = data
            
    def capture_error(self, stage: str, error: Exception):
        """Capture an error that occurred during processing."""
        self.errors[stage] = {
            'type': type(error).__name__,
            'message': str(error),
            'timestamp': datetime.now().isoformat()
        }
        
    def generate_debug_report(self, output_dir: str):
        """Generate a debug report."""
        if not self.debug_data and not self.errors:
            return
            
        debug_dir = Path(output_dir) / 'debug'
        debug_dir.mkdir(exist_ok=True)
        
        # Save state data
        for stage, data in self.debug_data.items():
            state_file = debug_dir / f"{stage}_state.json"
            with open(state_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        # Save error data
        if self.errors:
            error_file = debug_dir / 'errors.json'
            with open(error_file, 'w') as f:
                json.dump(self.errors, f, indent=2) 