# Third Party Imports
from pydantic import BaseModel


class Payload(BaseModel):
    message: str
