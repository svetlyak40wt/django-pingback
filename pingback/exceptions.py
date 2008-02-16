"""Pingback exceptions"""

class PingbackNotConfigured(Exception):
    pass


class PingbackError(object):
    SOURCE_DOES_NOT_EXIST = 0x0010
    SOURCE_DOES_NOT_LINKING = 0x0011
    TARGET_DOES_NOT_EXIST = 0x0020
    TARGET_IS_NOT_PINGABLE = 0x0021
    PINGBACK_ALREADY_REGISTERED = 0x0030
    ACCESS_DENIED = 0x0031
    CONNECTION_ERROR = 0x0032

    @classmethod
    def is_error(cls, value):
        return value in cls.__dict__.values()

