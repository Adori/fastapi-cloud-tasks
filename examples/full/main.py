from uuid import uuid4

from examples.full.serializer import Payload
from examples.full.tasks import hello
from fastapi import FastAPI, Response, status
from google.api_core.exceptions import AlreadyExists

app = FastAPI()

task_id = str(uuid4())


@app.get("/basic")
async def basic():
    hello.delay(p=Payload(message="Basic task"))
    return {"message": "Basic hello task scheduled"}


@app.get("/delayed")
async def delayed():
    hello.options(countdown=5).delay(p=Payload(message="Delayed task"))
    return {"message": "Delayed hello task scheduled"}


@app.get("/deduped")
async def deduped(response: Response):

    try:
        hello.options(task_id=task_id).delay(p=Payload(message="Deduped task"))
        return {"message": "Deduped hello task scheduled"}
    except AlreadyExists as e:
        response.status_code = status.HTTP_409_CONFLICT
        return {"error": "Could not schedule task.", "reason": str(e)}
