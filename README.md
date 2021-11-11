# Gelery

GCP's Cloud Tasks + FastAPI = Replacement for celery's async delayed tasks.

Gelery + Cloud Run = Autoscaled delayed tasks.

## Concept

[`Cloud Tasks`](https://cloud.google.com/tasks) allows us to schedule a HTTP request in the future.

[FastAPI](https://fastapi.tiangolo.com/tutorial/body/) makes us define complete schema and params for an HTTP endpoint.

Gelery works by putting the two together:

- It adds a `.delay` method to existing routes on FastAPI.
- When this method is called, it schedules a request with Cloud Tasks.
- The task worker is a regular FastAPI server which gets called by Cloud Tasks.

If we host the task worker on Cloud Run, we get free autoscaling.

## Pseudocode

In practice, this is what it looks like:

```python
router = APIRouter(route_class=TaskRouteBuilder(...))

class Recipe(BaseModel):
    ingredients: List[str]

@router.post("/{restaurant}/make_dinner")
async def make_dinner(restaurant: str, recipe: Recipe,):
    # Do a ton of work here.

app.include_router(router)
```

Now we can trigger the task with

```python
make_dinner.delay(restaurant="Taj", recipe=Recipe(ingredients=["Pav","Bhaji"]))
```

If we want to trigger the task 30 minutes later

```python
make_dinner.options(countdown=1800).delay(...)
```

## Running

### Local

We will need a an API endpoint to give to cloud tasks, so let us fire up ngrok on local

```sh
ngrok http 8000
```

You'll see something like this

```
Forwarding                    http://feda-49-207-221-153.ngrok.io -> http://localhost:8000
```

```python
# complete file: examples/simple/main.py

# First we construct our TaskRoute class with all relevant settings
# This can be done once across the entire project
TaskRoute = TaskRouteBuilder(
    base_url="http://feda-49-207-221-153.ngrok.io",
    queue_path=queue_path(
        project="gcp-project-id",
        location="asia-south1",
        queue="test-queue",
    ),
)

# Wherever we use
task_router = APIRouter(route_class=TaskRoute, prefix="/tasks")

class Payload(BaseModel):
    message: str

@task_router.post("/hello")
async def hello(p: Payload = Payload(message="Default")):
    logger.warning(f"Hello task ran with payload: {p.message}")


# Define our app and add trigger to it.
app = FastAPI()

@app.get("/trigger")
async def trigger():
    # Trigger the task
    hello.delay(p=Payload(message="Triggered task"))
    return {"message": "Hello task triggered"}

app.include_router(task_router)

```

Start running the task runner on port 8000 so that it is accessible from cloud tasks.

```sh
uvicorn main:app --reload --port 8000
```

In another terminal, trigger the task with curl

```
curl http://localhost:8000/trigger
```

Check the logs on the server, you should see

```
WARNING:  Hello task ran with payload: Triggered task
```

Note: You can read complete working source code of the above example in [`examples/simple/main.py`](examples/simple/main.py)
In the real world you'd have a separate process for task runner and actual task.

### Cloud Run

TK - Explain setup for OIDC auth
Check the full example at [`examples/full/tasks.py`](examples/full/tasks.py)

## Configuration

TK

## Hooks

TK

## How do I?

### Set custom deadline for task execution

TK

### Add Auth information

TK

## Future work

- Ensure queue exists.
- Integrate with [Cloud Scheduler](https://cloud.google.com/scheduler/) to replace celery beat
