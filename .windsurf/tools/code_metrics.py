#!/usr/bin/env python3
"""
Code metrics analyzer for the Video Converter project.
This script analyzes the codebase and generates metrics to establish a baseline
before refactoring.
"""

import os
import sys
import ast
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

# Configuration
PROJECT_ROOT = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PYTHON_DIRS = ["app"]
EXCLUDE_DIRS = ["__pycache__", ".git", ".windsurf", "venv", ".venv"]
OUTPUT_FILE = PROJECT_ROOT / ".windsurf" / "metrics" / "baseline_metrics.json"

# Ensure metrics directory exists
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)


class FunctionVisitor(ast.NodeVisitor):
    """AST visitor to collect function metrics."""
    
    def __init__(self):
        self.functions = []
        self.current_class = None
    
    def visit_ClassDef(self, node):
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class
    
    def visit_FunctionDef(self, node):
        function_info = {
            "name": node.name,
            "class": self.current_class,
            "lineno": node.lineno,
            "end_lineno": getattr(node, "end_lineno", None),
            "parameters": len(node.args.args),
            "defaults": len(node.args.defaults),
            "complexity": self._calculate_complexity(node),
            "docstring": ast.get_docstring(node) is not None,
            "docstring_lines": len(ast.get_docstring(node).split("\n")) if ast.get_docstring(node) else 0,
        }
        self.functions.append(function_info)
        self.generic_visit(node)
    
    def _calculate_complexity(self, node):
        """Calculate cyclomatic complexity of a function."""
        visitor = ComplexityVisitor()
        visitor.visit(node)
        return visitor.complexity


class ComplexityVisitor(ast.NodeVisitor):
    """AST visitor to calculate cyclomatic complexity."""
    
    def __init__(self):
        self.complexity = 1  # Start with 1 for the function itself
    
    def visit_If(self, node):
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_For(self, node):
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_While(self, node):
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_BoolOp(self, node):
        # BoolOp contains 'op' (And/Or) and 'values'
        self.complexity += len(node.values) - 1
        self.generic_visit(node)
    
    def visit_Try(self, node):
        self.complexity += len(node.handlers)
        self.generic_visit(node)


def count_lines(file_path: Path) -> Dict[str, int]:
    """Count different types of lines in a file."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    lines = content.split("\n")
    code_lines = 0
    comment_lines = 0
    blank_lines = 0
    docstring_lines = 0
    
    # Simple detection of docstrings and comments
    in_docstring = False
    docstring_delimiter = None
    
    for line in lines:
        stripped = line.strip()
        
        # Check for docstring delimiters
        if not in_docstring and (stripped.startswith('"""') or stripped.startswith("'''")):
            in_docstring = True
            docstring_delimiter = stripped[0:3]
            docstring_lines += 1
            if stripped.endswith(docstring_delimiter) and len(stripped) > 3:
                in_docstring = False
            continue
        
        if in_docstring:
            docstring_lines += 1
            if stripped.endswith(docstring_delimiter):
                in_docstring = False
            continue
        
        if not stripped:
            blank_lines += 1
        elif stripped.startswith("#"):
            comment_lines += 1
        else:
            code_lines += 1
    
    return {
        "total_lines": len(lines),
        "code_lines": code_lines,
        "comment_lines": comment_lines,
        "blank_lines": blank_lines,
        "docstring_lines": docstring_lines,
    }


def analyze_python_file(file_path: Path) -> Dict[str, Any]:
    """Analyze a Python file and return metrics."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Parse the AST
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        return {
            "error": f"Syntax error: {str(e)}",
            "lines": count_lines(file_path),
            "functions": [],
        }
    
    # Visit the AST to collect function metrics
    visitor = FunctionVisitor()
    visitor.visit(tree)
    
    return {
        "lines": count_lines(file_path),
        "functions": visitor.functions,
        "imports": count_imports(content),
        "classes": len([node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]),
    }


def count_imports(content: str) -> Dict[str, int]:
    """Count import statements in Python code."""
    import_lines = re.findall(r"^\s*(import|from)\s+.*$", content, re.MULTILINE)
    import_count = len(import_lines)
    
    # Count wildcard imports
    wildcard_imports = re.findall(r"^\s*from\s+.*\s+import\s+\*\s*$", content, re.MULTILINE)
    
    return {
        "total": import_count,
        "wildcard": len(wildcard_imports),
    }


def collect_metrics() -> Dict[str, Any]:
    """Collect metrics for the entire project."""
    metrics = {
        "files": {},
        "summary": {
            "total_files": 0,
            "total_lines": 0,
            "total_code_lines": 0,
            "total_comment_lines": 0,
            "total_blank_lines": 0,
            "total_docstring_lines": 0,
            "total_functions": 0,
            "total_classes": 0,
            "avg_function_length": 0,
            "avg_parameters_per_function": 0,
            "avg_complexity": 0,
            "max_complexity": 0,
            "functions_with_high_complexity": 0,  # Complexity > 10
            "functions_with_many_parameters": 0,  # Parameters > 5
        },
    }
    
    all_functions = []
    
    # Process Python files
    for directory in PYTHON_DIRS:
        dir_path = PROJECT_ROOT / directory
        for root, dirs, files in os.walk(dir_path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            
            for file in files:
                if file.endswith(".py"):
                    file_path = Path(os.path.join(root, file))
                    rel_path = file_path.relative_to(PROJECT_ROOT)
                    
                    # Analyze the file
                    file_metrics = analyze_python_file(file_path)
                    metrics["files"][str(rel_path)] = file_metrics
                    
                    # Update summary metrics
                    metrics["summary"]["total_files"] += 1
                    metrics["summary"]["total_lines"] += file_metrics["lines"]["total_lines"]
                    metrics["summary"]["total_code_lines"] += file_metrics["lines"]["code_lines"]
                    metrics["summary"]["total_comment_lines"] += file_metrics["lines"]["comment_lines"]
                    metrics["summary"]["total_blank_lines"] += file_metrics["lines"]["blank_lines"]
                    metrics["summary"]["total_docstring_lines"] += file_metrics["lines"]["docstring_lines"]
                    metrics["summary"]["total_functions"] += len(file_metrics["functions"])
                    metrics["summary"]["total_classes"] += file_metrics["classes"]
                    
                    # Collect all functions for calculating averages
                    all_functions.extend(file_metrics["functions"])
    
    # Calculate function-related metrics
    if all_functions:
        # Average function length
        function_lengths = []
        for func in all_functions:
            if func["end_lineno"] and func["lineno"]:
                function_lengths.append(func["end_lineno"] - func["lineno"] + 1)
        
        if function_lengths:
            metrics["summary"]["avg_function_length"] = sum(function_lengths) / len(function_lengths)
        
        # Average parameters per function
        param_counts = [func["parameters"] for func in all_functions]
        metrics["summary"]["avg_parameters_per_function"] = sum(param_counts) / len(all_functions)
        
        # Complexity metrics
        complexities = [func["complexity"] for func in all_functions]
        metrics["summary"]["avg_complexity"] = sum(complexities) / len(all_functions)
        metrics["summary"]["max_complexity"] = max(complexities) if complexities else 0
        metrics["summary"]["functions_with_high_complexity"] = sum(1 for c in complexities if c > 10)
        metrics["summary"]["functions_with_many_parameters"] = sum(1 for p in param_counts if p > 5)
    
    return metrics


def main():
    """Main function to run the metrics collection."""
    print(f"Analyzing codebase at {PROJECT_ROOT}...")
    metrics = collect_metrics()
    
    # Save metrics to file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    
    # Print summary
    summary = metrics["summary"]
    print("\nCodebase Metrics Summary:")
    print(f"Total Python files: {summary['total_files']}")
    print(f"Total lines: {summary['total_lines']}")
    print(f"  - Code lines: {summary['total_code_lines']} ({summary['total_code_lines']/summary['total_lines']*100:.1f}%)")
    print(f"  - Comment lines: {summary['total_comment_lines']} ({summary['total_comment_lines']/summary['total_lines']*100:.1f}%)")
    print(f"  - Docstring lines: {summary['total_docstring_lines']} ({summary['total_docstring_lines']/summary['total_lines']*100:.1f}%)")
    print(f"  - Blank lines: {summary['total_blank_lines']} ({summary['total_blank_lines']/summary['total_lines']*100:.1f}%)")
    print(f"Total functions: {summary['total_functions']}")
    print(f"Total classes: {summary['total_classes']}")
    print(f"Average function length: {summary['avg_function_length']:.1f} lines")
    print(f"Average parameters per function: {summary['avg_parameters_per_function']:.1f}")
    print(f"Average cyclomatic complexity: {summary['avg_complexity']:.1f}")
    print(f"Maximum cyclomatic complexity: {summary['max_complexity']}")
    print(f"Functions with high complexity (>10): {summary['functions_with_high_complexity']}")
    print(f"Functions with many parameters (>5): {summary['functions_with_many_parameters']}")
    print(f"\nDetailed metrics saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
