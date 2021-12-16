# Standard Library Imports
from typing import Callable

# Third Party Imports
from fastapi.routing import APIRoute
from google.cloud import scheduler_v1, tasks_v2

from fastapi_cloud_tasks.delayer import Delayer
from fastapi_cloud_tasks.hooks import SchedulerHook, TaskHook, noop_hook
from fastapi_cloud_tasks.scheduler import Scheduler


def TaskRouteBuilder(
    *,
    base_url: str,
    queue_path: str,
    task_create_timeout: float = 10.0,
    schedule_create_timeout: float = 10.0,
    pre_create_hook: TaskHook = None,
    pre_scheduler_hook: SchedulerHook = None,
    client=None,
    scheduler_client=None,
):
    if client is None:
        client = tasks_v2.CloudTasksClient()

    if scheduler_client is None:
        scheduler_client = scheduler_v1.CloudSchedulerClient()

    if pre_create_hook is None:
        pre_create_hook = noop_hook

    if pre_scheduler_hook is None:
        pre_scheduler_hook = noop_hook

    q_path = client.parse_queue_path(queue_path)
    default_location_path = scheduler_client.common_location_path(
        project=q_path["project"], location=q_path["location"]
    )

    class TaskRouteMixin(APIRoute):
        def get_route_handler(self) -> Callable:
            original_route_handler = super().get_route_handler()
            self.endpoint.options = self.delayOptions
            self.endpoint.delay = self.delay
            self.endpoint.scheduler = self.schedulerOptions
            return original_route_handler

        def delayOptions(self, **options) -> Delayer:
            delayOpts = dict(
                base_url=base_url,
                queue_path=queue_path,
                task_create_timeout=task_create_timeout,
                client=client,
                pre_create_hook=pre_create_hook,
            )
            if hasattr(self.endpoint, "_delayOptions"):
                delayOpts.update(self.endpoint._delayOptions)
            delayOpts.update(options)

            return Delayer(
                route=self,
                **delayOpts,
            )

        def delay(self, **kwargs):
            return self.delayOptions().delay(**kwargs)

        def schedulerOptions(self, *, name, schedule, **options) -> Scheduler:
            schedulerOpts = dict(
                base_url=base_url,
                location_path=default_location_path,
                client=scheduler_client,
                pre_scheduler_hook=pre_scheduler_hook,
                schedule_create_timeout=schedule_create_timeout,
                name=name,
                schedule=schedule,
            )

            schedulerOpts.update(options)

            return Scheduler(route=self, **schedulerOpts)

    return TaskRouteMixin
