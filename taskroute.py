# Standard Library Imports
from typing import Callable, Dict, List, Tuple
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

# Third Party Imports
from fastapi.dependencies.utils import request_params_to_args
from fastapi.routing import APIRoute
from google.cloud import tasks_v2
from pydantic.error_wrappers import ErrorWrapper
from pydantic.errors import MissingError

# Create a client.
client = tasks_v2.CloudTasksClient()


def queue_path(project, location, queue):
    return tasks_v2.CloudTasksClient.queue_path(project=project, location=location, queue=queue)


def err_val(resp: Tuple[Dict, List[ErrorWrapper]]):
    values, errors = resp

    if len(errors) != 0:
        # TODO: Log everything but raise first only
        # TODO: find a better way to raise and display these errors
        raise errors[0].exc
    return values


def make_url(*, base_url, path, params):
    url_parts = list(urlparse(base_url))
    # Note: you might think urljoin is a better solution here, it is not.
    url_parts[2] = url_parts[2].strip("/") + "/" + path.strip("/")

    query = dict(parse_qsl(url_parts[4]))
    query.update(params)

    url_parts[4] = urlencode(query)
    return urlunparse


class Delayer:
    def __init__(
        self, *, route: APIRoute, base_url: str, queue_path: str, countdown: int = 0, task_id: str = None
    ) -> None:
        self.route = route
        self.queue_path = queue_path
        self.base_url = base_url.rstrip("/")
        self.countdown = countdown
        self.task_id = task_id

    def delay(self, **kwargs):
        route = self.route
        methods = list(route.methods)
        # Only crash if we're being bound
        if len(methods) > 1:
            raise Exception("Can't trigger task with multiple methods")
        # Add default values of path and query params
        print(
            "bound",
            route.name,
            route.path,
            route.path_format,
            route.dependencies,
            route.param_convertors,
            route.dependant.path_params,
            route.dependant.query_params,
            route.dependant.header_params,
            route.dependant.cookie_params,
            route.body_field,
        )
        path_values = err_val(request_params_to_args(route.dependant.path_params, kwargs))
        for (name, converter) in route.param_convertors.items():
            if name in path_values:
                continue
            if name not in kwargs:
                # TODO: raise a better error, same as above
                raise MissingError()

            # TODO: should we catch errors here and raise better errors?
            path_values[name] = converter.convert(kwargs[name])
        request = {}

        path = route.path_format.format(**path_values)
        body = None
        if route.body_field and route.body_field.required:
            body = kwargs.get(route.body_field.name, None)
            if body is None:
                # TODO: raise better error
                raise MissingError()

        params = err_val(request_params_to_args(route.dependant.query_params, kwargs))
        request["url"] = make_url(base_url=self.base_url, path=path, query_params=params)
        request["headers"] = err_val(request_params_to_args(route.dependant.header_params, kwargs))
        # TODO: body add body
        # TODO: http method from map
        request["http_method"] = tasks_v2.HttpMethod.GET
        # cookies = err_val(request_params_to_args(route.dependant.cookie_params, kwargs))
        if len(route.dependant.cookie_params) > 0:
            raise Exception("Cookies are not supported by cloud tasks")
        client.create_task(request={"parent": self.queue_path, "task": {"http_request":request}})



def TaskRouteBuilder(
    *,
    base_url: str,
    queue_path: str,
):
    class TaskRouteMixin(APIRoute):
        def get_route_handler(self) -> Callable:
            original_route_handler = super().get_route_handler()
            self.endpoint.options = self.delayOptions
            self.endpoint.delay = self.delay
            return original_route_handler

        def delayOptions(self, **options):
            return Delayer(route=self, base_url=base_url, queue_path=queue_path, **options)

        def delay(self, **kwargs):
            return self.delayOptions().delay(**kwargs)

    return TaskRouteMixin
