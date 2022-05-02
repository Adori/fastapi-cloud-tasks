# FastAPI Cloud Tasks

Strongly typed background tasks with FastAPI and CloudTasks!

GCP's Cloud Tasks + FastAPI = Replacement for celery's async delayed tasks.

GCP's Cloud Scheduler + FastAPI = Replacement for celery beat.

FastAPI Cloud Tasks + Cloud Run = Autoscaled delayed tasks.

## Installation

```
pip install fastapi-cloud-tasks
```

## Concept

[`Cloud Tasks`](https://cloud.google.com/tasks) allows us to schedule a HTTP request in the future.

[FastAPI](https://fastapi.tiangolo.com/tutorial/body/) makes us define complete schema and params for an HTTP endpoint.


[`Cloud Scheduler`](https://cloud.google.com/scheduler) allows us to schedule recurring HTTP requests in the future.

FastAPI Cloud Tasks works by putting the three together:

- It adds a `.delay` method to existing routes on FastAPI.
- When this method is called, it schedules a request with Cloud Tasks.
- The task worker is a regular FastAPI server which gets called by Cloud Tasks.
- It adds a `.scheduler` method to existing routes on FastAPI.
- When this method is called, it schedules a recurring job with Cloud Scheduler.

If we host the task worker on Cloud Run, we get autoscaling workers.

## Pseudocode

In practice, this is what it looks like:

```python
delayed_router = APIRouter(route_class=DelayedRouteBuilder(...))
scheduled_router = APIRouter(route_class=ScheduledRouteBuilder(...))

class Recipe(BaseModel):
    ingredients: List[str]

@delayed_router.post("/{restaurant}/make_dinner")
async def make_dinner(restaurant: str, recipe: Recipe):
    # Do a ton of work here.

@scheduled_router.post("/home_cook")
async def home_cook(recipe: Recipe):
    # Make my own food

app.include_router(delayed_router)
app.include_router(scheduled_router)

# If you wan to make your own breakfast every morning at 7AM IST.
home_cook.scheduler(name="test-home-cook-at-7AM-IST", schedule="0 7 * * *", time_zone="Asia/Kolkata").schedule(recipe=Recipe(ingredients=["Milk","Cereal"]))
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

# First we construct our DelayedRoute class with all relevant settings
# This can be done once across the entire project
DelayedRoute = DelayedRouteBuilder(
    base_url="http://feda-49-207-221-153.ngrok.io",
    queue_path=queue_path(
        project="gcp-project-id",
        location="asia-south1",
        queue="test-queue",
    ),
)

delayed_router = APIRouter(route_class=DelayedRoute, prefix="/tasks")

class Payload(BaseModel):
    message: str

@delayed_router.post("/hello")
async def hello(p: Payload = Payload(message="Default")):
    logger.warning(f"Hello task ran with payload: {p.message}")


# Define our app and add trigger to it.
app = FastAPI()

@app.get("/trigger")
async def trigger():
    # Trigger the task
    hello.delay(p=Payload(message="Triggered task"))
    return {"message": "Hello task triggered"}

app.include_router(delayed_router)

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

DelayedRoute = DelayedRouteBuilder(
    base_url=base_url,
    # Task queue, same as above.
    queue_path=queue_path(...),
    pre_create_hook=oidc_task_hook(
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

### DelayedRouteBuilder

Usage:

```python
DelayedRoute = DelayedRouteBuilder(...)
delayed_router = APIRouter(route_class=DelayedRoute)

@delayed_router.get("/simple_task")
def mySimpleTask():
    return {}
```

- `base_url` - The URL of your worker FastAPI service.

- `queue_path` - Full path of the Cloud Tasks queue. (Hint: use the util function `queue_path`)

- `task_create_timeout` - How long should we wait before giving up on creating cloud task.

- `pre_create_hook` - If you need to edit the `CreateTaskRequest` before sending it to Cloud Tasks (eg: Auth for Cloud Run), you can do that with this hook. See hooks section below for more.

- `client` - If you need to override the Cloud Tasks client, pass the client here. (eg: changing credentials, transport etc)

#### Task level default options

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

#### Delayer Options

Usage:

```python
mySimpleTask.options(...).delay()
```

All options from above can be overriden per call (including DelayedRouteBuilder options like `base_url`) with kwargs to the `options` function before calling delay.

Example:

```python
# Trigger after 2 minutes
mySimpleTask.options(countdown=120).delay()
```

### ScheduledRouteBuilder

Usage:

```python
ScheduledRoute = ScheduledRouteBuilder(...)
scheduled_router = APIRouter(route_class=ScheduledRoute)

@scheduled_router.get("/simple_scheduled_task")
def mySimpleScheduledTask():
    return {}


mySimpleScheduledTask.scheduler(name="simple_scheduled_task", schedule="* * * * *").schedule()
```


## Hooks

We might need to override things in the task being sent to Cloud Tasks. The `pre_create_hook` allows us to do that.

Some hooks are included in the library.

- `oidc_delayed_hook` / `oidc_scheduled_hook` - Used to pass OIDC token (for Cloud Run etc).
- `deadline_delayed_hook` / `deadline_scheduled_hook` - Used to change the timeout for the worker of a task. (PS: this deadline is decided by the sender to the queue and not the worker)
- `chained_hook` - If you need to chain multiple hooks together, you can do that with `chained_hook(hook1, hook2)`

## Future work

- Ensure queue exists.
- Make helper features for worker's side. Eg:
  - Easier access to current retry count.
  - API Exceptions to make GCP back-off.
