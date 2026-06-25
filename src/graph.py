"""
LangGraph definition for BreakMyBot.
Orchestrates the multi-agent conversation loop.
"""

from langgraph.graph import StateGraph
from src.state import ConversationState
from src.nodes import TargetNode, AttackerNode, EvaluatorNode
from typing import Literal


def create_breakmybot_graph(max_turns: int = 5):
    """
    Create the BreakMyBot attack graph.
    
    Flow:
    START -> Attacker -> Target -> Evaluator -> (Loop or END)
    
    Args:
        max_turns: Maximum conversation turns before stopping
    
    Returns:
        Compiled LangGraph for execution
    """
    
    # Initialize nodes
    attacker = AttackerNode()
    target = TargetNode()
    evaluator = EvaluatorNode()
    
    # Create graph
    graph = StateGraph(ConversationState)
    
    # Add nodes
    graph.add_node("attacker", attacker)
    graph.add_node("target", target)
    graph.add_node("evaluator", evaluator)
    
    # Define routing logic
    def should_continue(state: ConversationState) -> str:
        """Determine if we should continue the loop or exit."""
        # Exit if success found
        if state["success"]:
            return "__end__"
        # Exit if max turns reached
        if state["current_turn"] >= state["max_turns"]:
            return "__end__"
        # Otherwise, continue attacking
        return "attacker"
    
    # Set entry point
    graph.set_entry_point("attacker")

    # Define edges
    graph.add_edge("attacker", "target")
    graph.add_edge("target", "evaluator")

    # Conditional edge based on evaluation — increment turn then loop or end
    graph.add_conditional_edges(
        "evaluator",
        should_continue,
        {
            "attacker": "attacker",
            "__end__": "__end__"
        }
    )

    # Compile the graph
    compiled_graph = graph.compile()
    
    return compiled_graph


def run_attack(
    target_rules: str,
    attack_strategy: str,
    max_turns: int = 5,
    difficulty: str = "medium",
    verbose: bool = True
) -> dict:
    """
    Execute a single attack attempt against a target chatbot.
    
    Args:
        target_rules: The chatbot's system instructions/guardrails
        attack_strategy: The attacker's persona and strategy
        max_turns: Maximum conversation turns
        difficulty: "easy", "medium", or "hard" - controls bot defensiveness
        verbose: Print progress information
    
    Returns:
        Dictionary with attack results
    """
    
    # Create the graph
    graph = create_breakmybot_graph(max_turns=max_turns)
    
    # Initialize state
    initial_state: ConversationState = {
        "target_rules": target_rules,
        "attack_strategy": attack_strategy,
        "difficulty": difficulty,
        "messages": [],
        "current_turn": 0,
        "max_turns": max_turns,
        "violations_found": [],
        "success": False,
        "last_evaluator_analysis": "",
        "closed_paths": [],
        "completed_paths": [],
        "confirmed_capabilities": [],
        "denied_capabilities": [],
        "evaluation_rubric": {},
    }
    
    if verbose:
        print(f"\n🎯 Starting attack on target chatbot...")
        print(f"📋 Target Rules: {target_rules[:100]}...")
        print(f"⚔️  Attack Strategy: {attack_strategy[:100]}...")
        print(f"🔄 Max Turns: {max_turns}")
        print(f"🎯 Difficulty: {difficulty}\n")
    
    # Run the graph
    final_state = None
    for state in graph.stream(initial_state, stream_mode="values"):
        if not isinstance(state, dict):
            continue

        if verbose and state.get("messages"):
            last_msg = state["messages"][-1]
            turn = state.get("current_turn", 0)
            role = last_msg["role"]
            print(f"--- Turn {turn} | Node: {role.upper()} ---")
            print(f"{role.upper()}: {last_msg['content']}\n")

        final_state = state
    
     # Format results
    if final_state is None:
        raise RuntimeError("Graph completed without producing any state. Check node implementations.")
    
    results = {
        "success": final_state["success"],
        "violations_found": final_state["violations_found"],
        "num_turns": final_state["current_turn"],
        "conversation": [
            {"role": msg["role"], "content": msg["content"]}
            for msg in final_state["messages"]
        ],
        "final_evaluation": final_state["last_evaluator_analysis"]
    }
    
    if verbose:
        print("\n" + "="*60)
        print("ATTACK RESULTS")
        print("="*60)
        print(f"✅ Success: {results['success']}")
        print(f"🚨 Violations Found: {len(results['violations_found'])}")
        for v in results['violations_found']:
            print(f"   - {v}")
        print(f"🔄 Total Turns: {results['num_turns']}")
        print("="*60 + "\n")
    
    return results
