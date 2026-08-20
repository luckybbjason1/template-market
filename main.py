"""
Template Market - 模板销售平台
出售设计模板、代码模板、文档模板
"""

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
from pathlib import Path
from datetime import datetime

app = FastAPI(title="Template Market", version="1.0.0")

class Template(BaseModel):
    id: int
    name: str
    category: str
    price: float
    description: str
    downloads: int = 0
    rating: float = 5.0

class Purchase(BaseModel):
    template_id: int
    email: str
    payment_method: str

templates_db = Path.home() / "桌面" / "template-market" / "templates.db"
templates_db.parent.mkdir(exist_ok=True)

def init_db():
    conn = sqlite3.connect(templates_db)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT,
            file_path TEXT,
            downloads INTEGER DEFAULT 0,
            rating REAL DEFAULT 5.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_id INTEGER,
            email TEXT NOT NULL,
            amount REAL NOT NULL,
            payment_method TEXT,
            purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.get("/")
async def root():
    return {"message": "Template Market - 自动赚钱平台", "version": "1.0.0"}

@app.get("/templates")
async def get_templates(category: Optional[str] = None):
    conn = sqlite3.connect(templates_db)
    cursor = conn.cursor()
    if category:
        cursor.execute("SELECT * FROM templates WHERE category = ?", (category,))
    else:
        cursor.execute("SELECT * FROM templates")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.post("/purchase")
async def purchase_template(purchase: Purchase):
    conn = sqlite3.connect(templates_db)
    cursor = conn.cursor()
    cursor.execute("SELECT price, name FROM templates WHERE id = ?", (purchase.template_id,))
    template = cursor.fetchone()
    if not template:
        conn.close()
        return {"error": "Template not found"}
    cursor.execute(
        "INSERT INTO purchases (template_id, email, amount, payment_method) VALUES (?, ?, ?, ?)",
        (purchase.template_id, purchase.email, template[0], purchase.payment_method)
    )
    cursor.execute("UPDATE templates SET downloads = downloads + 1 WHERE id = ?", (purchase.template_id,))
    conn.commit()
    conn.close()
    return {"message": "Purchase successful", "template": template[1], "amount": template[0]}

@app.get("/stats")
async def get_stats():
    conn = sqlite3.connect(templates_db)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM templates")
    total_templates = cursor.fetchone()[0]
    cursor.execute("SELECT SUM(amount) FROM purchases")
    total_revenue = cursor.fetchone()[0] or 0
    cursor.execute("SELECT COUNT(*) FROM purchases")
    total_sales = cursor.fetchone()[0]
    conn.close()
    return {
        "total_templates": total_templates,
        "total_revenue": total_revenue,
        "total_sales": total_sales,
        "avg_order_value": total_revenue / total_sales if total_sales > 0 else 0
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
