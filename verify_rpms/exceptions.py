
class BaseException(Exception):
    """The base class for all Verify RPMs exceptions."""


class CmdError(BaseException):
    """Denote error in running cmd"""
