"""
Autonomous Generative Trading Agent (AGT)
Core package for predictive market consciousness.
"""
__version__ = "0.1.0"
__author__ = "Evolution Ecosystem"

from .main import AGTAgent
from .state.firebase_manager import FirebaseStateManager

__all__ = ["AGTAgent", "FirebaseStateManager"]