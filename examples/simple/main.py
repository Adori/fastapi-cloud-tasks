import logging
import os

from fastapi import FastAPI
from fastapi.routing import APIRouter
from fastapi_cloud_tasks.taskroute import TaskRouteBuilder
from fastapi_cloud_tasks.utils import queue_path
from pydantic import BaseModel

TaskRoute = TaskRouteBuilder(
    # Base URL where the task server will get hosted
    base_url=os.getenv("TASK_LISTENER_BASE_URL", default="https://6045-49-207-221-153.ngrok.io"),
    # Full queue path to which we'll send tasks.
    # Edit values below to match your project
    queue_path=queue_path(
        project=os.getenv("TASK_PROJECT_ID", default="gcp-project-id"),
        location=os.getenv("TASK_LOCATION", default="asia-south1"),
        queue=os.getenv("TASK_QUEUE", default="test-queue"),
    ),
)

task_router = APIRouter(route_class=TaskRoute, prefix="/tasks")

logger = logging.getLogger("uvicorn")


class Payload(BaseModel):
    message: str


@task_router.post("/hello")
async def hello(p: Payload = Payload(message="Default")):
    logger.warning(f"Hello task ran with payload: {p.message}")


app = FastAPI()


@app.get("/trigger")
async def trigger():
    hello.delay(p=Payload(message="Triggered task"))
    return {"message": "Basic hello task triggered"}


app.include_router(task_router)
