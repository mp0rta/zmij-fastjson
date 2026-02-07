#!/usr/bin/env python3
"""
Convert pyperf JSON results to markdown report.

Usage:
    python tools/report_pyperf.py bench/results/
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any


def load_pyperf_result(filepath: Path) -> Dict[str, Any]:
    """Load a pyperf JSON result file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def format_benchmark(bench: Dict[str, Any]) -> str:
    """Format a single benchmark result."""
    name = bench.get('metadata', {}).get('name', 'unknown')
    runs = bench.get('runs', [])
    
    if not runs:
        return f"- **{name}**: No runs recorded"
    
    # Collect values from runs (skip calibration runs which may not have values)
    values: List[float] = []
    for run in runs:
        values.extend(run.get('values', []))
    if not values:
        return f"- **{name}**: No values recorded"
    
    # Calculate statistics
    mean = sum(values) / len(values)
    min_val = min(values)
    max_val = max(values)
    
    return (
        f"- **{name}**: "
        f"mean={mean:.6f}s, "
        f"min={min_val:.6f}s, "
        f"max={max_val:.6f}s, "
        f"n={len(values)}"
    )


def generate_report(results_dir: Path) -> str:
    """Generate markdown report from all pyperf results."""
    lines = [
        "# Benchmark Results",
        "",
        f"Generated from: `{results_dir}`",
        "",
    ]
    
    # Find all JSON files
    json_files = sorted(results_dir.glob('*.json'))
    
    if not json_files:
        lines.append("No benchmark results found.")
        return '\n'.join(lines)
    
    for json_file in json_files:
        lines.append(f"## {json_file.name}")
        lines.append("")
        
        try:
            data = load_pyperf_result(json_file)
            benchmarks = data.get('benchmarks', [])
            
            if not benchmarks:
                lines.append("No benchmarks found in this file.")
            else:
                for bench in benchmarks:
                    lines.append(format_benchmark(bench))
            
        except Exception as e:
            lines.append(f"Error loading file: {e}")
        
        lines.append("")
    
    return '\n'.join(lines)


def main():
    if len(sys.argv) < 2:
        results_dir = Path('bench/results')
    else:
        results_dir = Path(sys.argv[1])
    
    if not results_dir.exists():
        print(f"Error: Directory not found: {results_dir}", file=sys.stderr)
        sys.exit(1)
    
    report = generate_report(results_dir)
    print(report)


if __name__ == '__main__':
    main()
