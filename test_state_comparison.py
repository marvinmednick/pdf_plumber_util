#!/usr/bin/env python3
"""
Test comparison between state machine LLM analysis and direct LLM analyzer.

This script compares the results of:
1. Direct LLMDocumentAnalyzer.analyze_headers_footers()
2. HeaderFooterAnalysisState through workflow orchestrator

Both should produce equivalent results.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from pdf_plumb.core.llm_analyzer import LLMDocumentAnalyzer
from pdf_plumb.workflow.orchestrator import AnalysisOrchestrator
from pdf_plumb.workflow.states.header_footer import HeaderFooterAnalysisState


def load_test_data(json_file: Path) -> dict:
    """Load JSON test data."""
    print(f"📁 Loading test data from: {json_file}")
    
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    # Handle different JSON structures
    if 'pages' in data:
        pages_data = data['pages']
    elif isinstance(data, list):
        # Assume it's a list of pages
        pages_data = data
    else:
        raise ValueError(f"Unexpected JSON structure in {json_file}")
    
    print(f"📄 Loaded {len(pages_data)} pages")
    return pages_data


def test_direct_analyzer(pages_data: list, output_dir: Path) -> dict:
    """Test direct LLMDocumentAnalyzer."""
    print("\n🔍 Testing Direct LLMDocumentAnalyzer...")
    
    analyzer = LLMDocumentAnalyzer(provider_name="azure")
    
    # Check if configured
    if not analyzer.provider.is_configured():
        print("⚠️  LLM provider not configured - skipping actual analysis")
        return {"error": "LLM provider not configured"}
    
    try:
        result = analyzer.analyze_headers_footers(
            document_data=pages_data,
            save_results=True,
            output_dir=output_dir / "direct"
        )
        
        print(f"✅ Direct analysis completed")
        print(f"   📊 Pages analyzed: {len(result.per_page_analysis)}")
        print(f"   📈 Header confidence: {result.header_confidence.value}")
        print(f"   📉 Footer confidence: {result.footer_confidence.value}")
        print(f"   🏷️  Section headings found: {len(result.get_all_section_headings())}")
        print(f"   📋 Figure titles found: {len(result.get_all_figure_titles())}")
        print(f"   📊 Table titles found: {len(result.get_all_table_titles())}")
        
        return {
            "success": True,
            "pages_analyzed": len(result.per_page_analysis),
            "header_confidence": result.header_confidence.value,
            "footer_confidence": result.footer_confidence.value,
            "section_headings": len(result.get_all_section_headings()),
            "figure_titles": len(result.get_all_figure_titles()),
            "table_titles": len(result.get_all_table_titles()),
            "insights_count": len(result.insights),
            "sampling_summary": result.sampling_summary,
            "content_boundaries": result.get_content_boundaries(),
            "raw_result": result
        }
        
    except Exception as e:
        print(f"❌ Direct analysis failed: {e}")
        return {"error": str(e)}


def test_state_machine(pages_data: list, output_dir: Path) -> dict:
    """Test HeaderFooterAnalysisState through orchestrator."""
    print("\n🔧 Testing State Machine Analysis...")
    
    try:
        # Create orchestrator
        orchestrator = AnalysisOrchestrator(validate_on_init=True)
        
        # Prepare context
        context = {
            'document_data': pages_data,
            'save_results': True,
            'output_dir': str(output_dir / "state"),
        }
        
        # Run workflow starting with header_footer_analysis state
        result = orchestrator.run_workflow(
            document_data=pages_data,
            initial_state='header_footer_analysis',
            save_context=True,
            output_dir=output_dir / "state"
        )
        
        print(f"✅ State machine analysis completed")
        
        # Extract results from state workflow
        state_result = result.get('header_footer_analysis', {})
        results_data = state_result.get('results', {})
        metadata = state_result.get('metadata', {})
        knowledge = state_result.get('knowledge', {})
        
        print(f"   📊 Pages analyzed: {metadata.get('pages_analyzed', 0)}")
        print(f"   📈 Header confidence: {metadata.get('confidence', {}).get('header', 'Unknown')}")
        print(f"   📉 Footer confidence: {metadata.get('confidence', {}).get('footer', 'Unknown')}")
        print(f"   🏷️  Section headings found: {knowledge.get('section_headings_found', 0)}")
        print(f"   📋 Figure titles found: {knowledge.get('figure_titles_found', 0)}")
        print(f"   📊 Table titles found: {knowledge.get('table_titles_found', 0)}")
        
        return {
            "success": True,
            "pages_analyzed": metadata.get('pages_analyzed', 0),
            "header_confidence": metadata.get('confidence', {}).get('header'),
            "footer_confidence": metadata.get('confidence', {}).get('footer'),
            "section_headings": knowledge.get('section_headings_found', 0),
            "figure_titles": knowledge.get('figure_titles_found', 0),
            "table_titles": knowledge.get('table_titles_found', 0),
            "insights_count": len(results_data.get('insights', [])),
            "sampling_summary": results_data.get('sampling_summary'),
            "content_boundaries": knowledge.get('content_boundaries'),
            "raw_result": state_result.get('raw_result'),
            "workflow_result": result
        }
        
    except Exception as e:
        print(f"❌ State machine analysis failed: {e}")
        return {"error": str(e)}


def compare_results(direct_result: dict, state_result: dict) -> None:
    """Compare results from both approaches."""
    print("\n📊 COMPARISON RESULTS")
    print("=" * 50)
    
    if "error" in direct_result or "error" in state_result:
        print("❌ Cannot compare - one or both analyses failed")
        if "error" in direct_result:
            print(f"   Direct error: {direct_result['error']}")
        if "error" in state_result:
            print(f"   State error: {state_result['error']}")
        return
    
    # Compare key metrics
    metrics = [
        ("Pages Analyzed", "pages_analyzed"),
        ("Header Confidence", "header_confidence"), 
        ("Footer Confidence", "footer_confidence"),
        ("Section Headings", "section_headings"),
        ("Figure Titles", "figure_titles"),
        ("Table Titles", "table_titles"),
        ("Insights Count", "insights_count")
    ]
    
    print("Metric                | Direct    | State     | Match")
    print("-" * 50)
    
    all_match = True
    for name, key in metrics:
        direct_val = direct_result.get(key, "N/A")
        state_val = state_result.get(key, "N/A")
        match = "✅" if direct_val == state_val else "❌"
        
        if direct_val != state_val:
            all_match = False
            
        print(f"{name:<20} | {str(direct_val):<8} | {str(state_val):<8} | {match}")
    
    print("-" * 50)
    
    if all_match:
        print("🎉 ALL METRICS MATCH! State machine produces equivalent results.")
    else:
        print("⚠️  Some metrics differ - investigation needed.")
    
    # Compare sampling summaries
    direct_sampling = direct_result.get('sampling_summary', {})
    state_sampling = state_result.get('sampling_summary', {})
    
    if direct_sampling and state_sampling:
        print(f"\n📋 Sampling Comparison:")
        print(f"   Direct groups: {direct_sampling.get('groups', [])}")
        print(f"   State groups:  {state_sampling.get('groups', [])}")
        print(f"   Match: {'✅' if direct_sampling == state_sampling else '❌'}")


def main():
    """Main test function."""
    print("🧪 LLM Analysis: State vs Direct Comparison Test")
    print("=" * 60)
    
    # Setup
    output_dir = Path("output/comparison_test")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load test data - use h264_100pages since it has enough pages
    json_file = Path("output/h264_100pages_blocks.json")
    
    if not json_file.exists():
        print(f"❌ Test data not found: {json_file}")
        print("Available files:")
        for f in Path("output").glob("*.json"):
            print(f"   {f}")
        return
    
    try:
        pages_data = load_test_data(json_file)
        
        # Run tests
        direct_result = test_direct_analyzer(pages_data, output_dir)
        state_result = test_state_machine(pages_data, output_dir)
        
        # Compare results
        compare_results(direct_result, state_result)
        
        # Save comparison report
        report = {
            "timestamp": datetime.now().isoformat(),
            "test_data": str(json_file),
            "direct_result": direct_result,
            "state_result": state_result
        }
        
        report_file = output_dir / "comparison_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📄 Full comparison report saved to: {report_file}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()