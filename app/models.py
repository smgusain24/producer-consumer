from pydantic import BaseModel
from typing import List
from datetime import datetime

class Item(BaseModel):
    sku: str
    qty: int
    unit_price: float

class OrderRequest(BaseModel):
    vendor_id: str
    order_id: str
    items: List[Item]
    timestamp: datetime
