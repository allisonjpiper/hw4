"""
agent.py

PydanticAI entry point for the Campus Customs shop chatbot.

The agent answers product questions (search, description, price, per-size
stock - Problems 5 & 6) and account questions, using the system prompt in
prompts/prompt.md and the tools in tools.py. Structured output lives in
models.py so replies carry both text and product cards with a consistent
shape across the chat widget and the shop page.

Requires:
    pip install -r requirements.txt
    PORTKEY_API_KEY in the root .env file (see AGENTS.md)
"""

from __future__ import annotations

import os

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

import uuid
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from pydantic_ai import Agent, RunContext
from pydantic_ai.exceptions import UsageLimitExceeded
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.usage import UsageLimits

import tools
from models import AuditEventType, ChatReply, ChatTurn, CustomerContext, PageContext

HERE = Path(__file__).resolve().parent
load_dotenv(HERE.parent / ".env")  # hw4/.env, copied from .env.example
load_dotenv(find_dotenv())  # otherwise the nearest .env above this file

MODEL_NAME = os.environ.get("MODEL", "gpt-5.6-luna")
PORTKEY_BASE_URL = "https://api.portkey.ai/v1"
SYSTEM_PROMPT_PATH = HERE / "prompts" / "prompt.md"

# A chat turn needs at most a couple of tool calls (search/lookup) plus a final
# structured reply. These ceilings stop a runaway loop without cutting off a
# normal conversation.
MAX_REQUESTS_PER_RUN = 8
MAX_TOOL_CALLS_PER_RUN = 6
OUTPUT_RETRIES = 2

USAGE_LIMITS = UsageLimits(
    request_limit=MAX_REQUESTS_PER_RUN,
    tool_calls_limit=MAX_TOOL_CALLS_PER_RUN,
)


def build_model() -> OpenAIChatModel:
    """Portkey-backed model, per the project's AGENTS.md instructions."""
    api_key = os.getenv("PORTKEY_API_KEY")
    if not api_key:
        raise RuntimeError("PORTKEY_API_KEY is missing from the root .env file.")
    return OpenAIChatModel(
        MODEL_NAME, provider=OpenAIProvider(api_key=api_key, base_url=PORTKEY_BASE_URL)
    )


def build_agent() -> Agent[None, ChatReply]:
    model = build_model()
    agent = Agent(
        model,
        output_type=ChatReply,
        system_prompt=SYSTEM_PROMPT_PATH.read_text(),
        retries=OUTPUT_RETRIES,
    )

    @agent.tool
    def search_products(ctx: RunContext[None], query: str) -> list[dict]:
        """Search the catalogue for products matching a loose keyword query (name, garment type, color, tags)."""
        return [card.model_dump() for card in tools.search_products(query)]

    @agent.tool
    def product_lookup(ctx: RunContext[None], product_id: str) -> dict:
        """Look up one product's real description, price, and per-size stock by its product_id. Never guess these values yourself."""
        return tools.product_lookup(product_id).model_dump()

    @agent.tool
    def find_product_ids_by_name(ctx: RunContext[None], name_fragment: str) -> list[str]:
        """Resolve a product name a customer typed into matching product_id(s) to pass to product_lookup."""
        return tools.find_product_ids_by_name(name_fragment)

    @agent.tool
    def product_info_from_message(ctx: RunContext[None], customer_message: str) -> list[dict]:
        """Given the customer's own chat message (a full sentence, not a keyword), return full real product info - description, price, per-size stock - for whatever it matches, in one call."""
        return [result.model_dump() for result in tools.product_info_from_message(customer_message)]

    @agent.tool
    def list_categories(ctx: RunContext[None]) -> list[str]:
        """List the product categories actually in the catalogue (e.g. Hoodie, Crewneck, T-Shirt, Quarter-Zip, Outerwear, Long Sleeve)."""
        return tools.list_categories()

    @agent.tool
    def search_products_by_category(ctx: RunContext[None], category: str) -> list[dict]:
        """When the customer names a garment type (hoodie, t-shirt, crewneck, quarter-zip, jacket, long sleeve), call this first - it's a faster, more precise category lookup than search_products."""
        return [card.model_dump() for card in tools.search_products_by_category(category)]

    return agent


def run_chat(
    message: str,
    history: list[ChatTurn] | None = None,
    customer: CustomerContext | None = None,
    page_context: PageContext | None = None,
    audit_customer: str = "guest",
) -> ChatReply:
    """
    Run one turn of the shop chatbot and return its structured reply.

    `customer` and `page_context` are looked up/read server-side (never taken
    from the model's own guess) and passed in as plain context lines ahead of
    the conversation, so the agent reliably sees them on every turn rather
    than only when it happens to call a tool for them.
    """
    agent = build_agent()

    parts = []
    if customer is not None:
        parts.append(f"You are talking with: {customer.name} ({customer.email}). You may use their first name.")
    else:
        parts.append("This customer is a guest - not logged in. Do not address them by name.")

    if page_context is not None:
        if page_context.product_id:
            parts.append(
                f"The customer is currently looking at this product page: "
                f"'{page_context.product_name}' (product_id={page_context.product_id}). "
                "If they ask a context-free question (e.g. 'is this in pink?', 'do you have this in stock?'), "
                "assume they mean this product - resolve it with product_lookup, don't ask them to repeat the name."
            )
        else:
            parts.append(f"The customer is currently on the site's '{page_context.path}' page (not a specific product).")

    if history:
        convo = "\n".join(f"{turn.role}: {turn.content}" for turn in history)
        parts.append(f"Recent conversation so far:\n{convo}")

    parts.append(f"New customer message: {message}")

    run_id = uuid.uuid4().hex[:12]
    tools.append_audit_trail(
        [tools.audit_entry(AuditEventType.RUN_STARTED, run_id=run_id, model=MODEL_NAME, customer=audit_customer)]
    )
    try:
        result = agent.run_sync("\n\n".join(parts), usage_limits=USAGE_LIMITS)
    except Exception as exc:
        tools.append_audit_trail(
            [
                tools.audit_entry(
                    AuditEventType.RUN_STOPPED,
                    run_id=run_id,
                    status="failed",
                    stop_reason="usage limit reached" if isinstance(exc, UsageLimitExceeded) else "error during run",
                    error=tools.truncate_for_audit(str(exc)),
                )
            ]
        )
        raise

    entries = tools.iteration_audit_entries(result.all_messages(), run_id)
    entries.append(
        tools.audit_entry(
            AuditEventType.RUN_STOPPED,
            run_id=run_id,
            status="completed",
            stop_reason="final structured reply produced",
            note=f"{len(result.output.products)} product card(s) returned",
        )
    )
    tools.append_audit_trail(entries)
    return result.output


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Chat with the Campus Customs shop agent from the command line.")
    parser.add_argument("message")
    args = parser.parse_args()
    print(run_chat(args.message).model_dump_json(indent=2))
