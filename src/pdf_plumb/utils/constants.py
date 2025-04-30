"""Shared constants for the pdf_plumb package."""

# Points per inch
POINTS_PER_INCH = 72

# Default page dimensions
DEFAULT_PAGE_HEIGHT = 11 * POINTS_PER_INCH  # US Letter default

# Header/Footer zone sizes
HEADER_ZONE_INCHES = 1.25
FOOTER_ZONE_INCHES = 1.0

# Spacing multipliers (relative to typical body spacing)
LARGE_GAP_MULTIPLIER = 1.8  # Gap must be > this * body_spacing to be considered 'large'
SMALL_GAP_MULTIPLIER = 1.3  # Gap must be < this * body_spacing to be considered 'small'

# Rounding precision for font sizes and spacings
ROUND_TO_NEAREST_PT = 0.5  # Change to 0.25 for quarter-point rounding 