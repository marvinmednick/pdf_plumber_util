"""Configuration management for PDF Plumb using Pydantic."""

from pathlib import Path
from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings


class PDFPlumbConfig(BaseSettings):
    """PDF Plumb configuration with environment variable support."""
    
    # Extraction settings
    y_tolerance: float = Field(
        default=3.0,
        description="Y-axis tolerance for word alignment in points"
    )
    x_tolerance: float = Field(
        default=3.0, 
        description="X-axis tolerance for word alignment in points"
    )
    
    # Analysis settings
    large_gap_multiplier: float = Field(
        default=1.8,
        description="Gap must be > this * body_spacing to be considered 'large'"
    )
    small_gap_multiplier: float = Field(
        default=1.3,
        description="Gap must be < this * body_spacing to be considered 'small'"
    )
    round_to_nearest_pt: float = Field(
        default=0.5,
        description="Rounding precision for font sizes and spacings"
    )
    
    # Contextual spacing settings
    line_spacing_tolerance: float = Field(
        default=0.2,
        description="20% tolerance for line spacing variation"
    )
    para_spacing_multiplier: float = Field(
        default=1.1,
        description="Paragraph spacing is ~1.1x font size"
    )
    section_spacing_multiplier: float = Field(
        default=2.0,
        description="Section spacing is > paragraph spacing"
    )
    gap_rounding: float = Field(
        default=0.5,
        description="Round gaps to nearest 0.5pt for analysis"
    )
    
    # Page layout settings
    points_per_inch: float = Field(
        default=72.0,
        description="Points per inch conversion factor"
    )
    default_page_height: float = Field(
        default=11 * 72,  # US Letter
        description="Default page height in points"
    )
    header_zone_inches: float = Field(
        default=1.25,
        description="Header zone extends this many inches from top"
    )
    footer_zone_inches: float = Field(
        default=1.0,
        description="Footer zone extends this many inches from bottom"
    )
    
    # Directories
    output_dir: Path = Field(
        default=Path("output"),
        description="Default output directory for results"
    )
    data_dir: Path = Field(
        default=Path("data"),
        description="Default data directory for input files"
    )
    
    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)"
    )
    
    # Visualization defaults
    default_spacing_colors: List[str] = Field(
        default=[
            'red', 'blue', 'green', 'purple', 'orange', 'pink', 'magenta', 
            'yellow', 'lightblue', 'darkred', 'darkblue', 'darkgreen'
        ],
        description="Default colors for spacing visualization"
    )
    default_spacing_patterns: List[str] = Field(
        default=['solid', 'dashed', 'dotted', 'dashdot'],
        description="Default line patterns for spacing visualization"
    )
    
    model_config = {
        "env_file": ".env",
        "env_prefix": "PDF_PLUMB_",
        "env_file_encoding": "utf-8"
    }


# Global configuration instance
config = PDFPlumbConfig()


def get_config() -> PDFPlumbConfig:
    """Get the global configuration instance."""
    return config


def update_config(**kwargs) -> PDFPlumbConfig:
    """Update configuration with new values."""
    global config
    # Create new config with updated values
    current_values = config.model_dump()
    current_values.update(kwargs)
    config = PDFPlumbConfig(**current_values)
    return config


def reset_config() -> PDFPlumbConfig:
    """Reset configuration to defaults."""
    global config
    config = PDFPlumbConfig()
    return config


class DocumentTypeProfiles:
    """Predefined configuration profiles for different document types."""
    
    @staticmethod
    def technical_specification() -> dict:
        """Configuration optimized for technical specifications."""
        return {
            "y_tolerance": 3.0,
            "x_tolerance": 2.5,
            "large_gap_multiplier": 1.8,
            "small_gap_multiplier": 1.3,
            "header_zone_inches": 1.25,
            "footer_zone_inches": 1.0
        }
    
    @staticmethod
    def academic_paper() -> dict:
        """Configuration optimized for academic papers."""
        return {
            "y_tolerance": 2.5,
            "x_tolerance": 3.0,
            "large_gap_multiplier": 1.6,
            "small_gap_multiplier": 1.2,
            "header_zone_inches": 1.0,
            "footer_zone_inches": 0.75
        }
    
    @staticmethod
    def manual() -> dict:
        """Configuration optimized for user manuals."""
        return {
            "y_tolerance": 4.0,
            "x_tolerance": 3.5,
            "large_gap_multiplier": 2.0,
            "small_gap_multiplier": 1.4,
            "header_zone_inches": 1.5,
            "footer_zone_inches": 1.25
        }
    
    @staticmethod
    def dense_text() -> dict:
        """Configuration optimized for densely-packed documents."""
        return {
            "y_tolerance": 2.0,
            "x_tolerance": 1.5,
            "large_gap_multiplier": 1.5,
            "small_gap_multiplier": 1.2,
            "line_spacing_tolerance": 0.15,
            "para_spacing_multiplier": 1.05
        }


def apply_profile(profile_name: str) -> PDFPlumbConfig:
    """Apply a document type profile to the configuration."""
    profiles = {
        "technical": DocumentTypeProfiles.technical_specification,
        "academic": DocumentTypeProfiles.academic_paper,
        "manual": DocumentTypeProfiles.manual,
        "dense": DocumentTypeProfiles.dense_text
    }
    
    if profile_name not in profiles:
        available = ", ".join(profiles.keys())
        raise ValueError(f"Unknown profile '{profile_name}'. Available: {available}")
    
    profile_config = profiles[profile_name]()
    return update_config(**profile_config)


# Convenience functions for backward compatibility
def get_tolerance_settings() -> tuple:
    """Get current tolerance settings."""
    return config.y_tolerance, config.x_tolerance


def get_spacing_multipliers() -> tuple:
    """Get current spacing multipliers."""
    return config.large_gap_multiplier, config.small_gap_multiplier


def get_zone_settings() -> tuple:
    """Get current zone settings in points."""
    header_points = config.header_zone_inches * config.points_per_inch
    footer_points = config.footer_zone_inches * config.points_per_inch
    return header_points, footer_points