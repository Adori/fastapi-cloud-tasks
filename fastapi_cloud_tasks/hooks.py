# Standard Library Imports
from typing import Callable

# Third Party Imports
from google.cloud import scheduler_v1
from google.cloud import tasks_v2
from google.protobuf import duration_pb2

TaskHook = Callable[[tasks_v2.CreateTaskRequest], tasks_v2.CreateTaskRequest]
SchedulerHook = Callable[[scheduler_v1.CreateJobRequest], scheduler_v1.CreateJobRequest]


def noop_hook(request):
    return request


def chained_hook(*hooks):
    def chain(request):
        for hook in hooks:
            request = hook(request)
        return request

    return chain


def oidc_scheduler_hook(token: scheduler_v1.OidcToken) -> SchedulerHook:
    def add_token(
        request: scheduler_v1.CreateJobRequest,
    ) -> scheduler_v1.CreateJobRequest:
        request.job.http_target.oidc_token = token
        return request

    return add_token


def oidc_task_hook(token: tasks_v2.OidcToken) -> TaskHook:
    def add_token(request: tasks_v2.CreateTaskRequest) -> tasks_v2.CreateTaskRequest:
        request.task.http_request.oidc_token = token
        return request

    return add_token


def oauth_scheduler_hook(token: scheduler_v1.OAuthToken) -> SchedulerHook:
    def add_token(
        request: scheduler_v1.CreateJobRequest,
    ) -> scheduler_v1.CreateJobRequest:
        request.job.http_target.oauth_token = token
        return request

    return add_token


def oauth_task_hook(token: tasks_v2.OAuthToken) -> TaskHook:
    def add_token(request: tasks_v2.CreateTaskRequest) -> tasks_v2.CreateTaskRequest:
        request.task.http_request.oauth_token = token
        return request

    return add_token


def deadline_scheduler_hook(duration: duration_pb2.Duration) -> SchedulerHook:
    def deadline(
        request: scheduler_v1.CreateJobRequest,
    ) -> scheduler_v1.CreateJobRequest:
        request.job.attempt_deadline = duration
        return request

    return deadline


def deadline_task_hook(duration: duration_pb2.Duration) -> TaskHook:
    def deadline(request: tasks_v2.CreateTaskRequest) -> tasks_v2.CreateTaskRequest:
        request.task.dispatch_deadline = duration
        return request

    return deadline
