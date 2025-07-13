"""
Memory System Module

This module provides a singleton instance of the MemorySystem class
for handling vector-based memory storage and retrieval.
"""
from .memory import memory_system, save_memory, query_memory

# Export the memory system and its functions
__all__ = ['memory_system', 'save_memory', 'query_memory']
