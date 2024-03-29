# Third Party Imports
from pydantic.v1 import BaseModel


class Payload(BaseModel):
    message: str
