"""
Deterministic order logic for the coffee shop.

The AI never does arithmetic or decides prices. It calls these functions (as
Gemini "tools"), and this code validates every request against menu.json and
computes the totals. That keeps the running total correct even if the model
misunderstands something.
"""
import difflib
import json
import os
import random
import string
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Kolkata")  # change to your shop's timezone

MAX_QTY_PER_LINE = 10
MAX_LINES = 15

_here = os.path.dirname(os.path.abspath(__file__))


def load_menu():
    with open(os.path.join(_here, "menu.json"), encoding="utf-8") as f:
        return json.load(f)


MENU = load_menu()
ITEMS = {i["id"]: i for i in MENU["items"]}
CUR = MENU["currency"]


def money(x):
    return f"{CUR}{x:,.0f}" if float(x).is_integer() else f"{CUR}{x:,.2f}"


# ------------------------------------------------------------- name matching

def _norm(s):
    return "".join(ch for ch in str(s).lower() if ch.isalnum())


def resolve_item(text):
    """Accepts an id, an exact name, or a close spelling. Returns item or None."""
    if not text:
        return None
    if text in ITEMS:
        return ITEMS[text]
    key = _norm(text)
    table = {}
    for item in ITEMS.values():
        table[_norm(item["id"])] = item
        table[_norm(item["name"])] = item
    if key in table:
        return table[key]
    close = difflib.get_close_matches(key, list(table.keys()), n=1, cutoff=0.8)
    return table[close[0]] if close else None


def _resolve_option(text, options):
    """Match free text like 'oat milk' or 'large' to a key in options."""
    key = _norm(text).replace("milk", "").replace("syrup", "") or _norm(text)
    for opt in options:
        o = _norm(opt)
        if key == o or key == o.replace("milk", "").replace("syrup", ""):
            return opt
    close = difflib.get_close_matches(_norm(text), [_norm(o) for o in options], n=1, cutoff=0.75)
    if close:
        for opt in options:
            if _norm(opt) == close[0]:
                return opt
    return None


# ------------------------------------------------------------- pricing

def unit_price(item, size=None, milk=None, add_ons=()):
    price = item["price"]
    if item["category"] == "coffee":
        price += MENU["sizes"].get(size or "Regular", 0)
        if milk:
            price += MENU["milk_options"].get(milk, 0)
        price += sum(MENU["add_ons"][a] for a in add_ons)
    return price


def describe_line(line):
    item = ITEMS[line["item_id"]]
    bits = []
    if item["category"] == "coffee":
        if len(item["sizes"]) > 1:
            bits.append(line["size"])
        if line.get("milk") and line["milk"] != "Whole":
            bits.append(f'{line["milk"]} milk')
        bits.extend(line.get("add_ons", []))
    elif line.get("warmed"):
        bits.append("warmed")
    if line.get("notes"):
        bits.append(f'note: {line["notes"]}')
    extra = f" ({', '.join(bits)})" if bits else ""
    return f'{line["quantity"]} × {item["name"]}{extra}'


def totals(lines):
    subtotal = sum(l["unit_price"] * l["quantity"] for l in lines)
    gst = round(subtotal * MENU["gst_rate"], 2)
    return {"subtotal": subtotal, "gst": gst, "total": round(subtotal + gst, 2)}


def order_snapshot(lines):
    """Compact, model-friendly view of the cart."""
    t = totals(lines)
    return {
        "lines": [{"line_no": i + 1, "description": describe_line(l),
                   "line_total": money(l["unit_price"] * l["quantity"])} for i, l in enumerate(lines)],
        "subtotal": money(t["subtotal"]),
        "gst_5_percent": money(t["gst"]),
        "total": money(t["total"]),
        "item_count": sum(l["quantity"] for l in lines),
    }


def fingerprint(lines):
    return json.dumps([[l["item_id"], l["quantity"], l.get("size"), l.get("milk"), l.get("add_ons"), l.get("warmed"),
                        l.get("notes")] for l in lines], sort_keys=True)


# ------------------------------------------------------------- mutations
# Each returns (ok: bool, payload: dict). They mutate `state` in place.
# state = {"lines": [...], "pending_checkout": None | {...}, "orders": [...]}

def new_state():
    return {"lines": [], "pending_checkout": None, "orders": []}


def add_item(state, item_id, quantity=1, size="", milk="", add_ons=None, warmed=False, notes=""):
    item = resolve_item(item_id)
    if not item:
        names = ", ".join(i["name"] for i in ITEMS.values())
        return False, {"error": f"'{item_id}' is not on the menu.", "menu_items": names}
    if item.get("sold_out"):
        same = [i["name"] for i in ITEMS.values() if i["category"] == item["category"] and not i.get("sold_out")][:3]
        return False, {"error": f"{item['name']} is sold out today.", "suggest_instead": same}
    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        return False, {"error": "Quantity must be a whole number."}
    if not 1 <= quantity <= MAX_QTY_PER_LINE:
        return False, {"error": f"Quantity must be between 1 and {MAX_QTY_PER_LINE} per line. "
                                f"For bigger orders, ask a barista."}
    add_ons = [a for a in (add_ons or []) if str(a).strip()]
    notes = (notes or "").strip()[:120]

    line = {"item_id": item["id"], "quantity": quantity, "notes": notes}
    if item["category"] == "coffee":
        if size:
            s = _resolve_option(size, item["sizes"])
            if not s:
                if len(item["sizes"]) == 1:
                    return False, {"error": f"{item['name']} only comes in one size. "
                                            f"For more coffee, suggest adding an Extra shot."}
                return False, {"error": f"{item['name']} comes in: {', '.join(item['sizes'])}."}
        else:
            s = "Regular" if "Regular" in item["sizes"] else item["sizes"][0]
        m = ""
        if milk:
            if not item["has_milk"]:
                return False, {"error": f"{item['name']} is made without milk. "
                                        f"Add a note like 'splash of milk' instead, or pick a milk-based drink."}
            m = _resolve_option(milk, MENU["milk_options"])
            if not m:
                return False, {"error": f"Milk options are: {', '.join(MENU['milk_options'])}."}
        elif item["has_milk"]:
            m = "Whole"
        resolved = []
        for a in add_ons:
            r = _resolve_option(a, MENU["add_ons"])
            if not r:
                return False, {"error": f"'{a}' is not an available add-on. Options: {', '.join(MENU['add_ons'])}."}
            if r not in resolved:
                resolved.append(r)
        line.update(size=s, milk=m, add_ons=sorted(resolved), warmed=False)
    else:
        if add_ons or milk or size:
            return False, {"error": f"{item['name']} is a snack; sizes, milk and drink add-ons don't apply."}
        if warmed and not item.get("can_warm", False):
            return False, {"error": f"{item['name']} is served as is and can't be warmed."}
        line.update(size=None, milk=None, add_ons=[], warmed=bool(warmed))

    line["unit_price"] = unit_price(item, line.get("size"), line.get("milk"), line.get("add_ons", []))

    # merge with an identical existing line
    for existing in state["lines"]:
        if fingerprint([dict(existing, quantity=0)]) == fingerprint([dict(line, quantity=0)]):
            if existing["quantity"] + quantity > MAX_QTY_PER_LINE:
                return False, {"error": f"That would make {existing['quantity'] + quantity}; "
                                        f"the limit is {MAX_QTY_PER_LINE} per line."}
            existing["quantity"] += quantity
            state["pending_checkout"] = None
            return True, {"added": describe_line(dict(line)), "order": order_snapshot(state["lines"])}
    if len(state["lines"]) >= MAX_LINES:
        return False, {"error": "The order is very large; please ask a barista to help with catering orders."}
    state["lines"].append(line)
    state["pending_checkout"] = None
    return True, {"added": describe_line(line), "order": order_snapshot(state["lines"])}


def _line_index(state, line_no):
    try:
        idx = int(line_no) - 1
    except (TypeError, ValueError):
        return None
    return idx if 0 <= idx < len(state["lines"]) else None


def change_quantity(state, line_no, quantity):
    idx = _line_index(state, line_no)
    if idx is None:
        return False, {"error": f"There is no line {line_no}.", "order": order_snapshot(state["lines"])}
    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        return False, {"error": "Quantity must be a whole number."}
    if quantity == 0:
        return remove_line(state, line_no)
    if not 1 <= quantity <= MAX_QTY_PER_LINE:
        return False, {"error": f"Quantity must be between 0 and {MAX_QTY_PER_LINE}."}
    state["lines"][idx]["quantity"] = quantity
    state["pending_checkout"] = None
    return True, {"order": order_snapshot(state["lines"])}


def remove_line(state, line_no):
    idx = _line_index(state, line_no)
    if idx is None:
        return False, {"error": f"There is no line {line_no}.", "order": order_snapshot(state["lines"])}
    removed = describe_line(state["lines"].pop(idx))
    state["pending_checkout"] = None
    return True, {"removed": removed, "order": order_snapshot(state["lines"])}


def clear(state):
    state["lines"].clear()
    state["pending_checkout"] = None
    return True, {"order": order_snapshot(state["lines"])}


def prepare_checkout(state, customer_name, order_type):
    """Step 1 of 2. Locks a summary the customer must explicitly confirm."""
    if not state["lines"]:
        return False, {"error": "The order is empty."}
    name = (customer_name or "").strip()
    if not name or len(name) > 40:
        return False, {"error": "I need a first name for the order (up to 40 characters)."}
    ot = _resolve_option(order_type or "", ["Dine-in", "Takeaway"])
    if not ot:
        return False, {"error": "Is this for dine-in or takeaway?"}
    state["pending_checkout"] = {"name": name, "order_type": ot, "fingerprint": fingerprint(state["lines"])}
    return True, {"status": "awaiting_customer_confirmation", "name": name, "order_type": ot,
                  "order": order_snapshot(state["lines"])}


def place_order(state):
    """Step 2 of 2. Only works if the cart is unchanged since prepare_checkout."""
    pending = state.get("pending_checkout")
    if not pending:
        return False, {"error": "Checkout wasn't prepared. Show the summary and get a clear yes first."}
    if pending["fingerprint"] != fingerprint(state["lines"]):
        state["pending_checkout"] = None
        return False, {"error": "The order changed after the summary. Show the new summary and confirm again."}
    drinks = sum(l["quantity"] for l in state["lines"] if ITEMS[l["item_id"]]["category"] == "coffee")
    minutes = 4 + 2 * drinks
    order_id = "CK-" + datetime.now(TZ).strftime("%d%m") + "-" + "".join(random.choices(string.digits, k=4))
    snap = order_snapshot(state["lines"])
    record = {"order_id": order_id, "name": pending["name"], "order_type": pending["order_type"],
              "ready_in_minutes": minutes,
              "placed_at": datetime.now(TZ).strftime("%H:%M"),
              "ready_by": (datetime.now(TZ) + timedelta(minutes=minutes)).strftime("%H:%M"),
              **snap}
    state["orders"].append(record)
    state["lines"].clear()
    state["pending_checkout"] = None
    return True, {"status": "placed", **record, "payment": "Pay at the counter (cash, card or UPI)."}
