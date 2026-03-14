"""
Business Logic Layer
Handles order status, refund status, return initiation, and cancellation.
Uses SQLite with mock data for the e-commerce prototype.
"""
import sqlite3
import os
from typing import Optional
from pathlib import Path

from app.core.logger import logger


DB_PATH = Path(__file__).parent.parent.parent / "data" / "ecommerce.db"


def _get_connection():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize the SQLite database with mock data."""
    conn = _get_connection()
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id    TEXT PRIMARY KEY,
            customer    TEXT,
            product     TEXT,
            status      TEXT,  -- processing, shipped, delivered, cancelled
            eta         TEXT,
            amount      REAL,
            created_at  TEXT
        );

        CREATE TABLE IF NOT EXISTS refunds (
            order_id    TEXT PRIMARY KEY,
            status      TEXT,  -- pending, approved, completed, rejected
            amount      REAL,
            reason      TEXT
        );

        CREATE TABLE IF NOT EXISTS returns (
            order_id    TEXT PRIMARY KEY,
            status      TEXT,  -- initiated, picked_up, completed
            reason      TEXT
        );
    """)

    # Insert mock data (ignore if already exists)
    mock_orders = [
        ("ORD001", "Rahul Sharma",  "Bluetooth Headphones", "shipped",    "March 12, 2026", 1299.0, "2026-03-05"),
        ("ORD002", "Priya Verma",   "Running Shoes",        "processing", "March 15, 2026", 2499.0, "2026-03-08"),
        ("ORD003", "Amit Patel",    "Laptop Stand",         "delivered",  "March 01, 2026", 799.0,  "2026-02-25"),
        ("ORD004", "Sneha Jain",    "Yoga Mat",             "cancelled",  None,             599.0,  "2026-03-01"),
        ("ORD005", "Vikram Singh",  "Smart Watch",          "shipped",    "March 14, 2026", 3999.0, "2026-03-06"),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO orders VALUES (?,?,?,?,?,?,?)", mock_orders
    )

    mock_refunds = [
        ("ORD003", "completed", 799.0,  "item damaged"),
        ("ORD004", "approved",  599.0,  "order cancelled"),
        ("ORD005", "pending",   3999.0, "requested by customer"),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO refunds VALUES (?,?,?,?)", mock_refunds
    )

    conn.commit()
    conn.close()
    logger.info("DATABASE_INITIALIZED", db_path=str(DB_PATH))


def get_order_status(order_id: str) -> Optional[dict]:
    try:
        conn = _get_connection()
        row = conn.execute(
            "SELECT * FROM orders WHERE UPPER(order_id) = UPPER(?)", (order_id,)
        ).fetchone()
        conn.close()
        if row:
            return {"order_id": row["order_id"], "status": row["status"],
                    "product": row["product"], "eta": row["eta"] or "N/A",
                    "amount": row["amount"]}
        return None
    except Exception as e:
        logger.error("BL_GET_ORDER_FAILED", order_id=order_id, detail=str(e))
        return None


def get_refund_status(order_id: str) -> Optional[dict]:
    try:
        conn = _get_connection()
        row = conn.execute(
            "SELECT * FROM refunds WHERE UPPER(order_id) = UPPER(?)", (order_id,)
        ).fetchone()
        conn.close()
        if row:
            return {"order_id": row["order_id"], "status": row["status"],
                    "amount": row["amount"]}
        # Check if order exists but no refund
        order = get_order_status(order_id)
        if order:
            return {"order_id": order_id, "status": "pending", "amount": order["amount"]}
        return None
    except Exception as e:
        logger.error("BL_GET_REFUND_FAILED", order_id=order_id, detail=str(e))
        return None


def initiate_return(order_id: str) -> dict:
    try:
        conn = _get_connection()

        # Check if order exists and is delivered
        order = conn.execute(
            "SELECT * FROM orders WHERE UPPER(order_id) = UPPER(?)", (order_id,)
        ).fetchone()

        if not order:
            conn.close()
            return {"status": "not_found"}

        if order["status"] not in ("delivered",):
            conn.close()
            return {"status": "not_eligible"}

        # Check if return already exists
        existing = conn.execute(
            "SELECT * FROM returns WHERE UPPER(order_id) = UPPER(?)", (order_id,)
        ).fetchone()

        if existing:
            conn.close()
            return {"status": "already_exists"}

        conn.execute(
            "INSERT INTO returns VALUES (?, ?, ?)",
            (order["order_id"], "initiated", "customer_request")
        )
        conn.commit()
        conn.close()
        return {"status": "initiated"}
    except Exception as e:
        logger.error("BL_RETURN_FAILED", order_id=order_id, detail=str(e))
        return {"status": "error"}


def cancel_order(order_id: str) -> dict:
    try:
        conn = _get_connection()
        order = conn.execute(
            "SELECT * FROM orders WHERE UPPER(order_id) = UPPER(?)", (order_id,)
        ).fetchone()

        if not order:
            conn.close()
            return {"status": "not_found"}

        if order["status"] in ("shipped", "delivered"):
            conn.close()
            return {"status": "already_shipped"}

        conn.execute(
            "UPDATE orders SET status = 'cancelled' WHERE UPPER(order_id) = UPPER(?)",
            (order_id,)
        )
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        logger.error("BL_CANCEL_FAILED", order_id=order_id, detail=str(e))
        return {"status": "error"}


def execute_intent(intent: str, order_id: str) -> dict:
    """Route business logic call based on intent."""
    init_db()
    if intent == "check_order_status":
        result = get_order_status(order_id)
        return result if result else {"status": "not_found"}
    elif intent == "check_refund_status":
        result = get_refund_status(order_id)
        return result if result else {"status": "not_found"}
    elif intent == "initiate_return":
        return initiate_return(order_id)
    elif intent == "cancel_order":
        return cancel_order(order_id)
    else:
        return {"status": "error", "message": "Unknown business intent"}
