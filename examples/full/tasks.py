# Standard Library Imports
import logging

# Third Party Imports
from fastapi import Depends
from fastapi import FastAPI
from fastapi.routing import APIRouter
from google.protobuf import duration_pb2

# Imports from this repository
from examples.full.serializer import Payload
from examples.full.settings import CLOUD_TASKS_EMULATOR_URL
from examples.full.settings import IS_LOCAL
from examples.full.settings import SCHEDULED_LOCATION_PATH
from examples.full.settings import SCHEDULED_OIDC_TOKEN
from examples.full.settings import TASK_LISTENER_BASE_URL
from examples.full.settings import TASK_OIDC_TOKEN
from examples.full.settings import TASK_QUEUE_PATH
from fastapi_cloud_tasks import DelayedRouteBuilder
from fastapi_cloud_tasks.dependencies import CloudTasksHeaders
from fastapi_cloud_tasks.dependencies import max_retries
from fastapi_cloud_tasks.hooks import chained_hook
from fastapi_cloud_tasks.hooks import deadline_delayed_hook
from fastapi_cloud_tasks.hooks import deadline_scheduled_hook
from fastapi_cloud_tasks.hooks import oidc_delayed_hook
from fastapi_cloud_tasks.hooks import oidc_scheduled_hook
from fastapi_cloud_tasks.scheduled_route import ScheduledRouteBuilder
from fastapi_cloud_tasks.utils import emulator_client

app = FastAPI()


logger = logging.getLogger("uvicorn")

delayed_client = None
if IS_LOCAL:
    delayed_client = emulator_client(host=CLOUD_TASKS_EMULATOR_URL)

DelayedRoute = DelayedRouteBuilder(
    client=delayed_client,
    base_url=TASK_LISTENER_BASE_URL,
    queue_path=TASK_QUEUE_PATH,
    # Chain multiple hooks together
    pre_create_hook=chained_hook(
        # Add service account for cloud run
        oidc_delayed_hook(
            token=TASK_OIDC_TOKEN,
        ),
        # Wait for half an hour
        deadline_delayed_hook(duration=duration_pb2.Duration(seconds=1800)),
    ),
)

ScheduledRoute = ScheduledRouteBuilder(
    base_url=TASK_LISTENER_BASE_URL,
    location_path=SCHEDULED_LOCATION_PATH,
    pre_create_hook=chained_hook(
        # Add service account for cloud run
        oidc_scheduled_hook(
            token=SCHEDULED_OIDC_TOKEN,
        ),
        # Wait for half an hour
        deadline_scheduled_hook(duration=duration_pb2.Duration(seconds=1800)),
    ),
)

delayed_router = APIRouter(route_class=DelayedRoute, prefix="/delayed")


@delayed_router.post("/hello")
async def hello(p: Payload = Payload(message="Default")):
    message = f"Hello task ran with payload: {p.message}"
    logger.warning(message)


@delayed_router.post("/fail_twice", dependencies=[Depends(max_retries(2))])
async def fail_twice():
    raise Exception("nooo")


scheduled_router = APIRouter(route_class=ScheduledRoute, prefix="/scheduled")


@scheduled_router.post("/timed_hello")
async def scheduled_hello(p: Payload = Payload(message="Default")):
    message = f"Scheduled hello task ran with payload: {p.message}"
    logger.warning(message)
    return {"message": message}


# We want to schedule tasks only in a deployed environment
if not IS_LOCAL:
    scheduled_hello.scheduler(
        name="testing-examples-scheduled-hello",
        schedule="*/5 * * * *",
        time_zone="Asia/Kolkata",
    ).schedule(p=Payload(message="Scheduled"))

app.include_router(delayed_router)
app.include_router(scheduled_router)
