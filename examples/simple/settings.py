import os

from taskroute import queue_path

TASK_LISTENER_BASE_URL = os.getenv("TASK_LISTENER_BASE_URL", default="http://example.com")
TASK_PROJECT_ID = os.getenv("TASK_PROJECT_ID", default="sample-project")
TASK_LOCATION = os.getenv("TASK_LOCATION", default="asia-south1")
TASK_QUEUE = os.getenv("TASK_QUEUE", default="test-queue")

TASK_QUEUE_PATH = queue_path(
    project=TASK_PROJECT_ID,
    location=TASK_LOCATION,
    queue=TASK_QUEUE,
)
