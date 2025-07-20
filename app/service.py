import asyncio
import json
import logging
import os
import uuid
from collections import defaultdict
from datetime import datetime, timedelta

import redis.asyncio as redis
from fastapi import Depends, Header
from fastapi.requests import Request
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from app.database import get_db
from app.database.db import SessionLocal
from app.database.models import Order, OrderItem
from app.models import OrderRequest


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

redis_client = redis.from_url(REDIS_URL, decode_responses=True)

STREAM_NAME = "EVENT"
STREAM_COUNT = 1
STREAM_BLOCK = 5000

API_TOKEN = os.getenv("API_TOKEN", "074e35bc-0e9c-4ce4-a960-3eeafa3bb30c")


def flatten_object(obj):
    return {
        key: json.dumps(val) if isinstance(val, (dict, list)) else str(val)
        for key, val in obj.items()
    }


def verify_token(x_api_key: str = Header(..., alias="X-API-KEY")):
    if x_api_key != API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token",
        )


async def submit_event(request: Request,  _: None = Depends(verify_token)):
    """
        Producer: Publishes incoming event to message queue.
    """
    try:
        request_json = await request.json()
        logging.info(f"Request Payload:\n{request_json}")


        task_request = OrderRequest(**request_json)
        task = task_request.model_dump()
        task_id = str(uuid.uuid4())
        task.update({"taskID": task_id})
        logging.info(f"TASK: {task}")

        # Flatten task because redis stream does not support nested objects
        flatten_task = flatten_object(task)
        _id = await redis_client.xadd(name=STREAM_NAME, fields=flatten_task)
        return {"status": "success", "_id": _id}
    except Exception as e:
        logging.error(e, exc_info=True)
        return {"status": "failure", "_id": None}


async def get_vendor_metrics(request: Request, db: Session = Depends(get_db), _: None = Depends(verify_token)):
    """
        Get vendor metrics
    """
    try:
        vendor_id = request.query_params.get("vendor_id")
        orders = db.query(Order).filter(Order.vendor_id == vendor_id).all()

        if not orders:
            return JSONResponse(content={"message": "Invalid Request"}, status_code=400)

        total_orders = len(orders)
        total_revenue = 0
        high_value_orders = 0
        today = datetime.now().date()
        last_7_days_volume = defaultdict(int)

        for order in orders:
            total_revenue += order.total_amount

            # If high value order
            if order.high_value:
                high_value_orders += 1

            order_date = order.timestamp.date()

            # If order was made in last 7 days
            if today - timedelta(days=6) <= order_date <= today:
                for item in order.items:
                    last_7_days_volume[order_date.isoformat()] += int(item.qty)

        last_week_volume = {}
        for i in range(7):
            date_str = (today - timedelta(days=i)).isoformat()
            last_week_volume[date_str] = last_7_days_volume.get(date_str, 0)

        return {
            "vendor_id": vendor_id,
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "high_value_orders": high_value_orders,
            "last_7_days_volume": last_week_volume
        }

    except Exception as e:
        logging.error(e, exc_info=True)
        return JSONResponse(content={"error": str(e)}, status_code=500)


def process_data(data):
    """
        Process total amount and high value flag.
    """

    db = SessionLocal()
    items = json.loads(data["items"])
    total_amount = float(sum([item["qty"] * item["unit_price"] for item in items]))
    high_value = total_amount > 500

    order_timestamp = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))

    # Create order object
    order = Order(
        order_id=data["order_id"],
        vendor_id=data["vendor_id"],
        timestamp=order_timestamp,
        total_amount=total_amount,
        high_value=high_value,
    )

    # Create nested items object
    order.items = [
        OrderItem(sku=item["sku"], qty=item["qty"], unit_price=item["unit_price"])
        for item in items
    ]

    # Verify if OrderID already exists
    existing = db.query(Order).filter_by(order_id=data["order_id"]).first()
    if not existing:
        # Add order
        db.add(order)
        db.commit()
    else:
        print(f"Order '{data['order_id']}' already exists. Skipping.")


async def consume_event():
    try:
        logging.info("Consumer started")

        # Consume future event
        last_id = "$"
        while True:
            logging.info("Polling Redis...")
            result = await redis_client.xread(
                streams={STREAM_NAME: last_id}, count=STREAM_COUNT, block=STREAM_BLOCK
            )
            if result:
                for stream, messages in result:
                    for message_id, data in messages:
                        logging.info(f"Consumed message: id={message_id}, data={data}")
                        process_data(data)
                        last_id = message_id

            # Time buffer to avoid CPU hogging
            await asyncio.sleep(0.1)
    except Exception as e:
        logging.error(e, exc_info=True)
