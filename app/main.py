import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.service import consume_event, submit_event, get_vendor_metrics, get_vendor_chart

app = FastAPI(docs_url="/docs")

app.post("/events")(submit_event)
app.get("/metrics")(get_vendor_metrics)
app.get('/metrics/chart')(get_vendor_chart)



@asynccontextmanager
async def lifespan(app: FastAPI):
    consumer_task = asyncio.create_task(consume_event())
    yield
    consumer_task.cancel()


app.router.lifespan_context = lifespan

