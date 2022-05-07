# Standard Library Imports
from typing import Callable

# Third Party Imports
from fastapi.routing import APIRoute
from google.cloud import scheduler_v1

# Imports from this repository
from fastapi_cloud_tasks.hooks import ScheduledHook
from fastapi_cloud_tasks.hooks import noop_hook
from fastapi_cloud_tasks.scheduler import Scheduler


def ScheduledRouteBuilder(
    *,
    base_url: str,
    location_path: str,
    job_create_timeout: float = 10.0,
    pre_create_hook: ScheduledHook = None,
    client=None,
):
    """
    Returns a Mixin that should be used to override route_class.

    It adds a .scheduler method to the original endpoint.

    Example:
    ```
    scheduled_router = APIRouter(route_class=ScheduledRouteBuilder(...), prefix="/scheduled")

    @scheduled_router.get("/simple_scheduled_task")
    def simple_scheduled_task():
        # Do work here

    simple_scheduled_task.scheduler(name="simple_scheduled_task", schedule="* * * * *").schedule()

    app.include_router(scheduled_router)
    ```
    """
    if client is None:
        client = scheduler_v1.CloudSchedulerClient()

    if pre_create_hook is None:
        pre_create_hook = noop_hook

    class ScheduledRouteMixin(APIRoute):
        def get_route_handler(self) -> Callable:
            original_route_handler = super().get_route_handler()
            self.endpoint.scheduler = self.schedulerOptions
            return original_route_handler

        def schedulerOptions(self, *, name, schedule, **options) -> Scheduler:
            schedulerOpts = dict(
                base_url=base_url,
                location_path=location_path,
                client=client,
                pre_create_hook=pre_create_hook,
                job_create_timeout=job_create_timeout,
                name=name,
                schedule=schedule,
            )

            schedulerOpts.update(options)

            return Scheduler(route=self, **schedulerOpts)

    return ScheduledRouteMixin
