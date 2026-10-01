"""
tools.py

Tool logic for the Campus Customs shop chatbot (agent.py). agent.py only wires
these into `@agent.tool` calls; the actual database access lives here so
main.py can reuse the same helpers for the plain REST product endpoints.

Problem 5 - search_products: a loose keyword search over the catalogue, so the
agent can answer "what hoodies do you have" style questions with real product
cards.

Problem 6 - product info and stock: `product_lookup` is the single source of
truth for a product's description, price, and per-size stock. It always reads
campus_customs.db directly and never lets the model fill in a number itself -
if the product isn't found, `found=False` is returned so the agent can say so
and point the customer to SUPPORT_PHONE instead of guessing.

Problem 8 - customer memory: `load_full_history` reloads a logged-in
customer's saved conversation (with product cards) for the frontend, and
`get_customer_context` looks up their name/email so the agent knows who it's
talking to. Guests never call either - there's no row to load or look up.

Problem 9 - usability:
  - `product_info_from_message` fuses search + lookup into one tool call: given
    the customer's own chat wording, it finds the matching product(s) AND
    returns their full real description/price/stock in a single round trip,
    instead of the agent needing a separate search then a separate lookup.
  - `list_categories` / `search_products_by_category` group the catalogue by a
    normalized category (Hoodie, Crewneck, T-Shirt, etc., derived from the
    granular `garment_type` column) and keep that index sorted by category
    then name, so a question naming a garment type ("what hoodies do you
    have") can go straight to the matching category slice instead of a full
    keyword scan over every field of all 102 rows.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import TypeAdapter, ValidationError
from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart, ToolReturnPart

from models import (
    AuditEntry,
    AuditEventType,
    ChatHistoryMessage,
    ChatTurn,
    CustomerContext,
    ProductCard,
    ProductLookupResult,
    SizeStock,
)

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "campus_customs.db"

# Campus Customs has no real support line in the seed data; this is a
# placeholder the agent can point customers to when it genuinely doesn't know.
SUPPORT_PHONE = "(203) 555-0199"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def parse_json_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return []


def image_url_for(image_file_path: str) -> str:
    return f"/media/products/{Path(image_file_path).name}"


def _row_to_card(row: sqlite3.Row) -> ProductCard:
    return ProductCard(
        product_id=row["product_id"],
        name=row["name"],
        price=row["price"],
        image_url=image_url_for(row["image_file_path"]),
        colors=parse_json_list(row["colors"]),
        garment_type=row["garment_type"],
    )


def search_products(query: str, limit: int = 6) -> list[ProductCard]:
    """
    Loose keyword search over the catalogue (name, garment type, description,
    colors, search tags). Used for "what do you have" style browsing questions,
    not for a definitive price/stock answer - use product_lookup for that.
    """
    conn = get_connection()
    rows = conn.execute("SELECT * FROM catalogue ORDER BY name").fetchall()
    conn.close()

    q = query.lower().strip()
    if not q:
        matches = rows[:limit]
    else:
        def haystack(row: sqlite3.Row) -> str:
            return " ".join(
                [
                    row["name"],
                    row["garment_type"],
                    row["description"],
                    row["colors"] or "",
                    row["search_tags"] or "",
                ]
            ).lower()

        matches = [row for row in rows if q in haystack(row)][:limit]

    return [_row_to_card(row) for row in matches]


def product_lookup(product_id: str) -> ProductLookupResult:
    """
    The single source of truth for one product's description, price, and
    per-size stock, read straight from campus_customs.db. Never returns a
    guessed price or quantity: if the product_id doesn't exist, `found=False`
    is returned instead of any fabricated data.
    """
    conn = get_connection()
    row = conn.execute("SELECT * FROM catalogue WHERE product_id = ?", (product_id,)).fetchone()
    if row is None:
        conn.close()
        return ProductLookupResult(found=False, product_id=product_id)

    inventory_rows = conn.execute(
        "SELECT size, quantity FROM inventory WHERE product_id = ? ORDER BY id", (product_id,)
    ).fetchall()
    conn.close()

    sizes = [
        SizeStock(size=inv["size"], quantity=inv["quantity"], in_stock=inv["quantity"] > 0)
        for inv in inventory_rows
    ]
    return ProductLookupResult(
        found=True,
        product_id=row["product_id"],
        name=row["name"],
        description=row["description"],
        price=row["price"],
        colors=parse_json_list(row["colors"]),
        image_url=image_url_for(row["image_file_path"]),
        sizes=sizes,
    )


def find_product_ids_by_name(name_fragment: str, limit: int = 5) -> list[str]:
    """Help the agent resolve a customer's product name into product_id(s) it can pass to product_lookup."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT product_id, name FROM catalogue WHERE name LIKE ? ORDER BY name LIMIT ?",
        (f"%{name_fragment}%", limit),
    ).fetchall()
    conn.close()
    return [row["product_id"] for row in rows]


_MESSAGE_STOPWORDS = {
    "the", "a", "an", "is", "are", "do", "does", "you", "your", "i", "in", "on",
    "of", "to", "for", "this", "that", "it", "have", "has", "any", "can", "me",
    "what", "which", "about", "with", "and", "or", "please", "hi", "hello",
}


def product_info_from_message(customer_message: str, limit: int = 3) -> list[ProductLookupResult]:
    """
    Usability improvement (Problem 9): take the customer's own chat wording
    directly - a full sentence, not just a keyword - and return full product
    info (real description/price/stock) for whatever it matches, in one tool
    call instead of a separate search_products followed by a product_lookup
    per result. Ranks catalogue rows by keyword-token overlap with the
    message (not literal substring containment), since a real customer
    message is a sentence, not a search term.
    """
    tokens = [t for t in re.findall(r"[a-z0-9]+", customer_message.lower()) if len(t) > 2 and t not in _MESSAGE_STOPWORDS]
    if not tokens:
        return []

    conn = get_connection()
    rows = conn.execute("SELECT * FROM catalogue").fetchall()
    conn.close()

    def haystack(row: sqlite3.Row) -> str:
        return " ".join(
            [row["name"], row["garment_type"], row["description"], row["colors"] or "", row["search_tags"] or ""]
        ).lower()

    scored = [(sum(1 for t in tokens if t in haystack(row)), row) for row in rows]
    scored = [(score, row) for score, row in scored if score > 0]
    scored.sort(key=lambda item: (-item[0], item[1]["name"]))

    return [product_lookup(row["product_id"]) for _, row in scored[:limit]]


# --- Category index (Problem 9: usability/efficiency) ----------------------
#
# catalogue.garment_type is a granular free-text field ("hooded pullover
# sweatshirt", "pullover hoodie", "hoodie", ...) with 21 distinct values for
# 102 products. _CATEGORY_KEYWORDS groups those into a handful of broad,
# customer-facing categories, checked in order (most specific first) so e.g.
# "bomber jacket" resolves to Outerwear before any hoodie/crewneck check runs.

_CATEGORY_KEYWORDS: list[tuple[str, str]] = [
    ("quarter zip", "Quarter-Zip"),
    ("jacket", "Outerwear"),
    ("bomber", "Outerwear"),
    ("hood", "Hoodie"),
    ("crewneck", "Crewneck"),
    ("mockneck", "Crewneck"),
    ("long sleeve", "Long Sleeve"),
    ("t shirt", "T-Shirt"),
]


def normalize_category(garment_type: str) -> str:
    # Hyphens vs. spaces are the same word to a customer ("quarter-zip" /
    # "quarter zip"), so fold both to spaces before matching keywords.
    g = garment_type.lower().replace("-", " ")
    for keyword, category in _CATEGORY_KEYWORDS:
        if keyword in g:
            return category
    return "Other"


def _catalogue_sorted_by_category() -> list[sqlite3.Row]:
    """The full catalogue, sorted by (normalized category, name) - the category-first index."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM catalogue").fetchall()
    conn.close()
    return sorted(rows, key=lambda row: (normalize_category(row["garment_type"]), row["name"]))


def list_categories() -> list[str]:
    """Distinct product categories actually present in the catalogue, alphabetical."""
    rows = _catalogue_sorted_by_category()
    return sorted({normalize_category(row["garment_type"]) for row in rows})


def search_products_by_category(category: str, limit: int = 12) -> list[ProductCard]:
    """
    Category-first product lookup: filter the category-sorted catalogue index
    to one category (e.g. "Hoodie", "hoodies", "quarter zip", "jackets")
    instead of scanning every text field of every row, then return cards
    sorted by name.
    """
    rows = _catalogue_sorted_by_category()
    target_category = normalize_category(category)

    if target_category != "Other":
        matches = [row for row in rows if normalize_category(row["garment_type"]) == target_category]
    else:
        # category didn't match a known keyword directly (e.g. "long sleeves") -
        # fall back to a loose match against the canonical category names.
        loose = category.strip().lower().replace("-", " ").rstrip("s")
        matches = [
            row
            for row in rows
            if loose in normalize_category(row["garment_type"]).lower().replace("-", " ")
        ]

    return [_row_to_card(row) for row in matches[:limit]]


# --- Chat persistence -------------------------------------------------------
#
# chat_messages.user_id is NOT NULL with a FK to users, so we only persist
# turns for a logged-in customer. An anonymous visitor can still chat - the
# agent still runs and replies - but that conversation isn't saved, since the
# schema has no concept of a guest.


def load_recent_history(user_id: int, limit: int = 10) -> list[ChatTurn]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT role, content FROM chat_messages WHERE user_id = ? ORDER BY id DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    conn.close()
    return [ChatTurn(role=row["role"], content=row["content"]) for row in reversed(rows)]


def save_chat_message(user_id: int, role: str, content: str, products: list[ProductCard]) -> None:
    conn = get_connection()
    products_json = json.dumps([p.model_dump() for p in products]) if products else None
    conn.execute(
        "INSERT INTO chat_messages (user_id, role, content, products_json) VALUES (?, ?, ?, ?)",
        (user_id, role, content, products_json),
    )
    conn.commit()
    conn.close()


def load_full_history(user_id: int, limit: int = 30) -> list[ChatHistoryMessage]:
    """
    Full saved conversation (role, content, and any product cards), for the
    frontend to reload when a logged-in customer comes back - distinct from
    load_recent_history(), which only gives the agent role/content for context.
    """
    conn = get_connection()
    rows = conn.execute(
        "SELECT role, content, products_json FROM chat_messages WHERE user_id = ? ORDER BY id DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    conn.close()

    messages = []
    for row in reversed(rows):
        raw_products = json.loads(row["products_json"]) if row["products_json"] else []
        messages.append(
            ChatHistoryMessage(
                role=row["role"],
                content=row["content"],
                products=[ProductCard.model_validate(p) for p in raw_products],
            )
        )
    return messages


def get_customer_context(user_id: int) -> CustomerContext | None:
    """Look up the logged-in customer's name/email, so the agent knows who it's talking to."""
    conn = get_connection()
    row = conn.execute("SELECT name, email FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    if row is None:
        return None
    return CustomerContext(name=row["name"], email=row["email"])


# --- Audit trail (Problem 12) ----------------------------------------------
#
# Every chat turn appends to output/audit_trail.json: when it ran, which model,
# every tool the agent called (truncated args + result), each step's stop
# reason, and how the run ended. The file is append-only - it is never cleared
# between runs, and an unreadable file is moved aside rather than overwritten.

AUDIT_TRAIL_PATH = BASE_DIR / "output" / "audit_trail.json"
MAX_AUDIT_TEXT = 300
_audit_lock = threading.Lock()


def truncate_for_audit(value: Any) -> str:
    text = value if isinstance(value, str) else json.dumps(value, default=str)
    return text if len(text) <= MAX_AUDIT_TEXT else text[:MAX_AUDIT_TEXT] + "..."


def audit_entry(event: AuditEventType, timestamp: datetime | None = None, **details: Any) -> AuditEntry:
    return AuditEntry(timestamp=timestamp or datetime.now(timezone.utc), event=event, **details)


def iteration_audit_entries(messages: list[Any], run_id: str) -> list[AuditEntry]:
    """One record per tool call the model made, with that step's finish_reason."""
    returns: dict[str, str] = {}
    for message in messages:
        for part in getattr(message, "parts", []):
            if isinstance(part, ToolReturnPart):
                returns[part.tool_call_id] = truncate_for_audit(part.content)

    entries: list[AuditEntry] = []
    for message in messages:
        if not isinstance(message, ModelResponse):
            continue
        stop_reason = str(message.finish_reason) if message.finish_reason else None
        tool_calls = [p for p in message.parts if isinstance(p, ToolCallPart)]
        if not tool_calls:
            if any(isinstance(p, TextPart) for p in message.parts) or stop_reason:
                entries.append(
                    audit_entry(
                        AuditEventType.TOOL_CALL,
                        timestamp=message.timestamp,
                        run_id=run_id,
                        result_summary="(no tool called - final answer step)",
                        stop_reason=stop_reason,
                    )
                )
            continue
        for part in tool_calls:
            entries.append(
                audit_entry(
                    AuditEventType.TOOL_CALL,
                    timestamp=message.timestamp,
                    run_id=run_id,
                    tool_name=part.tool_name,
                    tool_args=truncate_for_audit(part.args),
                    result_summary=returns.get(part.tool_call_id, "(no return recorded)"),
                    stop_reason=stop_reason,
                )
            )
    return entries


def append_audit_trail(entries: list[AuditEntry], path: Path = AUDIT_TRAIL_PATH) -> None:
    with _audit_lock:
        path.parent.mkdir(parents=True, exist_ok=True)
        history: list[AuditEntry] = []
        if path.is_file():
            try:
                history = TypeAdapter(list[AuditEntry]).validate_python(json.loads(path.read_text()))
            except (json.JSONDecodeError, ValidationError):
                stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                aside = path.with_name(f"audit_trail.unreadable-{stamp}.json")
                path.rename(aside)
                history = [
                    audit_entry(
                        AuditEventType.TRAIL_UNREADABLE,
                        note=f"previous trail was not valid; preserved as {aside.name}",
                    )
                ]
        history.extend(entries)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps([e.model_dump(mode="json") for e in history], indent=2) + "\n")
        os.replace(tmp, path)
