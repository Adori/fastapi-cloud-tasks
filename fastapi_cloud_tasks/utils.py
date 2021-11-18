# Standard Library Imports
from typing import Dict, List, Tuple

# Third Party Imports
from google.cloud import tasks_v2
from pydantic.error_wrappers import ErrorWrapper


def queue_path(*, project, location, queue):
    return tasks_v2.CloudTasksClient.queue_path(project=project, location=location, queue=queue)


def err_val(resp: Tuple[Dict, List[ErrorWrapper]]):
    values, errors = resp

    if len(errors) != 0:
        # TODO: Log everything but raise first only
        # TODO: find a better way to raise and display these errors
        raise errors[0].exc
    return values


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
