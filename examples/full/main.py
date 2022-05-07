# Standard Library Imports
from uuid import uuid4

# Third Party Imports
from fastapi import FastAPI
from fastapi import Response
from fastapi import status
from google.api_core.exceptions import AlreadyExists

# Imports from this repository
from examples.full.serializer import Payload
from examples.full.settings import IS_LOCAL
from examples.full.tasks import fail_twice
from examples.full.tasks import hello

app = FastAPI()

task_id = str(uuid4())


@app.get("/basic")
async def basic():
    hello.delay(p=Payload(message="Basic task"))
    return {"message": "Basic hello task scheduled"}


@app.get("/with_countdown")
async def with_countdown():
    hello.options(countdown=5).delay(p=Payload(message="Countdown task"))
    return {"message": "Countdown hello task scheduled"}


@app.get("/deduped")
async def deduped(response: Response):
    # Note: this does not work with cloud-tasks-emulator.
    try:
        hello.options(task_id=task_id).delay(p=Payload(message="Deduped task"))
        return {"message": "Deduped hello task scheduled"}
    except AlreadyExists as e:
        response.status_code = status.HTTP_409_CONFLICT
        return {"error": "Could not schedule task.", "reason": str(e)}


@app.get("/fail")
async def fail():
    fail_twice.delay()
    return {
        "message": "The triggered task will fail twice and then be marked done automatically"
    }


# We can use a trick on local to get all tasks on the same process as the main server.
# In a deployed environment, we'd really want to run 2 separate processes
if IS_LOCAL:
    # Imports from this repository
    from examples.full.tasks import app as task_app

    app.mount("/_fastapi_cloud_tasks", task_app)
