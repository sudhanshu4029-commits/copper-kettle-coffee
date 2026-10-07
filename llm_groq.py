"""
Groq backend for Mira (fast: replies in ~1-2 seconds).

Groq speaks the OpenAI chat format, so tool calling works as a loop:
  1. send the conversation + tool definitions
  2. if the model asks for tools, run them in order_engine (via app.py) and send the results back
  3. repeat until the model answers in plain text

The model still never does arithmetic: every price comes from the tool results.
"""
import inspect
import json
import time

from groq import Groq

# gpt-oss-120b first: best quality per free token, and Groq caches the long system
# prompt (menu) so it doesn't count against the free-tier rate limit after the first call.
GROQ_MODELS = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "llama-3.3-70b-versatile"]
MAX_TOOL_STEPS = 8
HISTORY_MESSAGES = 30


class GroqFailure(Exception):
    """kind: key | rate | down | other"""

    def __init__(self, kind, detail=""):
        super().__init__(detail)
        self.kind = kind
        self.detail = detail


# ------------------------------------------------------------------ tool definitions (JSON schema)
def _tool(name, description, properties=None, required=()):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {"type": "object", "properties": properties or {}, "required": list(required)},
        },
    }


TOOL_SCHEMAS = [
    _tool(
        "add_to_order",
        "Add an item to the customer's order. Prices are calculated by the system. One call per distinct item/customisation.",
        {
            "item_id": {"type": "string", "description": 'Menu item id (e.g. "latte") or exact item name.'},
            "quantity": {"type": "integer", "description": "How many, 1-10."},
            "size": {"type": "string", "description": "Coffee size: Small, Regular or Large. Empty for snacks or default."},
            "milk": {"type": "string", "description": "Whole, Skim, Oat or Almond. Only for milk-based coffees."},
            "add_ons": {"type": "array", "items": {"type": "string"},
                        "description": 'Coffee add-ons from the menu, e.g. ["Extra shot"]. Empty for snacks.'},
            "warmed": {"type": "boolean", "description": "Snacks only. True if the customer wants it warmed."},
            "notes": {"type": "string", "description": 'Short preparation note, e.g. "extra hot".'},
        },
        required=["item_id"],
    ),
    _tool(
        "change_quantity",
        "Set the quantity of an existing order line. Quantity 0 removes the line.",
        {"line_no": {"type": "integer", "description": "Line number from the current order (starts at 1)."},
         "quantity": {"type": "integer", "description": "New quantity, 0-10."}},
        required=["line_no", "quantity"],
    ),
    _tool(
        "remove_from_order",
        "Remove one line from the order.",
        {"line_no": {"type": "integer", "description": "Line number from the current order (starts at 1)."}},
        required=["line_no"],
    ),
    _tool("clear_order", "Remove everything from the order. Only if the customer clearly asks to start over."),
    _tool("view_order", "Get the current order lines, subtotal, GST and total."),
    _tool(
        "prepare_checkout",
        "Step 1 of checkout. Locks the summary that the customer must confirm.",
        {"customer_name": {"type": "string", "description": "Customer's first name."},
         "order_type": {"type": "string", "enum": ["Dine-in", "Takeaway"]}},
        required=["customer_name", "order_type"],
    ),
    _tool("place_order",
          "Step 2 of checkout. Places the order. Call ONLY after the customer explicitly said yes to the summary."),
    _tool(
        "request_barista",
        "Hand off to a human barista (severe allergies, complaints, large catering orders, refunds, questions not covered by the menu).",
        {"reason": {"type": "string", "description": "One sentence describing what the customer needs."}},
        required=["reason"],
    ),
]


# ------------------------------------------------------------------ helpers
def _run_tool(name, raw_args, functions):
    func = functions.get(name)
    if not func:
        return {"ok": False, "error": f"Unknown tool '{name}'."}
    try:
        args = json.loads(raw_args or "{}")
        if not isinstance(args, dict):
            args = {}
    except json.JSONDecodeError:
        return {"ok": False, "error": "Tool arguments were not valid JSON. Try again."}
    allowed = inspect.signature(func).parameters
    args = {k: v for k, v in args.items() if k in allowed and v is not None}
    try:
        return func(**args)
    except Exception as e:  # never let a bad tool call crash the app
        return {"ok": False, "error": f"Could not run {name}: {e}"}


def trim_history(history):
    """Keep recent messages, starting at a user message so tool calls stay paired with their results."""
    if len(history) <= HISTORY_MESSAGES:
        return history
    tail = history[-HISTORY_MESSAGES:]
    for i, m in enumerate(tail):
        if m.get("role") == "user":
            return tail[i:]
    return history[-6:]


def _classify(e):
    msg = str(e)
    low = msg.lower()
    code = getattr(e, "status_code", None)
    if code == 401 or "invalid api key" in low or "invalid_api_key" in low:
        return "key"
    if code in (404,) or "decommissioned" in low or "does not exist" in low or "model_not_found" in low:
        return "model"
    if "tool_use_failed" in low or "failed to call a function" in low:
        return "bad_tool"
    if code == 429 or "rate limit" in low or "rate_limit" in low:
        return "rate"
    if code == 413 or "too large" in low:
        return "rate"
    if code and code >= 500:
        return "down"
    return "other"


# ------------------------------------------------------------------ main entry
def run_turn(api_key, system_prompt, history, user_message, functions, preferred_model=None):
    """Returns (reply_text, new_history, model_used). Raises GroqFailure."""
    client = Groq(api_key=api_key, max_retries=0, timeout=30)
    models = ([preferred_model] if preferred_model else []) + [m for m in GROQ_MODELS if m != preferred_model]
    # One conversation for the whole turn. If a model fails after tools already ran,
    # the next model continues from here, so items are never added twice.
    convo = trim_history(list(history)) + [{"role": "user", "content": user_message}]
    last = None

    for model in models:
        attempts = 0
        steps = 0
        while steps < MAX_TOOL_STEPS:
            kwargs = dict(
                model=model,
                messages=[{"role": "system", "content": system_prompt}] + convo,
                tools=TOOL_SCHEMAS,
                tool_choice="auto",
                temperature=0.3,
            )
            if model.startswith("openai/gpt-oss"):
                kwargs["reasoning_effort"] = "low"  # faster; ordering doesn't need deep reasoning
            try:
                resp = client.chat.completions.create(**kwargs)
            except Exception as e:
                last = e
                kind = _classify(e)
                attempts += 1
                if kind == "key":
                    raise GroqFailure("key", str(e))
                if kind == "model":
                    break  # try next model
                if kind in ("bad_tool", "other") and attempts < 2:
                    continue  # retry the same step once
                if kind == "rate" and attempts < 2:
                    time.sleep(4)
                    continue
                if kind == "rate":
                    raise GroqFailure("rate", str(e))
                if kind == "down" and attempts < 2:
                    time.sleep(2)
                    continue
                break  # give the next model a chance

            msg = resp.choices[0].message
            tool_calls = msg.tool_calls or []
            if not tool_calls:
                text = (msg.content or "").strip()
                convo.append({"role": "assistant", "content": text})
                return text, convo, model

            convo.append({
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {"id": tc.id, "type": "function",
                     "function": {"name": tc.function.name, "arguments": tc.function.arguments or "{}"}}
                    for tc in tool_calls
                ],
            })
            for tc in tool_calls:
                result = _run_tool(tc.function.name, tc.function.arguments, functions)
                convo.append({"role": "tool", "tool_call_id": tc.id,
                              "content": json.dumps(result, ensure_ascii=False, default=str)})
            steps += 1
            attempts = 0

        else:
            # too many tool steps in one turn: stop safely
            convo.append({"role": "assistant", "content": "Sorry, I got a bit tangled there. Could you say that again?"})
            return convo[-1]["content"], convo, model

    kind = _classify(last) if last else "other"
    raise GroqFailure("down" if kind in ("down", "model", "bad_tool") else kind, str(last))
