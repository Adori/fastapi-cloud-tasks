import logging

from examples.full.serializer import Payload
from examples.full.settings import (
    SCHEDULER_OIDC_TOKEN,
    TASK_LISTENER_BASE_URL,
    TASK_OIDC_TOKEN,
    TASK_QUEUE_PATH,
)
from fastapi import FastAPI
from fastapi.routing import APIRouter
from fastapi_cloud_tasks.hooks import (
    chained_hook,
    deadline_scheduler_hook,
    deadline_task_hook,
    oidc_scheduler_hook,
    oidc_task_hook,
)
from fastapi_cloud_tasks.taskroute import TaskRouteBuilder
from google.protobuf import duration_pb2

app = FastAPI()


logger = logging.getLogger("uvicorn")

TaskRoute = TaskRouteBuilder(
    base_url=TASK_LISTENER_BASE_URL,
    queue_path=TASK_QUEUE_PATH,
    # Chain multiple hooks together
    pre_create_hook=chained_hook(
        # Add service account for cloud run
        oidc_task_hook(
            token=TASK_OIDC_TOKEN,
        ),
        # Wait for half an hour
        deadline_task_hook(duration=duration_pb2.Duration(seconds=1800)),
    ),
    pre_scheduler_hook=chained_hook(
        # Add service account for cloud run
        oidc_scheduler_hook(
            token=SCHEDULER_OIDC_TOKEN,
        ),
        # Wait for half an hour
        deadline_scheduler_hook(duration=duration_pb2.Duration(seconds=1800)),
    ),
)

router = APIRouter(route_class=TaskRoute, prefix="/tasks")


@router.post("/hello")
async def hello(p: Payload = Payload(message="Default")):
    message = f"Hello task ran with payload: {p.message}"
    logger.warning(message)
    return {"message": message}


@router.post("/timed_hello")
async def scheduled_hello(p: Payload = Payload(message="Default")):
    message = f"Scheduled hello task ran with payload: {p.message}"
    logger.warning(message)
    return {"message": message}


scheduled_hello.scheduler(
    name="testing-examples-scheduled-hello",
    schedule="*/5 * * * *",
    time_zone="Asia/Kolkata",
).schedule(p=Payload(message="Scheduled"))

app.include_router(router)
