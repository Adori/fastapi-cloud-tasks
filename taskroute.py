# Standard Library Imports
import datetime
from typing import Callable, Dict, List, Tuple
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

# Third Party Imports
from fastapi.dependencies.utils import request_params_to_args
from fastapi.encoders import jsonable_encoder
from fastapi.routing import APIRoute
from google.cloud import tasks_v2
from google.cloud.tasks_v2.types import target as gct_target
from google.cloud.tasks_v2.types import task as gct_task
from google.protobuf import timestamp_pb2
from pydantic.error_wrappers import ErrorWrapper
from pydantic.errors import MissingError

try:
    import ujson as json
except Exception:
    import json


def queue_path(*, project, location, queue):
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
    return urlunparse(url_parts)


def taskMethod(methods):
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
        raise Exception("Can't trigger task with multiple methods")
    method = methodMap.get(methods[0], None)
    if method is None:
        raise Exception(f"Unknown method {methods[0]}")
    return method


class Delayer:
    def __init__(
        self,
        *,
        route: APIRoute,
        base_url: str,
        queue_path: str,
        task_create_timeout: float = 10.0,
        client: tasks_v2.CloudTasksClient,
        countdown: int = 0,
        task_id: str = None,
    ) -> None:
        self.route = route
        self.queue_path = queue_path
        self.base_url = base_url.rstrip("/")
        self.countdown = countdown
        self.task_create_timeout = task_create_timeout

        self.task_id = task_id
        self.method = taskMethod(route.methods)
        self.client = client
        if len(route.dependant.cookie_params) > 0:
            raise Exception("Cookies are not supported by cloud tasks")

    def delay(self, **kwargs):

        request = gct_target.HttpRequest()

        request.url = self._url(kwargs=kwargs)
        request.headers = err_val(request_params_to_args(self.route.dependant.header_params, kwargs))
        request.http_method = self.method
        body = self._body(kwargs=kwargs)
        if body:
            request.body = body
        # cookies = err_val(request_params_to_args(route.dependant.cookie_params, kwargs))
        task = gct_task.Task(http_request=request)
        schedule_time = self._schedule()
        if schedule_time:
            task.schedule_time = schedule_time

        if self.task_id:
            # Add the name to tasks.
            task.name = f"{self.queue_path}/tasks/{self.task_id}"

        return self.client.create_task(parent=self.queue_path, task=task, timeout=self.task_create_timeout)

    def _schedule(self):
        if self.countdown is None or self.countdown <= 0:
            return None
        d = datetime.datetime.utcnow() + datetime.timedelta(seconds=self.countdown)
        timestamp = timestamp_pb2.Timestamp()
        timestamp.FromDatetime(d)
        return timestamp

    def _url(self, *, kwargs):
        route = self.route
        path_values = err_val(request_params_to_args(route.dependant.path_params, kwargs))
        for (name, converter) in route.param_convertors.items():
            if name in path_values:
                continue
            if name not in kwargs:
                # TODO: raise a better error, same as above
                raise MissingError()

            # TODO: should we catch errors here and raise better errors?
            path_values[name] = converter.convert(kwargs[name])
        path = route.path_format.format(**path_values)
        params = err_val(request_params_to_args(route.dependant.query_params, kwargs))

        # Make final URL

        # Split base url into parts
        url_parts = list(urlparse(self.base_url))

        # Add relative path
        # Note: you might think urljoin is a better solution here, it is not.
        url_parts[2] = url_parts[2].strip("/") + "/" + path.strip("/")

        # Make query dict and update our with our params
        query = dict(parse_qsl(url_parts[4]))
        query.update(params)

        # override query params
        url_parts[4] = urlencode(query)
        return urlunparse(url_parts)

    def _body(self, *, kwargs):
        body = None
        body_field = self.route.body_field
        if body_field and body_field.name:
            got_body = kwargs.get(body_field.name, None)
            if got_body is None:
                if body_field.required:
                    # TODO: raise better error
                    raise MissingError()
                got_body = body_field.get_default()
            if not isinstance(got_body, body_field.type_):
                raise Exception(f"Expected {body_field.name} to be of type {body_field.type_}")
            body = json.dumps(jsonable_encoder(got_body)).encode()
        return body


def TaskRouteBuilder(
    *,
    base_url: str,
    queue_path: str,
    task_create_timeout: float = 10.0,
    client=None,
):
    if client is None:
        client = tasks_v2.CloudTasksClient()

    class TaskRouteMixin(APIRoute):
        def get_route_handler(self) -> Callable:
            original_route_handler = super().get_route_handler()
            self.endpoint.options = self.delayOptions
            self.endpoint.delay = self.delay
            return original_route_handler

        def delayOptions(self, **options):
            return Delayer(
                route=self,
                base_url=base_url,
                queue_path=queue_path,
                task_create_timeout=task_create_timeout,
                client=client,
                **options,
            )

        def delay(self, **kwargs):
            return self.delayOptions().delay(**kwargs)

    return TaskRouteMixin
