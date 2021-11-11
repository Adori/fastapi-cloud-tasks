import logging

from examples.full.serializer import Payload
from examples.full.settings import TASK_LISTENER_BASE_URL, TASK_OIDC_TOKEN, TASK_QUEUE_PATH
from fastapi import FastAPI
from fastapi.routing import APIRouter
from gelery.hooks import chained_hook, deadline_hook, oidc_hook
from gelery.taskroute import TaskRouteBuilder
from google.protobuf import duration_pb2

app = FastAPI()


logger = logging.getLogger("uvicorn")

TaskRoute = TaskRouteBuilder(
    base_url=TASK_LISTENER_BASE_URL,
    queue_path=TASK_QUEUE_PATH,
    # Chain multiple hooks together
    pre_create_hook=chained_hook(
        # Add service account for cloud run
        oidc_hook(
            token=TASK_OIDC_TOKEN,
        ),
        # Wait for half an hour
        deadline_hook(duration=duration_pb2.Duration(seconds=1800)),
    ),
)

router = APIRouter(route_class=TaskRoute, prefix="/tasks")


@router.post("/hello")
async def hello(p: Payload = Payload(message="Default")):
    message = f"Hello task ran with payload: {p.message}"
    logger.warning(message)
    return {"message": message}


app.include_router(router)
