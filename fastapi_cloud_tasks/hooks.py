from typing import Callable, List

from google.cloud import scheduler_v1, tasks_v2
from google.protobuf import duration_pb2

TaskHook = Callable[[tasks_v2.CreateTaskRequest], tasks_v2.CreateTaskRequest]
SchedulerHook = Callable[[scheduler_v1.CreateJobRequest], scheduler_v1.CreateJobRequest]


def noop_scheduler_hook(request: scheduler_v1.CreateJobRequest) -> scheduler_v1.CreateJobRequest:
    return request


def noop_task_hook(request: tasks_v2.CreateTaskRequest) -> tasks_v2.CreateTaskRequest:
    return request


def chained_task_hook(*hooks: List[TaskHook]) -> TaskHook:
    def chain(request: tasks_v2.CreateTaskRequest) -> tasks_v2.CreateTaskRequest:
        for hook in hooks:
            request = hook(request)
        return request

    return chain


def oidc_task_hook(token: tasks_v2.OidcToken) -> TaskHook:
    def add_token(request: tasks_v2.CreateTaskRequest) -> tasks_v2.CreateTaskRequest:
        request.task.http_request.oidc_token = token
        return request

    return add_token


def oauth_task_hook(token: tasks_v2.OAuthToken) -> TaskHook:
    def add_token(request: tasks_v2.CreateTaskRequest) -> tasks_v2.CreateTaskRequest:
        request.task.http_request.oauth_token = token
        return request

    return add_token


def deadline_task_hook(duration: duration_pb2.Duration) -> TaskHook:
    def deadline(request: tasks_v2.CreateTaskRequest) -> tasks_v2.CreateTaskRequest:
        request.task.dispatch_deadline = duration
        return request

    return deadline
