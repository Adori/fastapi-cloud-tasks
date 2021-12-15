# Standard Library Imports

# Third Party Imports
from fastapi.routing import APIRoute
from google.cloud import scheduler_v1

from fastapi_cloud_tasks.hooks import SchedulerHook
from fastapi_cloud_tasks.requester import Requester
from fastapi_cloud_tasks.utils import schedulerMethod


class Scheduler(Requester):
    def __init__(
        self,
        *,
        route: APIRoute,
        base_url: str,
        location_path: str,
        schedule: str,
        client: scheduler_v1.CloudSchedulerClient,
        pre_create_hook: SchedulerHook,
        name: str = "",
        schedule_create_timeout: float = 10.0,
    ) -> None:
        super().__init__(route=route, base_url=base_url)
        if name == "":
            name = route.unique_id

        location_parts = client.parse_common_location_path(location_path)

        self.job_id = client.job_path(job=name, **location_parts)

        self.location_path = location_path
        self.cron_schedule = schedule
        self.schedule_create_timeout = schedule_create_timeout

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
        request = scheduler_v1.CreateJobRequest(parent=self.location_path)
        # TODO: try updating job, if it fails, create job

        # request = tasks_v2.CreateTaskRequest(parent=self.queue_path, task=task)

        # request = self.pre_create_hook(request)

        # return self.client.create_task(request=request, timeout=self.task_create_timeout)
