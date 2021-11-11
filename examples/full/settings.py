import os

from gelery.utils import queue_path
from google.cloud import tasks_v2

TASK_LISTENER_BASE_URL = os.getenv("TASK_LISTENER_BASE_URL", default="http://example.com")
TASK_PROJECT_ID = os.getenv("TASK_PROJECT_ID", default="sample-project")
TASK_LOCATION = os.getenv("TASK_LOCATION", default="asia-south1")
TASK_QUEUE = os.getenv("TASK_QUEUE", default="test-queue")

TASK_SERVICE_ACCOUNT = os.getenv("TASK_SERVICE_ACCOUNT", default=f"gelery@{TASK_PROJECT_ID}.iam.gserviceaccount.com")

TASK_QUEUE_PATH = queue_path(
    project=TASK_PROJECT_ID,
    location=TASK_LOCATION,
    queue=TASK_QUEUE,
)

TASK_OIDC_TOKEN = tasks_v2.OidcToken(service_account_email=TASK_SERVICE_ACCOUNT, audience=TASK_LISTENER_BASE_URL)
