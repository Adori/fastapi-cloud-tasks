# Third Party Imports
from pydantic.errors import MissingError
from pydantic.errors import PydanticValueError


class MissingParamError(MissingError):
    msg_template = "field required: {param}"


class WrongTypeError(PydanticValueError):
    msg_template = "Expected {field} to be of type {type}"


class BadMethodException(Exception):
    pass
