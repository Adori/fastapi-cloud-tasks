# Standard Library Imports
from typing import Callable

# Third Party Imports
from google.cloud import scheduler_v1
from google.cloud import tasks_v2
from google.protobuf import duration_pb2

DelayedTaskHook = Callable[[tasks_v2.CreateTaskRequest], tasks_v2.CreateTaskRequest]
ScheduledHook = Callable[[scheduler_v1.CreateJobRequest], scheduler_v1.CreateJobRequest]


def noop_hook(request):
    return request


def chained_hook(*hooks):
    def chain(request):
        for hook in hooks:
            request = hook(request)
        return request

    return chain


def oidc_scheduled_hook(token: scheduler_v1.OidcToken) -> ScheduledHook:
    def add_token(
        request: scheduler_v1.CreateJobRequest,
    ) -> scheduler_v1.CreateJobRequest:
        request.job.http_target.oidc_token = token
        return request

    return add_token


def oidc_delayed_hook(token: tasks_v2.OidcToken) -> DelayedTaskHook:
    def add_token(request: tasks_v2.CreateTaskRequest) -> tasks_v2.CreateTaskRequest:
        request.task.http_request.oidc_token = token
        return request

    return add_token


def oauth_scheduled_hook(token: scheduler_v1.OAuthToken) -> ScheduledHook:
    def add_token(
        request: scheduler_v1.CreateJobRequest,
    ) -> scheduler_v1.CreateJobRequest:
        request.job.http_target.oauth_token = token
        return request

    return add_token


def oauth_delayed_hook(token: tasks_v2.OAuthToken) -> DelayedTaskHook:
    def add_token(request: tasks_v2.CreateTaskRequest) -> tasks_v2.CreateTaskRequest:
        request.task.http_request.oauth_token = token
        return request

    return add_token


def deadline_scheduled_hook(duration: duration_pb2.Duration) -> ScheduledHook:
    def deadline(
        request: scheduler_v1.CreateJobRequest,
    ) -> scheduler_v1.CreateJobRequest:
        request.job.attempt_deadline = duration
        return request

    return deadline


def deadline_delayed_hook(duration: duration_pb2.Duration) -> DelayedTaskHook:
    def deadline(request: tasks_v2.CreateTaskRequest) -> tasks_v2.CreateTaskRequest:
        request.task.dispatch_deadline = duration
        return request

    return deadline
