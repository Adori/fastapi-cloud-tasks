# Standard Library Imports
import logging
import os

# Third Party Imports
from fastapi import FastAPI
from fastapi.routing import APIRouter
from pydantic import BaseModel

# Imports from this repository
from fastapi_cloud_tasks import DelayedRouteBuilder
from fastapi_cloud_tasks.utils import emulator_client
from fastapi_cloud_tasks.utils import queue_path

# set env var IS_LOCAL=false for your deployment environment
IS_LOCAL = os.getenv("IS_LOCAL", "true").lower() == "true"

client = None
if IS_LOCAL:
    client = emulator_client()


DelayedRoute = DelayedRouteBuilder(
    client=client,
    # Base URL where the task server will get hosted
    base_url=os.getenv("TASK_LISTENER_BASE_URL", default="http://localhost:8000"),
    # Full queue path to which we'll send tasks.
    # Edit values below to match your project
    queue_path=queue_path(
        project=os.getenv("TASK_PROJECT_ID", default="gcp-project-id"),
        location=os.getenv("TASK_LOCATION", default="asia-south1"),
        queue=os.getenv("TASK_QUEUE", default="test-queue"),
    ),
)

delayed_router = APIRouter(route_class=DelayedRoute, prefix="/delayed")

logger = logging.getLogger("uvicorn")


class Payload(BaseModel):
    message: str


@delayed_router.post("/hello")
async def hello(
    p: Payload = Payload(message="Default"),
):
    logger.warning(f"Hello task ran with payload: {p.message}")


app = FastAPI()


@app.get("/trigger")
async def trigger():
    hello.delay(p=Payload(message="Triggered task"))
    return {"message": "Basic hello task triggered"}


app.include_router(delayed_router)
