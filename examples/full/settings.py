# Standard Library Imports
import os

# Third Party Imports
from google.cloud import scheduler_v1
from google.cloud import tasks_v2

# Imports from this repository
from fastapi_cloud_tasks.utils import queue_path

TASK_LISTENER_BASE_URL = os.getenv(
    "TASK_LISTENER_BASE_URL", default="https://b22d-35-207-241-4.ngrok.io"
)
TASK_PROJECT_ID = os.getenv("TASK_PROJECT_ID", default="applied-honor-105708")
TASK_LOCATION = os.getenv("TASK_LOCATION", default="asia-south1")
TASK_QUEUE = os.getenv("TASK_QUEUE", default="test-queue")

TASK_SERVICE_ACCOUNT = os.getenv(
    "TASK_SERVICE_ACCOUNT",
    default=f"fastapi-cloud-tasks@{TASK_PROJECT_ID}.iam.gserviceaccount.com",
)

TASK_QUEUE_PATH = queue_path(
    project=TASK_PROJECT_ID,
    location=TASK_LOCATION,
    queue=TASK_QUEUE,
)

TASK_OIDC_TOKEN = tasks_v2.OidcToken(
    service_account_email=TASK_SERVICE_ACCOUNT, audience=TASK_LISTENER_BASE_URL
)
SCHEDULER_OIDC_TOKEN = scheduler_v1.OidcToken(
    service_account_email=TASK_SERVICE_ACCOUNT, audience=TASK_LISTENER_BASE_URL
)
