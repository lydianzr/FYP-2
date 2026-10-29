# modules/index/structured.py
import os
import sqlite3
from typing import Dict, Any, List, Optional

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SQLITE_DB_PATH = os.path.join(PROJECT_ROOT, "data", "logistics.db")


class StructuredIndex:
    """SQLite relational store for exact metadata filtering and SQL aggregation."""

    def __init__(self, db_path: str = SQLITE_DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    document_id TEXT PRIMARY KEY,
                    document_type TEXT,
                    supplier_name TEXT,
                    receiver_name TEXT,
                    date TEXT,
                    total_amount REAL,
                    tax_amount REAL,
                    currency TEXT,
                    payment_terms TEXT,
                    po_number TEXT,
                    has_signature INTEGER,
                    has_stamp INTEGER,
                    raw_json TEXT
                )
            """)
            conn.commit()

    def insert_document(self, schema_dict: Dict[str, Any]):
        doc_id = str(schema_dict.get("document_id") or "doc_unknown")
        import json
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO documents VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc_id,
                schema_dict.get("document_type", "Invoice"),
                schema_dict.get("supplier_name", ""),
                schema_dict.get("receiver_name", ""),
                schema_dict.get("date", ""),
                float(schema_dict.get("total_amount") or 0.0),
                float(schema_dict.get("tax_amount") or 0.0),
                schema_dict.get("currency", "USD"),
                schema_dict.get("payment_terms", ""),
                schema_dict.get("po_number", ""),
                1 if schema_dict.get("has_signature") else 0,
                1 if schema_dict.get("has_stamp") else 0,
                json.dumps(schema_dict)
            ))
            conn.commit()

    def filter_documents(self, supplier: Optional[str] = None, min_amount: Optional[float] = None) -> List[Dict[str, Any]]:
        query = "SELECT document_id, supplier_name, total_amount, date FROM documents WHERE 1=1"
        params = []
        if supplier:
            query += " AND supplier_name LIKE ?"
            params.append(f"%{supplier}%")
        if min_amount is not None:
            query += " AND total_amount >= ?"
            params.append(min_amount)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def aggregate_sum(self, column: str = "total_amount", supplier: Optional[str] = None) -> float:
        query = f"SELECT SUM({column}) FROM documents WHERE 1=1"
        params = []
        if supplier:
            query += " AND supplier_name LIKE ?"
            params.append(f"%{supplier}%")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            res = cursor.fetchone()[0]
            return float(res) if res is not None else 0.0