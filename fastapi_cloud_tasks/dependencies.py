# Standard Library Imports
import typing
from datetime import datetime

# Third Party Imports
from fastapi import Depends
from fastapi import Header
from fastapi import HTTPException


def max_retries(count: int = 20):
    """
    Raises a http exception (with status 200) after max retries are exhausted
    """

    def retries_dep(meta: CloudTasksHeaders = Depends()) -> bool:
        # count starts from 0 so equality check is required
        if meta.retry_count >= count:
            raise HTTPException(status_code=200, detail="Max retries exhausted")

    return retries_dep


class CloudTasksHeaders:
    """
    Extracts known headers sent by Cloud Tasks

    Full list: https://cloud.google.com/tasks/docs/creating-http-target-tasks#handler
    """

    def __init__(
        self,
        x_cloudtasks_taskretrycount: typing.Optional[int] = Header(0),
        x_cloudtasks_taskexecutioncount: typing.Optional[int] = Header(0),
        x_cloudtasks_queuename: typing.Optional[str] = Header(""),
        x_cloudtasks_taskname: typing.Optional[str] = Header(""),
        x_cloudtasks_tasketa: typing.Optional[float] = Header(0),
        x_cloudtasks_taskpreviousresponse: typing.Optional[int] = Header(0),
        x_cloudtasks_taskretryreason: typing.Optional[str] = Header(""),
    ) -> None:
        self.retry_count = x_cloudtasks_taskretrycount
        self.execution_count = x_cloudtasks_taskexecutioncount
        self.queue_name = x_cloudtasks_queuename
        self.task_name = x_cloudtasks_taskname
        self.eta = datetime.fromtimestamp(x_cloudtasks_tasketa)
        self.previous_response = x_cloudtasks_taskpreviousresponse
        self.retry_reason = x_cloudtasks_taskretryreason
