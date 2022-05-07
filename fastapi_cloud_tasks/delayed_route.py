# Standard Library Imports
import queue
from typing import Callable

# Third Party Imports
from fastapi.routing import APIRoute
from google.cloud import tasks_v2

# Imports from this repository
from fastapi_cloud_tasks.delayer import Delayer
from fastapi_cloud_tasks.hooks import DelayedTaskHook
from fastapi_cloud_tasks.hooks import noop_hook
from fastapi_cloud_tasks.utils import ensure_queue


def DelayedRouteBuilder(
    *,
    base_url: str,
    queue_path: str,
    task_create_timeout: float = 10.0,
    pre_create_hook: DelayedTaskHook = None,
    client=None,
    auto_create_queue=True,
):
    """
    Returns a Mixin that should be used to override route_class.

    It adds a .delay and .options methods to the original endpoint.

    Example:
    ```
      delayed_router = APIRouter(route_class=DelayedRouteBuilder(...), prefix="/delayed")

      class UserData(BaseModel):
          name: str

      @delayed_router.post("/on_user_create/{user_id}")
      def on_user_create(user_id: str, data: UserData):
          # do work here
          # Return values are meaningless

      # Call .delay to trigger
      on_user_create.delay(user_id="007", data=UserData(name="Piyush"))

      app.include_router(delayed_router)
    ```
    """
    if client is None:
        client = tasks_v2.CloudTasksClient()

    if pre_create_hook is None:
        pre_create_hook = noop_hook

    if auto_create_queue:
        ensure_queue(client=client, path=queue_path)

    class TaskRouteMixin(APIRoute):
        def get_route_handler(self) -> Callable:
            original_route_handler = super().get_route_handler()
            self.endpoint.options = self.delayOptions
            self.endpoint.delay = self.delay
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

    return TaskRouteMixin
