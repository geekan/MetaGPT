#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   :

import typing

from tenacity import after_log, _utils


def general_after_log(logger: "loguru.Logger", sec_format: str = "%0.3f") -> typing.Callable[["RetryCallState"], None]:
    def log_it(retry_state: "RetryCallState") -> None:
        if retry_state.fn is None:
            fn_name = "<unknown>"
        else:
            fn_name = _utils.get_callback_name(retry_state.fn)
        logger.error(f"Finished call to '{fn_name}' after {sec_format % retry_state.seconds_since_start}(s), "
                     f"this was the {_utils.to_ordinal(retry_state.attempt_number)} time calling it. "
                     f"exp: {retry_state.outcome.exception()}")
    return log_it
