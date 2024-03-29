# Third Party Imports
from pydantic.v1.errors import MissingError
from pydantic.v1.errors import PydanticValueError


class MissingParamError(MissingError):
    msg_template = "field required: {param}"


class WrongTypeError(PydanticValueError):
    msg_template = "Expected {field} to be of type {type}"


class BadMethodException(Exception):
    pass
