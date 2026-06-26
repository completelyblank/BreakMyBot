<img width="400" height="225" alt="2026-06-26 05-42-54" src="https://github.com/user-attachments/assets/cd2ecb69-69dc-4926-9fec-caa65ec62044" />


# BreakMyBot

Automated Adversarial Testing Framework for AI Chatbots

A multi-agent system that autonomously tests chatbot guardrails by generating adversarial attacks designed to identify security flaws, policy violations, and exploitable weaknesses.

## Overview

Organizations deploy customer service chatbots with strict business rules -- refund limits, pricing restrictions, access controls. BreakMyBot systematically attacks these chatbots to evaluate their resilience:

```
[Attacker Agent] -> [Target Chatbot] -> [Evaluator Judge]
(Tries to crack it)  (Defends itself)  (Checks for violations)
```

The system uses a LangGraph state machine with three nodes in a loop. The attacker generates adversarial messages, the target chatbot responds according to its guardrails, and the evaluator judges the exchange for policy violations.

## Architecture

### Multi-Agent Loop (LangGraph)

1. **Attacker Node**: An adversarial LLM with pre-attack reasoning, strategy selection, and adaptive failure tracking. Maintains registries of confirmed capabilities and denied capabilities to pivot intelligently.

2. **Target Node**: The chatbot under test, defending its rules. Difficulty configuration (easy/medium/hard) controls temperature and vulnerability injection.

3. **Evaluator Node**: An LLM-as-a-Judge that audits each turn with a 7-point rubric (direct policy violation, hallucinated capabilities, fabricated identifiers, false escalation claim, promised future action, unauthorized authority claim, social engineering success). Includes negation awareness and false premise detection.

### Graph Flow

```
START
  |
ATTACKER (generates attack message with pre-attack reasoning)
  |
TARGET (responds to attack according to rules)
  |
EVALUATOR (checks for policy violations, extracts capabilities)
  |
[if success or max_turns reached] -> END
[otherwise] -> back to ATTACKER
```

## Key Features

- **Capability Tracking**: The evaluator extracts confirmed and denied capabilities from each target response. The attacker uses these registries to avoid closed paths and exploit open avenues.

- **Adaptive Strategy Switching**: When a path is rejected or closed, the attacker automatically selects a different strategy from a pool of 15+ options, filtered to avoid previously denied approaches.

- **Pre-Attack Reasoning**: Before generating each message, the attacker performs a structured reasoning pass answering four questions: what the target can do, what it cannot do, what was last attempted, and what new path to try next.

- **Difficulty Selector**: Three difficulty levels (easy, medium, hard) control the target bot's temperature and whether vulnerability hints are injected.

- **Negation-Aware Rubric**: The evaluator's rubric checks are batch-processed with negation awareness, ensuring affirmative statements are distinguished from denials.

- **False Premise Detection**: The evaluator checks whether the attacker successfully gaslit the target into accepting a false premise (requires social engineering success for a hard win).

- **Real-Time Web Interface**: A Flask API with SSE streaming provides a browser-based UI for running and observing attacks in real time.

- **LLM Provider**: All LLM calls use Groq API with llama-3.3-70b-versatile.

## Installation

```bash
pip install -r requirements.txt
```

Set up your Groq API key:

```bash
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

## Quick Start

### Run a Single Attack from the Command Line

```bash
python main.py
```

### Run with Custom Parameters

```bash
python main.py --difficulty easy --max-turns 7
```

### Web Interface

```bash
python api.py
```

Open the frontend at the URL printed in the console. Select a difficulty level and click "Launch Attack" to start a run with real-time streaming output.

## Core Components

### `src/state.py`

Defines `ConversationState` -- the shared state flowing through the graph:
- `target_rules`: The chatbot's guardrails
- `attack_strategy`: The attacker's persona and approach
- `difficulty`: easy, medium, or hard
- `messages`: Accumulated conversation history
- `confirmed_capabilities` / `denied_capabilities`: Capability registries
- `closed_paths` / `completed_paths`: Path tracking for adaptive pivoting
- `violations_found`: Policy breaches detected
- `evaluation_rubric`: Per-turn rubric results
- `success`: Whether the attack succeeded

### `src/nodes.py`

Three node implementations:
- **TargetNode**: Responds as the customer service bot with difficulty-based temperature and optional vulnerability injection on easy mode.
- **AttackerNode**: Generates adversarial messages with pre-attack reasoning, LLM-based rejection extraction, strategy filtering, and adaptive failure tracking.
- **EvaluatorNode**: LLM-as-a-Judge with batched negation-aware rubric checks, capability extraction, false premise detection, and escalation rules.

### `src/graph.py`

LangGraph orchestration:
- `create_breakmybot_graph()`: Builds the attack loop with conditional routing based on success and turn count.
- `run_attack()`: Executes a complete attack scenario with parameters for target rules, attack strategy, max turns, and difficulty.

### `src/attack_strategies.py`

Pre-configured attack personas with metadata for automated filtering:
- 15+ strategies including gaslighter, prompt injector, social engineer, policy interpreter, rule contradiction, compliance officer, fake documentation, and more.
- Each strategy has a description and keywords used by the attacker's strategy filtering logic.

### `api.py`

Flask API providing:
- SSE streaming endpoint for real-time attack execution
- Difficulty query parameter
- Structured JSON event stream with message content, turn number, and node information

### `frontend/index.html`

Browser-based UI with:
- Difficulty selector dropdown
- Launch button
- Real-time conversation display with color-coded messages

## Configuration

### Difficulty Levels

| Level | Temperature | Vulnerability Injection | Mode Options |
|-------|-------------|------------------------|--------------|
| easy | 0.7 | Injected (exceptions allowed for loyal customers) | Weighted toward customer-first |
| medium | 0.5 | None | Equal weight strict/balanced/customer-first |
| hard | 0.3 | None | Always strict |

### Attack Parameters

- `max_turns`: Number of conversation exchanges (default: 5)
- `target_rules`: The guardrails to test
- `attack_strategy`: The adversarial persona/approach
- `difficulty`: easy, medium, or hard

### LLM Models

All calls use Groq's llama-3.3-70b-versatile model. Configure via environment variables.

## LangGraph Design Patterns

This project demonstrates several LangGraph patterns:

1. **Conditional Routing**: The evaluator's output determines if the loop continues or exits.
2. **State Accumulation**: Messages and tracking lists accumulate through LangGraph's `Annotated[List, add]` reducer pattern.
3. **Multi-Agent Cycles**: Synchronous turn-taking between competing agents.
4. **Partial State Updates**: Each node returns only the fields it modifies, relying on LangGraph's reducer-based state merging.
5. **Extensibility**: Easy to add nodes for logging, persistence, or external validation.

## Extending BreakMyBot

### Add New Attack Strategies

Edit `src/attack_strategies.py`:

```python
ATTACK_STRATEGIES["my_strategy"] = """Your attack description..."""
STRATEGY_METADATA["my_strategy"] = {
    "description": "...",
    "keywords": ["keyword1", "keyword2"]
}
```

### Add New Target Roles

```python
ROLE_BASED_RULES["my_role"] = """Your target rules..."""
```

### Custom Evaluator Logic

Extend `EvaluatorNode` to detect domain-specific violations:

```python
class CustomEvaluator(EvaluatorNode):
    def __call__(self, state):
        # Your custom evaluation logic
        pass
```

## Safety and Ethics

This tool is designed for authorized security testing only. Use it to:
- Test your own chatbots before deployment
- Identify vulnerabilities during development
- Improve AI safety and robustness

Do not use this to attack third-party chatbots without explicit permission.

## Requirements

- Python 3.10+
- Groq API key
- LangChain and LangGraph
- Flask (for web interface)

## License

MIT
