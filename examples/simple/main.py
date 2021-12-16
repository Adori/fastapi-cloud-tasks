# Standard Library Imports
import logging
import os
import typing

# Third Party Imports
from fastapi import FastAPI
from fastapi.params import Header
from fastapi.routing import APIRouter
from pydantic import BaseModel

# Imports from this repository
from fastapi_cloud_tasks.taskroute import TaskRouteBuilder
from fastapi_cloud_tasks.utils import queue_path

TaskRoute = TaskRouteBuilder(
    # Base URL where the task server will get hosted
    base_url=os.getenv(
        "TASK_LISTENER_BASE_URL", default="https://d860-35-208-83-220.ngrok.io"
    ),
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
async def hello(
    p: Payload = Payload(message="Default"),
    x_cloudtasks_taskretrycount: typing.Optional[int] = Header(0),
):
    if x_cloudtasks_taskretrycount < 5:
        raise Exception("Noooo")
    logger.warning(f"Hello task ran with payload: {p.message}")


app = FastAPI()


@app.get("/trigger")
async def trigger():
    hello.delay(p=Payload(message="Triggered task"))
    return {"message": "Basic hello task triggered"}


app.include_router(task_router)
