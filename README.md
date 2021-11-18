# FastAPI Cloud Tasks

GCP's Cloud Tasks + FastAPI = Replacement for celery's async delayed tasks.

FastAPI Cloud Tasks + Cloud Run = Autoscaled delayed tasks.

## Concept

[`Cloud Tasks`](https://cloud.google.com/tasks) allows us to schedule a HTTP request in the future.

[FastAPI](https://fastapi.tiangolo.com/tutorial/body/) makes us define complete schema and params for an HTTP endpoint.

FastAPI Cloud Tasks works by putting the two together:

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

Pre-requisites:

- Create a task queue and copy the project id, location and queue name.
- Install and ensure that ngrok works.

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

Running on Cloud Run with authentication needs us to supply an OIDC token. To do that we can use a `hook`.

Pre-requisites:

- Create a task queue. Copy the project id, location and queue name.
- Deploy the worker as a service on Cloud Run and copy it's URL.
- Create a service account in cloud IAM and add `Cloud Run Invoker` role to it.

We'll only edit the parts from above that we need changed from above example.

```python
# URL of the Cloud Run service
base_url = "https://hello-randomchars-el.a.run.app"

TaskRoute = TaskRouteBuilder(
    base_url=base_url,
    # Task queue, same as above.
    queue_path=queue_path(...),
    pre_create_hook=oidc_hook(
        token=tasks_v2.OidcToken(
            # Service account that you created
            service_account_email="fastapi-cloud-tasks@gcp-project-id.iam.gserviceaccount.com",
            audience=base_url,
        ),
    ),
)
```

Check the fleshed out example at [`examples/full/tasks.py`](examples/full/tasks.py)

## Configuration

### TaskRouteBuilder

Usage:

```python
TaskRoute = TaskRouteBuilder(...)
task_router = APIRouter(route_class=TaskRoute)

@task_router.get("/simple_task")
def mySimpleTask():
    return {}
```

- `base_url` - The URL of your worker FastAPI service.

- `queue_path` - Full path of the Cloud Tasks queue. (Hint: use the util function `queue_path`)

- `task_create_timeout` - How long should we wait before giving up on creating cloud task.

- `pre_create_hook` - If you need to edit the `CreateTaskRequest` before sending it to Cloud Tasks (eg: Auth for Cloud Run), you can do that with this hook. See hooks section below for more.

- `client` - If you need to override the Cloud Tasks client, pass the client here. (eg: changing credentials, transport etc)

### Task level default options

Usage:

```python
@task_router.get("/simple_task")
@task_default_options(...)
def mySimpleTask():
    return {}
```

All options from above can be passed as `kwargs` to the decorator.

Additional options:

- `countdown` - Seconds in the future to schedule the task.
- `task_id` - named task id for deduplication. (One task id will only be queued once.)

Eg:

```python
# Trigger after 5 minutes
@task_router.get("/simple_task")
@task_default_options(countdown=300)
def mySimpleTask():
    return {}
```

### Delayer Options

Usage:

```python
mySimpleTask.options(...).delay()
```

All options from above can be overriden per call (including TaskRouteBuilder options like `base_url`) with kwargs to the `options` function before calling delay.

Example:

```python
# Trigger after 2 minutes
mySimpleTask.options(countdown=120).delay()
```

## Hooks

We might need to override things in the task being sent to Cloud Tasks. The `pre_create_hook` allows us to do that.

Some hooks are included in the library.

- `oidc_hook` - Used to work with Cloud Run.
- `deadline_hook` - Used to change the timeout for the worker of a task. (PS: this deadline is decided by the sender to the queue and not the worker)
- `chained_hook` - If you need to chain multiple hooks together, you can do that with `chained_hook(hook1, hook2)`

## Future work

- Ensure queue exists.
- Integrate with [Cloud Scheduler](https://cloud.google.com/scheduler/) to replace celery beat.
- Make helper features for worker's side. Eg:
  - Easier access to current retry count.
  - API Exceptions to make GCP back-off.
