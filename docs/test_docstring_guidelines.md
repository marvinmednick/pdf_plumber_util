# Test Docstring Guidelines

## Purpose

Test docstrings should explain **what is tested and how it's tested** so that tests can be reviewed and understood without reading the implementation. These guidelines support both manual code review and automated documentation generation with tools like mkdocstrings.

## Five-Section Structure

Use this structure for comprehensive test documentation:

```python
def test_example_function(self, fixtures):
    """Test the method_name() ability to [primary capability being tested].
    
    Test setup:
    - [Describe the test scenarios created]
    - [Explain key conditions needed for validation]
    - [Note any data preparation that matters for understanding]

    What it verifies:
    - [List what capabilities/behaviors are validated]
    - [Describe expected outcomes being checked]
    - [Note any return value or state validations]

    Test limitation:
    - [Honestly describe what this test doesn't cover]
    - [Note any weak assertions or always-true conditions]
    - [Identify gaps in validation logic]

    Key insight: [One-sentence summary of what this test actually proves]
    """
```

## Content Guidelines

### Focus on Test Goals, Not Implementation Details

**Ask these questions:**
- What is this test trying to prove works correctly?
- What scenarios/conditions are needed to prove that?
- What would break if this capability failed?
- What important scenarios are NOT tested here?

**✅ Good Examples:**
- "Verifies that gaps are correctly classified into Line/Paragraph/Section categories"
- "Tests that the method can handle lines with matching font sizes"
- "Ensures the method returns valid structure even when input data varies"
- "Validates core classification logic works for standard spacing scenarios"

**❌ Avoid These:**
- "Tests three specific gap values: 6.0pt, 12.0pt, and 18.0pt" (unless the specific values matter)
- "Uses sample data with various font sizes" (vague, doesn't explain why)
- "Validates proper functionality" (meaningless)
- "Ensures correct behavior" (doesn't say what behavior)

### Use Specific Details When They Matter for Understanding

Include concrete details **only when they help explain the test's logic or goals**:

**✅ When specifics help:**
- "Uses 6.0pt gap to test Line classification, 12.0pt for Paragraph, 18.0pt for Section" (shows boundary testing)
- "Creates consecutive lines with same font size (12pt) to trigger gap collection logic" (explains why this scenario matters)
- "Tests with 14pt header and 12pt body text to ensure different contexts are handled" (shows multi-context validation)

**❌ When specifics don't add value:**
- "Uses fixture data containing 2 lines" (count doesn't matter for understanding)
- "Manually adds a third line with line_number: 3" (implementation detail, not test logic)
- "Tests gap values of 6.0pt, 12.0pt, and 18.0pt" (without explaining why these values matter)

### Be Honest About What the Test Actually Validates

**Identify weak validation:**
- "Only verifies basic structure (isinstance(gaps, dict))"
- "Assertion len(gaps) >= 0 is essentially always true (can't fail)"
- "Uses mocked data, doesn't test actual PDF processing"

**Acknowledge coverage gaps:**
- "Only tests one font size context"
- "Doesn't test boundary conditions or invalid inputs"
- "Doesn't verify the actual gap values or font size groupings"

### Focus on Test Scenarios, Not Algorithm Descriptions

**✅ Good - explains test scenarios:**
- "Creates scenario where consecutive lines have matching font sizes"
- "Tests boundary conditions between Line and Paragraph classifications"
- "Simulates error condition with nonexistent file path"

**❌ Avoid - describes how algorithm works:**
- "The method groups gaps by font size and applies contextual rules"
- "Classification uses thresholds to determine spacing categories"
- "The algorithm iterates through lines and calculates gaps"

## Complete Examples

### Example 1: Classification Logic Testing

```python
def test_classify_gap_contextual(self, sample_spacing_rules):
    """Test the _classify_gap_contextual() method's ability to categorize gaps based on font size context.
    
    Test setup:
    - Uses predefined spacing rules for 12pt font context
    - Tests boundary conditions for Line/Paragraph/Section classification
    - Each test targets a different classification category

    What it verifies:
    - Small gaps (6.0pt) correctly classified as "Line" spacing
    - Medium gaps (12.0pt) correctly classified as "Paragraph" spacing
    - Large gaps (18.0pt) correctly classified as "Section" spacing
    - Method properly applies contextual rules for font size

    Test limitation:
    - Only tests one font size context (12pt)
    - Doesn't test edge cases or invalid inputs
    - Assumes spacing rules fixture is correctly structured

    Key insight: Validates that the core gap classification logic works for standard spacing scenarios.
    """
```

### Example 2: Data Organization Testing

```python
def test_collect_contextual_gaps(self, sample_lines_data):
    """Test the _collect_contextual_gaps() method's ability to organize text line gaps by font size context.
    
    Test setup:
    - Creates scenario with lines of different font sizes (14pt header, 12pt body)
    - Adds additional 12pt line to ensure consecutive same-size lines exist
    - This triggers the gap collection logic for matching font contexts

    What it verifies:
    - Method returns dictionary structure (gaps organized by font size)
    - Method can handle lines with matching predominant font sizes
    - Method produces valid output structure regardless of input variations

    Test limitation:
    - Only verifies basic structure (isinstance(gaps, dict))
    - Assertion len(gaps) >= 0 is essentially always true (can't fail)
    - Doesn't validate actual gap values or grouping logic

    Key insight: Ensures the gap collection mechanism works but doesn't validate the specific grouping logic.
    """
```

### Example 3: Error Handling Testing

```python
def test_pdf_not_found_error(self):
    """Test PDFNotFoundError exception creation with automatic suggestion generation.
    
    Test setup:
    - Creates error condition with nonexistent file path
    - Tests automatic error message and suggestion generation
    - No external dependencies or complex setup required

    What it verifies:
    - Error message contains appropriate "not found" text
    - Automatic suggestion provides helpful user guidance
    - Context dictionary preserves the problematic file path
    - Exception properly inherits from base PDFPlumbError class

    Test limitation:
    - Only tests error object creation, not actual file system interaction
    - Doesn't validate suggestion quality or usefulness
    - No testing of file path validation logic

    Key insight: Ensures error objects provide helpful context and guidance for users encountering file issues.
    """
```

### Example 4: Simple Function Testing

```python
def test_basic_property_access(self):
    """Test that config.output_dir returns the configured output directory path."""

def test_exception_inheritance(self):
    """Test that all custom exceptions inherit from PDFPlumbError base class."""
```

## When to Use Each Format

### Use Full Five-Section Format For:
- Tests with complex logic or multiple validation points
- Tests that create specific scenarios to validate capabilities
- Tests with known limitations or coverage gaps
- Tests where understanding the setup helps explain what's being validated

### Use Simplified Format For:
- Simple property access or basic validation
- Obvious functionality with single assertion
- Tests where the purpose is immediately clear from the test name

## Integration with mkdocstrings

These docstrings will generate useful documentation showing:
- **What capabilities are tested** - Clear overview of validation coverage
- **How tests validate behavior** - Understanding of test approach
- **Test coverage gaps** - Honest assessment of limitations
- **Test scenario explanations** - Context for why tests are structured as they are

## Benefits

This approach ensures:
- **Tests clearly explain their validation goals**
- **Test coverage gaps are visible and can be addressed**
- **Generated documentation focuses on capabilities, not implementation**
- **Test intent is clear to future maintainers**
- **Specific details are included only when they aid understanding**

Following these guidelines creates tests that serve as both validation and documentation, supporting both manual review and automated documentation generation while focusing on what really matters: what the test proves works correctly.