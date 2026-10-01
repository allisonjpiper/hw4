"""Campus Customs backend: serves product/inventory data and product images."""

import sqlite3
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr

from security import hash_password, password_strength_errors, verify_password

from agent import run_chat
from models import PageContext
from tools import get_customer_context, load_full_history, load_recent_history, save_chat_message

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"  # local-only data pack, not committed to git
DB_PATH = DATA_DIR / "campus_customs.db"
PRODUCTS_DIR = DATA_DIR / "products"

app = FastAPI(title="Campus Customs API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/media/products", StaticFiles(directory=PRODUCTS_DIR), name="product-images")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def image_url_for(image_file_path: str) -> str:
    filename = Path(image_file_path).name
    return f"/media/products/{filename}"


@app.get("/api/products")
def list_products():
    conn = get_connection()
    # campus_customs.db has no orders/sales-history table, so there's no real
    # "units sold" figure. As a documented stand-in for "best sellers first"
    # (Problem 10), we rank by total remaining stock ascending - the
    # assumption being that similar starting stock plus lower stock left means
    # more has already sold. This is a proxy, not a real sales count.
    rows = conn.execute(
        """
        SELECT catalogue.*, COALESCE(SUM(inventory.quantity), 0) AS total_stock
        FROM catalogue
        LEFT JOIN inventory ON inventory.product_id = catalogue.product_id
        GROUP BY catalogue.product_id
        ORDER BY total_stock ASC, catalogue.name ASC
        """
    ).fetchall()
    conn.close()

    products = []
    for row in rows:
        products.append(
            {
                "product_id": row["product_id"],
                "name": row["name"],
                "garment_type": row["garment_type"],
                "description": row["description"],
                "colors": _parse_json_list(row["colors"]),
                "price": row["price"],
                "image_url": image_url_for(row["image_file_path"]),
            }
        )
    return products


@app.get("/api/products/{product_id}")
def get_product(product_id: str):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM catalogue WHERE product_id = ?", (product_id,)
    ).fetchone()
    if row is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Product not found")

    inventory_rows = conn.execute(
        "SELECT size, quantity FROM inventory WHERE product_id = ?", (product_id,)
    ).fetchall()
    conn.close()

    return {
        "product_id": row["product_id"],
        "name": row["name"],
        "garment_type": row["garment_type"],
        "description": row["description"],
        "colors": _parse_json_list(row["colors"]),
        "search_tags": _parse_json_list(row["search_tags"]),
        "price": row["price"],
        "image_url": image_url_for(row["image_file_path"]),
        "inventory": [
            {"size": inv["size"], "quantity": inv["quantity"]} for inv in inventory_rows
        ],
    }


def _parse_json_list(value: str) -> list[str]:
    import json

    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return []


class CreateAccountRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    confirm_password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


def _user_public(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "first_name": row["first_name"],
        "last_name": row["last_name"],
        "name": row["name"],
        "email": row["email"],
    }


@app.post("/api/auth/register")
def register(body: CreateAccountRequest):
    if body.password != body.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match.")

    errors = password_strength_errors(body.password)
    if errors:
        raise HTTPException(status_code=400, detail=" ".join(errors))

    conn = get_connection()
    existing = conn.execute(
        "SELECT id FROM users WHERE email = ?", (body.email,)
    ).fetchone()
    if existing is not None:
        conn.close()
        raise HTTPException(status_code=400, detail="An account with this email already exists.")

    password_hash = hash_password(body.password)
    full_name = f"{body.first_name} {body.last_name}"
    cursor = conn.execute(
        """
        INSERT INTO users (name, email, password_hash, first_name, last_name)
        VALUES (?, ?, ?, ?, ?)
        """,
        (full_name, body.email, password_hash, body.first_name, body.last_name),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)).fetchone()
    conn.close()

    return _user_public(row)


@app.post("/api/auth/login")
def login(body: LoginRequest):
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE email = ?", (body.email,)).fetchone()
    conn.close()

    if row is None or not verify_password(body.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    return _user_public(row)


class ChatRequest(BaseModel):
    message: str
    user_id: int | None = None
    page_context: PageContext | None = None


@app.post("/api/chat")
def chat(body: ChatRequest):
    message = body.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    # Customer identity is looked up server-side from user_id - never trusted
    # from anything the client claims about who they are.
    customer = get_customer_context(body.user_id) if body.user_id is not None else None
    history = load_recent_history(body.user_id) if body.user_id is not None else []
    audit_customer = f"user:{body.user_id}" if body.user_id is not None else "guest"
    reply = run_chat(
        message, history, customer=customer, page_context=body.page_context, audit_customer=audit_customer
    )

    # chat_messages.user_id is NOT NULL, so only persist for a logged-in customer.
    if body.user_id is not None:
        save_chat_message(body.user_id, "user", message, [])
        save_chat_message(body.user_id, "assistant", reply.reply, reply.products)

    return reply


@app.get("/api/chat/history/{user_id}")
def chat_history(user_id: int):
    """Reload a logged-in customer's saved chat history (Problem 8). Guests never call this."""
    return load_full_history(user_id)
