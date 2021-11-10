from examples.simple.serializer import Payload
from examples.simple.settings import TASK_BASE_URL, TASK_QUEUE_PATH
from fastapi import FastAPI
from fastapi.routing import APIRouter
from taskroute import TaskRouteBuilder, queue_path

app = FastAPI()

TaskRoute = TaskRouteBuilder(base_url=TASK_BASE_URL, queue_path=TASK_QUEUE_PATH)

router = APIRouter(route_class=TaskRoute, prefix="/tasks")


@router.post("/hello")
async def hello(p: Payload = Payload(message="Default")):
    message = f"Hello task ran with payload: {p.message}"
    print(message)
    return {"message": message}


app.include_router(router)
