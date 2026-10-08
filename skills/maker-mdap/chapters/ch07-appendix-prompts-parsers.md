# Chapter 7: Appendix C/D — Reference Prompts, Parsers, and Sample Behavior

## Core Idea
The paper's exact prompt templates and both parser variants (repairing vs. red-flagging) are
reproduced here as directly reusable reference implementations for anyone building a MAD-style
single-step agent with a strict output contract.

## Code Examples

### System + user prompt template (Towers of Hanoi, per-step agent)
```text
SYSTEM_PROMPT = """
You are a helpful assistant. Solve this puzzle for me.

There are three pegs and n disks of different sizes stacked on the first peg. The disks are
numbered from 1 (smallest) to n (largest). Disk moves in this puzzle should follow:
1. Only one disk can be moved at a time.
2. Each move consists of taking the upper disk from one stack and placing it on top of
another stack.
3. A larger disk may not be placed on top of a smaller disk.
The goal is to move the entire stack to the third peg.

Example: With 3 disks numbered 1 (smallest), 2, and 3 (largest), the initial state is [[3, 2,
1], [], []], and a solution might be:
moves = [[1, 0, 2], [2, 0, 1], [1, 2, 1], [3, 0, 2], [1, 1, 0], [2, 1, 2], [1, 0, 2]]
This means: Move disk 1 from peg 0 to peg 2, then move disk 2 from peg 0 to peg 1, and so on.

Requirements:
- The positions are 0-indexed (the leftmost peg is 0).
- Ensure your answer includes a single next move in this EXACT FORMAT:
```move = [disk id, from peg, to peg]```
- Ensure your answer includes the next state resulting from applying the move to the current
state in this EXACT FORMAT:
```next_state = [[...], [...], [...]]```
"""

USER_TEMPLATE = """
Rules:
- Only one disk can be moved at a time.
- Only the top disk from any stack can be moved.
- A larger disk may not be placed on top of a smaller disk.

For all moves, follow the standard Tower of Hanoi procedure:
If the previous move did not move disk 1, move disk 1 clockwise one peg (0 -> 1 -> 2 -> 0).
If the previous move did move disk 1, make the only legal move that does not involve moving
disk1.
Use these clear steps to find the next move given the previous move and current state.

Previous move: {previous_move}

Current State: {current_state}

Based on the previous move and current state, find the single next move that follows the
procedure and the resulting next state.
"""
```
- **What it demonstrates**: a single-step agent prompt carries (1) the fixed overall strategy
  once, (2) a strict output-format contract, and (3) only the *current* state + prior move —
  never the growing history of the whole run. This is Maximal Agentic Decomposition (Ch 3) made
  concrete.

### Repairing parser (used for calibration only, Section 4.2 / Ch 4)
```python
import re, ast

def extract_balanced_brackets(text, start_idx):
    """Extract a substring with balanced brackets [[...]] starting at start_idx"""
    bracket_stack = []
    i = start_idx
    while i < len(text):
        if text[i] == '[':
            bracket_stack.append('[')
        elif text[i] == ']':
            if not bracket_stack:
                break
            bracket_stack.pop()
            if not bracket_stack:
                return text[start_idx:i + 1]
        i += 1
    return text[start_idx:i] + ']'

def parse_move_state_repair(response_text):
    try:
        move_matches = re.findall(r"(?i)\bmove\b\s*=\s*(\[[^\[\]]*\])", response_text)
        if not move_matches:
            raise ValueError("No 'move' found in response.")
        move = ast.literal_eval(move_matches[-1].strip())
    except Exception as e:
        raise ValueError("Could not parse 'move' from response.") from e

    try:
        pattern = re.compile(r"(?i)\bnext_state\b\s*=\s*(\[\s*\[)", re.DOTALL)
        matches = list(pattern.finditer(response_text))
        if not matches:
            raise ValueError("No 'next_state' found in response.")
        start_idx = matches[-1].start(1)  # last match
        next_state_str = extract_balanced_brackets(response_text, start_idx).strip()
        next_state = ast.literal_eval(next_state_str)
    except Exception as e:
        raise ValueError("Could not parse 'next_state' from response.") from e

    return move, next_state
```
- **What it demonstrates**: a "helpful" parser that tries hard to extract a usable answer even
  from slightly malformed output. Useful for cheaply *measuring* p, but shown (Ch 5) to let more
  correlated errors slip through than the strict variant below.

### Red-flagging parser (used for the scale-up run, Section 4.4 / Ch 4)
```python
import re, ast

def _validate_move(move):
    if not isinstance(move, list) or len(move) != 3 or not all(isinstance(x, int) for x in move):
        raise ValueError("'move' must be a list of exactly 3 integers.")
    return move

def _validate_state(state):
    if not (isinstance(state, list) and len(state) == 3 and all(isinstance(t, list) for t in state)):
        raise ValueError("'next_state' must be a list of three lists.")
    flat = [x for t in state for x in t]
    if not all(isinstance(x, int) for x in flat):
        raise ValueError("All entries in 'next_state' must be integers.")
    if len(flat) != 20 or set(flat) != set(range(1, 21)):
        missing = sorted(set(range(1, 21)) - set(flat))
        extra   = sorted(set(flat) - set(range(1, 21)))
        raise ValueError("State must contain 1..20 exactly once. "
                         f"Missing: {missing or '[]'}, Extras: {extra or '[]'}")
    return state

def parse_move_state_flag(response_text: str):
    move_pat = re.compile(r"(?is)\bmove\b\s*=\s*(\[[^\[\]]*\])")
    state_pat = re.compile(
        r"(?is)\bnext_state\b\s*=\s*(\[\s*\[[^\[\]]*\]\s*,\s*\[[^\[\]]*\]\s*,\s*\[[^\[\]]*\]\s*\])"
    )

    move_matches = list(move_pat.finditer(response_text))
    if not move_matches:
        raise ValueError("No 'move = [...]' found.")
    move_str = move_matches[-1].group(1)  # last 'move'

    state_matches = list(state_pat.finditer(response_text))
    if not state_matches:
        raise ValueError("No 'next_state = [[...],[...],[...]]' found.")
    state_str = state_matches[-1].group(1)  # last 'next_state'

    try:
        move = ast.literal_eval(move_str)
    except Exception as e:
        raise ValueError("Could not parse 'move' as a Python list.") from e
    try:
        next_state = ast.literal_eval(state_str)
    except Exception as e:
        raise ValueError("Could not parse 'next_state' as Python lists.") from e

    return _validate_move(move), _validate_state(next_state)
```
- **What it demonstrates**: strict validation with **no repair attempt** — any structural
  deviation (wrong bracket shape, wrong element count, duplicate/missing disk IDs, non-integer
  entries) raises, and the caller discards the sample and resamples. This is the red-flagging
  half of MAKER (Ch 3) made concrete, and is the parser actually used in the zero-error
  million-step run.

## Reference Tables
| Parser | Behavior on malformed output | Used for |
|---|---|---|
| Repairing (`parse_move_state_repair`) | Tries to salvage a usable answer via regex/bracket-balancing | Cheap p-estimation only (Ch 4 / Section 4.2) |
| Red-flagging (`parse_move_state_flag`) | Raises immediately, sample is discarded and resampled | The actual scale-up run (Ch 4 / Section 4.4) |

## Key Takeaways
1. The full prompt-and-parser pair here is a directly reusable template for any single-step,
   strict-output-format MAD agent — swap the domain-specific rules/state representation.
2. The red-flagging parser's validation is deliberately strict and unforgiving: exact list
   shapes, exact element counts, exact value sets — malformed input is a red flag, not a bug to
   patch around.
3. Two illustrative sample transcripts (Appendix D) contrast a clean 256-token correct answer
   against a 2048-token transcript where the model "talks in circles" after an early mistake and
   never reaches a validly formatted answer — concrete evidence for the length-correlates-with-
   confusion finding in Ch 5.

## Connects To
- **Ch 3**: the abstract `ψ_a` / `ψ_x` extractor functions these parsers implement concretely.
- **Ch 4/5**: the empirical comparison of these two parsers' effect on correlated errors.
