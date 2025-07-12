"""File handling utilities for PDF Plumb.

This module provides a centralized way to handle file operations for the PDF Plumb tool,
ensuring consistent file naming, directory structure, and error handling across all stages
of processing.
"""

from .json_utils import dump, load, JSONDecodeError
from pathlib import Path
from typing import Dict, Any, Optional
from .helpers import ensure_output_dir, get_base_name
from ..core.utils.logging import LogManager


class FileHandler:
    """Handles file operations for PDF Plumb.
    
    This class provides methods for saving and loading various types of analysis
    and intermediate results, ensuring consistent file naming and directory structure.
    """
    
    _instance = None
    
    def __new__(cls, output_dir: str = "output", debug_level: str = "INFO"):
        """Create or return the singleton instance."""
        if cls._instance is None:
            cls._instance = super(FileHandler, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, output_dir: str = "output", debug_level: str = "INFO"):
        """Initialize the file handler if not already initialized.
        
        Args:
            output_dir: Base directory for all output files
            debug_level: Logging level for the handler
        """
        if not self._initialized:
            self.output_dir = output_dir
            self.logger = LogManager(debug_level)
            self._initialized = True
        else:
            # Update output directory and logging level if already initialized
            self.output_dir = output_dir
            if hasattr(self, 'logger'):
                self.logger = LogManager(debug_level)
    
    def save_json(self, data: Dict[str, Any], base_name: str, stage: str) -> Optional[Path]:
        """Save data as JSON file.
        
        Args:
            data: Data to save
            base_name: Base name for the file
            stage: Processing stage (e.g., 'lines', 'blocks', 'analysis')
            
        Returns:
            Path to the saved file if successful, None otherwise
        """
        try:
            # Ensure output directory exists
            output_dir = ensure_output_dir(self.output_dir)
            
            # Create output file path
            output_file = Path(output_dir) / f"{base_name}_{stage}.json"
            
            # Save data
            with open(output_file, "w", encoding="utf-8") as f:
                dump(data, f, indent=2)
                
            self.logger.info(f"Saved {stage} data to {output_file}")
            return output_file
            
        except Exception as e:
            self.logger.error(f"Error saving {stage} data: {e}")
            return None
            
    def load_json(self, base_name: str, stage: str) -> Optional[Dict[str, Any]]:
        """Load data from JSON file.
        
        Args:
            base_name: Base name of the file
            stage: Processing stage (e.g., 'lines', 'blocks', 'analysis')
            
        Returns:
            Loaded data if successful, None otherwise
        """
        try:
            # Create input file path
            input_file = Path(self.output_dir) / f"{base_name}_{stage}.json"
            
            if not input_file.exists():
                self.logger.warning(f"No {stage} data found at {input_file}")
                return None
                
            # Load data
            with open(input_file, "r", encoding="utf-8") as f:
                data = load(f)
                
            self.logger.info(f"Loaded {stage} data from {input_file}")
            return data
            
        except Exception as e:
            self.logger.error(f"Error loading {stage} data: {e}")
            return None
            
    def save_text(self, text: str, base_name: str, stage: str) -> Optional[Path]:
        """Save text data to file.
        
        Args:
            text: Text to save
            base_name: Base name for the file
            stage: Processing stage (e.g., 'analysis', 'report')
            
        Returns:
            Path to the saved file if successful, None otherwise
        """
        try:
            # Ensure output directory exists
            output_dir = ensure_output_dir(self.output_dir)
            
            # Create output file path
            output_file = Path(output_dir) / f"{base_name}_{stage}.txt"
            
            # Save data
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(text)
                
            self.logger.info(f"Saved {stage} text to {output_file}")
            return output_file
            
        except Exception as e:
            self.logger.error(f"Error saving {stage} text: {e}")
            return None
            
    def get_file_path(self, base_name: str, stage: str, extension: str = "json") -> Path:
        """Get the path for a file without saving it.
        
        Args:
            base_name: Base name for the file
            stage: Processing stage
            extension: File extension (default: 'json')
            
        Returns:
            Path object for the file
        """
        return Path(self.output_dir) / f"{base_name}_{stage}.{extension}" 
"""File handling utilities for PDF Plumb.

This module provides a centralized way to handle file operations for the PDF Plumb tool,
ensuring consistent file naming, directory structure, and error handling across all stages
of processing.
"""

from .json_utils import dump, load, JSONDecodeError
from pathlib import Path
from typing import Dict, Any, Optional
from .helpers import ensure_output_dir, get_base_name
from ..core.utils.logging import LogManager


class FileHandler:
    """Handles file operations for PDF Plumb.
    
    This class provides methods for saving and loading various types of analysis
    and intermediate results, ensuring consistent file naming and directory structure.
    """
    
    _instance = None
    
    def __new__(cls, output_dir: str = "output", debug_level: str = "INFO"):
        """Create or return the singleton instance."""
        if cls._instance is None:
            cls._instance = super(FileHandler, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, output_dir: str = "output", debug_level: str = "INFO"):
        """Initialize the file handler if not already initialized.
        
        Args:
            output_dir: Base directory for all output files
            debug_level: Logging level for the handler (only used on first initialization)
        """
        if not self._initialized:
            self.output_dir = output_dir
            self.logger = LogManager(debug_level)
            self._initialized = True
    
    def save_json(self, data: Dict[str, Any], base_name: str, stage: str) -> Optional[Path]:
        """Save data as JSON file.
        
        Args:
            data: Data to save
            base_name: Base name for the file
            stage: Processing stage (e.g., 'lines', 'blocks', 'analysis')
            
        Returns:
            Path to the saved file if successful, None otherwise
        """
        try:
            # Ensure output directory exists
            output_dir = ensure_output_dir(self.output_dir)
            
            # Create output file path
            output_file = Path(output_dir) / f"{base_name}_{stage}.json"
            
            # Save data
            with open(output_file, "w", encoding="utf-8") as f:
                dump(data, f, indent=2)
                
            self.logger.info(f"Saved {stage} data to {output_file}")
            return output_file
            
        except Exception as e:
            self.logger.error(f"Error saving {stage} data: {e}")
            return None
            
    def load_json(self, base_name: str, stage: str) -> Optional[Dict[str, Any]]:
        """Load data from JSON file.
        
        Args:
            base_name: Base name of the file
            stage: Processing stage (e.g., 'lines', 'blocks', 'analysis')
            
        Returns:
            Loaded data if successful, None otherwise
        """
        try:
            # Create input file path
            input_file = Path(self.output_dir) / f"{base_name}_{stage}.json"
            
            if not input_file.exists():
                self.logger.warning(f"No {stage} data found at {input_file}")
                return None
                
            # Load data
            with open(input_file, "r", encoding="utf-8") as f:
                data = load(f)
                
            self.logger.info(f"Loaded {stage} data from {input_file}")
            return data
            
        except Exception as e:
            self.logger.error(f"Error loading {stage} data: {e}")
            return None
            
    def save_text(self, text: str, base_name: str, stage: str) -> Optional[Path]:
        """Save text data to file.
        
        Args:
            text: Text to save
            base_name: Base name for the file
            stage: Processing stage (e.g., 'analysis', 'report')
            
        Returns:
            Path to the saved file if successful, None otherwise
        """
        try:
            # Ensure output directory exists
            output_dir = ensure_output_dir(self.output_dir)
            
            # Create output file path
            output_file = Path(output_dir) / f"{base_name}_{stage}.txt"
            
            # Save data
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(text)
                
            self.logger.info(f"Saved {stage} text to {output_file}")
            return output_file
            
        except Exception as e:
            self.logger.error(f"Error saving {stage} text: {e}")
            return None
            
    def get_file_path(self, base_name: str, stage: str, extension: str = "json") -> Path:
        """Get the path for a file without saving it.
        
        Args:
            base_name: Base name for the file
            stage: Processing stage
            extension: File extension (default: 'json')
            
        Returns:
            Path object for the file
        """
        return Path(self.output_dir) / f"{base_name}_{stage}.{extension}" 