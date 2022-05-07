# Third Party Imports
import grpc
from google.api_core.exceptions import AlreadyExists
from google.cloud import scheduler_v1
from google.cloud import tasks_v2
from google.cloud.tasks_v2.services.cloud_tasks import transports


def location_path(*, project: str, location: str, **ignored):
    return scheduler_v1.CloudSchedulerClient.common_location_path(
        project=project, location=location
    )


def queue_path(*, project: str, location: str, queue: str):
    return tasks_v2.CloudTasksClient.queue_path(
        project=project, location=location, queue=queue
    )


def ensure_queue(
    *,
    client: tasks_v2.CloudTasksClient,
    path: str,
    **kwargs,
):
    # We extract information from the queue path to make the public api simpler
    parsed_queue_path = client.parse_queue_path(path=path)
    create_req = tasks_v2.CreateQueueRequest(
        parent=location_path(**parsed_queue_path),
        queue=tasks_v2.Queue(name=path, **kwargs),
    )
    try:
        client.create_queue(request=create_req)
    except AlreadyExists:
        pass


def emulator_client(*, host="localhost:8123"):
    channel = grpc.insecure_channel(host)
    transport = transports.CloudTasksGrpcTransport(channel=channel)
    return tasks_v2.CloudTasksClient(transport=transport)
