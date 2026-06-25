"""
Flask API for BreakMyBot frontend.
Streams attack events via Server-Sent Events (SSE).
"""

import json
import time
from flask import Flask, Response, request, jsonify, send_from_directory
from flask_cors import CORS

from src.attack_strategies import get_attack_strategy, get_target_rules, ATTACK_STRATEGIES, ROLE_BASED_RULES
from src.state import ConversationState, Message
from src.nodes import TargetNode, AttackerNode, EvaluatorNode
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder="frontend")
CORS(app)

# Initialize nodes once (reuse across requests)
attacker_node = AttackerNode()
target_node = TargetNode()
evaluator_node = EvaluatorNode()


def run_attack_stream(target_rules: str, attack_strategy: str, max_turns: int, difficulty: str = "medium"):
    """
    Generator that runs the attack loop and yields SSE events.
    Each event is a JSON object with a `type` field.
    """

    state: ConversationState = {
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

    def emit(event_type: str, data: dict):
        payload = json.dumps({"type": event_type, **data})
        return f"data: {payload}\n\n"

    yield emit("start", {"max_turns": max_turns, "difficulty": difficulty})

    for turn in range(max_turns):
        state["current_turn"] = turn

        # --- Attacker ---
        yield emit("node_start", {"node": "attacker", "turn": turn})
        try:
            state = attacker_node(state)
            last_msg = state["messages"][-1]
            yield emit("message", {
                "role": "attacker",
                "content": last_msg["content"],
                "turn": turn
            })
        except Exception as e:
            yield emit("error", {"message": str(e), "node": "attacker"})
            return

        # --- Target ---
        yield emit("node_start", {"node": "target", "turn": turn})
        try:
            state = target_node(state)
            last_msg = state["messages"][-1]
            yield emit("message", {
                "role": "target",
                "content": last_msg["content"],
                "turn": turn
            })
        except Exception as e:
            yield emit("error", {"message": str(e), "node": "target"})
            return

        # --- Evaluator ---
        yield emit("node_start", {"node": "evaluator", "turn": turn})
        try:
            state = evaluator_node(state)
            yield emit("evaluation", {
                "turn": turn,
                "violation_detected": state["success"],
                "violations": state["violations_found"],
                "analysis": state["last_evaluator_analysis"]
            })
        except Exception as e:
            yield emit("error", {"message": str(e), "node": "evaluator"})
            return

        if state["success"]:
            yield emit("breach", {
                "turn": turn,
                "violations": state["violations_found"]
            })
            break

    yield emit("complete", {
        "success": state["success"],
        "violations": state["violations_found"],
        "num_turns": state["current_turn"] + 1,
        "conversation": [
            {"role": m["role"], "content": m["content"]}
            for m in state["messages"]
        ]
    })


@app.route("/")
def index():
    return send_from_directory("frontend", "index.html")


@app.route("/api/strategies")
def get_strategies():
    return jsonify({
        "strategies": list(ATTACK_STRATEGIES.keys()),
        "targets": list(ROLE_BASED_RULES.keys())
    })


@app.route("/api/attack", methods=["GET"])
def attack():
    target_key = request.args.get("target", "airline_support")
    strategy_key = request.args.get("strategy", "gaslighter")
    max_turns = int(request.args.get("max_turns", 5))
    difficulty = request.args.get("difficulty", "medium")

    target_rules = get_target_rules(target_key)
    attack_strategy = get_attack_strategy(strategy_key)

    return Response(
        run_attack_stream(target_rules, attack_strategy, max_turns, difficulty),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000, threaded=True)
