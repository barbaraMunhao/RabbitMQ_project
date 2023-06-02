import enum


class Comands(enum.Enum):

    JOIN = 0
    LOGIN = 1
    ERROR = -1
    USER_EXIST = 1062
    SEND_MSG = 2
    USER_KEYS = 3
    HIST = 4
    ACK_MSG = -2
    GROUP_EXIST = -10

