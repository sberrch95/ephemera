"""Extractor interface and shared types.

An Extractor takes a parsed response and returns a list of Candidate
matches. Extractors don't touch the database directly - the memory
layer decides what to do with candidates.
"""

from dataclasses import dataclass


@dataclass
class Candidate:
    key: str
    value: str
    variable_type: str
