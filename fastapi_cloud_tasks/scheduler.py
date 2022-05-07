# Standard Library Imports

# Third Party Imports
from fastapi.routing import APIRoute
from google.cloud import scheduler_v1
from google.protobuf import duration_pb2

# Imports from this repository
from fastapi_cloud_tasks.exception import BadMethodException
from fastapi_cloud_tasks.hooks import ScheduledHook
from fastapi_cloud_tasks.requester import Requester


class Scheduler(Requester):
    def __init__(
        self,
        *,
        route: APIRoute,
        base_url: str,
        location_path: str,
        schedule: str,
        client: scheduler_v1.CloudSchedulerClient,
        pre_create_hook: ScheduledHook,
        name: str = "",
        job_create_timeout: float = 10.0,
        retry_config: scheduler_v1.RetryConfig = None,
        time_zone: str = "UTC",
        force: bool = False,
    ) -> None:
        super().__init__(route=route, base_url=base_url)
        if name == "":
            name = route.unique_id

        if retry_config is None:
            retry_config = scheduler_v1.RetryConfig(
                retry_count=5,
                max_retry_duration=duration_pb2.Duration(seconds=0),
                min_backoff_duration=duration_pb2.Duration(seconds=5),
                max_backoff_duration=duration_pb2.Duration(seconds=120),
                max_doublings=5,
            )

        self.retry_config = retry_config
        location_parts = client.parse_common_location_path(location_path)

        self.job_id = client.job_path(job=name, **location_parts)
        self.time_zone = time_zone

        self.location_path = location_path
        self.cron_schedule = schedule
        self.job_create_timeout = job_create_timeout

        self.method = _scheduler_method(route.methods)
        self.client = client
        self.pre_create_hook = pre_create_hook
        self.force = force

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
            time_zone=self.time_zone,
        )

        request = scheduler_v1.CreateJobRequest(parent=self.location_path, job=job)

        request = self.pre_create_hook(request)

        if self.force or self._has_changed(request=request):
            # Delete and create job
            self.delete()
            self.client.create_job(request=request, timeout=self.job_create_timeout)

    def _has_changed(self, request: scheduler_v1.CreateJobRequest):
        try:
            job = self.client.get_job(name=request.job.name)
            # Remove things that are either output only or GCP adds by default
            job.user_update_time = None
            job.state = None
            job.status = None
            job.last_attempt_time = None
            job.schedule_time = None
            del job.http_target.headers["User-Agent"]
            # Proto compare works directly with `__eq__`
            return job != request.job
        except Exception:
            return True
        return False

    def delete(self):
        # We return true or exception because you could have the delete code on multiple instances
        try:
            self.client.delete_job(name=self.job_id, timeout=self.job_create_timeout)
            return True
        except Exception as ex:
            return ex


def _scheduler_method(methods):
    methodMap = {
        "POST": scheduler_v1.HttpMethod.POST,
        "GET": scheduler_v1.HttpMethod.GET,
        "HEAD": scheduler_v1.HttpMethod.HEAD,
        "PUT": scheduler_v1.HttpMethod.PUT,
        "DELETE": scheduler_v1.HttpMethod.DELETE,
        "PATCH": scheduler_v1.HttpMethod.PATCH,
        "OPTIONS": scheduler_v1.HttpMethod.OPTIONS,
    }
    methods = list(methods)
    # Only crash if we're being bound
    if len(methods) > 1:
        raise BadMethodException("Can't schedule task with multiple methods")
    method = methodMap.get(methods[0], None)
    if method is None:
        raise BadMethodException(f"Unknown method {methods[0]}")
    return method
