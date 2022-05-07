# Standard Library Imports
import datetime

# Third Party Imports
from fastapi.routing import APIRoute
from google.cloud import tasks_v2
from google.protobuf import timestamp_pb2

# Imports from this repository
from fastapi_cloud_tasks.exception import BadMethodException
from fastapi_cloud_tasks.hooks import DelayedTaskHook
from fastapi_cloud_tasks.requester import Requester


class Delayer(Requester):
    def __init__(
        self,
        *,
        route: APIRoute,
        base_url: str,
        queue_path: str,
        client: tasks_v2.CloudTasksClient,
        pre_create_hook: DelayedTaskHook,
        task_create_timeout: float = 10.0,
        countdown: int = 0,
        task_id: str = None,
    ) -> None:
        super().__init__(route=route, base_url=base_url)
        self.queue_path = queue_path
        self.countdown = countdown
        self.task_create_timeout = task_create_timeout

        self.task_id = task_id
        self.method = _task_method(route.methods)
        self.client = client
        self.pre_create_hook = pre_create_hook

    def delay(self, **kwargs):
        # Create http request
        request = tasks_v2.HttpRequest()
        request.http_method = self.method
        request.url = self._url(values=kwargs)
        request.headers = self._headers(values=kwargs)

        body = self._body(values=kwargs)
        if body:
            request.body = body

        # Scheduled the task
        task = tasks_v2.Task(http_request=request)
        schedule_time = self._schedule()
        if schedule_time:
            task.schedule_time = schedule_time

        # Make task name for deduplication
        if self.task_id:
            task.name = f"{self.queue_path}/tasks/{self.task_id}"

        request = tasks_v2.CreateTaskRequest(parent=self.queue_path, task=task)

        request = self.pre_create_hook(request)

        return self.client.create_task(
            request=request, timeout=self.task_create_timeout
        )

    def _schedule(self):
        if self.countdown is None or self.countdown <= 0:
            return None
        d = datetime.datetime.utcnow() + datetime.timedelta(seconds=self.countdown)
        timestamp = timestamp_pb2.Timestamp()
        timestamp.FromDatetime(d)
        return timestamp


def _task_method(methods):
    methodMap = {
        "POST": tasks_v2.HttpMethod.POST,
        "GET": tasks_v2.HttpMethod.GET,
        "HEAD": tasks_v2.HttpMethod.HEAD,
        "PUT": tasks_v2.HttpMethod.PUT,
        "DELETE": tasks_v2.HttpMethod.DELETE,
        "PATCH": tasks_v2.HttpMethod.PATCH,
        "OPTIONS": tasks_v2.HttpMethod.OPTIONS,
    }
    methods = list(methods)
    # Only crash if we're being bound
    if len(methods) > 1:
        raise BadMethodException("Can't trigger task with multiple methods")
    method = methodMap.get(methods[0], None)
    if method is None:
        raise BadMethodException(f"Unknown method {methods[0]}")
    return method
