# Standard Library Imports
from typing import Dict
from typing import List
from typing import Tuple

# Third Party Imports
from google.cloud import scheduler_v1
from google.cloud import tasks_v2
from pydantic.error_wrappers import ErrorWrapper

# Imports from this repository
from fastapi_cloud_tasks.exception import BadMethodException


def location_path(*, project, location):
    return scheduler_v1.CloudSchedulerClient.common_location_path(project=project, location=location)


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
        raise BadMethodException("Can't trigger task with multiple methods")
    method = methodMap.get(methods[0], None)
    if method is None:
        raise BadMethodException(f"Unknown method {methods[0]}")
    return method


def schedulerMethod(methods):
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
