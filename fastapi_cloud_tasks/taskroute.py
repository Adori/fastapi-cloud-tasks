# Standard Library Imports
from typing import Callable

# Third Party Imports
from fastapi.routing import APIRoute
from google.cloud import tasks_v2

from fastapi_cloud_tasks.delayer import Delayer
from fastapi_cloud_tasks.hooks import Hook, noop_hook


def TaskRouteBuilder(
    *,
    base_url: str,
    queue_path: str,
    task_create_timeout: float = 10.0,
    pre_create_hook: Hook = None,
    client=None,
):
    if client is None:
        client = tasks_v2.CloudTasksClient()

    if pre_create_hook is None:
        pre_create_hook = noop_hook

    class TaskRouteMixin(APIRoute):
        def get_route_handler(self) -> Callable:
            original_route_handler = super().get_route_handler()
            self.endpoint.options = self.delayOptions
            self.endpoint.delay = self.delay
            return original_route_handler

        def delayOptions(self, **options):
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

    return TaskRouteMixin
