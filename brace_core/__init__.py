"""BRACE Stage 04: research-grade cohort intake and compatibility preflight."""
from .intake import parse_cohort, InputProblem
from .compatibility import evaluate_compatibility
__version__ = '0.4.0'
