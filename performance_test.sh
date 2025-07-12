#!/bin/bash
# PDF Plumb Performance Testing Script
# Usage: ./performance_test.sh [small|medium|large|all]

set -e

# Test configuration
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RESULTS_DIR="performance_results_${TIMESTAMP}"
PROFILE_DIR="${RESULTS_DIR}/profiles"

# Test files
SMALL_FILE="data/h264_20pages.pdf"      # 690K, 20 pages
MEDIUM_FILE="data/h264_100pages.pdf"    # 1.8M, 100 pages  
LARGE_FILE="data/h264_310pages.pdf"     # 4.0M, 310 pages

# CLI commands to test
COMMANDS=("extract" "analyze")

# Create results directory
mkdir -p "$RESULTS_DIR"
mkdir -p "$PROFILE_DIR"

echo "=== PDF Plumb Performance Testing ==="
echo "Results will be saved to: $RESULTS_DIR"
echo "Timestamp: $TIMESTAMP"
echo ""

# Function to run single performance test
run_performance_test() {
    local size=$1
    local file=$2
    local basename=$(basename "$file" .pdf)
    
    echo "Testing $size file: $file"
    echo "File size: $(ls -lh "$file" | awk '{print $5}')"
    echo "----------------------------------------"
    
    for cmd in "${COMMANDS[@]}"; do
        # Determine the correct input file for each command
        if [ "$cmd" = "extract" ]; then
            input_file="$file"
        elif [ "$cmd" = "analyze" ]; then
            # analyze needs the lines.json file from extract
            input_file="output/${basename}_lines.json"
            
            # Check if the lines file exists
            if [ ! -f "$input_file" ]; then
                echo "❌ Cannot run analyze: lines file not found: $input_file"
                echo "❌ Skipping analyze command (requires extract to run first)"
                continue
            fi
        fi
        
        echo "Running: uv run pdf-plumb $cmd $input_file"
        
        # Basic timing with time command
        echo "=== Basic Timing Test ===" >> "$RESULTS_DIR/${size}_${cmd}_timing.log"
        if /usr/bin/time -v uv run pdf-plumb "$cmd" "$input_file" \
            >> "$RESULTS_DIR/${size}_${cmd}_timing.log" 2>&1; then
            cmd_success=true
        else
            echo "⚠️  Command failed" >> "$RESULTS_DIR/${size}_${cmd}_timing.log"
            echo "❌ CRITICAL: Command '$cmd' failed - stopping test (remaining commands would be invalid)"
            echo "📋 Check ${RESULTS_DIR}/${size}_${cmd}_timing.log for error details"
            exit 1
        fi
        
        # Run cProfile (command already succeeded if we reach here)
        echo "=== Python cProfile Analysis ===" >> "$RESULTS_DIR/${size}_${cmd}_profile.log"
        uv run python -m cProfile -o "$PROFILE_DIR/${size}_${cmd}.prof" \
            -m pdf_plumb.cli "$cmd" "$input_file" \
            >> "$RESULTS_DIR/${size}_${cmd}_profile.log" 2>&1
        
        # Generate human-readable profile report
        if [ -f "$PROFILE_DIR/${size}_${cmd}.prof" ]; then
            echo "Generating profile summary for ${size}_${cmd}..."
            {
                echo "=== TOP 20 FUNCTIONS BY CUMULATIVE TIME ==="
                uv run python -c "
import pstats
p = pstats.Stats('$PROFILE_DIR/${size}_${cmd}.prof')
p.sort_stats('cumulative').print_stats(20)
"
                echo ""
                echo "=== TOP 20 FUNCTIONS BY INTERNAL TIME ==="
                uv run python -c "
import pstats
p = pstats.Stats('$PROFILE_DIR/${size}_${cmd}.prof')
p.sort_stats('tottime').print_stats(20)
"
                echo ""
                echo "=== CALLERS FOR TOP 10 FUNCTIONS ==="
                uv run python -c "
import pstats
p = pstats.Stats('$PROFILE_DIR/${size}_${cmd}.prof')
p.sort_stats('cumulative').print_callers(10)
"
            } > "$RESULTS_DIR/${size}_${cmd}_profile_summary.txt" 2>&1
            
            if [ $? -eq 0 ]; then
                echo "Profile summary generated successfully"
            else
                echo "Profile summary generation failed for ${size}_${cmd}"
            fi
        else
            echo "Profile file not found: $PROFILE_DIR/${size}_${cmd}.prof"
        fi
        
        echo "✅ Completed: $cmd on $size file"
        echo ""
    done
    
    echo "✅ All tests completed for $size file"
    echo "=========================================="
    echo ""
}

# Function to run system info
collect_system_info() {
    echo "=== System Information ===" > "$RESULTS_DIR/system_info.txt"
    echo "Date: $(date)" >> "$RESULTS_DIR/system_info.txt"
    echo "Hostname: $(hostname)" >> "$RESULTS_DIR/system_info.txt"
    echo "OS: $(uname -a)" >> "$RESULTS_DIR/system_info.txt"
    echo "Python: $(python3 --version)" >> "$RESULTS_DIR/system_info.txt"
    echo "CPU Info:" >> "$RESULTS_DIR/system_info.txt"
    grep "model name\|cpu cores\|siblings" /proc/cpuinfo | head -6 >> "$RESULTS_DIR/system_info.txt"
    echo "Memory Info:" >> "$RESULTS_DIR/system_info.txt"
    free -h >> "$RESULTS_DIR/system_info.txt"
    echo "UV Version:" >> "$RESULTS_DIR/system_info.txt"
    uv --version >> "$RESULTS_DIR/system_info.txt" 2>&1 || echo "UV version not available"
    echo "PDF Plumb Version:" >> "$RESULTS_DIR/system_info.txt"
    uv run pdf-plumb --version >> "$RESULTS_DIR/system_info.txt" 2>&1 || echo "PDF Plumb version not available"
}

# Function to generate summary report
generate_summary() {
    echo "=== Performance Test Summary ===" > "$RESULTS_DIR/summary.txt"
    echo "Generated: $(date)" >> "$RESULTS_DIR/summary.txt"
    echo "" >> "$RESULTS_DIR/summary.txt"
    
    for size in small medium large; do
        # Check if any timing files exist for this size
        local has_results=false
        for cmd in "${COMMANDS[@]}"; do
            if [ -f "$RESULTS_DIR/${size}_${cmd}_timing.log" ]; then
                has_results=true
                break
            fi
        done
        
        if [ "$has_results" = true ]; then
            echo "=== $size FILE RESULTS ===" >> "$RESULTS_DIR/summary.txt"
            
            # Extract key metrics from timing logs
            for cmd in "${COMMANDS[@]}"; do
                if [ -f "$RESULTS_DIR/${size}_${cmd}_timing.log" ]; then
                    echo "--- $cmd command ---" >> "$RESULTS_DIR/summary.txt"
                    
                    # Extract elapsed time and memory usage
                    grep "Elapsed (wall clock) time" "$RESULTS_DIR/${size}_${cmd}_timing.log" >> "$RESULTS_DIR/summary.txt" 2>/dev/null || true
                    grep "Maximum resident set size" "$RESULTS_DIR/${size}_${cmd}_timing.log" >> "$RESULTS_DIR/summary.txt" 2>/dev/null || true
                    grep "User time" "$RESULTS_DIR/${size}_${cmd}_timing.log" >> "$RESULTS_DIR/summary.txt" 2>/dev/null || true
                    grep "System time" "$RESULTS_DIR/${size}_${cmd}_timing.log" >> "$RESULTS_DIR/summary.txt" 2>/dev/null || true
                    grep "CPU this job got" "$RESULTS_DIR/${size}_${cmd}_timing.log" >> "$RESULTS_DIR/summary.txt" 2>/dev/null || true
                    echo "" >> "$RESULTS_DIR/summary.txt"
                fi
            done
            echo "" >> "$RESULTS_DIR/summary.txt"
        fi
    done
    
    # Add profile summary if available
    echo "=== PROFILING SUMMARY ===" >> "$RESULTS_DIR/summary.txt"
    for size in small medium large; do
        if [ -f "$RESULTS_DIR/${size}_extract_profile_summary.txt" ]; then
            echo "--- $size file extract profiling ---" >> "$RESULTS_DIR/summary.txt"
            head -10 "$RESULTS_DIR/${size}_extract_profile_summary.txt" >> "$RESULTS_DIR/summary.txt" 2>/dev/null || true
            echo "" >> "$RESULTS_DIR/summary.txt"
        fi
    done
}

# Main script logic
case "${1:-help}" in
    "small")
        echo "Running SMALL file performance tests..."
        collect_system_info
        run_performance_test "small" "$SMALL_FILE"
        generate_summary
        ;;
    "medium")
        echo "Running MEDIUM file performance tests..."
        collect_system_info
        run_performance_test "medium" "$MEDIUM_FILE"
        generate_summary
        ;;
    "large")
        echo "Running LARGE file performance tests..."
        collect_system_info
        run_performance_test "large" "$LARGE_FILE"
        generate_summary
        ;;
    "all")
        echo "Running ALL performance tests..."
        collect_system_info
        run_performance_test "small" "$SMALL_FILE"
        run_performance_test "medium" "$MEDIUM_FILE"
        run_performance_test "large" "$LARGE_FILE"
        generate_summary
        ;;
    "help"|*)
        echo "Usage: $0 [small|medium|large|all]"
        echo ""
        echo "Test files:"
        echo "  small:  $SMALL_FILE ($(ls -lh "$SMALL_FILE" 2>/dev/null | awk '{print $5}' || echo 'not found'))"
        echo "  medium: $MEDIUM_FILE ($(ls -lh "$MEDIUM_FILE" 2>/dev/null | awk '{print $5}' || echo 'not found'))"
        echo "  large:  $LARGE_FILE ($(ls -lh "$LARGE_FILE" 2>/dev/null | awk '{print $5}' || echo 'not found'))"
        echo ""
        echo "Commands tested: extract, analyze"
        echo "Results saved to: performance_results_TIMESTAMP/"
        exit 0
        ;;
esac

echo "🎉 Performance testing completed!"
echo "📊 Results saved to: $RESULTS_DIR/"
echo ""
echo "Key files to review:"
echo "  - system_info.txt      - System specifications"
echo "  - summary.txt          - Quick metrics overview"
echo "  - *_timing.log         - Detailed timing and memory data"
echo "  - *_profile_summary.txt - Python function performance analysis"
echo "  - profiles/*.prof      - Raw cProfile data for further analysis"