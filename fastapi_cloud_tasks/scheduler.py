# Standard Library Imports

# Third Party Imports
from fastapi.routing import APIRoute
from google.cloud import scheduler_v1

from fastapi_cloud_tasks.hooks import Hook
from fastapi_cloud_tasks.requester import Requester
from fastapi_cloud_tasks.utils import schedulerMethod


class Scheduler(Requester):
    def __init__(
        self,
        *,
        route: APIRoute,
        base_url: str,
        queue_path: str,
        task_create_timeout: float = 10.0,
        client: scheduler_v1.CloudSchedulerClient,
        pre_create_hook: Hook,
        countdown: int = 0,
        task_id: str = None,
    ) -> None:
        super().__init__(route=route, base_url=base_url)
        self.queue_path = queue_path
        self.countdown = countdown
        self.task_create_timeout = task_create_timeout

        self.task_id = task_id
        self.method = schedulerMethod(route.methods)
        self.client = client
        self.pre_create_hook = pre_create_hook

    def schedule(self, **kwargs):
        # Create http request
        request = scheduler_v1.HttpTarget()
        request.http_method = self.method
        request.uri = self._url(values=kwargs)
        request.headers = self._headers(values=kwargs)

        body = self._body(values=kwargs)
        if body:
            request.body = body

        # Scheduled the task
        job = scheduler_v1.Job(http_target=request)
        # TODO: try updating job, if it fails, create job

        # request = tasks_v2.CreateTaskRequest(parent=self.queue_path, task=task)

        # request = self.pre_create_hook(request)

        # return self.client.create_task(request=request, timeout=self.task_create_timeout)
