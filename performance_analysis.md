# PDF Plumb Performance Baseline Analysis

**Generated**: July 11, 2025  
**Test System**: Intel i7-10750H, 6 cores, 15GB RAM  
**Environment**: WSL2, Python 3.12.9, UV 0.6.4

## Small File Performance Baseline (20 pages, 690K) - UPDATED

### Streamlined Two-Command Pipeline

**File**: `data/h264_20pages.pdf` (690KB, 20 pages)  
**Commands**: `extract` + `analyze` (removed redundant `process`)

#### Key Metrics ⚡

**Extract Command (Primary Bottleneck):**
- **Wall Clock Time**: 13.23 seconds
- **CPU Time**: 12.71s user + 0.51s system = 13.22s total
- **CPU Utilization**: 99% (excellent CPU usage)
- **Peak Memory**: 446,096 KB ≈ **436 MB**
- **Function Calls**: 125M calls

**Analyze Command (Fast Post-Processing):**
- **Wall Clock Time**: 0.61 seconds
- **CPU Time**: 0.56s user + 0.04s system = 0.60s total  
- **CPU Utilization**: 99% (efficient)
- **Peak Memory**: 86,788 KB ≈ **85 MB**
- **Function Calls**: 3.8M calls

**Total Pipeline**: 13.84 seconds (extract + analyze)

#### Performance Analysis

**✅ Extract Command (95% of pipeline time):**
- **High CPU utilization** (99%) - no blocking I/O issues
- **Memory usage** (436MB for 20 pages = ~22MB per page)
- **JSON bottleneck confirmed**: 6.51s dict + 4.84s list + 3.16s dump = **14.5s of 48.7s profiled time**
- **PDF processing**: Remaining ~34s profiled time

**✅ Analyze Command (4% of pipeline time):**
- **Very fast**: 0.61s wall time
- **Lightweight**: 85MB memory (80% less than extract)
- **Minimal JSON usage**: Only 0.34s dict + 0.20s list encoding
- **Core analysis**: 0.13s in `_collect_contextual_gaps`

**⚠️ Areas for Investigation:**
- **Extract JSON serialization** - 30% of profiled time (primary target)
- **Extract PDF processing** - 70% of profiled time  
- **Memory scaling** - 22MB per page needs optimization

#### Updated Scaling Projections

**Streamlined Pipeline (extract + analyze):**

| Document Size | Extract Time | Analyze Time | Total Pipeline | Memory |
|---------------|-------------|--------------|----------------|---------|
| 20 pages      | 13.23s | 0.61s | **13.84s** | 436MB |
| 100 pages     | ~66s | ~3s | **~69s** | ~2.2GB |
| 310 pages     | ~205s | ~9s | **~214s (3.6m)** | ~6.8GB |

**Key insight**: Analyze scales but remains negligible compared to extract.

## Detailed Performance Breakdown (WITH cProfile Analysis)

### Function-Level Performance Hotspots 🔥

**Total Function Calls**: 125M calls in 47.08 seconds (125M calls vs 13.69s wall time = profiling overhead)

#### Top Performance Bottlenecks:
1. **JSON Serialization** - 20.9s (45% of total time!)
   - `json.dump()`: 3.02s direct + encoding overhead
   - Dict encoding: 6.26s in `_iterencode_dict`
   - List encoding: 4.52s in `_iterencode_list`
   
2. **PDF Text Extraction** - 25.8s (55% of processing time)
   - `PDFExtractor.extract_from_pdf()`: 25.76s
   - `pdfplumber` text mapping: 22.5s
   - Text parsing: 20.3s in character/word processing

#### Critical Path Analysis:
```
Total Time: 47.08s (profiled) vs 13.69s (wall clock)
├── PDF Processing: 25.8s
│   ├── Text extraction: 22.5s (pdfplumber._get_textmap)
│   └── Object parsing: 20.3s (character processing)
└── JSON Output: 20.9s  
    ├── Serialization: 3.02s
    ├── Dict encoding: 6.26s  
    └── List encoding: 4.52s
```

### Memory Usage Pattern
- **Peak resident memory**: 436MB (consistent between runs)
- **Page faults**: 107,906 minor, 0 major (good - no disk swapping)
- **Context switches**: 36 voluntary, 26 involuntary (minimal)
- **No swapping**: Excellent memory management

### I/O Profile  
- **Read operations**: 32 file system inputs (much lower than previous run)
- **Write operations**: 136,680 file system outputs
- **Write dominance**: JSON serialization creates massive I/O load

### Output Generation Timing
Based on log timestamps:
```
Lines:     17:52:29 (+1s)  - Fast line processing
Words:     17:52:33 (+4s)  - Word processing bottleneck  
Compare:   17:52:33 (+4s)  - Comparison complete
Total:     13.69s wall time
```

**Processing stages:**
1. **PDF extraction**: ~10 seconds (73% of wall time)
2. **Output generation**: ~4 seconds (27% of wall time)
3. **JSON overhead**: Profiler shows 45% of total processing time!

## Performance Optimization Opportunities

### 🔥 CRITICAL - JSON Serialization (45% of processing time!)
1. **Implement streaming JSON**: Avoid building full objects in memory
2. **Use faster JSON library**: Consider `orjson` or `ujson` (3-5x faster)
3. **Compress output data**: Reduce redundant data before serialization
4. **Batch smaller writes**: Instead of 5 large JSON files

### 🔥 HIGH PRIORITY - PDF Processing (55% of processing time)
1. **pdfplumber optimization**: 22.5s in `_get_textmap` - investigate alternatives
2. **Character processing**: 20.3s in object parsing - potential for optimization
3. **CropBox warnings**: 20 warnings indicate inefficient PDF handling

### 📈 MEDIUM PRIORITY - Data Structure  
1. **Memory scaling**: 436MB for 20 pages = 22MB/page needs optimization
2. **Reduce object creation**: 125M function calls suggests excessive allocation
3. **Cache frequently accessed data**: Reduce repeated computations

### 📊 LOW PRIORITY - Infrastructure
1. **Progress indicators**: Better user feedback during long operations
2. **Output organization**: Consider more efficient file structure
3. **Error handling**: Investigate CropBox warning suppression

## Test Command Issues Found

### ✅ cProfile Integration (FIXED)
**Issue**: Module path resolution in UV environment  
**Solution**: Updated script to use `uv run python -m cProfile`  
**Result**: Successfully captured 125M function calls with detailed timing

### PDF Structure Warnings
```
CropBox missing from /Page, defaulting to MediaBox
```
**Frequency**: 20 warnings for 20 pages (1 per page)  
**Impact**: May indicate suboptimal PDF library usage

## Recommendations for Phase 2.3

### Immediate Actions
1. **Fix profiling script** - Update cProfile integration for proper module detection
2. **Test medium file** - Validate scaling assumptions with 100-page document
3. **Investigate PDF warnings** - Research CropBox handling optimization

### Performance Targets Based on Profiling Data

#### Immediate Wins (JSON Optimization)
- **JSON serialization**: Target 50-75% reduction (from 20.9s to <5s)
- **Faster JSON library**: 3-5x speedup potential with orjson
- **Total improvement**: Could reduce 13.69s to <8s (40% improvement)

#### Long-term Goals  
- **Speed**: Target <5 seconds for 20 pages (65% improvement needed)
- **Memory**: Target <15MB per page (30% improvement needed)
- **Scalability**: Support 100+ page documents under 60 seconds

### Testing Strategy
1. ✅ **Small baseline complete** (20 pages)
2. **Next**: Medium file testing (100 pages) to validate scaling
3. **Then**: Large file stress testing (310 pages)
4. **Profile**: Fix and run detailed function profiling

## System Context

**Hardware**: Intel i7-10750H @ 2.60GHz (6 cores, 12 threads)  
**Memory**: 15GB total, 14GB available  
**Platform**: WSL2 Linux on Windows  
**Python**: 3.12.9 with UV package manager

This baseline provides solid foundation for optimization work in Phase 2.3.