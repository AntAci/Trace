"""
Phase 2: Synergy and Conflict Engine

This phase compares two Phase 1 structured JSON outputs and identifies:
- Overlapping variables
- Potential synergies
- Potential conflicts
- In-memory graph representation
"""

from phase2.synergy_agent import SynergyAgent, analyze_papers

__all__ = ["SynergyAgent", "analyze_papers"]

