from typing import Callable, List

from google.cloud import tasks_v2
from google.protobuf import duration_pb2

Hook = Callable[[tasks_v2.CreateTaskRequest], tasks_v2.CreateTaskRequest]


def noop_hook(request: tasks_v2.CreateTaskRequest) -> tasks_v2.CreateTaskRequest:
    return request


def chained_hook(*hooks: List[Hook]) -> Hook:
    def chain(request: tasks_v2.CreateTaskRequest) -> tasks_v2.CreateTaskRequest:
        for hook in hooks:
            request = hook(request)
        return request

    return chain


def oidc_hook(token: tasks_v2.OidcToken) -> Hook:
    def add_token(request: tasks_v2.CreateTaskRequest) -> tasks_v2.CreateTaskRequest:
        request.task.http_request.oidc_token = token
        return request

    return add_token


def oauth_hook(token: tasks_v2.OAuthToken) -> Hook:
    def add_token(request: tasks_v2.CreateTaskRequest) -> tasks_v2.CreateTaskRequest:
        request.task.http_request.oauth_token = token
        return request

    return add_token


def deadline_hook(duration: duration_pb2.Duration) -> Hook:
    def deadline(request: tasks_v2.CreateTaskRequest) -> tasks_v2.CreateTaskRequest:
        request.task.dispatch_deadline = duration
        return request

    return deadline
