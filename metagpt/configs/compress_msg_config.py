from enum import Enum


class CompressType(Enum):
    """
    Compression Type for messages. Used to compress messages under token limit.
    - "": No compression. Default value.
    - "post_cut_by_msg": Keep as many latest messages as possible.
    - "post_cut_by_token": Keep as many latest messages as possible and truncate the earliest fit-in message.
    - "pre_cut_by_msg": Keep as many earliest messages as possible.
    - "pre_cut_by_token": Keep as many earliest messages as possible and truncate the latest fit-in message.
    """

    NO_COMPRESS = ""
    POST_CUT_BY_MSG = "post_cut_by_msg"
    POST_CUT_BY_TOKEN = "post_cut_by_token"
    PRE_CUT_BY_MSG = "pre_cut_by_msg"
    PRE_CUT_BY_TOKEN = "pre_cut_by_token"

    def __missing__(self, key):
        return self.NO_COMPRESS

    @classmethod
    def get_type(cls, type_name):
        for member in cls:
            if member.value == type_name:
                return member
        return cls.NO_COMPRESS

    @classmethod
    def cut_types(cls):
        return [member for member in cls if "cut" in member.value]
