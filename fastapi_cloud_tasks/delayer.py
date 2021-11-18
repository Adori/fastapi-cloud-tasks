# Standard Library Imports
import datetime
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

# Third Party Imports
from fastapi.dependencies.utils import request_params_to_args
from fastapi.encoders import jsonable_encoder
from fastapi.routing import APIRoute
from google.cloud import tasks_v2
from google.protobuf import timestamp_pb2

from fastapi_cloud_tasks.exception import MissingParamError, WrongTypeError
from fastapi_cloud_tasks.hooks import Hook
from fastapi_cloud_tasks.utils import err_val, taskMethod

try:
    import ujson as json
except Exception:
    import json


class Delayer:
    def __init__(
        self,
        *,
        route: APIRoute,
        base_url: str,
        queue_path: str,
        task_create_timeout: float = 10.0,
        client: tasks_v2.CloudTasksClient,
        pre_create_hook: Hook,
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
        self.pre_create_hook = pre_create_hook

    def delay(self, **kwargs):
        # Create http request
        request = tasks_v2.HttpRequest()
        request.http_method = self.method
        request.url = self._url(values=kwargs)
        request.headers = self._headers(values=kwargs)

        body = self._body(values=kwargs)
        if body:
            request.body = body

        # Scheduled the task
        task = tasks_v2.Task(http_request=request)
        schedule_time = self._schedule()
        if schedule_time:
            task.schedule_time = schedule_time

        # Make task name for deduplication
        if self.task_id:
            task.name = f"{self.queue_path}/tasks/{self.task_id}"

        request = tasks_v2.CreateTaskRequest(parent=self.queue_path, task=task)

        request = self.pre_create_hook(request)

        return self.client.create_task(request=request, timeout=self.task_create_timeout)

    def _schedule(self):
        if self.countdown is None or self.countdown <= 0:
            return None
        d = datetime.datetime.utcnow() + datetime.timedelta(seconds=self.countdown)
        timestamp = timestamp_pb2.Timestamp()
        timestamp.FromDatetime(d)
        return timestamp

    def _headers(self, *, values):
        headers = err_val(request_params_to_args(self.route.dependant.header_params, values))
        cookies = err_val(request_params_to_args(self.route.dependant.cookie_params, values))
        if len(cookies) > 0:
            headers["Cookies"] = "; ".join([f"{k}={v}" for (k, v) in cookies.items()])
        return headers

    def _url(self, *, values):
        route = self.route
        path_values = err_val(request_params_to_args(route.dependant.path_params, values))
        for (name, converter) in route.param_convertors.items():
            if name in path_values:
                continue
            if name not in values:
                raise MissingParamError(param=name)

            # TODO: should we catch errors here and raise better errors?
            path_values[name] = converter.convert(values[name])
        path = route.path_format.format(**path_values)
        params = err_val(request_params_to_args(route.dependant.query_params, values))

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

    def _body(self, *, values):
        body = None
        body_field = self.route.body_field
        if body_field and body_field.name:
            got_body = values.get(body_field.name, None)
            if got_body is None:
                if body_field.required:
                    raise MissingParamError(name=body_field.name)
                got_body = body_field.get_default()
            if not isinstance(got_body, body_field.type_):
                raise WrongTypeError(field=body_field.name, type=body_field.type_)
            body = json.dumps(jsonable_encoder(got_body)).encode()
        return body
