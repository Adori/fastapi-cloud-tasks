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
        pre_scheduler_hook: SchedulerHook,
        name: str = "",
        schedule_create_timeout: float = 10.0,
        retry_config: scheduler_v1.RetryConfig = None,
        time_zone: str = None
    ) -> None:
        super().__init__(route=route, base_url=base_url)
        if name == "":
            name = route.unique_id

        if retry_config is None:
            retry_config = scheduler_v1.RetryConfig(retry_count=5)

        self.retry_config = retry_config
        location_parts = client.parse_common_location_path(location_path)

        self.job_id = client.job_path(job=name, **location_parts)
        self.time_zone = time_zone

        self.location_path = location_path
        self.cron_schedule = schedule
        self.schedule_create_timeout = schedule_create_timeout

        self.method = schedulerMethod(route.methods)
        self.client = client
        self.pre_scheduler_hook = pre_scheduler_hook

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
        job = scheduler_v1.Job(
            name=self.job_id,
            http_target=request,
            schedule=self.cron_schedule,
            retry_config=self.retry_config,
        )
        if self.time_zone is not None:
            job.time_zone = self.time_zone
        request = scheduler_v1.CreateJobRequest(parent=self.location_path, job=job)

        request = self.pre_scheduler_hook(request)

        # Delete and create job
        self.delete()
        return self.client.create_job(request=request, timeout=self.schedule_create_timeout)

    def delete(self):
        # We return true or exception because you could have the delete code on multiple instances
        try:
            self.client.delete_job(name=self.job_id, timeout=self.schedule_create_timeout)
            return True
        except Exception as ex:
            return ex
