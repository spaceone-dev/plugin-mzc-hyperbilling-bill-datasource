from spaceone.core.error import *


class ERROR_UNKNOWN_REGION(ERROR_INVALID_ARGUMENT):
    _message = 'region({region}) is not valid.'

class ERROR_UNSUPPORTED_FEATURE(ERROR_BASE):
    _message = 'unsupported feature request: {reason}'

class ERROR_WRONG_DATE_FORMAT(ERROR_BASE):
    _message = 'date format is yyyy-mm-dd, but {date}'

class ERROR_WRONG_DATE_RANGE(ERROR_BASE):
    _message = 'start {start} > end {end}'

class ERROR_RANGE_LIMIT(ERROR_BASE):
    _message = '{reason}, range <= {value}'
