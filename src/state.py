"""
State management for the BreakMyBot multi-agent system.
Defines the conversation state that flows through the graph.
"""

from typing import Annotated, TypedDict, List
from operator import add


class Message(TypedDict):
    """Individual message in the conversation."""
    role: str  # "target", "attacker", "evaluator"
    content: str
    turn: int


class ConversationState(TypedDict):
    """
    Shared state for all agents in the LangGraph.
    This represents the full context of the attack attempt.
    """
    # Configuration
    target_rules: str  # The chatbot's system instructions
    attack_strategy: str  # The attacker's persona and strategy
    difficulty: str  # "easy", "medium", or "hard"
    
    # Conversation history
    messages: Annotated[List[Message], add]  # Accumulated messages
    
    # Attack metrics
    current_turn: int  # Which turn we're on (0-indexed)
    max_turns: int  # Maximum number of turns before stopping
    
    # Evaluation results
    violations_found: Annotated[List[str], add]  # List of policy violations detected
    success: bool  # Whether the attack successfully broke the guardrails
    
    # Attack path tracking
    closed_paths: Annotated[List[str], add]  # Paths that have been explicitly closed
    completed_paths: Annotated[List[str], add]  # Paths that were completed (even if blocked)
    
    # Capability registry (updated by evaluator each turn)
    confirmed_capabilities: Annotated[List[str], add]  # What target said it CAN do
    denied_capabilities: Annotated[List[str], add]  # What target said it CANNOT do
    
    # Rubric-based evaluation
    evaluation_rubric: dict  # Rich evaluation metrics
    
    # Debug/logging
    last_evaluator_analysis: str  # The evaluator's latest judgment
