"""
All Pydantic / PydanticAI structured types for the Campus Customs shop chatbot.

Contents:
  - ProductCard: a lightweight, branding-consistent product summary used both by
    the agent's structured replies and by the shop frontend.
  - SizeStock / ProductLookupResult: real description, price, and per-size stock
    for one product, pulled straight from campus_customs.db (Problem 6's product
    info + stock tool) - never invented by the model.
  - ChatTurn: one role/content turn, used to give the agent short-term memory.
  - ChatReply: the agent's structured output - the reply text plus any product
    cards to render alongside it in the chat widget.
  - CustomerContext: the logged-in customer's name/email, so the agent knows
    who it's talking to (Problem 8).
  - PageContext: which page/product the customer is currently looking at, so
    a context-free question ("is this in pink?") resolves correctly (Problem 8).
  - ChatHistoryMessage: one saved turn returned to the frontend when a
    returning customer's chat history is reloaded (Problem 8).
  - AuditEventType / AuditEntry: one record in output/audit_trail.json
    (Problem 12).
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ProductCard(BaseModel):
    """Branding-consistent product summary shown in chat replies and the shop UI."""

    product_id: str
    name: str
    price: float
    image_url: str
    colors: list[str] = Field(default_factory=list)
    garment_type: str


class SizeStock(BaseModel):
    """Stock for one size of one product."""

    size: str
    quantity: int
    in_stock: bool


class ProductLookupResult(BaseModel):
    """
    Full answer to "tell me about this product": real description, price, and
    per-size stock pulled straight from campus_customs.db. `found=False` means
    the tool could not locate this product at all, in which case the other
    fields are left empty/null and the agent must say so rather than guess.
    """

    found: bool
    product_id: str
    name: str | None = None
    description: str | None = None
    price: float | None = None
    colors: list[str] = Field(default_factory=list)
    image_url: str | None = None
    sizes: list[SizeStock] = Field(default_factory=list)


class ChatTurn(BaseModel):
    """One turn of prior conversation, used to give the agent short-term memory."""

    role: str
    content: str


class ChatReply(BaseModel):
    """
    Structured output of the shop chatbot agent: the natural-language reply,
    plus any product cards to render alongside it (mirrors the products_json
    the seed chat_messages already store, so the branding stays consistent
    between the chatbot and the Products page).
    """

    reply: str = Field(..., description="The assistant's reply to the customer, in markdown")
    products: list[ProductCard] = Field(
        default_factory=list,
        description="Product cards to display under the reply, if any products are relevant",
    )


class CustomerContext(BaseModel):
    """Who the agent is talking to, for a logged-in customer. Never guessed by the model."""

    name: str
    email: str


class PageContext(BaseModel):
    """
    Which page (and, if applicable, which product) the customer is currently
    looking at in the site, so a context-free question like "is this in pink?"
    resolves to the right product without the customer having to repeat it.
    """

    path: str
    product_id: str | None = None
    product_name: str | None = None


class ChatHistoryMessage(BaseModel):
    """One saved turn, returned to the frontend so a returning customer's chat reloads."""

    role: str
    content: str
    products: list[ProductCard] = Field(default_factory=list)


class AuditEventType(str, Enum):
    RUN_STARTED = "run_started"
    TOOL_CALL = "tool_call"
    RUN_STOPPED = "run_stopped"
    TRAIL_UNREADABLE = "audit_trail_unreadable"


class AuditEntry(BaseModel):
    """
    One record in output/audit_trail.json. Every record has this same shape so
    the trail is a uniform, machine-checkable list; fields that don't apply to
    an event stay null. extra="forbid" makes a typo'd field fail loudly instead
    of silently writing a malformed record.
    """

    model_config = ConfigDict(extra="forbid")

    timestamp: datetime = Field(..., description="UTC time this record was created")
    event: AuditEventType
    run_id: str | None = Field(default=None, description="Groups every record from one chat turn")
    model: str | None = None
    customer: str | None = Field(
        default=None, description="'user:<id>' or 'guest' - never a name or email"
    )
    tool_name: str | None = None
    tool_args: str | None = Field(default=None, description="Truncated tool arguments")
    result_summary: str | None = Field(default=None, description="Truncated tool result")
    stop_reason: str | None = Field(
        default=None, description="Model finish_reason for a step, or why the run ended"
    )
    status: str | None = Field(default=None, description="'completed' or 'failed' on run_stopped")
    error: str | None = None
    note: str | None = None
