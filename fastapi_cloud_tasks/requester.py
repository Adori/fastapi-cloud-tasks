# Standard Library Imports
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

# Third Party Imports
from fastapi.dependencies.utils import request_params_to_args
from fastapi.encoders import jsonable_encoder
from fastapi.routing import APIRoute

from fastapi_cloud_tasks.exception import MissingParamError, WrongTypeError
from fastapi_cloud_tasks.utils import err_val

try:
    import ujson as json
except Exception:
    import json


class Requester:
    def __init__(
        self,
        *,
        route: APIRoute,
        base_url: str,
    ) -> None:
        self.route = route
        self.base_url = base_url.rstrip("/")

    def _headers(self, *, values):
        headers = err_val(request_params_to_args(self.route.dependant.header_params, values))
        cookies = err_val(request_params_to_args(self.route.dependant.cookie_params, values))
        if len(cookies) > 0:
            headers["Cookies"] = "; ".join([f"{k}={v}" for (k, v) in cookies.items()])
        # We use json only.
        headers["Content-Type"] = "application/json"
        # Always send string headers and skip all headers which are supposed to be sent by cloudtasks
        return {str(k): str(v) for (k, v) in headers.items() if not str(k).startswith("x_cloudtasks_")}

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
